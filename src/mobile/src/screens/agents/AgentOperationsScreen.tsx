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
  TextInput,
} from 'react-native';
import { useTheme } from '@/hooks/useTheme';
import { useHiredAgentById, useDeliverables } from '@/hooks/useHiredAgents';
import { useApprovalQueue } from '@/hooks/useApprovalQueue';
import { useAgentVoiceOverlay } from '@/hooks/useAgentVoiceOverlay';
import { ContentDraftApprovalCard } from '@/components/ContentDraftApprovalCard';
import { ScheduledPostsSection } from '@/components/ScheduledPostsSection';
import { VoiceFAB } from '@/components/voice/VoiceFAB';
import cpApiClient from '@/lib/cpApiClient';
import type { MyAgentsStackScreenProps } from '@/navigation/types';
import { DigitalMarketingBriefStepCard } from '@/components/DigitalMarketingBriefStepCard';
import { DigitalMarketingBriefSummaryCard } from '@/components/DigitalMarketingBriefSummaryCard';

type Props = MyAgentsStackScreenProps<'AgentOperations'>;

type GoalSchemaField = {
  key: string;
  label: string;
  type: 'text' | 'number' | 'boolean' | 'enum' | 'list' | 'object';
  required?: boolean;
  description?: string;
  options?: string[];
  show_if?: { key: string; value: unknown };
};

type AgentSkill = {
  skill_id: string;
  name?: string;
  display_name?: string;
  goal_schema?: { fields?: GoalSchemaField[] };
  goal_config?: Record<string, unknown>;
};

type BriefStepDefinition = {
  key: string;
  title: string;
  description: string;
  prompt: string;
  fieldKeys: string[];
};

const DIGITAL_MARKETING_AGENT_ID = 'AGT-MKT-DMA-001';

const BRIEF_STEP_DEFINITIONS: BriefStepDefinition[] = [
  {
    key: 'context',
    title: 'Map the business context',
    description: 'Give the agent enough context to sound like your business instead of generic marketing copy.',
    prompt: 'What business is this agent speaking for, which market are you in, and what locality should shape the examples, language, and proof points?',
    fieldKeys: ['business_background', 'industry', 'locality'],
  },
  {
    key: 'audience',
    title: 'Define the audience and promise',
    description: 'Clarify who this content is for and what offer should move them to act.',
    prompt: 'Who exactly are you trying to reach, what persona should the agent keep in mind, and what offer or promise should the content keep reinforcing?',
    fieldKeys: ['target_audience', 'persona', 'offer'],
  },
  {
    key: 'channel',
    title: 'Shape the YouTube angle',
    description: 'Translate the business goal into a channel-specific operating brief for YouTube.',
    prompt: 'What outcome should YouTube drive, what does success look like there, and how often should the agent aim to publish?',
    fieldKeys: ['objective', 'channel_intent', 'posting_cadence'],
  },
  {
    key: 'voice',
    title: 'Lock the voice and proof signal',
    description: 'Finish with how the work should sound and what signal tells you the brief is working.',
    prompt: 'What tone should the agent protect in every draft, and which business signals should tell you the content is doing its job?',
    fieldKeys: ['tone', 'success_metrics'],
  },
];

function hasValue(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0;
  if (value && typeof value === 'object') return Object.keys(value as Record<string, unknown>).length > 0;
  return String(value ?? '').trim().length > 0;
}

function isFieldVisible(field: GoalSchemaField, values: Record<string, unknown>): boolean {
  if (!field.show_if) return true;
  return values[field.show_if.key] === field.show_if.value;
}

function isFieldComplete(field: GoalSchemaField, values: Record<string, unknown>): boolean {
  if (!isFieldVisible(field, values)) return true;
  if (!field.required) return true;
  return hasValue(values[field.key]);
}

