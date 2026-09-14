# AI Code Review Bot

A configurable, BYOK (Bring Your Own Key) AI-powered code review bot that analyzes pull request diffs and suggests simplifications aligned with each repository's existing patterns and conventions.

## Features

- 🤖 **Multi-Provider AI Support**: Works with OpenAI, Anthropic, or any OpenAI-compatible API
- 🔐 **BYOK (Bring Your Own Key)**: Use your own API keys for complete control
- 📊 **Pattern Learning**: Automatically learns and adapts to your codebase conventions
- 🔄 **GitHub Webhooks**: Automatic PR review on pull request events
- 🎨 **Dashboard**: Web interface for manual reviews and repository analysis
- 💾 **Persistent Storage**: SQLite database for learned patterns and review history
- ⚙️ **Fully Configurable**: Per-repository settings and review customization

## Architecture

```
┌─────────────┐
│  GitHub PR  │
└──────┬──────┘
       │ Webhook
       ▼
┌─────────────────────────────────────┐
│        Flask Application            │
│  ┌───────────────────────────────┐  │
│  │   Webhook Handler             │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │   GitHub Client               │  │
│  │   - Fetch PR diff             │  │
│  │   - Fetch repository files    │  │
│  │   - Post review comments      │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │   Pattern Analyzer            │  │
│  │   - Learn codebase patterns   │  │
│  │   - Extract conventions       │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │   Diff Parser                 │  │
│  │   - Parse unified diffs       │  │
│  │   - Extract changes           │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │   AI Engine                   │  │
│  │   - Build prompts             │  │
│  │   - Call AI provider          │  │
│  │   - Parse suggestions         │  │
│  └───────────┬───────────────────┘  │
│              │                       │
│  ┌───────────▼───────────────────┐  │
│  │   Database (SQLite)           │  │
│  │   - Learned patterns          │  │
│  │   - Review history            │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip3
- GitHub account with repository access
- API key for one of:
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Custom OpenAI-compatible endpoint

### Installation

**Quick Start:**
```bash
./setup.sh
nano .env  # Configure credentials
source venv/bin/activate
python3 app.py
```

**📖 For complete installation instructions, webhook setup, and troubleshooting:**
See **[INSTALL.md](INSTALL.md)** for the detailed step-by-step guide.

**Key Requirements:**
- GitHub Personal Access Token with `repo` scope
- Webhook secret for signature verification
- AI provider API key (OpenAI/Anthropic/Custom)
- Public URL for webhook delivery (ngrok/cloudflare tunnel/server)
- Optional: Turso database for cloud persistence

The dashboard will be available at `http://localhost:5000`


## Configuration

### Environment Variables

**Flask Settings:**
```bash
FLASK_SECRET_KEY=your-random-secret-key
FLASK_DEBUG=false
```

**GitHub Integration:**
```bash
GITHUB_TOKEN=ghp_your_token_here
GITHUB_WEBHOOK_SECRET=your-webhook-secret
```

**AI Provider (Choose one):**

OpenAI:
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
```

Anthropic:
```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229
```

Custom OpenAI-compatible:
```bash
AI_PROVIDER=custom
CUSTOM_OPENAI_BASE_URL=https://your-api.com/v1
CUSTOM_OPENAI_API_KEY=your-key-here
CUSTOM_OPENAI_MODEL=your-model-name
```

**Review Settings:**
```bash
MAX_FILES_PER_REVIEW=20
MAX_DIFF_SIZE=50000
REVIEW_TIMEOUT=300
```

**Database:**
```bash
DATABASE_PATH=ai_reviews.db
```

## Setting Up GitHub Webhook

1. **Expose your application to the internet**
   - For production: Deploy to a server with public IP/domain
   - For testing: Use ngrok or similar tunnel service

2. **Configure webhook in GitHub:**
   - Go to your repository
   - Settings → Webhooks → Add webhook
   - **Payload URL**: `https://your-domain.com/webhook`
   - **Content type**: `application/json`
   - **Secret**: Your `GITHUB_WEBHOOK_SECRET` from `.env`
   - **Events**: Select "Pull requests"
   - **Active**: ✓ Checked

3. **Test webhook:**
   - Create a pull request in the repository
   - Check webhook deliveries in GitHub settings
   - Check application logs for webhook processing

## Usage

### Automatic Reviews (via Webhook)

