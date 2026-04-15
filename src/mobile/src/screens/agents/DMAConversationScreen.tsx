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
  getDigitalMarketingActivationWorkspace,
  patchDigitalMarketingActivationWorkspace,
  type DigitalMarketingStrategyWorkshopMessage,
} from '@/services/digitalMarketingActivation.service'
import {
  listCustomerDraftBatches,
  createContentBatchFromTheme,
  type DraftBatch,
  type DraftPost,
} from '@/services/marketingReview.service'
import { listPlatformConnections } from '@/services/platformConnections.service'
import { ArtifactRenderer } from '@/components/ArtifactRenderer'
import { VoiceFAB } from '@/components/voice/VoiceFAB'
import { useAgentVoiceOverlay } from '@/hooks/useAgentVoiceOverlay'
import type { MyAgentsStackScreenProps } from '@/navigation/types'

type Props = MyAgentsStackScreenProps<'DMAConversation'>

export const DMAConversationScreen = ({ navigation, route }: Props) => {
  const { hiredAgentId } = route.params
  const { colors, typography } = useTheme()
  const scrollRef = useRef<ScrollView>(null)

  const [messages, setMessages] = useState<DigitalMarketingStrategyWorkshopMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [inputText, setInputText] = useState('')
  const [sending, setSending] = useState(false)
  const [batches, setBatches] = useState<DraftBatch[]>([])
  const [createBatchLoading, setCreateBatchLoading] = useState(false)
  const [platformConnections, setPlatformConnections] = useState<any[]>([])

  useEffect(() => {
    Promise.all([
      getDigitalMarketingActivationWorkspace(hiredAgentId),
      listCustomerDraftBatches(),
      listPlatformConnections(hiredAgentId),
    ]).then(([resp, batchList, connections]) => {
      setMessages(resp.workspace?.campaign_setup?.strategy_workshop?.messages ?? [])
      setBatches(batchList)
      setPlatformConnections(Array.isArray(connections) ? connections : (connections as any)?.connections ?? [])
    }).catch(() => setError('Failed to load conversation. Please try again.'))
      .finally(() => setLoading(false))
  }, [hiredAgentId])

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || sending) return
    const userMsg: DigitalMarketingStrategyWorkshopMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInputText('')
    setSending(true)
    try {
      const resp = await patchDigitalMarketingActivationWorkspace(hiredAgentId, {
        campaign_setup: { strategy_workshop: { messages: [...messages, userMsg] } },
      })
      setMessages(resp.workspace?.campaign_setup?.strategy_workshop?.messages ?? [])
    } catch {
      setError('Failed to send message. Please try again.')
    } finally {
      setSending(false)
      setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100)
    }
  }, [hiredAgentId, inputText, messages, sending])

  const { isListening: voiceListening, toggle: voiceToggle, isAvailable: voiceAvailable } =
    useAgentVoiceOverlay({ 'send message': handleSend })

  // Derive pending theme batch (batch_type === 'theme' with status not yet content_generated)
  const pendingThemeBatch = batches.find(
    (b) => b.batch_type === 'theme' && b.status !== 'content_generated'
  ) ?? null

  // Derive YouTube credential ref from platform connections
  const youtubeConn = platformConnections.find((c: any) => (c.platform_key ?? c.platform) === 'youtube') as any
  const youtubeCredentialRef: string | null = youtubeConn?.credential_ref ?? youtubeConn?.customer_platform_credential_id ?? null

  const handleGenerateContent = useCallback(async () => {
    if (!pendingThemeBatch || createBatchLoading) return
    setCreateBatchLoading(true)
    try {
      const result = await createContentBatchFromTheme(pendingThemeBatch.batch_id, {
        youtube_credential_ref: youtubeCredentialRef,
      })
      setBatches((prev) => [...prev.filter((b) => b.batch_id !== pendingThemeBatch.batch_id), result])
      setMessages((prev) => [...prev, {
        role: 'assistant' as const,
        content: 'Content batch created. Your posts are ready for approval.',
      }])
    } catch {
      setError('Failed to create content batch. Please try again.')
    } finally {
      setCreateBatchLoading(false)
    }
  }, [pendingThemeBatch, createBatchLoading, youtubeCredentialRef])

  // Placeholder post stub; replaced by real post when batches are loaded
  const mockPost = { artifact_type: undefined } as unknown as DraftPost
  const artifactPost: DraftPost = batches.flatMap((b) => b.posts)[0] ?? mockPost

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
      testID="dma-conversation-screen"
    >
      <View style={[s.header, { borderBottomColor: colors.textSecondary + '20' }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={{ color: colors.neonCyan, fontSize: 14 }}>← Back</Text>
        </TouchableOpacity>
        <Text
          style={[
            s.title,
            { color: colors.textPrimary, fontFamily: typography.fontFamily.display },
          ]}
        >
          Strategy Workshop
        </Text>
      </View>

      {error ? (
        <View
          style={[s.errorBanner, { backgroundColor: '#ef444418', borderColor: '#ef444455' }]}
        >
          <Text style={{ color: '#ef4444' }}>{error}</Text>
        </View>
      ) : null}

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
            <Text
              style={{ color: colors.textSecondary, textAlign: 'center', marginTop: 40 }}
            >
              Start the strategy workshop — describe your business, audience, and goals.
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
                        backgroundColor: '#667eea22',
                        borderColor: '#667eea55',
                      }
                    : {
                        alignSelf: 'flex-start',
                        backgroundColor: '#18181b',
                        borderColor: colors.textSecondary + '30',
                      },
                ]}
              >
                <Text style={{ color: colors.textPrimary, fontSize: 14 }}>{msg.content}</Text>
              </View>
            ))
          )}
          {sending ? (
            <ActivityIndicator
              color={colors.neonCyan}
              style={{ alignSelf: 'flex-start', marginLeft: 16 }}
            />
          ) : null}
          {messages.length > 0 ? <ArtifactRenderer post={artifactPost} /> : null}
          {pendingThemeBatch && (
            <View
              style={[s.themeCard, { borderColor: colors.neonCyan + '44', backgroundColor: '#0a0a0a' }]}
              testID="generate-content-card"
            >
              <Text style={{ color: colors.neonCyan, fontSize: 12, marginBottom: 4 }}>Theme ready</Text>
              <Text style={{ color: colors.textPrimary, fontWeight: '700', marginBottom: 12 }}>
                {pendingThemeBatch.theme}
              </Text>
              <TouchableOpacity
                style={[s.sendBtn, { backgroundColor: createBatchLoading ? colors.textSecondary + '40' : colors.neonCyan }]}
                onPress={handleGenerateContent}
                disabled={createBatchLoading}
                testID="generate-content-btn"
              >
                {createBatchLoading
                  ? <ActivityIndicator size="small" color="#0a0a0a" />
                  : <Text style={{ color: '#0a0a0a', fontWeight: '700' }}>Generate Content</Text>}
              </TouchableOpacity>
            </View>
          )}
        </ScrollView>

        <View
          style={[
            s.inputBar,
            {
              borderTopColor: colors.textSecondary + '20',
              backgroundColor: colors.black,
            },
          ]}
        >
          <TextInput
            style={[
              s.textInput,
              { color: colors.textPrimary, borderColor: colors.textSecondary + '40' },
            ]}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Type your message…"
            placeholderTextColor={colors.textSecondary}
            multiline
            editable={!sending}
            testID="dma-chat-input"
          />
          <TouchableOpacity
            style={[
              s.sendBtn,
              {
                backgroundColor:
                  sending || !inputText.trim()
                    ? colors.textSecondary + '40'
                    : colors.neonCyan,
              },
            ]}
            onPress={handleSend}
            disabled={sending || !inputText.trim()}
            testID="dma-chat-send"
          >
            <Text style={{ color: '#0a0a0a', fontWeight: '700', fontSize: 13 }}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
      {voiceAvailable && (
        <VoiceFAB
          isListening={voiceListening}
          onPress={voiceToggle}
          testID="voice-fab-dma"
          position="bottom-left"
        />
      )}
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
  title: { flex: 1, fontSize: 18, fontWeight: 'bold' },
  errorBanner: { margin: 12, padding: 12, borderRadius: 8, borderWidth: 1 },
  bubble: { maxWidth: '80%', borderRadius: 12, borderWidth: 1, padding: 12 },
  themeCard: { borderWidth: 1, borderRadius: 12, padding: 16, marginTop: 8 },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
    padding: 12,
    borderTopWidth: 1,
  },
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
})
