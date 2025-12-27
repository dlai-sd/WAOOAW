# GitHub Webhook Setup Guide

## Overview

This guide explains how to configure GitHub webhooks to send events to your WAOOAW instance, enabling event-driven agent wake-ups.

## Architecture

```
GitHub → Webhook → /webhooks/github → MessageBus → Agents
```

**Flow**:
1. GitHub detects event (push, PR, issue, etc.)
2. Sends POST request to `/webhooks/github` endpoint
3. Webhook handler validates signature (HMAC SHA-256)
4. Transforms GitHub payload → message bus event
5. Publishes to message bus (Redis Streams)
6. Agents subscribe to relevant topics and wake up

## Prerequisites

- GitHub repository access (admin/owner)
- WAOOAW instance running and accessible
- Webhook secret (generate with `openssl rand -hex 32`)

## Setup Steps

### 1. Configure Webhook Secret

Add webhook secret to your environment:

```bash
# .env
GITHUB_WEBHOOK_SECRET=your_secret_here_32_chars_minimum
```

### 2. Start WAOOAW with Webhook Handler

```python
# main.py or app/main.py
from fastapi import FastAPI
from waooaw.webhooks import GitHubWebhookHandler
from waooaw.messaging import MessageBus
import redis

# Initialize message bus
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
message_bus = MessageBus(redis_client)

# Initialize webhook handler
webhook_handler = GitHubWebhookHandler(
    webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET"),
    message_bus=message_bus,
    enabled_events=["push", "pull_request", "issues", "issue_comment"]
)

# Create FastAPI app
app = FastAPI(title="WAOOAW")

# Include webhook router
app.include_router(webhook_handler.create_router())

# Run with: uvicorn main:app --host 0.0.0.0 --port 8000
```

### 3. Expose Endpoint (Development)

#### Option A: ngrok (Recommended for local testing)

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/download

# Start ngrok tunnel
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

#### Option B: GitHub Codespaces (Auto-exposed)

```bash
# Ports are automatically forwarded
# Find your URL: https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}
echo "https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/webhooks/github"
```

#### Option C: Production Deployment

```bash
# Deploy to your server (AWS, GCP, Azure, etc.)
# Example with domain: https://api.waooaw.com/webhooks/github
```

### 4. Configure GitHub Webhook

1. Go to your repository: `https://github.com/dlai-sd/WAOOAW`
2. Navigate to **Settings** → **Webhooks** → **Add webhook**
3. Configure webhook:
   - **Payload URL**: `https://your-domain.com/webhooks/github`
   - **Content type**: `application/json`
   - **Secret**: Your webhook secret (from step 1)
   - **SSL verification**: Enable (recommended)
   - **Events**: Select individual events:
     - ✅ Pushes
     - ✅ Pull requests
     - ✅ Issues
     - ✅ Issue comments
     - ✅ Branch or tag creation
     - ✅ Branch or tag deletion
   - **Active**: ✅ Enabled

4. Click **Add webhook**

### 5. Test Webhook

#### Test with GitHub UI

1. Make a change in your repository (create file, open PR, etc.)
2. Check webhook deliveries:
   - Settings → Webhooks → Recent Deliveries
   - Verify Response: 200 OK
   - Check payload and response

#### Test with curl

```bash
# Generate signature
SECRET="your_webhook_secret"
PAYLOAD='{"ref":"refs/heads/main","repository":{"full_name":"dlai-sd/WAOOAW"},"pusher":{"name":"test"},"commits":[{"id":"abc123","message":"Test","author":{"username":"test"},"added":["test.py"],"modified":[],"removed":[]}]}'

SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/SHA256.* //')

curl -X POST https://your-domain.com/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -H "X-GitHub-Event: push" \
  -d "$PAYLOAD"

# Expected: {"status":"success","event":"push","events_published":2}
```

#### Test with GitHub CLI

```bash
# Install GitHub CLI
brew install gh  # macOS

# Trigger webhook manually
gh api repos/dlai-sd/WAOOAW/dispatches \
  -F event_type=test_webhook
```

### 6. Monitor Webhook Activity

#### Check Webhook Health

```bash
curl https://your-domain.com/webhooks/github/health

# Expected:
# {
#   "status": "healthy",
#   "enabled_events": ["push", "pull_request", "issues", "issue_comment"],
#   "message_bus_connected": true
# }
```

#### Check Message Bus Events

```bash
# Connect to Redis and monitor streams
redis-cli

# Check recent messages in P1 (high priority) stream
XREAD COUNT 10 STREAMS waooaw:messages:p1 0

# Check P2 (normal priority) stream
XREAD COUNT 10 STREAMS waooaw:messages:p2 0
```

#### Check Application Logs

