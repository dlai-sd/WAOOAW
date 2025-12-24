---
name: WowVision Prime Status Dashboard
about: Auto-updated status dashboard (DO NOT CLOSE)
title: '📊 WowVision Prime Status Dashboard'
labels: ['wowvision-dashboard', 'pinned']
assignees: ''
---

# 📊 WowVision Prime Status Dashboard

**Last Updated:** {{ TIMESTAMP }} (Auto-updated every wake cycle)

## 🟢 System Health

| Component | Status | Last Check |
|-----------|--------|------------|
| PostgreSQL | ✅ Healthy | {{ PG_TIMESTAMP }} |
| Pinecone | ✅ Healthy | {{ PC_TIMESTAMP }} |
| Anthropic | ✅ Healthy | {{ AI_TIMESTAMP }} |
| GitHub Actions | ✅ Operational | {{ GH_TIMESTAMP }} |

## 📈 Activity (Last 24 Hours)

- **Wake Cycles:** {{ WAKE_COUNT }}
- **Tasks Processed:** {{ TASK_COUNT }}
- **Decisions Made:** {{ DECISION_COUNT }}
  - Approved: {{ APPROVE_COUNT }}
  - Rejected: {{ REJECT_COUNT }}
- **Escalations Created:** {{ ESCALATION_COUNT }}
- **LLM Calls:** {{ LLM_COUNT }} (Cache hit: {{ CACHE_HIT }}%)
- **Estimated Cost:** ${{ COST }}

## ⚠️ Pending Actions

{{ PENDING_ACTIONS }}

## 📊 All-Time Statistics

- **Total Decisions:** {{ TOTAL_DECISIONS }}
- **Accuracy:** {{ ACCURACY }}%
- **Average Response Time:** {{ AVG_RESPONSE }}s
- **Uptime:** {{ UPTIME }}%

## 💬 Quick Actions

Comment below with:
- `STATUS` - Force status update now
- `WAKE` - Trigger immediate wake cycle
- `STATS` - Show detailed statistics
- `TEST` - Run all 3 test workflows
- `HELP` - Show available commands

---

*Auto-updated by WowVision Prime • Last wake: #{{ WAKE_NUMBER }}*
