from github import Github, GithubException, GithubIntegration
from stinker.config import Config
import base64
import jwt
import time
import requests
from datetime import datetime, timedelta

class GitHubAppAuth:
    """GitHub App authentication helper"""
    
    def __init__(self):
        self.app_id = Config.GITHUB_APP_ID
        self.private_key = self._load_private_key()
        self._token_cache = {}  # installation_id -> (token, expiry)
    
    def _load_private_key(self):
        """Load private key from file or environment variable"""
        if Config.GITHUB_APP_PRIVATE_KEY:
            # Key provided as string in environment
            return Config.GITHUB_APP_PRIVATE_KEY
        elif Config.GITHUB_APP_PRIVATE_KEY_PATH:
            # Load from file
            try:
                with open(Config.GITHUB_APP_PRIVATE_KEY_PATH, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                print(f"⚠️  Private key file not found: {Config.GITHUB_APP_PRIVATE_KEY_PATH}")
                return None
        return None
    
    def generate_jwt(self):
        """Generate JWT for GitHub App authentication"""
        if not self.private_key or not self.app_id:
            return None
        
        # JWT expires after 10 minutes
        now = int(time.time())
        payload = {
            'iat': now,
            'exp': now + (10 * 60),
            'iss': self.app_id
        }
        
        try:
            token = jwt.encode(payload, self.private_key, algorithm='RS256')
            return token
        except Exception as e:
            print(f"Error generating JWT: {e}")
            return None
    
    def get_installation_token(self, installation_id):
        """Get installation access token (cached for 1 hour)"""
        # Check cache
        if installation_id in self._token_cache:
            token, expiry = self._token_cache[installation_id]
            if datetime.now() < expiry:
                return token
        
        # Generate new token
        jwt_token = self.generate_jwt()
        if not jwt_token:
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
            response = requests.post(url, headers=headers)
            
            if response.status_code == 201:
                data = response.json()
                token = data['token']
                # Cache for 50 minutes (tokens last 1 hour)
                expiry = datetime.now() + timedelta(minutes=50)
                self._token_cache[installation_id] = (token, expiry)
                return token
            else:
                print(f"Error getting installation token: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error requesting installation token: {e}")
            return None
    
    def get_installation_id_for_repo(self, repo_full_name):
        """Get installation ID for a repository"""
        jwt_token = self.generate_jwt()
        if not jwt_token:
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            owner, repo = repo_full_name.split('/')
            url = f'https://api.github.com/repos/{owner}/{repo}/installation'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data['id']
            else:
                print(f"Error getting installation: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching installation ID: {e}")
            return None


class GitHubClient:
    """GitHub API client for PR and repository interactions"""
    
    def __init__(self, token=None, installation_id=None):
        """
        Initialize GitHub client with either:
        - token: Personal Access Token (legacy mode)
        - installation_id: GitHub App installation ID
        """
        self.use_app = Config.USE_GITHUB_APP
        self.app_auth = GitHubAppAuth() if self.use_app else None
        self.installation_id = installation_id
        
        if self.use_app and installation_id:
            # GitHub App mode
            token = self.app_auth.get_installation_token(installation_id)
            if not token:
                print("⚠️  Failed to get installation token, falling back to PAT")
                token = Config.GITHUB_TOKEN
        else:
            # Legacy PAT mode
            token = token or Config.GITHUB_TOKEN
        
        self.token = token
        self.client = Github(token) if token else None
    
    def get_client_for_repo(self, repo_full_name):
        """Get authenticated client for a specific repository"""
        if self.use_app:
            installation_id = self.app_auth.get_installation_id_for_repo(repo_full_name)
            if installation_id:
                return GitHubClient(installation_id=installation_id)
        return self
    
    def get_repository(self, repo_full_name):
        """Get repository object"""
        if not self.client:
            print("No GitHub client available")
            return None
        
        try:
            return self.client.get_repo(repo_full_name)
        except GithubException as e:
            print(f"Error fetching repository {repo_full_name}: {e}")
            return None
    
    def get_pull_request(self, repo_full_name, pr_number):
        """Get pull request object"""
        try:
            repo = self.get_repository(repo_full_name)
            if repo:
                return repo.get_pull(pr_number)
        except GithubException as e:
            print(f"Error fetching PR #{pr_number}: {e}")
        return None
    
    def get_pr_files(self, repo_full_name, pr_number):
        """Get list of files changed in a PR"""
        pr = self.get_pull_request(repo_full_name, pr_number)
        if not pr:
            return []
        
        files = []
        try:
            for file in pr.get_files():
                files.append({
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'patch': file.patch if hasattr(file, 'patch') else None,
                    'raw_url': file.raw_url
                })
        except GithubException as e:
            print(f"Error fetching PR files: {e}")
        
        return files
    
    def get_pr_diff(self, repo_full_name, pr_number):
        """Get full diff for a PR"""
        pr = self.get_pull_request(repo_full_name, pr_number)
        if not pr:
            return None
        
        try:
            # Get the diff using the API
            diff_url = pr.diff_url
            headers = {'Accept': 'application/vnd.github.v3.diff'}
            response = requests.get(diff_url, headers=headers)
            return response.text if response.status_code == 200 else None
        except Exception as e:
            print(f"Error fetching diff: {e}")
            return None
    
    def post_review_comment(self, repo_full_name, pr_number, body):
        """Post a review comment on a PR"""
        pr = self.get_pull_request(repo_full_name, pr_number)
        if not pr:
            return False
        
        try:
            pr.create_issue_comment(body)
            return True
        except GithubException as e:
            print(f"Error posting comment: {e}")
            return False
    
    def post_review(self, repo_full_name, pr_number, comments, event='COMMENT'):
        """
        Post a code review with inline comments
        event: 'APPROVE', 'REQUEST_CHANGES', 'COMMENT'
        comments: list of {'path': str, 'line': int, 'body': str}
        """
        pr = self.get_pull_request(repo_full_name, pr_number)
        if not pr:
            return False
        
        try:
            # Get the latest commit
            commits = list(pr.get_commits())
            if not commits:
                return False
            
            latest_commit = commits[-1]
            
            # Create review with comments
            review_comments = []
            for comment in comments:
                review_comments.append({
                    'path': comment['path'],
                    'line': comment['line'],
                    'body': comment['body']
                })
            
            pr.create_review(
                commit=latest_commit,
                body="🤖 AI Code Review - Simplification Suggestions",
                event=event,
                comments=review_comments if review_comments else None
            )
            return True
        except GithubException as e:
            print(f"Error posting review: {e}")
            return False
    
    def get_file_content(self, repo_full_name, file_path, ref='main'):
        """Get content of a file from repository"""
        repo = self.get_repository(repo_full_name)
        if not repo:
            return None
        
        try:
            # Try different default branches
            branches_to_try = [ref, 'main', 'master']
            
            for branch in branches_to_try:
                try:
                    content = repo.get_contents(file_path, ref=branch)
                    if content:
                        return base64.b64decode(content.content).decode('utf-8')
                except:
                    continue
            
            return None
        except GithubException as e:
            print(f"Error fetching file {file_path}: {e}")
            return None
    
    def list_repository_files(self, repo_full_name, path='', ref='main', max_files=100):
        """List files in repository recursively"""
        repo = self.get_repository(repo_full_name)
        if not repo:
            return []
        
        files = []
        
        def traverse(path, ref):
            if len(files) >= max_files:
                return
            
            try:
                contents = repo.get_contents(path, ref=ref)
                
                for content in contents:
                    if len(files) >= max_files:
                        break
                    
                    if content.type == 'file':
                        # Filter code files
                        code_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', 
                                         '.go', '.rb', '.php', '.cs', '.cpp', '.c', '.h']
                        if any(content.name.endswith(ext) for ext in code_extensions):
                            files.append({
                                'path': content.path,
                                'name': content.name,
                                'size': content.size
                            })
                    elif content.type == 'dir':
                        traverse(content.path, ref)
            except GithubException as e:
                print(f"Error listing files in {path}: {e}")
        
        # Try different branches
        for branch in [ref, 'main', 'master']:
            try:
                traverse(path, branch)
                break
            except:
                continue
        
        return files
    
    def get_default_branch(self, repo_full_name):
        """Get default branch of repository"""
        repo = self.get_repository(repo_full_name)
        if repo:
            return repo.default_branch
        return 'main'
