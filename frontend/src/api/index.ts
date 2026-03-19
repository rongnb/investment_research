import { request } from './client';
import type {
  Stock,
  StockPrice,
  StockDetail,
  RealTimeQuote,
  MacroIndicator,
  CycleAnalysis,
  ScenarioAnalysis,
  PolicyImpact,
  TechnicalIndicators,
  BacktestParams,
  BacktestResult,
  ScreenerParams,
  ScreenerResult,
} from '@/types';

// 股票相关API
export const stockApi = {
  // 获取股票列表
  getStocks: (params?: { market?: string; industry?: string; page?: number; pageSize?: number }) =>
    request.get<{ items: Stock[]; total: number }>('/stocks', { params }),

  // 搜索股票
  searchStocks: (keyword: string) =>
    request.get<Stock[]>('/stocks/search', { params: { keyword } }),

  // 获取股票详情
  getStockDetail: (symbol: string) =>
    request.get<StockDetail>(`/stocks/${symbol}`),

  // 获取股票价格历史
  getStockPrices: (symbol: string, params: { startDate: string; endDate: string; frequency?: 'd' | 'w' | 'm' }) =>
    request.get<StockPrice[]>(`/stocks/${symbol}/prices`, { params }),

  // 获取实时行情
  getRealTimeQuote: (symbol: string) =>
    request.get<RealTimeQuote>(`/stocks/${symbol}/quote`),

  // 批量获取实时行情
  getRealTimeQuotes: (symbols: string[]) =>
    request.post<RealTimeQuote[]>('/stocks/quotes', symbols),
};

// 宏观经济相关API
export const macroApi = {
  // 获取宏观指标列表
  getIndicators: (params?: { category?: string; startDate?: string; endDate?: string }) =>
    request.get<MacroIndicator[]>('/macro/indicators', { params }),

  // 获取特定指标的历史数据
  getIndicatorHistory: (indicatorId: string, params?: { startDate?: string; endDate?: string }) =>
    request.get<{ date: string; value: number }[]>(`/macro/indicators/${indicatorId}/history`, { params }),

  // 经济周期分析
  analyzeCycle: (params?: { indicators?: MacroIndicator[] }) =>
    request.post<CycleAnalysis>('/macro/cycle/analysis', params),

  // 情景分析
  analyzeScenario: (params?: { indicators?: MacroIndicator[] }) =>
    request.post<ScenarioAnalysis>('/macro/scenario/analysis', params),

  // 政策影响分析
  analyzePolicy: (policyType?: string) =>
    request.post<PolicyImpact[]>('/macro/policy/analysis', { policyType }),
};

// 技术分析相关API
export const technicalApi = {
  // 获取技术指标
  getIndicators: (symbol: string, params?: { date?: string; indicators?: string[] }) =>
    request.get<TechnicalIndicators>(`/technical/indicators/${symbol}`, { params }),

  // 计算自定义指标
  calculateIndicators: (symbol: string, params: { startDate: string; endDate: string; indicators: string[] }) =>
    request.post<TechnicalIndicators[]>(`/technical/indicators/${symbol}/calculate`, params),

  // 获取形态信号
  getPatternSignals: (symbol: string, params?: { startDate?: string; endDate?: string }) =>
    request.get<{ signals: { type: string; strength: number; description: string; date: string }[] }>(
      `/technical/patterns/${symbol}`,
      { params }
    ),
};

// 回测相关API
export const backtestApi = {
  // 运行回测
  runBacktest: (params: BacktestParams) =>
    request.post<BacktestResult>('/backtest', params),

  // 获取回测结果
  getBacktestResult: (id: string) =>
    request.get<BacktestResult>(`/backtest/${id}`),

  // 获取回测历史
  getBacktestHistory: (params?: { page?: number; pageSize?: number }) =>
    request.get<{ items: BacktestResult[]; total: number }>('/backtest/history', { params }),
};

// 筛选器相关API
export const screenerApi = {
  // 股票筛选
  screen: (params: ScreenerParams) =>
    request.post<ScreenerResult>('/screener', params),

  // 获取筛选条件选项
  getOptions: () =>
    request.get<{ markets: string[]; industries: string[] }>('/screener/options'),
};

// 系统相关API
export const systemApi = {
  // 健康检查
  health: () => request.get<{ status: string; timestamp: number }>('/health'),

  // 系统状态
  status: () => request.get<{ version: string; uptime: number; dataSource: string }>('/api/v1/system/status'),
};