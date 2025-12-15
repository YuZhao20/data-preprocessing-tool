#!/bin/bash

# GitHubにプッシュするスクリプト

cd /Users/yuzhao/data_preprocessing_project

echo "=========================================="
echo "GitHubにプッシュ"
echo "=========================================="
echo ""

# 現在の状態を確認
echo "現在の状態:"
git status --short
echo ""

# リモートを確認
echo "リモートリポジトリ:"
git remote -v
echo ""

# プッシュ方法を選択
echo "=========================================="
echo "プッシュ方法を選択してください:"
echo "=========================================="
echo "1. Personal Access Tokenを使用（推奨）"
echo "2. GitHub CLI (gh) を使用"
echo "3. 既に認証済み（試行）"
echo "4. キャンセル"
echo ""
read -p "選択 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Personal Access Tokenを入力してください:"
        echo "（GitHub → Settings → Developer settings → Personal access tokens）"
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
        echo "GitHubにプッシュしています..."
        if git push -u origin main; then
            echo ""
            echo "✅ プッシュ成功！"
            echo ""
            echo "Streamlit Cloudが自動的に再デプロイを開始します（数分かかります）"
        else
            echo ""
            echo "❌ プッシュに失敗しました"
            exit 1
        fi
        ;;
    2)
        # GitHub CLIを使用
        if command -v gh &> /dev/null; then
            echo "GitHub CLIで認証しています..."
            gh auth login
            echo "GitHubにプッシュしています..."
            if git push -u origin main; then
                echo ""
                echo "✅ プッシュ成功！"
            else
                echo ""
                echo "❌ プッシュに失敗しました"
                exit 1
            fi
        else
            echo "❌ GitHub CLI (gh) がインストールされていません"
            echo "インストール: brew install gh"
            exit 1
        fi
        ;;
    3)
        # 通常のプッシュ（既に認証済みの場合）
        echo "GitHubにプッシュしています..."
        if git push -u origin main; then
            echo ""
            echo "✅ プッシュ成功！"
            echo ""
            echo "Streamlit Cloudが自動的に再デプロイを開始します（数分かかります）"
        else
            echo ""
            echo "❌ プッシュに失敗しました"
            echo "認証が必要な場合は、オプション1を選択してください"
            exit 1
        fi
        ;;
    4)
        echo "キャンセルしました"
        exit 0
        ;;
    *)
        echo "無効な選択です"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "次のステップ:"
echo "=========================================="
echo "1. Streamlit Cloudで再デプロイを確認:"
echo "   https://streamlit.io/cloud"
echo ""
echo "2. GitHubリポジトリを確認:"
echo "   https://github.com/YuZhao20/data-preprocessing-tool"
echo ""

