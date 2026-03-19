import React from 'react';
import { Layout, Menu } from 'antd';
import type { MenuProps } from 'antd';
import {
  HomeOutlined,
  LineChartOutlined,
  BarChartOutlined,
  FundOutlined,
  StockOutlined,
  FilterOutlined,
  SettingOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider: AntSider } = Layout;

interface SiderProps {
  collapsed?: boolean;
  onCollapse?: (collapsed: boolean) => void;
}

export const Sider: React.FC<SiderProps> = ({ collapsed, onCollapse }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems: MenuProps['items'] = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: '/stock',
      icon: <StockOutlined />,
      label: '股票详情',
    },
    {
      key: '/macro',
      icon: <FundOutlined />,
      label: '宏观分析',
    },
    {
      key: '/technical',
      icon: <LineChartOutlined />,
      label: '技术分析',
    },
    {
      key: '/backtest',
      icon: <BarChartOutlined />,
      label: '策略回测',
    },
    {
      key: '/screener',
      icon: <FilterOutlined />,
      label: '股票筛选',
    },
    {
      key: '/ai-assistant',
      icon: <ThunderboltOutlined />,
      label: 'AI助手',
    },
    {
      type: 'divider',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
  ];

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key);
  };

  return (
    <AntSider
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      breakpoint="lg"
      collapsedWidth={80}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 99,
      }}
    >
      <div
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold',
          fontSize: collapsed ? 14 : 16,
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        {collapsed ? '投研' : '投资研究系统'}
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ borderRight: 0 }}
      />
    </AntSider>
  );
};

export default Sider;