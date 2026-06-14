import React, { useState } from 'react';

const ScenarioFAB = ({ onSelectScenario, activeScenarioId, currentStatus }) => {
  const [isOpen, setIsOpen] = useState(false);

  const scenariosList = [
    { id: 'A', name: 'Urban Congestion', desc: 'High Idle & Inefficiency' },
    { id: 'B', name: 'Highway Efficiency', desc: 'Optimal Cruising' },
    { id: 'C', name: 'Aggressive Driving', desc: 'Spiky High Consumption' },
    { id: 'D', name: 'Mixed Weekly Driving', desc: 'Balanced Realism' },
  ];

  const handleSelect = (id) => {
    onSelectScenario(id);
    setIsOpen(false);
  };

  return (
    <div className="fab-container">
      {/* Expanded Menu */}
      {isOpen && (
        <div className="fab-menu">
          <div className="fab-menu-header">
            <span>Select Scenario Stream</span>
            <small>Changes live vehicle telemetry</small>
          </div>
          {scenariosList.map((sc) => (
            <button
              key={sc.id}
              onClick={() => handleSelect(sc.id)}
              className={`fab-menu-item ${activeScenarioId === sc.id ? 'fab-item-active' : ''}`}
            >
              <div className="fab-item-info">
                <span className="fab-item-name">{sc.name}</span>
                <span className="fab-item-desc">{sc.desc}</span>
              </div>
              <span className="fab-item-badge">{sc.id}</span>
            </button>
          ))}
        </div>
      )}

      {/* Main Trigger Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)} 
        className={`fab-trigger ${isOpen ? 'fab-trigger-open' : ''} ${currentStatus === 'RESETTING' ? 'fab-trigger-spinning' : ''}`}
        title="Switch Driving Scenario"
      >
        {isOpen ? (
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/>
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" width="24" height="24">
            <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" fill="currentColor"/>
          </svg>
        )}
      </button>
    </div>
  );
};

export default ScenarioFAB;
