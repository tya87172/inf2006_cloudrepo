import React, { useEffect, useMemo, useState, useCallback } from "react";
import ReactECharts from "echarts-for-react";
import TabNav from "../components/TabNav.jsx";

const VEHICLE_CLASSES = [
  "ALL",
  "Category A",
  "Category B",
  "Category C",
  "Category D",
  "Category E"
];

function buildHistogram(values, binCount = 30) {
  if (!values || values.length === 0) {
    return { labels: [], bins: [], min: 0, max: 0, binWidth: 0 };
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const binWidth = (max - min) / binCount || 1;
  const bins = new Array(binCount).fill(0);
  const labels = [];

  for (let i = 0; i < binCount; i += 1) {
    const binStart = min + i * binWidth;
    labels.push(`$${Math.round(binStart / 1000)}k`);
  }

  values.forEach((value) => {
    const idx = Math.min(Math.floor((value - min) / binWidth), binCount - 1);
    bins[idx] += 1;
  });

  return { labels, bins, min, max, binWidth };
}

export default function Analysis() {
  const [vehicleClass, setVehicleClass] = useState("ALL");
  const [startYear, setStartYear] = useState(2010);
  const [endYear, setEndYear] = useState(2025);
  const [chartType, setChartType] = useState("histogram");
  const [distribution, setDistribution] = useState([]);
  const [scatter, setScatter] = useState([]);

  // Wrapped in useCallback to safely use inside useEffect
  const loadData = useCallback(async () => {
    const url = new URL("/api/analysis", window.location.origin);
    url.searchParams.set("vehicle_class", vehicleClass);
    url.searchParams.set("start_year", String(startYear));
    url.searchParams.set("end_year", String(endYear));

    try {
      const res = await fetch(url);
      const json = await res.json();
      setDistribution(json.distribution || []);
      setScatter(json.scatter || []);
    } catch (error) {
      console.error("Failed to fetch data:", error);
    }
  }, [vehicleClass, startYear, endYear]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const histogramOption = useMemo(() => {
    const { labels, bins, min, binWidth } = buildHistogram(distribution);

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: "axis",
        backgroundColor: 'rgba(26, 31, 38, 0.95)',
        borderColor: 'rgba(88, 164, 176, 0.3)',
        textStyle: { color: '#E8ECF0' },
        formatter: (params) => {
          if (!params?.length) return "";
          const idx = params[0].dataIndex;
          const binStart = min + idx * binWidth;
          const binEnd = binStart + binWidth;
          return `$${Math.round(binStart).toLocaleString()} - $${Math.round(binEnd).toLocaleString()}<br/>Count: ${params[0].value}`;
        }
      },
      xAxis: { 
        type: "category", 
        data: labels, 
        axisLabel: { rotate: 45, color: "#E8ECF0" },
        axisLine: { lineStyle: { color: "rgba(169, 188, 208, 0.2)" } },
        splitLine: { show: false }
      },
      yAxis: { 
        type: "value", 
        name: "Frequency",
        axisLine: { lineStyle: { color: "rgba(169, 188, 208, 0.2)" } },
        axisLabel: { color: "#E8ECF0" },
        nameTextStyle: { color: "#E8ECF0" },
        splitLine: { lineStyle: { color: "rgba(169, 188, 208, 0.1)" } }
      },
      series: [
        {
          type: "bar",
          data: bins,
          itemStyle: { 
            color: "#66B3BA",
            borderRadius: [6, 6, 0, 0]
          },
          barWidth: "90%"
        }
      ],
      grid: { bottom: 80, left: 50, right: 30, top: 40 }
    };
  }, [distribution]);

  const scatterOption = useMemo(() => {
    const seriesMap = {};
    scatter.forEach((row) => {
      if (!seriesMap[row.vehicle_class]) {
        seriesMap[row.vehicle_class] = [];
      }
      seriesMap[row.vehicle_class].push([row.quota, row.premium]);
    });

    const categories = Object.keys(seriesMap).sort();
    const palette = ["#00D9FF", "#F08F90", "#FFD93D", "#6BCF7F", "#B28DFF"];

    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: "item",
        backgroundColor: 'rgba(26, 31, 38, 0.95)',
        borderColor: 'rgba(88, 164, 176, 0.3)',
        textStyle: { color: '#E8ECF0' },
        formatter: (params) => {
          if (!params?.data) return "";
          return `${params.seriesName}<br/>Quota: ${params.data[0].toLocaleString()}<br/>Premium: $${params.data[1].toLocaleString()}`;
        }
      },
      legend: { 
        data: categories, 
        top: 0,
        textStyle: { color: "#E8ECF0" }
      },
      xAxis: { 
        type: "value", 
        name: "Quota (Supply)", 
        nameGap: 30, 
        nameLocation: "middle",
        axisLine: { lineStyle: { color: "rgba(169, 188, 208, 0.2)" } },
        axisLabel: { color: "#E8ECF0" },
        nameTextStyle: { color: "#E8ECF0" },
        splitLine: { lineStyle: { color: "rgba(169, 188, 208, 0.1)" } }
      },
      yAxis: { 
        type: "value", 
        name: "Premium Price ($)",
        axisLine: { lineStyle: { color: "rgba(169, 188, 208, 0.2)" } },
        axisLabel: { color: "#E8ECF0" },
        nameTextStyle: { color: "#E8ECF0" },
        splitLine: { lineStyle: { color: "rgba(169, 188, 208, 0.1)" } }
      },
      series: categories.map((name, idx) => ({
        name,
        type: "scatter",
        data: seriesMap[name],
        symbolSize: 10,
        itemStyle: { color: palette[idx % palette.length], opacity: 0.85 }
      })),
      grid: { top: 60, left: 50, right: 30, bottom: 60 }
    };
  }, [scatter]);

  return (
    <div className="page">
      <div className="card">
        <TabNav />
        <p className="subtle">Switch between histogram and scatter to inspect pricing dynamics.</p>
        <div className="controls">
          <label>
            Vehicle Class
            <select value={vehicleClass} onChange={(event) => setVehicleClass(event.target.value)}>
              {VEHICLE_CLASSES.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label>
            Start Year
            <input
              type="number"
              value={startYear}
              onChange={(event) => setStartYear(Number(event.target.value))}
            />
          </label>
          <label>
            End Year
            <input
              type="number"
              value={endYear}
              onChange={(event) => setEndYear(Number(event.target.value))}
            />
          </label>
          <label>
            Chart Type
            <select value={chartType} onChange={(event) => setChartType(event.target.value)}>
              <option value="histogram">Histogram</option>
              <option value="scatter">Scatter Plot</option>
            </select>
          </label>
          <label>
            &nbsp;
            <button type="button" onClick={loadData}>Load</button>
          </label>
        </div>
      </div>

      {chartType === "histogram" ? (
        <div className="card">
          <h3>Price Distribution</h3>
          <ReactECharts key="histogram" option={histogramOption} className="chart" />
        </div>
      ) : (
        <div className="card">
          <h3>Supply vs Price</h3>
          <ReactECharts key="scatter" option={scatterOption} className="chart" />
        </div>
      )}
    </div>
  );
}