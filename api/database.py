"""
Database module for storing predictions and enabling real-time sync
Uses SQLite for simplicity (can be upgraded to PostgreSQL for production)
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

DB_PATH = os.getenv("DB_PATH", "predictions.db")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT,
            predictions_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            device_type TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def save_prediction(image_path: str, predictions: Dict, device_type: str = "unknown"):
    """Save prediction to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO predictions (image_path, predictions_json, device_type)
        VALUES (?, ?, ?)
    """, (image_path, json.dumps(predictions), device_type))
    
    conn.commit()
    prediction_id = cursor.lastrowid
    conn.close()
    return prediction_id

def get_latest_predictions(limit: int = 10) -> List[Dict]:
    """Get latest predictions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM predictions
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_prediction_by_id(prediction_id: int) -> Optional[Dict]:
    """Get prediction by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM predictions WHERE id = ?", (prediction_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

# Initialize database on import
init_db()

