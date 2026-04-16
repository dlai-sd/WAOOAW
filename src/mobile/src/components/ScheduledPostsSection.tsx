/**
 * ScheduledPostsSection (MOB-PARITY-2 E4-S2)
 *
 * Shows queued/published/failed scheduled posts for a hired agent inside
 * the Scheduler Controls section of AgentOperationsScreen.
 */

import React from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useTheme } from '@/hooks/useTheme';
import { hiredAgentsService } from '@/services/hiredAgents/hiredAgents.service';
import type { ScheduledPost } from '@/types/hiredAgents.types';

interface Props {
  hiredAgentId: string;
}

const STATUS_CONFIG: Record<ScheduledPost['status'], { color: string; label: string }> = {
  queued:    { color: '#f59e0b', label: 'Queued' },
  published: { color: '#10b981', label: 'Published' },
  failed:    { color: '#ef4444', label: 'Failed' },
};

export const ScheduledPostsSection = ({ hiredAgentId }: Props) => {
  const { colors, typography } = useTheme();

  const { data: posts = [], isLoading } = useQuery<ScheduledPost[]>({
    queryKey: ['scheduledPosts', hiredAgentId],
    queryFn: () => hiredAgentsService.listScheduledPosts(hiredAgentId),
    staleTime: 1000 * 60 * 1,
    gcTime: 1000 * 60 * 5,
    enabled: !!hiredAgentId,
    retry: 2,
  });

  if (isLoading) {
    return (
      <View style={{ alignItems: 'center', paddingVertical: 12 }}>
        <ActivityIndicator color={colors.neonCyan} size="small" testID="scheduled-posts-loading" />
      </View>
    );
  }

  if (posts.length === 0) {
    return (
      <Text
        testID="scheduled-posts-empty"
        style={{ color: colors.textSecondary, fontFamily: typography.fontFamily.body, fontSize: 13, marginTop: 8 }}
      >
        No scheduled posts yet
      </Text>
    );
  }

  return (
    <View style={{ marginTop: 12, gap: 8 }}>
      {posts.map((post) => {
        const cfg = STATUS_CONFIG[post.status];
        return (
          <View
            key={post.id}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              gap: 10,
              paddingVertical: 8,
              borderBottomWidth: 1,
              borderBottomColor: colors.textSecondary + '20',
            }}
          >
            <View
              testID={`post-status-${post.status}`}
              style={{
                paddingHorizontal: 8,
                paddingVertical: 3,
                borderRadius: 999,
                backgroundColor: cfg.color + '22',
              }}
            >
              <Text style={{ color: cfg.color, fontSize: 11, fontWeight: '600' }}>{cfg.label}</Text>
            </View>
            <Text
              style={{ flex: 1, color: colors.textPrimary, fontSize: 13, fontFamily: typography.fontFamily.body }}
              numberOfLines={1}
            >
              {post.title || post.content_preview || post.id}
            </Text>
            {post.target_platform ? (
              <Text style={{ color: colors.textSecondary, fontSize: 11 }}>{post.target_platform}</Text>
            ) : null}
          </View>
        );
      })}
    </View>
  );
};
