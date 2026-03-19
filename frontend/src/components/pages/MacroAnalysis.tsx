import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Tabs, Table, Tag, Progress, Button, Space, Select, DatePicker, Statistic, message } from 'antd';
import { ReloadOutlined, DownloadOutlined, FileTextOutlined, LineChartOutlined, PieChartOutlined, FundOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { LineChart, BarChart, PieChart } from '@/components/charts';
import { StatCard } from '@/components/common';
import { useMacroIndicators, useCycleAnalysis, useScenarioAnalysis, usePolicyImpact } from '@/hooks';
import type { MacroIndicator, CycleAnalysis, ScenarioAnalysis, PolicyImpact } from '@/types';

const { RangePicker } = DatePicker;

const cycleLabels: Record<string, { text: string; color: string }> = {
  recovery: { text: '复苏', color: '#52c41a' },
  expansion: { text: '扩张', color: '#1890ff' },
  peak: { text: '顶峰', color: '#faad14' },
  contraction: { text: '收缩', color: '#fa8c16' },
  trough: { text: '低谷', color: '#f5222d' },
};

const MacroAnalysisPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [category, setCategory] = useState<string>('all');
  const { indicators, loading: indicatorsLoading, refresh: refreshIndicators } = useMacroIndicators({ category: category === 'all' ? undefined : category });
  const { analysis: cycleAnalysis, analyze: analyzeCycle } = useCycleAnalysis();
  const { analysis: scenarioAnalysis, analyze: analyzeScenario } = useScenarioAnalysis();
  const { impacts: policyImpacts } = usePolicyImpact();

  useEffect(() => {
    analyzeCycle();
    analyzeScenario();
  }, [analyzeCycle, analyzeScenario]);

  const indicatorColumns: ColumnsType<MacroIndicator> = [
    { title: '指标名称', dataIndex: 'name', key: 'name', width: 150 },
    { 
      title: '数值', 
      dataIndex: 'value', 
      key: 'value', 
      width: 120,
      render: (value: number, record: MacroIndicator) => `${value?.toFixed(2)} ${record.unit}`,
    },
    { title: '日期', dataIndex: 'date', key: 'date', width: 120 },
    { 
      title: '类别', 
      dataIndex: 'category', 
      key: 'category',
      width: 100,
      render: (cat: string) => {
        const colors: Record<string, string> = {
          gdp: 'blue',
          pmi: 'green',
          cpi: 'orange',
          interest: 'purple',
          money: 'cyan',
          employment: 'magenta',
        };
        return <Tag color={colors[cat] || 'default'}>{cat?.toUpperCase()}</Tag>;
      },
    },
  ];

  // 模拟数据（当API不可用时展示）
  const mockCycleData: CycleAnalysis = {
    currentCycle: 'expansion',
    confidence: 0.75,
    score: 68,
    indicators: [
      { name: 'GDP增速', value: 5.2, contribution: 15 },
      { name: 'PMI指数', value: 50.8, contribution: 18 },
      { name: 'CPI同比', value: 0.2, contribution: 12 },
      { name: '社融增速', value: 9.5, contribution: 13 },
      { name: '失业率', value: 5.2, contribution: 10 },
    ],
    recommendations: [
      '建议增配周期类权益资产',
      '债券配置建议偏向中短久期',
      '商品方面关注工业金属机会',
    ],
    lastUpdated: new Date().toISOString(),
  };

  const mockScenarioData: ScenarioAnalysis = {
    scenarios: [
      { name: 'bullish', probability: 0.25, expectedReturn: 15, description: '经济强劲复苏，政策持续发力' },
      { name: 'base', probability: 0.55, expectedReturn: 5, description: '经济平稳运行，保持稳增长基调' },
      { name: 'bearish', probability: 0.2, expectedReturn: -8, description: '经济下行压力加大，需要更多政策支持' },
    ],
    recommendedAllocation: [
      { asset: 'A股', weight: 35 },
      { asset: '债券', weight: 30 },
      { asset: '港股', weight: 15 },
      { asset: '商品', weight: 10 },
      { asset: '现金', weight: 10 },
    ],
    riskScore: 45,
  };

  const displayCycle = cycleAnalysis || mockCycleData;
  const displayScenario = scenarioAnalysis || mockScenarioData;

  const cycleTabItems = [
    {
      key: 'status',
      label: '周期状态',
      children: (
        <Card>
          <Row gutter={24}>
            <Col xs={24} md={8}>
              <Card>
                <Statistic
                  title="当前周期阶段"
                  value={cycleLabels[displayCycle.currentCycle]?.text || '未知'}
                  valueStyle={{ color: cycleLabels[displayCycle.currentCycle]?.color }}
                />
                <div style={{ marginTop: 16 }}>
                  <span>置信度：</span>
                  <Progress percent={displayCycle.confidence * 100} status="active" />
                </div>
              </Card>
            </Col>
            <Col xs={24} md={16}>
              <Card title="周期指标贡献度">
                <BarChart
                  data={displayCycle.indicators.map((i) => ({ name: i.name, value: i.contribution }))}
                  height={250}
                  horizontal
                />
              </Card>
            </Col>
          </Row>
          <Card title="投资建议" style={{ marginTop: 16 }}>
            <ul>
              {displayCycle.recommendations.map((rec, idx) => (
                <li key={idx} style={{ marginBottom: 8 }}>{rec}</li>
              ))}
            </ul>
          </Card>
        </Card>
      ),
    },
    {
      key: 'trends',
      label: '趋势分析',
      children: (
        <Card>
          <LineChart
            data={[
              { name: '1月', value: 45 },
              { name: '2月', value: 52 },
              { name: '3月', value: 48 },
              { name: '4月', value: 55 },
              { name: '5月', value: 62 },
              { name: '6月', value: 58 },
              { name: '7月', value: 65 },
              { name: '8月', value: 68 },
            ]}
            title="经济周期综合指数"
            height={300}
            showArea
          />
        </Card>
      ),
    },
  ];

  const scenarioTabItems = [
    {
      key: 'probability',
      label: '情景概率',
      children: (
        <Card>
          <Row gutter={24}>
            <Col xs={24} md={12}>
              <PieChart
                data={displayScenario.scenarios.map((s) => ({
                  name: s.name === 'bullish' ? '乐观' : s.name === 'base' ? '基准' : '悲观',
                  value: s.probability * 100,
                }))}
                title="情景概率分布"
                height={300}
              />
            </Col>
            <Col xs={24} md={12}>
              <Card title="各情景预期收益">
                <Table
                  dataSource={displayScenario.scenarios.map((s, i) => ({
                    key: i,
                    scenario: s.name === 'bullish' ? '乐观' : s.name === 'base' ? '基准' : '悲观',
                    probability: `${(s.probability * 100).toFixed(0)}%`,
                    expectedReturn: `${s.expectedReturn}%`,
                    description: s.description,
                  }))}
                  columns={[
                    { title: '情景', dataIndex: 'scenario', key: 'scenario' },
                    { title: '概率', dataIndex: 'probability', key: 'probability' },
                    { title: '预期收益', dataIndex: 'expectedReturn', key: 'expectedReturn' },
                    { title: '描述', dataIndex: 'description', key: 'description' },
                  ]}
                  pagination={false}
                  size="small"
                />
              </Card>
            </Col>
          </Row>
        </Card>
      ),
    },
    {
      key: 'allocation',
      label: '资产配置',
      children: (
        <Card>
          <Row gutter={24}>
            <Col xs={24} md={12}>
              <PieChart
                data={displayScenario.recommendedAllocation.map((a) => ({
                  name: a.asset,
                  value: a.weight,
                }))}
                title="推荐资产配置"
                height={300}
              />
            </Col>
            <Col xs={24} md={12}>
              <Card title="风险评分">
                <Progress
                  type="dashboard"
                  percent={displayScenario.riskScore}
                  format={(p) => `${p}分`}
                  status="normal"
                />
                <p style={{ textAlign: 'center', color: '#999', marginTop: 16 }}>
                  风险等级：{displayScenario.riskScore < 30 ? '低' : displayScenario.riskScore < 60 ? '中' : '高'}
                </p>
              </Card>
            </Col>
          </Row>
        </Card>
      ),
    },
  ];

  const overviewContent = (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} md={6}>
        <StatCard title="GDP同比" value={5.2} suffix="%" change={0.3} loading={indicatorsLoading} />
      </Col>
      <Col xs={24} sm={12} md={6}>
        <StatCard title="PMI指数" value={50.8} change={1.2} loading={indicatorsLoading} />
      </Col>
      <Col xs={24} sm={12} md={6}>
        <StatCard title="CPI同比" value={0.2} suffix="%" change={-0.5} loading={indicatorsLoading} />
      </Col>
      <Col xs={24} sm={12} md={6}>
        <StatCard title="社融增速" value={9.5} suffix="%" change={-0.8} loading={indicatorsLoading} />
      </Col>
      <Col xs={24}>
        <Card 
          title="宏观指标列表" 
          extra={
            <Space>
              <Select
                value={category}
                onChange={setCategory}
                style={{ width: 120 }}
                options={[
                  { value: 'all', label: '全部' },
                  { value: 'gdp', label: 'GDP' },
                  { value: 'pmi', label: 'PMI' },
                  { value: 'cpi', label: 'CPI' },
                  { value: 'interest', label: '利率' },
                  { value: 'money', label: '货币' },
                ]}
              />
              <Button icon={<ReloadOutlined />} onClick={refreshIndicators}>刷新</Button>
            </Space>
          }
        >
          <Table
            columns={indicatorColumns}
            dataSource={indicators.length > 0 ? indicators : [
              { id: '1', name: 'GDP同比', value: 5.2, unit: '%', date: '2024-Q3', category: 'gdp' },
              { id: '2', name: 'PMI指数', value: 50.8, unit: '', date: '2024-10', category: 'pmi' },
              { id: '3', name: 'CPI同比', value: 0.2, unit: '%', date: '2024-10', category: 'cpi' },
              { id: '4', name: '社融增速', value: 9.5, unit: '%', date: '2024-09', category: 'money' },
              { id: '5', name: 'LPR1年', value: 3.35, unit: '%', date: '2024-10', category: 'interest' },
            ].map((i, k) => ({ ...i, key: k }))}
            pagination={{ pageSize: 5 }}
            size="small"
          />
        </Card>
      </Col>
    </Row>
  );

  const tabItems = [
    {
      key: 'overview',
      label: (
        <span>
          <FileTextOutlined /> 宏观概览
        </span>
      ),
      children: overviewContent,
    },
    {
      key: 'cycle',
      label: (
        <span>
          <LineChartOutlined /> 经济周期
        </span>
      ),
      children: (
        <Tabs items={cycleTabItems} />
      ),
    },
    {
      key: 'scenario',
      label: (
        <span>
          <PieChartOutlined /> 情景分析
        </span>
      ),
      children: (
        <Tabs items={scenarioTabItems} />
      ),
    },
    {
      key: 'policy',
      label: (
        <span>
          <FundOutlined /> 政策解读
        </span>
      ),
      children: (
        <Card>
          <Row gutter={16}>
            {(policyImpacts.length > 0 ? policyImpacts : [
              { policyType: 'monetary', direction: 'positive', impactScore: 75, description: '货币政策保持稳健偏松，降准降息仍有空间', affectedIndustries: ['银行', '房地产', '券商'], recommendations: ['关注利率敏感型行业', '配置高股息资产'] },
              { policyType: 'fiscal', direction: 'positive', impactScore: 65, description: '财政政策积极有为，重点支持新基建和科技创新', affectedIndustries: ['建筑', '计算机', '通信'], recommendations: ['关注基建投资主线', '把握科技创新机会'] },
              { policyType: 'industry', direction: 'positive', impactScore: 80, description: '产业政策聚焦新能源、人工智能等战略性新兴产业', affectedIndustries: ['新能源', 'AI', '半导体'], recommendations: ['长期看好成长赛道', '关注国产替代机会'] },
            ] as PolicyImpact[]).map((impact, idx) => (
              <Col xs={24} md={8} key={idx}>
                <Card 
                  title={impact.policyType === 'monetary' ? '货币政策' : impact.policyType === 'fiscal' ? '财政政策' : '产业政策'}
                  extra={
                    <Tag color={impact.direction === 'positive' ? 'green' : impact.direction === 'negative' ? 'red' : 'default'}>
                      {impact.direction === 'positive' ? '利好' : impact.direction === 'negative' ? '利空' : '中性'}
                    </Tag>
                  }
                >
                  <Progress percent={impact.impactScore} status="active" />
                  <p style={{ marginTop: 12 }}>{impact.description}</p>
                  <p style={{ color: '#999', fontSize: 12 }}>受影响行业: {impact.affectedIndustries?.join(', ')}</p>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="宏观分析"
        extra={
          <Space>
            <RangePicker />
            <Button icon={<DownloadOutlined />} onClick={() => message.success('导出功能开发中')}>
              导出报告
            </Button>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>
    </div>
  );
};

export default MacroAnalysisPage;