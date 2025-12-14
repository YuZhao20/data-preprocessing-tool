#!/bin/bash

# GitHubにプッシュするスクリプト
# Personal Access Tokenを使用

echo "=========================================="
echo "GitHubにプッシュ"
echo "=========================================="

cd /Users/yuzhao/data_preprocessing_project

# リモートを確認
echo "リモートリポジトリ:"
git remote -v
echo ""

# 状態を確認
echo "現在の状態:"
git status
echo ""

# Personal Access Tokenの入力
echo "=========================================="
echo "Personal Access Tokenを入力してください"
echo "（GitHub → Settings → Developer settings → Personal access tokens）"
echo "=========================================="
read -sp "Personal Access Token: " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo "エラー: トークンが入力されていません"
    exit 1
fi

# リモートURLを更新（トークンを含む）
echo "リモートURLを更新しています..."
git remote set-url origin https://${TOKEN}@github.com/YuZhao20/data-preprocessing-tool.git

# プッシュ
echo ""
echo "GitHubにプッシュしています..."
if git push -u origin main; then
    echo ""
    echo "✅ プッシュ成功！"
    echo ""
    echo "次のステップ:"
    echo "1. https://streamlit.io/cloud にアクセス"
    echo "2. GitHubアカウントでログイン"
    echo "3. リポジトリを選択してデプロイ"
else
    echo ""
    echo "❌ プッシュに失敗しました"
    echo "トークンが正しいか確認してください"
    exit 1
fi

