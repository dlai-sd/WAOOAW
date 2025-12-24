# WAOOAW GitHub Actions Workflows

This directory contains automated workflows for continuous platform development.

## Workflows

### 1. Continuous Development (`continuous-development.yml`)

**Purpose**: Maintains 24/7 development momentum with automated progress tracking and error recovery.

**Triggers**:
- **Schedule**: Every 1 hour automatically for rapid development
- **Manual**: Via workflow_dispatch with custom parameters
- **Push**: On commits to documentation, backend, or frontend

**Features**:
- ✅ Context preservation validation
- ✅ Automatic progress tracking
- ✅ Error recovery with logging
- ✅ Health checks for stale work
- ✅ Automated checklist generation
- ✅ Failure notifications via GitHub Issues

**Jobs**:
1. **context-check**: Validates context preservation infrastructure exists
2. **validation**: Checks documentation and code integrity
3. **auto-progress**: Executes next development task automatically
4. **health-check**: Monitors repository health and work freshness
5. **error-recovery**: Handles failures with logging and issue creation
6. **summary**: Generates comprehensive workflow report

## How It Works

### Context-Driven Development

The workflow is designed around the context preservation architecture:

```
Wake Up → Check Context → Validate Work → Execute Next Task → Report Progress → Sleep
```

**Phase Detection**:
- Vision Phase: Documentation only exists
- Planning Phase: Implementation roadmap created
- Foundation Phase: Context infrastructure being built
- CoE Phase: Individual CoEs being implemented
- Production Phase: Full platform operational

### Automatic Task Execution

Based on detected phase, the workflow automatically:

**Foundation Setup**:
- Creates database setup checklists
- Generates API implementation tasks
- Sets up infrastructure requirements

**CoE Implementation**:
- Creates CoE development order
- Generates integration plans
- Tracks parallel development

**Error Recovery**:
- Logs failures to `logs/` directory
- Creates GitHub issues for manual review
- Preserves context for recovery

### Manual Triggers

Run workflow manually with custom parameters:

```bash
# Via GitHub UI: Actions → Continuous Platform Development → Run workflow

# Or via gh CLI:
gh workflow run continuous-development.yml \
  -f task=foundation-setup \
  -f phase=foundation
```

## Monitoring

### View Workflow Status

1. Go to repository **Actions** tab
2. Select **Continuous Platform Development**
3. View recent runs and summaries

### Check Progress

Automated progress is tracked in:
- `progress/` directory (checklists, roadmaps)
- `logs/` directory (failure logs)
- GitHub Issues (for errors requiring attention)

### Workflow Summary

Each run generates a summary with:
- Context state and next task
- Validation results
- Health check status
- Required manual actions

## Configuration

### Environment Variables

Located in `continuous-development.yml`:
- `PYTHON_VERSION`: Python version (default: 3.11)
- `NODE_VERSION`: Node.js version (default: 18)

### Schedule Frequency

Current: Every 1 hour (`0 * * * *`)

To adjust, edit cron expression in workflow file:
```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
  # - cron: '0 */3 * * *'  # Every 3 hours
  # - cron: '0 * * * *'    # Every hour
```

## Error Handling

### Automatic Recovery

Workflow includes built-in error recovery:
- Failures are logged automatically
- GitHub Issues created for manual review
- Context state preserved for recovery
- Retry logic for transient failures (push conflicts)

### Manual Intervention

If workflow fails repeatedly:
1. Check created GitHub Issues with label `workflow-failure`
2. Review logs in `logs/` directory
3. Fix identified issues
4. Re-run workflow manually

## Integration with Context Preservation

This workflow implements the wake-up protocol from `docs/CONTEXT_PRESERVATION_ARCHITECTURE.md`:

```
1. Identity Retrieval → Check which phase/task
2. Context Load → Validate existing work
3. Work Execution → Execute next task
4. Context Save → Commit progress
5. Handoff → Report status
```

## Best Practices

### For Developers

1. **Review Progress**: Check `progress/` directory regularly
2. **Follow Checklists**: Use generated checklists for implementation
3. **Commit Regularly**: Every 5-6 hours as per workflow cadence
4. **Document Context**: Maintain context preservation in all work

### For Platform Continuity

1. **Monitor Health**: Check workflow runs for stale work warnings
2. **Address Failures**: Review and resolve workflow failures promptly
3. **Update Roadmap**: Keep PLAN_B document current with progress
4. **Maintain Context**: Never delete context preservation infrastructure

## Workflow Confidence Level

**Confidence: 8/10** for continuous development

**Strengths**:
- ✅ Automatic progress tracking
- ✅ Error recovery and logging
- ✅ Health monitoring
- ✅ Context validation
- ✅ 24/7 operation capability

**Limitations**:
- ⚠️  Requires manual intervention for complex tasks
- ⚠️  Cannot make code decisions autonomously
- ⚠️  Generates checklists/roadmaps, not implementations
- ⚠️  Needs human review for strategic decisions

**Mitigation**:
- Workflow focuses on continuity, not autonomy
- Generates actionable checklists for human implementation
- Maintains momentum through regular health checks
- Escalates to humans via GitHub Issues when needed

## Support

For workflow issues:
1. Check workflow run logs in GitHub Actions
2. Review `logs/` directory for failure details
3. Check GitHub Issues with `workflow-failure` label
4. Refer to `docs/PLAN_B_ACTION_WORKFLOW_IMPLEMENTATION.md` for context

---

**Last Updated**: 2025-12-23  
**Version**: 1.0  
**Status**: ✅ Production Ready
