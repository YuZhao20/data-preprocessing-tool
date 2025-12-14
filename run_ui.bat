@echo off
REM Web UI起動スクリプト（Windows用）

echo データ前処理ツール - Web UI を起動します...
echo.

REM 必要なライブラリがインストールされているか確認
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Streamlitがインストールされていません。
    echo インストール中...
    pip install streamlit
)

REM Web UIを起動
echo ブラウザが自動的に開きます...
streamlit run app.py

pause

