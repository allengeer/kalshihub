# Deployment Guide

This guide covers deploying the Kalshihub application to Google App Engine.

## Prerequisites

1. **Google Cloud Platform Account**
   - Active GCP account with billing enabled
   - Project created for Kalshihub deployment

2. **Required GCP Services**
   - Google App Engine enabled
   - Firebase Admin SDK enabled
   - Cloud Build API enabled

3. **GitHub Secrets Configuration**
   - `GCP_SA_KEY`: Service account JSON key with App Engine deployment permissions
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `CODECOV_TOKEN`: Codecov token for coverage reporting

## Automated Deployment (CI/CD)

The application automatically deploys to Google App Engine when changes are merged to the `main` branch.

### Deployment Workflow

1. **Push to Main**: Any push to the `main` branch triggers the CI/CD pipeline
2. **Run Tests**: All tests must pass (unit, BDD, coverage ≥80%)
3. **Build Artifact**: Application is prepared for deployment
4. **Deploy to GAE**: Automatic deployment with versioning
5. **Verify**: Deployment verification and artifact storage

### Deployment Process

The GitHub Actions workflow:
- Runs all quality checks (flake8, mypy, black, pytest, behave)
- Authenticates to GCP using service account credentials
- Deploys to App Engine with git SHA-based versioning
- Stores deployment artifacts for 30 days
- Promotes the new version automatically

## Manual Deployment

### Prerequisites

Install Google Cloud SDK:
```bash
# macOS
brew install --cask google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash

# Initialize gcloud
gcloud init
```

### Deploy Command

```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Deploy
gcloud app deploy app.yaml --project=YOUR_PROJECT_ID
```

### Deploy Specific Version

```bash
# Deploy without promoting (for testing)
gcloud app deploy app.yaml --no-promote --version=test-v1

# Promote a version to receive traffic
gcloud app services set-traffic default --splits=test-v1=1
```

## Configuration

### Environment Variables

The application requires the following environment variables (configured in [app.yaml](app.yaml)):

#### Required
- `FIREBASE_PROJECT_ID`: Firebase project ID (auto-set from GCP_PROJECT_ID in CI/CD)

#### Optional (with defaults)
- `KALSHI_BASE_URL`: Kalshi API base URL (default: https://api.elections.kalshi.com/trade-api/v2)
- `KALSHI_RATE_LIMIT`: API rate limit in req/sec (default: 20.0)
- `CRAWLER_INTERVAL_MINUTES`: Market crawler interval (default: 5)
- `MARKET_CLOSE_WINDOW_HOURS`: Hours ahead to crawl markets (default: 24)
- `CRAWLER_MAX_RETRIES`: Maximum retries for failed operations (default: 3)
- `CRAWLER_RETRY_DELAY_SECONDS`: Initial retry delay (default: 1)

### Firebase Credentials

Firebase credentials are handled via Google Cloud's default application credentials:
- In GAE, the default App Engine service account is used
- Ensure the service account has Firebase Admin permissions
- No need to manually upload credential files

## Scaling Configuration

The application uses automatic scaling configured in [app.yaml](app.yaml):

```yaml
automatic_scaling:
  target_cpu_utilization: 0.65
  min_instances: 1
  max_instances: 2
```

### Adjust Scaling

Edit [app.yaml](app.yaml) to modify:
- `min_instances`: Minimum number of instances (affects cost)
- `max_instances`: Maximum number of instances
- `target_cpu_utilization`: CPU threshold for scaling

## Monitoring and Logs

### View Logs

```bash
# Real-time logs
gcloud app logs tail --service=default

# Recent logs
gcloud app logs read --service=default --limit=50

# Filter by severity
gcloud app logs read --service=default --level=error
```

### View in Console

1. Go to [GCP Console](https://console.cloud.google.com)
2. Navigate to App Engine → Services
3. Click on service to view metrics and logs

### Health Checks

The application includes health check endpoints (defined in [app.yaml](app.yaml)):
- **Liveness**: `/health` - Checks if app is running
- **Readiness**: `/ready` - Checks if app is ready to serve traffic

## Version Management

### List Versions

```bash
gcloud app versions list
```

### Stop Old Versions

```bash
# Stop a specific version
gcloud app versions stop VERSION_ID

# Delete old versions
gcloud app versions delete VERSION_ID
```

### Traffic Splitting

```bash
# Split traffic between versions
gcloud app services set-traffic default --splits=v1=0.9,v2=0.1

# Migrate traffic gradually
gcloud app services set-traffic default --splits=v2=1 --migrate
```

## Cost Management

### Pricing Factors

- **Instance hours**: F2 instance class (~$0.10/hour per instance)
- **Minimum instances**: 1 instance always running
- **Scaling**: Additional instances during high load
- **Outbound traffic**: Data transfer costs

### Cost Optimization

1. **Reduce min_instances to 0** (adds cold start latency)
   ```yaml
   min_instances: 0
   ```

2. **Use smaller instance class** (F1 for development)
   ```yaml
   instance_class: F1
   ```

3. **Stop unused versions**
   ```bash
   gcloud app versions stop OLD_VERSION
   ```

## Troubleshooting

### Deployment Fails

1. **Check logs**:
   ```bash
   gcloud app logs tail
   ```

2. **Verify service account permissions**:
   - App Engine Admin
   - Cloud Build Service Account
   - Firebase Admin

3. **Check quota limits**:
   - Navigate to IAM & Admin → Quotas in GCP Console

### Application Errors

1. **View error logs**:
   ```bash
   gcloud app logs read --level=error --limit=50
   ```

2. **Check environment variables**:
   - Ensure all required secrets are set in GitHub
   - Verify app.yaml configuration

3. **Test locally**:
   ```bash
   python -m src.service_runner
   ```

### Health Check Failures

If health checks fail:
1. Implement `/health` and `/ready` endpoints in the application
2. Or remove health check configuration from [app.yaml](app.yaml)
3. Check application startup time (adjust `app_start_timeout_sec`)

## Rollback

### Automatic Rollback

```bash
# List versions
gcloud app versions list

# Route traffic to previous version
gcloud app services set-traffic default --splits=PREVIOUS_VERSION=1
```

### Emergency Rollback

```bash
# Immediately switch all traffic to a stable version
gcloud app services set-traffic default --splits=stable-v1=1 --no-migrate
```

## Security

### Service Account Permissions

Required permissions for deployment:
- `roles/appengine.appAdmin`
- `roles/cloudbuild.builds.editor`
- `roles/firebase.admin`
- `roles/iam.serviceAccountUser`

### Secrets Management

- Never commit credentials to git
- Use GitHub Secrets for CI/CD credentials
- Use Google Secret Manager for runtime secrets (future enhancement)

### Network Security

- All endpoints use HTTPS (enforced in [app.yaml](app.yaml))
- Configure Firebase security rules
- Implement authentication for sensitive endpoints

## Support

For deployment issues:
1. Check [GitHub Actions logs](https://github.com/allengeer/kalshihub/actions)
2. Review GCP App Engine logs
3. Create an issue on GitHub
4. Consult [GCP App Engine documentation](https://cloud.google.com/appengine/docs/standard/python3)
