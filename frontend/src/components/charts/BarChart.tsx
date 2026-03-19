import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

interface BarChartProps {
  data: { name: string; value: number }[];
  title?: string;
  height?: number;
  xAxisName?: string;
  yAxisName?: string;
  horizontal?: boolean;
  stacked?: boolean;
  colors?: string[];
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  title,
  height = 300,
  xAxisName,
  yAxisName,
  horizontal = false,
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
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: horizontal
      ? {
          type: 'value',
          name: yAxisName,
        }
      : {
          type: 'category',
          data: data.map((d) => d.name),
          name: xAxisName,
        },
    yAxis: horizontal
      ? {
          type: 'category',
          data: data.map((d) => d.name),
          name: xAxisName,
        }
      : {
          type: 'value',
          name: yAxisName,
        },
    series: [
      {
        name: title || '',
        type: 'bar',
        data: data.map((d) => d.value),
        label: {
          show: true,
          position: 'right',
        },
        itemStyle: colors ? { color: colors[0] } : undefined,
      },
    ],
  }), [data, title, xAxisName, yAxisName, horizontal, colors]);

  return <ReactECharts option={option} style={{ height }} />;
};

export default BarChart;