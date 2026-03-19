import { useState, useCallback, useEffect } from 'react';
import { macroApi } from '@/api';
import type { MacroIndicator, CycleAnalysis, ScenarioAnalysis, PolicyImpact } from '@/types';

export const useMacroIndicators = (params?: { category?: string; startDate?: string; endDate?: string }) => {
  const [indicators, setIndicators] = useState<MacroIndicator[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchIndicators = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await macroApi.getIndicators(params);
      setIndicators(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取宏观指标失败');
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    fetchIndicators();
  }, [fetchIndicators]);

  return {
    indicators,
    loading,
    error,
    refresh: fetchIndicators,
  };
};

export const useCycleAnalysis = () => {
  const [analysis, setAnalysis] = useState<CycleAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (indicators?: MacroIndicator[]) => {
    setLoading(true);
    setError(null);

    try {
      const data = await macroApi.analyzeCycle({ indicators });
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '周期分析失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const clearAnalysis = useCallback(() => {
    setAnalysis(null);
  }, []);

  return {
    analysis,
    loading,
    error,
    analyze,
    clearAnalysis,
  };
};

export const useScenarioAnalysis = () => {
  const [analysis, setAnalysis] = useState<ScenarioAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async (indicators?: MacroIndicator[]) => {
    setLoading(true);
    setError(null);

    try {
      const data = await macroApi.analyzeScenario({ indicators });
      setAnalysis(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '情景分析失败');
    } finally {
      setLoading(false);
    }
  }, []);

  const clearAnalysis = useCallback(() => {
    setAnalysis(null);
  }, []);

  return {
    analysis,
    loading,
    error,
    analyze,
    clearAnalysis,
  };
};

export const usePolicyImpact = (policyType?: string) => {
  const [impacts, setImpacts] = useState<PolicyImpact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await macroApi.analyzePolicy(policyType);
      setImpacts(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '政策分析失败');
    } finally {
      setLoading(false);
    }
  }, [policyType]);

  useEffect(() => {
    analyze();
  }, [analyze]);

  return {
    impacts,
    loading,
    error,
    refresh: analyze,
  };
};