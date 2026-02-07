import React, { useCallback, useEffect, useMemo, useState } from "react";
import ReactECharts from "echarts-for-react";
import TabNav from "../components/TabNav.jsx";

const VEHICLE_CLASSES = ["Category A", "Category B", "Category C", "Category D"];

export default function Seasonality() {
  const [vehicleClass, setVehicleClass] = useState("Category A");
  const [startYear, setStartYear] = useState(2010);
  const [endYear, setEndYear] = useState(2019);
  const [aggregation, setAggregation] = useState("mean");
  const [data, setData] = useState([]);

  const loadData = useCallback(async () => {
    const url = new URL("/api/seasonality", window.location.origin);
    url.searchParams.set("vehicle_class", vehicleClass);
    url.searchParams.set("start_year", String(startYear));
    url.searchParams.set("end_year", String(endYear));
    url.searchParams.set("aggregation", aggregation);

    const res = await fetch(url);
    const json = await res.json();
    setData(json.data || []);
  }, [vehicleClass, startYear, endYear, aggregation]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const option = useMemo(() => {
    const months = data.map((row) => row.month_name);
    const quota = data.map((row) => row.quota);
    const premium = data.map((row) => row.premium);

    return {
      backgroundColor: 'transparent',
      tooltip: { 
        trigger: "axis",
        backgroundColor: 'rgba(26, 31, 38, 0.95)',
        borderColor: 'rgba(88, 164, 176, 0.3)',
        textStyle: { color: '#E8ECF0' }
      },
      legend: { 
        data: ["Quota", "Premium"],
        textStyle: { color: "#E8ECF0" }
      },
      xAxis: { 
        type: "category", 
        data: months,
        axisLine: { lineStyle: { color: "rgba(169, 188, 208, 0.2)" } },
        axisLabel: { color: "#E8ECF0" },
        splitLine: { show: false }
      },
      yAxis: [
        { 
          type: "value", 
          name: "Quota",
          axisLine: { lineStyle: { color: "rgba(169, 188, 208, 0.2)" } },
          axisLabel: { color: "#E8ECF0" },
          nameTextStyle: { color: "#E8ECF0" },
          splitLine: { lineStyle: { color: "rgba(169, 188, 208, 0.1)" } }
        },
        { 
          type: "value", 
          name: "Premium",
          axisLine: { lineStyle: { color: "rgba(169, 188, 208, 0.2)" } },
          axisLabel: { color: "#E8ECF0" },
          nameTextStyle: { color: "#E8ECF0" },
          splitLine: { lineStyle: { color: "rgba(169, 188, 208, 0.1)" } }
        }
      ],
      series: [
        { 
          name: "Quota", 
          type: "bar", 
          data: quota, 
          itemStyle: { 
            color: "#66B3BA",
            borderRadius: [6, 6, 0, 0]
          } 
        },
        { 
          name: "Premium", 
          type: "line", 
          yAxisIndex: 1, 
          data: premium, 
          itemStyle: { color: "#F08F90" },
          lineStyle: { width: 3 },
          smooth: true
        }
      ],
      grid: { top: 60, bottom: 70, left: 50, right: 50 }
    };
  }, [data]);

  return (
    <div className="page">
      <div className="card">
        <TabNav />
        <p className="subtle">Compare quota and premium patterns by vehicle category and time range.</p>
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
            Aggregation
            <select value={aggregation} onChange={(event) => setAggregation(event.target.value)}>
              <option value="mean">Mean</option>
              <option value="median">Median</option>
            </select>
          </label>
          <label>
            &nbsp;
            <button type="button" onClick={loadData}>Load</button>
          </label>
        </div>
      </div>

      <div className="card">
        <h3>Monthly Pattern</h3>
        <ReactECharts option={option} className="chart" />
      </div>
    </div>
  );
}
