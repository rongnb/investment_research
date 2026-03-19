import React, { useState } from 'react';
import { Layout, Input, Switch, Button, Dropdown, Space, Badge, theme } from 'antd';
import type { MenuProps } from 'antd';
import {
  BellOutlined,
  UserOutlined,
  SunOutlined,
  MoonOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '@/store';
import { useStockSearch } from '@/hooks';

const { Header: AntHeader } = Layout;

interface HeaderProps {
  onMenuClick?: () => void;
}

export const Header: React.FC<HeaderProps> = () => {
  const navigate = useNavigate();
  const { theme: appTheme, setTheme, collapsed, toggleCollapsed } = useAppStore();
  const { token } = theme.useToken();
  const { searchResults, searching, search, clearSearch } = useStockSearch();
  const [searchValue, setSearchValue] = useState('');

  const handleSearch = (value: string) => {
    setSearchValue(value);
    if (value) {
      search(value);
    } else {
      clearSearch();
    }
  };

  const handleSelectStock = (symbol: string) => {
    navigate(`/stock?symbol=${symbol}`);
    clearSearch();
    setSearchValue('');
  };

  const userMenuItems: MenuProps['items'] = [
    { key: 'profile', label: '个人资料' },
    { key: 'settings', label: '设置' },
    { type: 'divider' },
    { key: 'logout', label: '退出登录', danger: true },
  ];

  return (
    <AntHeader
      style={{
        padding: '0 16px',
        background: token.colorBgContainer,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: `1px solid ${token.colorBorder}`,
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      <Space size="middle">
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleCollapsed}
          style={{ fontSize: 16 }}
        />
        <div
          style={{
            fontWeight: 'bold',
            fontSize: 18,
            color: token.colorPrimary,
            cursor: 'pointer',
          }}
          onClick={() => navigate('/')}
        >
          投资研究系统
        </div>
      </Space>

      <div style={{ flex: 1, maxWidth: 500, margin: '0 24px' }}>
        <Input.Search
          placeholder="搜索股票代码或名称..."
          allowClear
          loading={searching}
          value={searchValue}
          onChange={(e) => handleSearch(e.target.value)}
          onSearch={handleSearch}
          style={{ width: '100%' }}
          dropdownRender={(menu) => (
            <div>
              {searchResults.length > 0 ? (
                menu
              ) : searchValue ? (
                <div style={{ padding: '8px 12px', color: token.colorTextSecondary }}>
                  未找到相关股票
                </div>
              ) : null}
            </div>
          )}
          dropdownStyle={{ maxHeight: 400, overflow: 'auto' }}
          options={searchResults.map((stock) => ({
            value: stock.symbol,
            label: (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>
                  {stock.symbol} - {stock.name}
                </span>
                <span style={{ color: token.colorTextSecondary, fontSize: 12 }}>
                  {stock.market}
                </span>
              </div>
            ),
            key: stock.symbol,
            onClick: () => handleSelectStock(stock.symbol),
          }))}
        />
      </div>

      <Space size="middle">
        <Switch
          checked={appTheme === 'dark'}
          checkedChildren={<MoonOutlined />}
          unCheckedChildren={<SunOutlined />}
          onChange={(checked) => setTheme(checked ? 'dark' : 'light')}
        />
        <Badge count={5} size="small">
          <Button type="text" icon={<BellOutlined />} />
        </Badge>
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Button type="text" icon={<UserOutlined />} />
        </Dropdown>
      </Space>
    </AntHeader>
  );
};

export default Header;