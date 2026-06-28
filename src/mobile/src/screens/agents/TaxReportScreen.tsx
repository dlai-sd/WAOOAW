/**
 * TaxReportScreen — monthly/quarterly P&L tax report with CSV export (ST-MVP-1 S12).
 *
 * Reads from GET /cp/trading/tax-report/{hiredAgentId} via tradingSetup.service.ts.
 * Provides a "Share / Export CSV" button for Indian crypto income tax filing.
 */
import React, { useCallback, useEffect, useState } from 'react'
import {
  ActivityIndicator,
  FlatList,
  SafeAreaView,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native'
import { useTheme } from '@/hooks/useTheme'
import { getTaxReport, type TaxReportResponse } from '@/services/tradingSetup.service'
import type { MyAgentsStackScreenProps } from '@/navigation/types'

type Props = MyAgentsStackScreenProps<'TaxReport'>

const CURRENT_YEAR = new Date().getFullYear()
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4'] as const

export const TaxReportScreen = ({ navigation, route }: Props) => {
  const { hiredAgentId } = route.params
  const { colors } = useTheme()

  const [report, setReport] = useState<TaxReportResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  // Filter state
  const [year] = useState(CURRENT_YEAR)
  const [period, setPeriod] = useState<'monthly' | 'quarterly'>('monthly')
  const [month, setMonth] = useState(new Date().getMonth() + 1)
  const [quarter, setQuarter] = useState<'Q1' | 'Q2' | 'Q3' | 'Q4'>('Q2')

  const fetchReport = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await getTaxReport(
        hiredAgentId,
        year,
        period,
        period === 'monthly' ? month : undefined,
        period === 'quarterly' ? quarter : undefined
      )
      setReport(resp)
    } catch {
      setError('Failed to load tax report. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [hiredAgentId, year, period, month, quarter])

  useEffect(() => {
    fetchReport()
  }, [fetchReport])

  const handleExport = async () => {
    if (!report) return
    setExporting(true)
    try {
      const csv = ['date,skill_id,trades,pnl_pct,stop_losses']
        .concat(
          report.trades.map(
            (t) =>
              `${t.date},${t.skill_id},${t.trades_count},${t.pnl_pct},${t.stop_loss_count}`
          )
        )
        .join('\n')
      await Share.share({
        message: csv,
        title: `Trade Report ${report.year} — ${period === 'monthly' ? MONTHS[month - 1] : quarter}`,
      })
    } catch {
      // Share cancelled or failed — no-op
    } finally {
      setExporting(false)
    }
  }

  return (
    <SafeAreaView style={[s.root, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={[s.header, { borderBottomColor: colors.border }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} accessibilityLabel="Go back" testID="tax-report-back">
          <Text style={{ color: colors.neonCyan, fontSize: 16 }}>← Back</Text>
        </TouchableOpacity>
        <Text style={[s.title, { color: colors.textPrimary }]}>P&L Tax Report</Text>
        <TouchableOpacity
          onPress={handleExport}
          disabled={!report || exporting}
          accessibilityLabel="Export CSV"
          testID="export-csv-btn"
        >
          {exporting ? (
            <ActivityIndicator color={colors.neonCyan} size="small" />
          ) : (
            <Text style={{ color: colors.neonCyan, fontSize: 14 }}>Export CSV</Text>
          )}
        </TouchableOpacity>
      </View>

      <ScrollView>
        {/* Period selector */}
        <View style={[s.filterSection, { borderBottomColor: colors.border }]}>
          <View style={s.periodRow}>
            {(['monthly', 'quarterly'] as const).map((p) => (
              <TouchableOpacity
                key={p}
                style={[
                  s.periodBtn,
                  {
                    backgroundColor: period === p ? colors.neonCyan + '22' : 'transparent',
                    borderColor: period === p ? colors.neonCyan : colors.border,
                  },
                ]}
                onPress={() => setPeriod(p)}
                testID={`period-${p}`}
              >
                <Text
                  style={{
                    color: period === p ? colors.neonCyan : colors.textSecondary,
                    fontWeight: '600',
                    fontSize: 13,
                    textTransform: 'capitalize',
                  }}
                >
                  {p}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {period === 'monthly' ? (
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.monthRow}>
              {MONTHS.map((m, idx) => (
                <TouchableOpacity
                  key={m}
                  style={[
                    s.chipBtn,
                    {
                      backgroundColor:
                        month === idx + 1 ? colors.neonCyan + '22' : 'transparent',
                      borderColor: month === idx + 1 ? colors.neonCyan : colors.border,
                    },
                  ]}
                  onPress={() => setMonth(idx + 1)}
                >
                  <Text
                    style={{
                      color: month === idx + 1 ? colors.neonCyan : colors.textSecondary,
                      fontSize: 12,
                    }}
                  >
                    {m}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          ) : (
            <View style={s.quarterRow}>
              {QUARTERS.map((q) => (
                <TouchableOpacity
                  key={q}
                  style={[
                    s.chipBtn,
                    {
                      backgroundColor:
                        quarter === q ? colors.neonCyan + '22' : 'transparent',
                      borderColor: quarter === q ? colors.neonCyan : colors.border,
                    },
                  ]}
                  onPress={() => setQuarter(q)}
                >
                  <Text
                    style={{
                      color: quarter === q ? colors.neonCyan : colors.textSecondary,
                      fontSize: 12,
                    }}
                  >
                    {q}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>

        {loading ? (
          <ActivityIndicator color={colors.neonCyan} style={{ marginTop: 40 }} testID="tax-report-loading" />
        ) : error ? (
          <View style={s.errorContainer} testID="tax-report-error">
            <Text style={{ color: '#ef4444', textAlign: 'center' }}>{error}</Text>
            <TouchableOpacity onPress={fetchReport} style={{ marginTop: 12 }}>
              <Text style={{ color: colors.neonCyan }}>Retry</Text>
            </TouchableOpacity>
          </View>
        ) : report ? (
          <>
            {/* Summary cards */}
            <View style={s.summaryRow} testID="tax-report-summary">
              <View style={[s.summaryCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text style={[s.summaryValue, { color: colors.textPrimary }]}>{report.total_trades}</Text>
                <Text style={[s.summaryLabel, { color: colors.textSecondary }]}>Total Trades</Text>
              </View>
              <View style={[s.summaryCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text
                  style={[
                    s.summaryValue,
                    { color: report.total_pnl_pct >= 0 ? '#10b981' : '#ef4444' },
                  ]}
                >
                  {report.total_pnl_pct >= 0 ? '+' : ''}
                  {report.total_pnl_pct.toFixed(2)}%
                </Text>
                <Text style={[s.summaryLabel, { color: colors.textSecondary }]}>Total P&L</Text>
              </View>
              <View style={[s.summaryCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text style={[s.summaryValue, { color: '#10b981' }]}>{report.profitable_trades}</Text>
                <Text style={[s.summaryLabel, { color: colors.textSecondary }]}>Profitable</Text>
              </View>
              <View style={[s.summaryCard, { backgroundColor: colors.card, borderColor: colors.border }]}>
                <Text style={[s.summaryValue, { color: '#ef4444' }]}>{report.loss_trades}</Text>
                <Text style={[s.summaryLabel, { color: colors.textSecondary }]}>Loss Days</Text>
              </View>
            </View>

            {/* Per-day rows */}
            {report.trades.length === 0 ? (
              <Text style={[s.emptyText, { color: colors.textSecondary }]} testID="tax-report-empty">
                No trades for this period.
              </Text>
            ) : (
              report.trades.map((t, idx) => (
                <View
                  key={`${t.date}-${idx}`}
                  style={[s.tradeRow, { backgroundColor: colors.card, borderColor: colors.border }]}
                  accessibilityLabel={`Trade on ${t.date}, P&L ${t.pnl_pct}%`}
                >
                  <Text style={[s.tradeDateText, { color: colors.textPrimary }]}>{t.date}</Text>
                  <Text
                    style={[
                      s.tradePnlText,
                      { color: t.pnl_pct >= 0 ? '#10b981' : '#ef4444' },
                    ]}
                  >
                    {t.pnl_pct >= 0 ? '+' : ''}
                    {t.pnl_pct.toFixed(2)}%
                  </Text>
                  <Text style={[s.tradeMetaText, { color: colors.textSecondary }]}>
                    {t.trades_count} trades · {(t.win_rate * 100).toFixed(0)}% win
                    {t.stop_loss_count > 0 ? ` · 🛑 ${t.stop_loss_count} SL` : ''}
                  </Text>
                </View>
              ))
            )}
          </>
        ) : null}
      </ScrollView>
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
  filterSection: { padding: 12, borderBottomWidth: 1, gap: 8 },
  periodRow: { flexDirection: 'row', gap: 8 },
  periodBtn: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
  },
  monthRow: { marginTop: 8 },
  quarterRow: { flexDirection: 'row', gap: 8, marginTop: 8 },
  chipBtn: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 6,
    borderWidth: 1,
    marginRight: 6,
  },
  summaryRow: { flexDirection: 'row', padding: 12, gap: 8 },
  summaryCard: {
    flex: 1,
    borderRadius: 10,
    borderWidth: 1,
    padding: 10,
    alignItems: 'center',
  },
  summaryValue: { fontSize: 16, fontWeight: '700' },
  summaryLabel: { fontSize: 10, marginTop: 2 },
  tradeRow: {
    marginHorizontal: 12,
    marginBottom: 6,
    borderRadius: 10,
    borderWidth: 1,
    padding: 12,
  },
  tradeDateText: { fontSize: 13, fontWeight: '600' },
  tradePnlText: { fontSize: 15, fontWeight: '700', marginTop: 2 },
  tradeMetaText: { fontSize: 11, marginTop: 2 },
  errorContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  emptyText: { textAlign: 'center', padding: 40 },
})
