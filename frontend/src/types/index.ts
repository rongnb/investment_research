// 股票相关类型
export interface Stock {
  symbol: string;
  name: string;
  market: 'SH' | 'SZ' | 'BJ';
  industry?: string;
  listDate?: string;
}

export interface StockPrice {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount?: number;
  change?: number;
  pctChange?: number;
}

export interface StockDetail {
  stock: Stock;
  prices: StockPrice[];
  realTime?: RealTimeQuote;
}

export interface RealTimeQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  pctChange: number;
  volume: number;
  amount: number;
  open: number;
  high: number;
  low: number;
  close: number;
  timestamp: number;
}

// 宏观经济相关类型
export interface MacroIndicator {
  id: string;
  name: string;
  value: number;
  unit: string;
  date: string;
  category: 'gdp' | 'pmi' | 'cpi' | 'interest' | 'money' | 'employment' | 'other';
}

export interface CycleAnalysis {
  currentCycle: 'recovery' | 'expansion' | 'peak' | 'contraction' | 'trough';
  confidence: number;
  score: number;
  indicators: {
    name: string;
    value: number;
    contribution: number;
  }[];
  recommendations: string[];
  lastUpdated: string;
}

export interface ScenarioAnalysis {
  scenarios: {
    name: 'bullish' | 'base' | 'bearish';
    probability: number;
    expectedReturn: number;
    description: string;
  }[];
  recommendedAllocation: {
    asset: string;
    weight: number;
  }[];
  riskScore: number;
}

export interface PolicyImpact {
  policyType: 'monetary' | 'fiscal' | 'industry';
  direction: 'positive' | 'negative' | 'neutral';
  impactScore: number;
  description: string;
  affectedIndustries: string[];
  recommendations: string[];
}

// 技术指标相关类型
export interface TechnicalIndicators {
  symbol: string;
  date: string;
  ma?: {
    ma5: number;
    ma10: number;
    ma20: number;
    ma60: number;
  };
  macd?: {
    diff: number;
    dea: number;
    hist: number;
  };
  rsi?: {
    rsi6: number;
    rsi12: number;
    rsi24: number;
  };
  kdj?: {
    k: number;
    d: number;
    j: number;
  };
  bollinger?: {
    upper: number;
    middle: number;
    lower: number;
  };
  fractal?: {
    top: boolean;
    bottom: boolean;
  };
}

export interface PatternSignal {
  type: 'golden_cross' | 'death_cross' | 'head_shoulders' | 'double_top' | 'double_bottom' | 'bullish_divergence' | 'bearish_divergence';
  strength: number;
  description: string;
  date: string;
}

// 回测相关类型
export interface BacktestParams {
  symbol: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  strategy: string;
  parameters: Record<string, unknown>;
}

export interface BacktestResult {
  params: BacktestParams;
  summary: {
    totalReturn: number;
    annualReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
    totalTrades: number;
  };
  trades: Trade[];
  equityCurve: {
    date: string;
    value: number;
  }[];
  monthlyReturns: {
    month: string;
    return: number;
  }[];
}

export interface Trade {
  date: string;
  type: 'buy' | 'sell';
  price: number;
  quantity: number;
  amount: number;
  reason?: string;
}

// 筛选器相关类型
export interface ScreenerParams {
  market?: 'SH' | 'SZ' | 'BJ' | 'ALL';
  industry?: string;
  priceMin?: number;
  priceMax?: number;
  peMin?: number;
  peMax?: number;
  pbMin?: number;
  pbMax?: number;
  marketCapMin?: number;
  marketCapMax?: number;
  volumeMin?: number;
  turnoverRateMin?: number;
 ROEMin?: number;
  revenueGrowthMin?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  page?: number;
  pageSize?: number;
}

export interface ScreenerResult {
  stocks: Stock[];
  total: number;
  page: number;
  pageSize: number;
}

// 通用类型
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface PageParams {
  page: number;
  pageSize: number;
}

export interface PagedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface WebSocketMessage {
  type: 'quote' | 'trade' | 'news' | 'alert';
  data: unknown;
  timestamp: number;
}