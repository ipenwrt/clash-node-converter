#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点订阅源生成器：多源动态抓取 TXT → 原始链接 base64。
支持动态日期子目录。
用法：python converter.py
输出：output/links.b64
"""

import base64
import urllib.request
from datetime import datetime, timedelta, timezone
import os
import re  # 用于 Base64 粗检测

BASE_URLS_FILE = 'sources/base-urls.txt'

def is_base64_content(content):
    """检测内容是否为单一 Base64 字符串（长、无 \n、有效 b64）"""
    stripped = content.strip()
    if '\n' in stripped or len(stripped) < 100:  # 非单一长字符串
        return False
    # 粗检测：b64 特征（A-Za-z0-9+/=，mod 4==0）
    if len(stripped) % 4 != 0 or re.search(r'[^A-Za-z0-9+/=]', stripped):
        return False
    try:
        base64.b64decode(stripped)
        return True
    except:
        return False

def get_today_date_str():
    """生成 %y%m%d 格式日期字符串（UTC）"""
    today = datetime.now(timezone.UTC).date()
    return today.strftime('%y%m%d')  # 如 '251029'

def fetch_sources_from_base(base_url, max_retries=2):
    """从单个基 URL 抓取源文件：支持固定 .txt、动态日期后缀 + Base64 自动解码"""
    # 判断是否固定文件名
    is_fixed = base_url.endswith('.txt')
    all_links = []
    date_offset = 0
    while date_offset <= max_retries:
        if is_fixed:
            full_url = base_url  # 直接抓取固定文件
            date_info = "fixed"
        else:
            target_date = datetime.now(timezone.UTC).date() - timedelta(days=date_offset)
            date_str = target_date.strftime('%y%m%d')
            full_url = f"{base_url.rstrip('/')}/{date_str}.txt"  # 动态拼接
            date_info = f"{date_str}: {target_date}"
        
        try:
            print(f"  尝试抓取: {full_url}")
            with urllib.request.urlopen(full_url, timeout=10) as response:
                content = response.read().decode('utf-8')
                # Base64 检测 & 解码
                if is_base64_content(content):
                    try:
                        decoded_bytes = base64.b64decode(content.strip())
                        content = decoded_bytes.decode('utf-8')
                        print(f"  Base64 解码成功 ({date_info})")
                    except Exception as decode_e:
                        print(f"  Base64 解码失败: {decode_e}，按 plain TXT 处理")
                
                # 过滤有效协议链接（支持常见 Clash 协议）
                valid_protocols = ('vmess://', 'vless://', 'hysteria2://', 'ss://', 'trojan://')
                links = [link.strip() for link in content.split('\n') if link.strip() and any(link.startswith(proto) for proto in valid_protocols)]
                if links:
                    all_links.extend(links)
                    print(f"  成功抓取 {len(links)} 个链接 ({date_info})")
                    break  # 成功后停止回退
                else:
                    print(f"  文件为空或无有效链接，尝试前一天")
        except Exception as e:
            print(f"  抓取 {full_url} 失败: {e}")
        
        date_offset += 1
    
    if not all_links:
        print(f"  警告: 该源无有效链接，跳过")
    
    return all_links

def fetch_all_sources(max_retries=2):
    """多源抓取：读取 base-urls.txt，合并所有链接（去重）"""
    if not os.path.exists(BASE_URLS_FILE):
        print(f"警告: {BASE_URLS_FILE} 不存在！请创建并添加基 URL（一行一个）。当前无源，输出空 b64。")
        return []  # 返回空列表，避免 raise 崩 Actions
    
    with open(BASE_URLS_FILE, 'r', encoding='utf-8') as f:
        base_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]  # 忽略空行/注释
    
    if not base_urls:
        print("警告: base-urls.txt 为空或仅注释，请添加至少一个基 URL。当前无源，输出空 b64。")
        return []  # 空源也返回空
    
    all_links_set = set()  # 用 set 去重
    total_links = 0
    for base_url in base_urls:
        print(f"处理源: {base_url}")
        links = fetch_sources_from_base(base_url, max_retries)
        all_links_set.update(links)
        total_links += len(links)
        print(f"  当前总唯一链接数: {len(all_links_set)} (本源新增: {len(links)})")
    
    all_links = list(all_links_set)
    if not all_links:
        print("警告: 所有源抓取失败或无有效链接，输出空 b64。请检查 base-urls.txt 和源 URL。")
    
    print(f"多源合并: {total_links} 个链接 (去重后 {len(all_links)} 个)")
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
    
    # 生成 base64（唯一输出，即使空）
    b64_links = generate_links_base64(links)
    output_file = 'output/links.b64'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(b64_links)
    print(f"Base64 生成完成: {output_file} (链接数: {len(links)})")
    print(f"订阅源 URL 示例: https://raw.githubusercontent.com/你的用户名/clash-node-converter/main/{output_file}")

if __name__ == '__main__':
    main()
