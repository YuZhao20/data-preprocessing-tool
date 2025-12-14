#!/bin/bash

# GitHubリポジトリへの初回プッシュスクリプト
# 使用方法: ./GITHUB_SETUP.sh YOUR_REPO_NAME

if [ -z "$1" ]; then
    echo "エラー: リポジトリ名を指定してください"
    echo "使用方法: ./GITHUB_SETUP.sh YOUR_REPO_NAME"
    echo "例: ./GITHUB_SETUP.sh data-preprocessing-tool"
    exit 1
fi

REPO_NAME=$1
GITHUB_USER="YuZhao20"

echo "=========================================="
echo "GitHubリポジトリセットアップ"
echo "=========================================="
echo "リポジトリ名: $REPO_NAME"
echo "GitHubユーザー: $GITHUB_USER"
echo ""

# 現在のディレクトリを確認
if [ ! -f "app.py" ]; then
    echo "エラー: app.pyが見つかりません。"
    echo "このスクリプトは data_preprocessing_project ディレクトリで実行してください。"
    exit 1
fi

# Gitが初期化されているか確認
if [ ! -d ".git" ]; then
    echo "Gitリポジトリを初期化しています..."
    git init
fi

# すべてのファイルを追加
echo "ファイルを追加しています..."
git add .

# 初回コミット（まだコミットがない場合）
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "初回コミットを作成しています..."
    git commit -m "Initial commit: データ前処理ツール"
else
    echo "既存のコミットがあります。新しい変更をコミットしますか？ (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        git commit -m "Update: データ前処理ツールの更新"
    fi
fi

# リモートリポジトリを設定
echo ""
echo "リモートリポジトリを設定しています..."
git remote remove origin 2>/dev/null
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"

# メインブランチを設定
git branch -M main

echo ""
echo "=========================================="
echo "次のステップ:"
echo "=========================================="
echo "1. GitHubでリポジトリを作成してください:"
echo "   https://github.com/new"
echo "   リポジトリ名: $REPO_NAME"
echo "   Public を選択"
echo ""
echo "2. リポジトリ作成後、以下のコマンドでプッシュ:"
echo "   git push -u origin main"
echo ""
echo "3. Streamlit Cloudでデプロイ:"
echo "   https://streamlit.io/cloud"
echo "=========================================="

