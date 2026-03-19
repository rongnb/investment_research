import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, Row, Col, Descriptions, Table, Tabs, Space, Button, Statistic, Tag, Divider, message } from 'antd';
import { ReloadOutlined, StarOutlined, StarFilled, ExportOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { KLineChart, LineChart, BarChart } from '@/components/charts';
import { Loading } from '@/components/common';
import { useStockDetail } from '@/hooks';
import type { StockPrice } from '@/types';

const StockDetailPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const symbol = searchParams.get('symbol') || '000001';
  const { detail, prices, loading, error, refresh } = useStockDetail(symbol);
  const [favorite, setFavorite] = useState(false);
  const [activeTab, setActiveTab] = useState('chart');

  if (loading) {
    return <Loading tip="加载股票数据..." />;
  }

  if (error) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <p style={{ color: '#f56c6c' }}>加载失败: {error}</p>
          <Button type="primary" onClick={refresh}>重试</Button>
        </div>
      </Card>
    );
  }

  const priceColumns: ColumnsType<StockPrice> = [
    { title: '日期', dataIndex: 'date', key: 'date' },
    { title: '开盘', dataIndex: 'open', key: 'open', render: (v) => v?.toFixed(2) },
    { title: '收盘', dataIndex: 'close', key: 'close', render: (v) => v?.toFixed(2) },
    { title: '最高', dataIndex: 'high', key: 'high', render: (v) => v?.toFixed(2) },
    { title: '最低', dataIndex: 'low', key: 'low', render: (v) => v?.toFixed(2) },
    { title: '成交量', dataIndex: 'volume', key: 'volume', render: (v) => v?.toLocaleString() },
    { title: '涨跌幅', dataIndex: 'pctChange', key: 'pctChange', render: (v) => (
      <span style={{ color: (v || 0) >= 0 ? '#f56c6c' : '#67c23a' }}>
        {v ? `${v.toFixed(2)}%` : '-'}
      </span>
    )},
  ];

  const kLineData = prices.slice(-120);
  const latestPrice = prices[prices.length - 1];
  const prevPrice = prices[prices.length - 2];
  const priceChange = latestPrice && prevPrice ? latestPrice.close - prevPrice.close : 0;
  const pctChange = latestPrice && prevPrice ? (priceChange / prevPrice.close) * 100 : 0;

  const tabItems = [
    {
      key: 'chart',
      label: 'K线走势',
      children: (
        <KLineChart
          data={kLineData}
          title={`${symbol} K线图`}
          height={500}
          showVolume
          showMA
        />
      ),
    },
    {
      key: 'indicators',
      label: '技术指标',
      children: (
        <Row gutter={16}>
          <Col span={12}>
            <LineChart
              data={prices.slice(-30).map((p) => ({ name: p.date, value: p.close }))}
              title="收盘价走势"
              height={250}
            />
          </Col>
          <Col span={12}>
            <BarChart
              data={prices.slice(-30).map((p) => ({ name: p.date.slice(5), value: p.volume }))}
              title="成交量"
              height={250}
            />
          </Col>
        </Row>
      ),
    },
    {
      key: 'history',
      label: '历史数据',
      children: (
        <Table
          columns={priceColumns}
          dataSource={prices.slice(0, 50).map((p, i) => ({ ...p, key: i }))}
          pagination={{ pageSize: 10 }}
          size="small"
          scroll={{ x: 800 }}
        />
      ),
    },
  ];

  return (
    <div>
      <Card
        title={
          <Space>
            <span style={{ fontSize: 20, fontWeight: 'bold' }}>
              {detail?.stock?.name || symbol}
            </span>
            <Tag color="blue">{symbol}</Tag>
            <Tag>{detail?.stock?.market}</Tag>
            <Button
              type="text"
              icon={favorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
              onClick={() => setFavorite(!favorite)}
            >
              {favorite ? '已收藏' : '收藏'}
            </Button>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ExportOutlined />} onClick={() => message.success('导出功能开发中')}>
              导出
            </Button>
            <Button icon={<ReloadOutlined />} onClick={refresh}>
              刷新
            </Button>
          </Space>
        }
      >
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="最新价"
              value={latestPrice?.close || 0}
              precision={2}
              valueStyle={{ color: priceChange >= 0 ? '#f56c6c' : '#67c23a' }}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Statistic
              title="涨跌"
              value={priceChange}
              precision={2}
              valueStyle={{ color: priceChange >= 0 ? '#f56c6c' : '#67c23a' }}
              prefix={priceChange >= 0 ? '+' : ''}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Statistic
              title="涨跌幅"
              value={pctChange}
              precision={2}
              valueStyle={{ color: pctChange >= 0 ? '#f56c6c' : '#67c23a' }}
              suffix="%"
              prefix={pctChange >= 0 ? '+' : ''}
            />
          </Col>
          <Col xs={12} sm={6} md={4}>
            <Statistic
              title="成交量"
              value={latestPrice?.volume || 0}
              valueStyle={{ fontSize: 16 }}
            />
          </Col>
          <Col xs={12} sm={6} md={6}>
            <Statistic
              title="成交额"
              value={latestPrice?.amount || 0}
              precision={0}
              suffix="元"
            />
          </Col>
        </Row>

        <Descriptions bordered size="small" column={{ xs: 1, sm: 2, md: 4 }}>
          <Descriptions.Item label="开盘">{latestPrice?.open?.toFixed(2)}</Descriptions.Item>
          <Descriptions.Item label="最高">{latestPrice?.high?.toFixed(2)}</Descriptions.Item>
          <Descriptions.Item label="最低">{latestPrice?.low?.toFixed(2)}</Descriptions.Item>
          <Descriptions.Item label="昨收">{prevPrice?.close?.toFixed(2)}</Descriptions.Item>
          <Descriptions.Item label="行业">{detail?.stock?.industry || '-'}</Descriptions.Item>
          <Descriptions.Item label="上市日期">{detail?.stock?.listDate || '-'}</Descriptions.Item>
        </Descriptions>

        <Divider />

        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>
    </div>
  );
};

export default StockDetailPage;