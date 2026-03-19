"""
常量定义模块
"""

from enum import Enum
from typing import Dict, List

# 市场类型
class MarketType(Enum):
    SH = "sh"           # 上海
    SZ = "sz"           # 深圳
    BJ = "bj"           # 北京
    HK = "hk"           # 香港
    US = "us"           # 美股
    FUTURES = "futures" # 期货
    OPTIONS = "options" # 期权

MARKET_TYPES = [m.value for m in MarketType]

# 时间频率
class TimeFrequency(Enum):
    TICK = "tick"
    MIN_1 = "1min"
    MIN_5 = "5min"
    MIN_15 = "15min"
    MIN_30 = "30min"
    MIN_60 = "60min"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

TIME_FREQUENCIES = [f.value for f in TimeFrequency]

# 技术指标周期
INDICATOR_PERIODS = {
    "short": [5, 10, 12],
    "medium": [20, 26, 30],
    "long": [60, 120, 250]
}

# 默认重试参数
DEFAULT_RETRY_TIMES = 3
DEFAULT_RETRY_DELAY = 1.0  # 秒
DEFAULT_RATE_LIMIT = 60  # 每分钟最大请求数

# 宏观经济指标列表
MACRO_INDICATORS = [
    'gdp',
    'gdp_yoy',
    'cpi',
    'cpi_yoy',
    'ppi',
    'ppi_yoy',
    'pmi',
    'manufacturing_pmi',
    'non_manufacturing_pmi',
    'interest_rate',
    'rrr',
    'm2',
    'm2_yoy',
    'social_financing',
    'unemployment',
    'consumer_confidence',
    'industrial_output',
    'fixed_asset_investment',
    'retail_sales',
]

# 数据源配置
DATA_SOURCES = {
    "tushare": {
        "name": "Tushare",
        "base_url": "https://api.tushare.pro",
        "requires_token": True,
        "rate_limit": 500,  # 每分钟请求数
        "supported_markets": ["sh", "sz", "bj", "hk"],
        "data_types": ["stock", "index", "fund", "futures"]
    },
    "akshare": {
        "name": "AKShare",
        "base_url": "https://www.akshare.xyz",
        "requires_token": False,
        "rate_limit": None,  # 无明确限制
        "supported_markets": ["sh", "sz", "bj", "hk", "us"],
        "data_types": ["stock", "index", "fund", "futures", "options"]
    },
    "baostock": {
        "name": "BaoStock",
        "base_url": "http://baostock.com",
        "requires_token": False,
        "rate_limit": 200,
        "supported_markets": ["sh", "sz"],
        "data_types": ["stock", "index"]
    }
}

# 筛选因子默认值
DEFAULT_SCREENING_FACTORS = {
    "valuation": {
        "pe_ratio": {"min": 0, "max": 30, "weight": 0.2},
        "pb_ratio": {"min": 0, "max": 3, "weight": 0.15},
        "ps_ratio": {"min": 0, "max": 5, "weight": 0.1},
    },
    "profitability": {
        "roe": {"min": 10, "max": None, "weight": 0.2},
        "roa": {"min": 5, "max": None, "weight": 0.1},
        "gross_margin": {"min": 20, "max": None, "weight": 0.1},
    },
    "growth": {
        "revenue_growth": {"min": 15, "max": None, "weight": 0.15},
        "profit_growth": {"min": 15, "max": None, "weight": 0.15},
    },
    "technical": {
        "ma_golden_cross": {"period": [5, 20], "weight": 0.1},
        "macd_signal": {"weight": 0.1},
        "rsi_range": {"min": 30, "max": 70, "weight": 0.05},
    }
}

# 回测配置
BACKTEST_CONFIG = {
    "initial_capital": 100000,  # 初始资金
    "commission_rate": 0.0003,  # 佣金费率
    "stamp_duty_rate": 0.001,   # 印花税
    "slippage": 0.001,          # 滑点
    "min_commission": 5,        # 最低佣金
    "risk_free_rate": 0.03,     # 无风险利率
    "benchmark": "000300.SH",   # 基准指数
}

# 风险指标阈值
RISK_THRESHOLDS = {
    "max_drawdown": 0.20,      # 最大回撤
    "sharpe_ratio": 1.0,       # 夏普比率
    "sortino_ratio": 1.0,      # 索提诺比率
    "calmar_ratio": 0.5,       # 卡玛比率
    "volatility": 0.25,        # 年化波动率
    "beta": 1.2,               # 贝塔系数
    "var_95": 0.05,            # 95% VaR
    "var_99": 0.02,            # 99% VaR
}