```bash
# Look for webhook events
tail -f logs/waooaw.log | grep "webhook"

# Example log entries:
# INFO: 🔗 GitHubWebhookHandler initialized. Enabled events: ['push', 'pull_request', ...]
# INFO: ✅ Webhook signature validated
# INFO: 🔄 Transforming push event
# INFO: ✅ Published github.file.created to message bus (ID: msg_12345)
```

## Event Types

### Push Events

Triggered when commits are pushed to repository.

**Generates**:
- `github.file.created` (for each added file)
- `github.file.updated` (for each modified file)
- `github.file.deleted` (for each removed file)
- `github.commit.pushed` (for each commit)

### Pull Request Events

Triggered on PR lifecycle: open, update, close, merge.

**Generates**:
- `github.pr.opened` (high priority)
- `github.pr.updated`
- `github.pr.closed`
- `github.pr.merged` (high priority)

### Issues Events

Triggered on issue lifecycle: open, close, comment.

**Generates**:
- `github.issue.opened`
- `github.issue.closed`
- `github.issue.comment`

### Branch Events

Triggered on branch creation/deletion.

**Generates**:
- `github.branch.created`
- `github.branch.deleted`

## Security

### Signature Validation

All webhooks are validated using HMAC SHA-256:

```python
# GitHub computes:
signature = HMAC-SHA256(webhook_secret, request_body)

# Sent in header:
X-Hub-Signature-256: sha256=<signature>

# WAOOAW validates:
if not hmac.compare_digest(computed, received):
    raise HTTPException(status_code=401)
```

### Best Practices

1. **Use HTTPS only** - Never expose webhook endpoint over HTTP
2. **Rotate secrets regularly** - Update webhook secret every 90 days
3. **Monitor failures** - Alert on repeated 401/500 responses
4. **Rate limiting** - Configure rate limits on webhook endpoint
5. **IP allowlisting** - Restrict to GitHub's IP ranges (optional)

## Troubleshooting

### Webhook Returns 401 Unauthorized

**Cause**: Invalid signature or secret mismatch

**Fix**:
1. Verify webhook secret matches: `GITHUB_WEBHOOK_SECRET` in `.env`
2. Check GitHub webhook configuration (Settings → Webhooks)
3. Test signature generation locally (see test curl command)

### Webhook Returns 400 Bad Request

**Cause**: Invalid JSON payload

**Fix**:
1. Check GitHub webhook Recent Deliveries for payload format
2. Verify Content-Type header is `application/json`
3. Check application logs for JSON parsing errors

### Webhook Returns 500 Internal Server Error

**Cause**: Application error (message bus connection, transformation logic)

**Fix**:
1. Check application logs: `tail -f logs/waooaw.log`
2. Verify Redis is running: `redis-cli ping` (should return PONG)
3. Test message bus health: `/webhooks/github/health`

### Events Not Reaching Agents

**Cause**: Message bus subscription issue

**Fix**:
1. Verify message bus has events:
   ```bash
   redis-cli
   XREAD COUNT 10 STREAMS waooaw:messages:p2 0
   ```
2. Check agent subscription topics match published topics
3. Verify agent is subscribed and running

### GitHub Shows "Connection Refused"

**Cause**: Endpoint not accessible

**Fix**:
1. Verify application is running: `curl http://localhost:8000/webhooks/github/health`
2. Check ngrok/tunnel is active: `ngrok status`
3. Verify port forwarding (Codespaces): Ports panel → Public visibility

## Performance

### Expected Latency

- **Webhook receipt**: <100ms
- **Signature validation**: <10ms
- **Transformation**: <50ms
- **Message bus publish**: <100ms
- **Total**: **<300ms p95**

### Throughput

- **Development**: 10 events/sec
- **Production**: 100+ events/sec (with load balancing)

### Load Testing

```bash
# Install Apache Bench
brew install httpd  # macOS

# Generate test payload
SECRET="your_secret"
PAYLOAD='{"ref":"refs/heads/main","commits":[...]}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/.* //')

# Save payload to file
echo "$PAYLOAD" > webhook_payload.json

# Run load test (100 requests, 10 concurrent)
ab -n 100 -c 10 \
   -H "Content-Type: application/json" \
   -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
   -H "X-GitHub-Event: push" \
   -p webhook_payload.json \
   https://your-domain.com/webhooks/github
```

## References

- [GitHub Webhooks Documentation](https://docs.github.com/en/webhooks)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Streams Guide](https://redis.io/docs/data-types/streams/)
- Story 1.3: GitHub Webhook Integration (commit a89c648)

## Support

For issues or questions:
- Check logs: `tail -f logs/waooaw.log`
- Test health: `/webhooks/github/health`
- Open issue: https://github.com/dlai-sd/WAOOAW/issues
