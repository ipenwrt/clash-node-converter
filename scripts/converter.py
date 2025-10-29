#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点订阅源生成器：多源动态抓取 TXT → 原始链接 base64。
支持未来扩展：sources/base-urls.txt 一行一个基 URL。
用法：python converter.py
输出：output/links.b64 (订阅源 URL: https://raw.../output/links.b64)
"""

import base64
import urllib.request
from datetime import datetime, timedelta
import os

BASE_URLS_FILE = 'sources/base-urls.txt'

def get_today_date_str():
    """生成 %y%m%d 格式日期字符串（UTC）"""
    today = datetime.utcnow().date()
    return today.strftime('%y%m%d')  # 如 '251029'

def fetch_sources_from_base(max_retries=2):
    """从单个基 URL 抓取源文件：尝试当天 → 前一天，返回链接列表"""
    all_links = []
    date_offset = 0
    while date_offset <= max_retries:
        target_date = datetime.utcnow().date() - timedelta(days=date_offset)
        date_str = target_date.strftime('%y%m%d')
        full_url = f"{base_url}{date_str}.txt"
        
        try:
            print(f"  尝试抓取: {full_url}")
            with urllib.request.urlopen(full_url, timeout=10) as response:
                content = response.read().decode('utf-8')
                links = [link.strip() for link in content.split('\n') if link.strip() and link.startswith(('vmess://', 'vless://', 'hysteria2://'))]  # 过滤有效链接
                if links:
                    all_links.extend(links)
                    print(f"  成功抓取 {len(links)} 个链接 (日期: {target_date})")
                    break  # 成功后停止回退
                else:
                    print(f"  文件为空或无有效链接，尝试前一天")
        except Exception as e:
            print(f"  抓取 {full_url} 失败: {e}")
        
        date_offset += 1
    
    return all_links

def fetch_all_sources(max_retries=2):
    """多源抓取：读取 base-urls.txt，合并所有链接（去重）"""
    if not os.path.exists(BASE_URLS_FILE):
        raise FileNotFoundError(f"请创建 {BASE_URLS_FILE} 并添加基 URL（一行一个）")
    
    with open(BASE_URLS_FILE, 'r', encoding='utf-8') as f:
        base_urls = [line.strip().rstrip('/') for line in f if line.strip() and not line.startswith('#')]  # 忽略空行/注释
    
    if not base_urls:
        raise ValueError("base-urls.txt 为空，请添加至少一个基 URL")
    
    all_links_set = set()  # 用 set 去重
    for base_url in base_urls:
        print(f"处理源: {base_url}")
        links = fetch_sources_from_base(max_retries)
        all_links_set.update(links)
        print(f"  当前总链接数: {len(all_links_set)}")
    
    all_links = list(all_links_set)
    if not all_links:
        raise ValueError("所有源抓取失败或无有效链接，请检查 base-urls.txt")
    
    return all_links

def generate_links_base64(links):
    """生成原始链接 base64（Clash/Sub-Store 标准）"""
    links_str = '\n'.join(links)
    b64_links = base64.b64encode(links_str.encode('utf-8')).decode('utf-8')
    return b64_links

def main():
    """主函数"""
    print(f"当前日期: {get_today_date_str()}")
    links = fetch_all_sources()
    print(f"成功合并 {len(links)} 个唯一原始链接")
    
    os.makedirs('output', exist_ok=True)
    
    # 生成 base64（唯一输出）
    b64_links = generate_links_base64(links)
    output_file = 'output/links.b64'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(b64_links)
    print(f"Base64 生成完成: {output_file}")
    print(f"订阅源 URL 示例: https://raw.githubusercontent.com/你的用户名/clash-node-converter/main/{output_file}")

if __name__ == '__main__':
    main()
