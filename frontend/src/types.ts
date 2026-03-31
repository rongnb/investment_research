export interface Holding {
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

export interface Portfolio {
  id: number;
  name: string;
  description: string;
  cash: number;
  created_at: string;
  updated_at: string;
  holdings: Holding[];
}

export interface PortfolioSummary {
  portfolio_id: number;
  name: string;
  cash: number;
  holding_count: number;
  total_cost: number;
  total_market_value: number;
  total_gain_loss: number;
  total_gain_loss_percent: number;
}

export interface Strategy {
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

export interface BacktestHistory {
  id: number;
  strategy_id: number;
  strategy_name?: string;
  symbol: string;
  start_date: string | null;
  end_date: string | null;
  total_return: number | null;
  annual_return: number | null;
  sharpe_ratio: number | null;
  max_drawdown: number | null;
  created_at: string;
}

export interface BacktestResult {
  status: string;
  saved_result_id: number;
  strategy_id: number;
  symbol: string;
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  sortino_ratio?: number;
  calmar_ratio?: number;
  max_drawdown: number;
  volatility?: number;
  win_rate?: number;
  profit_loss_ratio?: number;
  total_trades?: number;
  drawdown_duration?: number;
  transaction_costs?: number;
  trades: any[];
  equity_curve: Array<{date: string; value: number}>;
  start_date: string;
  end_date: string;
  trading_days: number;
}

export interface CompareResult {
  status: string;
  symbol: string;
  start_date: string;
  end_date: string;
  trading_days: number;
  results: Array<{
    strategy_id: number;
    strategy_name: string;
    category: string;
    total_return: number;
    annual_return: number;
    sharpe_ratio: number;
    sortino_ratio?: number;
    calmar_ratio?: number;
    max_drawdown: number;
    volatility?: number;
    win_rate?: number;
    profit_loss_ratio?: number;
    equity_curve: Array<{date: string; value: number}>;
    trades_count: number;
  }>;
}

export const API_BASE = 'http://localhost:8000/api';