function buildBriefSteps(fields: GoalSchemaField[]) {
  const usedKeys = new Set<string>();
  const steps = BRIEF_STEP_DEFINITIONS.map((step) => {
    const stepFields = step.fieldKeys
      .map((key) => fields.find((field) => field.key === key))
      .filter((field): field is GoalSchemaField => Boolean(field));

    stepFields.forEach((field) => usedKeys.add(field.key));

    return {
      ...step,
      fields: stepFields,
    };
  }).filter((step) => step.fields.length > 0);

  const extraFields = fields.filter((field) => !usedKeys.has(field.key));
  if (extraFields.length > 0) {
    if (steps.length > 0) {
      steps[steps.length - 1] = {
        ...steps[steps.length - 1],
        fields: [...steps[steps.length - 1].fields, ...extraFields],
      };
    } else {
      steps.push({
        key: 'brief',
        title: 'Capture the brief',
        description: 'Capture the core operating details the agent needs before it can draft.',
        prompt: 'Complete the structured brief so the agent can create specific, credible content instead of guessing.',
        fieldKeys: extraFields.map((field) => field.key),
        fields: extraFields,
      });
    }
  }

  return steps;
}

function getThemeDiscoverySkill(skills: AgentSkill[]): AgentSkill | null {
  return (
    skills.find((skill) => {
      const names = [skill.display_name, skill.name]
        .map((value) => String(value || '').trim().toLowerCase())
        .filter(Boolean);
      return names.some((value) => value === 'theme discovery' || value === 'theme_discovery');
    }) || null
  );
}

function isDigitalMarketingAgent(agentId?: string | null, agentTypeId?: string | null): boolean {
  return (
    String(agentId || '').trim().toUpperCase() === DIGITAL_MARKETING_AGENT_ID ||
    String(agentTypeId || '').trim() === 'marketing.digital_marketing.v1'
  );
}

function normalizeSkillsPayload(data: unknown): AgentSkill[] {
  if (Array.isArray(data)) return data as AgentSkill[];
  if (Array.isArray((data as { skills?: unknown[] } | null)?.skills)) {
    return ((data as { skills: AgentSkill[] }).skills || []).slice();
  }
  if (Array.isArray((data as { items?: unknown[] } | null)?.items)) {
    return ((data as { items: AgentSkill[] }).items || []).slice();
  }
  return [];
}

