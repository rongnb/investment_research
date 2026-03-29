# 项目结构说明

## 目录结构

```
invest_management/
├── src/                     # 源代码目录
│   ├── api/                 # API接口层
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑层
│   ├── utils/               # 工具函数
│   └── config/              # 应用配置
├── docs/                    # 项目文档
│   ├── api/                 # API文档
│   └── design/              # 设计文档
├── tests/                   # 测试代码
│   ├── unit/                # 单元测试
│   └── integration/         # 集成测试
├── config/                  # 配置文件
├── README.md                # 项目说明
├── .gitignore               # Git忽略配置
└── LICENSE                  # 许可证文件
```

## 设计原则

- **分层架构**：API层 → 服务层 → 数据层，职责清晰
- **可扩展性**：预留扩展接口，方便后续功能新增
- **可测试性**：单元测试+集成测试，保证代码质量
- **可读可维护**：清晰的命名和注释，一致的代码风格
