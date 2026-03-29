# Invest Management

投资管理应用 - 投资策略研究 + 回测框架 + 个人投资组合管理

## 项目简介

这是一个投资管理应用，旨在帮助个人投资者：
- 📊 **管理个人投资组合** - 跟踪持仓、实时计算收益
- 📈 **投资策略回测** - 用历史数据回测不同投资策略表现，交互式图表展示结果
- 📚 **策略知识库** - 整理汇总当前市场上经过验证的有效投资策略
- 🔍 **数据分析** - 对投资组合进行收益分析、风险评估

## 技术栈

- **后端**：Python + FastAPI
- **数据分析**：pandas + numpy + akshare/yfinance
- **前端**：React + TypeScript + Tailwind CSS + Chart.js
- **数据库**：SQLite (开发) / PostgreSQL (生产可选)

## 功能特性

### 投资组合管理
- ✅ 创建多个投资组合
- ✅ 添加/删除持仓
- ✅ 一键更新最新价格（支持 A股/美股）
- ✅ 自动计算单持仓和组合总收益
- ✅ 盈亏直观展示（涨绿跌红）

### 策略知识库
- ✅ 8种经典投资策略内置
- ✅ 分类标签展示（被动投资/价值投资/成长投资/资产配置/行业轮动）
- ✅ 一键初始化策略到数据库
- ✅ 每种策略有详细描述和特点介绍

### 在线回测
- ✅ 支持任意股票（A股纯数字代码/美股字母代码自动识别）
- ✅ 支持自定义时间区间
- ✅ 多种策略实现：买入持有、定投、股债平衡
- ✅ 回测结果自动保存
- ✅ **交互式权益曲线图**展示收益走势
- ✅ 关键指标：总收益、年化收益、夏普比率、最大回撤

## 项目结构

```
invest_management/
├── src/                     # 后端Python源代码
│   ├── api/                # API路由 (portfolio + strategies)
│   ├── core/               # 配置
│   ├── db/                 # 数据库基础
│   ├── models/             # SQLAlchemy数据模型
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # 业务逻辑服务 (backtest + data_fetcher)
│   └── strategies/         # 投资策略数据
├── frontend/               # React前端 (TypeScript)
├── scripts/                # 工具脚本
├── docs/                   # 项目文档
├── tests/                  # 测试代码
├── requirements.txt        # Python依赖
├── Dockerfile              # Docker 镜像
├── docker-compose.yml      # Docker Compose 一键启动
├── pyproject.toml          # Python配置
├── README.md
└── .gitignore
```

## 快速开始

### 方式一：Docker 一键启动（推荐）

```bash
docker-compose up -d --build
```

后端：http://localhost:8000/docs

### 方式二：本地开发启动

#### 1. 启动后端

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python scripts/init_db.py

# 运行开发服务器
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API文档地址：http://localhost:8000/docs

#### 2. 启动前端

```bash
cd frontend
npm install
npm start
```

前端地址：http://localhost:3000

## 已内置投资策略

| 策略名称 | 分类 | 回测支持 |
|---------|------|---------|
| 买入持有策略 (Buy and Hold) | 被动投资 | ✅ |
| 定投策略 (Dollar-Cost Averaging) | 被动投资 | ✅ |
| 红利策略 | 价值投资 | ✅ (默认买入持有) |
| 股债平衡策略 | 资产配置 | ✅ |
| 80-年龄法则 | 资产配置 | ✅ |
| 指数ETF投资 | 被动投资 | ✅ |
| 顺周期投资 | 行业轮动 | ✅ (默认买入持有) |
| 科技创新成长投资 | 成长投资 | ✅ (默认买入持有) |

## 使用示例

1. **使用回测功能**：
   - 点击"投资策略"标签
   - 点击"初始化内置策略"加载8种策略
   - 找到你想回测的策略，点击"运行回测"
   - 输入股票代码（例如 `600000` 浦发银行，`AAPL` 苹果）
   - 选择时间范围，点击"开始回测"
   - 查看回测结果和权益曲线图

2. **管理投资组合**：
   - 点击"+ 新建投资组合"
   - 输入组合名称和初始现金
   - 点击进入组合详情
   - 点击"+ 添加持仓"输入持仓信息
   - 点击"🔄 更新价格"获取最新价格

## 数据来源

- A股数据：[akshare](https://github.com/akfamily/akshare)
- 美股数据：[yfinance](https://pypi.org/project/yfinance/)

## 开发进度

- [x] 项目框架搭建
- [x] 基础API结构
- [x] 投资组合CRUD
- [x] 自动价格更新
- [x] 收益计算
- [x] 投资策略知识库
- [x] 策略回测引擎
- [x] 前端页面开发
- [x] 图表可视化
- [ ] 更多策略实现
- [ ] 多资产回测
- [ ] 交易信号生成
- [ ] 单元测试

## 贡献指南

欢迎提交 Issue 和 Pull Request

## 许可证

MIT
