#!/bin/bash

# エラーが発生したら停止
set -e

echo "Hue照明コントロールWebアプリケーションのデプロイを開始します..."

# 必要なパッケージのインストール
echo "必要なシステムパッケージをインストールしています..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip nginx

# アプリケーションディレクトリの作成
echo "アプリケーションディレクトリを作成しています..."
mkdir -p ~/hue_controller
cd ~/hue_controller

# 現在のディレクトリからファイルをコピー
echo "アプリケーションファイルをコピーしています..."
cp -r $PWD/* ~/hue_controller/

# セットアップスクリプトの実行
echo "セットアップスクリプトを実行しています..."
cd ~/hue_controller
chmod +x setup.sh
./setup.sh

# Gunicornのインストール
echo "Gunicornをインストールしています..."
source venv/bin/activate
pip install gunicorn

# systemdサービスファイルの設定
echo "systemdサービスを設定しています..."
sudo cp hue-controller.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hue-controller.service
sudo systemctl start hue-controller.service

# Nginxの設定
echo "Nginxを設定しています..."
sudo bash -c 'cat > /etc/nginx/sites-available/hue-controller << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF'

# Nginxの設定を有効化
sudo ln -sf /etc/nginx/sites-available/hue-controller /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "デプロイが完了しました！"
echo "ブラウザで http://サーバーのIPアドレス にアクセスしてください。"
echo "Hueブリッジのアドレスを設定するには、設定ページにアクセスしてください。" 