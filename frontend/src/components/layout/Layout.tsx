import React from 'react';
import { Layout, ConfigProvider, theme } from 'antd';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sider from './Sider';
import { useAppStore } from '@/store';

const { Content, Footer } = Layout;

const { defaultAlgorithm, darkAlgorithm } = theme;

export const AppLayout: React.FC = () => {
  const { theme: appTheme, collapsed, setCollapsed } = useAppStore();

  return (
    <ConfigProvider
      theme={{
        algorithm: appTheme === 'dark' ? darkAlgorithm : defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 4,
        },
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Sider collapsed={collapsed} onCollapse={setCollapsed} />
        <Layout
          style={{
            marginLeft: collapsed ? 80 : 200,
            transition: 'margin-left 0.2s',
          }}
        >
          <Header />
          <Content
            style={{
              margin: 16,
              padding: 24,
              background: '#fff',
              borderRadius: 8,
              minHeight: 280,
            }}
          >
            <Outlet />
          </Content>
          <Footer
            style={{
              textAlign: 'center',
              background: 'transparent',
            }}
          >
            投资研究系统 ©{new Date().getFullYear()} - 量化投资分析平台
          </Footer>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
};

export default AppLayout;