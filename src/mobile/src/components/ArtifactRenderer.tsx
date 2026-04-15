import React from 'react'
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Linking,
  StyleSheet,
} from 'react-native'
import { useTheme } from '@/hooks/useTheme'
import type { DraftPost } from '@/services/marketingReview.service'

interface Props {
  post: DraftPost
}

export const ArtifactRenderer = ({ post }: Props) => {
  const { colors } = useTheme()
  const status = post.artifact_generation_status

  if (status === 'queued' || status === 'running') {
    return (
      <View style={s.row}>
        <ActivityIndicator color={colors.neonCyan} size="small" />
        <Text style={{ color: colors.textSecondary, marginLeft: 8 }}>Generating artifact…</Text>
      </View>
    )
  }

  if (status === 'failed') {
    return (
      <View style={[s.banner, { borderColor: '#ef444455', backgroundColor: '#ef444418' }]}>
        <Text style={{ color: '#ef4444' }}>Artifact generation failed</Text>
      </View>
    )
  }

  const type = post.artifact_type
  const uri = post.artifact_uri
  if (!type || type === 'text' || !uri) return null

  if (type === 'image') {
    return (
      <Image
        source={{ uri }}
        style={s.img}
        resizeMode="cover"
        testID="artifact-image"
        accessibilityLabel="Content image"
      />
    )
  }

  if (type === 'video' || type === 'video_audio') {
    return (
      <TouchableOpacity
        style={[
          s.videoCard,
          { borderColor: colors.textSecondary + '30', backgroundColor: '#18181b' },
        ]}
        onPress={() => Linking.openURL(uri)}
        testID="artifact-video"
        accessibilityLabel="Play video"
      >
        {post.artifact_preview_uri ? (
          <Image
            source={{ uri: post.artifact_preview_uri }}
            style={s.thumb}
            resizeMode="cover"
          />
        ) : null}
        <Text style={{ color: colors.neonCyan, fontWeight: '700', marginTop: 8 }}>
          ▶ Play video
        </Text>
      </TouchableOpacity>
    )
  }

  if (type === 'table') {
    let rows: Record<string, string>[] = []
    let headers: string[] = []
    try {
      const parsed = JSON.parse(uri)
      if (Array.isArray(parsed) && parsed.length > 0) {
        headers = Object.keys(parsed[0])
        rows = parsed
      }
    } catch {
      return (
        <View
          style={[s.banner, { borderColor: '#f59e0b55', backgroundColor: '#f59e0b18' }]}
        >
          <Text style={{ color: '#f59e0b' }}>Table data could not be parsed</Text>
        </View>
      )
    }
    return (
      <View style={[s.table, { borderColor: colors.textSecondary + '30' }]} testID="artifact-table">
        <View style={[s.trow, { backgroundColor: '#27272a' }]}>
          {headers.map((h) => (
            <Text key={h} style={[s.th, { color: colors.textPrimary }]}>
              {h}
            </Text>
          ))}
        </View>
        <FlatList
          data={rows}
          keyExtractor={(_, i) => String(i)}
          scrollEnabled={false}
          renderItem={({ item, index }) => (
            <View
              style={[
                s.trow,
                { backgroundColor: index % 2 === 0 ? '#18181b' : '#1c1c1f' },
              ]}
            >
              {headers.map((h) => (
                <Text key={h} style={[s.td, { color: colors.textSecondary }]}>
                  {String((item as Record<string, string>)[h] ?? '')}
                </Text>
              ))}
            </View>
          )}
        />
      </View>
    )
  }

  return null
}

const s = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', padding: 8 },
  banner: { borderWidth: 1, borderRadius: 8, padding: 10, marginVertical: 4 },
  img: { width: '100%', height: 200, borderRadius: 10, marginVertical: 4 },
  videoCard: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    alignItems: 'center',
    marginVertical: 4,
  },
  thumb: { width: '100%', height: 100, borderRadius: 8 },
  table: { borderWidth: 1, borderRadius: 8, overflow: 'hidden', marginVertical: 4 },
  trow: { flexDirection: 'row' },
  th: { flex: 1, padding: 8, fontSize: 12, fontWeight: '700' },
  td: { flex: 1, padding: 8, fontSize: 12 },
})
