import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout';
import StockDetailPage from './pages/StockDetail';
import MacroAnalysisPage from './pages/MacroAnalysis';

const HomePage: React.FC = () => {
  return (
    <div>
      <h1>投资研究系统</h1>
      <p>欢迎使用投资研究系统</p>
    </div>
  );
};

const AppRoutes: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<HomePage />} />
          <Route path="stock" element={<StockDetailPage />} />
          <Route path="macro" element={<MacroAnalysisPage />} />
          <Route path="technical" element={<div>技术分析页面开发中...</div>} />
          <Route path="backtest" element={<div>策略回测页面开发中...</div>} />
          <Route path="screener" element={<div>股票筛选页面开发中...</div>} />
          <Route path="settings" element={<div>设置页面开发中...</div>} />
          <Route path="ai-assistant" element={<div>AI助手页面开发中...</div>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default AppRoutes;