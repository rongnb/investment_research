import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

interface LineChartProps {
  data: { name: string; value: number }[];
  title?: string;
  height?: number;
  xAxisName?: string;
  yAxisName?: string;
  showArea?: boolean;
  smooth?: boolean;
  colors?: string[];
}

export const LineChart: React.FC<LineChartProps> = ({
  data,
  title,
  height = 300,
  xAxisName = '',
  yAxisName = '',
  showArea = false,
  smooth = true,
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
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map((d) => d.name),
      name: xAxisName,
      nameLocation: 'middle',
      nameGap: 30,
    },
    yAxis: {
      type: 'value',
      name: yAxisName,
    },
    series: [
      {
        name: title || '',
        type: 'line',
        smooth,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        areaStyle: showArea
          ? {
              opacity: 0.3,
            }
          : undefined,
        lineStyle: {
          width: 2,
        },
        data: data.map((d) => d.value),
        itemStyle: colors ? { color: colors[0] } : undefined,
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
    ],
  }), [data, title, xAxisName, yAxisName, showArea, smooth, colors]);

  return <ReactECharts option={option} style={{ height }} />;
};

export default LineChart;