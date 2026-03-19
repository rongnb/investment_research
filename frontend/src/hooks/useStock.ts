import { useState, useCallback, useEffect } from 'react';
import { stockApi } from '@/api';
import type { Stock, StockPrice, StockDetail } from '@/types';

export const useStockSearch = () => {
  const [searchResults, setSearchResults] = useState<Stock[]>([]);
  const [searching, setSearching] = useState(false);

  const search = useCallback(async (keyword: string) => {
    if (!keyword || keyword.length < 1) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const results = await stockApi.searchStocks(keyword);
      setSearchResults(results || []);
    } catch (error) {
      console.error('Stock search failed:', error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  const clearSearch = useCallback(() => {
    setSearchResults([]);
  }, []);

  return {
    searchResults,
    searching,
    search,
    clearSearch,
  };
};

export const useStockDetail = (symbol: string | null) => {
  const [detail, setDetail] = useState<StockDetail | null>(null);
  const [prices, setPrices] = useState<StockPrice[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDetail = useCallback(async () => {
    if (!symbol) return;

    setLoading(true);
    setError(null);

    try {
      const [detailData, pricesData] = await Promise.all([
        stockApi.getStockDetail(symbol),
        stockApi.getStockPrices(symbol, {
          startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          endDate: new Date().toISOString().split('T')[0],
        }),
      ]);

      setDetail(detailData);
      setPrices(pricesData || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取股票详情失败');
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  return {
    detail,
    prices,
    loading,
    error,
    refresh: fetchDetail,
  };
};

export const useStockList = (params?: { market?: string; industry?: string; page?: number; pageSize?: number }) => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStocks = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await stockApi.getStocks(params);
      setStocks(result?.items || []);
      setTotal(result?.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取股票列表失败');
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchStocks();
  }, [fetchStocks]);

  return {
    stocks,
    total,
    loading,
    error,
    refresh: fetchStocks,
  };
};