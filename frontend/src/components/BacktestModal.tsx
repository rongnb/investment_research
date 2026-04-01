import React from 'react';
import { Line } from 'react-chartjs-2';
import { Strategy, BacktestResult } from '../types';

interface BacktestModalProps {
  show: boolean;
  selectedStrategy: Strategy | null;
  backtestSymbol: string;
  backtestStartDate: string;
  backtestEndDate: string;
  backtestResult: BacktestResult | null;
  backtestLoading: boolean;
  darkMode: boolean;
  getColorClass: (value: number) => string;
  getChartData: any;
  chartOptions: any;
  onClose: () => void;
  onRun: () => void;
  onSymbolChange: (value: string) => void;
  onStartDateChange: (value: string) => void;
  onEndDateChange: (value: string) => void;
}

export default function BacktestModal({
  show,
  selectedStrategy,
  backtestSymbol,
  backtestStartDate,
  backtestEndDate,
  backtestResult,
  backtestLoading,
  darkMode,
  getColorClass,
  getChartData,
  chartOptions,
  onClose,
  onRun,
  onSymbolChange,
  onStartDateChange,
  onEndDateChange,
}: BacktestModalProps) {
  if (!show || !selectedStrategy) return null;

  // 准备回撤曲线数据
  const getDrawdownChartData = () => {
    if (!backtestResult || !backtestResult.equity_curve) return null;

    const labels = backtestResult.equity_curve.map(p => p.date);

    return {
      labels,
      datasets: [
        {
          label: '回撤 (%)',
          data: backtestResult.equity_curve.map((p, i) => {
            // 重新计算累计回撤
            const subset = backtestResult.equity_curve.slice(0, i + 1);
            const peak = Math.max(...subset.map(p => p.value));
            return ((p.value - peak) / peak) * 100;
          }),
          borderColor: 'rgb(239, 68, 68)',
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          fill: true,
          tension: 0.1,
        },
      ],
    };
  };

  const getDrawdownChartOptions = () => {
    const textColor = darkMode ? '#e5e7eb' : '#374151';
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: {
            color: textColor,
          },
        },
      },
      scales: {
        y: {
          ticks: {
            color: textColor,
            callback: function(value: any) {
              return value + '%';
            },
          },
          grid: {
            color: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          },
        },
        x: {
          ticks: {
            color: textColor,
          },
          grid: {
            color: darkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          },
        },
      },
    };
  };

  // 改进原始chart options适配深色模式
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
      <div className={`p-4 sm:p-6 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <h3 className={`text-xl sm:text-2xl font-bold mb-3 sm:mb-4 ${darkMode ? 'text-white' : 'text-gray-900'}`}>
          ▶️ 运行回测 · {selectedStrategy.name}
        </h3>

        {/* 输入参数 - 移动端单列 */}
        <div className="grid grid-cols-1 gap-3 sm:gap-4 md:grid-cols-3 mb-4 sm:mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">股票代码 *</label>
            <input
              type="text"
              placeholder="A股: 600000, 美股: AAPL"
              className="w-full border rounded px-3 py-2"
              value={backtestSymbol}
              onChange={e => onSymbolChange(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">纯数字识别为A股，字母识别为美股</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">开始日期</label>
            <input
              type="date"
              className="w-full border rounded px-3 py-2"
              value={backtestStartDate}
              onChange={e => onStartDateChange(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1 dark:text-gray-300">结束日期</label>
            <input
              type="date"
              className="w-full border rounded px-3 py-2"
              value={backtestEndDate}
              onChange={e => onEndDateChange(e.target.value)}
            />
          </div>
        </div>

        <div className="mb-6">
          <button
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
            onClick={onRun}
            disabled={backtestLoading}
          >
            {backtestLoading ? '计算中...' : '开始回测'}
          </button>
          <button
            className="ml-2 px-4 py-2 border rounded text-gray-600 hover:bg-gray-50"
            onClick={onClose}
          >
            关闭
          </button>
        </div>

        {/* 回测结果 */}
        {backtestResult && (
          <div>
            {/* 关键指标 - 移动端2列，桌面4列 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3 md:gap-4 mb-4 sm:mb-6">
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">总收益</div>
                <div className={`text-lg sm:text-xl font-semibold ${getColorClass(backtestResult.total_return)}`}>
                  {backtestResult.total_return.toFixed(2)}%
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">年化收益</div>
                <div className={`text-lg sm:text-xl font-semibold ${getColorClass(backtestResult.annual_return)}`}>
                  {backtestResult.annual_return.toFixed(2)}%
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">波动率</div>
                <div className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  {backtestResult.volatility?.toFixed(2) ?? '-'}%
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">最大回撤</div>
                <div className={`text-lg sm:text-xl font-semibold ${getColorClass(-backtestResult.max_drawdown)}`}>
                  {backtestResult.max_drawdown.toFixed(2)}%
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">夏普比率</div>
                <div className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  {backtestResult.sharpe_ratio.toFixed(2)}
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Sortino比率</div>
                <div className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  {backtestResult.sortino_ratio?.toFixed(2) ?? '-'}
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Calmar比率</div>
                <div className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  {backtestResult.calmar_ratio?.toFixed(2) ?? '-'}
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">胜率</div>
                <div className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  {backtestResult.win_rate?.toFixed(1) ?? '-'}%
                </div>
              </div>
            </div>

            {/* 第二行指标 - 移动端2列 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 sm:gap-3 md:gap-4 mb-4 sm:mb-6">
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">盈亏比</div>
                <div className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  {backtestResult.profit_loss_ratio?.toFixed(2) ?? '-'}
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">交易次数</div>
                <div className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  {backtestResult.total_trades ?? '-'}
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">最大回撤持续天数</div>
                <div className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  {backtestResult.drawdown_duration ?? '-'}
                </div>
              </div>
              <div className={`p-2 sm:p-3 rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-50'}`}>
                <div className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">交易成本</div>
                <div className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
                  {backtestResult.transaction_costs?.toFixed(2) ?? '-'}%
                </div>
              </div>
            </div>

            <div className="mb-2 text-sm text-gray-600 dark:text-gray-400">
              回测区间: {backtestResult.start_date} 至 {backtestResult.end_date}
              · 交易日: {backtestResult.trading_days} 天
            </div>

            {/* 权益曲线图 - 移动端更小高度 */}
            {backtestResult.equity_curve && backtestResult.equity_curve.length > 0 && getChartData && (
              <div className="h-60 sm:h-80 border rounded p-3 sm:p-4 bg-white dark:bg-gray-800 mb-3 sm:mb-4">
                <h4 className="text-base sm:text-lg font-semibold mb-2 sm:mb-3 text-gray-900 dark:text-white">权益曲线 (初始值=1)</h4>
                <Line data={getChartData} options={adaptedChartOptions} />
              </div>
            )}

            {/* 回撤曲线图 - 移动端更小高度 */}
            {backtestResult.equity_curve && backtestResult.equity_curve.length > 0 && (
              <div className="h-48 sm:h-64 border rounded p-3 sm:p-4 bg-white dark:bg-gray-800">
                <h4 className="text-base sm:text-lg font-semibold mb-2 sm:mb-3 text-gray-900 dark:text-white">回撤曲线 (百分比)</h4>
                <Line data={getDrawdownChartData()!} options={getDrawdownChartOptions()} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
