"""
投资策略知识库 - 存储常见的有效投资策略
整理自公开资料
"""

STRATEGIES = [
    {
        "name": "买入持有策略 (Buy and Hold)",
        "category": "被动投资",
        "description": """买入并长期持有优质资产，不靠择时交易获利，享受企业长期成长带来的收益。

特点：
- 操作简单，交易成本低
- 适合大多数普通投资者
- 复利效应明显
- 忽略短期市场波动""",
        "parameters": {
            "holding_period_years": 10,
            "rebalance_frequency": "yearly"
        }
    },
    {
        "name": "定投策略 (Dollar-Cost Averaging)",
        "category": "被动投资",
        "description": """定期定额买入资产，摊平平均成本，降低市场波动对整体收益的影响。

特点：
- 适合工薪阶层，用闲钱持续投资
- 不需要择时，克服人性弱点
- 在震荡市场效果尤其好
- 纪律性投资，避免追涨杀跌""",
        "parameters": {
            "investment_amount": 固定金额,
            "investment_interval": "monthly"
        }
    },
    {
        "name": "红利策略 (Dividend Investing)",
        "category": "价值投资",
        "description": """投资于持续稳定分红的公司，依靠分红获得稳定现金流，同时享受股价增值。

特点：
- 在低利率环境下吸引力强
- 分红可以再投资，复利增长
- 高质量红利公司一般财务健康
- 熊市中分红提供缓冲""",
        "parameters": {
            "min_dividend_yield": 3,
            "min_dividend_growth_years": 5
        }
    },
    {
        "name": "股债平衡策略",
        "category": "资产配置",
        "description": """按固定比例配置股票和债券，定期再平衡，在熊市减持股票增持债券，牛市反之。

经典比例：
- 保守型：股票20% + 债券80%
- 平衡型：股票50% + 债券50%
- 进取型：股票80% + 债券20%

特点：
- 纪律性再平衡，自动实现低买高卖
- 平滑波动，控制最大回撤
- 操作简单，一年再平衡一次即可""",
        "parameters": {
            "stock_percent": 50,
            "bond_percent": 50,
            "rebalance_threshold": 5
        }
    },
    {
        "name": "80-年龄法则",
        "category": "资产配置",
        "description": """股票仓位 = 80 - 你的年龄，随着年龄增长逐步降低股票仓位，增加债券。

例子：
- 30岁：80-30 = 50% 股票
- 50岁：80-50 = 30% 股票
- 70岁：80-70 = 10% 股票

特点：
- 随年龄自动调整风险暴露
- 简单易记，适合个人投资者
- 符合生命周期投资理论""",
        "parameters": {
            "base": 80,
            "age_factor": 1
        }
    },
    {
        "name": "指数ETF投资",
        "category": "被动投资",
        "description": """投资宽基指数ETF，获得市场平均收益，避免选股风险。

常见选择：
- A股：沪深300ETF、中证500ETF
- 美股：SPY(S&P500)、QQQ(Nasdaq100)
- 全球：全球ETF配置分散风险

优势：
- 费率低，成本优势长期明显
- 天然分散，避免黑天鹅
- 跑赢大多数主动基金""",
        "parameters": {
            "tracking_index": "沪深300",
            "expense_ratio_max": 0.5
        }
    },
    {
        "name": "顺周期投资",
        "category": "行业轮动",
        "description": """在经济复苏阶段，优先投资顺周期行业（可选消费、金融、工业等），享受经济增长红利。

逻辑：
- 经济复苏 → 企业盈利改善 → 股价上涨
- 当前背景下，稳增长政策推动下顺周期优先受益""",
        "parameters": {
            "lookback_months": 3,
            "sectors": ["可选消费", "金融", "工业"]
        }
    },
    {
        "name": "科技创新成长投资",
        "category": "成长投资",
        "description": """投资科技赛道，包括芯片半导体、新能源、人工智能等符合发展方向的领域。

逻辑：
- 科技是长期核心驱动力
- 国产替代空间广阔
- 政策支持力度大""",
        "parameters": {
            "sectors": ["半导体", "新能源", "AI"],
            "growth_rate_min": 20
        }
    }
]
