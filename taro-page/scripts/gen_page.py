#!/usr/bin/env python3
"""Taro 页面脚手架生成器"""

import argparse
import re
import sys
from pathlib import Path


def gen_tsx(name: str) -> str:
    cap = name.replace("-", " ").title().replace(" ", "")
    return f"""import {{ useState }} from 'react'
import {{ View, Text }} from '@tarojs/components'
import Taro, {{ useRouter }} from '@tarojs/taro'
import './{name.replace(name, "index")}.scss'

function {cap}() {{
  const router = useRouter()

  return (
    <View className='page-{name}'>
      <Text>{cap}</Text>
    </View>
  )
}}

export default {cap}
"""


def gen_scss(name: str) -> str:
    return f""".page-{name} {{
  min-height: 100vh;
  padding: 32rpx;
  background: linear-gradient(180deg, #FFF5E6 0%, #FFFFFF 100%);
}}
"""


def gen_config(title: str) -> str:
    return f"""export default definePageConfig({{
  navigationBarTitleText: '{title}',
}})
"""


def register_route(app_config: Path, name: str) -> bool:
    text = app_config.read_text(encoding="utf-8")
    route = f"pages/{name}/index"
    if route in text:
        print(f"  路由已存在: {route}")
        return False

    # 在 pages 数组最后一项后插入
    pattern = r"(pages:\s*\[.*?)((\s*)'pages/[^']+',?)(\s*\])"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        print("  ⚠ 无法解析 app.config.ts，请手动添加路由")
        return False

    indent = match.group(3)
    last_entry_end = match.end(4) - len(match.group(4))
    insert = f"{indent}'{route}',"
    new_text = text[: match.end(2)] + insert + text[match.end(2) :]
    app_config.write_text(new_text, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="生成 Taro 页面脚手架")
    parser.add_argument("--name", required=True, help="页面目录名")
    parser.add_argument("--title", required=True, help="导航栏标题")
    parser.add_argument("--project", default=".", help="项目根目录")
    args = parser.parse_args()

    project = Path(args.project).resolve()
    pages_dir = project / "src" / "pages" / args.name

    if pages_dir.exists():
        print(f"✗ 目录已存在: {pages_dir}")
        sys.exit(1)

    pages_dir.mkdir(parents=True)

    (pages_dir / "index.tsx").write_text(gen_tsx(args.name), encoding="utf-8")
    print(f"  ✓ {pages_dir / 'index.tsx'}")

    (pages_dir / "index.scss").write_text(gen_scss(args.name), encoding="utf-8")
    print(f"  ✓ {pages_dir / 'index.scss'}")

    (pages_dir / "index.config.ts").write_text(gen_config(args.title), encoding="utf-8")
    print(f"  ✓ {pages_dir / 'index.config.ts'}")

    app_config = project / "src" / "app.config.ts"
    if app_config.exists():
        if register_route(app_config, args.name):
            print(f"  ✓ 路由已注册: pages/{args.name}/index")
    else:
        print(f"  ⚠ 未找到 app.config.ts，请手动注册路由")

    print(f"\n✓ 页面 {args.name} 创建完成")


if __name__ == "__main__":
    main()
