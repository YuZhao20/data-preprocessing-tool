# 独自サーバーでのデプロイ方法

## 概要

Xserverなどの共有ホスティングやVPSでStreamlitアプリをデプロイする方法です。

**重要**: このガイドでは、GitHubリンクを完全に非表示にできる独自サーバーでのデプロイ方法を説明します。

## 方法1: Xserverなどの共有ホスティング（制限あり）

### 制限事項

- Python実行環境の制限
- ポート制限（通常、80/443のみ）
- バックグラウンドプロセスの実行制限

### 推奨: リバースプロキシを使用

Xserverでは直接Streamlitを実行するのは難しいため、**別のサーバー（VPSなど）でStreamlitを実行し、Xserverからリバースプロキシで接続**する方法が推奨されます。

## 方法2: VPSでデプロイ（推奨）

### 必要なもの

- VPS（例: AWS EC2、DigitalOcean、Linode、ConoHaなど）
- ドメイン（オプション、サブドメインでも可）

### ステップ1: VPSを準備

1. **VPSを契約**
   - 推奨: 1GB RAM以上、Ubuntu 20.04/22.04
   - 例: DigitalOcean Droplet、AWS EC2 t2.micro

2. **SSHで接続**
   ```bash
   ssh root@your-server-ip
   ```

### ステップ2: システムのセットアップ

```bash
# システムを更新
sudo apt update && sudo apt upgrade -y

# Python 3.8以上をインストール
sudo apt install python3 python3-pip python3-venv -y

# ユーザーを作成（オプション、セキュリティのため）
sudo adduser streamlit
sudo usermod -aG sudo streamlit
su - streamlit
```

### ステップ3: アプリケーションのセットアップ

```bash
# アプリケーションディレクトリを作成
mkdir -p ~/streamlit-app
cd ~/streamlit-app

# ファイルをアップロード（SCP、FTP、またはGit）
# 方法A: Gitからクローン
git clone https://github.com/YuZhao20/data-preprocessing-tool.git .
# または
# 方法B: SCPでアップロード
# ローカルから: scp -r /Users/yuzhao/data_preprocessing_project/* user@server:~/streamlit-app/

# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate

# 依存パッケージをインストール
pip install --upgrade pip
pip install -r requirements.txt
```

### ステップ4: systemdサービスとして設定

```bash
# サービスファイルを作成
sudo nano /etc/systemd/system/streamlit-app.service
```

以下の内容を記述:

```ini
[Unit]
Description=Streamlit Data Preprocessing App
After=network.target

[Service]
Type=simple
User=streamlit
WorkingDirectory=/home/streamlit/streamlit-app
Environment="PATH=/home/streamlit/streamlit-app/venv/bin"
ExecStart=/home/streamlit/streamlit-app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

サービスを有効化・開始:

```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit-app
sudo systemctl start streamlit-app
sudo systemctl status streamlit-app
```

### ステップ5: Nginxでリバースプロキシ設定

```bash
# Nginxをインストール
sudo apt install nginx -y

# 設定ファイルを作成
sudo nano /etc/nginx/sites-available/streamlit-app
```

以下の内容を記述:

```nginx
server {
    listen 80;
    server_name tools.yu-zhao.com;  # サブドメインまたはメインドメイン

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
        proxy_buffering off;
    }
}
```

シンボリックリンクを作成:

```bash
sudo ln -s /etc/nginx/sites-available/streamlit-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### ステップ6: SSL証明書の設定（Let's Encrypt）

```bash
# Certbotをインストール
sudo apt install certbot python3-certbot-nginx -y

# SSL証明書を取得
sudo certbot --nginx -d tools.yu-zhao.com

# 自動更新を設定
sudo certbot renew --dry-run
```

### ステップ7: ファイアウォール設定

```bash
# UFWを有効化
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 方法3: Dockerを使用（推奨・簡単）

### Dockerfileの作成

`Dockerfile`を作成:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### docker-compose.ymlの作成

```yaml
version: '3.8'

services:
  streamlit-app:
    build: .
    ports:
      - "8501:8501"
    restart: unless-stopped
    volumes:
      - ./data:/app/data
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### デプロイ

```bash
# DockerとDocker Composeをインストール
sudo apt install docker.io docker-compose -y

# アプリをビルド・起動
docker-compose up -d

# ログを確認
docker-compose logs -f
```

## 方法4: Xserverからリバースプロキシ（上級）

Xserverの`public_html`から別サーバーのStreamlitに接続する方法:

### `.htaccess`でリバースプロキシ（制限あり）

Xserverでは通常、`.htaccess`でのリバースプロキシは制限されています。

### 代替案: サブドメインを使用

1. **DNS設定でサブドメインを追加**
   - `tools.yu-zhao.com` → VPSのIPアドレス

2. **VPSでStreamlitを実行**（上記の方法2または3）

3. **XserverのHPからリンク**
   - `public_html/tools/data-preprocessing.html` から `https://tools.yu-zhao.com` にリンク

## トラブルシューティング

### アプリが起動しない

```bash
# ログを確認
sudo journalctl -u streamlit-app -f

# ポートが使用中か確認
sudo netstat -tlnp | grep 8501

# サービスを再起動
sudo systemctl restart streamlit-app
```

### メモリ不足

```bash
# メモリ使用量を確認
free -h

# スワップファイルを追加（必要に応じて）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Nginxエラー

```bash
# Nginxの設定をテスト
sudo nginx -t

# エラーログを確認
sudo tail -f /var/log/nginx/error.log
```

## セキュリティ考慮事項

1. **ファイアウォール設定**: 必要なポートのみ開放
2. **SSL証明書**: Let's EncryptでHTTPS化
3. **定期的な更新**: システムとパッケージを更新
4. **ログ監視**: 異常なアクセスを監視

## コスト目安

- **VPS**: 月額 $5-20（DigitalOcean、Linodeなど）
- **ドメイン**: 年額 $10-20（既に持っている場合は不要）
- **合計**: 月額 $5-20程度

## 推奨構成

1. **VPSでStreamlitを実行**（Docker使用推奨）
2. **Nginxでリバースプロキシ**
3. **Let's EncryptでSSL化**
4. **systemdまたはDocker Composeで自動起動**
