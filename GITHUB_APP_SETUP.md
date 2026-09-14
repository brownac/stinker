# GitHub App Setup Instructions

## Step 1: Create Your GitHub App

1. **Navigate to GitHub Settings**
   - Go to https://github.com/settings/apps
   - Or: Your Profile → Settings → Developer settings → GitHub Apps
   - Click "New GitHub App"

2. **Basic Information**
   - **GitHub App name**: `stinker-code-reviewer` (or your preferred name)
   - **Homepage URL**: `https://github.com/yourusername/ai-code-reviewer`
   - **Webhook URL**: `https://your-domain.com/webhook` (your public URL)
   - **Webhook secret**: Generate a random secret (save for .env)
     ```bash
     openssl rand -hex 32
     ```

3. **Permissions Required**

   **Repository permissions:**
   - Contents: Read-only (to read repository files and analyze patterns)
   - Pull requests: Read & write (to read PR diffs and post review comments)
   - Metadata: Read-only (automatically selected)

   **Subscribe to events:**
   - [x] Pull request
   - [x] Pull request review
   - [x] Pull request review comment

4. **Where can this GitHub App be installed?**
   - Select: "Any account" (for public marketplace)
   - OR: "Only on this account" (for private/personal use)

5. **Create the App**
   - Click "Create GitHub App"
   - You'll be redirected to your app's settings page

## Step 2: Generate Private Key

1. Scroll down to "Private keys" section
2. Click "Generate a private key"
3. A `.pem` file will download - **save this securely!**
4. Move it to your project directory:
   ```bash
   mv ~/Downloads/your-app-name.2024-01-01.private-key.pem /home/nonbios/ai-code-reviewer/github-app-key.pem
   chmod 600 /home/nonbios/ai-code-reviewer/github-app-key.pem
   ```

## Step 3: Note Your App Credentials

From the app settings page, copy these values:

- **App ID**: Found at the top (e.g., "123456")
- **Client ID**: Found in "About" section
- **Webhook secret**: The secret you generated in step 2

## Step 4: Update Your .env File

Add these to your `.env`:

```bash
# GitHub App Configuration
GITHUB_APP_ID=your_app_id_here
GITHUB_APP_PRIVATE_KEY_PATH=github-app-key.pem
GITHUB_APP_WEBHOOK_SECRET=your_webhook_secret_here
GITHUB_APP_CLIENT_ID=your_client_id_here
GITHUB_APP_CLIENT_SECRET=your_client_secret_here

# Legacy - Keep for backward compatibility during migration
GITHUB_TOKEN=ghp_legacy_token_if_needed
GITHUB_WEBHOOK_SECRET=same_as_app_webhook_secret
```

## Step 5: Install Your App

### For Testing (Your Own Repos)
1. Go to your app's page: `https://github.com/settings/apps/your-app-name`
2. Click "Install App" in the left sidebar
3. Select your account
4. Choose "All repositories" or select specific repos
5. Click "Install"

### For Users (OAuth Flow)
Users can install via:
```
https://github.com/apps/your-app-name/installations/new
```

## Step 6: Test the Installation

After implementing the code changes, test with:

```bash
cd /home/nonbios/ai-code-reviewer
source venv/bin/activate
python3 app.py
```

Then:
1. Open a PR in an installed repository
2. Check the app receives the webhook
3. Verify it posts a review comment

## Verification Checklist

- [ ] GitHub App created
- [ ] Private key downloaded and saved securely
- [ ] App installed on at least one test repository
- [ ] Webhook URL is publicly accessible
- [ ] All credentials added to .env
- [ ] App permissions are correct
- [ ] Webhook events are subscribed

## Troubleshooting

**Webhook not received:**
- Verify webhook URL is publicly accessible
- Check webhook secret matches
- Review "Recent Deliveries" in app settings

**Authentication failed:**
- Verify App ID is correct
- Check private key path and permissions
- Ensure private key format is correct (PEM)

**Installation not found:**
- Confirm app is installed on the repository
- Check installation ID in database
- Verify installation hasn't been suspended

## Next Steps

Once you've completed this setup:
1. ✅ Mark that you've created the app
2. The bot will implement the code changes
3. Deploy and test the installation flow
4. Optionally publish to GitHub Marketplace
