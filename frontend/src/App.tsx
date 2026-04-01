import React, { useState, useEffect, useCallback, useMemo, lazy, Suspense } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// 所有导入都放在文件顶部，满足 ESLint 顺序要求
import PortfolioTab from './components/PortfolioTab';
import StrategiesTab from './components/StrategiesTab';

import {
  Portfolio,
  PortfolioSummary,
  Strategy,
  BacktestHistory,
  BacktestResult,
  CompareResult,
  API_BASE,
} from './types';

import './App.css';

// bundle-dynamic-imports: 动态加载模态框组件，减小初始 bundle 大小
const NewPortfolioModal = lazy(() => import('./components/NewPortfolioModal'));
const AddHoldingModal = lazy(() => import('./components/AddHoldingModal'));
const BacktestModal = lazy(() => import('./components/BacktestModal'));
const CompareModal = lazy(() => import('./components/CompareModal'));
const CreateStrategyModal = lazy(() => import('./components/CreateStrategyModal'));
const BacktestHistoryModal = lazy(() => import('./components/BacktestHistoryModal'));

// 注册 Chart.js 组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

type Tab = 'portfolio' | 'strategies';

// 静态提取颜色映射
const CATEGORY_BADGES: Record<string, string> = {
  '被动投资': 'bg-blue-100 text-blue-800',
  '价值投资': 'bg-green-100 text-green-800',
  '成长投资': 'bg-purple-100 text-purple-800',
  '资产配置': 'bg-yellow-100 text-yellow-800',
  '行业轮动': 'bg-orange-100 text-orange-800',
  '趋势跟踪': 'bg-red-100 text-red-800',
  '风险管理': 'bg-cyan-100 text-cyan-800',
  '均值回归': 'bg-pink-100 text-pink-800',
};
const DEFAULT_BADGE = 'bg-gray-100 text-gray-800';

