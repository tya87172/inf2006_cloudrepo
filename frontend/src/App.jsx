import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import PageShell from "./components/PageShell.jsx";
import Seasonality from "./pages/Seasonality.jsx";
import Analysis from "./pages/Analysis.jsx";
import Premium from "./pages/Premium.jsx";

export default function App() {
  return (
    <PageShell>
      <Routes>
        <Route path="/" element={<Seasonality />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/premium" element={<Premium />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </PageShell>
  );
}
