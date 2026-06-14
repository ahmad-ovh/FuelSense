import React from 'react';

const RefuelDecisionCard = ({ refuel = null, priceContext = {}, fuelLevel = 100, onAnalyze, isLoading }) => {
  // Render the CTA timing trigger state if uncalculated
  if (!refuel || !refuel.decision) {
    return (
      <div className="decision-card decision-neutral" style={{ minHeight: '160px', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
          <span className="decision-title" style={{ alignSelf: 'center' }}>Refuel Optimizer</span>
          <p className="decision-reason" style={{ fontSize: '12.5px', color: '#94a3b8', lineHeight: '1.4', padding: '0 12px' }}>
            Telemetry feed active. Analyze your refueling window using current fuel levels and weekly price trends.
          </p>
          <button 
            onClick={onAnalyze} 
            disabled={isLoading}
            className="chat-send-btn" 
            style={{ 
              alignSelf: 'center', 
              width: 'auto', 
              padding: '10px 24px', 
              fontSize: '13px', 
              fontWeight: '700', 
              borderRadius: '24px',
              background: 'linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%)',
              boxShadow: '0 4px 15px rgba(59, 130, 246, 0.3)',
              cursor: 'pointer'
            }}
          >
            {isLoading ? 'Processing Telemetry...' : 'Calculate Optimal Refuel Timing'}
          </button>
        </div>
      </div>
    );
  }

  const { decision = 'BUY', reason = 'Standard evaluation', estimated_savings = 0.0, is_ai_justified = false } = refuel;
  const { current_price = 2.05, rolling_30day_avg = 2.05, trend = 'NEUTRAL' } = priceContext;

  // Determine urgency levels
  let cardClass = 'decision-buy';
  let badgeText = 'Recommended';
  let badgeClass = 'badge-recommended';

  if (decision === 'PENDING') {
    cardClass = 'decision-neutral';
    badgeText = 'Analyzing...';
    badgeClass = 'badge-recommended';
  } else if (decision === 'WAIT') {
    cardClass = 'decision-wait';
    badgeText = 'Hold / Wait';
    badgeClass = 'badge-neutral';
  } else if (fuelLevel < 15.0 || reason.toLowerCase().includes('critical') || reason.toLowerCase().includes('15%')) {
    cardClass = 'decision-critical';
    badgeText = 'CRITICAL FUEL';
    badgeClass = 'badge-critical';
  }

  // Trend Arrow Icon
  const getTrendIcon = () => {
    if (trend === 'RISING') {
      return <i className="ph ph-trend-up trend-arrow trend-rising" style={{ fontSize: '16px' }}></i>;
    } else if (trend === 'FALLING') {
      return <i className="ph ph-trend-down trend-arrow trend-falling" style={{ fontSize: '16px' }}></i>;
    }
    return <span className="trend-neutral">-</span>;
  };

  return (
    <div className={`decision-card ${cardClass}`}>
      <div className="decision-header">
        <span className="decision-title">Refuel Optimizer</span>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button 
            onClick={onAnalyze} 
            disabled={isLoading}
            style={{ 
              background: 'rgba(255, 255, 255, 0.08)', 
              border: 'none', 
              color: '#cbd5e1', 
              fontSize: '9px', 
              padding: '3px 8px', 
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
              transition: 'background 0.2s'
            }}
            onMouseOver={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.15)'}
            onMouseOut={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.08)'}
          >
            {isLoading ? 'Recalculating...' : 'Recalculate Advice'}
          </button>
          <span className={`urgency-badge ${badgeClass}`}>{badgeText}</span>
        </div>
      </div>

      <div className="decision-value-wrapper">
        {decision === 'PENDING' ? (
          <div className="shimmer" style={{ height: '36px', width: '120px', borderRadius: '8px', marginBottom: '8px' }} />
        ) : (
          <h1 className="decision-value">{decision}</h1>
        )}
        {estimated_savings > 0 && (
          <div className="savings-badge">
            <span className="savings-label">Projected Savings</span>
            <span className="savings-amount">RM{estimated_savings.toFixed(2)}</span>
          </div>
        )}
      </div>

      {!is_ai_justified ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', margin: '12px 0 16px 0' }}>
          <div className="shimmer" style={{ height: '12.5px', width: '100%', borderRadius: '4px' }} />
          <div className="shimmer" style={{ height: '12.5px', width: '75%', borderRadius: '4px' }} />
        </div>
      ) : (
        <p className="decision-reason">{reason}</p>
      )}

      <div className="price-trend-section">
        <div className="price-stat">
          <span className="price-lbl">Pump Price (RON95)</span>
          <span className="price-val">RM{current_price.toFixed(2)}/L</span>
        </div>
        <div className="trend-indicator-wrapper">
          {getTrendIcon()}
          <span className="trend-txt" style={{ color: trend === 'RISING' ? '#ef4444' : '#10b981' }}>{trend}</span>
        </div>
        <div className="price-stat">
          <span className="price-lbl">30-Day Average</span>
          <span className="price-val">RM{rolling_30day_avg.toFixed(2)}/L</span>
        </div>
      </div>
    </div>
  );
};

export default RefuelDecisionCard;
