/**
 * ScheduledPostsScreen (MOB-PARITY-2 E6-S1)
 *
 * Full-page list of all scheduled posts for a hired agent.
 * Filter tabs: All / Queued / Published / Failed
 * Uses FlashList, pull-to-refresh.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '@/hooks/useTheme';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { ErrorView } from '@/components/ErrorView';
import { EmptyState } from '@/components/EmptyState';
import { hiredAgentsService } from '@/services/hiredAgents/hiredAgents.service';
import type { ScheduledPost } from '@/types/hiredAgents.types';
import type { MyAgentsStackScreenProps } from '@/navigation/types';

type PostFilter = 'all' | 'queued' | 'published' | 'failed';

const FILTER_TABS: { key: PostFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'queued', label: 'Queued' },
  { key: 'published', label: 'Published' },
];

// ─── PostRow ─────────────────────────────────────────────────────────────────

function PostRow({ post }: { post: ScheduledPost }) {
  const { colors, spacing, typography } = useTheme();

  const chipColor =
    post.status === 'published'
      ? colors.success ?? '#10b981'
      : post.status === 'failed'
      ? colors.error
      : colors.warning ?? '#f59e0b';

  return (
    <View
      testID={`post-row-${post.id}`}
      style={[styles.row, {
        backgroundColor: colors.card,
        borderRadius: spacing.md,
        marginBottom: spacing.sm,
        padding: spacing.md,
      }]}
    >
      <View style={styles.rowHeader}>
        <View style={[styles.chip, { backgroundColor: chipColor + '20', borderColor: chipColor }]}>
          <Text
            testID={`post-status-${post.status}`}
            style={{ color: chipColor, fontSize: 11,
              fontFamily: typography.fontFamily.bodyBold, textTransform: 'capitalize' }}
          >
            {post.status}
          </Text>
        </View>
        {post.target_platform && (
          <Text style={{ color: colors.textSecondary, fontSize: 12,
            fontFamily: typography.fontFamily.body }}>
            {post.target_platform}
          </Text>
        )}
      </View>
      {post.title && (
        <Text style={{ color: colors.textPrimary, fontSize: 14,
          fontFamily: typography.fontFamily.bodyBold, marginTop: 4 }}
          numberOfLines={2}>
          {post.title}
        </Text>
      )}
      {post.content_preview && (
        <Text style={{ color: colors.textSecondary, fontSize: 12,
          fontFamily: typography.fontFamily.body, marginTop: 4 }}
          numberOfLines={2}>
          {post.content_preview}
        </Text>
      )}
    </View>
  );
}

// ─── ScheduledPostsScreen ─────────────────────────────────────────────────────

export function ScheduledPostsScreen({
  route,
  navigation,
}: MyAgentsStackScreenProps<'ScheduledPosts'>) {
  const { hiredAgentId } = route.params;
  const { colors, spacing, typography } = useTheme();
  const [activeFilter, setActiveFilter] = React.useState<PostFilter>('all');

  const { data: posts = [], isLoading, error, isFetching, refetch } = useQuery({
    queryKey: ['scheduledPosts', hiredAgentId],
    queryFn: () => hiredAgentsService.listScheduledPosts(hiredAgentId),
    staleTime: 1000 * 60,
  });

  const filteredPosts = posts.filter(p =>
    activeFilter === 'all' ? true : p.status === activeFilter
  );

  if (isLoading) return <LoadingSpinner testID="scheduled-posts-loading" />;
  if (error) return <ErrorView message="Could not load scheduled posts" onRetry={refetch} />;

  return (
    <SafeAreaView
      testID="scheduled-posts-screen"
      style={[styles.safe, { backgroundColor: colors.black }]}
    >
      {/* Header */}
      <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.lg, paddingBottom: spacing.md }}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginBottom: 8 }}>
          <Text style={{ color: colors.neonCyan, fontSize: 13, fontFamily: typography.fontFamily.body }}>
            ← Back
          </Text>
        </TouchableOpacity>
        <Text style={{ color: colors.textPrimary, fontSize: 22,
          fontFamily: typography.fontFamily.display }}>
          Scheduled Posts
        </Text>
      </View>

      {/* Filter tabs */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: spacing.sm, gap: spacing.sm }}
      >
        {FILTER_TABS.map(tab => (
          <TouchableOpacity
            key={tab.key}
            testID={`filter-${tab.key}`}
            onPress={() => setActiveFilter(tab.key)}
            style={[styles.filterTab, {
              backgroundColor: activeFilter === tab.key ? colors.neonCyan : colors.card,
              borderRadius: 999,
              paddingHorizontal: spacing.md,
              paddingVertical: spacing.xs,
            }]}
          >
            <Text style={{
              color: activeFilter === tab.key ? colors.black : colors.textSecondary,
              fontSize: 13,
              fontFamily: typography.fontFamily.bodyBold,
            }}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* List */}
      <FlashList
        testID="scheduled-posts-list"
        data={filteredPosts}
        renderItem={({ item }) => <PostRow post={item} />}
        estimatedItemSize={80}
        keyExtractor={item => item.id}
        contentContainerStyle={{
          paddingHorizontal: spacing.lg,
          paddingBottom: 40,
        }}
        ListEmptyComponent={
          <EmptyState testID="scheduled-posts-empty" message="No posts match this filter" />
        }
        refreshControl={
          <RefreshControl
            refreshing={isFetching}
            onRefresh={refetch}
            tintColor={colors.neonCyan}
          />
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1 },
  row: {},
  rowHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  chip: { borderWidth: 1, borderRadius: 4, paddingHorizontal: 6, paddingVertical: 2 },
  filterTab: {},
});
