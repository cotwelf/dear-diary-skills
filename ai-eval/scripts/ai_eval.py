#!/usr/bin/env python3
"""AI 输出质量批量评估"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

STORE_DIR = Path.home() / ".dear-diary-skills" / "eval"
OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.1:8b"

EXTRACT_PROMPT = """分析这篇日记，提取其中的人物和关键词。

日记内容：{content}

请严格按以下 JSON 格式返回，不要有其他内容：
{{"people": ["人名1", "人名2"], "keywords": ["关键词1", "关键词2", "关键词3"]}}

注意：
- people：提取日记中提到的所有人名，不包括"我"
- keywords：提取 3-5 个核心关键词
- 如果没有人物，people 返回空数组
- 只返回 JSON，不要解释"""

REPLY_PROMPT = """你是一个温暖、真诚的朋友，正在和对方交换日记。

对方今天的日记：
{content}

回复要求：像给好朋友写信一样回复，100-200字。不要用套话开头。直接开始回复。"""

GEN_CASE_PROMPT = """生成一篇中文日记测试用例，用于测试 AI 日记分析系统。

要求：
- 日记内容 50-150 字，自然真实
- 包含 1-3 个人名
- 包含明确的情绪倾向（正面/负面/中性）
- 包含 3-5 个可提取的关键词

严格按以下 JSON 格式返回：
{{"input": "日记内容...", "expected": {{"people": ["人名"], "keywords": ["关键词"], "sentiment": "positive/negative/neutral"}}}}

只返回 JSON。"""


def ollama_chat(prompt: str, temperature: float = 0.7) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": temperature, "top_p": 0.9},
    }).encode()
    req = Request(f"{OLLAMA_URL}/api/chat", data=body,
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())["message"]["content"]
    except URLError:
        print("✗ Ollama 未运行，请先启动: ollama serve")
        sys.exit(1)


def parse_json_response(text: str) -> Optional[dict]:
    """尝试从 LLM 输出中提取 JSON"""
    # 先尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 尝试提取 ```json ... ``` 块
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 尝试找第一个 { ... }
    m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


# --- metrics ---

def precision_recall(expected: list, actual: list) -> dict:
    exp_set = set(expected)
    act_set = set(actual)
    if not act_set:
        return {"precision": 0, "recall": 0, "f1": 0}
    tp = len(exp_set & act_set)
    p = tp / len(act_set) if act_set else 0
    r = tp / len(exp_set) if exp_set else 0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}


# --- commands ---

def cmd_gen_cases(args):
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    cases = []

    if args.synthetic:
        print(f"用 LLM 生成 {args.count} 个测试用例...\n")
        for i in range(args.count):
            raw = ollama_chat(GEN_CASE_PROMPT, temperature=0.9)
            parsed = parse_json_response(raw)
            if parsed and "input" in parsed and "expected" in parsed:
                cases.append(parsed)
                print(f"  ✓ [{i+1}/{args.count}] {parsed['input'][:40]}...")
            else:
                print(f"  ✗ [{i+1}/{args.count}] 解析失败，跳过")
    elif args.source:
        source = Path(args.source)
        if not source.exists():
            print(f"✗ 文件不存在: {source}")
            sys.exit(1)
        diaries = json.loads(source.read_text(encoding="utf-8"))
        samples = random.sample(diaries, min(args.count, len(diaries)))
        print(f"从 {source.name} 采样 {len(samples)} 条，用 LLM 标注...\n")
        for i, d in enumerate(samples):
            content = d.get("content", "")
            if not content:
                continue
            label_prompt = f"""为这篇日记生成标注数据。

日记：{content}

