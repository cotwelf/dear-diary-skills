#!/bin/zsh
# 将 dear-diary-skills 安装到对应项目的 .claude/commands/ 目录
# 双击或执行: ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND="$HOME/dev/dear-diary"
BACKEND="$HOME/dev/dear-diary-server"

install_skill() {
  local skill="$1"
  local target="$2"
  local cmd_dir="$target/.claude/commands"
  local skill_md="$SCRIPT_DIR/$skill/SKILL.md"
  local script_dir="$SCRIPT_DIR/$skill/scripts"

  if [ ! -d "$target" ]; then
    echo "⚠ 项目不存在，跳过: $target"
    return
  fi

  if [ ! -f "$skill_md" ]; then
    echo "⚠ SKILL.md 不存在，跳过: $skill"
    return
  fi

  mkdir -p "$cmd_dir"

  # 复制 SKILL.md → .claude/commands/{skill}.md
  cp "$skill_md" "$cmd_dir/$skill.md"
  echo "✓ $skill.md → $cmd_dir/"

  # 复制 scripts/ 目录（如果有）
  if [ -d "$script_dir" ]; then
    local target_scripts="$target/.claude/commands/$skill-scripts"
    mkdir -p "$target_scripts"
    cp "$script_dir"/* "$target_scripts/"
    echo "  ✓ scripts → $target_scripts/"
  fi
}

install_skill "taro-page"       "$FRONTEND"
install_skill "diary-doctor"    "$FRONTEND"
install_skill "diary-doctor"    "$BACKEND"
install_skill "api-sync-check"  "$FRONTEND"
install_skill "ai-prompt-lab"   "$BACKEND"
install_skill "ai-eval"         "$BACKEND"

echo ""
echo "安装完成。可用命令："
echo "  前端 (dear-diary):        /taro-page, /diary-doctor, /api-sync-check"
echo "  后端 (dear-diary-server): /ai-prompt-lab, /ai-eval, /diary-doctor"
