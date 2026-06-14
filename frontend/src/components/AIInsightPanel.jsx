import React, { useState, useEffect, useRef } from 'react';

const AIInsightPanel = ({ aiInsights = {}, scenarioId, apiBaseUrl }) => {
  const { explanation = '', status = '' } = aiInsights;
  const [streamedText, setStreamedText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const activeStreamRef = useRef(null);

  useEffect(() => {
    // If backend state says loading and we are not already streaming, run the stream
    if (status === 'loading' && !isStreaming && scenarioId) {
      startStreamingInsights();
    }
  }, [status, scenarioId]);

  const startStreamingInsights = async () => {
    if (activeStreamRef.current) return;
    setIsStreaming(true);
    setStreamedText('');
    activeStreamRef.current = true;

    try {
      const response = await fetch(`${apiBaseUrl}/scenario/insights/stream?scenario_id=${scenarioId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch insights stream');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Save last partial line back to buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.type === 'chunk') {
              accumulatedText += data.content;
              setStreamedText(accumulatedText);
            }
          } catch (e) {
            console.error('Error parsing insights stream chunk:', e);
          }
        }
      }
    } catch (e) {
      console.error('Error streaming insights:', e);
    } finally {
      setIsStreaming(false);
      activeStreamRef.current = null;
    }
  };

  // Use the streamed text if active, otherwise fallback to the central cached state
  const displayText = isStreaming ? streamedText : (status === 'loading' ? '' : explanation);

  // Helper to parse Cause, Effect, and Action from the explanation text dynamically
  const parseInsights = (text) => {
    let cause = '';
    let effect = '';
    let action = '';

    if (text) {
      if (text.includes("Cause:")) {
        const afterCause = text.split("Cause:")[1] || "";
        if (afterCause.includes("Effect:")) {
          cause = afterCause.split("Effect:")[0].trim();
          const afterEffect = afterCause.split("Effect:")[1] || "";
          if (afterEffect.includes("Action:")) {
            effect = afterEffect.split("Action:")[0].trim();
            action = afterEffect.split("Action:")[1].trim();
          } else {
            effect = afterEffect.trim();
          }
        } else {
          cause = afterCause.trim();
        }
      } else {
        cause = text;
      }
    }

    return { cause, effect, action };
  };

  const { cause, effect, action } = parseInsights(displayText);
  const isLoadingState = status === 'loading' || isStreaming;

  return (
    <div className="ai-insight-panel">
      <h3 className="section-title">AI Driving Performance Report</h3>
      <div className="insight-grid">
        {/* Cause Block */}
        {!cause && isLoadingState ? (
          <div className="insight-item insight-skeleton">
            <div className="insight-lbl-badge" style={{ color: '#f59e0b' }}>CAUSE</div>
            <div className="shimmer" style={{ width: '90%', height: '8px', borderRadius: '4px', marginBottom: '6px' }} />
            <div className="shimmer" style={{ width: '75%', height: '8px', borderRadius: '4px' }} />
          </div>
        ) : (
          <div className="insight-item insight-cause">
            <div className="insight-lbl-badge font-semibold">CAUSE</div>
            <p className="insight-desc">{cause || "No congestion or idling patterns detected."}</p>
          </div>
        )}

        {/* Effect Block */}
        {!effect && isLoadingState ? (
          <div className="insight-item insight-skeleton">
            <div className="insight-lbl-badge" style={{ color: '#3b82f6' }}>EFFECT</div>
            <div className="shimmer" style={{ width: '85%', height: '8px', borderRadius: '4px', marginBottom: '6px' }} />
            <div className="shimmer" style={{ width: '60%', height: '8px', borderRadius: '4px' }} />
          </div>
        ) : (
          <div className="insight-item insight-effect">
            <div className="insight-lbl-badge font-semibold">EFFECT</div>
            <p className="insight-desc">{effect || "Driving efficiency meets standard expectations."}</p>
          </div>
        )}

        {/* Action Block */}
        {!action && isLoadingState ? (
          <div className="insight-item insight-skeleton">
            <div className="insight-lbl-badge" style={{ color: '#10b981' }}>ACTION</div>
            <div className="shimmer" style={{ width: '80%', height: '8px', borderRadius: '4px', marginBottom: '6px' }} />
            <div className="shimmer" style={{ width: '70%', height: '8px', borderRadius: '4px' }} />
          </div>
        ) : (
          <div className="insight-item insight-action">
            <div className="insight-lbl-badge font-semibold">ACTION</div>
            <p className="insight-desc">{action || "Continue driving to collect telemetry."}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIInsightPanel;
