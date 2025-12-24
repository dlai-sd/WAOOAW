# 📱 Mobile Monitoring Guide for WowVision Prime

Monitor and control WowVision Prime entirely from GitHub mobile app.

## Quick Start (5 Minutes)

### 1. Install GitHub Mobile App
- iOS: https://apps.apple.com/app/github/id1477376905
- Android: https://play.google.com/store/apps/details?id=com.github.android

### 2. Enable Notifications
```
Settings → Notifications → dlai-sd/waooaw
Enable: Issues, Pull Requests, Actions
```

### 3. Run Your First Test
```
1. Open GitHub app
2. Navigate to dlai-sd/waooaw
3. Tap "Actions" tab
4. Tap "Test 1: Vision Violation Detection"
5. Tap "Run workflow"
6. Watch test execute in real-time
7. Tap "Issues" tab
8. See escalation issue created
9. Tap issue, read details
10. Comment "APPROVE" or "REJECT"
```

## Monitoring Workflows

### Actions Tab

**What You'll See:**
- ✅ Completed workflows (green check)
- 🟡 Running workflows (yellow dot)
- ❌ Failed workflows (red X)
- ⏸️ Queued workflows (gray dash)

**Tap any workflow to:**
- See live logs
- Check step results
- View summary
- Re-run if failed

### Issues Tab

**What You'll See:**
- 🚨 Vision violations (wowvision-escalation label)
- 📊 Status dashboard (wowvision-dashboard label)
- ✅ Approved actions
- ❌ Rejected actions

**Tap any issue to:**
- Read full details
- See decision reasoning
- View vision citations
- Add comment (APPROVE/REJECT)

## Responding to Escalations

### Quick Response
```
1. Get notification: "New issue: Vision Violation"
2. Open notification
3. Read issue details
4. Tap "Add comment"
5. Type: "APPROVE" or "REJECT"
6. Submit
7. Done! WowVision processes on next wake-up
```

### Detailed Response
```
APPROVE - reason here
```
or
```
REJECT - reason here
```

**WowVision Prime will:**
- Process your response within 6 hours
- Close the issue
- Update decision log
- Apply learning for future

## Status Dashboard

**Location:** Issues tab → "WowVision Prime Status Dashboard"

**What It Shows:**
- System health (all components)
- Recent activity (last 24h)
- Pending actions (awaiting your response)
- Statistics (all-time)

**Auto-Updates:** Every 6 hours

**Manual Update:** Comment "STATUS" on dashboard issue

## Quick Actions

Comment on Status Dashboard issue:

| Command | Action |
|---------|--------|
| `STATUS` | Force immediate status update |
| `WAKE` | Trigger wake cycle now |
| `STATS` | Show detailed statistics |
| `TEST` | Run all 3 test workflows |
| `HELP` | Show all commands |

## Running Tests from Mobile

### Test 1: Vision Violation
```
Actions → "Test 1: Vision Violation Detection" → Run workflow
Expected: Creates escalation issue (Python file in Phase 1)
```

### Test 2: Vision Approval  
```
Actions → "Test 2: Vision Approval" → Run workflow
Expected: No escalation (Markdown file allowed)
```

### Test 3: Memory Persistence
```
Actions → "Test 3: Memory Persistence" → Run workflow
Expected: 2 wake cycles, context saved/loaded
```

## Notifications Setup

**Recommended Settings:**
```
Issues: ✅ Enabled (for escalations)
Actions: ✅ Enabled (for workflow results)
Pull Requests: ⏸️ Optional
Discussions: ❌ Disabled
```

**Notification Examples:**
- "🚨 New issue: Vision Violation: test.py"
- "✅ Workflow completed: Test 1"
- "❌ Workflow failed: WowVision Prime"

## Troubleshooting from Mobile

### Workflow Failed
```
1. Tap failed workflow
2. Tap failed job
3. Read error logs
4. If infrastructure issue → Check Status Dashboard
5. If code issue → Will need laptop to fix
6. Can re-run workflow after fix
```

### No Escalation Created
```
1. Check Actions tab → Verify workflow ran
2. Check workflow logs → Look for "issue created"
3. Check Issues tab → Verify no escalation exists
4. This is normal for approved files
```

### Status Dashboard Not Updating
```
1. Comment "STATUS" on dashboard issue
2. Wait 5 minutes
3. Refresh issue
4. If still stale → Comment "WAKE"
```

## Best Practices

✅ **DO:**
- Check notifications daily
- Respond to escalations within 24h
- Review status dashboard weekly
- Run tests after infrastructure changes

❌ **DON'T:**
- Close Status Dashboard issue
- Delete escalation issues without responding
- Ignore failures for more than 24h
- Run multiple tests simultaneously (queue them)

## Summary

**Everything you need on mobile:**
- ✅ Run tests (Actions tab)
- ✅ View escalations (Issues tab)
- ✅ Approve/reject (Comment on issue)
- ✅ Check status (Dashboard issue)
- ✅ Trigger actions (Comment commands)

**No laptop needed!**
