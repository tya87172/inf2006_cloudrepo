import React, { useCallback, useEffect, useMemo, useState } from "react";
import ReactECharts from "echarts-for-react";
import TabNav from "../components/TabNav.jsx";

const VEHICLE_CLASSES = ["ALL", "Category A", "Category B", "Category C", "Category D"];

export default function Premium() {
  const [vehicleClass, setVehicleClass] = useState("ALL");
  const [windowSize, setWindowSize] = useState(6);
  const [xAxisMode, setXAxisMode] = useState("Year");
  const [startYear, setStartYear] = useState(2010);
  const [endYear, setEndYear] = useState(2019);
  const [data, setData] = useState([]);

  const loadData = useCallback(async () => {
    const url = new URL("/api/premium", window.location.origin);
    url.searchParams.set("vehicle_class", vehicleClass);
    url.searchParams.set("window", String(windowSize));
    url.searchParams.set("x_axis_mode", xAxisMode);
    url.searchParams.set("start_year", String(startYear));
    url.searchParams.set("end_year", String(endYear));

    const res = await fetch(url);
    const json = await res.json();
    setData(json.data || []);
  }, [vehicleClass, windowSize, xAxisMode, startYear, endYear]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const option = useMemo(() => {
    const labels = data.map((row) => row.x_label);
    const premium = data.map((row) => row.premium);
    const moving = data.map((row) => row.moving_avg);

    return {
      backgroundColor: 'transparent',
      tooltip: { 
        trigger: "axis",
        backgroundColor: 'rgba(26, 31, 38, 0.95)',
        borderColor: 'rgba(88, 164, 176, 0.3)',
        textStyle: { color: '#E8ECF0' }
      },
      legend: { 
        data: ["Premium", "Moving Avg"],
        textStyle: { color: "#E8ECF0" }
      },
      xAxis: { 
        type: "category", 
        data: labels,
        axisLine: { lineStyle: { color: "rgba(169, 188, 208, 0.2)" } },
        axisLabel: { color: "#E8ECF0" },
        splitLine: { show: false }
      },
      yAxis: { 
        type: "value", 
        name: "Premium (SGD)",
        axisLine: { lineStyle: { color: "rgba(169, 188, 208, 0.2)" } },
        axisLabel: { color: "#E8ECF0" },
        nameTextStyle: { color: "#E8ECF0" },
        splitLine: { lineStyle: { color: "rgba(169, 188, 208, 0.1)" } }
      },
      series: [
        {
          name: "Premium",
          type: "line",
          data: premium,
          smooth: false,
          showSymbol: true,
          symbol: "circle",
          symbolSize: 6,
          lineStyle: { type: "dashed", width: 2, opacity: 0.6 },
          itemStyle: { color: "#F08F90", opacity: 0.8 }
        },
        {
          name: "Moving Avg",
          type: "line",
          data: moving,
          smooth: true,
          showSymbol: true,
          symbol: "circle",
          symbolSize: 8,
          lineStyle: { type: "solid", width: 3 },
          itemStyle: { color: "#66B3BA" }
        }
      ],
      grid: { top: 60, bottom: 70, left: 50, right: 30 }
    };
  }, [data]);

  return (
    <div className="page">
      <div className="card">
        <TabNav />
        <p className="subtle">Follow premium smoothing by month or year.</p>
        <div className="controls">
          <label>
            Category
            <select value={vehicleClass} onChange={(event) => setVehicleClass(event.target.value)}>
              {VEHICLE_CLASSES.map((item) => (
                <option key={item}>{item}</option>
              ))}
            </select>
          </label>
          <label>
            Window
            <input
              type="number"
              min="1"
              value={windowSize}
              onChange={(event) => setWindowSize(Number(event.target.value))}
            />
          </label>
          <label>
            X-Axis
            <select value={xAxisMode} onChange={(event) => setXAxisMode(event.target.value)}>
              <option value="Year">Year</option>
              <option value="Month">Month</option>
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
            &nbsp;
            <button type="button" onClick={loadData}>Load</button>
          </label>
        </div>
      </div>

      <div className="card">
        <h3>Moving Average Tracker</h3>
        <ReactECharts option={option} className="chart" />
      </div>
    </div>
  );
}
