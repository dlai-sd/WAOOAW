/**
 * TradingSetupScreen — chat-based configuration wizard for Share Trader agent.
 *
 * Mirrors the DMAConversationScreen pattern but uses a rule-based step machine
 * (no LLM) because API keys must never be sent to an AI model.
 *
 * Sensitive steps (api_key, api_secret) use secureTextEntry so the OS masks
 * the input field. All masked content shows ●●●●… in the chat bubbles.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react'
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from 'react-native'
import { useTheme } from '@/hooks/useTheme'
import {
  getTradingSetup,
  sendTradingSetupMessage,
  type TradingSetupMessage,
} from '@/services/tradingSetup.service'
import type { MyAgentsStackScreenProps } from '@/navigation/types'

type Props = MyAgentsStackScreenProps<'TradingSetup'>

const SECURE_STEPS = new Set(['api_key', 'api_secret'])

export const TradingSetupScreen = ({ navigation, route }: Props) => {
  const { hiredAgentId } = route.params
  const { colors, typography } = useTheme()
  const scrollRef = useRef<ScrollView>(null)

  const [messages, setMessages] = useState<TradingSetupMessage[]>([])
  const [currentStep, setCurrentStep] = useState<string>('welcome')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inputText, setInputText] = useState('')
  const [sending, setSending] = useState(false)

  const isSecureStep = SECURE_STEPS.has(currentStep)

  useEffect(() => {
    getTradingSetup(hiredAgentId)
      .then((resp) => {
        setMessages(resp.state?.messages ?? [])
        setCurrentStep(resp.state?.step ?? 'welcome')
      })
      .catch(() => setError('Failed to load trading setup. Please try again.'))
      .finally(() => setLoading(false))
  }, [hiredAgentId])

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || sending) return

    // For sensitive steps, add masked preview locally before the server response
    const displayContent = isSecureStep ? '●'.repeat(Math.min(text.length, 8)) + '…' : text
    const optimisticMsg: TradingSetupMessage = {
      role: 'user',
      content: displayContent,
      masked: isSecureStep,
    }
    setMessages((prev) => [...prev, optimisticMsg])
    setInputText('')
    setSending(true)

    try {
      const resp = await sendTradingSetupMessage(hiredAgentId, text)
      setMessages(resp.state?.messages ?? [])
      setCurrentStep(resp.state?.step ?? 'welcome')
    } catch {
      setError('Failed to send message. Please try again.')
    } finally {
      setSending(false)
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100)
    }
  }, [hiredAgentId, inputText, sending, isSecureStep])

  const stepLabel: Record<string, string> = {
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

  if (loading) {
    return (
      <SafeAreaView style={[s.root, { backgroundColor: colors.black }]}>
        <ActivityIndicator color={colors.neonCyan} style={{ flex: 1 }} />
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView
      style={[s.root, { backgroundColor: colors.black }]}
      testID="trading-setup-screen"
    >
      {/* Header */}
      <View style={[s.header, { borderBottomColor: colors.textSecondary + '20' }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} testID="trading-setup-back">
          <Text style={{ color: colors.neonCyan, fontSize: 14 }}>← Back</Text>
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text
            style={[s.title, { color: colors.textPrimary, fontFamily: typography.fontFamily.display }]}
          >
            ⚙️ Configure Trading
          </Text>
          <Text style={{ color: colors.textSecondary, fontSize: 12, marginTop: 2 }}>
            {stepLabel[currentStep] ?? currentStep}
          </Text>
        </View>
        {isSecureStep && (
          <View style={[s.secureBadge, { backgroundColor: '#10b98122', borderColor: '#10b98155' }]}>
            <Text style={{ color: '#10b981', fontSize: 11, fontWeight: '600' }}>🔒 Secure</Text>
          </View>
        )}
      </View>

      {error ? (
        <View style={[s.errorBanner, { backgroundColor: '#ef444418', borderColor: '#ef444455' }]}>
          <Text style={{ color: '#ef4444' }}>{error}</Text>
        </View>
      ) : null}

      {/* Autonomous mode warning banner */}
      {currentStep === 'autonomous_mode' && (
        <View
          style={{
            backgroundColor: '#f59e0b18',
            borderColor: '#f59e0b55',
            borderWidth: 1,
            borderRadius: 8,
            padding: 10,
            marginHorizontal: 16,
            marginTop: 8,
          }}
        >
          <Text style={{ color: '#f59e0b', fontSize: 12 }}>
            ⚠️ Autonomous mode: trades will execute without your approval. You will be notified after each execution.
          </Text>
        </View>
      )}

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={80}
      >
        <ScrollView
          ref={scrollRef}
          contentContainerStyle={{ padding: 16, gap: 12 }}
          onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: false })}
        >
          {messages.length === 0 ? (
            <Text style={{ color: colors.textSecondary, textAlign: 'center', marginTop: 40 }}>
              Loading your trading configuration…
            </Text>
          ) : (
            messages.map((msg, i) => (
              <View
                key={i}
                style={[
                  s.bubble,
                  msg.role === 'user'
                    ? {
                        alignSelf: 'flex-end',
                        backgroundColor: msg.masked ? '#10b98122' : '#667eea22',
                        borderColor: msg.masked ? '#10b98155' : '#667eea55',
                      }
                    : {
                        alignSelf: 'flex-start',
                        backgroundColor: '#18181b',
                        borderColor: colors.textSecondary + '30',
                      },
                ]}
              >
                {msg.masked && (
                  <Text style={{ color: '#10b981', fontSize: 10, marginBottom: 4, fontWeight: '600' }}>
                    🔒 Encrypted
                  </Text>
                )}
                <Text style={{ color: colors.textPrimary, fontSize: 14, lineHeight: 20 }}>
                  {msg.content}
                </Text>
              </View>
            ))
          )}
          {sending ? (
            <ActivityIndicator
              color={colors.neonCyan}
              style={{ alignSelf: 'flex-start', marginLeft: 16 }}
            />
          ) : null}
        </ScrollView>

        {/* Input bar — hidden on done step */}
        {currentStep !== 'done' && (
          <View
            style={[
              s.inputBar,
              { borderTopColor: colors.textSecondary + '20', backgroundColor: colors.black },
            ]}
          >
            {isSecureStep && (
              <Text style={{ color: '#10b981', fontSize: 11, marginBottom: 6, paddingHorizontal: 2 }}>
                🔒 Your input is masked and encrypted
              </Text>
            )}
            <View style={s.inputRow}>
              <TextInput
                style={[
                  s.textInput,
                  {
                    color: colors.textPrimary,
                    borderColor: isSecureStep
                      ? '#10b98160'
                      : colors.textSecondary + '40',
                  },
                ]}
                value={inputText}
                onChangeText={setInputText}
                placeholder={isSecureStep ? 'Enter securely…' : 'Type your message…'}
                placeholderTextColor={colors.textSecondary}
                secureTextEntry={isSecureStep}
                autoCapitalize="none"
                autoCorrect={false}
                multiline={!isSecureStep}
                editable={!sending && currentStep !== 'validate'}
                testID="trading-setup-input"
              />
              <TouchableOpacity
                style={[
                  s.sendBtn,
                  {
                    backgroundColor:
                      sending || !inputText.trim() || currentStep === 'validate'
                        ? colors.textSecondary + '40'
                        : colors.neonCyan,
                  },
                ]}
                onPress={handleSend}
                disabled={sending || !inputText.trim() || currentStep === 'validate'}
                testID="trading-setup-send"
              >
                <Text style={{ color: '#0a0a0a', fontWeight: '700', fontSize: 13 }}>
                  {currentStep === 'validate' ? '…' : 'Send'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Done — back to agent button */}
        {currentStep === 'done' && (
          <View style={[s.doneBar, { borderTopColor: colors.textSecondary + '20' }]}>
            <TouchableOpacity
              style={[s.doneBtn, { backgroundColor: colors.neonCyan }]}
              onPress={() => navigation.goBack()}
              testID="trading-setup-done-btn"
            >
              <Text style={{ color: '#0a0a0a', fontWeight: '700', fontSize: 15 }}>
                🚀 Go to Agent Dashboard
              </Text>
            </TouchableOpacity>
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const s = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 16,
    borderBottomWidth: 1,
  },
  title: { fontSize: 18, fontWeight: 'bold' },
  secureBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    borderWidth: 1,
  },
  errorBanner: { margin: 12, padding: 12, borderRadius: 8, borderWidth: 1 },
  bubble: { maxWidth: '82%', borderRadius: 14, borderWidth: 1, padding: 12 },
  inputBar: { padding: 12, borderTopWidth: 1 },
  inputRow: { flexDirection: 'row', alignItems: 'flex-end', gap: 10 },
  textInput: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 10,
    padding: 10,
    minHeight: 40,
    maxHeight: 120,
    fontSize: 14,
  },
  sendBtn: {
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  doneBar: { padding: 16, borderTopWidth: 1 },
  doneBtn: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
})
