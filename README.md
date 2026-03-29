# Invest Management

投资管理应用 - 投资策略研究 + 回测框架 + 个人投资组合管理

## 项目简介

这是一个投资管理应用，旨在帮助个人投资者：
- 📊 **管理个人投资组合** - 跟踪持仓、实时计算收益
- 📈 **投资策略回测** - 用历史数据回测不同投资策略表现
- 📚 **策略知识库** - 整理汇总当前市场上经过验证的有效投资策略
- 🔍 **数据分析** - 对投资组合进行收益分析、风险评估

## 技术栈

- **后端**：Python + FastAPI
- **数据分析**：pandas + numpy + akshare/yfinance
- **前端**：React + TypeScript
- **数据库**：SQLite (开发) / PostgreSQL (生产可选)

## 项目结构

```
invest_management/
├── src/                     # 后端Python源代码
│   ├── api/                # API路由
│   ├── core/               # 配置
│   ├── db/                 # 数据库基础
│   ├── models/             # SQLAlchemy数据模型
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # 业务逻辑服务
│   └── strategies/         # 投资策略实现
├── frontend/               # React前端 (TypeScript)
├── docs/                   # 项目文档
├── tests/                  # 测试代码
├── config/                 # 配置文件
├── requirements.txt        # Python依赖
├── pyproject.toml          # Python配置
├── README.md
└── .gitignore
```

## 快速开始

### 启动后端

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API文档地址：http://localhost:8000/docs

### 启动前端

```bash
cd frontend
npm install
npm start
```

前端地址：http://localhost:3000

## 已内置投资策略

- ✅ 买入持有策略 (Buy and Hold)
- ✅ 定投策略 (Dollar-Cost Averaging)
- ✅ 红利策略
- ✅ 股债平衡策略
- ✅ 80-年龄资产配置法则
- ✅ 指数ETF投资
- ✅ 顺周期投资
- ✅ 科技创新成长投资

## 开发计划

- [x] 项目框架搭建
- [x] 基础API结构
- [x] 投资策略知识库
- [ ] 策略回测引擎完善
- [ ] 前端页面开发
- [ ] 数据获取模块完善
- [ ] 图表可视化
- [ ] 单元测试

## 贡献指南

欢迎提交 Issue 和 Pull Request

## 许可证

MIT
