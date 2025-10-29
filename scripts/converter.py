#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点转换脚本：动态抓取源 TXT → 原始链接 base64 编码。
支持 Sub-Store + rename.js (重命名/去重/加旗) + skywrt-simple.ini (规则/策略)。
用法：python converter.py
输出：output/links.b64 (订阅源) + example-full.yaml (测试用完整 YAML)
"""

import base64
import urllib.request
from datetime import datetime, timedelta
import os
import yaml  # 只用于 example-full.yaml

BASE_URL_FILE = 'sources/base-url.txt'  # https://raw.githubusercontent.com/wrtv/combination/refs/heads/main/sub/2510/

def get_today_date_str():
    """生成 %y%m%d 格式日期字符串（UTC）"""
    today = datetime.utcnow().date()
    return today.strftime('%y%m%d')  # 如 '251029'

def fetch_sources(max_retries=2):
    """动态抓取源文件：尝试当天 → 前一天，返回原始链接列表"""
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
                    print(f"成功抓取 {len(links)} 个原始链接 (日期: {target_date})")
                    break
                else:
                    print(f"文件为空，尝试前一天")
        except Exception as e:
            print(f"抓取 {full_url} 失败: {e}")
        
        date_offset += 1
    
    if not all_links:
        raise ValueError("所有日期文件抓取失败，请检查源仓库")
    
    return all_links

# 可选：解析函数（如果需过滤链接，启用以下并在 main 中用）
# def parse_vmess(link): ...  # 历史代码，略
# def parse_vless(link): ...  # 历史代码，略
# def parse_hysteria2(link): ...  # 历史代码，略
#
# def filter_and_parse_links(links):
#     proxies = []
#     for link in links:
#         if link.startswith('vmess://'):
#             proxy = parse_vmess(link)
#         # ... 其他
#         if proxy:
#             proxies.append(proxy)
#     return proxies  # 返回解析后 proxies，用于 example-full.yaml

def generate_links_base64(links):
    """生成原始链接 base64（Clash/Sub-Store 标准）"""
    links_str = '\n'.join(links)
    b64_links = base64.b64encode(links_str.encode('utf-8')).decode('utf-8')
    return b64_links

def generate_example_full_yaml(links, ini_path='configs/skywrt-simple.ini'):
    """模拟生成完整 YAML（测试用；实际用 Sub-Store + rename.js 处理 links）"""
    # 模拟 rename.js：简单加序号（实际 JS 更复杂，加旗/去重）
    renamed_links = []
    for i, link in enumerate(links, 1):
        # 模拟重命名：从 fragment 或简单提取
        if '#' in link:
            name = link.split('#')[-1][:10]  # 截取 name
        else:
            name = f'节点-{i:02d}'
        renamed_links.append(f"{link}#{name}-{i:02d}")  # 模拟 #flag&one
    
    # 模拟解析为 proxies（用历史 parse；实际 Sub-Store 处理后是 YAML proxies）
    proxies = []  # 这里可调用 filter_and_parse_links(renamed_links) 如果启用解析
    # 简化：假设 proxies = [{'name': f'模拟节点{i}', 'type': 'vmess', ...} for i in range(len(links))]
    for i, link in enumerate(renamed_links[:]):  # 限前几个测试
        proxies.append({'name': f'模拟-{i+1:02d}', 'type': 'vmess', 'server': 'example.com', 'port': 443})  # 占位
    
    # 从 ini 提取规则/组（简化 7 组）
    proxy_groups = [
        {'name': '🚀 所有-手动', 'type': 'select', 'proxies': [p['name'] for p in proxies] + ['DIRECT', 'REJECT']},
        {'name': '♻️ 所有-自动', 'type': 'url-test', 'proxies': [p['name'] for p in proxies], 'url': 'http://www.gstatic.com/generate_204', 'interval': 180, 'tolerance': 50}
    ]
    rules = [
        'DOMAIN-SUFFIX,openai.com,🤖 AI & 社交',  # 模拟 ini ruleset
        'DOMAIN-SUFFIX,youtube.com,🎬 流媒体',
        'GEOIP,CN,DIRECT',  # 国内
        'MATCH,♻️ 所有-自动'  # 兜底
    ]
    # 添加节点组示例（从 ini）
    proxy_groups.extend([
        {'name': '🇺🇸 美国-自动', 'type': 'url-test', 'proxies': [p['name'] for p in proxies if 'US' in p['name'] or True], 'url': 'http://www.gstatic.com/generate_204', 'interval': 180},
        {'name': '🇭🇰 香港-自动', 'type': 'url-test', 'proxies': [p['name'] for p in proxies if 'HK' in p['name'] or True], 'url': 'http://www.gstatic.com/generate_204', 'interval': 180},
        # ... 其他 5 组类似
    ])
    
    full_config = {
        'proxies': proxies,
        'proxy-groups': proxy_groups,
        'rules': rules
    }
    return full_config

def main():
    """主函数"""
    print(f"当前日期: {get_today_date_str()}")
    links = fetch_sources()
    print(f"成功获取 {len(links)} 个原始链接")
    
    os.makedirs('output', exist_ok=True)
    
    # 1. 生成 base64 原始链接（核心输出，供 Sub-Store + rename.js）
    b64_links = generate_links_base64(links)
    with open('output/links.b64', 'w', encoding='utf-8') as f:
        f.write(b64_links)
    print("Base64 原始链接生成完成: output/links.b64")
    print(f"订阅源 URL: https://raw.githubusercontent.com/你的用户名/clash-node-converter/main/output/links.b64")
    
    # 2. 示例完整 YAML（本地测试；模拟 rename + ini）
    full_config = generate_example_full_yaml(links)
    with open('output/example-full.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(full_config, f, allow_unicode=True, default_flow_style=False, indent=2, sort_keys=False)
    print("示例完整 YAML 生成: output/example-full.yaml (简化版，实际用 Sub-Store)")

if __name__ == '__main__':
    main()
