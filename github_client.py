from github import Github, GithubException
from config import Config
import base64

class GitHubClient:
    """GitHub API client for PR and repository interactions"""
    
    def __init__(self, token=None):
        self.token = token or Config.GITHUB_TOKEN
        self.client = Github(self.token)
    
    def get_repository(self, repo_full_name):
        """Get repository object"""
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
            import requests
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
