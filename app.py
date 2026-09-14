from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
import threading
import sys
import os

# Add src directory to Python path for kiss package imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stinker.config import Config
from stinker.database import Database
from stinker.github_client import GitHubClient
from stinker.diff_parser import DiffParser
from stinker.pattern_analyzer import PatternAnalyzer
from stinker.ai_engine import AIEngine
from stinker.utils import require_github_signature, format_error_response, format_success_response, validate_pr_number, validate_repo_name

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Initialize components
db = Database()
github_client = GitHubClient()
diff_parser = DiffParser()
pattern_analyzer = PatternAnalyzer(github_client)
ai_engine = AIEngine()

# Validate configuration on startup
config_errors = Config.validate()
if config_errors:
    print("⚠️  Configuration errors:")
    for error in config_errors:
        print(f"   - {error}")
    print("\nPlease check your .env file")

@app.route('/')
def index():
    """Dashboard home page"""
    recent_reviews = db.get_recent_reviews(limit=10)
    return render_template('index.html', reviews=recent_reviews, config=Config)

@app.route('/config')
def config_page():
    """Configuration page"""
    return render_template('config.html', config=Config)

@app.route('/webhook', methods=['POST'])
@require_github_signature
def webhook():
    """GitHub webhook endpoint for PR events"""
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.json
    
    if not payload:
        return format_error_response('No payload received')
    
    # Handle pull request events
    if event_type == 'pull_request':
        return handle_pull_request(payload)
    
    
    # Handle GitHub App installation events
    elif event_type == 'installation':
        return handle_installation(payload)
    
    elif event_type == 'installation_repositories':
        return handle_installation_repositories(payload)
    # Handle ping event (webhook test)
    elif event_type == 'ping':
        return jsonify({'message': 'Pong! Webhook is configured correctly'}), 200
    
    return jsonify({'message': f'Event {event_type} received but not processed'}), 200


def handle_installation(payload):
    """Handle GitHub App installation events (created, deleted, suspend, unsuspend)"""
    action = payload.get('action')
    installation = payload.get('installation', {})
    
    installation_id = installation.get('id')
    account = installation.get('account', {})
    
    logger.info(f"Installation event: action={action}, installation_id={installation_id}, account={account.get('login')}")
    
    if action == 'created':
        # New installation - save to database
        installation_data = {
            'installation_id': installation_id,
            'account_id': account.get('id'),
            'account_login': account.get('login'),
            'account_type': account.get('type'),
            'target_type': installation.get('target_type'),
            'repository_selection': installation.get('repository_selection', 'all'),
            'repositories': [repo.get('full_name') for repo in installation.get('repositories', [])],
            'permissions': installation.get('permissions', {}),
            'events': installation.get('events', [])
        }
        
        try:
            db.save_installation(installation_data)
            logger.info(f"Saved installation {installation_id} for {account.get('login')}")
            return jsonify({'message': 'Installation created successfully'}), 201
        except Exception as e:
            logger.error(f"Failed to save installation: {str(e)}")
            return format_error_response(f'Failed to save installation: {str(e)}')
    
    elif action == 'deleted':
        # Installation removed - delete from database
        try:
            db.delete_installation(installation_id)
            logger.info(f"Deleted installation {installation_id}")
            return jsonify({'message': 'Installation deleted successfully'}), 200
        except Exception as e:
            logger.error(f"Failed to delete installation: {str(e)}")
            return format_error_response(f'Failed to delete installation: {str(e)}')
    
    elif action == 'suspend':
        # Installation suspended
        installation_data = {
            'installation_id': installation_id,
            'account_id': account.get('id'),
            'account_login': account.get('login'),
            'account_type': account.get('type'),
            'target_type': installation.get('target_type'),
            'suspended_at': datetime.utcnow(),
            'suspended_by': payload.get('sender', {}).get('login')
        }
        
        try:
            db.save_installation(installation_data)
            logger.info(f"Suspended installation {installation_id}")
            return jsonify({'message': 'Installation suspended'}), 200
        except Exception as e:
            logger.error(f"Failed to suspend installation: {str(e)}")
            return format_error_response(f'Failed to suspend installation: {str(e)}')
    
    elif action == 'unsuspend':
        # Installation unsuspended
        installation_data = {
            'installation_id': installation_id,
            'account_id': account.get('id'),
            'account_login': account.get('login'),
            'account_type': account.get('type'),
            'target_type': installation.get('target_type'),
            'suspended_at': None,
            'suspended_by': None
        }
        
        try:
            db.save_installation(installation_data)
            logger.info(f"Unsuspended installation {installation_id}")
            return jsonify({'message': 'Installation unsuspended'}), 200
        except Exception as e:
            logger.error(f"Failed to unsuspend installation: {str(e)}")
            return format_error_response(f'Failed to unsuspend installation: {str(e)}')
    
    return jsonify({'message': f'Installation action {action} received'}), 200

