#!/bin/bash
# 用于临时设置 Git 凭证的脚本

# 设置 Git 凭证存储
git config --global credential.helper store

# 注意：请在运行前设置环境变量 GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ 错误: 请设置 GITHUB_TOKEN 环境变量"
    echo "示例: export GITHUB_TOKEN=\"your_personal_access_token\""
    exit 1
fi

# 设置个人访问令牌（仅用于此会话）
git remote set-url origin "https://${GITHUB_TOKEN}@github.com/rongnb/investment_research.git"