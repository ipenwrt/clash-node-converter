#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点转换脚本：动态抓取源 TXT → 解析 proxies → base64 编码。
支持 Sub-Store + rename.js + skywrt-simple.ini 生成完整订阅。
用法：python converter.py
输出：output/proxies.b64 (订阅源) + example-full.yaml (测试用)
"""

import base64
import json
import re
import urllib.request
import yaml
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import os

BASE_URL_FILE = 'sources/base-url.txt'  # 历史：https://raw.githubusercontent.com/wrtv/combination/refs/heads/main/sub/2510/

def get_today_date_str():
    """生成 YYYYMMDD 格式日期字符串（UTC）"""
    today = datetime.utcnow().date()
    return today.strftime('%y%m%d')  # 如 '251029'

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
        date_str = target_date.strftime('%y%m%d')
        full_url = f"{base_url}{date_str}.txt"
        
        try:
            print(f"尝试抓取: {full_url}")
            with urllib.request.urlopen(full_url, timeout=10) as response:
                content = response.read().decode('utf-8')
                links = [link.strip() for link in content.split('\n') if link.strip()]
                if links:
                    all_links.extend(links)
                    print(f"成功抓取 {len(links)} 个链接 (日期: {target_date})")
                    break
                else:
                    print(f"文件为空，尝试前一天")
        except Exception as e:
            print(f"抓取 {full_url} 失败: {e}")
        
        date_offset += 1
    
    if not all_links:
        raise ValueError("所有日期文件抓取失败，请检查源仓库")
    
    return all_links

def parse_vmess(link):
    """解析 vmess:// base64 JSON"""  # 历史逻辑，无变
    try:
        base64_part = link.split('://')[1]
        decoded = base64.b64decode(base64_part).decode('utf-8')
        config = json.loads(decoded)
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
    """解析 vless:// URL"""  # 历史逻辑 + path 修正
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
        if proxy['network'] == 'ws':
            path = params.get('path', ['/'])[0]
            if '?' in path:
                path = path.split('?')[0]  # 历史修正
            proxy['ws-opts'] = {
                'path': path,
                'headers': {'Host': params.get('host', [server])[0]}
            }
        return proxy
    except Exception as e:
        print(f"VLESS 解析失败: {link[:50]}... 错误: {e}")
        return None

def parse_hysteria2(link):
    """解析 hysteria2:// URL"""  # 历史逻辑 + unquote 解码
    try:
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
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
            'password': urllib.parse.unquote(password),
            'sni': params.get('sni', [''])[0],
            'insecure': params.get('insecure', ['0'])[0] == '1',
            'obfs': params.get('obfs', [''])[0],
            'obfs-password': urllib.parse.unquote(params.get('obfs-password', [''])[0])
        }
        return proxy
    except Exception as e:
        print(f"Hysteria2 解析失败: {link[:50]}... 错误: {e}")
        return None

def generate_proxies_yaml(proxies):
    """生成 proxies YAML 字符串（用于 base64）"""
    config = {'proxies': proxies}
    yaml_str = yaml.dump(config, allow_unicode=True, default_flow_style=False, indent=2, sort_keys=False)
    return yaml_str

def generate_example_full_yaml(proxies, ini_path='configs/skywrt-simple.ini'):
    """模拟生成完整 YAML（测试用；实际用 Sub-Store）"""
    # 简单读取 ini 规则（实际 Sub-Store 会解析 ini 生成 rules/proxy-groups）
    rules = []
    proxy_groups = [
        {'name': '🚀 所有-手动', 'type': 'select', 'proxies': [p['name'] for p in proxies] + ['DIRECT', 'REJECT']},
        {'name': '♻️ 所有-自动', 'type': 'url-test', 'proxies': [p['name'] for p in proxies], 'url': 'http://www.gstatic.com/generate_204', 'interval': 180}
    ]
    # 从 ini 提取示例规则（简化；完整用 Sub-Store）
    if os.path.exists(ini_path):
        with open(ini_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('ruleset='):
                    rules.append(line.strip())  # 占位
    rules.append('- MATCH,♻️ 所有-自动')
    
    full_config = {
        'proxies': proxies,
        'proxy-groups': proxy_groups + [  # 添加节点组示例
            {'name': '🇺🇸 美国-自动', 'type': 'url-test', 'proxies': [p['name'] for p in proxies if 'US' in p['name']], 'url': 'http://www.gstatic.com/generate_204', 'interval': 180}
            # ... 其他组从 ini
        ],
        'rules': rules
    }
    return full_config

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
    
    os.makedirs('output', exist_ok=True)
    
    # 1. 生成 base64 proxies（核心输出）
    proxies_yaml = generate_proxies_yaml(proxies)
    b64_proxies = base64.b64encode(proxies_yaml.encode('utf-8')).decode('utf-8')
    with open('output/proxies.b64', 'w', encoding='utf-8') as f:
        f.write(b64_proxies)
    print("Base64 生成完成: output/proxies.b64")
    print(f"订阅源 URL: https://raw.githubusercontent.com/你的用户名/clash-node-converter/main/output/proxies.b64")
    
    # 2. 示例完整 YAML（本地测试；Actions 可选生成）
    full_config = generate_example_full_yaml(proxies)
    with open('output/example-full.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(full_config, f, allow_unicode=True, default_flow_style=False, indent=2)
    print("示例完整 YAML 生成: output/example-full.yaml")

if __name__ == '__main__':
    main()
