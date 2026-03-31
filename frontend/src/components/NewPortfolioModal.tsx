import React from 'react';

interface NewPortfolioModalProps {
  show: boolean;
  darkMode: boolean;
  name: string;
  description: string;
  cash: string;
  onClose: () => void;
  onCreate: () => void;
  onNameChange: (value: string) => void;
  onDescChange: (value: string) => void;
  onCashChange: (value: string) => void;
}

export default function NewPortfolioModal({
  show,
  darkMode,
  name,
  description,
  cash,
  onClose,
  onCreate,
  onNameChange,
  onDescChange,
  onCashChange,
}: NewPortfolioModalProps) {
  if (!show) return null;

  const bgClass = darkMode ? 'bg-gray-800' : 'bg-white';
  const textClass = darkMode ? 'text-white' : 'text-gray-900';
  const labelClass = darkMode ? 'text-gray-300' : 'text-gray-700';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div className={`${bgClass} p-6 rounded-lg w-96`}>
        <h3 className={`text-xl font-bold mb-4 ${textClass}`}>新建投资组合</h3>
        <div className="space-y-3">
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>组合名称</label>
            <input
              type="text"
              className="w-full border rounded px-3 py-2"
              value={name}
              onChange={e => onNameChange(e.target.value)}
            />
          </div>
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>描述</label>
            <textarea
              className="w-full border rounded px-3 py-2"
              value={description}
              onChange={e => onDescChange(e.target.value)}
            />
          </div>
          <div>
            <label className={`block text-sm font-medium mb-1 ${labelClass}`}>初始现金</label>
            <input
              type="number"
              className="w-full border rounded px-3 py-2"
              value={cash}
              onChange={e => onCashChange(e.target.value)}
            />
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
