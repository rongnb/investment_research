import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Stock, RealTimeQuote, MacroIndicator, ScreenerParams } from '@/types';

interface AppState {
  // 主题设置
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  toggleTheme: () => void;

  // 侧边栏状态
  collapsed: boolean;
  setCollapsed: (collapsed: boolean) => void;
  toggleCollapsed: () => void;

  // 当前选中的股票
  selectedStock: Stock | null;
  setSelectedStock: (stock: Stock | null) => void;

  // 实时行情数据
  realTimeQuotes: Map<string, RealTimeQuote>;
  updateRealTimeQuote: (quote: RealTimeQuote) => void;
  setRealTimeQuotes: (quotes: RealTimeQuote[]) => void;

  // 宏观经济数据
  macroIndicators: MacroIndicator[];
  setMacroIndicators: (indicators: MacroIndicator[]) => void;

  // 筛选器参数
  screenerParams: Partial<ScreenerParams>;
  setScreenerParams: (params: Partial<ScreenerParams>) => void;
  resetScreenerParams: () => void;

  // 加载状态
  loading: boolean;
  setLoading: (loading: boolean) => void;

  // 错误信息
  error: string | null;
  setError: (error: string | null) => void;
  clearError: () => void;
}

const defaultScreenerParams: Partial<ScreenerParams> = {
  market: 'ALL',
  page: 1,
  pageSize: 20,
  sortBy: 'marketCap',
  sortOrder: 'desc',
};

export const useAppStore = create<AppState>()(
  persist(
    (set, _get) => ({
      // 主题设置
      theme: 'light',
      setTheme: (theme) => set({ theme }),
      toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),

      // 侧边栏状态
      collapsed: false,
      setCollapsed: (collapsed) => set({ collapsed }),
      toggleCollapsed: () => set((state) => ({ collapsed: !state.collapsed })),

      // 当前选中的股票
      selectedStock: null,
      setSelectedStock: (stock) => set({ selectedStock: stock }),

      // 实时行情数据
      realTimeQuotes: new Map(),
      updateRealTimeQuote: (quote) =>
        set((state) => {
          const newMap = new Map(state.realTimeQuotes);
          newMap.set(quote.symbol, quote);
          return { realTimeQuotes: newMap };
        }),
      setRealTimeQuotes: (quotes) => {
        const newMap = new Map<string, RealTimeQuote>();
        quotes.forEach((q) => newMap.set(q.symbol, q));
        set({ realTimeQuotes: newMap });
      },

      // 宏观经济数据
      macroIndicators: [],
      setMacroIndicators: (indicators) => set({ macroIndicators: indicators }),

      // 筛选器参数
      screenerParams: defaultScreenerParams,
      setScreenerParams: (params) =>
        set((state) => ({
          screenerParams: { ...state.screenerParams, ...params },
        })),
      resetScreenerParams: () => set({ screenerParams: defaultScreenerParams }),

      // 加载状态
      loading: false,
      setLoading: (loading) => set({ loading }),

      // 错误信息
      error: null,
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'investment-research-storage',
      partialize: (state) => ({
        theme: state.theme,
        collapsed: state.collapsed,
        screenerParams: state.screenerParams,
      }),
    }
  )
);