返回 JSON：{{"people": ["人名"], "keywords": ["关键词"], "sentiment": "positive/negative/neutral"}}
只返回 JSON。"""
            raw = ollama_chat(label_prompt, temperature=0.3)
            parsed = parse_json_response(raw)
            if parsed:
                cases.append({"input": content, "expected": parsed})
                print(f"  ✓ [{i+1}] {content[:40]}...")
            else:
                print(f"  ✗ [{i+1}] 标注失败，跳过")
    else:
        print("请指定 --synthetic 或 --source")
        sys.exit(1)

    out = STORE_DIR / "cases.json"
    out.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ 已保存 {len(cases)} 个用例: {out}")


def cmd_run(args):
    cases_file = Path(args.cases)
    if not cases_file.exists():
        print(f"✗ 用例文件不存在: {cases_file}")
        sys.exit(1)

    cases = json.loads(cases_file.read_text(encoding="utf-8"))
    print(f"运行 {len(cases)} 个测试用例...\n")

    results = []
    for i, case in enumerate(cases):
        content = case["input"]
        expected = case["expected"]
        result = {"input": content[:50], "expected": expected}

        # 1. 人物/关键词提取
        t0 = time.time()
        raw = ollama_chat(EXTRACT_PROMPT.format(content=content), temperature=0.3)
        extract_time = time.time() - t0
        parsed = parse_json_response(raw)

        if parsed:
            actual_people = parsed.get("people", [])
            actual_keywords = parsed.get("keywords", [])
            result["extract"] = {
                "people": precision_recall(expected.get("people", []), actual_people),
                "keywords": precision_recall(expected.get("keywords", []), actual_keywords),
                "time": round(extract_time, 2),
                "actual": {"people": actual_people, "keywords": actual_keywords},
            }
        else:
            result["extract"] = {"error": "JSON 解析失败", "time": round(extract_time, 2)}

        # 2. 回复质量
        t0 = time.time()
        reply = ollama_chat(REPLY_PROMPT.format(content=content))
        reply_time = time.time() - t0
        result["reply"] = {
            "output": reply,
            "char_count": len(reply),
            "length_ok": 100 <= len(reply) <= 200,
            "time": round(reply_time, 2),
        }

        status = "✓" if result.get("extract", {}).get("people") else "△"
        print(f"  {status} [{i+1}/{len(cases)}] {content[:40]}... ({extract_time + reply_time:.1f}s)")
        results.append(result)

    # 保存结果
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "time": datetime.now().isoformat(),
        "total": len(results),
        "results": results,
    }

    # 汇总统计
    people_f1s = [r["extract"]["people"]["f1"] for r in results if "people" in r.get("extract", {})]
    kw_f1s = [r["extract"]["keywords"]["f1"] for r in results if "keywords" in r.get("extract", {})]
    times = [r["extract"].get("time", 0) + r["reply"].get("time", 0) for r in results]
    length_ok = sum(1 for r in results if r["reply"].get("length_ok"))
    errors = sum(1 for r in results if "error" in r.get("extract", {}))

    report["summary"] = {
        "people_f1_avg": round(sum(people_f1s) / len(people_f1s), 3) if people_f1s else 0,
        "keywords_f1_avg": round(sum(kw_f1s) / len(kw_f1s), 3) if kw_f1s else 0,
        "length_compliance": f"{length_ok}/{len(results)}",
        "avg_time": round(sum(times) / len(times), 2) if times else 0,
        "error_rate": f"{errors}/{len(results)}",
    }

    out = STORE_DIR / "report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*50}")
    print(f"📊 评估报告")
    print(f"{'='*50}")
    s = report["summary"]
    print(f"  人物提取 F1:    {s['people_f1_avg']}")
    print(f"  关键词提取 F1:  {s['keywords_f1_avg']}")
    print(f"  长度合规:       {s['length_compliance']}")
    print(f"  平均耗时:       {s['avg_time']}s")
    print(f"  解析失败:       {s['error_rate']}")
    print(f"\n✓ 完整报告: {out}")


def cmd_report(_args):
    report_file = STORE_DIR / "report.json"
    if not report_file.exists():
        print("暂无报告。先运行 run 命令。")
        return
    report = json.loads(report_file.read_text(encoding="utf-8"))
    s = report.get("summary", {})
    print(f"📊 最近一次评估 ({report['time'][:16]})")
    print(f"  用例数:         {report['total']}")
    print(f"  人物提取 F1:    {s.get('people_f1_avg', 'N/A')}")
    print(f"  关键词提取 F1:  {s.get('keywords_f1_avg', 'N/A')}")
    print(f"  长度合规:       {s.get('length_compliance', 'N/A')}")
    print(f"  平均耗时:       {s.get('avg_time', 'N/A')}s")
    print(f"  解析失败:       {s.get('error_rate', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(description="AI Eval")
    sub = parser.add_subparsers(dest="cmd")

    p_gen = sub.add_parser("gen-cases", help="生成测试用例")
    p_gen.add_argument("--count", type=int, default=5)
    p_gen.add_argument("--source", help="从现有日记文件采样")
    p_gen.add_argument("--synthetic", action="store_true", help="用 LLM 生成")

    p_run = sub.add_parser("run", help="批量运行评估")
    p_run.add_argument("--cases", default=str(STORE_DIR / "cases.json"))

    sub.add_parser("report", help="查看最近报告")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    {"gen-cases": cmd_gen_cases, "run": cmd_run, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
