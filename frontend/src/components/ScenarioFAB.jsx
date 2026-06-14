import React, { useState } from 'react';

const ScenarioFAB = ({ onSelectScenario, activeScenarioId, currentStatus }) => {
  const [isOpen, setIsOpen] = useState(false);

  const scenariosList = [
    { id: 'A', name: 'Urban Congestion', desc: 'Stop-and-go heavy city traffic' },
    { id: 'B', name: 'Highway Cruising', desc: 'Optimal high-speed fuel efficiency' },
    { id: 'C', name: 'Aggressive Driving', desc: 'High RPM performance driving stress-test' },
    { id: 'D', name: 'Mixed Commute', desc: 'Balanced real-world weekly driving cycle' },
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
            <span>Simulate Driving Conditions</span>
            <small>Switches the telemetry stream profile</small>
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
          <i className="ph ph-x" style={{ fontSize: '22px' }}></i>
        ) : (
          <i className="ph ph-gear" style={{ fontSize: '22px' }}></i>
        )}
      </button>
    </div>
  );
};

export default ScenarioFAB;
