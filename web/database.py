"""
SQLite Database Manager for User Authentication
Handles user registration, login tracking, and compliance data storage
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database operations for the authentication system"""
    
    def __init__(self, db_path: str = "app_data.db"):
        """Initialize database connection"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.create_tables()
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def create_tables(self):
        """Create all required database tables"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'Inspector',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Login history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS login_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    device_info TEXT,
                    status TEXT DEFAULT 'success',
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # Compliance checks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    product_title TEXT,
                    product_url TEXT,
                    platform TEXT,
                    compliance_score FLOAT,
                    compliance_status TEXT,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # Crawler history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crawler_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    query TEXT,
                    platform TEXT,
                    products_found INTEGER,
                    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    results_summary TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # Search history table - for heatmap visualization
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    search_query TEXT,
                    platform TEXT,
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    search_count INTEGER DEFAULT 1,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # Image uploads table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_uploads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    filename TEXT,
                    file_size INTEGER,
                    extracted_text TEXT,
                    confidence FLOAT,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_time FLOAT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            # System logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT,
                    message TEXT,
                    user_id INTEGER,
                    action TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            
            conn.commit()
            
            # Run migrations to add new columns to existing tables
            self._run_migrations(cursor)
            conn.commit()
            
            logger.info("Database tables created successfully")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            return False
        finally:
            conn.close()
    
    def _run_migrations(self, cursor):
        """Run database migrations to add new columns to existing tables"""
        try:
            # Check if product_url column exists in compliance_checks table
            cursor.execute("PRAGMA table_info(compliance_checks)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'product_url' not in columns:
                logger.info("Adding product_url column to compliance_checks table")
                cursor.execute("ALTER TABLE compliance_checks ADD COLUMN product_url TEXT")
                logger.info("Migration completed: product_url column added")
        except sqlite3.Error as e:
            logger.error(f"Error running migrations: {e}")
    
    # ==================== USER MANAGEMENT ====================
    
    def register_user(self, username: str, email: str, password: str, role: str = "Inspector") -> Tuple[bool, str]:
        """Register a new user"""
        conn = self.get_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (username, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password, role))
            
            conn.commit()
            user_id = cursor.lastrowid
            self.log_system_action(None, "user_registration", f"New user registered: {username}")
            logger.info(f"User registered: {username}")
            return True, f"User registered successfully with ID: {user_id}"
            
        except sqlite3.IntegrityError as e:
            if "username" in str(e):
                return False, "Username already exists"
            elif "email" in str(e):
                return False, "Email already registered"
            else:
                return False, f"Registration error: {str(e)}"
        except sqlite3.Error as e:
            logger.error(f"Database error during registration: {e}")
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'username': row['username'],
                    'email': row['email'],
                    'password': row['password'],
                    'role': row['role'],
                    'created_at': row['created_at'],
                    'is_active': row['is_active']
                }
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching user: {e}")
            return None
        finally:
            conn.close()
    
    def get_all_users(self) -> List[Dict]:
        """Get all registered users"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, role, created_at FROM users WHERE is_active = 1')
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching users: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== LOGIN TRACKING ====================
    
    def log_login(self, username: str, status: str = "success", ip_address: str = None, device_info: str = None) -> bool:
        """Log user login attempt"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Get user ID
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            user_id = user['id'] if user else None
            
            cursor.execute('''
                INSERT INTO login_history (user_id, username, ip_address, device_info, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, ip_address, device_info, status))
            
            conn.commit()
            logger.info(f"Login logged for user: {username} ({status})")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error logging login: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_login_history(self, username: str, limit: int = 10) -> List[Dict]:
        """Get login history for a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM login_history 
                WHERE username = ? 
                ORDER BY login_time DESC 
                LIMIT ?
            ''', (username, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching login history: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== COMPLIANCE CHECKS ====================
    
    def save_compliance_check(self, user_id: int, username: str, product_title: str, 
                            platform: str, score: float, status: str, details: str = None, product_url: str = None) -> bool:
        """Save compliance check result"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check if product_url column exists
            cursor.execute("PRAGMA table_info(compliance_checks)")
            columns = [column[1] for column in cursor.fetchall()]
            has_product_url = 'product_url' in columns
            
            # Use appropriate INSERT statement based on schema
            if has_product_url:
                cursor.execute('''
                    INSERT INTO compliance_checks 
                    (user_id, username, product_title, product_url, platform, compliance_score, compliance_status, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, product_title, product_url, platform, score, status, details))
            else:
                # Fallback for old schema without product_url
                cursor.execute('''
                    INSERT INTO compliance_checks 
                    (user_id, username, product_title, platform, compliance_score, compliance_status, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, username, product_title, platform, score, status, details))
                logger.warning("product_url column not found, saving without it. Please restart the app to run migrations.")
            
            conn.commit()
            logger.info(f"Compliance check saved for user: {username}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving compliance check: {e}")
            return False
        finally:
            conn.close()
    
    def get_user_compliance_history(self, username: str, limit: int = 20) -> List[Dict]:
        """Get compliance check history for a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM compliance_checks 
                WHERE username = ? 
                ORDER BY checked_at DESC 
                LIMIT ?
            ''', (username, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching compliance history: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== CRAWLER HISTORY ====================
    
    def save_crawler_session(self, user_id: int, username: str, query: str, 
                            platform: str, products_found: int, summary: str = None) -> bool:
        """Save web crawler session"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO crawler_history 
                (user_id, username, query, platform, products_found, results_summary)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, query, platform, products_found, summary))
            
            conn.commit()
            logger.info(f"Crawler session saved for user: {username}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving crawler session: {e}")
            return False
        finally:
            conn.close()
    
    def get_crawler_history(self, username: str, limit: int = 10) -> List[Dict]:
        """Get crawler history for a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM crawler_history 
                WHERE username = ? 
                ORDER BY crawl_time DESC 
                LIMIT ?
            ''', (username, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching crawler history: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== IMAGE UPLOADS ====================
    
    def save_image_upload(self, user_id: int, username: str, filename: str, 
                         file_size: int, extracted_text: str, confidence: float, 
                         processing_time: float) -> bool:
        """Save image upload record"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO image_uploads 
                (user_id, username, filename, file_size, extracted_text, confidence, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, filename, file_size, extracted_text, confidence, processing_time))
            
            conn.commit()
            logger.info(f"Image upload saved for user: {username}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving image upload: {e}")
            return False
        finally:
            conn.close()
    
    def get_upload_history(self, username: str, limit: int = 20) -> List[Dict]:
        """Get image upload history for a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM image_uploads 
                WHERE username = ? 
                ORDER BY uploaded_at DESC 
                LIMIT ?
            ''', (username, limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching upload history: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== SYSTEM LOGS ====================
    
    def log_system_action(self, user_id: Optional[int], action: str, message: str, level: str = "INFO") -> bool:
        """Log system action"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_logs (user_id, action, message, level)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action, message, level))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error logging action: {e}")
            return False
        finally:
            conn.close()
    
    # ==================== STATISTICS ====================
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_active = 1')
            total_users = cursor.fetchone()['count']
            
            # Total logins
            cursor.execute('SELECT COUNT(*) as count FROM login_history')
            total_logins = cursor.fetchone()['count']
            
            # Total compliance checks
            cursor.execute('SELECT COUNT(*) as count FROM compliance_checks')
            total_checks = cursor.fetchone()['count']
            
            # Compliance rate
            cursor.execute('SELECT COUNT(*) as count FROM compliance_checks WHERE compliance_status = "COMPLIANT"')
            compliant_products = cursor.fetchone()['count']
            
            compliance_rate = (compliant_products / total_checks * 100) if total_checks > 0 else 0
            
            # Total images processed
            cursor.execute('SELECT COUNT(*) as count FROM image_uploads')
            total_images = cursor.fetchone()['count']
            
            # Total crawler sessions
            cursor.execute('SELECT COUNT(*) as count FROM crawler_history')
            total_crawls = cursor.fetchone()['count']
            
            return {
                'total_users': total_users,
                'total_logins': total_logins,
                'total_compliance_checks': total_checks,
                'compliant_products': compliant_products,
                'compliance_rate': round(compliance_rate, 2),
                'total_images_processed': total_images,
                'total_crawler_sessions': total_crawls
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching statistics: {e}")
            return {}
        finally:
            conn.close()
    
    def get_user_stats(self, username: str) -> Dict:
        """Get statistics for a specific user"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Get user ID
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if not user:
                return {}
            
            user_id = user['id']
            
            # Login count
            cursor.execute('SELECT COUNT(*) as count FROM login_history WHERE user_id = ?', (user_id,))
            login_count = cursor.fetchone()['count']
            
            # Compliance checks
            cursor.execute('SELECT COUNT(*) as count FROM compliance_checks WHERE user_id = ?', (user_id,))
            check_count = cursor.fetchone()['count']
            
            # Images processed
            cursor.execute('SELECT COUNT(*) as count FROM image_uploads WHERE user_id = ?', (user_id,))
            image_count = cursor.fetchone()['count']
            
            # Crawler sessions
            cursor.execute('SELECT COUNT(*) as count FROM crawler_history WHERE user_id = ?', (user_id,))
            crawler_count = cursor.fetchone()['count']
            
            return {
                'logins': login_count,
                'compliance_checks': check_count,
                'images_processed': image_count,
                'crawler_sessions': crawler_count
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching user stats: {e}")
            return {}
        finally:
            conn.close()
    
    # ==================== SEARCH HISTORY ====================
    
    def log_search(self, user_id: int, username: str, search_query: str, platform: str) -> bool:
        """Log a search query to search history for heatmap visualization"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check if similar search exists for this user in the last hour
            cursor.execute('''
                SELECT id, search_count FROM search_history 
                WHERE user_id = ? AND search_query = ? AND platform = ?
                AND datetime(search_date) > datetime('now', '-1 hour')
                ORDER BY search_date DESC LIMIT 1
            ''', (user_id, search_query, platform))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing search count
                cursor.execute('''
                    UPDATE search_history 
                    SET search_count = ?, search_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (existing['search_count'] + 1, existing['id']))
            else:
                # Insert new search
                cursor.execute('''
                    INSERT INTO search_history (user_id, username, search_query, platform, search_count)
                    VALUES (?, ?, ?, ?, 1)
                ''', (user_id, username, search_query, platform))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error logging search: {e}")
            return False
        finally:
            conn.close()
    
    def get_search_heatmap_data(self, username: str, days: int = 30) -> List[Dict]:
        """Get search history for heatmap visualization"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Get user ID
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if not user:
                return []
            
            user_id = user['id']
            
            # Get search history for the past N days
            cursor.execute('''
                SELECT 
                    search_query,
                    platform,
                    DATE(search_date) as search_date,
                    SUM(search_count) as total_searches,
                    COUNT(*) as unique_searches
                FROM search_history
                WHERE user_id = ?
                AND datetime(search_date) > datetime('now', '-' || ? || ' days')
                GROUP BY search_query, platform, DATE(search_date)
                ORDER BY search_date DESC, total_searches DESC
            ''', (user_id, days))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching search heatmap data: {e}")
            return []
        finally:
            conn.close()
    
    def get_popular_searches(self, username: str, limit: int = 10) -> List[Dict]:
        """Get most popular searches for a user"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Get user ID
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if not user:
                return []
            
            user_id = user['id']
            
            # Get popular searches
            cursor.execute('''
                SELECT 
                    search_query,
                    platform,
                    COUNT(*) as search_count,
                    MAX(search_date) as last_searched
                FROM search_history
                WHERE user_id = ?
                GROUP BY search_query, platform
                ORDER BY search_count DESC
                LIMIT ?
            ''', (user_id, limit))
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
        except sqlite3.Error as e:
            logger.error(f"Error fetching popular searches: {e}")
            return []
        finally:
            conn.close()
    
    def export_user_data(self, username: str) -> Dict:
        """Export all data for a user"""
        return {
            'user_info': self.get_user(username),
            'login_history': self.get_user_login_history(username),
            'compliance_checks': self.get_user_compliance_history(username),
            'crawler_history': self.get_crawler_history(username),
            'upload_history': self.get_upload_history(username),
            'statistics': self.get_user_stats(username)
        }

# Global database instance
db = DatabaseManager()
