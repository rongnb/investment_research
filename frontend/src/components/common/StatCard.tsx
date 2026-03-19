import React from 'react';
import { Card, Statistic, Row, Col } from 'antd';
import { CaretUpOutlined, CaretDownOutlined } from '@ant-design/icons';

interface StatCardProps {
  title: string;
  value: number | string;
  prefix?: React.ReactNode;
  suffix?: string;
  change?: number;
  precision?: number;
  loading?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  prefix,
  suffix,
  change,
  precision = 2,
  loading = false,
}) => {
  const isPositive = change !== undefined && change >= 0;

  return (
    <Card loading={loading}>
      <Statistic
        title={title}
        value={value}
        precision={precision}
        prefix={prefix}
        suffix={suffix}
      />
      {change !== undefined && (
        <div style={{ marginTop: 8 }}>
          <span style={{ color: isPositive ? '#f56c6c' : '#67c23a' }}>
            {isPositive ? <CaretUpOutlined /> : <CaretDownOutlined />}
            {Math.abs(change).toFixed(2)}%
          </span>
          <span style={{ marginLeft: 8, color: '#999' }}>较上期</span>
        </div>
      )}
    </Card>
  );
};

interface StatGridProps {
  data: StatCardProps[];
  gutter?: number;
}

export const StatGrid: React.FC<StatGridProps> = ({ data, gutter = 16 }) => {
  return (
    <Row gutter={gutter}>
      {data.map((item, index) => (
        <Col key={index} xs={24} sm={12} md={6}>
          <StatCard {...item} />
        </Col>
      ))}
    </Row>
  );
};

export default StatCard;