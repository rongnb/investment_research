import React from 'react';
import { Portfolio, PortfolioSummary } from '../types';

interface PortfolioTabProps {
  portfolios: Portfolio[];
  selectedPortfolio: Portfolio | null;
  summary: PortfolioSummary | null;
  loading: boolean;
  onSelectPortfolio: (portfolio: Portfolio) => void;
  onCreateClick: () => void;
  onAddHoldingClick: () => void;
  onUpdatePrices: (id: number) => void;
  onDeleteHolding: (id: number) => void;
  getColorClass: (value: number) => string;
}

export default function PortfolioTab({
  portfolios,
  selectedPortfolio,
  summary,
  loading,
  onSelectPortfolio,
  onCreateClick,
  onAddHoldingClick,
  onUpdatePrices,
  onDeleteHolding,
  getColorClass,
}: PortfolioTabProps) {
  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <>
      <div className="mb-4">
        <button
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          onClick={onCreateClick}
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
            onClick={() => onSelectPortfolio(p)}
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
                onClick={onAddHoldingClick}
              >
                + 添加持仓
              </button>
              <button
                className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 text-sm"
                onClick={() => onUpdatePrices(selectedPortfolio.id)}
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
                          <br />
                          <small>({(h.gain_loss_percent || 0).toFixed(2)}%)</small>
                        </>
                      ) : '-'}
                    </td>
                    <td className="p-2 text-right">
                      <button
                        className="text-red-500 hover:text-red-700 text-sm"
                        onClick={() => onDeleteHolding(h.id)}
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
    </>
  );
}
