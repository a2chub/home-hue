#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from phue import Bridge
from dotenv import load_dotenv
import logging
import requests
import socket
import time

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)

# Hueブリッジの設定
bridge_ip = os.getenv('HUE_BRIDGE_IP')
bridge = None

def discover_bridge():
    """Hueブリッジを自動検出する関数"""
    try:
        response = requests.get('https://discovery.meethue.com/')
        bridges = response.json()
        if bridges:
            return bridges[0]['internalipaddress']
    except Exception as e:
        logger.error(f"ブリッジ検出エラー: {e}")
    return None

def connect_to_bridge():
    """Hueブリッジに接続する関数"""
    global bridge, bridge_ip
    
    # 環境変数からIPアドレスを取得
    if bridge_ip:
        try:
            bridge = Bridge(bridge_ip)
            # 初回接続時はブリッジの物理ボタンを押す必要がある
            bridge.connect()
            logger.info(f"ブリッジ {bridge_ip} に接続しました")
            return True
        except Exception as e:
            logger.error(f"ブリッジ接続エラー: {e}")
    
    # IPアドレスが設定されていないか、接続に失敗した場合は自動検出を試みる
    discovered_ip = discover_bridge()
    if discovered_ip:
        try:
            bridge_ip = discovered_ip
            bridge = Bridge(bridge_ip)
            # 初回接続時はブリッジの物理ボタンを押す必要がある
            bridge.connect()
            logger.info(f"ブリッジ {bridge_ip} に接続しました")
            # 検出したIPアドレスを.envファイルに保存
            with open('.env', 'w') as f:
                f.write(f"HUE_BRIDGE_IP={bridge_ip}\n")
            return True
        except Exception as e:
            logger.error(f"ブリッジ接続エラー: {e}")
    
    return False

@app.route('/')
def index():
    """メインページを表示"""
    global bridge
    
    # ブリッジに接続されていない場合は接続を試みる
    if bridge is None:
        if not connect_to_bridge():
            return render_template('setup.html', error="Hueブリッジに接続できませんでした。")
    
    try:
        # 照明の情報を取得
        lights = bridge.get_light_objects('id')
        light_data = []
        
        for light_id, light in lights.items():
            light_info = bridge.get_light(light_id)
            light_data.append({
                'id': light_id,
                'name': light_info['name'],
                'on': light_info['state']['on'],
                'brightness': light_info['state'].get('bri', 0),
                'reachable': light_info['state']['reachable'],
                'type': light_info['type'],
                'has_color': 'hue' in light_info['state'] and 'sat' in light_info['state']
            })
        
        return render_template('index.html', lights=light_data, bridge_ip=bridge_ip)
    except Exception as e:
        logger.error(f"照明情報取得エラー: {e}")
        return render_template('setup.html', error=f"エラーが発生しました: {e}")

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """セットアップページ"""
    global bridge, bridge_ip
    
    if request.method == 'POST':
        new_bridge_ip = request.form.get('bridge_ip')
        if new_bridge_ip:
            bridge_ip = new_bridge_ip
            # 新しいIPアドレスを.envファイルに保存
            with open('.env', 'w') as f:
                f.write(f"HUE_BRIDGE_IP={bridge_ip}\n")
            
            # 新しいIPアドレスでブリッジに接続を試みる
            if connect_to_bridge():
                return redirect(url_for('index'))
    
    # 自動検出を試みる
    discovered_ip = discover_bridge()
    
    return render_template('setup.html', discovered_ip=discovered_ip, current_ip=bridge_ip)

@app.route('/api/lights', methods=['GET'])
def get_lights():
    """照明の情報をJSON形式で返すAPI"""
    global bridge
    
    if bridge is None:
        if not connect_to_bridge():
            return jsonify({'error': 'ブリッジに接続できません'}), 500
    
    try:
        lights = bridge.get_light_objects('id')
        light_data = {}
        
        for light_id, light in lights.items():
            light_info = bridge.get_light(light_id)
            light_data[light_id] = {
                'name': light_info['name'],
                'on': light_info['state']['on'],
                'brightness': light_info['state'].get('bri', 0),
                'reachable': light_info['state']['reachable'],
                'type': light_info['type'],
                'has_color': 'hue' in light_info['state'] and 'sat' in light_info['state']
            }
        
        return jsonify(light_data)
    except Exception as e:
        logger.error(f"API照明情報取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/lights/<int:light_id>', methods=['PUT'])
def update_light(light_id):
    """照明の状態を更新するAPI"""
    global bridge
    
    if bridge is None:
        if not connect_to_bridge():
            return jsonify({'error': 'ブリッジに接続できません'}), 500
    
    try:
        data = request.json
        command = {}
        
        # オン/オフ状態
        if 'on' in data:
            command['on'] = data['on']
        
        # 明るさ
        if 'brightness' in data:
            command['bri'] = max(1, min(254, int(data['brightness'])))
        
        # 色相
        if 'hue' in data:
            command['hue'] = max(0, min(65535, int(data['hue'])))
        
        # 彩度
        if 'saturation' in data:
            command['sat'] = max(0, min(254, int(data['saturation'])))
        
        # 色温度
        if 'color_temp' in data:
            command['ct'] = max(153, min(500, int(data['color_temp'])))
        
        # コマンドを送信
        bridge.set_light(light_id, command)
        
        return jsonify({'success': True, 'light_id': light_id, 'command': command})
    except Exception as e:
        logger.error(f"照明更新エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups', methods=['GET'])
def get_groups():
    """グループの情報をJSON形式で返すAPI"""
    global bridge
    
    if bridge is None:
        if not connect_to_bridge():
            return jsonify({'error': 'ブリッジに接続できません'}), 500
    
    try:
        groups = bridge.get_group()
        return jsonify(groups)
    except Exception as e:
        logger.error(f"グループ情報取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id):
    """グループの状態を更新するAPI"""
    global bridge
    
    if bridge is None:
        if not connect_to_bridge():
            return jsonify({'error': 'ブリッジに接続できません'}), 500
    
    try:
        data = request.json
        command = {}
        
        # オン/オフ状態
        if 'on' in data:
            command['on'] = data['on']
        
        # 明るさ
        if 'brightness' in data:
            command['bri'] = max(1, min(254, int(data['brightness'])))
        
        # 色相
        if 'hue' in data:
            command['hue'] = max(0, min(65535, int(data['hue'])))
        
        # 彩度
        if 'saturation' in data:
            command['sat'] = max(0, min(254, int(data['saturation'])))
        
        # 色温度
        if 'color_temp' in data:
            command['ct'] = max(153, min(500, int(data['color_temp'])))
        
        # コマンドを送信
        bridge.set_group(group_id, command)
        
        return jsonify({'success': True, 'group_id': group_id, 'command': command})
    except Exception as e:
        logger.error(f"グループ更新エラー: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # アプリケーション起動時にブリッジへの接続を試みる
    connect_to_bridge()
    
    # 開発サーバーの起動（本番環境ではWSGIサーバーを使用することを推奨）
    app.run(host='0.0.0.0', port=5000, debug=True) 