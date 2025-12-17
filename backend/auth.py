from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
import os
from functools import wraps

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

# User background model
class UserBackground(BaseModel):
    software_experience: str
    hardware_experience: str
    user_id: str

class UserSignup(BaseModel):
    email: str
    password: str
    software_experience: str
    hardware_experience: str

class UserSignin(BaseModel):
    email: str
    password: str

def get_db_connection():
    """Get database connection"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{hashed}:{salt}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    stored_hash, salt = hashed.split(':')
    computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return computed_hash == stored_hash

def init_auth_tables():
    """Initialize auth-related tables in the database"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Create users table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(255) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create user_profiles table for storing background info
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
            software_experience TEXT,
            hardware_experience TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create user_preferences table for personalization
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE,
            chapter_id VARCHAR(255),
            language_preference VARCHAR(10) DEFAULT 'en',
            difficulty_level INTEGER DEFAULT 2,  -- 1=easy, 2=medium, 3=hard
            hide_advanced_examples BOOLEAN DEFAULT FALSE,
            hide_code_examples BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()

def save_user_background(user_id: str, software_exp: str, hardware_exp: str):
    """Save user background information"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO user_profiles (user_id, software_experience, hardware_experience)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            software_experience = EXCLUDED.software_experience,
            hardware_experience = EXCLUDED.hardware_experience,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, software_exp, hardware_exp))

    conn.commit()
    cur.close()
    conn.close()

def get_user_background(user_id: str):
    """Get user background information"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT software_experience, hardware_experience
        FROM user_profiles
        WHERE user_id = %s
    """, (user_id,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    return result

def save_user_preference(user_id: str, chapter_id: str, language: str = 'en', difficulty: int = 2,
                        hide_advanced: bool = False, hide_code: bool = False):
    """Save user preference for a specific chapter"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO user_preferences (
            user_id, chapter_id, language_preference, difficulty_level,
            hide_advanced_examples, hide_code_examples
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, chapter_id)
        DO UPDATE SET
            language_preference = EXCLUDED.language_preference,
            difficulty_level = EXCLUDED.difficulty_level,
            hide_advanced_examples = EXCLUDED.hide_advanced_examples,
            hide_code_examples = EXCLUDED.hide_code_examples,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, chapter_id, language, difficulty, hide_advanced, hide_code))

    conn.commit()
    cur.close()
    conn.close()

def get_user_preference(user_id: str, chapter_id: str):
    """Get user preference for a specific chapter"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT language_preference, difficulty_level, hide_advanced_examples, hide_code_examples
        FROM user_preferences
        WHERE user_id = %s AND chapter_id = %s
    """, (user_id, chapter_id))

    result = cur.fetchone()
    cur.close()
    conn.close()

    return result

def create_session_token(user_id: str) -> str:
    """Create a session token for the user"""
    token = secrets.token_urlsafe(32)
    # In a real implementation, you'd store this in a sessions table
    # For now, we'll just return it and handle session management differently
    return token

def authenticate_user(email: str, password: str):
    """Authenticate user and return user info if successful"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    if user and verify_password(password, user['password_hash']):
        cur.close()
        conn.close()
        return {'id': user['id'], 'email': user['email']}

    cur.close()
    conn.close()
    return None

def get_user_by_email(email: str):
    """Get user by email"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, email FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

    cur.close()
    conn.close()
    return user

def translate_to_urdu(text: str) -> str:
    """
    Translate text to Urdu using a translation API.
    This implementation uses the Google Translate API via the googletrans library.
    """
    try:
        # Import here to avoid dependency issues if not needed
        from googletrans import Translator

        translator = Translator()
        result = translator.translate(text, src='en', dest='ur')
        return result.text
    except ImportError:
        # Fallback if googletrans is not installed
        # You can install it with: pip install googletrans==4.0.0-rc1
        print("googletrans not installed. Install with: pip install googletrans==4.0.0-rc1")
        return text
    except Exception as e:
        print(f"Translation error: {str(e)}")
        # Return original text if translation fails
        return text

# Initialize the auth tables
init_auth_tables()