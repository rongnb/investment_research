import React from 'react';

interface CreateStrategyModalProps {
  show: boolean;
  darkMode: boolean;
  newStrategyName: string;
  newStrategyDesc: string;
  newStrategyCategory: string;
  newStrategyParams: string;
  onClose: () => void;
  onCreate: () => void;
  onNameChange: (value: string) => void;
  onDescChange: (value: string) => void;
  onCategoryChange: (value: string) => void;
  onParamsChange: (value: string) => void;
}

// 提取静态分类选项
const CATEGORY_OPTIONS = [
  { value: '被动投资', label: '被动投资' },
  { value: '价值投资', label: '价值投资' },
  { value: '成长投资', label: '成长投资' },
  { value: '资产配置', label: '资产配置' },
  { value: '行业轮动', label: '行业轮动' },
  { value: '趋势跟踪', label: '趋势跟踪' },
  { value: '风险管理', label: '风险管理' },
];

export default function CreateStrategyModal({
  show,
  darkMode,
  newStrategyName,
  newStrategyDesc,
  newStrategyCategory,
  newStrategyParams,
  onClose,
  onCreate,
  onNameChange,
  onDescChange,
  onCategoryChange,
  onParamsChange,
}: CreateStrategyModalProps) {
  if (!show) return null;

  const bgClass = darkMode ? 'bg-gray-800' : 'bg-white';
  const textClass = darkMode ? 'text-white' : 'text-gray-900';
  const labelClass = darkMode ? 'text-gray-300' : 'text-gray-700';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className={`p-6 rounded-lg w-96 ${bgClass}`}>
        <h3 className={`text-xl font-bold mb-4 ${textClass}`}>
          + 创建自定义策略
        </h3>
        <div className="space-y-3">
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>策略名称 *</label>
            <input
              type="text"
              placeholder="我的策略"
              className="w-full border rounded px-3 py-2"
              value={newStrategyName}
              onChange={e => onNameChange(e.target.value)}
            />
          </div>
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>分类</label>
            <select
              className="w-full border rounded px-3 py-2"
              value={newStrategyCategory}
              onChange={e => onCategoryChange(e.target.value)}
            >
              {CATEGORY_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>策略描述</label>
            <textarea
              className="w-full border rounded px-3 py-2"
              rows={4}
              value={newStrategyDesc}
              onChange={e => onDescChange(e.target.value)}
            />
          </div>
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>参数 (JSON)</label>
            <textarea
              className="w-full border rounded px-3 py-2 font-mono text-sm"
              rows={3}
              placeholder='{"param1": 10}'
              value={newStrategyParams}
              onChange={e => onParamsChange(e.target.value)}
            />
            <p className="text-xs text-gray-500 mt-1">系统会根据策略名称自动匹配回测算法</p>
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
            onClick={onCreate}
          >
            创建
          </button>
        </div>
      </div>
    </div>
  );
}
