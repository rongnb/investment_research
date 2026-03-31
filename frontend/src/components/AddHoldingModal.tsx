import React from 'react';
import { Portfolio } from '../types';

interface AddHoldingModalProps {
  show: boolean;
  portfolio: Portfolio | null;
  darkMode: boolean;
  symbol: string;
  name: string;
  quantity: string;
  cost: string;
  type: string;
  onClose: () => void;
  onAdd: () => void;
  onSymbolChange: (value: string) => void;
  onNameChange: (value: string) => void;
  onQuantityChange: (value: string) => void;
  onCostChange: (value: string) => void;
  onTypeChange: (value: string) => void;
}

// 静态选项提取到组件外部
const ASSET_TYPES = [
  { value: 'stock', label: '股票' },
  { value: 'etf', label: 'ETF' },
  { value: 'fund', label: '基金' },
  { value: 'bond', label: '债券' },
];

export default function AddHoldingModal({
  show,
  portfolio,
  darkMode,
  symbol,
  name,
  quantity,
  cost,
  type,
  onClose,
  onAdd,
  onSymbolChange,
  onNameChange,
  onQuantityChange,
  onCostChange,
  onTypeChange,
}: AddHoldingModalProps) {
  if (!show || !portfolio) return null;

  const bgClass = darkMode ? 'bg-gray-800' : 'bg-white';
  const textClass = darkMode ? 'text-white' : 'text-gray-900';
  const labelClass = darkMode ? 'text-gray-300' : 'text-gray-700';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className={`${bgClass} p-6 rounded-lg w-96`}>
        <h3 className={`text-xl font-bold mb-4 ${textClass}`}>
          添加持仓 · {portfolio.name}
        </h3>
        <div className="space-y-3">
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>代码 *</label>
            <input
              type="text"
              placeholder="A股 600000，美股 AAPL"
              className="w-full border rounded px-3 py-2"
              value={symbol}
              onChange={e => onSymbolChange(e.target.value)}
            />
          </div>
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>名称</label>
            <input
              type="text"
              placeholder="贵州茅台"
              className="w-full border rounded px-3 py-2"
              value={name}
              onChange={e => onNameChange(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={`block text-sm font-medium mb-1 ${labelClass}`}>数量 *</label>
              <input
                type="number"
                step="0.01"
                className="w-full border rounded px-3 py-2"
                value={quantity}
                onChange={e => onQuantityChange(e.target.value)}
              />
            </div>
            <div>
              <label className={`block text-sm font-medium mb-1 ${labelClass}`}>成本价 *</label>
              <input
                type="number"
                step="0.01"
                className="w-full border rounded px-3 py-2"
                value={cost}
                onChange={e => onCostChange(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>资产类型</label>
            <select
              className="w-full border rounded px-3 py-2"
              value={type}
              onChange={e => onTypeChange(e.target.value)}
            >
              {ASSET_TYPES.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex justify-end space-x-2 mt-6">
          <button
            className={`px-4 py-2 border rounded ${darkMode ? 'border-gray-600 text-gray-300 hover:bg-gray-700' : 'border-gray-200 text-gray-600 hover:bg-gray-50'}`}
            onClick={onClose}
          >
            取消
          </button>
          <button
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            onClick={onAdd}
          >
            添加
          </button>
        </div>
      </div>
    </div>
  );
}
