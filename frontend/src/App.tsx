import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
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
import './App.css';

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

// 类型定义
interface Holding {
  id: number;
  portfolio_id: number;
  symbol: string;
  name: string;
  quantity: number;
  cost_basis: number;
  current_price: number;
  asset_type: string;
  total_cost: number;
  market_value: number;
  gain_loss: number;
  gain_loss_percent: number;
}

interface Portfolio {
  id: number;
  name: string;
  description: string;
  cash: number;
  created_at: string;
  updated_at: string;
  holdings: Holding[];
}

interface PortfolioSummary {
  portfolio_id: number;
  name: string;
  cash: number;
  holding_count: number;
  total_cost: number;
  total_market_value: number;
  total_gain_loss: number;
  total_gain_loss_percent: number;
}

interface Strategy {
  id: number;
  name: string;
  description: string;
  category: string;
  parameters: string | null;
  total_return: number | null;
  annual_return: number | null;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  is_active: boolean;
}

const API_BASE = 'http://localhost:8000/api';

type Tab = 'portfolio' | 'strategies';

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
  const [backtestSymbol, setBacktestSymbol] = useState('');
  const [backtestStartDate, setBacktestStartDate] = useState('');
  const [backtestEndDate, setbacktestEndDate] = useState('');
  const [backtestResult, setbacktestResult] = useState<any>(null);
  const [backtestLoading, setbacktestLoading] = useState(false);

  // 策略对比相关状态
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [compareSymbol, setCompareSymbol] = useState('');
  const [compareStartDate, setCompareStartDate] = useState('');
  const [compareEndDate, setCompareEndDate] = useState('');
  const [selectedStrategyIds, setSelectedStrategyIds] = useState<number[]>([]);
  const [compareResult, setCompareResult] = useState<any>(null);
  const [compareLoading, setCompareLoading] = useState(false);

  // 创建策略弹窗相关状态
  const [showCreateStrategyModal, setShowCreateStrategyModal] = useState(false);
  const [newStrategyName, setnewStrategyName] = useState('');
  const [newStrategyDesc, setnewStrategyDesc] = useState('');
  const [newStrategyCategory, setnewStrategyCategory] = useState('被动投资');
  const [newStrategyParams, setnewStrategyParams] = useState('{}');

  // 深色模式
  const [darkMode, setDarkMode] = useState(false);

  // 加载投资组合列表
  const loadPortfolios = async () => {
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
  };

  // 加载策略列表
  const loadStrategies = async () => {
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
  };

  // 加载投资组合详情和汇总
  const loadPortfolioDetail = async (portfolio: Portfolio) => {
    setSelectedPortfolio(portfolio);
    try {
      const res = await fetch(`${API_BASE}/portfolio/${portfolio.id}/summary`);
      const data = await res.json();
      setSummary(data);
    } catch (err) {
      console.error('Failed to load summary:', err);
    }
  };

  // 创建新投资组合
  const createPortfolio = async () => {
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
  };

  // 更新价格
  const updatePrices = async (portfolioId: number) => {
    try {
      const res = await fetch(`${API_BASE}/portfolio/${portfolioId}/update-prices`, {
        method: 'POST'
      });
      const data = await res.json();
      alert(`更新完成，成功更新 ${data.updated_count} 个价格`);
      if (selectedPortfolio) {
        loadPortfolioDetail(selectedPortfolio);
        loadPortfolios();
      }
    } catch (err) {
      console.error('Failed to update prices:', err);
      alert('更新失败');
    }
  };

  // 添加持仓
  const addHolding = async () => {
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
        // 重新加载
        loadPortfolioDetail(selectedPortfolio);
        loadPortfolios();
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
  };

  // 删除持仓
  const deleteHolding = async (holdingId: number) => {
    if (!selectedPortfolio || !window.confirm('确认删除此持仓？')) return;
    
    try {
      const res = await fetch(`${API_BASE}/portfolio/${selectedPortfolio.id}/holdings/${holdingId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        loadPortfolioDetail(selectedPortfolio);
        loadPortfolios();
      } else {
        alert('删除失败');
      }
    } catch (err) {
      console.error('Failed to delete holding:', err);
      alert('删除失败');
    }
  };

  // 初始化内置策略到数据库
  const initBuiltinStrategies = async () => {
    try {
      const res = await fetch(`${API_BASE}/strategies/`);
      const existing = await res.json();
      if (existing.length > 0) {
        alert('已有策略数据，无需重复初始化');
        return;
      }

      // 从前端内置数据初始化
      const builtinStrategies = [
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
          description: "按固定比例配置股票和债券，定期再平衡，熊市减持股票增持债券，牛市反之。\n\n经典比例：\n- 保守型：股票20% + 债券80%\n- 平衡型：股票50% + 债券50%\n- 进取型：股票80% + 债券20%\n\n特点：\n- 纪律性再平衡，自动实现低买高卖\n- 平滑波动，控制最大回撤\n- 操作简单，一年再平衡一次即可",
          category: "资产配置",
          parameters: JSON.stringify({ stock_percent: 50, bond_percent: 50, rebalance_threshold: 5 })
        },
        {
          name: "80-年龄法则",
          description: "股票仓位 = 80 - 你的年龄，随着年龄增长逐步降低股票仓位，增加债券仓位。\n\n例子：\n- 30岁：80-30 = 50% 股票\n- 50岁：80-50 = 30% 股票\n- 70岁：80-70 = 10% 股票\n\n特点：\n- 随年龄自动调整风险暴露\n- 简单易记，适合个人投资者\n- 符合生命周期投资理论",
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
          description: "在经济复苏阶段，优先投资顺周期行业，享受经济增长红利。\n\n逻辑：\n- 经济复苏 → 企业盈利改善 → 股价上涨\n- 当前背景下，稳增长政策推动顺周期行业上涨",
          category: "行业轮动",
          parameters: JSON.stringify({ lookback_months: 3, sectors: ["可选消费", "金融", "industrial"] })
        },
        {
          name: "科技创新成长投资",
          description: "投资科技赛道，包括芯片半导体、新能源、人工智能等符合发展方向的领域。\n\n逻辑：\n- 科技是长期核心驱动力\n- 国产替代空间广阔\n- 政策支持力度大",
          category: "成长投资",
          parameters: JSON.stringify({ sectors: ["semiconductor", "new energy", "ai"], growth_rate_min: 20 })
        },
        {
          name: "双均线策略 (20/60)",
          description: "基于移动平均线交叉的趋势跟踪策略。\n\n规则：\n- 短期均线(20日)上穿长期均线(60日) → 金叉买入\n- 短期均线下穿长期均线(60日) → 死叉卖出\n\n特点：\n- 趋势跟踪，顺势而为\n- 避免长期熊市亏损\n- 适合有一定波动的市场",
          category: "趋势跟踪",
          parameters: JSON.stringify({ short_window: 20, long_window: 60 })
        },
        {
          name: "格雷厄姆防御策略",
          description: "本杰明·格雷厄姆经典防御型投资策略，只买入满足估值条件的股票长期持有。\n\n规则（单资产简化版）：\n- 满足估值条件时持仓\n- 不满足估值条件时空仓\n\n特点：\n- 严格估值纪律，拒绝高估\n- 安全边际保护，下跌空间有限\n- 符合价值投资核心思想",
          category: "价值投资",
          parameters: JSON.stringify({ pe_threshold: 15, pb_threshold: 1.5 })
        },
        {
          name: "12个月动量策略",
          description: "买入过去12个月收益为正的资产，动量为负时空仓。\n\n逻辑：\n- 强者恒强，上涨趋势会延续\n- 顺势而为，不接下跌飞刀\n- 定期再平衡更新信号",
          category: "趋势跟踪",
          parameters: JSON.stringify({ momentum_window: 252 })
        }
      ];

      for (const s of builtinStrategies) {
        await fetch(`${API_BASE}/strategies/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(s)
        });
      }

      alert('初始化完成，已添加' + builtinStrategies.length + '种经典投资策略');
      loadStrategies();
    } catch (err) {
      console.error('Failed to init strategies:', err);
      alert('初始化失败');
    }
  };

  // 打开对比弹窗
  const openCompare = () => {
    // 默认最近五年
    const end = new Date();
    const start = new Date();
    start.setFullYear(start.getFullYear() - 5);
    setCompareEndDate(end.toISOString().split('T')[0]);
    setCompareStartDate(start.toISOString().split('T')[0]);
    setCompareResult(null);
    setSelectedStrategyIds([]);
    setShowCompareModal