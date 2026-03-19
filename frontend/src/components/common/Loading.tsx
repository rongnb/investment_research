import React from 'react';
import { Spin } from 'antd';

interface LoadingProps {
  tip?: string;
  size?: 'small' | 'default' | 'large';
  fullscreen?: boolean;
}

export const Loading: React.FC<LoadingProps> = ({
  tip = '加载中...',
  size = 'default',
  fullscreen = false,
}) => {
  if (fullscreen) {
    return (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(255, 255, 255, 0.8)',
          zIndex: 9999,
        }}
      >
        <Spin size={size} tip={tip} />
      </div>
    );
  }

  return <Spin size={size} tip={tip} />;
};

export default Loading;