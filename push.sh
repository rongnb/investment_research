#!/bin/bash
# 用于推送到 GitHub 的脚本
# 使用前请确保已安装 gh 客户端或配置好 Git 凭证

# 配置变量
REPO="investment_research"
BRANCH="main"
REMOTE="origin"

# 检查是否配置了远程仓库
if ! git remote -v | grep -q "$REMOTE"; then
    echo "未配置远程仓库，请先执行："
    echo "  git remote add $REMOTE https://github.com/rongnb/$REPO.git"
    exit 1
fi

# 检查工作区状态
if [ -n "$(git status --porcelain)" ]; then
    echo "工作区有未提交的更改，请先提交"
    git status
    exit 1
fi

# 尝试推送
echo "正在推送到 $REMOTE $BRANCH..."
if git push -u $REMOTE $BRANCH; then
    echo "✅ 推送成功！"
else
    echo "❌ 推送失败，请检查网络连接或GitHub访问权限"
    exit 1
fi
