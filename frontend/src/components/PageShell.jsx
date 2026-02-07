import React from "react";
import { NavLink } from "react-router-dom";

export default function PageShell({ children }) {
  return (
    <div className="shell">
      <header className="page">
        <div className="brand">
          <div>
            <h1>COE Analytics Dashboard</h1>
          </div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
