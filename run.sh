#!/bin/bash

# エラーが発生したら停止
set -e

# 仮想環境のアクティベート
source venv/bin/activate

# アプリケーションの起動
echo "Hue照明コントロールWebアプリケーションを起動しています..."
python app.py

# 終了時のメッセージ
echo "アプリケーションが終了しました。" 