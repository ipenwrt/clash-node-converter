# Clash 节点订阅转换器（Base64 + Sub-Store）

自动抓取源节点，生成 base64 订阅，支持 rename.js 重命名 + skywrt-simple.ini 规则。

## 订阅链接
- **Base64 源**：https://raw.githubusercontent.com/你的用户名/clash-node-converter/main/output/proxies.b64

## 使用方法（推荐 Sub-Store）
1. **安装 Sub-Store**：Clash Meta/MetaCubeX 插件 > Sub-Store（或 https://github.com/tindy2013/sub-store）。
2. **添加订阅**：
   - URL: 上述 base64 源。
   - JS 脚本: https://raw.githubusercontent.com/你的用户名/clash-node-converter/main/configs/rename.js#flag&blkey=IPLC+GPT&nm&out=zh&clear&one（加国旗、保留 IPLC/GPT、输出中文、清理乱名、清理单节点 01）。
   - 配置: https://raw.githubusercontent.com/你的用户名/clash-node-converter/main/configs/skywrt-simple.ini（7 组规则 + 自动优选）。
3. **生成 & 导入**：Sub-Store > 生成 > 复制 YAML 到 Clash 配置文件。更新间隔：每天自动。
4. **参数自定义**：
   - `#flag`：加国旗（🇺🇸 等）。
   - `#blkey=IPLC+GPT`：保留关键词（高质节点）。
   - `#out=en`：输出英文名。
   - 测试：生成后，Clash > 延迟测试，策略组如 ♻️ 所有-自动 会优选低延迟。

## 本地测试
运行 `python scripts/converter.py`，导入 `output/example-full.yaml` 测试（简化版规则）。

## 更新日志
- 每天 UTC 00:00 自动更新。
- 问题：Issues 反馈。