function getResumeStepIndex(
  steps: Array<{ fields: GoalSchemaField[] }>,
  values: Record<string, unknown>
): number {
  const index = steps.findIndex((step) => step.fields.some((field) => !isFieldComplete(field, values)));
  if (index >= 0) return index;
  return Math.max(steps.length - 1, 0);
}

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
    <View
      style={[sectionStyles.card, { borderColor: colors.textSecondary + '20' }]}
      testID={`agent-ops-section-${id}`}
    >
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
        <View
          style={[sectionStyles.body, { borderTopColor: colors.textSecondary + '20' }]}
          testID={`agent-ops-section-body-${id}`}
        >
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
  const { data: allDeliverables = [] } = useDeliverables(hiredAgentId);

  // Weekly output count — deliverables created since start of current week
  const weeklyCount = React.useMemo(() => {
    const now = new Date();
    const startOfWeek = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay());
    startOfWeek.setHours(0, 0, 0, 0);
    return allDeliverables.filter((d) => {
      if (!d.created_at) return false;
      return new Date(d.created_at) >= startOfWeek;
    }).length;
  }, [allDeliverables]);

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
  const [briefLoading, setBriefLoading] = useState(false);
  const [briefSaving, setBriefSaving] = useState(false);
  const [briefError, setBriefError] = useState<string | null>(null);
  const [briefSuccess, setBriefSuccess] = useState<string | null>(null);
  const [themeDiscoveryFields, setThemeDiscoveryFields] = useState<GoalSchemaField[]>([]);
  const [themeDiscoverySkillId, setThemeDiscoverySkillId] = useState('');
  const [briefValues, setBriefValues] = useState<Record<string, unknown>>({});
  const [currentBriefStepIndex, setCurrentBriefStepIndex] = useState(0);

  const isDigitalMarketing = isDigitalMarketingAgent(agent?.agent_id, agent?.agent_type_id);

  const briefSteps = React.useMemo(
    () => buildBriefSteps(themeDiscoveryFields),
    [themeDiscoveryFields]
  );
  const currentBriefStep = briefSteps[currentBriefStepIndex] || null;
  const visibleBriefFields = React.useMemo(
    () => themeDiscoveryFields.filter((field) => isFieldVisible(field, briefValues)),
    [themeDiscoveryFields, briefValues]
  );
  const missingFieldLabels = React.useMemo(() => {
    if (!currentBriefStep) return [];
    return currentBriefStep.fields
      .filter((field) => !isFieldComplete(field, briefValues))
      .map((field) => field.label);
  }, [currentBriefStep, briefValues]);

  const canContinueBrief = missingFieldLabels.length === 0;

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

  useEffect(() => {
    let cancelled = false;

    const loadThemeDiscovery = async () => {
      if (!isDigitalMarketing) {
        setThemeDiscoveryFields([]);
        setThemeDiscoverySkillId('');
        setBriefValues({});
        setBriefError(null);
        setBriefSuccess(null);
        setCurrentBriefStepIndex(0);
        return;
      }

      setBriefLoading(true);
      setBriefError(null);
      setBriefSuccess(null);
      try {
        const response = await cpApiClient.get(`/cp/hired-agents/${hiredAgentId}/skills`);
        const skills = normalizeSkillsPayload(response.data);
        const skill = getThemeDiscoverySkill(skills);
        if (!skill) {
          if (!cancelled) {
            setThemeDiscoveryFields([]);
            setThemeDiscoverySkillId('');
            setBriefValues({});
            setCurrentBriefStepIndex(0);
            setBriefError('This hired agent does not expose the Theme Discovery skill yet.');
          }
          return;
        }

        const fields = skill.goal_schema?.fields || [];
        const values = skill.goal_config || {};
        if (!cancelled) {
          setThemeDiscoveryFields(fields);
          setThemeDiscoverySkillId(skill.skill_id);
          setBriefValues(values);
          setCurrentBriefStepIndex(getResumeStepIndex(buildBriefSteps(fields), values));
        }
      } catch (error: any) {
        if (!cancelled) {
          setThemeDiscoveryFields([]);
          setThemeDiscoverySkillId('');
          setBriefValues({});
          setCurrentBriefStepIndex(0);
          setBriefError(error?.message || 'Failed to load Theme Discovery brief');
        }
      } finally {
        if (!cancelled) setBriefLoading(false);
      }
    };

    void loadThemeDiscovery();
    return () => {
      cancelled = true;
    };
  }, [hiredAgentId, isDigitalMarketing]);

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

  const handleBriefFieldChange = useCallback((key: string, value: unknown) => {
    setBriefError(null);
    setBriefSuccess(null);
    setBriefValues((current) => ({ ...current, [key]: value }));
  }, []);

  const handleBriefSave = useCallback(async () => {
    if (!themeDiscoverySkillId) return;

    setBriefSaving(true);
    setBriefError(null);
    setBriefSuccess(null);
    try {
      const response = await cpApiClient.patch(
        `/cp/hired-agents/${hiredAgentId}/skills/${themeDiscoverySkillId}/goal-config`,
        { goal_config: briefValues }
      );
      const nextValues = (response.data as { goal_config?: Record<string, unknown> } | null)?.goal_config || briefValues;
      setBriefValues(nextValues);
      setCurrentBriefStepIndex(getResumeStepIndex(briefSteps, nextValues));
      setBriefSuccess('Theme Discovery brief saved. Content Creation will use this structured brief.');
    } catch (error: any) {
      setBriefError(error?.message || 'Failed to save Theme Discovery brief');
    } finally {
      setBriefSaving(false);
    }
  }, [briefSteps, briefValues, hiredAgentId, themeDiscoverySkillId]);

  const agentName = agent?.nickname || agent?.agent_id || hiredAgentId;

  const { isListening: voiceListening, toggle: voiceToggle, isAvailable: voiceAvailable } =
    useAgentVoiceOverlay({
      'go to inbox': () => navigation.navigate('Inbox'),
      'go to analytics': () => navigation.navigate('ContentAnalytics', { hiredAgentId }),
      'go to connections': () => navigation.navigate('PlatformConnections', { hiredAgentId }),
    });

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.black }} testID="mobile-agent-operations-screen">
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
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
          {[
            `${pendingApprovals.length} approvals`,
            'Scheduler controls',
            'Health + spend view',
          ].map((pill) => (
            <View
              key={pill}
              style={{
                paddingHorizontal: 10,
                paddingVertical: 6,
                borderRadius: 999,
                borderWidth: 1,
                borderColor: colors.textSecondary + '25',
                backgroundColor: colors.card,
              }}
            >
              <Text style={{ color: colors.textPrimary, fontSize: 12 }}>{pill}</Text>
            </View>
          ))}
        </View>
        {/* Weekly output tile (E4-S3) */}
        <View
          testID="ops-weekly-output"
          style={{
            marginTop: 12,
            paddingHorizontal: 14,
            paddingVertical: 10,
            borderRadius: 12,
            borderWidth: 1,
            borderColor: colors.neonCyan + '30',
            backgroundColor: colors.card,
            flexDirection: 'row',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <Text style={{ color: colors.neonCyan, fontSize: 20, fontFamily: typography.fontFamily.display, fontWeight: 'bold' }}>
            {weeklyCount}
          </Text>
          <Text style={{ color: colors.textSecondary, fontSize: 12, fontFamily: typography.fontFamily.body }}>
            deliverable{weeklyCount !== 1 ? 's' : ''} this week
          </Text>
        </View>
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
          <View
            style={{
              marginBottom: 14,
              borderRadius: 16,
              borderWidth: 1,
              borderColor: colors.textSecondary + '20',
              backgroundColor: colors.card,
              padding: 16,
            }}
          >
            <Text style={{ color: colors.neonCyan, fontSize: 12, marginBottom: 6 }}>Next best action</Text>
            <Text style={{ color: colors.textPrimary, fontSize: 16, fontFamily: typography.fontFamily.bodyBold, marginBottom: 4 }}>
              {pendingApprovals.length > 0 ? 'Clear pending approvals to keep work moving.' : 'Your agent is clear to run. Tune goals or schedule next.'}
            </Text>
            <Text style={{ color: colors.textSecondary, fontSize: 13, fontFamily: typography.fontFamily.body }}>
              Mobile should help you make the few decisions only you need to make, fast.
            </Text>
          </View>

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
                        <ContentDraftApprovalCard
                          key={item.id}
                          deliverable={item}
                          onApprove={approve}
                          onReject={reject}
                        />
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
                      {agent?.subscription_status === 'active' ? (
                        <TouchableOpacity
                          style={[styles.actionBtn, { backgroundColor: '#f59e0b22' }]}
                          onPress={handlePause}
                          disabled={pauseLoading}
                          accessibilityLabel="Pause agent"
                          testID="ops-pause-btn"
                        >
                          {pauseLoading
                            ? <ActivityIndicator size="small" color="#f59e0b" />
                            : <Text style={{ color: '#f59e0b', fontSize: 13 }}>⏸ Pause</Text>}
                        </TouchableOpacity>
                      ) : (
                        <TouchableOpacity
                          style={[styles.actionBtn, { backgroundColor: '#10b98122' }]}
                          onPress={handleResume}
                          disabled={resumeLoading}
                          accessibilityLabel="Resume agent"
                          testID="ops-resume-btn"
                        >
                          {resumeLoading
                            ? <ActivityIndicator size="small" color="#10b981" />
                            : <Text style={{ color: '#10b981', fontSize: 13 }}>▶ Resume</Text>}
                        </TouchableOpacity>
                      )}
                    </View>
                    <ScheduledPostsSection hiredAgentId={hiredAgentId} />
                  </View>
                )}

                {section.id === 'goals' && isDigitalMarketing && (
                  <View style={{ gap: 12 }}>
                    <View
                      style={{
                        borderRadius: 12,
                        borderWidth: 1,
                        borderColor: colors.textSecondary + '20',
                        backgroundColor: colors.card,
                        padding: 12,
                      }}
                    >
                      <Text style={{ color: colors.neonCyan, fontSize: 12, marginBottom: 4 }}>Theme Discovery</Text>
                      <Text
                        style={{
                          color: colors.textPrimary,
                          fontSize: 15,
                          fontFamily: typography.fontFamily.bodyBold,
                          marginBottom: 4,
                        }}
                      >
                        Keep the brief continuous across CP and mobile.
                      </Text>
                      <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13 }}>
                        This mobile flow resumes the same structured brief the Digital Marketing Agent uses for draft generation and YouTube readiness.
                      </Text>
                    </View>

                    {briefLoading ? (
                      <View style={[styles.infoCard, { borderColor: colors.textSecondary + '20' }]}>
                        <ActivityIndicator color={colors.neonCyan} />
                        <Text style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body }}>
                          Loading Theme Discovery brief...
                        </Text>
                      </View>
                    ) : null}

                    {briefError ? (
                      <View style={[styles.infoCard, { borderColor: '#ef444455', backgroundColor: '#ef444418' }]}>
                        <Text style={{ color: '#ef4444', fontFamily: typography.fontFamily.bodyBold, marginBottom: 4 }}>
                          Theme Discovery unavailable
                        </Text>
                        <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.body }}>{briefError}</Text>
                      </View>
                    ) : null}

                    {!briefLoading && !briefError && currentBriefStep ? (
                      <View style={{ gap: 12 }}>
                        <DigitalMarketingBriefStepCard
                          title={currentBriefStep.title}
                          description={currentBriefStep.description}
                          prompt={currentBriefStep.prompt}
                          fields={currentBriefStep.fields}
                          values={briefValues}
                          stepIndex={currentBriefStepIndex}
                          stepCount={briefSteps.length}
                          canGoBack={currentBriefStepIndex > 0}
                          canContinue={canContinueBrief}
                          isSaving={briefSaving}
                          isLastStep={currentBriefStepIndex === briefSteps.length - 1}
                          missingFieldLabels={missingFieldLabels}
                          onChange={handleBriefFieldChange}
                          onBack={() => setCurrentBriefStepIndex((index) => Math.max(0, index - 1))}
                          onNext={() => setCurrentBriefStepIndex((index) => Math.min(briefSteps.length - 1, index + 1))}
                          onSave={handleBriefSave}
                        />

                        {(briefSuccess || briefError) && !briefLoading ? (
                          <View
                            style={[
                              styles.infoCard,
                              {
                                borderColor: briefError ? '#ef444455' : '#10b98155',
                                backgroundColor: briefError ? '#ef444418' : '#10b98118',
                              },
                            ]}
                          >
                            <Text
                              style={{
                                color: briefError ? '#ef4444' : '#10b981',
                                fontFamily: typography.fontFamily.bodyBold,
                                marginBottom: 4,
                              }}
                            >
                              {briefError ? 'Theme Discovery was not saved' : 'Theme Discovery saved'}
                            </Text>
                            <Text style={{ color: colors.textPrimary, fontFamily: typography.fontFamily.body }}>
                              {briefError || briefSuccess}
                            </Text>
                          </View>
                        ) : null}

                        <DigitalMarketingBriefSummaryCard
                          fields={visibleBriefFields}
                          values={briefValues}
                        />
                        <TouchableOpacity
                          style={[styles.actionBtn, { backgroundColor: colors.neonCyan + '22', marginTop: 12 }]}
                          onPress={() => navigation.navigate('DMAConversation', { hiredAgentId })}
                          testID="chat-with-agent-btn"
                          accessibilityLabel="Chat with Agent"
                        >
                          <Text style={{ color: colors.neonCyan, fontSize: 14, fontWeight: '600' }}>
                            💬 Chat with Agent
                          </Text>
                        </TouchableOpacity>
                      </View>
                    ) : null}
                  </View>
                )}

                {section.id !== 'approvals' && section.id !== 'scheduler' && !(section.id === 'goals' && isDigitalMarketing) && (
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
      {/* Voice FAB */}
      {voiceAvailable && (
        <VoiceFAB
          isListening={voiceListening}
          onPress={voiceToggle}
          testID="voice-fab-agent-ops"
          position="bottom-right"
        />
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  infoCard: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    gap: 8,
  },
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
