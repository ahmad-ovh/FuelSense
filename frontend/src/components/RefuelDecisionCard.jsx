import React from 'react';

const RefuelDecisionCard = ({ refuel = null, priceContext = {}, fuelLevel = 100, onAnalyze, isLoading }) => {
  // If refuel is null, not calculated yet, or empty, render the CTA calculation button
  if (!refuel || !refuel.decision) {
    return (
      <div className="decision-card decision-neutral" style={{ minHeight: '160px', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
          <span className="decision-title" style={{ alignSelf: 'center' }}>Refuel Intelligence</span>
          <p className="decision-reason" style={{ fontSize: '13px', color: '#94a3b8' }}>
            Refuel timing is currently uncalculated to ensure maximum telemetry precision.
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
            {isLoading ? 'Running Algorithms...' : 'Analyze Refuel Timing'}
          </button>
        </div>
      </div>
    );
  }

  const { decision = 'BUY', reason = 'Standard evaluation', estimated_savings = 0.0 } = refuel;
  const { current_price = 2.05, rolling_30day_avg = 2.05, trend = 'NEUTRAL' } = priceContext;

  // Determine urgency level and colors
  let cardClass = 'decision-buy';
  let badgeText = 'Recommended';
  let badgeClass = 'badge-recommended';

  if (decision === 'WAIT') {
    cardClass = 'decision-wait';
    badgeText = 'Neutral';
    badgeClass = 'badge-neutral';
  } else if (fuelLevel < 15.0 || reason.toLowerCase().includes('critical') || reason.toLowerCase().includes('15%')) {
    cardClass = 'decision-critical';
    badgeText = 'CRITICAL';
    badgeClass = 'badge-critical';
  }

  // Trend Arrow Icon
  const getTrendIcon = () => {
    if (trend === 'RISING') {
      return (
        <svg viewBox="0 0 24 24" className="trend-arrow trend-rising" width="16" height="16">
          <path d="M4 12l1.41 1.41L11 7.83V20h2V7.83l5.58 5.59L20 12l-8-8-8 8z" fill="currentColor"/>
        </svg>
      );
    } else if (trend === 'FALLING') {
      return (
        <svg viewBox="0 0 24 24" className="trend-arrow trend-falling" width="16" height="16">
          <path d="M20 12l-1.41-1.41L13 16.17V4h-2v12.17l-5.58-5.59L4 12l8 8 8-8z" fill="currentColor"/>
        </svg>
      );
    }
    return <span className="trend-neutral">-</span>;
  };

  return (
    <div className={`decision-card ${cardClass}`}>
      <div className="decision-header">
        <span className="decision-title">Refuel Intelligence</span>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <button 
            onClick={onAnalyze} 
            disabled={isLoading}
            style={{ 
              background: 'rgba(255, 255, 255, 0.08)', 
              border: 'none', 
              color: '#94a3b8', 
              fontSize: '9px', 
              padding: '3px 8px', 
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            {isLoading ? '...' : 'Recalculate'}
          </button>
          <span className={`urgency-badge ${badgeClass}`}>{badgeText}</span>
        </div>
      </div>

      <div className="decision-value-wrapper">
        <h1 className="decision-value">{decision}</h1>
        {estimated_savings > 0 && (
          <div className="savings-badge">
            <span className="savings-label">Proj. Savings</span>
            <span className="savings-amount">RM{estimated_savings.toFixed(2)}</span>
          </div>
        )}
      </div>

      <p className="decision-reason">{reason}</p>

      <div className="price-trend-section">
        <div className="price-stat">
          <span className="price-lbl">Current Price</span>
          <span className="price-val">RM{current_price.toFixed(2)}/L</span>
        </div>
        <div className="trend-indicator-wrapper">
          {getTrendIcon()}
          <span className="trend-txt">{trend}</span>
        </div>
        <div className="price-stat">
          <span className="price-lbl">30d Avg</span>
          <span className="price-val">RM{rolling_30day_avg.toFixed(2)}/L</span>
        </div>
      </div>
    </div>
  );
};

export default RefuelDecisionCard;
