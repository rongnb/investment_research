# Investment Research System

## 项目简介

这是一个面向小额投资者（投资额<10万）的量化投资研究系统。系统整合了宏观经济分析、研报解读、经济参数估计和智能决策等多个模块，帮助投资者做出更科学的投资决策。

## 核心特性

- 📊 **宏观分析模块**: 经济指标监控、周期判断
- 📈 **研报分析模块**: 自动化研报解读、关键信息提取
- 🧮 **参数估计模块**: 经济参数建模、预测分析
- 🎯 **决策支持模块**: 投资组合优化、风险评估

## 系统架构

```
investment_research/
├── config/                 # 配置文件
├── data/                   # 数据存储
├── models/                 # 模型定义
├── modules/               # 核心模块
│   ├── macro/            # 宏观分析
│   ├── research/         # 研报分析
│   ├── estimation/       # 参数估计
│   └── decision/       # 决策支持
├── strategies/           # 投资策略
├── tests/                # 测试文件
└── utils/                # 工具函数
```

## 快速开始

### 环境要求

- Python 3.9+
- pip 20.0+
- Git

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/rongnb/investment_research.git
cd investment_research
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

## 使用指南

### 运行宏观分析

```python
from modules.macro import MacroAnalyzer

analyzer = MacroAnalyzer()
indicators = analyzer.get_economic_indicators()
trend = analyzer.analyze_trend()
print(f"当前经济周期: {trend}")
```

### 研报分析

```python
from modules.research import ResearchAnalyzer

analyzer = ResearchAnalyzer()
report = analyzer.analyze_report("path/to/report.pdf")
print(f"关键信息: {report['key_points']}")
```

### 投资组合优化

```python
from modules.decision import PortfolioOptimizer

optimizer = PortfolioOptimizer(budget=100000)
portfolio = optimizer.optimize_risk_return()
print(f"推荐组合: {portfolio}")
```

## 配置文件说明

### config/settings.yaml

```yaml
# 数据源配置
data_sources:
  macro_economy: tushare
  stock_data: akshare
  research_report: pdf_parser

# 模型参数
model_params:
  risk_tolerance: moderate
  investment_horizon: long_term
  rebalancing_frequency: monthly

# 通知设置
notifications:
  email: true
  wechat: false
  slack: false
```

## API文档

详见 `docs/API.md`

## 开发计划

- [ ] v0.1.0 - 基础框架搭建
- [ ] v0.2.0 - 宏观分析模块
- [ ] v0.3.0 - 研报分析模块
- [ ] v0.4.0 - 参数估计模块
- [ ] v0.5.0 - 决策支持模块
- [ ] v1.0.0 - 完整系统发布

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目主页: https://github.com/rongnb/investment_research
- Issue 追踪: https://github.com/rongnb/investment_research/issues
- 邮箱: contact@investment-research.com

## 致谢

感谢所有为本项目做出贡献的开发者！

---

**注意**: 本项目仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。
