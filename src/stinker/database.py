import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects import registry
import libsql_experimental as libsql
# Register libsql dialect manually
registry.register("libsql", "sqlalchemy_libsql.libsql", "SQLiteDialect_libsql")
from stinker.config import Config
from stinker.models import Base, Pattern, Review, RepoConfig, Installation

class Database:
    """SQLAlchemy ORM database for storing codebase patterns and review history"""
    def __init__(self, db_path=None):
        # Determine database URL (Turso cloud or SQLite local)
        if Config.TURSO_DATABASE_URL and Config.TURSO_AUTH_TOKEN:
            # Turso cloud database - use custom creator with https:// URL
            turso_url = Config.TURSO_DATABASE_URL.replace('turso://', '').replace('libsql://', '')
            turso_https_url = f"https://{turso_url}"
            
            # Custom creator function for Turso remote connection
            def creator():
                return libsql.connect(
                    database=turso_https_url,
                    auth_token=Config.TURSO_AUTH_TOKEN
                )
            
            # Use sqlite dialect with custom creator (libsql is SQLite-compatible)
            self.engine = create_engine("libsql:///:memory:", creator=creator, echo=False)
        else:
            # Local SQLite fallback
            self.db_path = db_path or Config.DATABASE_PATH
            database_url = f"sqlite:///{self.db_path}"
            self.engine = create_engine(database_url, echo=False)
            self.engine = create_engine(database_url, echo=False)
        
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.init_db()
    
    def get_connection(self):
        """Get database session (replaces sqlite connection)"""
        return self.SessionLocal()
    
    def init_db(self):
        """Initialize database tables"""
        Base.metadata.create_all(self.engine)
    
    def save_pattern(self, repo_full_name, pattern_type, pattern_name, pattern_data):
        """Save or update a coding pattern"""
        session = self.get_connection()
        try:
            # Check if pattern exists
            existing = session.query(Pattern).filter_by(
                repo_full_name=repo_full_name,
                pattern_type=pattern_type,
                pattern_name=pattern_name
            ).first()
            
            if existing:
                # Update existing pattern
                existing.frequency += 1
                existing.last_seen = datetime.utcnow()
                existing.pattern_data = json.dumps(pattern_data)
            else:
                # Create new pattern
                pattern = Pattern(
                    repo_full_name=repo_full_name,
                    pattern_type=pattern_type,
                    pattern_name=pattern_name,
                    pattern_data=json.dumps(pattern_data),
                    frequency=1,
                    last_seen=datetime.utcnow()
                )
                session.add(pattern)
            
            session.commit()
        finally:
            session.close()
    
    def get_patterns(self, repo_full_name, pattern_type=None):
        """Retrieve patterns for a repository"""
        session = self.get_connection()
        try:
            query = session.query(Pattern).filter_by(repo_full_name=repo_full_name)
            
            if pattern_type:
                query = query.filter_by(pattern_type=pattern_type)
                query = query.order_by(Pattern.frequency.desc(), Pattern.last_seen.desc())
            else:
                query = query.order_by(Pattern.pattern_type, Pattern.frequency.desc())
            
            rows = query.all()
            
            patterns = []
            for row in rows:
                patterns.append({
                    'id': row.id,
                    'pattern_type': row.pattern_type,
                    'pattern_name': row.pattern_name,
                    'pattern_data': json.loads(row.pattern_data),
                    'frequency': row.frequency,
                    'last_seen': row.last_seen.isoformat() if row.last_seen else None
                })
            
            return patterns
        finally:
            session.close()
    
    def save_review(self, repo_full_name, pr_number, review_data):
        """Save PR review results"""
        session = self.get_connection()
        try:
            # Check if review exists
            existing = session.query(Review).filter_by(
                repo_full_name=repo_full_name,
                pr_number=pr_number
            ).first()
            
            if existing:
                # Update existing review
                existing.review_data = json.dumps(review_data)
                existing.created_at = datetime.utcnow()
            else:
                # Create new review
                review = Review(
                    repo_full_name=repo_full_name,
                    pr_number=pr_number,
                    review_data=json.dumps(review_data),
                    status='completed'
                )
                session.add(review)
            
            session.commit()
        finally:
            session.close()
    
    def get_review(self, repo_full_name, pr_number):
        """Get review for a specific PR"""
        session = self.get_connection()
        try:
            row = session.query(Review).filter_by(
                repo_full_name=repo_full_name,
                pr_number=pr_number
            ).first()
            
            if row:
                return {
                    'id': row.id,
                    'repo_full_name': row.repo_full_name,
                    'pr_number': row.pr_number,
                    'review_data': json.loads(row.review_data),
                    'status': row.status,
                    'created_at': row.created_at.isoformat() if row.created_at else None
                }
            return None
        finally:
            session.close()
    
    def get_recent_reviews(self, limit=10):
        """Get recent reviews across all repos"""
        session = self.get_connection()
        try:
            rows = session.query(Review).order_by(
                Review.created_at.desc()
            ).limit(limit).all()
            
            reviews = []
            for row in rows:
                reviews.append({
                    'id': row.id,
                    'repo_full_name': row.repo_full_name,
                    'pr_number': row.pr_number,
                    'review_data': json.loads(row.review_data),
                    'status': row.status,
                    'created_at': row.created_at.isoformat() if row.created_at else None
                })
            
            return reviews
        finally:
            session.close()
    
    def update_repo_config(self, repo_full_name, config_data):
        """Update repository configuration"""
        session = self.get_connection()
        try:
            # Check if config exists
            existing = session.query(RepoConfig).filter_by(
                repo_full_name=repo_full_name
            ).first()
            
            if existing:
                # Update existing config
                existing.config_data = json.dumps(config_data)
                existing.last_analyzed = datetime.utcnow()
            else:
                # Create new config
                config = RepoConfig(
                    repo_full_name=repo_full_name,
                    config_data=json.dumps(config_data),
                    last_analyzed=datetime.utcnow()
                )
                session.add(config)
            
            session.commit()
        finally:
            session.close()
    
    def get_repo_config(self, repo_full_name):
        """Get repository configuration"""
        session = self.get_connection()
        try:
            row = session.query(RepoConfig).filter_by(
                repo_full_name=repo_full_name
            ).first()
            
            if row:
                return {
                    'repo_full_name': row.repo_full_name,
                    'config_data': json.loads(row.config_data),
                    'last_analyzed': row.last_analyzed.isoformat() if row.last_analyzed else None
                }
            return None
        finally:
            session.close()

    # Installation Management Methods
    
    def save_installation(self, installation_data):
        """
        Save or update a GitHub App installation.
        
        Args:
            installation_data: Dict containing installation details
                - installation_id (required)
                - account_id (required)
                - account_login (required)
                - account_type (required)
                - target_type (required)
                - repositories (optional, list of repo names)
                - repository_selection (optional)
                - permissions (optional)
                - events (optional)
                - suspended_at (optional)
                - suspended_by (optional)
        
        Returns:
            The saved Installation object
        """
        session = self.get_connection()
        try:
            installation = session.query(Installation).filter_by(
                installation_id=installation_data['installation_id']
            ).first()
            
            if installation:
                # Update existing installation
                installation.account_id = installation_data['account_id']
                installation.account_login = installation_data['account_login']
                installation.account_type = installation_data['account_type']
                installation.target_type = installation_data['target_type']
                installation.repositories = json.dumps(installation_data.get('repositories', []))
                installation.repository_selection = installation_data.get('repository_selection', 'all')
                installation.permissions = json.dumps(installation_data.get('permissions', {}))
                installation.event_types = json.dumps(installation_data.get('events', []))
                
                if installation_data.get('suspended_at'):
                    suspended_val = installation_data['suspended_at']
                    installation.suspended_at = datetime.fromisoformat(suspended_val.replace('Z', '+00:00')) if isinstance(suspended_val, str) else suspended_val
                    suspended_by_val = installation_data.get('suspended_by')
                    installation.suspended_by = json.dumps(suspended_by_val) if isinstance(suspended_by_val, dict) else suspended_by_val
                else:
                    installation.suspended_at = None
                    installation.suspended_by = None
                    
                installation.updated_at = datetime.utcnow()
            else:
                # Create new installation
                installation = Installation(
                    installation_id=installation_data['installation_id'],
                    account_id=installation_data['account_id'],
                    account_login=installation_data['account_login'],
                    account_type=installation_data['account_type'],
                    target_type=installation_data['target_type'],
                    repositories=json.dumps(installation_data.get('repositories', [])),
                    repository_selection=installation_data.get('repository_selection', 'all'),
                    permissions=json.dumps(installation_data.get('permissions', {})),
                    event_types=json.dumps(installation_data.get('events', [])),
                    suspended_at=datetime.fromisoformat(installation_data.get('suspended_at').replace('Z', '+00:00')) if installation_data.get('suspended_at') and isinstance(installation_data.get('suspended_at'), str) else installation_data.get('suspended_at'),
                    suspended_by=json.dumps(installation_data.get('suspended_by')) if isinstance(installation_data.get('suspended_by'), dict) else installation_data.get('suspended_by')
                )
                session.add(installation)
            
            session.commit()
            return installation
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_installation(self, installation_id):
        """
        Retrieve an installation by installation_id.
        
        Args:
            installation_id: GitHub App installation ID
            
        Returns:
            Dict with installation details or None
        """
        session = self.get_connection()
        try:
            installation = session.query(Installation).filter_by(
                installation_id=installation_id
            ).first()
            
            if installation:
                return {
                    'installation_id': installation.installation_id,
                    'account_id': installation.account_id,
                    'account_login': installation.account_login,
                    'account_type': installation.account_type,
                    'target_type': installation.target_type,
                    'repositories': json.loads(installation.repositories),
                    'repository_selection': installation.repository_selection,
                    'permissions': json.loads(installation.permissions),
                    'events': json.loads(installation.event_types),
                    'suspended_at': installation.suspended_at.isoformat() if installation.suspended_at else None,
                    'suspended_by': json.loads(installation.suspended_by) if installation.suspended_by and installation.suspended_by.startswith('{') else installation.suspended_by,
                    'created_at': installation.created_at.isoformat(),
                    'updated_at': installation.updated_at.isoformat()
                }
            return None
        finally:
            session.close()
    
    def get_installation_by_account(self, account_id):
        """
        Retrieve an installation by account_id.
        
        Args:
            account_id: GitHub account ID
            
        Returns:
            Dict with installation details or None
        """
        session = self.get_connection()
        try:
            installation = session.query(Installation).filter_by(
                account_id=account_id
            ).first()
            
            if installation:
                return {
                    'installation_id': installation.installation_id,
                    'account_id': installation.account_id,
                    'account_login': installation.account_login,
                    'account_type': installation.account_type,
                    'target_type': installation.target_type,
                    'repositories': json.loads(installation.repositories),
                    'repository_selection': installation.repository_selection,
                    'permissions': json.loads(installation.permissions),
                    'events': json.loads(installation.event_types),
                    'suspended_at': installation.suspended_at.isoformat() if installation.suspended_at else None,
                    'suspended_by': json.loads(installation.suspended_by) if installation.suspended_by and installation.suspended_by.startswith('{') else installation.suspended_by,
                    'created_at': installation.created_at.isoformat(),
                    'updated_at': installation.updated_at.isoformat()
                }
            return None
        finally:
            session.close()
    
    def delete_installation(self, installation_id):
        """
        Delete an installation.
        
        Args:
            installation_id: GitHub App installation ID
            
        Returns:
            True if deleted, False if not found
        """
        session = self.get_connection()
        try:
            installation = session.query(Installation).filter_by(
                installation_id=installation_id
            ).first()
            
            if installation:
                session.delete(installation)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def list_installations(self, active_only=True):
        """
        List all installations.
        
        Args:
            active_only: If True, only return non-suspended installations
            
        Returns:
            List of installation dicts
        """
        session = self.get_connection()
        try:
            query = session.query(Installation)
            
            if active_only:
                query = query.filter(Installation.suspended_at.is_(None))
            
            installations = query.order_by(Installation.created_at.desc()).all()
            
            return [{
                'installation_id': inst.installation_id,
                'account_id': inst.account_id,
                'account_login': inst.account_login,
                'account_type': inst.account_type,
                'target_type': inst.target_type,
                'repositories': json.loads(inst.repositories),
                'repository_selection': inst.repository_selection,
                'permissions': json.loads(inst.permissions),
                'events': json.loads(inst.event_types),
                'suspended_at': inst.suspended_at.isoformat() if inst.suspended_at else None,
                'suspended_by': json.loads(inst.suspended_by) if inst.suspended_by and inst.suspended_by.startswith('{') else inst.suspended_by,
                'created_at': inst.created_at.isoformat(),
                'updated_at': inst.updated_at.isoformat()
            } for inst in installations]
        finally:
            session.close()
