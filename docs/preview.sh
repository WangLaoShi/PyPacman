#!/bin/bash
# 快速预览教程网站

echo "=== PyPacman 教程网站预览 ==="
echo ""
echo "正在打开浏览器..."
echo ""

# macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    open tutorial-site.html
# Linux
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open tutorial-site.html
# Windows (Git Bash)
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    start tutorial-site.html
fi

echo "✓ 已在默认浏览器中打开 tutorial-site.html"
echo ""
echo "提示："
echo "  - 截图位于 docs/screenshots/ 目录"
echo "  - 如需重新截图，运行: python auto_screenshot.py"
echo "  - 发布为 Qoder Site 前，请确保所有截图已生成"
