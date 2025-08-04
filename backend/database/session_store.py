"""SQLite-based session storage for persistence across restarts"""
import sqlite3
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

class SQLiteSessionStore:
    """Simple SQLite-based session storage"""
    
    def __init__(self, db_path: str = "./data/sessions.db"):
        """Initialize the session store with the given database path"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT,
            conversation_id TEXT,
            created_at TEXT,
            updated_at TEXT,
            message_count INTEGER,
            execution_started INTEGER DEFAULT 0,
            approved_at TEXT,
            data TEXT
        )
        ''')
        
        # Create messages table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"SQLite session store initialized at {self.db_path}")
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """Save or update a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract basic session data
        user_id = session_data.get("user_id", "")
        conversation_id = session_data.get("conversation_id", "")
        created_at = session_data.get("created_at", datetime.now().isoformat())
        updated_at = datetime.now().isoformat()
        message_count = session_data.get("message_count", 0)
        execution_started = 1 if session_data.get("execution_started", False) else 0
        approved_at = session_data.get("approved_at", None)
        
        # Store messages separately
        messages = session_data.get("messages", [])
        
        # Remove messages from data to avoid duplication
        session_data_copy = session_data.copy()
        if "messages" in session_data_copy:
            del session_data_copy["messages"]
        
        # Convert remaining data to JSON
        data_json = json.dumps(session_data_copy)
        
        # Insert or update session
        cursor.execute('''
        INSERT OR REPLACE INTO sessions 
        (session_id, user_id, conversation_id, created_at, updated_at, 
         message_count, execution_started, approved_at, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, user_id, conversation_id, created_at, updated_at, 
              message_count, execution_started, approved_at, data_json))
        
        # Delete existing messages for this session
        cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        
        # Insert messages
        for msg in messages:
            cursor.execute('''
            INSERT INTO messages (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
            ''', (session_id, msg.get("role", ""), msg.get("content", ""), 
                  msg.get("timestamp", datetime.now().isoformat())))
        
        conn.commit()
        conn.close()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get session data
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session_row = cursor.fetchone()
        
        if not session_row:
            conn.close()
            return None
        
        # Convert to dict
        session = dict(session_row)
        
        # Parse JSON data
        session_data = json.loads(session["data"])
        
        # Get messages
        cursor.execute('SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id', 
                      (session_id,))
        messages = [dict(row) for row in cursor.fetchall()]
        
        # Combine data
        result = {
            **session_data,
            "session_id": session["session_id"],
            "user_id": session["user_id"],
            "conversation_id": session["conversation_id"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "message_count": session["message_count"],
            "execution_started": bool(session["execution_started"]),
            "messages": messages
        }
        
        if session["approved_at"]:
            result["approved_at"] = session["approved_at"]
        
        conn.close()
        return result
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions (basic info only)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT session_id, user_id, conversation_id, created_at, updated_at, 
               message_count, execution_started 
        FROM sessions
        ORDER BY updated_at DESC
        ''')
        
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Convert execution_started to boolean
        for session in sessions:
            session["execution_started"] = bool(session["execution_started"])
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete messages first (foreign key constraint)
        cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        
        # Delete session
        cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted

# Global instance
session_store = SQLiteSessionStore()