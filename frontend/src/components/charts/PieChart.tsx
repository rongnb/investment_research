import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

interface PieChartProps {
  data: { name: string; value: number }[];
  title?: string;
  height?: number;
  radius?: [string, string];
  center?: [string, string];
  showLabel?: boolean;
  showPercent?: boolean;
  colors?: string[];
}

export const PieChart: React.FC<PieChartProps> = ({
  data,
  title,
  height = 300,
  radius = ['0%', '70%'],
  center = ['50%', '50%'],
  showLabel = true,
  showPercent = true,
  colors,
}) => {
  const option = useMemo<EChartsOption>(() => ({
    title: title
      ? {
          text: title,
          left: 'center',
        }
      : undefined,
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
    },
    series: [
      {
        name: title || '',
        type: 'pie',
        radius,
        center,
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: showLabel
          ? {
              show: true,
              formatter: showPercent ? '{b}: {d}%' : '{b}',
            }
          : {
              show: false,
            },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        labelLine: {
          show: showLabel,
        },
        data: data.map((d, i) => ({
          ...d,
          itemStyle: colors ? { color: colors[i % colors.length] } : undefined,
        })),
      },
    ],
  }), [data, title, radius, center, showLabel, showPercent, colors]);

  return <ReactECharts option={option} style={{ height }} />;
};

export default PieChart;