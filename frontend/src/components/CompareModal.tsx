import React from 'react';
import { Line } from 'react-chartjs-2';
import { CompareResult, Strategy } from '../types';

interface CompareModalProps {
  show: boolean;
  compareSymbol: string;
  compareStartDate: string;
  compareEndDate: string;
  selectedStrategyIds: number[];
  compareResult: CompareResult | null;
  compareLoading: boolean;
  strategies: Strategy[];
  darkMode: boolean;
  getColorClass: (value: number) => string;
  getCompareChartData: any;
  chartOptions: any;
  onClose: () => void;
  onRun: () => void;
  onSymbolChange: (value: string) => void;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
  onToggleStrategy: (id: number) => void;
}

export default function CompareModal({
  show,
  compareSymbol,
  compareStartDate,
  compareEndDate,
  selectedStrategyIds,
  compareResult,
  compareLoading,
  strategies,
  darkMode,
  getColorClass,
  getCompareChartData,
  chartOptions,
  onClose,
  onRun,
  onSymbolChange,
  onStartDateChange,
  onEndDateChange,
  onToggleStrategy,
}: CompareModalProps) {
  if (!show) return null;

  // 适配深色模式图表选项
  const adaptedChartOptions = {
    ...chartOptions,
    plugins: {
      ...chartOptions.plugins,
      legend: {
        ...chartOptions.plugins?.legend,
        labels: {
          ...chartOptions.plugins?.legend?.labels,
          color: darkMode ? '#e5e7eb' : '#374151',
        },
      },
    },
    scales: {
      ...chartOptions.scales,
      y: {
        ...chartOptions.scales?.y,
        ticks: {
          ...chartOptions.scales?.y?.ticks,
          color: darkMode ? '#e5e7eb' : '#374151',
        },
        grid: {
          ...chartOptions.scales?.y?.grid,
          color: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        },
      },
      x: {
        ...chartOptions.scales?.x,
        ticks: {
          ...chartOptions.scales?.x?.ticks,
          color: darkMode ? '#e5e7eb' : '#374151',
        },
        grid: {
          ...chartOptions.scales?.x?.grid,
          color: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
        },
      },
    },
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center overflow-y-auto p-2 sm:p-4">
      <div className={`p-4 sm:p-6 rounded-lg w-full max-w-5xl max-h-[90vh] overflow-y-auto ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <h3 className={`text-xl sm:text-2xl font-bold mb-3 sm:mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          ⚖️ 策略对比
        </h3>

        {/* 输入参数 - 移动端单列 */}
        <div className="grid grid-cols-1 gap-3 sm:gap-4 md:grid-cols-3 mb-4 sm:mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">股票代码 *</label>
            <input
              type="text"
              placeholder="A股: 600000, 美股: AAPL"
              className="w-full border rounded px-3 py-2"
              value={compareSymbol}
              onChange={e => onSymbolChange(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">纯数字识别为A股，字母识别为美股</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">开始日期</label>
            <input
              type="date"
              className="w-full border rounded px-3 py-2"
              value={compareStartDate}
              onChange={e => onStartDateChange(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">结束日期</label>
            <input
              type="date"
              className="w-full border rounded px-3 py-2"
              value={compareEndDate}
              onChange={e => onEndDateChange(e.target.value)}
            />
          </div>
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2 dark:text-gray-400">
            已选择 {selectedStrategyIds.length} 个策略进行对比。在上方列表点击勾选策略。
          </p>
        </div>

        <div className="mb-6">
          <button
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
            onClick={onRun}
            disabled={compareLoading}
          >
            {compareLoading ? '计算中...' : '开始对比'}
          </button>
          <button
            className="ml-2 px-4 py-2 border rounded text-gray-600 hover:bg-gray-50"
            onClick={onClose}
          >
            关闭
          </button>
        </div>

        {/* 对比结果表格 */}
        {compareResult && compareResult.results && (
          <>
            <div className="mb-6">
              <h4 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">对比指标</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse">
                  <thead className={darkMode ? 'bg-gray-700' : 'bg-gray-50'}>
                    <tr>
                      <th className="px-3 py-2 text-left text-gray-900 dark:text-white">策略</th>
                      <th className="px-3 py-2 text-right text-gray-900 dark:text-white">总收益</th>
                      <th className="px-3 py-2 text-right text-gray-900 dark:text-white">年化收益</th>
                      <th className="px-3 py-2 text-right text-gray-900 dark:text-white">波动率</th>
                      <th className="px-3 py-2 text-right text-gray-900 dark:text-white">最大回撤</th>
                      <th className="px-3 py-2 text-right text-gray-900 dark:text-white">夏普比率</th>
                      <th className="px-3 py-2 text-right text-gray-900 dark:text-white">Calmar比率</th>
                      <th className="px-3 py-2 text-right text-gray-900 dark:text-white">胜率</th>
                    </tr>
                  </thead>
                  <tbody className={darkMode ? 'divide-y divide-gray-700' : 'divide-y divide-gray-200'}>
                    {compareResult.results.map(r => (
                      <tr key={r.strategy_id} className={`hover:bg-gray-50 ${darkMode ? 'dark:hover:bg-gray-700' : ''}`}>
                        <td className="px-3 py-2 text-gray-900 dark:text-white">
                          <div className="font-medium">{r.strategy_name}</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">{r.category}</div>
                        </td>
                        <td className={`px-3 py-2 text-right font-semibold ${getColorClass(r.total_return)}`}>
                          {r.total_return.toFixed(2)}%
                        </td>
                        <td className={`px-3 py-2 text-right font-semibold ${getColorClass(r.annual_return)}`}>
                          {r.annual_return.toFixed(2)}%
                        </td>
                        <td className="px-3 py-2 text-right font-semibold text-gray-900 dark:text-white">
                          {r.volatility?.toFixed(2) ?? '-'}%
                        </td>
                        <td className={`px-3 py-2 text-right font-semibold ${getColorClass(-r.max_drawdown)}`}>
                          {r.max_drawdown.toFixed(2)}%
                        </td>
                        <td className="px-3 py-2 text-right font-semibold text-gray-900 dark:text-white">
                          {r.sharpe_ratio.toFixed(2)}
                        </td>
                        <td className="px-3 py-2 text-right font-semibold text-gray-900 dark:text-white">
                          {r.calmar_ratio?.toFixed(2) ?? '-'}
                        </td>
                        <td className="px-3 py-2 text-right font-semibold text-gray-900 dark:text-white">
                          {r.win_rate?.toFixed(1) ?? '-'}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 权益曲线图 - 移动端更小高度 */}
            {compareResult.results[0] && compareResult.results[0].equity_curve && (
              <div className="h-60 sm:h-80 border rounded p-3 sm:p-4 bg-white dark:bg-gray-800">
                <h4 className="text-base sm:text-lg font-semibold mb-2 sm:mb-3 text-gray-900 dark:text-white">权益曲线对比</h4>
                <Line data={getCompareChartData()} options={adaptedChartOptions} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
