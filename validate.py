#!/usr/bin/env python3
"""Validation script to check AI Code Review Bot installation"""

import os
import sys
from pathlib import Path

# Add src directory to Python path for kiss package imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))


def check_files():
    """Check if all required files exist"""
    print("📁 Checking file structure...")
    
    required_files = [
        'app.py',
        'src/kiss/__init__.py',
        'src/kiss/config.py',
        'src/kiss/database.py',
        'src/kiss/github_client.py',
        'src/kiss/diff_parser.py',
        'src/kiss/pattern_analyzer.py',
        'src/kiss/ai_engine.py',
        'src/kiss/utils.py',
        'requirements.txt',
        '.env',
        '.env.example',
        'README.md',
        'setup.sh',
        'templates/index.html',
        'templates/config.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
            print(f"   ❌ {file}")
        else:
            print(f"   ✅ {file}")
    
    if missing:
        print(f"\n❌ Missing {len(missing)} files: {missing}")
        return False
    
    print("\n✅ All required files present\n")
    return True

def check_config():
    """Check configuration"""
    print("⚙️  Checking configuration...")
    
    from kiss.config import Config
    
    checks = {
        'Flask Secret Key': Config.SECRET_KEY != 'dev-secret-key-change-in-production',
        'GitHub Token': bool(Config.GITHUB_TOKEN),
        'Webhook Secret': bool(Config.GITHUB_WEBHOOK_SECRET),
        'AI Provider': Config.AI_PROVIDER in ['openai', 'anthropic', 'custom']
    }
    
    for check, passed in checks.items():
        status = '✅' if passed else '⚠️ '
        print(f"   {status} {check}")
    
    if not all(checks.values()):
        print("\n⚠️  Some configuration values need to be set in .env file")
    else:
        print("\n✅ Configuration looks good\n")
    
    return True

def check_database():
    """Check database"""
    print("💾 Checking database...")
    
    from kiss.database import Database
    
    try:
        db = Database()
        print("   ✅ Database connection successful")
        print(f"   ✅ Database path: {db.db_path}\n")
        return True
    except Exception as e:
        print(f"   ❌ Database error: {e}\n")
        return False

def check_modules():
    """Check all modules can be imported"""
    print("📦 Checking module imports...")
    
    modules = [
        ('app', 'Flask application'),
        ('kiss.config', 'Configuration'),
        ('kiss.database', 'Database layer'),
        ('kiss.github_client', 'GitHub client'),
        ('kiss.diff_parser', 'Diff parser'),
        ('kiss.pattern_analyzer', 'Pattern analyzer'),
        ('kiss.ai_engine', 'AI engine'),
        ('kiss.utils', 'Utilities')
    ]
    
    failed = []
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"   ✅ {description} ({module_name}.py)")
        except Exception as e:
            print(f"   ❌ {description} ({module_name}.py): {e}")
            failed.append(module_name)
    
    if failed:
        print(f"\n❌ Failed to import: {failed}\n")
        return False
    
    print("\n✅ All modules imported successfully\n")
    return True

def check_routes():
    """Check Flask routes"""
    print("🛣️  Checking Flask routes...")
    
    from app import app
    
    expected_routes = [
        '/',
        '/config',
        '/webhook',
        '/api/review',
        '/api/analyze-repo',
        '/api/health'
    ]
    
    registered_routes = [rule.rule for rule in app.url_map.iter_rules() if rule.rule != '/static/<path:filename>']
    
    for route in expected_routes:
        if route in registered_routes:
            print(f"   ✅ {route}")
        else:
            print(f"   ❌ {route}")
    
    print(f"\n   Total routes: {len(registered_routes)}")
    print("✅ Flask routes registered\n")
    return True

def main():
    """Run all validation checks"""
    print("=" * 50)
    print("AI Code Review Bot - Validation")
    print("=" * 50)
    print()
    
    checks = [
        check_files(),
        check_modules(),
        check_database(),
        check_config(),
        check_routes()
    ]
    
    print("=" * 50)
    if all(checks):
        print("✅ All validation checks passed!")
        print("\nYou can now start the application:")
        print("  source venv/bin/activate")
        print("  python3 app.py")
    else:
        print("⚠️  Some validation checks failed")
        print("\nPlease fix the issues above before starting the application")
        sys.exit(1)
    print("=" * 50)

if __name__ == '__main__':
    main()
