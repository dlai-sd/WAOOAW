# 🚨 Agent Needs Approval

**Agent:** `{agent_id}`  
**Action:** `{action_type}`  
**File:** `{file_path}`  
**Time:** {timestamp}

---

## Quick Actions

Comment on this issue to respond:

- **APPROVED** ✅ - Agent can proceed with this action
- **REJECTED** ❌ - Agent must not perform this action

Your response will be logged to the `human_escalations` table for audit trail.

---

## Context

**Phase:** {current_phase}  
**Priority:** {priority}  
**Reason:** {escalation_reason}

**Previous approvals today:** {approval_count_today}  
**Agent violation history:** {violation_count_24h} violations in last 24 hours

---

## Action Details

```json
{action_json}
```

---

## Vision References

**Triggered by:**
- {trigger_policy_id}: {trigger_description}

**Citations:**
- {citation_1}
- {citation_2}

---

## What Happens Next?

### If you approve (comment "APPROVED"):
1. ✅ Agent proceeds with the action
2. 📝 Decision logged to `agent_decisions` table
3. 📊 Action tracked in context database
4. 🔔 Notification sent to agent

### If you reject (comment "REJECTED"):
1. ❌ Agent is blocked from this action
2. 📝 Rejection logged to `agent_decisions` table
3. 🚫 Vision violation recorded (if applicable)
4. 🔔 Agent notified to find alternative approach

### If no response in 24 hours:
1. ⏱️ Action automatically **REJECTED** (safety first)
2. 📧 Reminder notification sent
3. 📊 Timeout logged for policy review

---

## Additional Information

**Agent Status:** {agent_status}  
**CoE:** {coe_name}  
**Related Actions:** {related_actions_count} similar actions pending

**Database Record ID:** `{escalation_id}`

---

## Debugging

<details>
<summary>View full context (click to expand)</summary>

### Agent Context
```json
{agent_context_json}
```

### Vision Layer Check
- ✅ Immutable Core: {core_check_result}
- ✅ Dynamic Policies: {policy_check_result}
- ❌ Escalation triggered: {escalation_check_result}

### Recent Decisions (Last 10)
{recent_decisions_list}

</details>

---

**Powered by WAOOAW Vision Stack v1.0**  
*Mobile-optimized for GitHub app approval workflow*
