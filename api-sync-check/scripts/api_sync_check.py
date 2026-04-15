#!/usr/bin/env python3
"""前后端接口一致性校验"""

import argparse
import json
import re
import sys
from pathlib import Path


def extract_backend_routes(backend: Path) -> list[dict]:
    """从后端路由文件提取 API 定义（含 prefix）"""
    routes = []
    route_dir = backend / "src" / "routes"
    if not route_dir.exists():
        return routes

    for f in route_dir.glob("*.ts"):
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines()

        # 提取 prefix: new Router({ prefix: '/api/diaries' })
        prefix = ""
        pm = re.search(r"prefix:\s*['\"]([^'\"]+)['\"]", text)
        if pm:
            prefix = pm.group(1).rstrip("/")

        for i, line in enumerate(lines, 1):
            m = re.search(
                r"router\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
                line, re.I,
            )
            if m:
                route_path = m.group(2)
                full_path = prefix + route_path if route_path != "/" else prefix + "/"
                # 去掉尾部多余的 /
                full_path = full_path.rstrip("/") or "/"
                routes.append({
                    "method": m.group(1).upper(),
                    "path": full_path,
                    "file": str(f.relative_to(backend)),
                    "line": i,
                })
    return routes


def extract_frontend_calls(frontend: Path) -> list[dict]:
    """从前端 service 文件提取 API 调用"""
    calls = []
    service_dir = frontend / "src" / "services"
    if not service_dir.exists():
        return calls

    for f in service_dir.glob("*.ts"):
        text = f.read_text(encoding="utf-8")
        lines = text.splitlines()

        # 检测 API_BASE_URL 是否已包含 /api
        base_has_api = bool(re.search(r"API_BASE_URL\s*=\s*['\"][^'\"]*\/api['\"]", text))
        api_prefix = "/api" if base_has_api else ""

        # 提取 Taro.request({ url: `${...}/path`, method: 'GET' }) 块
        for m in re.finditer(
            r"Taro\.request\s*\(\s*\{(.*?)\}\s*\)",
            text, re.DOTALL,
        ):
            block = m.group(1)
            url_m = re.search(r"url:\s*`\$\{[^}]*\}([^`]+)`", block)
            method_m = re.search(r"method:\s*['\"](\w+)['\"]", block)
            if url_m:
                path = url_m.group(1)
                full_path = (api_prefix + path).rstrip("/") or "/"
                method = method_m.group(1).upper() if method_m else "GET"
                # 计算行号
                line_no = text[:m.start()].count("\n") + 1
                calls.append({
                    "method": method,
                    "path": full_path,
                    "file": str(f.relative_to(frontend)),
                    "line": line_no,
                })
                continue

        # 补充：匹配 axios 风格 .get(`${BASE}/path`)
        for i, line in enumerate(lines, 1):
            m = re.search(
                r"\.(get|post|put|delete|patch)\s*\(\s*`?\$\{[^}]*\}([^`'\")\s,]+)",
                line, re.I,
            )
            if m and "Taro.request" not in line:
                path = m.group(2)
                full_path = (api_prefix + path).rstrip("/") or "/"
                calls.append({
                    "method": m.group(1).upper(),
                    "path": full_path,
                    "file": str(f.relative_to(frontend)),
                    "line": i,
                })
    return calls


def normalize_path(path: str) -> str:
    """将路径参数统一为 :param 格式"""
    # /diaries/xxx → /diaries/:id
    path = re.sub(r"/\$\{[^}]+\}", "/:id", path)
    return path.rstrip("/")


def extract_frontend_types(frontend: Path) -> dict[str, list[str]]:
    """提取前端 service 中的类型定义字段"""
    types = {}
    service_file = frontend / "src" / "services" / "diary.ts"
    if not service_file.exists():
        return types

    text = service_file.read_text(encoding="utf-8")
    # 提取 type/interface 定义
    for m in re.finditer(r"(?:type|interface)\s+(\w+)\s*(?:=\s*)?\{(.*?)\}", text, re.DOTALL):
        name = m.group(1)
        body = m.group(2)
        fields = []
        for fm in re.finditer(r"(\w+)\??\s*:", body):
            fields.append(fm.group(1))
        types[name] = fields
    return types


