import hashlib
import hmac
from functools import wraps
from flask import request, jsonify
from config import Config

def verify_github_signature(payload_body, signature_header):
    """Verify that the webhook payload was sent from GitHub"""
    if not Config.GITHUB_WEBHOOK_SECRET:
        return True  # Skip verification if no secret configured
    
    if not signature_header:
        return False
    
    hash_algorithm, github_signature = signature_header.split('=')
    algorithm = hashlib.__dict__.get(hash_algorithm)
    
    if not algorithm:
        return False
    
    mac = hmac.new(
        Config.GITHUB_WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=algorithm
    )
    
    return hmac.compare_digest(mac.hexdigest(), github_signature)

def require_github_signature(f):
    """Decorator to verify GitHub webhook signature"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get('X-Hub-Signature-256') or request.headers.get('X-Hub-Signature')
        
        if not verify_github_signature(request.data, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def format_error_response(error_message, status_code=400):
    """Format error response"""
    return jsonify({
        'error': error_message,
        'status': 'error'
    }), status_code

def format_success_response(data, message='Success'):
    """Format success response"""
    return jsonify({
        'status': 'success',
        'message': message,
        'data': data
    }), 200

def truncate_text(text, max_length=100):
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + '...'

def sanitize_repo_name(repo_full_name):
    """Sanitize repository name"""
    return repo_full_name.replace('/', '_').replace('.', '_')

def get_file_type_emoji(filename):
    """Get emoji for file type"""
    if filename.endswith('.py'):
        return '🐍'
    elif filename.endswith(('.js', '.jsx')):
        return '📜'
    elif filename.endswith(('.ts', '.tsx')):
        return '📘'
    elif filename.endswith('.java'):
        return '☕'
    elif filename.endswith('.go'):
        return '🐹'
    elif filename.endswith('.rb'):
        return '💎'
    elif filename.endswith('.php'):
        return '🐘'
    elif filename.endswith(('.html', '.css')):
        return '🎨'
    else:
        return '📄'

def validate_pr_number(pr_number):
    """Validate PR number"""
    try:
        num = int(pr_number)
        return num > 0
    except (ValueError, TypeError):
        return False

def validate_repo_name(repo_name):
    """Validate repository name format"""
    if not repo_name or '/' not in repo_name:
        return False
    
    parts = repo_name.split('/')
    return len(parts) == 2 and all(part.strip() for part in parts)
