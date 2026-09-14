# Stinker Installation Guide

Complete guide to install and configure the Stinker AI code-review bot on your GitHub repository.

## Overview

Stinker is a **webhook-based** code review bot that uses your own API keys (BYOK). It connects to GitHub repositories via:
- **GitHub Personal Access Token** for API access
- **Webhook** for receiving PR events
- **Your AI provider** (OpenAI, Anthropic, or custom endpoint)
- **Turso or SQLite** for persistent pattern storage

---

## Prerequisites

- Python 3.8+ installed
- GitHub repository with admin access
- One of: OpenAI API key, Anthropic API key, or custom OpenAI-compatible endpoint
- Public URL for webhook delivery (ngrok, Cloudflare Tunnel, or dedicated server)
- Optional: Turso database for cloud persistence (free tier available)

---

## Step 1: Initial Setup

### 1.1 Clone and Install

```bash
cd /path/to/ai-code-reviewer
./setup.sh
```

This creates:
- Python virtual environment
- `.env` file from `.env.example`
- SQLite database (if Turso not configured)

### 1.2 Activate Environment

```bash
source venv/bin/activate
```

---

## Step 2: Configure Credentials

Edit `.env` file:

```bash
nano .env
```

### Required Configuration

#### 2.1 Flask Secret Key

Generate a secure secret:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Update in `.env`:
```bash
SECRET_KEY=<generated-secret-key>
```

#### 2.2 GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens/new
2. Token name: `Stinker Code Review Bot`
3. Expiration: Choose appropriate duration
4. Scopes required:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `write:discussion` (if using team discussions)

5. Click **Generate token**
6. Copy token (starts with `ghp_`)

Update in `.env`:
```bash
GITHUB_TOKEN=ghp_your_actual_token_here
```

#### 2.3 Webhook Secret

Generate a secure webhook secret:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update in `.env`:
```bash
GITHUB_WEBHOOK_SECRET=<generated-webhook-secret>
```

⚠️ **Important**: Save this secret - you'll need it when configuring GitHub webhook.

#### 2.4 AI Provider

Choose ONE provider:

**OpenAI:**
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-key
OPENAI_MODEL=gpt-4
```

**Anthropic:**
```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-actual-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

**Custom OpenAI-Compatible:**
```bash
AI_PROVIDER=custom
CUSTOM_AI_ENDPOINT=https://your-endpoint.com/v1/chat/completions
CUSTOM_AI_API_KEY=your-api-key
CUSTOM_AI_MODEL=your-model-name
```

#### 2.5 Database (Optional: Turso Cloud)

**Default:** Uses local SQLite (`patterns.db`)

**Turso Cloud Setup:**
1. Create account: https://turso.tech
2. Create database: `turso db create stinker`
3. Get URL: `turso db show stinker`
4. Create token: `turso db tokens create stinker`

Update in `.env`:
```bash
TURSO_DATABASE_URL=libsql://your-database.turso.io
TURSO_AUTH_TOKEN=eyJhbGc...
```

---

## Step 3: Expose Application to Internet

Your Flask app must be publicly accessible for GitHub webhooks.

### Option A: ngrok (Development/Testing)

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5000
```

You'll get a URL like: `https://abc123.ngrok.io`

⚠️ **Note**: ngrok free tier generates new URLs on restart.

### Option B: Cloudflare Tunnel (Free, Persistent)

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Create tunnel
cloudflared tunnel create stinker

# Configure tunnel (creates ~/.cloudflared/config.yml)
cloudflared tunnel route dns stinker stinker.yourdomain.com

# Run tunnel
cloudflared tunnel run stinker --url http://localhost:5000
```

### Option C: Production Server

Configure reverse proxy (nginx/Apache) with:
- HTTPS certificate (Let's Encrypt)
- Proxy to `http://localhost:5000`
- Example domain: `stinker.yourcompany.com`

---

## Step 4: Start Application

```bash
source venv/bin/activate
python3 app.py
```

Expected output:
```
 * Running on http://0.0.0.0:5000
📊 Using Turso database: libsql://...turso.io
✅ Database initialized successfully
```

Visit dashboard: `http://localhost:5000` (or your public URL)

---

## Step 5: Configure GitHub Webhook

### 5.1 Navigate to Repository Settings

1. Go to your repository: `https://github.com/owner/repo`
2. Click **Settings** tab
3. Click **Webhooks** in left sidebar
4. Click **Add webhook**

### 5.2 Configure Webhook

**Payload URL:**
```
https://your-public-url.com/webhook
```
Example: `https://abc123.ngrok.io/webhook`

**Content type:**
- Select: `application/json`

