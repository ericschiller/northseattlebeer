# Deployment Guide

## Overview

The scraper pushes a complete Nuxt-built static site to a **target repository**, which Vercel deploys automatically on every push.

**Two-Repository Architecture:**
- **Source repo** (this one): scraping code, Nuxt frontend, web templates
- **Target repo**: receives the built site; connected to Vercel for hosting

---

## 1. Vercel Setup

### Create Target Repository

Create a new GitHub repository (e.g., `northseattlefoodtrucks-web`) that will receive the deployed site.

### Connect to Vercel

1. Go to [vercel.com](https://vercel.com) and create a new project
2. Import your target repository
3. Framework preset: **Other** (the site is pre-built static HTML/JS)
4. Leave build command and output directory blank — files are pushed directly
5. Click **Deploy**

Vercel will redeploy automatically every time the scraper pushes new data to the target repo.

---

## 2. GitHub App Authentication

The scraper uses a GitHub App to authenticate pushes to the target repository.

### Create GitHub App

1. Go to https://github.com/settings/apps and click **New GitHub App**
2. Configure:
   - **App name**: `north-seattle-food-trucks-deployer` (or similar)
   - **Homepage URL**: your source repo URL
   - **Repository permissions**: Contents: Read & Write, Metadata: Read
   - **Where can this app be installed**: Only on this account
3. Click **Create GitHub App**
4. On the app settings page, note the **App ID**
5. Scroll to **Private keys** and click **Generate a private key** — download the `.pem` file

### Install App on Target Repository

1. In your GitHub App settings, click **Install App**
2. Select your target repository
3. Click **Install**

### Configure Environment Variables

```bash
# Encode your private key
GITHUB_APP_PRIVATE_KEY_B64=$(base64 -i path/to/your-app.private-key.pem)

# Add to .env
GITHUB_APP_ID=123456
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_APP_PRIVATE_KEY_B64=<base64-encoded-key>
GIT_REPOSITORY_URL=https://github.com/your-username/northseattlefoodtrucks-web.git

# Optional: AI vision analysis
ANTHROPIC_API_KEY=your-anthropic-api-key
```

The installation ID is retrieved automatically via the GitHub API — you do not need to set it manually.

---

## 3. Running Deployment

```bash
# Scrape and deploy
uv run around-the-grounds --deploy

# Deploy to a specific repository
uv run around-the-grounds --deploy --git-repo https://github.com/username/repo.git

# Or via environment variable
export GIT_REPOSITORY_URL="https://github.com/username/repo.git"
uv run around-the-grounds --deploy
```

**What `--deploy` does:**
1. Scrapes all brewery websites for fresh data
2. Generates `data.json` with `truck_events` and `other_events`
3. Copies the Nuxt frontend files to the target repository
4. Authenticates via GitHub App and pushes to the target repo
5. Vercel detects the push and redeploys the site (typically under 1 minute)

---

## 4. Automated Scheduling (Temporal)

Use Temporal workflows to run the scraper on a schedule automatically.

### Local Temporal Server

```bash
# Start worker (runs continuously in a separate terminal)
uv run python -m around_the_grounds.temporal.worker

# Create a schedule (every 30 minutes)
uv run python -m around_the_grounds.temporal.schedule_manager create --schedule-id daily-scrape --interval 30

# Trigger manually
uv run python -m around_the_grounds.temporal.schedule_manager trigger --schedule-id daily-scrape
```

### Temporal Cloud

```bash
export TEMPORAL_ADDRESS="your-namespace.acct.tmprl.cloud:7233"
export TEMPORAL_NAMESPACE="your-namespace"
export TEMPORAL_API_KEY="your-api-key"

uv run python -m around_the_grounds.temporal.worker
uv run python -m around_the_grounds.temporal.starter --deploy --verbose
```

See [SCHEDULES.md](./SCHEDULES.md) for full schedule management documentation.

---

## 5. Configuration Precedence

For `GIT_REPOSITORY_URL`:
1. CLI argument (`--git-repo`)
2. Environment variable (`GIT_REPOSITORY_URL`)
3. Default value in `around_the_grounds/config/settings.py`
