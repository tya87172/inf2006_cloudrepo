import React from "react";
import { NavLink } from "react-router-dom";

export default function TabNav() {
  return (
    <nav className="tab-nav">
      <NavLink to="/" end>
        Seasonality
      </NavLink>
      <NavLink to="/analysis">Analysis</NavLink>
      <NavLink to="/premium">Premium</NavLink>
    </nav>
  );
}
