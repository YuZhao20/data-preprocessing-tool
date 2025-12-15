#!/bin/bash

# Personal Access Tokenを使用してGitHubにプッシュするスクリプト

cd /Users/yuzhao/data_preprocessing_project

echo "=========================================="
echo "GitHubにプッシュ（Personal Access Token使用）"
echo "=========================================="
echo ""

# Personal Access Tokenの入力
echo "Personal Access Tokenを入力してください:"
echo "（GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic)）"
echo "スコープ: repo を選択してください"
echo ""
read -sp "Token: " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo "❌ トークンが入力されていません"
    exit 1
fi

# リモートURLを更新
echo "リモートURLを更新しています..."
git remote set-url origin https://${TOKEN}@github.com/YuZhao20/data-preprocessing-tool.git

# プッシュ
echo ""
echo "GitHubにプッシュしています..."
if git push origin main; then
    echo ""
    echo "✅ プッシュ成功！"
    echo ""
    echo "Streamlit Cloudが自動的に再デプロイを開始します（数分かかります）"
    echo ""
    echo "確認:"
    echo "  - GitHub: https://github.com/YuZhao20/data-preprocessing-tool"
    echo "  - Streamlit Cloud: https://streamlit.io/cloud"
else
    echo ""
    echo "❌ プッシュに失敗しました"
    echo "トークンが正しいか確認してください"
    exit 1
fi

