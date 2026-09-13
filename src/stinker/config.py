import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration management for AI Code Reviewer"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    PORT = int(os.getenv('PORT', 5000))
    
    # GitHub
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET')
    
    # AI Provider Configuration
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')  # openai, anthropic, custom
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    # Anthropic
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
    
    # Custom AI Endpoint
    CUSTOM_AI_ENDPOINT = os.getenv('CUSTOM_AI_ENDPOINT')
    CUSTOM_AI_API_KEY = os.getenv('CUSTOM_AI_API_KEY')
    CUSTOM_AI_MODEL = os.getenv('CUSTOM_AI_MODEL')
    
    # Review Settings
    MAX_FILES_TO_ANALYZE = int(os.getenv('MAX_FILES_TO_ANALYZE', 20))
    MAX_DIFF_SIZE = int(os.getenv('MAX_DIFF_SIZE', 10000))
    PATTERN_ANALYSIS_DEPTH = int(os.getenv('PATTERN_ANALYSIS_DEPTH', 100))  # files to scan
    
    # Database
    # Database - Turso (cloud) or SQLite (local)
    TURSO_DATABASE_URL = os.getenv('TURSO_DATABASE_URL', '')
    TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN', '')
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'patterns.db')  # Fallback for local dev
    
    @staticmethod
    def validate():
        """Validate required configuration"""
        errors = []
        
        if not Config.GITHUB_TOKEN:
            errors.append("GITHUB_TOKEN is required")
        
        if Config.AI_PROVIDER == 'openai' and not Config.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required when using OpenAI")
        elif Config.AI_PROVIDER == 'anthropic' and not Config.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is required when using Anthropic")
        elif Config.AI_PROVIDER == 'custom' and not Config.CUSTOM_AI_ENDPOINT:
            errors.append("CUSTOM_AI_ENDPOINT is required when using custom provider")
        
        return errors
