#!/bin/bash
# 使用 GitHub API 创建仓库

# 注意：请在运行前设置环境变量 GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ 错误: 请设置 GITHUB_TOKEN 环境变量"
    echo "示例: export GITHUB_TOKEN=\"your_personal_access_token\""
    exit 1
fi

REPO_NAME="investment_research"
REPO_DESC="Investment Research System"

echo "正在创建 GitHub 仓库..."
response=$(curl -L \
  -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"${REPO_NAME}\",\"description\":\"${REPO_DESC}\",\"private\":false,\"has_issues\":true,\"has_projects\":true,\"has_wiki\":true}")

if echo "$response" | grep -q "repository already exists"; then
    echo "✅ 仓库已存在"
elif echo "$response" | grep -q "name"; then
    echo "✅ 仓库创建成功"
else
    echo "❌ 创建失败: $response"
    exit 1
fi