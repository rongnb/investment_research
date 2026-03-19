import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

interface HeatmapData {
  x: string;
  y: string;
  value: number;
}

interface HeatmapProps {
  data: HeatmapData[];
  title?: string;
  height?: number;
  xAxisName?: string;
  yAxisName?: string;
  colors?: string[];
}

export const Heatmap: React.FC<HeatmapProps> = ({
  data,
  title,
  height = 300,
  xAxisName,
  yAxisName,
  colors,
}) => {
  const option = useMemo<EChartsOption>(() => {
    const xAxisData = [...new Set(data.map((d) => d.x))];
    const yAxisData = [...new Set(data.map((d) => d.y))];

    return {
      title: title
        ? {
            text: title,
            left: 'center',
          }
        : undefined,
      tooltip: {
        position: 'top',
      },
      grid: {
        left: '3%',
        right: '10%',
        bottom: '3%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        name: xAxisName,
        nameLocation: 'middle',
        nameGap: 30,
        splitArea: {
          show: true,
        },
      },
      yAxis: {
        type: 'category',
        data: yAxisData,
        name: yAxisName,
        nameLocation: 'middle',
        nameGap: 50,
        splitArea: {
          show: true,
        },
      },
      visualMap: {
        min: Math.min(...data.map((d) => d.value)),
        max: Math.max(...data.map((d) => d.value)),
        calculable: true,
        orient: 'vertical',
        right: '0',
        top: 'center',
        inRange: {
          color: colors || ['#f0f9ff', '#1890ff', '#0050b3'],
        },
      },
      series: [
        {
          name: title || '',
          type: 'heatmap',
          data: data.map((d) => [d.x, d.y, d.value]),
          label: {
            show: true,
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
    };
  }, [data, title, xAxisName, yAxisName, colors]);

  return <ReactECharts option={option} style={{ height }} />;
};

export default Heatmap;