/**
 * AgentThinkingIndicator — animated AI agent thinking indicator.
 *
 * Replaces the static "Thinking through the brief…" text with an animated
 * SVG neural-network / brain-pulse animation that conveys AI processing.
 *
 * Pure CSS animation — no external GIF dependency, works offline, matches
 * the WAOOAW dark theme with neon cyan/purple accents.
 */

export interface AgentThinkingIndicatorProps {
  /** Optional message to display alongside the animation */
  message?: string
  /** Test ID for automation */
  'data-testid'?: string
}

export function AgentThinkingIndicator({
  message,
  'data-testid': testId = 'agent-thinking-indicator',
}: AgentThinkingIndicatorProps) {
  return (
    <div
      data-testid={testId}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.25rem 0',
      }}
    >
      {/* Animated AI brain SVG */}
      <div
        style={{
          width: '36px',
          height: '36px',
          flexShrink: 0,
        }}
      >
        <svg
          viewBox="0 0 48 48"
          width="36"
          height="36"
          xmlns="http://www.w3.org/2000/svg"
          role="img"
          aria-label="AI agent is thinking"
        >
          {/* Outer pulsing ring */}
          <circle cx="24" cy="24" r="20" fill="none" stroke="#667eea" strokeWidth="1.5" opacity="0.3">
            <animate attributeName="r" values="18;22;18" dur="2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.2;0.5;0.2" dur="2s" repeatCount="indefinite" />
          </circle>

          {/* Middle ring */}
          <circle cx="24" cy="24" r="14" fill="none" stroke="#00f2fe" strokeWidth="1" opacity="0.4">
            <animate attributeName="r" values="14;16;14" dur="1.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.3;0.6;0.3" dur="1.5s" repeatCount="indefinite" />
          </circle>

          {/* Core brain node */}
          <circle cx="24" cy="24" r="6" fill="#667eea" opacity="0.8">
            <animate attributeName="r" values="5;7;5" dur="1.2s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.6;1;0.6" dur="1.2s" repeatCount="indefinite" />
          </circle>

          {/* Neural connection lines — pulsing outward from center */}
          {/* Top */}
          <line x1="24" y1="18" x2="24" y2="8" stroke="#00f2fe" strokeWidth="1.2" strokeLinecap="round" opacity="0.5">
            <animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.8s" begin="0s" repeatCount="indefinite" />
          </line>
          {/* Top-right */}
          <line x1="28" y1="19" x2="36" y2="11" stroke="#00f2fe" strokeWidth="1.2" strokeLinecap="round" opacity="0.5">
            <animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.8s" begin="0.3s" repeatCount="indefinite" />
          </line>
          {/* Right */}
          <line x1="30" y1="24" x2="40" y2="24" stroke="#00f2fe" strokeWidth="1.2" strokeLinecap="round" opacity="0.5">
            <animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.8s" begin="0.6s" repeatCount="indefinite" />
          </line>
          {/* Bottom-right */}
          <line x1="28" y1="29" x2="36" y2="37" stroke="#00f2fe" strokeWidth="1.2" strokeLinecap="round" opacity="0.5">
            <animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.8s" begin="0.9s" repeatCount="indefinite" />
          </line>
          {/* Bottom */}
          <line x1="24" y1="30" x2="24" y2="40" stroke="#00f2fe" strokeWidth="1.2" strokeLinecap="round" opacity="0.5">
            <animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.8s" begin="1.2s" repeatCount="indefinite" />
          </line>
          {/* Bottom-left */}
          <line x1="20" y1="29" x2="12" y2="37" stroke="#00f2fe" strokeWidth="1.2" strokeLinecap="round" opacity="0.5">
            <animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.8s" begin="1.5s" repeatCount="indefinite" />
          </line>
          {/* Left */}
          <line x1="18" y1="24" x2="8" y2="24" stroke="#00f2fe" strokeWidth="1.2" strokeLinecap="round" opacity="0.5">
            <animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.8s" begin="0.15s" repeatCount="indefinite" />
          </line>
          {/* Top-left */}
          <line x1="20" y1="19" x2="12" y2="11" stroke="#00f2fe" strokeWidth="1.2" strokeLinecap="round" opacity="0.5">
            <animate attributeName="opacity" values="0.2;0.8;0.2" dur="1.8s" begin="0.45s" repeatCount="indefinite" />
          </line>

          {/* Outer endpoint nodes */}
          {[
            { cx: 24, cy: 7, delay: '0s' },
            { cx: 37, cy: 10, delay: '0.3s' },
            { cx: 41, cy: 24, delay: '0.6s' },
            { cx: 37, cy: 38, delay: '0.9s' },
            { cx: 24, cy: 41, delay: '1.2s' },
            { cx: 11, cy: 38, delay: '1.5s' },
            { cx: 7, cy: 24, delay: '0.15s' },
            { cx: 11, cy: 10, delay: '0.45s' },
          ].map((node, i) => (
            <circle key={i} cx={node.cx} cy={node.cy} r="2.5" fill="#00f2fe" opacity="0.4">
              <animate attributeName="r" values="1.5;3;1.5" dur="1.8s" begin={node.delay} repeatCount="indefinite" />
              <animate attributeName="opacity" values="0.3;0.9;0.3" dur="1.8s" begin={node.delay} repeatCount="indefinite" />
            </circle>
          ))}

          {/* Rotating scan arc */}
          <circle cx="24" cy="24" r="16" fill="none" stroke="#f093fb" strokeWidth="1.5" strokeDasharray="8 92" strokeLinecap="round" opacity="0.5">
            <animateTransform attributeName="transform" type="rotate" from="0 24 24" to="360 24 24" dur="3s" repeatCount="indefinite" />
          </circle>
        </svg>
      </div>

      {/* Animated typing dots */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
        {message ? (
          <span style={{ fontSize: '0.88rem', opacity: 0.85 }}>{message}</span>
        ) : null}
        <span style={{ display: 'inline-flex', gap: '3px', marginLeft: message ? '0.25rem' : 0 }}>
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              style={{
                width: '5px',
                height: '5px',
                borderRadius: '50%',
                background: '#00f2fe',
                display: 'inline-block',
                animation: `agentThinkingDot 1.4s ease-in-out ${i * 0.2}s infinite`,
              }}
            />
          ))}
        </span>
      </div>

      {/* Keyframe injection — only added once */}
      <style>{`
        @keyframes agentThinkingDot {
          0%, 80%, 100% { transform: scale(0.4); opacity: 0.3; }
          40% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  )
}