def handle_installation_repositories(payload):
    """Handle installation_repositories events (added, removed)"""
    action = payload.get('action')
    installation = payload.get('installation', {})
    installation_id = installation.get('id')
    
    repositories_added = [repo.get('full_name') for repo in payload.get('repositories_added', [])]
    repositories_removed = [repo.get('full_name') for repo in payload.get('repositories_removed', [])]
    
    logger.info(f"Installation repositories event: action={action}, installation_id={installation_id}")
    logger.info(f"Added: {repositories_added}, Removed: {repositories_removed}")
    
    try:
        # Get current installation
        current_installation = db.get_installation(installation_id)
        if not current_installation:
            logger.error(f"Installation {installation_id} not found")
            return format_error_response('Installation not found')
        
        current_repos = set(current_installation.get('repositories', []))
        
        # Update repository list
        if action == 'added':
            current_repos.update(repositories_added)
        elif action == 'removed':
            current_repos.difference_update(repositories_removed)
        
        # Save updated installation
        account = installation.get('account', {})
        installation_data = {
            'installation_id': installation_id,
            'account_id': account.get('id'),
            'account_login': account.get('login'),
            'account_type': account.get('type'),
            'target_type': installation.get('target_type'),
            'repository_selection': installation.get('repository_selection', 'selected'),
            'repositories': list(current_repos),
            'permissions': installation.get('permissions', {}),
            'events': installation.get('events', [])
        }
        
        db.save_installation(installation_data)
        logger.info(f"Updated repositories for installation {installation_id}")
        return jsonify({'message': 'Installation repositories updated'}), 200
        
    except Exception as e:
        logger.error(f"Failed to update installation repositories: {str(e)}")
        return format_error_response(f'Failed to update installation repositories: {str(e)}')

def handle_pull_request(payload):
    """Handle pull request webhook event"""
    action = payload.get('action')
    
    # Only process opened and synchronize (updated) PRs
    if action not in ['opened', 'synchronize']:
        return jsonify({'message': f'Action {action} ignored'}), 200
    
    pr = payload.get('pull_request', {})
    repo = payload.get('repository', {})
    installation = payload.get('installation', {})
    
    repo_full_name = repo.get('full_name')
    pr_number = pr.get('number')
    installation_id = installation.get('id')
    
    if not repo_full_name or not pr_number:
        return format_error_response('Invalid payload structure')
    
    print(f"📝 Processing PR #{pr_number} from {repo_full_name} (installation: {installation_id})")
    
    # Process in background thread to avoid webhook timeout
    thread = threading.Thread(
        target=process_pr_review,
        args=(repo_full_name, pr_number, installation_id)
    )
    thread.start()
    
    return jsonify({
        'message': f'Review started for PR #{pr_number}',
        'status': 'processing'
    }), 202

def process_pr_review(repo_full_name, pr_number, installation_id=None):
    """Process PR review (called in background thread)"""
    try:
        print(f"🔍 Starting review for {repo_full_name} PR #{pr_number}")
        
        # 1. Check if we have patterns for this repo
        repo_config = db.get_repo_config(repo_full_name)
        
        if not repo_config or not repo_config.get('config_data', {}).get('patterns'):
            print(f"📚 Learning patterns for {repo_full_name}...")
            patterns = pattern_analyzer.analyze_repository(repo_full_name)
            db.update_repo_config(repo_full_name, {'patterns': patterns})
        else:
            patterns = repo_config['config_data']['patterns']
            print(f"✅ Using cached patterns ({patterns.get('total_files_analyzed', 0)} files)")
        
        # 2. Get PR diff
        print(f"📥 Fetching PR diff...")
        pr_files = github_client.get_pr_files(repo_full_name, pr_number, installation_id=installation_id)
        
        if not pr_files:
            print(f"⚠️  No files found in PR #{pr_number}")
            return
        
        # Limit number of files
        if len(pr_files) > Config.MAX_FILES_TO_ANALYZE:
            print(f"⚠️  Too many files ({len(pr_files)}), limiting to {Config.MAX_FILES_TO_ANALYZE}")
            pr_files = pr_files[:Config.MAX_FILES_TO_ANALYZE]
        
        # 3. Parse diffs
        print(f"🔬 Parsing {len(pr_files)} files...")
        all_changes = []
        
        for file_info in pr_files:
            if file_info.get('patch'):
                parsed = diff_parser.parse_diff(file_info['patch'])
                changes = diff_parser.extract_changed_code(parsed)
                all_changes.extend(changes)
        
        if not all_changes:
            print(f"ℹ️  No code changes to review in PR #{pr_number}")
            return
        
        print(f"📊 Found {len(all_changes)} change sections")
        
        # 4. AI Review
        print(f"🤖 Requesting AI review...")
        review_result = ai_engine.review_code(all_changes, patterns, repo_full_name)
        
        # 5. Post comment to GitHub
        comment_body = ai_engine.format_review_comment(review_result)
        
        print(f"💬 Posting review comment...")
        success = github_client.post_review_comment(repo_full_name, pr_number, comment_body, installation_id=installation_id)
        
        if success:
            print(f"✅ Review posted successfully for PR #{pr_number}")
        else:
            print(f"❌ Failed to post review for PR #{pr_number}")
        
        # 6. Save review to database
        db.save_review(repo_full_name, pr_number, {
            'review_result': review_result,
            'files_reviewed': len(pr_files),
            'changes_analyzed': len(all_changes),
            'posted': success
        })
        
        print(f"✨ Review complete for {repo_full_name} PR #{pr_number}")
        
    except Exception as e:
        print(f"❌ Error processing PR review: {e}")
        import traceback
        traceback.print_exc()

