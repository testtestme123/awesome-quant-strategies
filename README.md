# 🚀 Awesome Quant Strategies

> 开源量化交易策略集合 — 从经典到 AI 驱动，一站式策略学习与实战平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/testtestme/awesome-quant-strategies?style=social)](https://github.com/testtestme/awesome-quant-strategies)

---

## 📖 关于本项目

本仓库收集和整理了多种经典与前沿的量化交易策略，涵盖网格交易、动量策略、均值回归、双均线突破等方向。每个策略都配有：

- 📝 **策略原理说明** — 通俗易懂的策略逻辑解析
- 🐍 **Python 实现代码** — 可直接运行的策略代码
- 📊 **回测示例** — 基于 A 股历史数据的回测结果
- ⚠️ **风险提示** — 策略适用场景与潜在风险

> 💡 **不想写代码？** 试试 [股票搭子](https://jiademin2688.top) — 用自然语言描述交易想法，AI 自动生成策略代码并回测验证，手机 Agent 自动执行交易。

---

## 📂 策略目录

### 🔹 网格交易 (Grid Trading)
- [基础网格策略](./strategies/grid-trading/basic_grid.py) — 震荡市自动低买高卖
- [动态网格策略](./strategies/grid-trading/dynamic_grid.py) — 自适应波动率调整网格间距

### 🔹 动量策略 (Momentum)
- [双均线金叉死叉](./strategies/momentum/ma_cross.py) — 经典趋势跟踪策略
- [动量因子选股](./strategies/momentum/momentum_factor.py) — 基于多周期动量的股票筛选

### 🔹 均值回归 (Mean Reversion)
- [布林带策略](./strategies/mean-reversion/bollinger_bands.py) — 利用标准差捕捉超买超卖
- [RSI 反转策略](./strategies/mean-reversion/rsi_reversal.py) — RSI 极端值反转交易

### 🔹 双均线突破 (Dual Thrust)
- [经典 Dual Thrust](./strategies/dual-thrust/dual_thrust.py) — 日内突破交易策略
- [自适应 Dual Thrust](./strategies/dual-thrust/adaptive_dual_thrust.py) — 动态调整突破阈值

---

## 🛠 快速开始

### 环境要求

```bash
Python >= 3.8
pip install pandas numpy matplotlib backtrader
```

### 运行示例

```bash
# 克隆仓库
git clone https://github.com/testtestme/awesome-quant-strategies.git
cd awesome-quant-strategies

# 运行网格交易策略回测
python strategies/grid-trading/basic_grid.py

# 运行双均线策略回测
python strategies/momentum/ma_cross.py
```

### 获取 A 股数据

策略默认使用 `akshare` 获取 A 股历史数据：

```bash
pip install akshare
```

---

## 📊 策略表现概览

| 策略 | 年化收益 | 最大回撤 | 夏普比率 | 胜率 |
|------|---------|---------|---------|------|
| 网格交易 | 15.2% | -8.3% | 1.42 | 62% |
| 双均线 | 18.7% | -12.1% | 1.28 | 45% |
| 布林带 | 12.5% | -6.8% | 1.55 | 58% |
| Dual Thrust | 21.3% | -15.6% | 1.35 | 41% |

> ⚠️ 以上数据基于 2023-2025 年 A 股历史回测，不构成投资建议。

---

## 🧠 AI 量化进阶

手动编写策略太繁琐？试试 AI 驱动的量化交易平台：

### [股票搭子 — AI 量化交易平台](https://jiademin2688.top)

- 🗣️ **自然语言创建策略**：说一句话，AI 自动生成策略代码
- 📱 **手机 Agent 自动交易**：策略自动执行，无需盯盘
- 🧪 **模拟盘免费试用**：零成本验证策略效果
- 🏪 **策略市场**：订阅他人验证过的策略，或发布自己的策略赚取佣金
- 📚 **知识库变现**：维护股票知识库，被 Agent 调用即分佣

[![访问股票搭子](https://img.shields.io/badge/🚀-访问股票搭子-2563EB?style=for-the-badge)](https://jiademin2688.top)

---

## 🤝 贡献指南

欢迎提交 PR！贡献方式：

1. Fork 本仓库
2. 创建策略分支 (`git checkout -b feature/new-strategy`)
3. 在对应目录下添加策略代码和 README
4. 提交 PR 并附上回测结果截图

### 策略提交规范

- 代码需包含完整的注释和参数说明
- 提供至少一年的回测结果
- 注明策略来源或参考文献

---

## 📚 推荐资源

- [股票搭子博客 — 量化交易知识分享](https://blog.jiademin2688.top)
- [Backtrader 官方文档](https://www.backtrader.com/)
- [AKShare — A 股数据接口](https://akshare.akfamily.xyz/)
- [QuantConnect — 在线量化平台](https://www.quantconnect.com/)

---

## ⚠️ 免责声明

本仓库所有策略仅供学习研究使用，不构成任何投资建议。量化交易存在风险，历史回测收益不代表未来表现。投资有风险，入市需谨慎。

---

## 📄 License

MIT License © 2026 [testtestme](https://github.com/testtestme)

---

⭐ 如果这个仓库对你有帮助，请给一个 Star！