def extract_backend_types(backend: Path) -> dict[str, list[str]]:
    """提取后端 types 中的类型定义字段"""
    types = {}
    types_file = backend / "src" / "types" / "index.ts"
    if not types_file.exists():
        return types

    text = types_file.read_text(encoding="utf-8")
    for m in re.finditer(r"(?:interface|type)\s+(\w+)\s*(?:=\s*)?\{(.*?)\}", text, re.DOTALL):
        name = m.group(1)
        body = m.group(2)
        fields = []
        for fm in re.finditer(r"(\w+)\??\s*:", body):
            fields.append(fm.group(1))
        types[name] = fields
    return types


def check_routes(backend_routes: list[dict], frontend_calls: list[dict]) -> list[dict]:
    """对比路由和调用"""
    issues = []

    backend_set = {(r["method"], normalize_path(r["path"])) for r in backend_routes}
    frontend_set = {(c["method"], normalize_path(c["path"])) for c in frontend_calls}

    # 后端有但前端没调用
    backend_only = backend_set - frontend_set
    for method, path in sorted(backend_only):
        route = next(r for r in backend_routes if r["method"] == method and normalize_path(r["path"]) == path)
        issues.append({
            "level": "info",
            "type": "unused_route",
            "method": method,
            "path": path,
            "location": f"{route['file']}:{route['line']}",
            "msg": f"后端定义了 {method} {path} 但前端未调用",
        })

    # 前端调用但后端没有
    frontend_only = frontend_set - backend_set
    for method, path in sorted(frontend_only):
        call = next(c for c in frontend_calls if c["method"] == method and normalize_path(c["path"]) == path)
        issues.append({
            "level": "critical",
            "type": "ghost_call",
            "method": method,
            "path": path,
            "location": f"{call['file']}:{call['line']}",
            "msg": f"前端调用了 {method} {path} 但后端未定义",
        })

    return issues


def check_types(frontend: Path, backend: Path) -> list[dict]:
    """对比前后端类型字段"""
    issues = []
    fe_types = extract_frontend_types(frontend)
    be_types = extract_backend_types(backend)

    # 对比 FrontendDiary / BackendDiary vs DiaryJSON
    diary_json = be_types.get("DiaryJSON", [])
    if not diary_json:
        return issues

    for type_name in ["BackendDiary", "FrontendDiary"]:
        fe_fields = fe_types.get(type_name, [])
        if not fe_fields:
            continue

        be_only = set(diary_json) - set(fe_fields)
        fe_only = set(fe_fields) - set(diary_json)

        for f in be_only:
            issues.append({
                "level": "warning",
                "type": "field_mismatch",
                "msg": f"DiaryJSON 有 '{f}' 但前端 {type_name} 缺失",
            })
        for f in fe_only:
            issues.append({
                "level": "info",
                "type": "field_mismatch",
                "msg": f"前端 {type_name} 有 '{f}' 但 DiaryJSON 缺失",
            })

    return issues


def print_report(backend_routes, frontend_calls, issues):
    print(f"\n{'='*60}")
    print(f"📋 API 一致性检查报告")
    print(f"{'='*60}")
    print(f"\n后端路由: {len(backend_routes)} 个")
    for r in backend_routes:
        print(f"  {r['method']:6s} {r['path']:30s}  ({r['file']}:{r['line']})")

    print(f"\n前端调用: {len(frontend_calls)} 个")
    for c in frontend_calls:
        print(f"  {c['method']:6s} {c['path']:30s}  ({c['file']}:{c['line']})")

    if not issues:
        print(f"\n✓ 前后端接口完全一致")
        return

    labels = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
    print(f"\n问题 ({len(issues)}):")
    for issue in sorted(issues, key=lambda x: {"critical": 0, "warning": 1, "info": 2}[x["level"]]):
        loc = issue.get("location", "")
        print(f"  {labels[issue['level']]} {issue['msg']}" + (f"  ({loc})" if loc else ""))


def main():
    parser = argparse.ArgumentParser(description="前后端接口一致性校验")
    parser.add_argument("--frontend", required=True, help="前端项目目录")
    parser.add_argument("--backend", required=True, help="后端项目目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    frontend = Path(args.frontend).resolve()
    backend = Path(args.backend).resolve()

    backend_routes = extract_backend_routes(backend)
    frontend_calls = extract_frontend_calls(frontend)

    issues = []
    issues.extend(check_routes(backend_routes, frontend_calls))
    issues.extend(check_types(frontend, backend))

    if args.json:
        print(json.dumps({
            "backend_routes": backend_routes,
            "frontend_calls": frontend_calls,
            "issues": issues,
        }, ensure_ascii=False, indent=2))
    else:
        print_report(backend_routes, frontend_calls, issues)


if __name__ == "__main__":
    main()
