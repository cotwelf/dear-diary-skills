#!/usr/bin/env python3
"""Prompt 版本管理 + A/B 测试 + LLM-as-judge"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

STORE_DIR = Path.home() / ".dear-diary-skills" / "prompt-lab" / "versions"
OLLAMA_URL = "http://localhost:11434"
MODEL = "llama3.1:8b"


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


# --- commands ---

def cmd_list(_args):
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    versions = sorted(STORE_DIR.glob("*.json"))
    if not versions:
        print("暂无 prompt 版本。用 save 命令保存第一个版本。")
        return
    print(f"共 {len(versions)} 个版本:\n")
    for v in versions:
        meta = json.loads(v.read_text(encoding="utf-8"))
        print(f"  {meta['name']:20s}  type={meta['type']:8s}  {meta['created']}")


def cmd_save(args):
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    prompt_text = Path(args.file).read_text(encoding="utf-8").strip()
    meta = {
        "name": args.name,
        "type": args.type,
        "prompt": prompt_text,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    out = STORE_DIR / f"{args.name}.json"
    out.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 已保存: {out}")


def load_version(name: str) -> dict:
    path = STORE_DIR / f"{name}.json"
    if not path.exists():
        print(f"✗ 版本不存在: {name}")
        sys.exit(1)
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_test(args):
    v1 = load_version(args.v1)
    v2 = load_version(args.v2)
    diary = args.input

    print(f"输入: {diary}\n")
    for label, ver in [("A", v1), ("B", v2)]:
        prompt = ver["prompt"].replace("${diaryContent}", diary)
        # 简单替换时间占位符
        prompt = prompt.replace("${now}", datetime.now().strftime("%Y年%m月%d日"))
        prompt = prompt.replace("${memorySection}", "")
        prompt = prompt.replace("${similarSection}", "")

        t0 = time.time()
        output = ollama_chat(prompt)
        elapsed = time.time() - t0

        print(f"--- [{label}] {ver['name']} ({elapsed:.1f}s) ---")
        print(output)
        print(f"字数: {len(output)}\n")


def cmd_judge(args):
    v1 = load_version(args.v1)
    v2 = load_version(args.v2)
    diary = args.input

    outputs = {}
    for ver in [v1, v2]:
        prompt = ver["prompt"].replace("${diaryContent}", diary)
        prompt = prompt.replace("${now}", datetime.now().strftime("%Y年%m月%d日"))
        prompt = prompt.replace("${memorySection}", "")
        prompt = prompt.replace("${similarSection}", "")
        outputs[ver["name"]] = ollama_chat(prompt)

    judge_prompt = f"""你是一个 AI 回复质量评审员。下面有两个 AI 对同一篇日记的回复，请从 4 个维度打分（1-5分）。

## 日记内容
{diary}

## 回复 A（{v1['name']}）
{outputs[v1['name']]}

## 回复 B（{v2['name']}）
{outputs[v2['name']]}

## 评分维度
1. 自然度：像朋友聊天，不像 AI 生成
2. 共情度：理解情绪，不说空话套话
3. 具体性：回应日记中的具体细节
4. 长度合规：100-200 字为满分

请严格按以下 JSON 格式返回，不要有其他内容：
{{
  "A": {{"自然度": N, "共情度": N, "具体性": N, "长度合规": N, "总分": N}},
  "B": {{"自然度": N, "共情度": N, "具体性": N, "长度合规": N, "总分": N}},
  "winner": "A 或 B",
  "reason": "一句话说明为什么"
}}"""

    print(f"输入: {diary}\n")
    print(f"A = {v1['name']}, B = {v2['name']}\n")
    print("评分中...\n")

    result = ollama_chat(judge_prompt, temperature=0.3)
    print(result)

    # 保存评分记录
    record_dir = Path.home() / ".dear-diary-skills" / "prompt-lab" / "judgements"
    record_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "time": datetime.now().isoformat(),
        "input": diary,
        "v1": v1["name"], "v2": v2["name"],
        "output_a": outputs[v1["name"]],
        "output_b": outputs[v2["name"]],
        "judgement": result,
    }
    out = record_dir / f"{int(time.time())}.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ 评分记录: {out}")


def main():
    parser = argparse.ArgumentParser(description="Prompt Lab")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="列出所有版本")

    p_save = sub.add_parser("save", help="保存 prompt 版本")
    p_save.add_argument("--name", required=True)
    p_save.add_argument("--file", required=True, help="prompt 文本文件路径")
    p_save.add_argument("--type", default="reply", choices=["reply", "summary", "extract"])

    p_test = sub.add_parser("test", help="A/B 对比测试")
    p_test.add_argument("--v1", required=True)
    p_test.add_argument("--v2", required=True)
    p_test.add_argument("--input", required=True, help="测试日记内容")

    p_judge = sub.add_parser("judge", help="LLM-as-judge 评分")
    p_judge.add_argument("--v1", required=True)
    p_judge.add_argument("--v2", required=True)
    p_judge.add_argument("--input", required=True, help="测试日记内容")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    {"list": cmd_list, "save": cmd_save, "test": cmd_test, "judge": cmd_judge}[args.cmd](args)


if __name__ == "__main__":
    main()
