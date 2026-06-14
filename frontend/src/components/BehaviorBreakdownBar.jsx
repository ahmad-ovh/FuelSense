import React from 'react';

const BehaviorBreakdownBar = ({ idlePct = 0, drivingMode = 'city' }) => {
  // Calculate relative splits based on current idle % and driving mode
  let cityPct = 0;
  let highwayPct = 0;
  
  const remaining = 100 - idlePct;

  if (drivingMode === 'highway') {
    highwayPct = remaining;
    cityPct = 0;
  } else if (drivingMode === 'city') {
    cityPct = remaining;
    highwayPct = 0;
  } else {
    // Mixed driving splits remaining equally
    cityPct = remaining * 0.5;
    highwayPct = remaining * 0.5;
  }

  // Round values for displaying
  const idle = Math.round(idlePct * 10) / 10;
  const city = Math.round(cityPct * 10) / 10;
  const highway = Math.round(highwayPct * 10) / 10;

  return (
    <div className="behavior-container">
      <h3 className="section-title">Driving Style Breakdown</h3>
      
      {/* Segmented Progress Bar */}
      <div className="breakdown-bar-wrapper">
        <div className="breakdown-bar">
          {idle > 0 && (
            <div 
              className="bar-segment segment-idle" 
              style={{ width: `${idle}%`, transition: 'width 0.8s ease' }}
            />
          )}
          {city > 0 && (
            <div 
              className="bar-segment segment-city" 
              style={{ width: `${city}%`, transition: 'width 0.8s ease' }}
            />
          )}
          {highway > 0 && (
            <div 
              className="bar-segment segment-highway" 
              style={{ width: `${highway}%`, transition: 'width 0.8s ease' }}
            />
          )}
        </div>
      </div>

      {/* Legend & Labels */}
      <div className="breakdown-legend">
        <div className="legend-item">
          <span className="dot dot-idle" />
          <div className="legend-text">
            <span className="legend-label">Idle (Waste)</span>
            <span className="legend-val">{idle}%</span>
          </div>
        </div>
        <div className="legend-item">
          <span className="dot dot-city" />
          <div className="legend-text">
            <span className="legend-label">City (Stop-Go)</span>
            <span className="legend-val">{city}%</span>
          </div>
        </div>
        <div className="legend-item">
          <span className="dot dot-highway" />
          <div className="legend-text">
            <span className="legend-label">Highway (Cruise)</span>
            <span className="legend-val">{highway}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BehaviorBreakdownBar;
