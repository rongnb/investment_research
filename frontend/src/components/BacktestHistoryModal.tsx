import React from 'react';
import { BacktestHistory } from '../types';

interface BacktestHistoryModalProps {
  show: boolean;
  loading: boolean;
  history: BacktestHistory[];
  darkMode: boolean;
  onClose: () => void;
  onDelete: (id: number) => Promise<void>;
}

export default function BacktestHistoryModal({
  show,
  loading,
  history,
  darkMode,
  onClose,
  onDelete,
}: BacktestHistoryModalProps) {
  if (!show) return null;

  const theadBg = darkMode ? 'bg-gray-700' : 'bg-gray-50';
  const borderColor = darkMode ? 'divide-y divide-gray-700' : 'divide-y divide-gray-200';

  // 颜色工具函数内联
  const getColorClass = (value: number) => {
    if (value > 0) return 'text-green-600';
    if (value < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`p-6 rounded-lg w-full max-w-4xl max-h-[80vh] overflow-y-auto ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <div className="flex justify-between items-center mb-4">
          <h3 className={`text-xl font-bold ${darkMode ? 'text-white' : ''}`}>📜 历史回测记录</h3>
          <button
            className={`px-3 py-1 rounded border ${darkMode ? 'border-gray-600 text-gray-300' : 'border-gray-200 text-gray-600'}`}
            onClick={onClose}
          >
            关闭
          </button>
        </div>

        {loading && <div>加载中...</div>}

        {!loading && history.length === 0 && (
          <div className={`py-8 text-center ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            暂无历史回测记录，运行一次回测后会自动保存
          </div>
        )}

        {!loading && history.length > 0 && (
          <div className="overflow-x-auto">
            <table className={`min-w-full ${darkMode ? 'text-gray-200' : ''}`}>
              <thead className={theadBg}>
                <tr>
                  <th className="px-3 py-2 text-left">策略</th>
                  <th className="px-3 py-2 text-left">标的</th>
                  <th className="px-3 py-2 text-right">总收益</th>
                  <th className="px-3 py-2 text-right">年化</th>
                  <th className="px-3 py-2 text-right">夏普</th>
                  <th className="px-3 py-2 text-right">最大回撤</th>
                  <th className="px-3 py-2 text-left">时间</th>
                  <th className="px-3 py-2 text-center">操作</th>
                </tr>
              </thead>
              <tbody className={borderColor}>
                {history.map(item => (
                  <tr key={item.id}>
                    <td className={`px-3 py-2 ${darkMode ? 'text-white' : ''}`}>
                      {item.strategy_name || `策略 #${item.strategy_id}`}
                    </td>
                    <td className={`px-3 py-2 font-mono ${darkMode ? 'text-white' : ''}`}>
                      {item.symbol}
                    </td>
                    <td className={`px-3 py-2 text-right font-semibold ${item.total_return != null ? getColorClass(item.total_return) : ''}`}>
                      {item.total_return != null ? `${item.total_return.toFixed(2)}%` : '-'}
                    </td>
                    <td className={`px-3 py-2 text-right ${darkMode ? 'text-gray-300' : ''}`}>
                      {item.annual_return != null ? `${item.annual_return.toFixed(2)}%` : '-'}
                    </td>
                    <td className={`px-3 py-2 text-right ${darkMode ? 'text-gray-300' : ''}`}>
                      {item.sharpe_ratio != null ? item.sharpe_ratio.toFixed(2) : '-'}
                    </td>
                    <td className={`px-3 py-2 text-right ${darkMode ? 'text-gray-300' : ''}`}>
                      {item.max_drawdown != null ? `${item.max_drawdown.toFixed(2)}%` : '-'}
                    </td>
                    <td className={`px-3 py-2 text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <button
                        className="text-red-500 hover:text-red-700 text-sm"
                        onClick={() => onDelete(item.id)}
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
