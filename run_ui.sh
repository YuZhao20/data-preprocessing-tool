#!/bin/bash
# Web UI起動スクリプト

echo "データ前処理ツール - Web UI を起動します..."
echo ""

# 必要なライブラリがインストールされているか確認
if ! python -c "import streamlit" 2>/dev/null; then
    echo "Streamlitがインストールされていません。"
    echo "インストール中..."
    pip install streamlit
fi

# Web UIを起動
echo "ブラウザが自動的に開きます..."
streamlit run app.py

