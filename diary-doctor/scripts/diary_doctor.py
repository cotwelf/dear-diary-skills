#!/usr/bin/env python3
"""前后端代码健康检查"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


def find_ts_files(root: Path) -> list[Path]:
    src = root / "src"
    if not src.exists():
        return []
    return sorted(
        p for p in src.rglob("*")
        if p.suffix in (".ts", ".tsx") and "node_modules" not in str(p)
    )


def read_file(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return text, text.splitlines()


# ── Checks ──────────────────────────────────────────────


def check_unused_imports(path: Path, text: str, lines: list[str]) -> list[dict]:
    """检测未使用的 import"""
    issues = []
    for i, line in enumerate(lines, 1):
        m = re.match(r"import\s+(?:React,?\s*)?{([^}]+)}\s+from", line)
        if not m:
            continue
        names = [n.strip().split(" as ")[-1].strip() for n in m.group(1).split(",")]
        rest = text[text.index(line) + len(line):]
        for name in names:
            if not name:
                continue
            # 检查 import 之后的代码是否使用了这个名字
            if not re.search(rf"\b{re.escape(name)}\b", rest):
                issues.append({
                    "level": "info",
                    "file": str(path),
                    "line": i,
                    "msg": f"未使用的 import: {name}",
                })
    return issues


def check_empty_catch(path: Path, text: str, lines: list[str]) -> list[dict]:
    """检测空 catch 块"""
    issues = []
    for i, line in enumerate(lines, 1):
        if re.search(r"catch\s*(\([^)]*\))?\s*\{\s*\}", line):
            issues.append({
                "level": "warning",
                "file": str(path),
                "line": i,
                "msg": "空 catch 块，错误被静默吞掉",
            })
    return issues


def check_uncleared_timers(path: Path, text: str, lines: list[str]) -> list[dict]:
    """检测未清理的 setTimeout/setInterval"""
    issues = []
    has_set = bool(re.search(r"\bsetTimeout\b|\bsetInterval\b", text))
    has_clear = bool(re.search(r"\bclearTimeout\b|\bclearInterval\b", text))
    if has_set and not has_clear and path.suffix == ".tsx":
        for i, line in enumerate(lines, 1):
            if re.search(r"\bsetTimeout\b|\bsetInterval\b", line):
                issues.append({
                    "level": "warning",
                    "file": str(path),
                    "line": i,
                    "msg": "setTimeout/setInterval 未见对应的 clear，可能内存泄漏",
                })
    return issues


def check_fire_and_forget(path: Path, text: str, lines: list[str]) -> list[dict]:
    """检测 fire-and-forget 的 async 调用（无 await 无 catch）"""
    issues = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # 匹配 this.save() 或 someService.method() 没有 await 也没有 .catch
        if (re.search(r"(?<!await\s)\bthis\.\w+\(", stripped)
                and stripped.endswith(";")
                and "await" not in stripped
                and ".catch" not in stripped
                and "async" not in stripped
                and "return" not in stripped
                and re.search(r"\b(save|update|delete|create|remove|write)\b", stripped, re.I)):
            issues.append({
                "level": "warning",
                "file": str(path),
                "line": i,
                "msg": f"可能的 fire-and-forget: {stripped.strip()[:60]}",
            })
    return issues


def check_empty_files(path: Path, text: str, lines: list[str]) -> list[dict]:
    """检测空文件"""
    if len(text.strip()) == 0:
        return [{"level": "info", "file": str(path), "line": 1, "msg": "空文件"}]
    return []


def check_empty_hooks(path: Path, text: str, lines: list[str]) -> list[dict]:
    """检测空的 useEffect hook"""
    issues = []
    for i, line in enumerate(lines, 1):
        if re.search(r"useEffect\(\s*\(\)\s*=>\s*\{\s*\}", line):
            issues.append({
                "level": "info",
                "file": str(path),
                "line": i,
                "msg": "空的 useEffect hook",
            })
    return issues


# ── Type consistency checks ─────────────────────────────


def extract_interface_fields(text: str, name: str) -> dict[str, int]:
    """从 TS 文件中提取 interface/type 的字段名和行号"""
    fields = {}
    pattern = rf"(?:interface|type)\s+{re.escape(name)}\s*(?:=\s*)?\{{(.*?)\}}"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return fields
    body = m.group(1)
    # 计算起始行号
    start_line = text[:m.start()].count("\n") + 1
    for j, fline in enumerate(body.splitlines()):
        fm = re.match(r"\s*(\w+)\??\s*:", fline)
        if fm:
            fields[fm.group(1)] = start_line + j + 1
    return fields


def extract_class_fields(text: str, name: str) -> dict[str, int]:
    """从 TS class 中提取字段"""
    fields = {}
    pattern = rf"class\s+{re.escape(name)}\s*\{{(.*?)\n\s*constructor"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return fields
    body = m.group(1)
    start_line = text[:m.start()].count("\n") + 1
    for j, fline in enumerate(body.splitlines()):
        fm = re.match(r"\s+(\w+)\??\s*:", fline)
        if fm:
            fields[fm.group(1)] = start_line + j + 1
    return fields


def check_model_type_consistency(project: Path) -> list[dict]:
    """检查 model class 和 types interface 的字段一致性"""
    issues = []
    types_file = project / "src" / "types" / "index.ts"
    model_file = project / "src" / "models" / "Diary.ts"
    if not types_file.exists() or not model_file.exists():
        return issues

    types_text = types_file.read_text(encoding="utf-8")
    model_text = model_file.read_text(encoding="utf-8")

    # DiaryJSON interface vs Diary class
    json_fields = extract_interface_fields(types_text, "DiaryJSON")
    class_fields = extract_class_fields(model_text, "Diary")

    for f in json_fields:
        if f not in class_fields:
            issues.append({
                "level": "critical",
                "file": str(types_file),
                "line": json_fields[f],
                "msg": f"DiaryJSON 有字段 '{f}' 但 Diary class 中缺失",
            })
    for f in class_fields:
        if f not in json_fields:
            issues.append({
                "level": "warning",
                "file": str(model_file),
                "line": class_fields[f],
                "msg": f"Diary class 有字段 '{f}' 但 DiaryJSON 中缺失",
            })
    return issues


# ── Unused exports check ────────────────────────────────


def check_unused_exports(project: Path, files: list[Path]) -> list[dict]:
    """检测导出了但项目中没有其他文件导入的符号"""
    issues = []
    all_text = {}
    for f in files:
        all_text[f] = f.read_text(encoding="utf-8", errors="ignore")

    for f in files:
        text = all_text[f]
        for m in re.finditer(r"export\s+(?:const|function|class|type|interface)\s+(\w+)", text):
            name = m.group(1)
            line_no = text[:m.start()].count("\n") + 1
            # 检查其他文件是否引用了这个名字
            used = False
            for other_f, other_text in all_text.items():
                if other_f == f:
                    continue
                if re.search(rf"\b{re.escape(name)}\b", other_text):
                    used = True
                    break
            if not used:
                issues.append({
                    "level": "info",
                    "file": str(f),
                    "line": line_no,
                    "msg": f"导出的 '{name}' 未被其他文件引用",
                })
    return issues


# ── Runner ──────────────────────────────────────────────


def run_checks(project: Path, project_type: str) -> list[dict]:
    files = find_ts_files(project)
    if not files:
        print(f"⚠ 未找到 TS 文件: {project}")
        return []

    issues = []
    for f in files:
        text, lines = read_file(f)
        issues.extend(check_unused_imports(f, text, lines))
        issues.extend(check_empty_catch(f, text, lines))
        issues.extend(check_uncleared_timers(f, text, lines))
        issues.extend(check_fire_and_forget(f, text, lines))
        issues.extend(check_empty_files(f, text, lines))
        issues.extend(check_empty_hooks(f, text, lines))

    if project_type == "backend":
        issues.extend(check_model_type_consistency(project))

    issues.extend(check_unused_exports(project, files))
    return issues


def print_report(issues: list[dict], project: Path):
    if not issues:
        print(f"✓ {project.name}: 未发现问题")
        return

    by_level = {"critical": [], "warning": [], "info": []}
    for issue in issues:
        by_level[issue["level"]].append(issue)

    labels = {"critical": "🔴 严重", "warning": "🟡 警告", "info": "🔵 提示"}
    total = len(issues)
    print(f"\n{'='*60}")
    print(f"📋 {project.name} — 共 {total} 个问题")
    print(f"{'='*60}")

    for level in ["critical", "warning", "info"]:
        items = by_level[level]
        if not items:
            continue
        print(f"\n{labels[level]} ({len(items)})")
        for item in items:
            rel = Path(item["file"]).relative_to(project)
            print(f"  {rel}:{item['line']}  {item['msg']}")


def main():
    parser = argparse.ArgumentParser(description="Dear Diary 代码健康检查")
    parser.add_argument("--project", help="单个项目目录")
    parser.add_argument("--type", choices=["frontend", "backend"], help="项目类型")
    parser.add_argument("--frontend", help="前端项目目录")
    parser.add_argument("--backend", help="后端项目目录")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    all_issues = []

    if args.project:
        ptype = args.type or ("backend" if "server" in args.project else "frontend")
        project = Path(args.project).resolve()
        issues = run_checks(project, ptype)
        all_issues.extend(issues)
        if not args.json:
            print_report(issues, project)
    elif args.frontend or args.backend:
        for proj, ptype in [(args.frontend, "frontend"), (args.backend, "backend")]:
            if not proj:
                continue
            project = Path(proj).resolve()
            issues = run_checks(project, ptype)
            all_issues.extend(issues)
            if not args.json:
                print_report(issues, project)
    else:
        parser.print_help()
        return

    if args.json:
        print(json.dumps(all_issues, ensure_ascii=False, indent=2))
    elif all_issues:
        c = sum(1 for i in all_issues if i["level"] == "critical")
        w = sum(1 for i in all_issues if i["level"] == "warning")
        n = sum(1 for i in all_issues if i["level"] == "info")
        print(f"\n总计: {c} 严重 / {w} 警告 / {n} 提示")


if __name__ == "__main__":
    main()
