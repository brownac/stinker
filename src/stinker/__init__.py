"""
Stinker AI Code Reviewer
A configurable BYOK AI code-review bot that analyzes pull-request diffs
and suggests simplifications aligned with repository patterns.
"""

__version__ = '1.0.0'
__author__ = 'AI Code Reviewer Bot'

# Core modules
from stinker.config import Config
from stinker.database import Database
from stinker.github_client import GitHubClient
from stinker.diff_parser import DiffParser
from stinker.pattern_analyzer import PatternAnalyzer
from stinker.ai_engine import AIEngine
from stinker.utils import (
    verify_github_signature,
    require_github_signature,
    format_error_response,
    format_success_response,
    validate_pr_number,
    validate_repo_name
)

__all__ = [
    'Config',
    'Database',
    'GitHubClient',
    'DiffParser',
    'PatternAnalyzer',
    'AIEngine',
    'verify_github_signature',
    'require_github_signature',
    'format_error_response',
    'format_success_response',
    'validate_pr_number',
    'validate_repo_name',
]