// rendering-hoist-jsx: 提取静态数据到模块级别，只创建一次不重复分配内存
const BUILTIN_STRATEGIES = [
  {
    name: "买入持有策略 (Buy and Hold)",
    description: "买入并长期持有优质资产，不靠择时交易获利，享受企业长期成长带来的收益。\n\n特点：\n- 操作简单，交易成本低\n- 适合大多数普通投资者\n- 复利效应明显\n- 忽略短期市场波动",
    category: "被动投资",
    parameters: JSON.stringify({ holding_period_years: 10, rebalance_frequency: "yearly" })
  },
  {
    name: "定投策略 (Dollar-Cost Averaging)",
    description: "定期定额买入资产，摊平平均成本，降低市场波动对整体收益的影响。\n\n特点：\n- 适合工薪阶层，用闲钱持续投资\n- 不需要择时，克服人性弱点\n- 在震荡市场效果尤其好\n- 纪律性投资，避免追涨杀跌",
    category: "被动投资",
    parameters: JSON.stringify({ investment_amount: "固定金额", investment_interval: "monthly" })
  },
  {
    name: "红利策略 (Dividend Investing)",
    description: "投资于持续稳定分红的公司，依靠分红获得稳定现金流，同时享受股价增值。\n\n特点：\n- 在低利率环境下吸引力强\n- 分红可以再投资，复利增长\n- 高质量红利公司一般财务健康\n- 熊市中分红提供缓冲",
    category: "价值投资",
    parameters: JSON.stringify({ min_dividend_yield: 3, min_dividend_growth_years: 5 })
  },
  {
    name: "股债平衡策略",
    description: "按固定比例配置股票和债券，定期再平衡，在熊市减持股票增持债券，牛市反之。\n\n经典比例：\n- 保守型：股票20% + 债券80%\n- 平衡型：股票50% + 债券50%\n- 进取型：股票80% + 债券20%\n\n特点：\n- 纪律性再平衡，自动实现低买高卖\n- 平滑波动，控制最大回撤\n- 操作简单，一年再平衡一次即可",
    category: "资产配置",
    parameters: JSON.stringify({ stock_percent: 50, bond_percent: 50, rebalance_threshold: 5 })
  },
  {
    name: "80-年龄法则",
    description: "股票仓位 = 80 - 你的年龄，随着年龄增长逐步降低股票仓位，增加债券。\n\n例子：\n- 30岁：80-30 = 50% 股票\n- 50岁：80-50 = 30% 股票\n- 70岁：80-70 = 10% 股票\n\n特点：\n- 随年龄自动调整风险暴露\n- 简单易记，适合个人投资者\n- 符合生命周期投资理论",
    category: "资产配置",
    parameters: JSON.stringify({ base: 80, age_factor: 1 })
  },
  {
    name: "指数ETF投资",
    description: "投资宽基指数ETF，获得市场平均收益，避免选股风险。\n\n常见选择：\n- A股：沪深300ETF、中证500ETF\n- 美股：SPY(S&P500)、QQQ(Nasdaq100)\n- 全球：全球ETF配置分散风险\n\n优势：\n- 费率低，成本优势长期明显\n- 天然分散，避免黑天鹅\n- 跑赢大多数主动基金",
    category: "被动投资",
    parameters: JSON.stringify({ tracking_index: "沪深300", expense_ratio_max: 0.5 })
  },
  {
    name: "顺周期投资",
    description: "在经济复苏阶段，优先投资顺周期行业（可选消费、金融、工业等），享受经济增长红利。\n\n逻辑：\n- 经济复苏 → 企业盈利改善 → 股价上涨\n- 当前背景下，稳增长政策推动 → 顺周期优先受益",
    category: "行业轮动",
    parameters: JSON.stringify({ lookback_months: 3, sectors: ["可选消费", "金融", "工业"] })
  },
  {
    name: "科技创新成长投资",
    description: "投资科技赛道，包括芯片半导体、新能源、人工智能等符合发展方向的领域。\n\n逻辑：\n- 科技是长期核心驱动力\n- 国产替代空间广阔\n- 政策支持力度大",
    category: "成长投资",
    parameters: JSON.stringify({ sectors: ["半导体", "新能源", "AI"], growth_rate_min: 20 })
  },
  {
    name: "双均线交叉策略 (20/60)",
    description: "基于移动平均线交叉的趋势跟踪策略。\n\n规则：\n- 短期均线(20日)上穿长期均线(60日) → 金叉买入\n- 短期均线下穿长期均线 → 死叉卖出\n- 只在多头趋势持仓，空仓时不参与下跌\n\n特点：\n- 趋势跟踪，顺势而为\n- 避免长期熊市亏损\n- 适合有一定波动的市场",
    category: "趋势跟踪",
    parameters: JSON.stringify({ short_window: 20, long_window: 60 })
  },
  {
    name: "格雷厄姆防御策略",
    description: "本杰明·格雷厄姆经典防御型投资策略，只买入满足估值条件的股票长期持有。\n\n规则（单资产简化版）：\n- 满足估值条件时持仓\n- 不满足估值条件时空仓\n\n选股条件：\n- 市盈率 < 15\n- 市净率 < 1.5\n\n特点：\n- 严格估值纪律，拒绝高估\n- 安全边际保护，下跌空间有限\n- 符合价值投资核心思想",
    category: "价值投资",
    parameters: JSON.stringify({ pe_threshold: 15, pb_threshold: 1.5 })
  },
  {
    name: "12个月动量策略",
    description: "买入过去12个月收益为正的资产，动量为负时空仓。\n\n逻辑：\n- 强者恒强，上涨趋势会延续\n- 顺势而为，不接下跌飞刀\n- 定期再平衡更新信号",
    category: "趋势跟踪",
    parameters: JSON.stringify({ momentum_window: 252 })
  },
  {
    name: "低波动策略",
    description: "只在波动率较低的时候持仓，高波动时段回避。\n\n规则：\n- 计算近期滚动波动率\n- 波动率低于阈值时持仓\n- 波动率高于阈值时空仓\n\n特点：\n- 回避剧烈下跌风险\n- 在震荡市场表现较好\n- 减少交易次数，降低情绪影响",
    category: "风险管理",
    parameters: JSON.stringify({ volatility_window: 20, volatility_threshold: 0.02 })
  },
  {
    name: "海龟交易法则",
    description: "经典的趋势跟踪策略，由著名的海龟交易实验公开。\n\n核心规则：\n- 价格突破20日新高 → 买入入场\n- 价格跌破10日新低 → 卖出离场\n- 使用ATR(真实波动幅度均值)进行仓位管理\n\n特点：\n- 系统化趋势交易，纪律性强\n- 大趋势中获利，截断亏损\n- 让利润奔跑，亏损及时止损",
    category: "趋势跟踪",
    parameters: JSON.stringify({ entry_window: 20, exit_window: 10, atr_window: 20 })
  },
  {
    name: "MACD金叉死叉策略",
    description: "基于MACD指标的经典技术分析策略。\n\n规则：\n- MACD线上穿信号线（金叉）→ 买入\n- MACD线下穿信号线（死叉）→ 卖出\n- 通过MACD判断趋势方向和强度\n\n特点：\n- 技术分析中最经典的趋势策略\n- 适合中等波动市场\n- 信号清晰，容易执行",
    category: "趋势跟踪",
    parameters: JSON.stringify({ fast_period: 12, slow_period: 26, signal_period: 9 })
  },
  {
    name: "RSI超买超卖策略",
    description: "基于相对强弱指数(RSI)的均值回归策略。\n\n规则：\n- RSI < 30（超卖区间）→ 买入\n- RSI > 70（超买区间）→ 卖出\n\n特点：\n- 适合震荡市\n- 均值回归逻辑，高抛低吸\n- 在横盘整理行情表现较好",
    category: "均值回归",
    parameters: JSON.stringify({ period: 14, oversold: 30, overbought: 70 })
  },
  {
    name: "布林带突破策略",
    description: "基于布林带的均值回归/突破策略。\n\n规则：\n- 价格跌破下轨 → 买入（认为超跌会反弹）\n- 价格涨过上轨 → 卖出（认为超涨会回调）\n\n特点：\n- 利用波动率做交易\n- 适合震荡区间\n- 在均值回归市场效果好",
    category: "均值回归",
    parameters: JSON.stringify({ window: 20, std_dev: 2.0 })
  }
];