**Secret:**
- Paste the `GITHUB_WEBHOOK_SECRET` from your `.env` file

**Which events would you like to trigger this webhook?**
- Select: **Let me select individual events**
- Check only: ✅ **Pull requests**

**Active:**
- ✅ Ensure this is checked

Click **Add webhook**

### 5.3 Verify Webhook

GitHub will immediately send a `ping` event.

Check webhook page:
- ✅ Green checkmark = Success
- ❌ Red X = Check logs and troubleshoot

View delivery details to see request/response.

---

## Step 6: Test Installation

### 6.1 Create Test Pull Request

1. Create a new branch in your repository
2. Make a small code change
3. Open a pull request

### 6.2 Verify Bot Response

The bot should:
1. Receive webhook event (check Flask logs)
2. Analyze PR diff
3. Learn repository patterns (first PR)
4. Post review comment with suggestions

**Flask logs should show:**
```
📝 Processing PR #123 from owner/repo
🔍 Analyzing 5 changed files
🤖 Generating AI review...
✅ Posted review comment
```

### 6.3 Dashboard Verification

Visit `http://localhost:5000` (or public URL):
- **Home**: See recent review listed
- **Config**: Verify all settings green

---

## Troubleshooting

### Webhook Not Receiving Events

**Check:**
1. Public URL is accessible: `curl https://your-url.com/webhook`
2. Webhook secret matches `.env` exactly
3. Flask app is running
4. Firewall allows incoming connections

**View GitHub webhook deliveries:**
- Repository → Settings → Webhooks → Edit → Recent Deliveries

### Authentication Errors

**GitHub Token Issues:**
```bash
# Test token manually
curl -H "Authorization: token ghp_your_token" https://api.github.com/user
```

Should return your GitHub user info.

**Verify token has `repo` scope.**

### AI Provider Errors

**OpenAI:**
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Anthropic:**
```bash
# Test API key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

### Database Connection Issues

**SQLite:**
- Check `patterns.db` file exists and is writable
- Permissions: `chmod 644 patterns.db`

**Turso:**
- Verify URL starts with `libsql://` (not `https://`)
- Test token: `turso db show stinker --token`
- Check network connectivity to `*.turso.io`

### Pattern Learning Not Working

**First PR will have minimal context.**

Bot learns from:
1. Existing repository files (up to 100 files)
2. Previous reviews
3. Accumulated patterns over time

**Force relearn:**
```bash
# Via dashboard: http://localhost:5000/repos/owner/repo/analyze
# Or API:
curl -X POST http://localhost:5000/api/repos/owner/repo/analyze
```

---

## Production Deployment

### Systemd Service (Linux)

Create `/etc/systemd/system/stinker.service`:

```ini
[Unit]
Description=Stinker AI Code Review Bot
After=network.target

[Service]
Type=simple
User=nonbios
WorkingDirectory=/home/nonbios/ai-code-reviewer
Environment="PATH=/home/nonbios/ai-code-reviewer/venv/bin"
ExecStart=/home/nonbios/ai-code-reviewer/venv/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable stinker
sudo systemctl start stinker
sudo systemctl status stinker
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name stinker.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Add SSL:
```bash
sudo certbot --nginx -d stinker.yourdomain.com
```

---

## Security Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Rotate tokens regularly** (GitHub tokens, API keys)
3. **Use strong webhook secret** (32+ characters)
4. **Enable HTTPS** for production webhook URL
5. **Restrict GitHub token** to specific repositories if possible
6. **Monitor API usage** and set rate limits
7. **Review logs regularly** for suspicious activity
8. **Keep dependencies updated**: `pip install --upgrade -r requirements.txt`

---

## Uninstalling

### Remove from Repository

1. Go to: Repository → Settings → Webhooks
2. Click webhook → **Delete webhook**

### Remove Application

```bash
# Stop service (if using systemd)
sudo systemctl stop stinker
sudo systemctl disable stinker

# Remove files
cd /home/nonbios
rm -rf ai-code-reviewer

# Revoke GitHub token
# Visit: https://github.com/settings/tokens
```

---

## Support

- **Issues**: https://github.com/yourusername/ai-code-reviewer/issues
- **Documentation**: https://github.com/yourusername/ai-code-reviewer
- **Logs**: Check Flask output or `/var/log/stinker.log` (if configured)

---

## Next Steps

After successful installation:

1. **Configure per-repo settings** via dashboard
2. **Review initial patterns** learned from codebase
3. **Adjust AI models** based on cost/quality tradeoff
4. **Monitor review quality** and provide feedback
5. **Scale to multiple repositories** by adding more webhooks

Enjoy automated, context-aware code reviews! 🚀
