# Clash 节点订阅源生成器

自动从多源 TXT 抓取原始节点链接，生成 base64 订阅源。专注核心：抓取 + base64。完整 YAML 用 Sub-Store 处理（重命名/规则）。

## 订阅源
- **Base64 URL**：https://raw.githubusercontent.com/ipenwrt/clash-node-converter/main/output/links.b64

## 使用方法（Sub-Store 生成完整订阅）
1. **安装 Sub-Store**：Clash Meta/MetaCubeX 插件 > Sub-Store（https://github.com/tindy2013/sub-store）。
2. **添加订阅**：
   - **URL**：上述 base64（解码为原始 vmess:// 等链接）。
   - **JS 脚本**（重命名/去重/加旗）：https://raw.githubusercontent.com/ipenwrt/clash-node-converter/main/configs/rename.js#flag&blkey=IPLC+GPT+NF&nm&out=zh&clear&one&blgd&bl&nx
     - 参数解释：`#flag` 加国旗；`#blkey=...` 保留关键词；`#out=zh` 中文名；`#clear` 清理乱名；`#one` 清理单节点 01。
   - **配置**（skywrt-simple.ini 规则/策略）：https://raw.githubusercontent.com/ipenwrt/clash-node-converter/main/configs/skywrt-simple.ini
     - 7 组规则（AI/流媒体/国内等）+ 自动优选（url-test 180s）。
3. **生成 & 导入**：
   - Sub-Store > 生成 YAML > 复制到 Clash 配置文件。
   - 结果：节点如 🇺🇸 IPLC-01；规则如 YouTube 走 🎬 流媒体 → ♻️ 所有-自动（优选低延迟）。
4. **自定义**：
   - 测试参数：去掉 `#clear` 保留所有节点。
   - 无 Sub-Store：用在线 subconverter（如 https://api.dler.cloud/sub?target=clash&url=base64_url&config=ini_url&js=js_url#params）。

## 配置扩展
- **多源**：编辑 sources/base-urls.txt 加行（e.g., 新仓库路径），Actions 自动合并。
- **本地测试**：`python scripts/converter.py`；解码 b64：`echo "内容" | base64 -d`（Linux）。

## 更新
- 每天自动 UTC 00:00。
- 日志：Actions > 查看输出（链接数/源状态）。
- 问题：如 TXT 格式变，调整过滤条件。
