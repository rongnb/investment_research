import React, { useMemo, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import type { StockPrice } from '@/types';

interface KLineChartProps {
  data: StockPrice[];
  title?: string;
  height?: number;
  showVolume?: boolean;
  showMA?: boolean;
  showMA5?: boolean;
  showMA10?: boolean;
  showMA20?: boolean;
}

export const KLineChart: React.FC<KLineChartProps> = ({
  data,
  title = 'K线图',
  height = 500,
  showVolume = true,
  showMA = true,
  showMA5 = true,
  showMA10 = true,
  showMA20 = true,
}) => {
  const chartRef = useRef<ReactECharts>(null);

  const option = useMemo<EChartsOption>(() => {
    if (!data || data.length === 0) {
      return {};
    }

    const dates = data.map((d) => d.date);
    const ohlc = data.map((d) => [d.open, d.close, d.low, d.high]);
    const volumes = data.map((d) => d.volume);
    const volumesColor = data.map((d) => (d.close >= d.open ? '#f56c6c' : '#67c23a'));

    // 计算移动平均线
    const calculateMA = (day: number) => {
      const result: (number | null)[] = [];
      for (let i = 0; i < data.length; i++) {
        if (i < day - 1) {
          result.push(null);
        } else {
          const sum = data.slice(i - day + 1, i + 1).reduce((acc, d) => acc + d.close, 0);
          result.push(+(sum / day).toFixed(2));
        }
      }
      return result;
    };

    const grid: EChartsOption['grid'][] = [
      {
        left: '10%',
        right: '8%',
        height: showVolume ? '50%' : '70%',
        top: '10%',
      },
    ];

    const xAxis: EChartsOption['xAxis'][] = [
      {
        type: 'category',
        data: dates,
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
      },
    ];

    const yAxis: EChartsOption['yAxis'][] = [
      {
        scale: true,
        splitArea: { show: true },
      },
    ];

    if (showVolume) {
      grid.push({
        left: '10%',
        right: '8%',
        top: '65%',
        height: '15%',
      });
      xAxis.push({
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLabel: { show: false },
      });
      yAxis.push({
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
      });
    }

    const series: EChartsOption['series'] = [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        itemStyle: {
          color: '#f56c6c',
          color0: '#67c23a',
          borderColor: '#f56c6c',
          borderColor0: '#67c23a',
        },
      },
      {
        name: 'MA5',
        type: 'line',
        data: calculateMA(5),
        smooth: true,
        lineStyle: { opacity: showMA && showMA5 ? 1 : 0 },
        symbol: 'none',
      },
      {
        name: 'MA10',
        type: 'line',
        data: calculateMA(10),
        smooth: true,
        lineStyle: { opacity: showMA && showMA10 ? 1 : 0 },
        symbol: 'none',
      },
      {
        name: 'MA20',
        type: 'line',
        data: calculateMA(20),
        smooth: true,
        lineStyle: { opacity: showMA && showMA20 ? 1 : 0 },
        symbol: 'none',
      },
    ];

    if (showVolume) {
      series.push({
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes.map((vol, i) => ({
          value: vol,
          itemStyle: { color: volumesColor[i] },
        })),
      });
    }

    return {
      title: {
        text: title,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
        },
      },
      legend: {
        data: ['K线', 'MA5', 'MA10', 'MA20', '成交量'],
        top: 30,
      },
      grid,
      xAxis,
      yAxis,
      series,
      dataZoom: [
        {
          type: 'inside',
          start: 50,
          end: 100,
        },
        {
          show: true,
          type: 'slider',
          bottom: 10,
          start: 50,
          end: 100,
        },
      ],
    };
  }, [data, title, showVolume, showMA, showMA5, showMA10, showMA20]);

  return <ReactECharts ref={chartRef} option={option} style={{ height }} />;
};

export default KLineChart;