// 对比颜色数组也提取到模块级别
const COMPARE_COLORS = [
  'rgb(59, 130, 246)',
  'rgb(34, 197, 94)',
  'rgb(239, 68, 68)',
  'rgb(168, 85, 247)',
  'rgb(245, 158, 11)',
];

// 纯函数提取到模块级别，不需要 useCallback
// 根据 Vercel 最佳实践：rerender-simple-expression-in-memo - 不需要 memo 简单纯函数
const getColorClass = (value: number): string => {
  if (value > 0) return 'text-green-600';
  if (value < 0) return 'text-red-600';
  return 'text-gray-600';
};

const getCategoryBadgeClass = (category: string): string => {
  return CATEGORY_BADGES[category] || DEFAULT_BADGE;
};

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('portfolio');
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showAddHoldingModal, setShowAddHoldingModal] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [newPortfolioDesc, setNewPortfolioDesc] = useState('');
  const [newCash, setNewCash] = useState('0');

  // 添加持仓表单
  const [newHoldingSymbol, setNewHoldingSymbol] = useState('');
  const [newHoldingName, setNewHoldingName] = useState('');
  const [newHoldingQuantity, setNewHoldingQuantity] = useState('');
  const [newHoldingCost, setNewHoldingCost] = useState('');
  const [newHoldingType, setNewHoldingType] = useState('stock');

  // 回测相关状态
  const [showBacktestModal, setShowBacktestModal] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [backtestSymbol, setbacktestSymbol] = useState('');
  const [backtestStartDate, setbacktestStartDate] = useState('');
  const [backtestEndDate, setbacktestEndDate] = useState('');
  const [backtestResult, setbacktestResult] = useState<BacktestResult | null>(null);
  const [backtestLoading, setbacktestLoading] = useState(false);

  // 策略对比相关状态
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [compareSymbol, setcompareSymbol] = useState('');
  const [compareStartDate, setcompareStartDate] = useState('');
  const [compareEndDate, setcompareEndDate] = useState('');
  const [selectedStrategyIds, setselectedStrategyIds] = useState<number[]>([]);
  const [compareResult, setcompareResult] = useState<CompareResult | null>(null);
  const [compareLoading, setcompareLoading] = useState(false);

  // 创建策略弹窗相关状态
  const [showCreateStrategyModal, setshowCreateStrategyModal] = useState(false);
  const [newStrategyName, setnewStrategyName] = useState('');
  const [newStrategyDesc, setnewStrategyDesc] = useState('');
  const [newStrategyCategory, setnewStrategyCategory] = useState('被动投资');
  const [newStrategyParams, setnewStrategyParams] = useState('{}');

  // 深色模式
  const [darkMode, setDarkMode] = useState(false);

  // 历史回测结果弹窗
  const [showHistoryModal, setshowHistoryModal] = useState(false);
  const [backtestHistory, setbacktestHistory] = useState<BacktestHistory[]>([]);
  const [historyLoading, sethistoryLoading] = useState(false);
  const [historyLoaded, sethistoryLoaded] = useState(false);

  // ---------------
  // 纯函数提取为模块级常量/函数，不需要 useCallback
  // ---------------
  // getColorClass 和 getCategoryBadgeClass 提取到模块级别，避免依赖变化导致重渲染
  // 根据 Vercel 最佳实践：rerender-simple-expression-in-memo - 不需要 memo 简单函数

  // 加载投资组合列表
  const loadPortfolios = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/portfolio/`);
      const data = await res.json();
      setPortfolios(data);
    } catch (err) {
      console.error('Failed to load portfolios:', err);
      alert('加载失败，请检查后端是否启动');
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载策略列表
  const loadStrategies = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/strategies/`);
      const data = await res.json();
      setStrategies(data);
    } catch (err) {
      console.error('Failed to load strategies:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载投资组合详情和汇总
  const loadPortfolioDetail = useCallback(async (portfolio: Portfolio) => {
    setSelectedPortfolio(portfolio);
    try {
      const res = await fetch(`${API_BASE}/portfolio/${portfolio.id}/summary`);
      const data = await res.json();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load summary:', err);
    }
  }, []);

  // 创建新投资组合
  const createPortfolio = useCallback(async () => {
    if (!newPortfolioName) {
      alert('请输入组合名称');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/portfolio/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newPortfolioName,
          description: newPortfolioDesc,
          cash: parseFloat(newCash) || 0
        })
      });
      if (res.ok) {
        await loadPortfolios();
        setShowAddModal(false);
        setNewPortfolioName('');
        setNewPortfolioDesc('');
        setNewCash('0');
      }
    } catch (err) {
      console.error('Failed to create:', err);
      alert('创建失败');
    }
  }, [newPortfolioName, newPortfolioDesc, newCash, loadPortfolios]);

  // 更新价格
  const updatePrices = useCallback(async (portfolioId: number) => {
    try {
      const res = await fetch(`${API_BASE}/portfolio/${portfolioId}/update-prices`, {
        method: 'POST'
      });
      const data = await res.json();
      alert(`更新完成，成功更新 ${data.updated_count} 个持仓`);
      if (selectedPortfolio) {
        // async-parallel: 两个独立请求并行执行，减少等待时间
        await Promise.all([
          loadPortfolioDetail(selectedPortfolio),
          loadPortfolios()
        ]);
      }
    } catch (err) {
      console.error('Failed to update prices:', err);
      alert('更新失败');
    }
  }, [selectedPortfolio, loadPortfolioDetail, loadPortfolios]);

  // 添加持仓
  const addHolding = useCallback(async () => {
    if (!selectedPortfolio) return;
    if (!newHoldingSymbol || !newHoldingQuantity || !newHoldingCost) {
      alert('请填写必填项：代码、数量、成本价');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/portfolio/${selectedPortfolio.id}/holdings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: newHoldingSymbol,
          name: newHoldingName,
          quantity: parseFloat(newHoldingQuantity),
          cost_basis: parseFloat(newHoldingCost),
          asset_type: newHoldingType
        })
      });
      if (res.ok) {
        // async-parallel: 两个独立请求并行执行，减少等待时间
        await Promise.all([
          loadPortfolioDetail(selectedPortfolio),
          loadPortfolios()
        ]);
        setShowAddHoldingModal(false);
        // 清空表单
        setNewHoldingSymbol('');
        setNewHoldingName('');
        setNewHoldingQuantity('');
        setNewHoldingCost('');
      } else {
        alert('添加失败');
      }
    } catch (err) {
      console.error('Failed to add holding:', err);
      alert('添加失败');
    }
  }, [
    selectedPortfolio,
    newHoldingSymbol,
    newHoldingName,
    newHoldingQuantity,
    newHoldingCost,
    newHoldingType,
    loadPortfolioDetail,
    loadPortfolios
  ]);

  // 删除持仓
  const deleteHolding = useCallback(async (holdingId: number) => {
    if (!selectedPortfolio || !window.confirm('确认删除此持仓？')) return;

    try {
      const res = await fetch(`${API_BASE}/portfolio/${selectedPortfolio.id}/holdings/${holdingId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        // async-parallel: 两个独立请求并行执行，减少等待时间
        await Promise.all([
          loadPortfolioDetail(selectedPortfolio),
          loadPortfolios()
        ]);
      } else {
        alert('删除失败');
      }
    } catch (err) {
      console.error('Failed to delete holding:', err);
      alert('删除失败');
    }
  }, [selectedPortfolio, loadPortfolioDetail, loadPortfolios]);

  // 初始化内置策略到数据库
  const initBuiltinStrategies = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/strategies/`);
      const existing = await res.json();
      if (existing.length > 0) {
        alert('已有策略数据，无需重复初始化');
        return;
      }

      // Use batch create API instead of sequential requests
      // async-parallel: one network round trip instead of 13
      const batchRes = await fetch(`${API_BASE}/strategies/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(BUILTIN_STRATEGIES)
      });

      if (batchRes.ok) {
        alert('初始化完成，已添加13种经典策略');
        loadStrategies();
      } else {
        alert('批量初始化失败，可能已经初始化过了');
      }
    } catch (err) {
      console.error('Failed to init strategies:', err);
      alert('初始化失败');
    }
  }, [loadStrategies]);

  // 打开回测弹窗
  const openBacktest = useCallback((strategy: Strategy) => {
    setSelectedStrategy(strategy);
    setbacktestSymbol('');
    // 默认最近5年
    const end = new Date();
    const start = new Date();
    start.setFullYear(start.getFullYear() - 5);
    setbacktestEndDate(end.toISOString().split('T')[0]);
    setbacktestStartDate(start.toISOString().split('T')[0]);
    setbacktestResult(null);
    setShowBacktestModal(true);
  }, []);

  // 运行回测
  const runBacktest = useCallback(async () => {
    if (!selectedStrategy) return;
    if (!backtestSymbol) {
      alert('请输入股票代码');
      return;
    }

    setbacktestLoading(true);
    try {
      let url = `${API_BASE}/strategies/${selectedStrategy.id}/run-backtest?symbol=${encodeURIComponent(backtestSymbol)}`;
      if (backtestStartDate) url += `&start_date=${backtestStartDate}`;
      if (backtestEndDate) url += `&end_date=${backtestEndDate}`;

      const res = await fetch(url, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json();
        alert(`回测失败: ${err.detail || '未知错误'}`);
        return;
      }
      const data = await res.json();
      setbacktestResult(data);
      // 刷新策略列表更新回测结果
      loadStrategies();
    } catch (err) {
      console.error('Backtest failed:', err);
      alert('回测请求失败，请检查后端是否启动');
    } finally {
      setbacktestLoading(false);
    }
  }, [selectedStrategy, backtestSymbol, backtestStartDate, backtestEndDate, loadStrategies]);

  // 对比图表数据（多条曲线）
  const getCompareChartData = useMemo(() => {
    if (!compareResult || !compareResult.results) return null;

    // 获取所有日期的并集
    const allDates = new Set<string>();
    compareResult.results.forEach((r) => {
      r.equity_curve.forEach((p: any) => allDates.add(p.date));
    });
    const labels = Array.from(allDates).sort();

    // 使用模块级预定义颜色
    const datasets = compareResult.results.map((r, idx) => {
      const color = COMPARE_COLORS[idx % COMPARE_COLORS.length];

      // 将数据映射到所有日期（前向填充）
      const data: number[] = [];
      let lastValue = 1;
      const valueMap: Record<string, number> = {};
      r.equity_curve.forEach((p: any) => {
        valueMap[p.date] = p.value;
      });

      labels.forEach(date => {
        if (valueMap[date] !== undefined) {
          lastValue = valueMap[date];
        }
        data.push(lastValue);
      });

      return {
        label: r.strategy_name,
        data,
        borderColor: color,
        backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.1)'),
        fill: false,
        tension: 0.1
      };
    });

    return { labels, datasets };
  }, [compareResult]);

  // 准备图表数据
  const getChartData = useMemo(() => {
    if (!backtestResult || !backtestResult.equity_curve) return null;
    const labels = backtestResult.equity_curve.map((p: any) => p.date);
    const data = backtestResult.equity_curve.map((p: any) => p.value);

    return {
      labels,
      datasets: [
        {
          label: '权益曲线 (初始值=1)',
          data,
          borderColor: 'rgb(59, 130, 246)',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.1
        }
      ]
    };
  }, [backtestResult]);

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const
      }
    },
    scales: {
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: '累计净值'
        }
      },
      x: {
        ticks: {
          maxTicksLimit: 10
        }
      }
    }
  }), []);

  // 切换策略选择
  const toggleStrategySelection = useCallback((strategyId: number) => {
    if (selectedStrategyIds.includes(strategyId)) {
      setselectedStrategyIds(selectedStrategyIds.filter(id => id !== strategyId));
    } else {
      setselectedStrategyIds([...selectedStrategyIds, strategyId]);
    }
  }, [selectedStrategyIds]);

  // 运行对比
  const runCompare = useCallback(async () => {
    if (!compareSymbol) {
      alert('请输入股票代码');
      return;
    }
    if (selectedStrategyIds.length < 2) {
      alert('请至少选择两个策略进行对比');
      return;
    }

    setcompareLoading(true);
    try {
      let url = `${API_BASE}/strategies/compare?symbol=${encodeURIComponent(compareSymbol)}&strategy_ids=${selectedStrategyIds.join(',')}`;
      if (compareStartDate) url += `&start_date=${compareStartDate}`;
      if (compareEndDate) url += `&end_date=${compareEndDate}`;

      const res = await fetch(url, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json();
        alert(`对比失败: ${err.detail || '未知错误'}`);
        return;
      }
      const data = await res.json();
      setcompareResult(data);
    } catch (err) {
      console.error('Compare failed:', err);
      alert('对比请求失败，请检查后端是否启动');
    } finally {
      setcompareLoading(false);
    }
  }, [compareSymbol, compareStartDate, compareEndDate, selectedStrategyIds]);

  // 打开对比弹窗
  const openCompare = useCallback(() => {
    // 默认最近5年
    const end = new Date();
    const start = new Date();
    start.setFullYear(start.getFullYear() - 5);
    setcompareEndDate(end.toISOString().split('T')[0]);
    setcompareStartDate(start.toISOString().split('T')[0]);
    setcompareResult(null);
    setselectedStrategyIds([]);
    setShowCompareModal(true);
  }, []);

  // 创建新策略
  const createStrategy = useCallback(async () => {
    if (!newStrategyName) {
      alert('请输入策略名称');
      return;
    }
    try {
      // 只验证JSON格式，实际发送原始字符串
      JSON.parse(newStrategyParams);
    } catch (e) {
      alert('参数JSON格式错误');
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/strategies/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newStrategyName,
          description: newStrategyDesc,
          category: newStrategyCategory,
          parameters: newStrategyParams
        })
      });
      if (res.ok) {
        alert('创建成功');
        loadStrategies();
        setshowCreateStrategyModal(false);
        // 重置表单
        setnewStrategyName('');
        setnewStrategyDesc('');
        setnewStrategyCategory('被动投资');
        setnewStrategyParams('{}');
      } else {
        alert('创建失败');
      }
    } catch (err) {
      console.error('Failed to create strategy:', err);
      alert('创建失败');
    }
  }, [newStrategyName, newStrategyDesc, newStrategyCategory, newStrategyParams, loadStrategies]);

  // 加载历史回测记录 - 缓存已加载的数据，避免重复请求 (client-localstorage-schema)
  const loadBacktestHistory = useCallback(async () => {
    // 如果已经加载过，直接显示，不需要重新请求
    if (historyLoaded) {
      setshowHistoryModal(true);
      return;
    }

    sethistoryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/strategies/backtest-results`);
      const data = await res.json();
      setbacktestHistory(data);
      sethistoryLoaded(true);
      setshowHistoryModal(true);
    } catch (err) {
      console.error('Failed to load history:', err);
      alert('加载失败，请检查后端是否启动');
    } finally {
      sethistoryLoading(false);
    }
  }, [historyLoaded]);

  // 删除历史回测记录
  const deleteBacktestHistory = useCallback(async (id: number) => {
    if (!window.confirm('确认删除这条回测记录？')) return;
    try {
      await fetch(`${API_BASE}/strategies/backtest-results/${id}`, {
        method: 'DELETE'
      });
      // 重新加载
      const res = await fetch(`${API_BASE}/strategies/backtest-results`);
      const data = await res.json();
      setbacktestHistory(data);
    } catch (err) {
      console.error('Delete failed:', err);
      alert('删除失败');
    }
  }, []);

  useEffect(() => {
    loadPortfolios();
    loadStrategies();
  }, [loadPortfolios, loadStrategies]);

  // 分类颜色处理：涨红跌绿
  const bgContainer = darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50 text-gray-900';

  return (
    <div className={`container mx-auto p-4 min-h-screen ${bgContainer}`}>
      <header className="mb-4 sm:mb-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3">
          <div>
            <h1 className={`text-2xl sm:text-3xl font-bold ${darkMode ? 'text-white' : 'text-gray-800'}`}>
              📊 Invest Management
            </h1>
            <p className={`mt-1 text-sm sm:text-base ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>投资策略研究与组合管理</p>
          </div>
          <button
            className={`self-start sm:self-auto px-3 py-2 rounded border ${darkMode ? 'border-gray-600 hover:bg-gray-800 text-white' : 'border-gray-200 hover:bg-gray-100 text-gray-900'}`}
            onClick={() => setDarkMode(!darkMode)}
          >
            {darkMode ? '☀️ 浅色' : '🌙 深色'}
          </button>
        </div>

        {/* 标签页导航 - 移动端小字号 */}
        <div className={`flex space-x-0.5 sm:space-x-1 mt-3 sm:mt-4 border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          <button
            className={`flex-1 sm:flex-none text-sm sm:text-base px-2 sm:px-4 py-2 font-medium rounded-t-lg ${activeTab === 'portfolio' ? `border-b-2 border-blue-500 ${darkMode ? 'text-blue-400' : 'text-blue-600'}` : `${darkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'}`}`}
            onClick={() => setActiveTab('portfolio')}
          >
            📂 投资组合
          </button>
          <button
            className={`flex-1 sm:flex-none text-sm sm:text-base px-2 sm:px-4 py-2 font-medium rounded-t-lg ${activeTab === 'strategies' ? `border-b-2 border-blue-500 ${darkMode ? 'text-blue-400' : 'text-blue-600'}` : `${darkMode ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'}`}`}
            onClick={() => setActiveTab('strategies')}
          >
            📚 投资策略
          </button>
        </div>
      </header>

      {/* 投资组合标签 */}
      {activeTab === 'portfolio' && (
        <PortfolioTab
          portfolios={portfolios}
          selectedPortfolio={selectedPortfolio}
          summary={summary}
          loading={loading}
          darkMode={darkMode}
          onSelectPortfolio={loadPortfolioDetail}
          onCreateClick={() => setShowAddModal(true)}
          onAddHoldingClick={() => setShowAddHoldingModal(true)}
          onUpdatePrices={updatePrices}
          onDeleteHolding={deleteHolding}
          getColorClass={getColorClass}
        />
      )}

      {/* 投资策略标签 */}
      {activeTab === 'strategies' && (
        <StrategiesTab
          strategies={strategies}
          loading={loading}
          selectedStrategyIds={selectedStrategyIds}
          darkMode={darkMode}
          onInitBuiltin={initBuiltinStrategies}
          onCreateClick={() => setshowCreateStrategyModal(true)}
          onHistoryClick={loadBacktestHistory}
          onCompareClick={openCompare}
          onBacktestClick={openBacktest}
          getCategoryBadgeClass={getCategoryBadgeClass}
          getColorClass={getColorClass}
          onToggleStrategySelection={toggleStrategySelection}
        />
      )}

      {/* 弹窗 - 动态加载减小初始 bundle size (bundle-dynamic-imports) */}
      <Suspense fallback={<div>加载中...</div>}>
        <NewPortfolioModal
          show={showAddModal}
          darkMode={darkMode}
          onClose={() => setShowAddModal(false)}
          onCreate={createPortfolio}
          name={newPortfolioName}
          description={newPortfolioDesc}
          cash={newCash}
          onNameChange={setNewPortfolioName}
          onDescChange={setNewPortfolioDesc}
          onCashChange={setNewCash}
        />
        <AddHoldingModal
          show={showAddHoldingModal}
          portfolio={selectedPortfolio}
          darkMode={darkMode}
          onClose={() => setShowAddHoldingModal(false)}
          onAdd={addHolding}
          symbol={newHoldingSymbol}
          name={newHoldingName}
          quantity={newHoldingQuantity}
          cost={newHoldingCost}
          type={newHoldingType}
          onSymbolChange={setNewHoldingSymbol}
          onNameChange={setNewHoldingName}
          onQuantityChange={setNewHoldingQuantity}
          onCostChange={setNewHoldingCost}
          onTypeChange={setNewHoldingType}
        />
        <BacktestModal
          show={showBacktestModal}
          darkMode={darkMode}
          onClose={() => setShowBacktestModal(false)}
          selectedStrategy={selectedStrategy}
          backtestSymbol={backtestSymbol}
          backtestStartDate={backtestStartDate}
          backtestEndDate={backtestEndDate}
          backtestLoading={backtestLoading}
          backtestResult={backtestResult}
          getColorClass={getColorClass}
          getChartData={getChartData}
          chartOptions={chartOptions}
          onSymbolChange={setbacktestSymbol}
          onStartDateChange={setbacktestStartDate}
          onEndDateChange={setbacktestEndDate}
          onRun={runBacktest}
        />
        <CompareModal
          show={showCompareModal}
          darkMode={darkMode}
          onClose={() => setShowCompareModal(false)}
          strategies={strategies}
          selectedStrategyIds={selectedStrategyIds}
          compareSymbol={compareSymbol}
          compareStartDate={compareStartDate}
          compareEndDate={compareEndDate}
          compareLoading={compareLoading}
          compareResult={compareResult}
          getCompareChartData={getCompareChartData}
          chartOptions={chartOptions}
          getColorClass={getColorClass}
          onSymbolChange={setcompareSymbol}
          onStartDateChange={setcompareStartDate}
          onEndDateChange={setcompareEndDate}
          onToggleStrategy={toggleStrategySelection}
          onRun={runCompare}
        />
        <CreateStrategyModal
          show={showCreateStrategyModal}
          darkMode={darkMode}
          onClose={() => setshowCreateStrategyModal(false)}
          onCreate={createStrategy}
          newStrategyName={newStrategyName}
          newStrategyDesc={newStrategyDesc}
          newStrategyCategory={newStrategyCategory}
          newStrategyParams={newStrategyParams}
          onNameChange={setnewStrategyName}
          onDescChange={setnewStrategyDesc}
          onCategoryChange={setnewStrategyCategory}
          onParamsChange={setnewStrategyParams}
        />
        <BacktestHistoryModal
          show={showHistoryModal}
          darkMode={darkMode}
          onClose={() => setshowHistoryModal(false)}
          history={backtestHistory}
          loading={historyLoading}
          onDelete={deleteBacktestHistory}
        />
      </Suspense>
    </div>
  );
}

export default App;
