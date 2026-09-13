# Quick Start Guide - AI Code Review Bot

## Server Information
- **Public IP**: 136.83.37.29
- **Installation Path**: /home/nonbios/ai-code-reviewer
- **User**: nonbios
- **Password**: KlhR45oZZJ4zWYLRcS#1

## Access Methods

### 1. Dashboard (via Flask App)
Once started, access at:
- **Local**: http://localhost:5000
- **Public**: http://136.83.37.29:5000

### 2. File Browser
- **URL**: http://136.83.37.29:8080
- **User**: nonbios
- **Password**: KlhR45oZZJ4zWYLRcS#1

### 3. SSH Access
```bash
ssh nonbios@136.83.37.29
```

## Starting the Application

### Development Mode (Quick Test)
```bash
cd /home/nonbios/ai-code-reviewer
source venv/bin/activate
python3 app.py
```

The app will start on port 5000.

### Production Mode (Recommended)
```bash
cd /home/nonbios/ai-code-reviewer
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 app:app
```

Or run in background:
```bash
nohup gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 app:app > logs/app.log 2>&1 &
```

## Configuration

Edit `.env` file with your credentials:
```bash
nano .env
```

**Required settings:**
1. `GITHUB_TOKEN` - GitHub Personal Access Token
2. `GITHUB_WEBHOOK_SECRET` - Secret for webhook verification
3. AI Provider credentials (choose one):
   - OpenAI: `OPENAI_API_KEY`
   - Anthropic: `ANTHROPIC_API_KEY`
   - Custom: `CUSTOM_OPENAI_BASE_URL` + `CUSTOM_OPENAI_API_KEY`

## GitHub Webhook Setup

1. **Make your endpoint accessible**:
   - Your webhook URL: `http://136.83.37.29:5000/webhook`
   - For production, use HTTPS with domain name

2. **Configure in GitHub**:
   - Go to repository → Settings → Webhooks → Add webhook
   - **Payload URL**: `http://136.83.37.29:5000/webhook`
   - **Content type**: application/json
   - **Secret**: [Your GITHUB_WEBHOOK_SECRET]
   - **Events**: Pull requests
   - **Active**: ✓

## Testing the Bot

### 1. Test Health Check
```bash
curl http://localhost:5000/api/health
```

### 2. Analyze a Repository
Using the dashboard or API:
```bash
curl -X POST http://localhost:5000/api/analyze-repo \
  -H "Content-Type: application/json" \
  -d '{"repo": "owner/repo-name"}'
```

### 3. Manual PR Review
```bash
curl -X POST http://localhost:5000/api/review \
  -H "Content-Type: application/json" \
  -d '{"repo": "owner/repo-name", "pr_number": 1}'
```

### 4. Create Test PR
Create a PR in your test repository and watch for automatic review!

## Checking Logs

If running in background:
```bash
tail -f logs/app.log
```

If running directly, logs appear in terminal.

## Stopping the Application

If running in foreground: `Ctrl+C`

If running in background:
```bash
pkill -f gunicorn
# or
ps aux | grep gunicorn
kill [PID]
```

## Troubleshooting

### Port already in use
```bash
# Find process on port 5000
sudo lsof -i :5000
# Kill it
sudo kill [PID]
```

### Webhook not working
- Check GitHub webhook delivery status
- Verify GITHUB_WEBHOOK_SECRET matches
- Check application logs
- Ensure port 5000 is accessible from internet

### AI Provider errors
- Verify API key in .env
- Check API rate limits
- Test with curl to provider API directly

## File Locations

- **Application**: `/home/nonbios/ai-code-reviewer/`
- **Database**: `/home/nonbios/ai-code-reviewer/patterns.db`
- **Configuration**: `/home/nonbios/ai-code-reviewer/.env`
- **Logs**: `/home/nonbios/ai-code-reviewer/logs/` (if configured)

## Next Steps

1. ✅ Installation complete
2. ⚙️ Configure .env with your credentials
3. 🚀 Start the application
4. 🌐 Access dashboard at http://136.83.37.29:5000
5. 🔗 Set up GitHub webhooks
6. 🧪 Test with a pull request

## Support

For detailed documentation, see README.md
