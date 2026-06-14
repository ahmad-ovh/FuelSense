import React from 'react';

const AIInsightPanel = ({ aiInsights = {} }) => {
  const { explanation = '', status = '' } = aiInsights;

  if (status === 'loading' || !explanation || explanation.includes('Generating report...')) {
    return (
      <div className="ai-insight-panel">
        <h3 className="section-title">AI Advisor Insights</h3>
        <div className="insight-grid">
          <div className="insight-item insight-skeleton">
            <div className="shimmer" style={{ width: '30%', height: '10px', borderRadius: '4px', marginBottom: '8px' }} />
            <div className="shimmer" style={{ width: '90%', height: '8px', borderRadius: '4px', marginBottom: '6px' }} />
            <div className="shimmer" style={{ width: '75%', height: '8px', borderRadius: '4px' }} />
          </div>
          <div className="insight-item insight-skeleton">
            <div className="shimmer" style={{ width: '30%', height: '10px', borderRadius: '4px', marginBottom: '8px' }} />
            <div className="shimmer" style={{ width: '85%', height: '8px', borderRadius: '4px', marginBottom: '6px' }} />
            <div className="shimmer" style={{ width: '60%', height: '8px', borderRadius: '4px' }} />
          </div>
          <div className="insight-item insight-skeleton">
            <div className="shimmer" style={{ width: '30%', height: '10px', borderRadius: '4px', marginBottom: '8px' }} />
            <div className="shimmer" style={{ width: '80%', height: '8px', borderRadius: '4px', marginBottom: '6px' }} />
            <div className="shimmer" style={{ width: '70%', height: '8px', borderRadius: '4px' }} />
          </div>
        </div>
      </div>
    );
  }

  // Helper to parse Cause, Effect, and Action from the explanation text
  const parseInsights = (text) => {
    let cause = "Analyzing driving patterns...";
    let effect = "Waiting for more telemetry data.";
    let action = "Continue driving normally.";

    if (text) {
      try {
        if (text.includes("Cause:") && text.includes("Effect:") && text.includes("Action:")) {
          cause = text.split("Cause:")[1].split("Effect:")[0].trim();
          effect = text.split("Effect:")[1].split("Action:")[0].trim();
          action = text.split("Action:")[1].trim();
        } else {
          // Fallback if not matching exactly
          cause = text;
        }
      } catch (e) {
        cause = text;
      }
    }

    return { cause, effect, action };
  };

  const { cause, effect, action } = parseInsights(explanation);

  return (
    <div className="ai-insight-panel">
      <h3 className="section-title">AI Advisor Insights</h3>
      <div className="insight-grid">
        <div className="insight-item insight-cause">
          <div className="insight-lbl-badge font-semibold">CAUSE</div>
          <p className="insight-desc">{cause}</p>
        </div>
        <div className="insight-item insight-effect">
          <div className="insight-lbl-badge font-semibold">EFFECT</div>
          <p className="insight-desc">{effect}</p>
        </div>
        <div className="insight-item insight-action">
          <div className="insight-lbl-badge font-semibold">ACTION</div>
          <p className="insight-desc">{action}</p>
        </div>
      </div>
    </div>
  );
};

export default AIInsightPanel;