Once configured, the bot automatically:
1. Detects new pull requests
2. Analyzes repository patterns (if first time)
3. Reviews the PR diff
4. Posts suggestions as PR comments

### Manual Review (via Dashboard)

1. Open dashboard at `http://localhost:5000`
2. Enter repository (e.g., `owner/repo-name`)
3. Enter PR number
4. Click "Review Pull Request"
5. Review processes in background
6. Results appear on dashboard and as PR comments

### Repository Analysis

Analyze a repository to learn its patterns:
1. Go to dashboard
2. Enter repository name
3. Click "Analyze Repository"
4. Bot learns naming, style, imports, and conventions

## API Endpoints

### POST `/webhook`
GitHub webhook endpoint for pull request events.

**Headers:**
- `X-Hub-Signature-256`: HMAC signature for verification

**Body:** GitHub webhook payload

### POST `/api/review`
Manually trigger a PR review.

**Body:**
```json
{
  "repo": "owner/repo-name",
  "pr_number": 123
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Review started",
  "data": {
    "repo": "owner/repo-name",
    "pr_number": 123
  }
}
```

### POST `/api/analyze-repo`
Analyze a repository to learn patterns.

**Body:**
```json
{
  "repo": "owner/repo-name"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Repository analyzed successfully",
  "data": {
    "repo": "owner/repo-name",
    "files_analyzed": 45,
    "patterns_learned": ["naming", "imports", "style"]
  }
}
```

### GET `/api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "success",
  "data": {
    "provider": "openai",
    "github_configured": true,
    "database": "connected"
  }
}
```

## Database Schema

### patterns
Stores learned codebase patterns and conventions.

```sql
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY,
    repo TEXT NOT NULL,
    pattern_type TEXT NOT NULL,
    pattern_data TEXT NOT NULL,
    last_updated TIMESTAMP,
    UNIQUE(repo, pattern_type)
)
```

### reviews
Stores review history.

```sql
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    repo TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    review_data TEXT NOT NULL,
    created_at TIMESTAMP,
    status TEXT DEFAULT 'completed'
)
```

### repo_config
Per-repository configuration (future use).

```sql
CREATE TABLE repo_config (
    id INTEGER PRIMARY KEY,
    repo TEXT UNIQUE NOT NULL,
    config_data TEXT NOT NULL,
    updated_at TIMESTAMP
)
```

## Production Deployment

### Using Gunicorn

1. **Install Gunicorn** (already in requirements.txt)
```bash
pip install gunicorn
```

2. **Run with Gunicorn**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. **With systemd service**
Create `/etc/systemd/system/ai-reviewer.service`:
```ini
[Unit]
Description=AI Code Review Bot
After=network.target

[Service]
Type=simple
User=nonbios
WorkingDirectory=/home/nonbios/ai-code-reviewer
Environment="PATH=/home/nonbios/ai-code-reviewer/venv/bin"
ExecStart=/home/nonbios/ai-code-reviewer/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-reviewer
sudo systemctl start ai-reviewer
```

### Using Nginx as Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Webhook not triggering
- Check webhook delivery status in GitHub settings
- Verify `GITHUB_WEBHOOK_SECRET` matches
- Check application logs for errors
- Ensure endpoint is publicly accessible

### AI provider errors
- Verify API key is correct
- Check API rate limits
- Verify model name is correct
- Check provider status page

### Database errors
- Ensure write permissions on database file
- Check disk space
- Verify SQLite installation

### Pattern learning fails
- Ensure GitHub token has repository read access
- Check repository visibility (public vs private)
- Verify file extensions are supported

## Development

### Running tests
```bash
source venv/bin/activate
python3 -m pytest tests/
```

### Adding new AI providers
1. Extend `ai_engine.py` with new provider class
2. Add provider configuration to `config.py`
3. Update `.env.example` with new provider settings
4. Test with manual review

## Security

- **Never commit `.env` file** - Contains sensitive credentials
- **Rotate webhook secrets regularly**
- **Use HTTPS in production** - Protect webhook payload
- **Limit GitHub token scope** - Only `repo` access needed
- **Validate all inputs** - Prevent injection attacks
- **Rate limit API endpoints** - Prevent abuse

## License

MIT License - See LICENSE file for details

## Support

For issues, feature requests, or questions:
- Check existing issues in GitHub
- Review troubleshooting section
- Check application logs for errors

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

---

**Built with ❤️ for better code reviews**
