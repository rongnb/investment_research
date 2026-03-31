import React from 'react';
import { Strategy } from '../types';

interface StrategiesTabProps {
  strategies: Strategy[];
  loading: boolean;
  selectedStrategyIds: number[];
  darkMode: boolean;
  onInitBuiltin: () => Promise<void>;
  onCreateClick: () => void;
  onHistoryClick: () => void;
  onCompareClick: () => void;
  onBacktestClick: (strategy: Strategy) => void;
  onToggleStrategySelection: (id: number) => void;
  getCategoryBadgeClass: (category: string) => string;
  getColorClass: (value: number) => string;
}

export default function StrategiesTab({
  strategies,
  loading,
  selectedStrategyIds,
  darkMode,
  onInitBuiltin,
  onCreateClick,
  onHistoryClick,
  onCompareClick,
  onBacktestClick,
  onToggleStrategySelection,
  getCategoryBadgeClass,
  getColorClass,
}: StrategiesTabProps) {
  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <>
      <div className="mb-4 flex flex-wrap gap-2 justify-between items-center">
        <p className={darkMode ? 'text-gray-300' : 'text-gray-600'}>
          系统内置经典投资策略，可用于学习研究和回测
        </p>
        <div className="space-x-2">
          <button
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            onClick={onHistoryClick}
          >
            📜 历史回测
          </button>
          <button
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            onClick={onCreateClick}
          >
            + 创建策略
          </button>
          <button
            className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
            onClick={onCompareClick}
          >
            ⚖️ 策略对比
          </button>
          <button
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            onClick={onInitBuiltin}
          >
            📥 初始化内置策略
          </button>
        </div>
      </div>

      {/* 策略列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {strategies.map(s => (
          <div
            key={s.id}
            className={`border rounded-lg p-5 bg-white hover:shadow-md transition ${selectedStrategyIds.includes(s.id) ? 'border-purple-500 bg-purple-50' : 'border-gray-200'}`}
          >
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center">
                {selectedStrategyIds.length > 0 && (
                  <input
                    type="checkbox"
                    checked={selectedStrategyIds.includes(s.id)}
                    onChange={() => onToggleStrategySelection(s.id)}
                    className="mr-2 h-4 w-4"
                  />
                )}
                <h3 className="text-xl font-semibold">{s.name}</h3>
              </div>
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
            <div className="mt-4 pt-3 border-t text-right">
              <button
                className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 text-sm"
                onClick={() => onBacktestClick(s)}
              >
                ▶️ 运行回测
              </button>
            </div>
          </div>
        ))}
      </div>

      {strategies.length === 0 && !loading && (
        <div className="text-center py-10 text-gray-500">
          <p className="mb-4">暂无策略数据</p>
          <p>点击"初始化内置策略"按钮加载16种经典投资策略</p>
        </div>
      )}
    </>
  );
}
