/**
 * TradeHistoryScreen — paginated list of per-day trade performance records (ST-MVP-1 S11).
 *
 * Reads from GET /cp/trading/history/{hiredAgentId} via tradingSetup.service.ts.
 * Each row shows: date, instrument (skill_id), P&L %, win rate, stop-loss count.
 */
import React, { useCallback, useEffect, useState } from 'react'
import {
  ActivityIndicator,
  FlatList,
  SafeAreaView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native'
import { useTheme } from '@/hooks/useTheme'
import { getTradeHistory, type TradeHistoryRow } from '@/services/tradingSetup.service'
import type { MyAgentsStackScreenProps } from '@/navigation/types'

type Props = MyAgentsStackScreenProps<'TradeHistory'>

const PAGE_SIZE = 20

export const TradeHistoryScreen = ({ navigation, route }: Props) => {
  const { hiredAgentId } = route.params
  const { colors } = useTheme()

  const [trades, setTrades] = useState<TradeHistoryRow[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPage = useCallback(
    async (pageNum: number, append = false) => {
      if (pageNum === 1) setLoading(true)
      else setLoadingMore(true)
      try {
        const resp = await getTradeHistory(hiredAgentId, pageNum, PAGE_SIZE)
        setTotal(resp.total)
        setTrades((prev) => (append ? [...prev, ...resp.trades] : resp.trades))
        setPage(pageNum)
      } catch {
        setError('Failed to load trade history. Please try again.')
      } finally {
        setLoading(false)
        setLoadingMore(false)
      }
    },
    [hiredAgentId]
  )

  useEffect(() => {
    fetchPage(1)
  }, [fetchPage])

  const handleLoadMore = () => {
    if (!loadingMore && trades.length < total) {
      fetchPage(page + 1, true)
    }
  }

  const renderRow = ({ item }: { item: TradeHistoryRow }) => {
    const pnlPositive = item.pnl_pct_avg >= 0
    return (
      <View
        style={[s.row, { backgroundColor: colors.card, borderColor: colors.border }]}
        accessibilityLabel={`Trade on ${item.stat_date}, P&L ${item.pnl_pct_avg}%`}
      >
        <View style={s.rowLeft}>
          <Text style={[s.dateText, { color: colors.text }]}>{item.stat_date}</Text>
          <Text style={[s.skillText, { color: colors.textSecondary }]}>{item.skill_id}</Text>
        </View>
        <View style={s.rowRight}>
          <Text
            style={[
              s.pnlText,
              { color: pnlPositive ? '#10b981' : '#ef4444' },
            ]}
          >
            {pnlPositive ? '+' : ''}
            {item.pnl_pct_avg.toFixed(2)}%
          </Text>
          <Text style={[s.metaText, { color: colors.textSecondary }]}>
            Win {(item.win_rate * 100).toFixed(0)}% · {item.trades_count} trades
          </Text>
          {item.stop_loss_count > 0 && (
            <Text style={[s.slText, { color: '#f59e0b' }]}>
              🛑 {item.stop_loss_count} SL
            </Text>
          )}
        </View>
      </View>
    )
  }

  return (
    <SafeAreaView style={[s.root, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[s.header, { borderBottomColor: colors.border }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} accessibilityLabel="Go back">
          <Text style={{ color: colors.neonCyan, fontSize: 16 }}>← Back</Text>
        </TouchableOpacity>
        <Text style={[s.title, { color: colors.text }]}>Trade History</Text>
        <Text style={[s.totalText, { color: colors.textSecondary }]}>{total} records</Text>
      </View>

      {loading ? (
        <ActivityIndicator color={colors.neonCyan} style={{ marginTop: 40 }} />
      ) : error ? (
        <View style={s.errorContainer}>
          <Text style={{ color: '#ef4444', textAlign: 'center' }}>{error}</Text>
          <TouchableOpacity onPress={() => fetchPage(1)} style={{ marginTop: 12 }}>
            <Text style={{ color: colors.neonCyan }}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={trades}
          keyExtractor={(item, idx) => `${item.stat_date}-${idx}`}
          renderItem={renderRow}
          contentContainerStyle={s.list}
          onEndReached={handleLoadMore}
          onEndReachedThreshold={0.3}
          ListEmptyComponent={
            <Text style={[s.emptyText, { color: colors.textSecondary }]}>
              No trade history yet. Trades will appear here once the agent executes orders.
            </Text>
          }
          ListFooterComponent={
            loadingMore ? <ActivityIndicator color={colors.neonCyan} style={{ padding: 16 }} /> : null
          }
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
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
  },
  title: { fontSize: 18, fontWeight: 'bold' },
  totalText: { fontSize: 12 },
  list: { padding: 12, gap: 8 },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
  },
  rowLeft: { flex: 1 },
  rowRight: { alignItems: 'flex-end' },
  dateText: { fontSize: 14, fontWeight: '600' },
  skillText: { fontSize: 11, marginTop: 2 },
  pnlText: { fontSize: 16, fontWeight: '700' },
  metaText: { fontSize: 11, marginTop: 2 },
  slText: { fontSize: 11, marginTop: 2 },
  errorContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  emptyText: { textAlign: 'center', padding: 40, lineHeight: 22 },
})
