# Clash 节点订阅转换器
自动从源抓取节点，转换为 Clash YAML 订阅。
## 订阅链接
- YAML: https://raw.githubusercontent.com/你的用户名/clash-node-converter/main/output/clash-sub.yaml
## 使用方法
1. 在 Clash Verge/Meta/MetaCubeX 中添加订阅 URL。
2. 更新间隔：每天自动。
3. 测试：导入后运行延迟测试。
## 源配置
编辑 `sources/sources.txt` 添加更多 txt URL，触发 Actions 更新。
## 自定义
- 只想特定节点？修改 `converter.py` 的过滤逻辑。
- 问题反馈：Issues 提 issue。