@app.route('/api/review', methods=['POST'])
def manual_review():
    """Manual trigger for PR review"""
    data = request.json
    
    repo_full_name = data.get('repo')
    pr_number = data.get('pr_number')
    installation_id = data.get('installation_id')  # Optional for GitHub App mode
    
    if not validate_repo_name(repo_full_name):
        return format_error_response('Invalid repository name format. Use: owner/repo')
    
    if not validate_pr_number(pr_number):
        return format_error_response('Invalid PR number')
    
    # Start review in background
    thread = threading.Thread(
        target=process_pr_review,
        args=(repo_full_name, int(pr_number), installation_id)
    )
    thread.start()
    
    return format_success_response(
        {'repo': repo_full_name, 'pr_number': pr_number},
        'Review started'
    )

@app.route('/api/analyze-repo', methods=['POST'])
def analyze_repository():
    """Manually analyze repository patterns"""
    data = request.json
    repo_full_name = data.get('repo')
    
    if not validate_repo_name(repo_full_name):
        return format_error_response('Invalid repository name format. Use: owner/repo')
    
    try:
        print(f"📚 Analyzing patterns for {repo_full_name}...")
        patterns = pattern_analyzer.analyze_repository(repo_full_name)
        db.update_repo_config(repo_full_name, {'patterns': patterns})
        
        summary = pattern_analyzer.get_pattern_summary(patterns)
        
        return format_success_response({
            'repo': repo_full_name,
            'files_analyzed': patterns.get('total_files_analyzed', 0),
            'summary': summary
        }, 'Repository analyzed successfully')
    except Exception as e:
        return format_error_response(f'Error analyzing repository: {str(e)}')

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    """Get recent reviews"""
    limit = request.args.get('limit', 10, type=int)
    reviews = db.get_recent_reviews(limit=min(limit, 100))
    return format_success_response(reviews, 'Reviews retrieved')

@app.route('/api/review/<repo_owner>/<repo_name>/<int:pr_number>', methods=['GET'])
def get_review(repo_owner, repo_name, pr_number):
    """Get specific review"""
    repo_full_name = f"{repo_owner}/{repo_name}"
    review = db.get_review(repo_full_name, pr_number)
    
    if review:
        return format_success_response(review, 'Review found')
    else:
        return format_error_response('Review not found', 404)

@app.route('/api/patterns/<repo_owner>/<repo_name>', methods=['GET'])
def get_patterns(repo_owner, repo_name):
    """Get learned patterns for a repository"""
    repo_full_name = f"{repo_owner}/{repo_name}"
    patterns = db.get_patterns(repo_full_name)
    
    return format_success_response({
        'repo': repo_full_name,
        'patterns': patterns
    }, 'Patterns retrieved')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return format_success_response({
        'status': 'healthy',
        'provider': Config.AI_PROVIDER,
        'github_configured': bool(Config.GITHUB_TOKEN)
    }, 'Service is healthy')

@app.errorhandler(404)
def not_found(e):
    return format_error_response('Endpoint not found', 404)

@app.errorhandler(500)
def internal_error(e):
    return format_error_response('Internal server error', 500)

if __name__ == '__main__':
    print("🚀 AI Code Review Bot Starting...")
    print(f"   Provider: {Config.AI_PROVIDER}")
    print(f"   Port: {Config.PORT}")
    print(f"   Environment: {Config.FLASK_ENV}")
    
    if config_errors:
        print("\n⚠️  Warning: Configuration incomplete. Some features may not work.")
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=(Config.FLASK_ENV == 'development')
    )
