#!/bin/bash

# 変更をGitHubにプッシュするスクリプト

echo "=========================================="
echo "変更をGitHubにプッシュ"
echo "=========================================="

cd /Users/yuzhao/data_preprocessing_project

# 変更を確認
echo "変更されたファイル:"
git status --short
echo ""

# 変更があるか確認
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ 変更はありません。すべてコミット済みです。"
    exit 0
fi

# すべての変更を追加
echo "変更をステージングしています..."
git add .

# 変更内容を表示
echo ""
echo "コミットする変更:"
git status --short
echo ""

# コミット
echo "コミットを作成しています..."
git commit -m "Update: プライバシー設定の追加（メニュー非表示、README最小化）"

# リモートを確認
echo ""
echo "リモートリポジトリ:"
git remote -v
echo ""

# プッシュ方法を選択
echo "=========================================="
echo "プッシュ方法を選択してください:"
echo "=========================================="
echo "1. Personal Access Tokenを使用（推奨）"
echo "2. 既に認証済み（Keychainに保存済み）"
echo "3. キャンセル"
echo ""
read -p "選択 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Personal Access Tokenを入力してください:"
        read -sp "Token: " TOKEN
        echo ""
        
        if [ -z "$TOKEN" ]; then
            echo "❌ トークンが入力されていません"
            exit 1
        fi
        
        # リモートURLを更新
        git remote set-url origin https://${TOKEN}@github.com/YuZhao20/data-preprocessing-tool.git
        
        # プッシュ
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
        # 通常のプッシュ（Keychainに保存されている場合）
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
    3)
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
echo "2. アプリのメニューが非表示になっているか確認"
echo ""

