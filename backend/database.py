"""Database initialization and connection for BharatVision"""
import sqlite3
from datetime import datetime
from pathlib import Path
import json

class Database:
    """SQLite database for BharatVision validation results"""
    
    def __init__(self, db_path: str = "bharatvision.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Validation results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                status TEXT NOT NULL,
                compliance_score REAL NOT NULL,
                present_items TEXT,
                missing_items TEXT,
                flagged_items TEXT,
                ocr_text TEXT,
                image_path TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Compliance issues table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                validation_id INTEGER NOT NULL,
                issue_type TEXT NOT NULL,
                issue_name TEXT NOT NULL,
                issue_description TEXT,
                severity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (validation_id) REFERENCES validation_results(id)
            )
        ''')
        
        # OCR extractions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ocr_extractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                validation_id INTEGER NOT NULL,
                extracted_text TEXT,
                confidence_score REAL,
                extracted_fields TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (validation_id) REFERENCES validation_results(id)
            )
        ''')
        
        # Images table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                validation_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                image_size INTEGER,
                image_format TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (validation_id) REFERENCES validation_results(id)
            )
        ''')
        
        # Statistics cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_validations INTEGER,
                compliant_count INTEGER,
                non_compliant_count INTEGER,
                average_score REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Database initialized at {self.db_path}")
    
    def save_validation_result(self, validation_data: dict) -> int:
        """Save validation result to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO validation_results 
            (product_name, status, compliance_score, present_items, 
             missing_items, flagged_items, ocr_text, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            validation_data.get('product_name', 'Unknown'),
            validation_data.get('status', 'unknown'),
            validation_data.get('compliance_score', 0),
            json.dumps(validation_data.get('present_items', {})),
            json.dumps(validation_data.get('missing_items', {})),
            json.dumps(validation_data.get('flagged_items', {})),
            validation_data.get('ocr_text', ''),
            validation_data.get('image_path', '')
        ))
        
        result_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_validation_result(self, result_id: int) -> dict:
        """Get validation result by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM validation_results WHERE id = ?', (result_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'product_name': row['product_name'],
                'status': row['status'],
                'compliance_score': row['compliance_score'],
                'present_items': json.loads(row['present_items']) if row['present_items'] else {},
                'missing_items': json.loads(row['missing_items']) if row['missing_items'] else {},
                'flagged_items': json.loads(row['flagged_items']) if row['flagged_items'] else {},
                'ocr_text': row['ocr_text'],
                'image_path': row['image_path'],
                'upload_date': row['upload_date']
            }
        return None
    
    def get_all_validation_results(self, limit: int = 50, offset: int = 0) -> list:
        """Get all validation results with pagination"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, product_name, status, compliance_score, upload_date 
            FROM validation_results 
            ORDER BY upload_date DESC 
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_statistics(self) -> dict:
        """Get validation statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'compliant' THEN 1 ELSE 0 END) as compliant,
                SUM(CASE WHEN status = 'non-compliant' THEN 1 ELSE 0 END) as non_compliant,
                AVG(compliance_score) as avg_score
            FROM validation_results
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        return {
            'total_validations': row['total'] or 0,
            'compliant_count': row['compliant'] or 0,
            'non_compliant_count': row['non_compliant'] or 0,
            'average_score': round(row['avg_score'], 2) if row['avg_score'] else 0
        }
    
    def save_compliance_issue(self, validation_id: int, issue_data: dict) -> int:
        """Save compliance issue"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO compliance_issues 
            (validation_id, issue_type, issue_name, issue_description, severity)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            validation_id,
            issue_data.get('issue_type', 'unknown'),
            issue_data.get('issue_name', ''),
            issue_data.get('issue_description', ''),
            issue_data.get('severity', 'medium')
        ))
        
        issue_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return issue_id
    
    def delete_validation_result(self, result_id: int) -> bool:
        """Delete validation result"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM validation_results WHERE id = ?', (result_id,))
        cursor.execute('DELETE FROM compliance_issues WHERE validation_id = ?', (result_id,))
        cursor.execute('DELETE FROM ocr_extractions WHERE validation_id = ?', (result_id,))
        cursor.execute('DELETE FROM validation_images WHERE validation_id = ?', (result_id,))
        
        conn.commit()
        conn.close()
        
        return True

    def save_compliance_check(self, user_id: int, username: str, product_title: str, 
                              platform: str, score: float, status: str, details: str) -> int:
        """Save compliance check result from crawler"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create compliance_checks table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                product_title TEXT,
                platform TEXT,
                score REAL,
                status TEXT,
                details TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO compliance_checks 
            (user_id, username, product_title, platform, score, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, product_title, platform, score, status, details))
        
        check_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return check_id

    def get_compliance_history(self, limit: int = 100) -> list:
        """Get compliance check history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                product_title TEXT,
                platform TEXT,
                score REAL,
                status TEXT,
                details TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            SELECT * FROM compliance_checks 
            ORDER BY checked_at DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_platform_analytics(self) -> dict:
        """Get analytics per platform"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS compliance_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                product_title TEXT,
                platform TEXT,
                score REAL,
                status TEXT,
                details TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            SELECT 
                platform,
                COUNT(*) as total,
                AVG(score) as avg_score,
                SUM(CASE WHEN status = 'COMPLIANT' THEN 1 ELSE 0 END) as compliant,
                SUM(CASE WHEN status = 'PARTIAL' THEN 1 ELSE 0 END) as partial,
                SUM(CASE WHEN status = 'NON-COMPLIANT' THEN 1 ELSE 0 END) as non_compliant
            FROM compliance_checks
            GROUP BY platform
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def log_search(self, user_id: int, username: str, search_query: str, platform: str) -> int:
        """Log search query for analytics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                search_query TEXT,
                platform TEXT,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT INTO search_logs (user_id, username, search_query, platform)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, search_query, platform))
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return log_id

# Initialize database instance
db = Database()
