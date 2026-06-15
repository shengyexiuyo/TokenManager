#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Manager Web Server - Flask后端服务
提供REST API与前端daisyUI界面交互
"""

import sys
import os

# 获取应用根目录（支持打包后的exe）
def get_app_root():
    """获取应用根目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的exe
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

# 添加根目录到路径
sys.path.insert(0, get_app_root())

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import json

from token_core import (
    API_PROVIDERS,
    TokenBalanceChecker,
    get_provider_by_key,
    list_providers
)

# 静态文件目录
STATIC_FOLDER = os.path.join(get_app_root(), 'gui')

app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='')
CORS(app)

# 配置文件路径
def get_config_path(filename: str) -> str:
    """获取配置文件路径（保存在exe同目录）"""
    return os.path.join(get_app_root(), filename)


@app.route('/')
def index():
    """返回主页"""
    return send_from_directory('gui', 'index.html')


@app.route('/api/providers')
def get_providers():
    """获取所有提供商列表"""
    providers = list_providers()
    return jsonify(providers)


@app.route('/api/balance', methods=['POST'])
def query_balance():
    """查询余额"""
    data = request.get_json()
    provider_key = data.get('provider')
    api_key = data.get('api_key')
    
    if not provider_key or not api_key:
        return jsonify({
            'success': False,
            'error': '缺少参数'
        })
    
    provider = get_provider_by_key(provider_key)
    if not provider:
        return jsonify({
            'success': False,
            'error': f'未知的服务商: {provider_key}'
        })
    
    checker = TokenBalanceChecker(provider, api_key)
    success, result, error = checker.get_balance()
    
    if success:
        currency = 'CNY'
        if result and len(result) > 0:
            currency = result[0].get('currency', 'CNY')
        return jsonify({
            'success': True,
            'data': result,
            'currency': currency
        })
    else:
        return jsonify({
            'success': False,
            'error': error
        })


@app.route('/api/usage', methods=['POST'])
def query_usage():
    """查询用量"""
    data = request.get_json()
    provider_key = data.get('provider')
    api_key = data.get('api_key')
    
    if not provider_key or not api_key:
        return jsonify({
            'success': False,
            'error': '缺少参数'
        })
    
    provider = get_provider_by_key(provider_key)
    if not provider:
        return jsonify({
            'success': False,
            'error': f'未知的服务商: {provider_key}'
        })
    
    checker = TokenBalanceChecker(provider, api_key)
    success, result, error = checker.get_usage()
    
    if success:
        currency = result.get('currency', 'CNY') if result else 'CNY'
        return jsonify({
            'success': True,
            'data': result,
            'currency': currency
        })
    else:
        return jsonify({
            'success': False,
            'error': error
        })


@app.route('/api/keys/<provider_key>', methods=['GET'])
def get_saved_key(provider_key):
    """获取已保存的密钥"""
    config_file = get_config_path(f'.{provider_key}_key')
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                key_data = json.load(f)
                return jsonify({
                    'success': True,
                    'key': key_data.get('api_key', '')
                })
    except Exception as e:
        pass
    
    return jsonify({
        'success': True,
        'key': ''
    })


@app.route('/api/keys/<provider_key>', methods=['POST'])
def save_key(provider_key):
    """保存密钥"""
    data = request.get_json()
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({
            'success': False,
            'error': '缺少 API Key'
        })
    
    provider = get_provider_by_key(provider_key)
    if not provider:
        return jsonify({
            'success': False,
            'error': f'未知的服务商: {provider_key}'
        })
    
    # 验证API Key格式
    if not provider.validate_api_key(api_key):
        return jsonify({
            'success': False,
            'error': 'API Key 格式不正确'
        })
    
    config_file = get_config_path(f'.{provider_key}_key')
    
    try:
        with open(config_file, 'w') as f:
            json.dump({
                'api_key': api_key,
                'provider': provider_key,
                'provider_name': provider.name,
                'saved_at': datetime.now().isoformat()
            }, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': '密钥已保存'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'保存失败: {str(e)}'
        })


@app.route('/api/keys', methods=['GET'])
def list_saved_keys():
    """列出所有已保存的密钥"""
    keys = []
    
    for provider_key in API_PROVIDERS.keys():
        config_file = get_config_path(f'.{provider_key}_key')
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    key_data = json.load(f)
                    keys.append({
                        'provider_key': provider_key,
                        'provider_name': key_data.get('provider_name', provider_key),
                        'key': key_data.get('api_key', ''),
                        'saved_at': key_data.get('saved_at', '')
                    })
        except Exception:
            pass
    
    return jsonify(keys)


@app.route('/api/keys/<provider_key>', methods=['DELETE'])
def delete_key(provider_key):
    """删除已保存的密钥"""
    config_file = get_config_path(f'.{provider_key}_key')
    
    try:
        if os.path.exists(config_file):
            os.remove(config_file)
            return jsonify({
                'success': True,
                'message': '密钥已删除'
            })
        else:
            return jsonify({
                'success': False,
                'error': '密钥不存在'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'删除失败: {str(e)}'
        })


def main():
    print("=" * 60)
    print("Token Manager Web Server")
    print("=" * 60)
    print("\n支持的AI API提供商:")
    for p in list_providers():
        print(f"  - {p['name']}")
    print("\n" + "=" * 60)
    print("启动服务: http://localhost:5000")
    print("按 Ctrl+C 停止服务")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
