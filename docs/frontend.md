# 前端部署文档

## 项目概述

投资研究系统前端是一个基于 React + TypeScript + Ant Design 的量化投资分析平台。

## 技术栈

- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5.x
- **图表**: ECharts 5.x
- **状态管理**: Zustand
- **路由**: React Router 6
- **构建工具**: Vite 5
- **代码规范**: ESLint + Prettier

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API客户端封装
│   │   ├── client.ts      # axios封装
│   │   └── index.ts       # API接口定义
│   ├── components/        # 组件库
│   │   ├── charts/        # 图表组件
│   │   │   ├── KLineChart.tsx    # K线图
│   │   │   ├── LineChart.tsx     # 折线图
│   │   │   ├── BarChart.tsx      # 柱状图
│   │   │   ├── PieChart.tsx      # 饼图
│   │   │   └── Heatmap.tsx       # 热力图
│   │   ├── common/        # 通用组件
│   │   │   ├── Loading.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── StatCard.tsx
│   │   ├── layout/        # 布局组件
│   │   │   ├── Header.tsx
│   │   │   ├── Sider.tsx
│   │   │   └── Layout.tsx
│   │   └── pages/         # 页面组件
│   │       ├── StockDetail.tsx   # 股票详情
│   │       └── MacroAnalysis.tsx # 宏观分析
│   ├── hooks/             # 自定义Hooks
│   │   ├── useWebSocket.ts
│   │   ├── useStock.ts
│   │   └── useMacro.ts
│   ├── store/             # 状态管理
│   │   └── index.ts       # Zustand store
│   ├── styles/            # 样式文件
│   │   └── global.css
│   ├── types/             # TypeScript类型定义
│   │   └── index.ts
│   ├── utils/             # 工具函数
│   ├── App.tsx            # 应用入口
│   └── main.tsx           # 渲染入口
├── .env                   # 环境变量
├── .eslintrc.cjs          # ESLint配置
├── .prettierrc            # Prettier配置
├── index.html             # HTML模板
├── package.json           # 依赖配置
├── tsconfig.json          # TypeScript配置
└── vite.config.ts         # Vite配置
```

## 开发环境

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

开发服务器默认在 `http://localhost:3000` 启动，并代理API请求到后端服务。

### 代码检查

```bash
# ESLint检查
npm run lint

# 自动修复
npm run lint:fix

# 代码格式化
npm run format
```

### 运行测试

```bash
npm run test
```

## 生产环境构建

### 构建项目

```bash
npm run build
```

构建产物输出到 `dist` 目录。

### 预览构建结果

```bash
npm run preview
```

## 环境变量

在 `.env` 文件中配置：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| VITE_API_BASE_URL | API基础URL | /api/v1 |
| VITE_WS_URL | WebSocket URL | ws://localhost:8000/ws |
| VITE_APP_TITLE | 应用标题 | 投资研究系统 |
| VITE_ENABLE_MOCK | 启用模拟数据 | false |
| VITE_ENABLE_DEBUG | 启用调试模式 | false |

## 核心功能

### 1. 股票详情页
- K线图展示（支持MA5/MA10/MA20）
- 实时行情显示
- 技术指标图表
- 历史数据表格

### 2. 宏观分析页
- 经济周期分析（复苏/扩张/顶峰/收缩/低谷）
- 情景分析（乐观/基准/悲观）
- 政策影响评估
- 资产配置建议

### 3. 数据可视化
- K线图（支持缩放、平移）
- 折线图（支持面积图）
- 柱状图（支持横向、堆叠）
- 饼图（支持标签、百分比）
- 热力图（行业相关性等）

## 部署建议

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/frontend/dist;
    index index.html;

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理（可选）
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket代理（可选）
    location /ws/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Docker 部署

```dockerfile
# 构建阶段
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 运行阶段
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 后续开发

### 待实现页面
- 技术分析页 (TechnicalAnalysis)
- 策略回测页 (Backtest)
- 股票筛选页 (Screener)
- 设置页 (Settings)
- AI助手页

### 待完善功能
- 实时数据WebSocket推送
- 股票搜索自动补全
- 数据导出功能
- 移动端响应式适配
- 单元测试覆盖

## 常见问题

### 1. 依赖安装失败
尝试清除npm缓存后重试：
```bash
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

### 2. 端口被占用
修改 `vite.config.ts` 中的 `server.port` 配置，或使用：
```bash
npm run dev -- --port 3001
```

### 3. API请求失败
检查：
1. 后端服务是否启动
2. `.env` 中的 `VITE_API_BASE_URL` 配置是否正确
3. 浏览器控制台是否有跨域错误