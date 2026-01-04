# WAOOAW Production Environment

**Environment**: GCP Cloud Run + Load Balancer  
**Purpose**: Production services for live customers

## Services

### Platform Portal
- **URL**: https://pp.waooaw.com
- **Backend**: Cloud Run (multi-region)
- **Load Balancer**: Yes (with SSL, CDN)
- **OAuth**: Enabled
- **Monitoring**: Stackdriver, uptime checks

### Backend API
- **URL**: https://api.waooaw.com
- **Backend**: Cloud Run (multi-region)
- **Load Balancer**: Yes (with SSL)
- **Rate Limiting**: Yes
- **Monitoring**: Stackdriver, uptime checks

### Customer Portal
- **URL**: https://www.waooaw.com
- **Backend**: Cloud Run (multi-region)
- **Load Balancer**: Yes (with SSL, CDN)
- **CDN**: Enabled

### Additional Portals
- **DataOps Portal**: https://dp.waooaw.com
- **YK Portal**: https://yk.waooaw.com

## Deployment

**Method**: GitHub Actions + Manual approval

**Workflow**:
1. Code merged to `main`
2. Runs tests and builds
3. Manual approval required
4. Deploys to production
5. Runs smoke tests
6. Sends notification

## OAuth Configuration

**Google OAuth Client ID**: 270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com

**Authorized Redirect URIs**:
- https://api.waooaw.com/auth/callback
- https://pp.waooaw.com/auth/callback
- https://www.waooaw.com/auth/callback

## Secrets Management

Secrets stored in Google Secret Manager:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `JWT_SECRET`
- `DATABASE_URL`
- `REDIS_URL`

Mounted to Cloud Run services as environment variables.

## Monitoring

### Uptime Checks
- Platform Portal: https://pp.waooaw.com/health
- Backend API: https://api.waooaw.com/health
- Customer Portal: https://www.waooaw.com/health

### Alerts
- Service downtime > 5 minutes
- Error rate > 5%
- Response time > 2s (p95)

### Logs
```bash
gcloud logging read 'resource.type=cloud_run_revision AND severity>=ERROR' \
  --limit=100 \
  --project=waooaw-oauth
```

## Rollback

```bash
# List revisions
gcloud run revisions list --service=waooaw-platform-portal-prod

# Rollback to specific revision
gcloud run services update-traffic waooaw-platform-portal-prod \
  --to-revisions=REVISION_NAME=100
```

## Disaster Recovery

- **Database**: Daily backups, point-in-time recovery
- **Redis**: Persistence enabled, snapshots every 15 minutes
- **Code**: GitHub repository, all changes tracked
- **Configs**: Stored in git, version controlled

## Performance Targets

- **Uptime**: 99.9%
- **Response Time**: < 500ms (p95)
- **Cold Start**: < 5s
- **OAuth Flow**: < 3s end-to-end
