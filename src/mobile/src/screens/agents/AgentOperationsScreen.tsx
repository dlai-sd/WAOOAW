/**
 * AgentOperationsScreen (CP-MOULD-1 E5-S1)
 *
 * Single operations hub for a hired agent — 8 collapsible sections.
 * Accepts optional focusSection param from notification deep-links (E6-S1).
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  SafeAreaView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { useHiredAgentById } from '@/hooks/useHiredAgents';
import { useApprovalQueue } from '@/hooks/useApprovalQueue';
import cpApiClient from '@/lib/cpApiClient';
import type { MyAgentsStackScreenProps } from '@/navigation/types';

type Props = MyAgentsStackScreenProps<'AgentOperations'>;

// ─── Section map ─────────────────────────────────────────────────────────────

const SECTIONS = [
  { id: 'activity',   title: "Today's Activity",      icon: '⚡' },
  { id: 'approvals',  title: 'Pending Approvals',      icon: '✋' },
  { id: 'scheduler',  title: 'Schedule Controls',      icon: '🕐' },
  { id: 'health',     title: 'Connection Health',      icon: '🔗' },
  { id: 'goals',      title: 'Goal Configuration',     icon: '🎯' },
  { id: 'spend',      title: 'Trial Usage & Spend',    icon: '💰' },
  { id: 'recent',     title: 'Recent Publications',    icon: '📤' },
  { id: 'history',    title: 'Performance History',    icon: '📈' },
] as const;

type SectionId = typeof SECTIONS[number]['id'];

// ─── Collapsible section card ─────────────────────────────────────────────────

interface SectionCardProps {
  id: SectionId;
  title: string;
  icon: string;
  badge?: number;
  expanded: boolean;
  onToggle: (id: SectionId) => void;
  children: React.ReactNode;
}

const SectionCard = ({
  id, title, icon, badge, expanded, onToggle, children,
}: SectionCardProps) => {
  const { colors, spacing, typography } = useTheme();
  return (
    <View style={[sectionStyles.card, { borderColor: colors.textSecondary + '20' }]}>
      <TouchableOpacity
        style={sectionStyles.header}
        onPress={() => onToggle(id)}
        accessibilityRole="button"
        accessibilityLabel={`${expanded ? 'Collapse' : 'Expand'} ${title}`}
      >
        <Text style={sectionStyles.icon}>{icon}</Text>
        <Text style={[sectionStyles.title, { color: colors.textPrimary,
          fontFamily: typography.fontFamily.bodyBold }]}>
          {title}
        </Text>
        {badge != null && badge > 0 && (
          <View style={[sectionStyles.badge, { backgroundColor: '#f59e0b44' }]}>
            <Text style={[sectionStyles.badgeText, { color: '#f59e0b' }]}>{badge}</Text>
          </View>
        )}
        <Text style={[sectionStyles.chevron, { color: colors.textSecondary }]}>
          {expanded ? '▲' : '▼'}
        </Text>
      </TouchableOpacity>
      {expanded && (
        <View style={[sectionStyles.body, { borderTopColor: colors.textSecondary + '20' }]}>
          {children}
        </View>
      )}
    </View>
  );
};

const sectionStyles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 12,
    overflow: 'hidden',
    backgroundColor: '#18181b',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 10,
  },
  icon: { fontSize: 18 },
  title: { flex: 1, fontSize: 15 },
  badge: {
    borderRadius: 10,
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginRight: 6,
  },
  badgeText: { fontSize: 12, fontWeight: '600' },
  chevron: { fontSize: 12 },
  body: { borderTopWidth: 1, padding: 16 },
});

// ─── Main screen ─────────────────────────────────────────────────────────────

export const AgentOperationsScreen = ({ navigation, route }: Props) => {
  const { hiredAgentId, focusSection } = route.params;
  const { colors, spacing, typography } = useTheme();
  const scrollRef = useRef<ScrollView>(null);
  const sectionRefs = useRef<Record<string, number>>({});

  const { data: agent, isLoading } = useHiredAgentById(hiredAgentId);
  const { deliverables: pendingApprovals, approve, reject } = useApprovalQueue(hiredAgentId);

  // Expanded sections state — focusSection is pre-expanded on mount
  const [expanded, setExpanded] = useState<Record<SectionId, boolean>>(() => {
    const initial = Object.fromEntries(
      SECTIONS.map((s) => [s.id, false])
    ) as Record<SectionId, boolean>;
    if (focusSection && focusSection in initial) {
      initial[focusSection as SectionId] = true;
    }
    return initial;
  });

  const [pauseLoading, setPauseLoading] = useState(false);
  const [resumeLoading, setResumeLoading] = useState(false);

  const toggleSection = useCallback((id: SectionId) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  }, []);

  // Auto-expand and scroll to focusSection on mount
  useEffect(() => {
    if (!focusSection) return;
    const id = focusSection as SectionId;
    setExpanded((prev) => ({ ...prev, [id]: true }));
    // Small delay for layout to complete
    const timer = setTimeout(() => {
      const yOffset = sectionRefs.current[id] ?? 0;
      if (scrollRef.current && typeof (scrollRef.current as any).scrollTo === 'function') {
        (scrollRef.current as any).scrollTo({ y: yOffset, animated: true });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [focusSection]);

  const handlePause = async () => {
    setPauseLoading(true);
    try {
      await cpApiClient.post(`/cp/hired-agents/${hiredAgentId}/pause`);
    } finally {
      setPauseLoading(false);
    }
  };

  const handleResume = async () => {
    setResumeLoading(true);
    try {
      await cpApiClient.post(`/cp/hired-agents/${hiredAgentId}/resume`);
    } finally {
      setResumeLoading(false);
    }
  };

  const agentName = agent?.nickname || agent?.agent_id || hiredAgentId;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }}>
      {/* Header */}
      <View style={{ paddingHorizontal: spacing.screenPadding?.horizontal ?? 16,
        paddingTop: spacing.md, paddingBottom: spacing.sm }}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginBottom: spacing.sm }}>
          <Text style={{ color: colors.neonCyan,
            fontFamily: typography.fontFamily.body, fontSize: 14 }}>← Back</Text>
        </TouchableOpacity>
        <Text style={{ color: colors.textPrimary,
          fontFamily: typography.fontFamily.display, fontSize: 22, fontWeight: 'bold' }}>
          {agentName}
        </Text>
        <Text style={{ color: colors.textSecondary,
          fontFamily: typography.fontFamily.body, fontSize: 13, marginTop: 2 }}>
          Agent Operations Hub
        </Text>
      </View>

      {isLoading ? (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator color={colors.neonCyan} />
        </View>
      ) : (
        <ScrollView
          ref={scrollRef}
          contentContainerStyle={{ padding: spacing.screenPadding?.horizontal ?? 16,
            paddingBottom: 40 }}
        >
          {SECTIONS.map((section) => (
            <View
              key={section.id}
              onLayout={(e) => {
                sectionRefs.current[section.id] = e.nativeEvent.layout.y;
              }}
            >
              <SectionCard
                id={section.id}
                title={section.title}
                icon={section.icon}
                badge={section.id === 'approvals' ? pendingApprovals.length : undefined}
                expanded={expanded[section.id]}
                onToggle={toggleSection}
              >
                {section.id === 'approvals' && (
                  <View>
                    {pendingApprovals.length === 0 ? (
                      <Text style={{ color: colors.textSecondary,
                        fontFamily: typography.fontFamily.body }}>
                        No pending approvals
                      </Text>
                    ) : (
                      pendingApprovals.map((item) => (
                        <View key={item.id} style={styles.approvalItem}>
                          <Text style={{ color: colors.textPrimary, fontSize: 14,
                            fontFamily: typography.fontFamily.body }}>
                            {item.title || item.type}
                          </Text>
                          <View style={{ flexDirection: 'row', gap: 8, marginTop: 8 }}>
                            <TouchableOpacity
                              style={[styles.actionBtn, { backgroundColor: '#10b98122' }]}
                              onPress={() => approve(item.id)}
                              accessibilityLabel="Approve"
                            >
                              <Text style={{ color: '#10b981', fontSize: 13 }}>Approve</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                              style={[styles.actionBtn, { backgroundColor: '#ef444422' }]}
                              onPress={() => reject(item.id)}
                              accessibilityLabel="Reject"
                            >
                              <Text style={{ color: '#ef4444', fontSize: 13 }}>Reject</Text>
                            </TouchableOpacity>
                          </View>
                        </View>
                      ))
                    )}
                  </View>
                )}

                {section.id === 'scheduler' && (
                  <View>
                    <Text style={{ color: colors.textSecondary,
                      fontFamily: typography.fontFamily.body, marginBottom: 12 }}>
                      Manage your agent's execution schedule.
                    </Text>
                    <View style={{ flexDirection: 'row', gap: 12 }}>
                      <TouchableOpacity
                        style={[styles.actionBtn, { backgroundColor: '#f59e0b22' }]}
                        onPress={handlePause}
                        disabled={pauseLoading}
                        accessibilityLabel="Pause agent"
                        testID="pause-button"
                      >
                        {pauseLoading
                          ? <ActivityIndicator size="small" color="#f59e0b" />
                          : <Text style={{ color: '#f59e0b', fontSize: 13 }}>⏸ Pause</Text>}
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.actionBtn, { backgroundColor: '#10b98122' }]}
                        onPress={handleResume}
                        disabled={resumeLoading}
                        accessibilityLabel="Resume agent"
                        testID="resume-button"
                      >
                        {resumeLoading
                          ? <ActivityIndicator size="small" color="#10b981" />
                          : <Text style={{ color: '#10b981', fontSize: 13 }}>▶ Resume</Text>}
                      </TouchableOpacity>
                    </View>
                  </View>
                )}

                {section.id !== 'approvals' && section.id !== 'scheduler' && (
                  <Text style={{ color: colors.textSecondary,
                    fontFamily: typography.fontFamily.body }}>
                    {section.title} data will appear here.
                  </Text>
                )}
              </SectionCard>
            </View>
          ))}
        </ScrollView>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  approvalItem: {
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#27272a',
  },
  actionBtn: {
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 7,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
