import sqlite3
import json
from datetime import datetime
from stinker.config import Config

class Database:
    """SQLite database for storing codebase patterns and review history"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Patterns table - stores learned coding patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_full_name TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                pattern_name TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(repo_full_name, pattern_type, pattern_name)
            )
        ''')
        
        # Reviews table - stores PR review history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_full_name TEXT NOT NULL,
                pr_number INTEGER NOT NULL,
                review_data TEXT NOT NULL,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(repo_full_name, pr_number)
            )
        ''')
        
        # Repository configs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repo_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_full_name TEXT UNIQUE NOT NULL,
                config_data TEXT NOT NULL,
                last_analyzed TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_pattern(self, repo_full_name, pattern_type, pattern_name, pattern_data):
        """Save or update a coding pattern"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO patterns (repo_full_name, pattern_type, pattern_name, pattern_data, frequency, last_seen)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(repo_full_name, pattern_type, pattern_name) 
            DO UPDATE SET 
                frequency = frequency + 1,
                last_seen = CURRENT_TIMESTAMP,
                pattern_data = excluded.pattern_data
        ''', (repo_full_name, pattern_type, pattern_name, json.dumps(pattern_data)))
        
        conn.commit()
        conn.close()
    
    def get_patterns(self, repo_full_name, pattern_type=None):
        """Retrieve patterns for a repository"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if pattern_type:
            cursor.execute('''
                SELECT * FROM patterns 
                WHERE repo_full_name = ? AND pattern_type = ?
                ORDER BY frequency DESC, last_seen DESC
            ''', (repo_full_name, pattern_type))
        else:
            cursor.execute('''
                SELECT * FROM patterns 
                WHERE repo_full_name = ?
                ORDER BY pattern_type, frequency DESC
            ''', (repo_full_name,))
        
        rows = cursor.fetchall()
        conn.close()
        
        patterns = []
        for row in rows:
            patterns.append({
                'id': row['id'],
                'pattern_type': row['pattern_type'],
                'pattern_name': row['pattern_name'],
                'pattern_data': json.loads(row['pattern_data']),
                'frequency': row['frequency'],
                'last_seen': row['last_seen']
            })
        
        return patterns
    
    def save_review(self, repo_full_name, pr_number, review_data):
        """Save PR review results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reviews (repo_full_name, pr_number, review_data)
            VALUES (?, ?, ?)
            ON CONFLICT(repo_full_name, pr_number)
            DO UPDATE SET 
                review_data = excluded.review_data,
                created_at = CURRENT_TIMESTAMP
        ''', (repo_full_name, pr_number, json.dumps(review_data)))
        
        conn.commit()
        conn.close()
    
    def get_review(self, repo_full_name, pr_number):
        """Get review for a specific PR"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM reviews 
            WHERE repo_full_name = ? AND pr_number = ?
        ''', (repo_full_name, pr_number))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'repo_full_name': row['repo_full_name'],
                'pr_number': row['pr_number'],
                'review_data': json.loads(row['review_data']),
                'status': row['status'],
                'created_at': row['created_at']
            }
        return None
    
    def get_recent_reviews(self, limit=10):
        """Get recent reviews across all repos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM reviews 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        reviews = []
        for row in rows:
            reviews.append({
                'id': row['id'],
                'repo_full_name': row['repo_full_name'],
                'pr_number': row['pr_number'],
                'review_data': json.loads(row['review_data']),
                'status': row['status'],
                'created_at': row['created_at']
            })
        
        return reviews
    
    def update_repo_config(self, repo_full_name, config_data):
        """Update repository configuration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO repo_configs (repo_full_name, config_data, last_analyzed)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(repo_full_name)
            DO UPDATE SET 
                config_data = excluded.config_data,
                last_analyzed = CURRENT_TIMESTAMP
        ''', (repo_full_name, json.dumps(config_data)))
        
        conn.commit()
        conn.close()
    
    def get_repo_config(self, repo_full_name):
        """Get repository configuration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM repo_configs 
            WHERE repo_full_name = ?
        ''', (repo_full_name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'repo_full_name': row['repo_full_name'],
                'config_data': json.loads(row['config_data']),
                'last_analyzed': row['last_analyzed']
            }
        return None
