# Streamlitアプリのデプロイ方法

## 概要

Streamlitアプリを個人HP（yu-zhao.com）に統合する方法を説明します。

## 方法1: Streamlit Cloud（推奨・最も簡単）

### メリット
- 無料
- 自動デプロイ
- HTTPS対応
- 簡単なセットアップ

### 手順

1. **GitHubにリポジトリを作成**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/data-preprocessing-tool.git
   git push -u origin main
   ```

2. **Streamlit Cloudでデプロイ**
   - https://streamlit.io/cloud にアクセス
   - GitHubアカウントでログイン
   - リポジトリを選択
   - 自動的にデプロイされます

3. **HPからリンク**
   - `public_html/tools/data-preprocessing.html` を作成:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <meta http-equiv="refresh" content="0; url=https://your-app-name.streamlit.app">
       <title>データ前処理ツール</title>
   </head>
   <body>
       <p>リダイレクト中... <a href="https://your-app-name.streamlit.app">こちらをクリック</a></p>
   </body>
   </html>
   ```

## 方法2: サブドメインでデプロイ（独自ドメイン使用）

### メリット
- 独自ドメイン（例: tools.yu-zhao.com）
- 完全な制御

### 手順

1. **サーバーにPython環境をセットアップ**
   ```bash
   # Python 3.8以上をインストール
   python3 --version
   
   # 仮想環境を作成
   python3 -m venv venv
   source venv/bin/activate
   
   # 依存パッケージをインストール
   pip install -r requirements.txt
   ```

2. **systemdサービスとして設定**
   `/etc/systemd/system/streamlit-app.service` を作成:
   ```ini
   [Unit]
   Description=Streamlit Data Preprocessing App
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/data_preprocessing_project
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/streamlit run app.py --server.port=8501 --server.address=127.0.0.1
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

3. **Nginxでリバースプロキシ設定**
   `/etc/nginx/sites-available/streamlit-app` を作成:
   ```nginx
   server {
       listen 80;
       server_name tools.yu-zhao.com;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 86400;
       }
   }
   ```

4. **サービスを開始**
   ```bash
   sudo systemctl enable streamlit-app
   sudo systemctl start streamlit-app
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## 方法3: 既存サーバーで直接実行（Xserver等）

### Xserverの場合

1. **SSHでサーバーに接続**
2. **Python環境をセットアップ**
   ```bash
   # ユーザーディレクトリに移動
   cd ~
   
   # プロジェクトをアップロード（FTPまたはgit）
   # 仮想環境を作成
   python3 -m venv venv
   source venv/bin/activate
   
   # 依存パッケージをインストール
   pip install -r requirements.txt
   ```

3. **screenまたはtmuxでバックグラウンド実行**
   ```bash
   screen -S streamlit
   source venv/bin/activate
   streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   # Ctrl+A, D でデタッチ
   ```

4. **`.htaccess`でリバースプロキシ設定**
   `public_html/tools/.htaccess` を作成（ただし、Xserverでは通常Nginxリバースプロキシは使用不可）

### 代替案: ポートフォワーディング

Xserverなどの共有ホスティングでは、直接Streamlitを実行するのは難しい場合があります。
その場合は、**Streamlit Cloudを使用し、HPからリンクする方法（方法1）が最も簡単**です。

## 方法4: iframeで埋め込み（非推奨）

Streamlitはiframeでの埋め込みを公式にサポートしていませんが、技術的には可能です。

```html
<iframe src="https://your-app-name.streamlit.app" 
        width="100%" 
        height="800px" 
        frameborder="0">
</iframe>
```

**注意**: セキュリティとパフォーマンスの問題があるため、推奨しません。

## 推奨構成

### 最も簡単な方法（推奨）
1. **Streamlit Cloudでデプロイ**（無料、自動HTTPS）
2. **HPのtoolsフォルダにリダイレクトページを作成**
3. **メインページからリンクを追加**

### ファイル構成例

```
public_html/
├── index.php
├── tools/
│   ├── data-preprocessing.html  ← リダイレクトページ
│   └── pdf-redactor.html
└── ...
```

## セキュリティ考慮事項

1. **データの取り扱い**
   - アップロードされたデータは一時ファイルとしてのみ保存
   - セッション終了時に自動削除

2. **HTTPSの使用**
   - Streamlit Cloudは自動でHTTPS対応
   - 独自サーバーの場合はSSL証明書を設定

3. **アクセス制限（オプション）**
   - Streamlitの認証機能を使用
   - または、NginxでBasic認証を設定

## トラブルシューティング

### ポートが使用中
```bash
# ポートを確認
lsof -i :8501
# 別のポートを使用
streamlit run app.py --server.port=8502
```

### メモリ不足
- 大きなデータセットの処理を制限
- タイムアウトを設定

## 参考リンク

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)

