import React from 'react';

const EcoScoreGauge = ({ score = 100 }) => {
  const radius = 50;
  const strokeWidth = 8;
  const circumference = 2 * Math.PI * radius; // ~314.16
  const sweepAngle = 270;
  const arcLength = circumference * (sweepAngle / 360); // ~235.62
  const strokeDashoffset = arcLength * (1 - score / 100);

  // Determine color based on score thresholds from design-spec.md Section 4.1
  let color = '#ef4444'; // Red (0-39)
  let label = 'Highly Inefficient';
  if (score >= 70) {
    color = '#10b981'; // Green (70-100)
    label = 'Optimal Efficiency';
  } else if (score >= 40) {
    color = '#f59e0b'; // Orange (40-69)
    label = 'Moderate Efficiency';
  }

  return (
    <div className="eco-gauge-container">
      <div className="eco-gauge-svg-wrapper">
        <svg
          viewBox="0 0 120 120"
          className="eco-gauge-svg"
        >
          {/* Track Circle */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke="#1e293b"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference - arcLength}`}
            strokeLinecap="round"
            transform="rotate(135 60 60)"
          />
          {/* Indicator Arc */}
          <circle
            cx="60"
            cy="60"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference - arcLength}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            transform="rotate(135 60 60)"
            style={{ transition: 'stroke-dashoffset 0.8s ease, stroke 0.8s ease' }}
          />
        </svg>
        <div className="eco-gauge-text">
          <span className="eco-score-number" style={{ color }}>{Math.round(score)}</span>
          <span className="eco-score-lbl">Index</span>
        </div>
      </div>
      <div className="eco-gauge-label" style={{ color }}>{label}</div>
      <div className="eco-gauge-subtext">Driving Efficiency Index</div>
    </div>
  );
};

export default EcoScoreGauge;
