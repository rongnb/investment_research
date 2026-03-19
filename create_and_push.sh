#!/bin/bash
# 创建仓库和推送脚本

# 注意：请在运行前设置环境变量 GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ 错误: 请设置 GITHUB_TOKEN 环境变量"
    echo "示例: export GITHUB_TOKEN=\"your_personal_access_token\""
    exit 1
fi

GITHUB_USER="rongnb"
REPO_NAME="investment_research"
REPO_DESC="Investment Research System"

# 1. 创建仓库
echo "1. 在 GitHub 上创建仓库..."
curl -s -L \
  -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"${REPO_NAME}\",\"description\":\"${REPO_DESC}\",\"private\":false,\"has_issues\":true,\"has_projects\":true,\"has_wiki\":true}" > /dev/null

# 2. 添加远程仓库
echo "2. 配置远程仓库..."
git remote add origin https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git

# 3. 推送到 GitHub
echo "3. 推送到 GitHub..."
git push -u origin main

echo "✅ 推送成功！"
echo "仓库地址: https://github.com/${GITHUB_USER}/${REPO_NAME}"