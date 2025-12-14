# Xserverでのデプロイ - クイックスタートガイド

## 最も簡単な方法: Xserver VPSを使用

### 1. Xserver VPSを契約

1. https://www.xserver.ne.jp/ にアクセス
2. **VPSプラン**を選択
3. **推奨設定**:
   - メモリ: 2GB以上
   - CPU: 2コア以上
   - OS: Ubuntu 22.04

### 2. VPSにSSH接続

```bash
ssh root@your-vps-ip
```

### 3. アプリをセットアップ

```bash
# システムを更新
apt update && apt upgrade -y

# 必要なパッケージをインストール
apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx

# アプリをクローン
mkdir -p /root/streamlit-app
cd /root/streamlit-app
git clone https://github.com/YuZhao20/data-preprocessing-tool.git .

# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. systemdサービスとして設定

```bash
# サービスファイルを作成
cat > /etc/systemd/system/streamlit-app.service << 'EOF'
[Unit]
Description=Streamlit Data Preprocessing App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/streamlit-app
Environment="PATH=/root/streamlit-app/venv/bin"
ExecStart=/root/streamlit-app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# サービスを有効化・起動
systemctl daemon-reload
systemctl enable streamlit-app
systemctl start streamlit-app
systemctl status streamlit-app
```

### 5. Nginxでリバースプロキシ設定

```bash
# 設定ファイルを作成（tools.yu-zhao.comは実際のドメインに変更）
cat > /etc/nginx/sites-available/streamlit-app << 'EOF'
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
        proxy_buffering off;
    }
}
EOF

# シンボリックリンクを作成
ln -s /etc/nginx/sites-available/streamlit-app /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 6. SSL証明書を設定

```bash
# SSL証明書を取得（tools.yu-zhao.comは実際のドメインに変更）
certbot --nginx -d tools.yu-zhao.com
```

### 7. ドメインのDNS設定

1. **Xserverのコントロールパネル**にログイン
2. **ドメイン設定** → **DNSレコード設定**
3. **Aレコードを追加**:
   - ホスト名: `tools`
   - タイプ: `A`
   - 値: VPSのIPアドレス

### 完了！

`https://tools.yu-zhao.com` にアクセスして、アプリが表示されることを確認してください。

---

## トラブルシューティング

### アプリが起動しない

```bash
# ログを確認
journalctl -u streamlit-app -f

# サービスを再起動
systemctl restart streamlit-app
```

### Nginxエラー

```bash
# 設定をテスト
nginx -t

# エラーログを確認
tail -f /var/log/nginx/error.log
```

---

詳細な手順は `XSERVER_DEPLOY_SIMPLE.md` を参照してください。

