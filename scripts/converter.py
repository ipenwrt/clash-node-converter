#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点转换脚本：动态抓取当天源 TXT，解析为 Clash YAML。
支持：vmess, vless, hysteria2。
用法：python converter.py
输出：output/clash-sub.yaml
"""

import base64
import json
import re
import urllib.request
import yaml
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import os

BASE_URL_FILE = 'sources/base-url.txt'

def get_today_date_str():
    """生成 YYYYMMDD 格式日期字符串（UTC）"""
    today = datetime.utcnow().date()
    return today.strftime('%y%m%d')  # 如 '251029' (25=2025, 10=月, 29=日)

def fetch_sources(max_retries=2):
    """动态抓取源文件：尝试当天 → 前一天"""
    if not os.path.exists(BASE_URL_FILE):
        raise FileNotFoundError(f"请创建 {BASE_URL_FILE} 并添加基 URL")
    
    with open(BASE_URL_FILE, 'r', encoding='utf-8') as f:
        base_url = f.read().strip()
    
    all_links = []
    date_offset = 0
    while date_offset <= max_retries:
        target_date = datetime.utcnow().date() - timedelta(days=date_offset)
        date_str = target_date.strftime('%y%m%d')  # YYYYMMDD 缩写
        full_url = f"{base_url}{date_str}.txt"
        
        try:
            print(f"尝试抓取: {full_url}")
            with urllib.request.urlopen(full_url, timeout=10) as response:
                content = response.read().decode('utf-8')
                links = [link.strip() for link in content.split('\n') if link.strip()]
                if links:
                    all_links.extend(links)
                    print(f"成功抓取 {len(links)} 个链接 (日期: {target_date})")
                    break  # 成功后停止
                else:
                    print(f"文件为空，尝试前一天")
        except Exception as e:
            print(f"抓取 {full_url} 失败: {e}")
        
        date_offset += 1
    
    if not all_links:
        raise ValueError("所有日期文件抓取失败，请检查源仓库")
    
    return all_links

def parse_vmess(link):
    """解析 vmess:// base64 JSON"""
    try:
        # 提取 base64 部分
        base64_part = link.split('://')[1]
        decoded = base64.b64decode(base64_part).decode('utf-8')
        config = json.loads(decoded)
        
        # 提取 ps (name)，支持 Unicode
        name = config.get('ps', 'Unnamed VMess')
        
        return {
            'name': name,
            'type': 'vmess',
            'server': config.get('add', ''),
            'port': int(config.get('port', 0)),
            'uuid': config.get('id', ''),
            'alterId': int(config.get('aid', 0)),
            'cipher': config.get('scy', 'auto'),
            'network': config.get('net', 'tcp'),
            'tls': config.get('tls', '') != '',
            'skip-cert-verify': False,
            'ws-opts': {} if config.get('net') == 'ws' else None
        }
    except Exception as e:
        print(f"VMess 解析失败: {link[:50]}... 错误: {e}")
        return None

def parse_vless(link):
    """解析 vless:// URL"""
    try:
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        
        name = parsed.fragment or 'Unnamed VLESS'
        server = parsed.hostname
        port = int(parsed.port or 443)
        uuid = parsed.path.strip('/')
        
        proxy = {
            'name': name,
            'type': 'vless',
            'server': server,
            'port': port,
            'uuid': uuid,
            'network': params.get('type', ['tcp'])[0] or 'tcp',
            'tls': params.get('security', [''])[0] == 'tls',
            'skip-cert-verify': params.get('allowInsecure', ['0'])[0] == '1',
            'flow': params.get('flow', [''])[0],
            'client-fingerprint': params.get('fp', [''])[0],
            'servername': params.get('sni', [server])[0],
            'ws-opts': None
        }
        
        # WS 选项
        if proxy['network'] == 'ws':
            path = params.get('path', ['/'])[0]
            # 修正历史问题：如果 path 末尾有误参数，截取到 ?
            if '?' in path:
                path = path.split('?')[0]
            proxy['ws-opts'] = {
                'path': path,
                'headers': {'Host': params.get('host', [server])[0]}
            }
        
        return proxy
    except Exception as e:
        print(f"VLESS 解析失败: {link[:50]}... 错误: {e}")
        return None

def parse_hysteria2(link):
    """解析 hysteria2:// URL"""
    try:
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        
        # hysteria2 格式: hysteria2://password@server:port?params#name
        auth = parsed.path.split('@')
        if len(auth) != 2:
            raise ValueError("无效 hysteria2 格式")
        password, server_port = auth
        server, port_str = server_port.rsplit(':', 1)
        port = int(port_str)
        
        name = parsed.fragment or 'Unnamed Hysteria2'
        
        proxy = {
            'name': name,
            'type': 'hysteria2',
            'server': server,
            'port': port,
            'password': urllib.parse.unquote(password),  # 解码 %3E 等
            'sni': params.get('sni', [''])[0],
            'insecure': params.get('insecure', ['0'])[0] == '1',
            'obfs': params.get('obfs', [''])[0],
            'obfs-password': urllib.parse.unquote(params.get('obfs-password', [''])[0])  # 解码特殊字符
        }
        
        return proxy
    except Exception as e:
        print(f"Hysteria2 解析失败: {link[:50]}... 错误: {e}")
        return None

def generate_yaml(proxies):
    """生成 Clash YAML"""
    if not proxies:
        return {}
    
    # 基本结构（添加健康检查组）
    config = {
        'proxies': proxies,
        'proxy-groups': [
            {
                'name': '🚀 节点选择',
                'type': 'select',
                'proxies': [p['name'] for p in proxies]
            },
            {
                'name': '🔗 主代理 (自动测试)',
                'type': 'url-test',
                'proxies': [p['name'] for p in proxies],
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300,
                'tolerance': 50
            }
        ],
        'rules': [
            'DOMAIN-SUFFIX,google.com,🚀 节点选择',
            'GEOIP,CN,DIRECT',
            'MATCH,🔗 主代理 (自动测试)'
        ]
    }
    return config

def main():
    """主函数"""
    print(f"当前日期: {get_today_date_str()}")
    links = fetch_sources()
    proxies = []
    
    for link in links:
        if link.startswith('vmess://'):
            proxy = parse_vmess(link)
        elif link.startswith('vless://'):
            proxy = parse_vless(link)
        elif link.startswith('hysteria2://'):
            proxy = parse_hysteria2(link)
        else:
            print(f"跳过不支持的链接: {link[:50]}...")
            continue
        
        if proxy:
            proxies.append(proxy)
    
    print(f"成功解析 {len(proxies)} 个节点")
    
    config = generate_yaml(proxies)
    
    os.makedirs('output', exist_ok=True)
    output_file = 'output/clash-sub.yaml'
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, indent=2)
    
    print(f"YAML 生成完成: {output_file} (订阅 URL: https://raw.githubusercontent.com/你的用户名/clash-node-converter/main/{output_file})")

if __name__ == '__main__':
    main()
