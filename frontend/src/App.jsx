import React, { useState, useEffect } from 'react';
import RefuelDecisionCard from './components/RefuelDecisionCard';
import EcoScoreGauge from './components/EcoScoreGauge';
import MetricCard from './components/MetricCard';
import BehaviorBreakdownBar from './components/BehaviorBreakdownBar';
import AIInsightPanel from './components/AIInsightPanel';
import AIChat from './components/AIChat';
import ScenarioFAB from './components/ScenarioFAB';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [simulationState, setSimulationState] = useState(null);
  const [activeScenarioId, setActiveScenarioId] = useState('B'); // Default to B
  const [currentStatus, setCurrentStatus] = useState('IDLE');
  const [error, setError] = useState(null);
  const [isRefuelLoading, setIsRefuelLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('refuel'); // 'refuel', 'drive', 'insights', 'chat'

  // Trigger refuel analysis manually (on-demand) and stream results
  const handleAnalyzeRefuel = async () => {
    setIsRefuelLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/refuel/active`);
      if (!response.ok) {
        throw new Error('Failed to run refuel analysis');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedReason = '';

      // Initialize loading state in UI
      setSimulationState((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          refuel_decision: {
            decision: 'PENDING',
            reason: '',
            estimated_savings: 0.0,
            is_ai_justified: false,
          }
        };
      });

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Save the incomplete last line back to buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.type === 'metadata') {
              setSimulationState((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  refuel_decision: {
                    ...prev.refuel_decision,
                    decision: data.decision,
                    estimated_savings: data.estimated_savings,
                    is_ai_justified: false,
                  }
                };
              });
            } else if (data.type === 'chunk') {
              accumulatedReason += data.content;
              setSimulationState((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  refuel_decision: {
                    ...prev.refuel_decision,
                    reason: accumulatedReason,
                    is_ai_justified: true, // first chunk turns off shimmer and starts streaming
                  }
                };
              });
            }
          } catch (e) {
            console.error('Error parsing refuel stream JSON-line:', e);
          }
        }
      }

      // Re-poll to lock in full backend DB state sync
      await fetchState();
    } catch (err) {
      console.error('Error analyzing refuel:', err);
    } finally {
      setIsRefuelLoading(false);
    }
  };

  // Poll simulation state
  const fetchState = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/scenario/state`);
      if (!response.ok) {
        throw new Error('Failed to fetch simulation state');
      }
      
      const data = await response.json();
      
      if (data.status === 'ERROR') {
        setError(data.error);
        return;
      }

      setError(null);
      const stateObj = data.simulation_state;
      if (stateObj) {
        setSimulationState(stateObj);
        setActiveScenarioId(stateObj.scenario_id);
        setCurrentStatus(stateObj.status);
      }
    } catch (err) {
      console.error('Error fetching state:', err);
      setError({
        code: 'NETWORK_ERROR',
        message: "Unable to connect to the vehicle's onboard diagnostics system. Please check your backend connection."
      });
    }
  };

  // Trigger scenario set
  const handleSelectScenario = async (scenarioId) => {
    setCurrentStatus('RESETTING');
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/scenario/set`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: scenarioId }),
      });

      if (!response.ok) {
        throw new Error('Failed to set scenario');
      }

      // Re-fetch immediately to show resetting status
      await fetchState();
    } catch (err) {
      console.error('Error setting scenario:', err);
      setError({
        code: 'SWITCH_ERROR',
        message: 'Failed to switch scenario stream. Ensure the backend is active.'
      });
    }
  };

  // Start polling on mount
  useEffect(() => {
    fetchState(); // Initial fetch
    
    // Poll every 3 seconds as per Section 5.1 of api-contract-and-state-sync.md
    const interval = setInterval(() => {
      fetchState();
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // Auto-trigger refuel analysis when state loads and decision is missing
  useEffect(() => {
    if (simulationState && (!simulationState.refuel_decision || !simulationState.refuel_decision.decision) && !isRefuelLoading) {
      handleAnalyzeRefuel();
    }
  }, [simulationState, isRefuelLoading]);

  const telemetry = simulationState?.telemetry || {};
  const analytics = simulationState?.analytics || {};
  const refuel = simulationState?.refuel_decision || {};
  const priceContext = simulationState?.fuel_price_context || {};
  const aiInsights = simulationState?.ai_insights || {};

  return (
    <div className="app-layout-wrapper">
      {/* Centered Mobile Phone Frame */}
      <div className="app-container">
        {/* Header */}
        <header className="app-header">
          <div className="logo-wrapper">
            <svg viewBox="0 0 24 24" width="22" height="22" className="logo-icon">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" fill="currentColor"/>
            </svg>
            <span className="app-title">FuelSense</span>
          </div>
          
          <div className={`live-indicator ${currentStatus !== 'RUNNING' ? 'live-indicator-stopped' : ''}`}>
            <span className={`pulse-dot ${currentStatus !== 'RUNNING' ? 'pulse-dot-stopped' : ''}`} />
            <span>{currentStatus === 'RUNNING' ? 'Live Telemetry' : currentStatus}</span>
          </div>
        </header>

        {/* Loading overlay for RESETTING state */}
        {currentStatus === 'RESETTING' && (
          <div className="loading-overlay">
            <div className="spinner" />
            <span className="loading-text">Connecting to Telemetry Feed...</span>
          </div>
        )}

        {/* Error overlay */}
        {error && (
          <div className="error-overlay">
            <div className="error-title">Telemetry Signal Offline</div>
            <p className="error-msg">{error.message}</p>
            <button onClick={fetchState} className="chat-send-btn" style={{ width: 'auto', padding: '8px 16px', fontSize: '11px', fontWeight: 'bold' }}>
              Reconnect Signal
            </button>
          </div>
        )}

        {/* Dashboard Content */}
        <main className="dashboard-content">
          {activeTab === 'refuel' && (
            <RefuelDecisionCard
              refuel={refuel}
              priceContext={priceContext}
              fuelLevel={telemetry.fuel_level_pct || 100}
              onAnalyze={handleAnalyzeRefuel}
              isLoading={isRefuelLoading}
            />
          )}

          {activeTab === 'drive' && (
            <>
              <EcoScoreGauge score={analytics.eco_score || 100} />
              <div className="metrics-grid">
                <MetricCard
                  label="Fuel Efficiency"
                  value={analytics.fuel_efficiency?.toFixed(1) || '0.0'}
                  unit="L/100km"
                  subLabel="Standardized fuel consumption"
                />
                <MetricCard
                  label="Cost Index"
                  value={analytics.cost_per_km ? `RM${analytics.cost_per_km.toFixed(3)}` : 'RM0.000'}
                  unit="/ km"
                  subLabel="Projected cost per kilometer"
                />
                <MetricCard
                  label="Projected Spend"
                  value={analytics.monthly_spend_myr ? `RM${analytics.monthly_spend_myr.toFixed(2)}` : 'RM0.00'}
                  unit="/ mo"
                  subLabel="Estimated monthly spend (1.2k km)"
                />
                <MetricCard
                  label="Carbon Footprint"
                  value={analytics.co2_kg?.toFixed(1) || '0.0'}
                  unit="kg CO₂"
                  subLabel="Projected monthly CO₂ footprint"
                />
              </div>
              <BehaviorBreakdownBar
                idlePct={analytics.idle_pct || 0}
                drivingMode={telemetry.driving_mode || 'city'}
              />
            </>
          )}

          {activeTab === 'insights' && (
            <AIInsightPanel aiInsights={aiInsights} scenarioId={activeScenarioId} apiBaseUrl={API_BASE_URL} />
          )}

          {activeTab === 'chat' && (
            <AIChat apiBaseUrl={API_BASE_URL} />
          )}
        </main>

        {/* Bottom Navigation Bar */}
        <nav className="bottom-nav">
          <button 
            className={`bottom-nav-item ${activeTab === 'refuel' ? 'active' : ''}`}
            onClick={() => setActiveTab('refuel')}
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M19 5h-1V3H6v2H5c-1.1 0-2 .9-2 2v10h1v4h12v-4h1v-7c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm-3 12H8v-2h8v2zm0-4H8V7h8v6z" fill="currentColor"/>
            </svg>
            <span>Refuel</span>
          </button>
          <button 
            className={`bottom-nav-item ${activeTab === 'drive' ? 'active' : ''}`}
            onClick={() => setActiveTab('drive')}
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M12 4C6.5 4 2 8.5 2 14c0 4.7 3.3 8.6 7.8 9.7.5.1 1-.3 1-.8v-.5c0-.4-.3-.8-.7-.9C6.4 20.6 4 17.6 4 14c0-4.4 3.6-8 8-8s8 3.6 8 8c0 3.6-2.4 6.6-6.1 7.5-.4.1-.7.5-.7.9v.5c0 .5.5.9 1 .8 4.5-1.1 7.8-5 7.8-9.7 0-5.5-4.5-10-10-10z M12.5 8h-1v5.2l4.5 2.7.5-.8-4-2.4V8z" fill="currentColor"/>
            </svg>
            <span>Eco Drive</span>
          </button>
          <button 
            className={`bottom-nav-item ${activeTab === 'insights' ? 'active' : ''}`}
            onClick={() => setActiveTab('insights')}
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" fill="currentColor"/>
            </svg>
            <span>AI Report</span>
          </button>
          <button 
            className={`bottom-nav-item ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M11.5 9.5L9 4L6.5 9.5L1 12L6.5 14.5L9 20L11.5 14.5L17 12L11.5 9.5Z M20 8.5L19 6L18 8.5L15.5 9.5L18 10.5L19 13L20 10.5L22.5 9.5L20 8.5Z" fill="currentColor"/>
            </svg>
            <span>Copilot</span>
          </button>
        </nav>

        {/* Level 6: Floating Action Button selector (Only displayed on mobile sizes) */}
        <ScenarioFAB
          onSelectScenario={handleSelectScenario}
          activeScenarioId={activeScenarioId}
          currentStatus={currentStatus}
        />
      </div>

      {/* Desktop Simulation Controller Sidebar (Only displayed on desktop sizes) */}
      <aside className="demo-control-sidebar">
        <div className="sidebar-header">
          <h3>Simulation Controller</h3>
          <p>Inject driving profiles to test refuel optimizer recommendations and driving style analytics.</p>
        </div>

        <div className="sidebar-menu">
          {[
            { id: 'A', name: 'Urban Congestion', desc: 'Stop-and-go heavy city traffic' },
            { id: 'B', name: 'Highway Cruising', desc: 'Optimal high-speed fuel efficiency' },
            { id: 'C', name: 'Aggressive Driving', desc: 'High RPM performance driving stress-test' },
            { id: 'D', name: 'Mixed Commute', desc: 'Balanced real-world weekly driving cycle' },
          ].map((sc) => (
            <button
              key={sc.id}
              onClick={() => handleSelectScenario(sc.id)}
              className={`sidebar-menu-item ${activeScenarioId === sc.id ? 'sidebar-item-active' : ''}`}
            >
              <div className="sidebar-item-info">
                <span className="sidebar-item-name">{sc.name}</span>
                <span className="sidebar-item-desc">{sc.desc}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {activeScenarioId === sc.id && <span className="active-dot" />}
                <span className="sidebar-item-badge">{sc.id}</span>
              </div>
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <span className="footer-status-lbl">Diagnostics Node</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className={`pulse-dot ${currentStatus !== 'RUNNING' ? 'pulse-dot-stopped' : ''}`} style={{ width: '8px', height: '8px' }} />
            <span style={{ fontSize: '11px', fontWeight: '800', textTransform: 'uppercase', color: currentStatus === 'RUNNING' ? '#10b981' : '#ef4444' }}>
              {currentStatus}
            </span>
          </div>
        </div>
      </aside>
    </div>
  );
}

export default App;
