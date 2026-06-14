import React from 'react';

const MetricCard = ({ label, value, unit, subLabel }) => {
  return (
    <div className="metric-card">
      <span className="metric-lbl">{label}</span>
      <div className="metric-val-wrapper">
        <span className="metric-val">{value}</span>
        {unit && <span className="metric-unit">{unit}</span>}
      </div>
      {subLabel && <span className="metric-sublbl">{subLabel}</span>}
    </div>
  );
};

export default MetricCard;
