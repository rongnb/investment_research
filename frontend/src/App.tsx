import React, { useState, useEffect } from 'react';
import './App.css';

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
      alert(`更新完成，成功更新 ${data.updated_count} 个持仓`);
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
          description: "在经济复苏阶段，优先投资顺周期行业（可选消费、金融、工业等），享受经济增长红利。\n\n逻辑：\n- 经济复苏 → 企业盈利改善 → 股价上涨\n- 当前背景下，稳增长政策推动下顺周期优先受益",
          category: "行业轮动",
          parameters: JSON.stringify({ lookback_months: 3, sectors: ["可选消费", "金融", "工业"] })
        },
        {
          name: "科技创新成长投资",
          description: "投资科技赛道，包括芯片半导体、新能源、人工智能等符合发展方向的领域。\n\n逻辑：\n- 科技是长期核心驱动力\n- 国产替代空间广阔\n- 政策支持力度大",
          category: "成长投资",
          parameters: JSON.stringify({ sectors: ["半导体", "新能源", "AI"], growth_rate_min: 20 })
        }
      ];

      for (const s of builtinStrategies) {
        await fetch(`${API_BASE}/strategies/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(s)
        });
      }

      alert('初始化完成，已添加8种经典策略');
      loadStrategies();
    } catch (err) {
      console.error('Failed to init strategies:', err);
      alert('初始化失败');
    }
  };

  useEffect(() => {
    loadPortfolios();
    loadStrategies();
  }, []);

  // 颜色处理：涨红跌绿
  const getColorClass = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  // 分类颜色
  const getCategoryBadgeClass = (category: string) => {
    switch (category) {
      case '被动投资': return 'bg-blue-100 text-blue-800';
      case '价值投资': return 'bg-green-100 text-green-800';
      case '成长投资': return 'bg-purple-100 text-purple-800';
      case '资产配置': return 'bg-yellow-100 text-yellow-800';
      case '行业轮动': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto p-4">
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800">
          📊 Invest Management
        </h1>
        <p className="text-gray-500 mt-1">投资策略研究与组合管理</p>
        
        {/* 标签页导航 */}
        <div className="flex space-x-1 mt-4 border-b">
          <button
            className={`px-4 py-2 font-medium rounded-t-lg ${activeTab === 'portfolio' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('portfolio')}
          >
            📂 投资组合
          </button>
          <button
            className={`px-4 py-2 font-medium rounded-t-lg ${activeTab === 'strategies' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
            onClick={() => setActiveTab('strategies')}
          >
            📚 投资策略
          </button>
        </div>
      </header>

      {/* 投资组合标签 */}
      {activeTab === 'portfolio' && (
        <>
          <div className="mb-4">
            <button 
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              onClick={() => setShowAddModal(true)}
            >
              + 新建投资组合
            </button>
          </div>

          {/* 投资组合列表 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {portfolios.map(p => (
              <div 
                key={p.id}
                className={`border rounded-lg p-4 cursor-pointer hover:shadow-md transition ${selectedPortfolio?.id === p.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}
                onClick={() => loadPortfolioDetail(p)}
              >
                <h3 className="font-semibold text-lg">{p.name}</h3>
                {p.description && <p className="text-gray-500 text-sm">{p.description}</p>}
                <div className="mt-2 text-sm text-gray-600">
                  持仓数: {p.holdings?.length || 0} | 现金: ¥{p.cash.toFixed(2)}
                </div>
              </div>
            ))}
          </div>

          {/* 投资组合详情 */}
          {selectedPortfolio && summary && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="mb-4 flex justify-between items-center">
                <h2 className="text-2xl font-bold">{selectedPortfolio.name}</h2>
                <div className="space-x-2">
                  <button 
                    className="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 text-sm"
                    onClick={() => setShowAddHoldingModal(true)}
                  >
                    + 添加持仓
                  </button>
                  <button 
                    className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 text-sm"
                    onClick={() => updatePrices(selectedPortfolio.id)}
                  >
                    🔄 更新价格
                  </button>
                </div>
              </div>

              {/* 汇总信息 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-500">总成本</div>
                  <div className="text-xl font-semibold">¥{summary.total_cost.toFixed(2)}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-500">总市值</div>
                  <div className="text-xl font-semibold">¥{summary.total_market_value.toFixed(2)}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-500">总收益</div>
                  <div className={`text-xl font-semibold ${getColorClass(summary.total_gain_loss)}`}>
                    {summary.total_gain_loss > 0 ? '+' : ''}{summary.total_gain_loss.toFixed(2)}
                    ({summary.total_gain_loss_percent.toFixed(2)}%)
                  </div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-500">持仓数</div>
                  <div className="text-xl font-semibold">{summary.holding_count}</div>
                </div>
              </div>

              {/* 持仓列表 */}
              <h3 className="text-lg font-semibold mb-3">持仓明细</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse">
                  <thead>
                    <tr className="bg-gray-50 border-b">
                      <th className="text-left p-2">代码</th>
                      <th className="text-left p-2">名称</th>
                      <th className="text-right p-2">数量</th>
                      <th className="text-right p-2">成本价</th>
                      <th className="text-right p-2">当前价</th>
                      <th className="text-right p-2">总成本</th>
                      <th className="text-right p-2">市值</th>
                      <th className="text-right p-2">盈亏</th>
                      <th className="text-right p-2">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedPortfolio.holdings.map(h => (
                      <tr key={h.id} className="border-b hover:bg-gray-50">
                        <td className="p-2 font-mono">{h.symbol}</td>
                        <td className="p-2">{h.name}</td>
                        <td className="p-2 text-right">{h.quantity}</td>
                        <td className="p-2 text-right">¥{h.cost_basis.toFixed(2)}</td>
                        <td className="p-2 text-right">¥{h.current_price?.toFixed(2) || '-'}</td>
                        <td className="p-2 text-right">¥{h.total_cost?.toFixed(2) || '-'}</td>
                        <td className="p-2 text-right">¥{h.market_value?.toFixed(2) || '-'}</td>
                        <td className={`p-2 text-right font-semibold ${getColorClass(h.gain_loss || 0)}`}>
                          {h.gain_loss != null ? (
                            <>
                              {(h.gain_loss > 0 ? '+' : '')}{h.gain_loss.toFixed(2)}
                              <br/>
                              <small>({(h.gain_loss_percent || 0).toFixed(2)}%)</small>
                            </>
                          ) : '-'}
                        </td>
                        <td className="p-2 text-right">
                          <button 
                            className="text-red-500 hover:text-red-700 text-sm"
                            onClick={() => deleteHolding(h.id)}
                          >
                            删除
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 新建组合弹窗 */}
          {showAddModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
              <div className="bg-white p-6 rounded-lg w-96">
                <h3 className="text-xl font-bold mb-4">新建投资组合</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">组合名称</label>
                    <input 
                      type="text" 
                      className="w-full border rounded px-3 py-2"
                      value={newPortfolioName}
                      onChange={e => setNewPortfolioName(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">描述</label>
                    <textarea 
                      className="w-full border rounded px-3 py-2"
                      value={newPortfolioDesc}
                      onChange={e => setNewPortfolioDesc(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">初始现金</label>
                    <input 
                      type="number" 
                      className="w-full border rounded px-3 py-2"
                      value={newCash}
                      onChange={e => setNewCash(e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-2 mt-6">
                  <button 
                    className="px-4 py-2 border rounded text-gray-600 hover:bg-gray-50"
                    onClick={() => setShowAddModal(false)}
                  >
                    取消
                  </button>
                  <button 
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    onClick={createPortfolio}
                  >
                    创建
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 添加持仓弹窗 */}
          {showAddHoldingModal && selectedPortfolio && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
              <div className="bg-white p-6 rounded-lg w-96">
                <h3 className="text-xl font-bold mb-4">添加持仓 · {selectedPortfolio.name}</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">代码 *</label>
                    <input 
                      type="text" 
                      placeholder="A股 600000，美股 AAPL"
                      className="w-full border rounded px-3 py-2"
                      value={newHoldingSymbol}
                      onChange={e => setNewHoldingSymbol(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">名称</label>
                    <input 
                      type="text" 
                      placeholder="贵州茅台"
                      className="w-full border rounded px-3 py-2"
                      value={newHoldingName}
                      onChange={e => setNewHoldingName(e.target.value)}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">数量 *</label>
                      <input 
                        type="number" 
                        step="0.01"
                        className="w-full border rounded px-3 py-2"
                        value={newHoldingQuantity}
                        onChange={e => setNewHoldingQuantity(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">成本价 *</label>
                      <input 
                        type="number" 
                        step="0.01"
                        className="w-full border rounded px-3 py-2"
                        value={newHoldingCost}
                        onChange={e => setNewHoldingCost(e.target.value)}
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">资产类型</label>
                    <select 
                      className="w-full border rounded px-3 py-2"
                      value={newHoldingType}
                      onChange={e => setNewHoldingType(e.target.value)}
                    >
                      <option value="stock">股票</option>
                      <option value="etf">ETF</option>
                      <option value="fund">基金</option>
                      <option value="bond">债券</option>
                    </select>
                  </div>
                </div>
                <div className="flex justify-end space-x-2 mt-6">
                  <button 
                    className="px-4 py-2 border rounded text-gray-600 hover:bg-gray-50"
                    onClick={() => setShowAddHoldingModal(false)}
                  >
                    取消
                  </button>
                  <button 
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    onClick={addHolding}
                  >
                    添加
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* 投资策略标签 */}
      {activeTab === 'strategies' && (
        <>
          <div className="mb-4 flex justify-between items-center">
            <p className="text-gray-600">系统内置经典投资策略，可用于学习研究和回测</p>
            <button 
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              onClick={initBuiltinStrategies}
            >
              📥 初始化内置策略
            </button>
          </div>

          {/* 策略列表 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {strategies.map(s => (
              <div key={s.id} className="border rounded-lg p-5 bg-white hover:shadow-md transition">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-xl font-semibold">{s.name}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryBadgeClass(s.category || '')}`}>
                    {s.category}
                  </span>
                </div>
                {s.description && (
                  <div className="text-gray-600 text-sm whitespace-pre-line mb-3">
                    {s.description}
                  </div>
                )}
                {/* 回测结果 */}
                {(s.total_return != null || s.sharpe_ratio != null || s.max_drawdown != null) && (
                  <div className="grid grid-cols-4 gap-2 mt-4 pt-3 border-t">
                    {s.total_return != null && (
                      <div>
                        <div className="text-xs text-gray-500">总收益</div>
                        <div className={`font-semibold ${getColorClass(s.total_return)}`}>
                          {s.total_return.toFixed(2)}%
                        </div>
                      </div>
                    )}
                    {s.annual_return != null && (
                      <div>
                        <div className="text-xs text-gray-500">年化</div>
                        <div className={`font-semibold ${getColorClass(s.annual_return)}`}>
                          {s.annual_return.toFixed(2)}%
                        </div>
                      </div>
                    )}
                    {s.sharpe_ratio != null && (
                      <div>
                        <div className="text-xs text-gray-500">夏普比率</div>
                        <div className="font-semibold">
                          {s.sharpe_ratio.toFixed(2)}
                        </div>
                      </div>
                    )}
                    {s.max_drawdown != null && (
                      <div>
                        <div className="text-xs text-gray-500">最大回撤</div>
                        <div className={`font-semibold ${getColorClass(-s.max_drawdown)}`}>
                          {s.max_drawdown.toFixed(2)}%
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {strategies.length === 0 && !loading && (
            <div className="text-center py-10 text-gray-500">
              <p className="mb-4">暂无策略数据</p>
              <p>点击"初始化内置策略"按钮加载8种经典投资策略</p>
            </div>
          )}
        </>
      )}

      {loading && <div>加载中...</div>}
    </div>
  );
}

export default App;