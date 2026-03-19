# 投资研究系统 - Phase 1 设计方案

## 1. 系统架构概览

```
investment_research/
├── modules/
│   ├── data_collector/      # 【新增】数据采集模块
│   │   ├── __init__.py
│   │   ├── base.py          # 抽象基类
│   │   ├── tushare_adapter.py
│   │   ├── akshare_adapter.py
│   │   ├── cache.py         # 缓存管理
│   │   └── validator.py     # 数据质量检查
│   │
│   ├── macro/               # 宏观分析模块（需优化）
│   │   ├── analyzer.py      # 现有，需扩展
│   │   ├── indicators.py    # 【新增】经济指标采集
│   │   ├── cycle.py         # 【新增】周期判断算法
│   │   ├── scenario.py      # 【新增】情景分析
│   │   └── policy.py        # 【新增】政策评估
│   │
│   └── api/                 # 【新增】API层
│       ├── __init__.py
│       ├── routes/
│       ├── models/
│       └── middleware/
│
├── config/
│   ├── settings.yaml
│   └── database.yaml        # 【新增】数据库配置
│
├── models/                  # 数据模型
│   └── schema.sql           # 【新增】数据库表结构
│
└── tests/
    └── (扩展测试覆盖)
```

## 2. 信息收集模块设计

### 2.1 统一数据采集接口

```python
# modules/data_collector/base.py
class DataCollector(ABC):
    """数据采集器抽象基类"""
    
    @abstractmethod
    def fetch_macro_indicators(self, start_date, end_date) -> pd.DataFrame:
        """获取宏观经济指标"""
        pass
    
    @abstractmethod
    def fetch_stock_data(self, code, start_date, end_date) -> pd.DataFrame:
        """获取股票数据"""
        pass
    
    @abstractmethod
    def fetch_financial_report(self, code, year, quarter) -> dict:
        """获取财务报告"""
        pass
```

### 2.2 多数据源适配器

| 数据源 | 用途 | 优先级 |
|--------|------|--------|
| Tushare | A股行情、财务数据 | Primary |
| AKShare | 宏观经济指标、另类数据 | Primary |
| 东方财富 | 研报、财经新闻 | Fallback |

### 2.3 缓存机制

- 使用 SQLite 本地缓存
- 缓存过期时间：1天（可配置）
- 增量更新：记录最新数据时间戳

### 2.4 数据质量检查

- 缺失值检测与处理
- 异常值检测（3σ原则）
- 数据完整性校验

## 3. 宏观分析模块设计

### 3.1 经济指标采集

| 指标 | 数据源 | 更新频率 |
|------|--------|----------|
| GDP | AKShare | 季度 |
| CPI/PPI | AKShare | 月度 |
| PMI | AKShare | 月度 |
| 利率 | AKShare | 日度 |
| 货币供应量M2 | AKShare | 月度 |
| 社融 | AKShare | 月度 |

### 3.2 经济周期判断算法

使用**综合评分法**结合**马尔可夫转换模型**：

1. **领先指标**: PMI、消费者信心指数
2. **同步指标**: GDP、工业增加值
3. **滞后指标**: 失业率、CPI

周期阶段: 复苏期 → 扩张期 → 顶峰期 → 收缩期 → 低谷期

### 3.3 宏观情景分析

建立三种情景：

| 情景 | 描述 | 概率 |
|------|------|------|
| 基准情景 | 维持当前趋势 | 60% |
| 乐观情景 | 超预期增长 | 20% |
| 悲观情景 | 低于预期 | 20% |

### 3.4 政策影响评估

- 货币政策（利率、准备金率、公开市场操作）
- 财政政策（基建、减税）
- 产业政策（新能源、半导体等）

## 4. API接口设计

### 4.1 RESTful API 端点

```
GET  /api/v1/macro/indicators      # 获取宏观指标
GET  /api/v1/macro/cycle           # 获取经济周期
GET  /api/v1/macro/scenario        # 获取情景分析
GET  /api/v1/macro/policy          # 获取政策评估

POST /api/v1/data/refresh          # 刷新数据缓存
GET  /api/v1/data/status           # 数据源状态
```

### 4.2 响应格式

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "data_source": "akshare",
    "cached": true
  }
}
```

## 5. 数据库设计

### 5.1 核心表结构

```sql
-- 宏观指标历史数据
CREATE TABLE macro_indicators (
    id INTEGER PRIMARY KEY,
    indicator_type VARCHAR(50),
    value DECIMAL(10, 4),
    period DATE,
    source VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据缓存记录
CREATE TABLE data_cache (
    id INTEGER PRIMARY KEY,
    cache_key VARCHAR(100) UNIQUE,
    data JSON,
    updated_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- 经济周期记录
CREATE TABLE economic_cycle (
    id INTEGER PRIMARY KEY,
    cycle_phase VARCHAR(20),
    confidence DECIMAL(5, 4),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP
);
```

## 6. 配置管理

### 6.1 环境变量

```bash
# .env
TUSHARE_TOKEN=your_token
AKSHARE_TOKEN=optional
DATABASE_URL=sqlite:///data/research.db
LOG_LEVEL=INFO
CACHE_EXPIRY=86400
```

### 6.2 配置文件扩展

在 `config/settings.yaml` 中添加:

```yaml
data_collector:
  cache:
    enabled: true
    ttl: 86400
    max_size: 1000
  
  sources:
    tushare:
      enabled: true
      token_env: TUSHARE_TOKEN
    
    akshare:
      enabled: true
      
    eastmoney:
      enabled: false

api:
  enabled: true
  host: "0.0.0.0"
  port: 8000
  cors:
    enabled: true
    origins: ["http://localhost:3000"]
```

## 7. 实现优先级

### 第一批（本周）

1. ✅ 模块设计方案文档
2. 📌 数据采集基类和适配器实现
3. 📌 缓存和数据质量检查
4. 📌 宏观指标采集功能
5. 📌 扩展经济周期判断算法

### 第二批（下周）

6. 📌 情景分析和政策评估
7. 📌 API层基础架构
8. 📌 数据库schema和模型
9. 📌 单元测试覆盖

## 8. 异常处理

```python
class DataCollectionError(Exception):
    """数据采集异常"""
    pass

class DataValidationError(Exception):
    """数据验证异常"""
    pass

class DataSourceUnavailableError(Exception):
    """数据源不可用"""
    pass
```

统一错误响应:

```json
{
  "success": false,
  "error": {
    "code": "DATA_SOURCE_UNAVAILABLE",
    "message": "Tushare服务暂时不可用",
    "retry_after": 60
  }
}
```