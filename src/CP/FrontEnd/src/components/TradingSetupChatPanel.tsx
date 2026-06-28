import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Badge, Button, Dialog, DialogActions, DialogBody,
  DialogContent, DialogSurface, DialogTitle, Spinner,
} from '@fluentui/react-components'
import { FeedbackMessage } from './FeedbackIndicators'
import {
  getTradingSetup, sendTradingSetupMessage, emergencyStop,
  type TradingSetupMessage, type TradingSetupResponse,
} from '../services/tradingSetup.service'

// Design tokens — never use other hex values
const COLOURS = {
  bg: '#0a0a0a',
  card: '#18181b',
  cyan: '#00f2fe',
  green: '#10b981',
  red: '#ef4444',
  yellow: '#f59e0b',
  textPrimary: '#f4f4f5',
  textSecondary: '#71717a',
  border: '#27272a',
}

const SECURE_STEPS = new Set(['api_key', 'api_secret'])

const STEP_LABEL: Record<string, string> = {
  welcome: 'Welcome',
  api_key: 'Step 1 of 10 — API Key',
  api_secret: 'Step 2 of 10 — API Secret',
  validate: 'Step 3 of 10 — Validating…',
  instrument: 'Step 4 of 10 — Instrument',
  rsi_period: 'Step 5 of 10 — RSI Period',
  risk_limits: 'Step 6 of 10 — Risk Limits',
  capital_pct: 'Step 7 of 10 — Capital Deployment',
  leverage: 'Step 8 of 10 — Leverage',
  autonomous_mode: 'Step 9 of 10 — Autonomous Mode',
  risk_disclosure: 'Step 10 of 10 — Risk Disclosure',
  done: 'Setup Complete ✅',
}

interface Props {
  hiredInstanceId: string
}

export function TradingSetupChatPanel({ hiredInstanceId }: Props) {
  const [messages, setMessages] = useState<TradingSetupMessage[]>([])
  const [step, setStep] = useState('welcome')
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stopDialogOpen, setStopDialogOpen] = useState(false)
  const [stopping, setStopping] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  const isSecure = SECURE_STEPS.has(step)

  useEffect(() => {
    getTradingSetup(hiredInstanceId)
      .then((resp: TradingSetupResponse) => {
        setMessages(resp.state.messages)
        setStep(resp.state.step)
      })
      .catch(() => setError('Failed to load trading setup.'))
      .finally(() => setLoading(false))
  }, [hiredInstanceId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || sending) return
    setInputText('')
    setSending(true)
    setError(null)
    try {
      const resp = await sendTradingSetupMessage(hiredInstanceId, text)
      setMessages(resp.state.messages)
      setStep(resp.state.step)
    } catch {
      setError('Failed to send. Please try again.')
    } finally {
      setSending(false)
    }
  }, [hiredInstanceId, inputText, sending])

  const handleEmergencyStop = async () => {
    setStopping(true)
    try {
      await emergencyStop(hiredInstanceId)
      setStopDialogOpen(false)
      setError(null)
    } catch {
      setError('Emergency stop failed. Please try again.')
    } finally {
      setStopping(false)
    }
  }

  if (loading) return <Spinner label="Loading trading setup…" />
  if (error) return <FeedbackMessage intent="error" message={error} />

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 8 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0' }}>
        <div>
          <span style={{ color: COLOURS.textPrimary, fontWeight: 600 }}>⚙️ Configure Trading</span>
          <span style={{ color: COLOURS.textSecondary, fontSize: 12, marginLeft: 12 }}>
            {STEP_LABEL[step] ?? step}
          </span>
        </div>
        {isSecure && (
          <Badge appearance="tint" color="success" size="small">🔒 Secure Input</Badge>
        )}
      </div>

      {/* Autonomous mode warning */}
      {step === 'autonomous_mode' && (
        <div style={{ background: `${COLOURS.yellow}18`, border: `1px solid ${COLOURS.yellow}55`,
          borderRadius: 8, padding: '8px 12px', fontSize: 12, color: COLOURS.yellow }}>
          ⚠️ Autonomous mode: trades will execute without approval. You will be notified after each.
        </div>
      )}

      {/* Message list */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8, padding: '4px 0' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '80%',
            background: msg.role === 'user'
              ? (msg.masked ? `${COLOURS.green}18` : `${COLOURS.cyan}18`)
              : COLOURS.card,
            border: `1px solid ${msg.role === 'user' ? (msg.masked ? `${COLOURS.green}55` : `${COLOURS.cyan}55`) : COLOURS.border}`,
            borderRadius: 12, padding: '8px 12px',
          }}>
            {msg.masked && (
              <div style={{ color: COLOURS.green, fontSize: 10, marginBottom: 4, fontWeight: 600 }}>
                🔒 Encrypted
              </div>
            )}
            <p style={{ color: COLOURS.textPrimary, fontSize: 14, margin: 0, whiteSpace: 'pre-wrap' }}>
              {msg.content}
            </p>
          </div>
        ))}
        {sending && <Spinner size="tiny" style={{ alignSelf: 'flex-start', margin: '4px 0' }} />}
        <div ref={bottomRef} />
      </div>

      {/* Input bar — hidden on done step */}
      {step !== 'done' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, borderTop: `1px solid ${COLOURS.border}`, paddingTop: 8 }}>
          {isSecure && (
            <div style={{ fontSize: 11, color: COLOURS.green, marginBottom: 4 }}>
              🔒 Your input is masked and encrypted
            </div>
          )}
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type={isSecure ? 'password' : 'text'}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              disabled={sending}
              placeholder={isSecure ? 'Enter securely…' : 'Type your reply…'}
              data-testid="trading-chat-input"
              style={{
                flex: 1, background: COLOURS.card, border: `1px solid ${COLOURS.border}`,
                borderRadius: 8, padding: '8px 12px', color: COLOURS.textPrimary,
                fontSize: 14, outline: 'none',
              }}
            />
            <Button
              appearance="primary"
              onClick={handleSend}
              disabled={sending || !inputText.trim()}
              data-testid="trading-chat-send"
            >
              Send
            </Button>
          </div>
        </div>
      )}

      {/* Done step: Emergency Stop */}
      {step === 'done' && (
        <>
          <Button
            appearance="subtle"
            onClick={() => setStopDialogOpen(true)}
            data-testid="emergency-stop-btn"
            style={{ borderColor: `${COLOURS.red}55`, color: COLOURS.red, alignSelf: 'flex-start' }}
          >
            🛑 Emergency Stop
          </Button>
          <Dialog open={stopDialogOpen} onOpenChange={(_, d) => setStopDialogOpen(d.open)}>
            <DialogSurface style={{ background: COLOURS.card }}>
              <DialogBody>
                <DialogTitle style={{ color: COLOURS.red }}>⚠️ Confirm Emergency Stop</DialogTitle>
                <DialogContent style={{ color: COLOURS.textSecondary }}>
                  This will halt all trading immediately and pause your agent. Are you sure?
                </DialogContent>
                <DialogActions>
                  <Button appearance="subtle" onClick={() => setStopDialogOpen(false)}>Cancel</Button>
                  <Button
                    appearance="primary"
                    onClick={handleEmergencyStop}
                    disabled={stopping}
                    style={{ background: COLOURS.red }}
                    data-testid="emergency-stop-confirm"
                  >
                    {stopping ? <Spinner size="tiny" /> : 'Yes, stop trading'}
                  </Button>
                </DialogActions>
              </DialogBody>
            </DialogSurface>
          </Dialog>
        </>
      )}
    </div>
  )
}
