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

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null);
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [newPortfolioDesc, setNewPortfolioDesc] = useState('');
  const [newCash, setNewCash] = useState('0');

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

  useEffect(() => {
    loadPortfolios();
  }, []);

  // 颜色处理：涨红跌绿
  const getColorClass = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="container mx-auto p-4">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">
          📊 投资组合管理
        </h1>
        <p className="text-gray-500 mt-1">Invest Management</p>
      </header>

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
            <button 
              className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 text-sm"
              onClick={() => updatePrices(selectedPortfolio.id)}
            >
              🔄 更新价格
            </button>
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

      {loading && <div>加载中...</div>}
    </div>
  );
}

export default App;
