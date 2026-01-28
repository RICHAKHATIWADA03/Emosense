"""Database setup for PostgreSQL with user authentication and analysis history"""
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
import json
from datetime import datetime, timedelta
import hashlib
import config

def get_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=config.POSTGRES_CONFIG['host'],
        port=config.POSTGRES_CONFIG['port'],
        database=config.POSTGRES_CONFIG['database'],
        user=config.POSTGRES_CONFIG['user'],
        password=config.POSTGRES_CONFIG['password']
    )

def init_database():
    """Initialize the PostgreSQL database with tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                subscription_tier VARCHAR(50) DEFAULT 'free',
                subscription_start TIMESTAMP,
                subscription_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Analysis history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                analysis_type VARCHAR(50) NOT NULL,
                file_name TEXT,
                file_size BIGINT DEFAULT 0,
                duration REAL DEFAULT 0,
                predicted_emotion VARCHAR(50),
                confidence REAL,
                transcript TEXT,
                results_json JSONB,
                metrics_json JSONB,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Payment history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                amount REAL NOT NULL,
                currency VARCHAR(10) DEFAULT 'USD',
                payment_method VARCHAR(50),
                transaction_id VARCHAR(255),
                status VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_history ON analysis_history(user_id, created_at DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscription ON users(subscription_tier, subscription_end)')
        
        conn.commit()
        print("✅ PostgreSQL database initialized")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def hash_password(password):
    """Hash password with SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, email, password):
    """Create a new user with free tier"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, subscription_tier)
            VALUES (%s, %s, %s, 'free')
            RETURNING id
        ''', (username, email, password_hash))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return True, user_id
    except psycopg2.IntegrityError as e:
        return False, "Username or email already exists"
    except Exception as e:
        return False, str(e)

def verify_user(username, password):
    """Verify user credentials"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    password_hash = hash_password(password)
    
    try:
        cursor.execute('''
            SELECT id, username, email, subscription_tier, subscription_end 
            FROM users 
            WHERE username = %s AND password_hash = %s
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (user['id'],))
            conn.commit()
            
            # Check if subscription expired
            subscription_tier = user['subscription_tier'] or 'free'
            
            if subscription_tier == 'premium' and user['subscription_end']:
                if user['subscription_end'] < datetime.now():
                    # Downgrade to free
                    cursor.execute('UPDATE users SET subscription_tier = %s WHERE id = %s', 
                                 ('free', user['id']))
                    conn.commit()
                    subscription_tier = 'free'
            
            cursor.close()
            conn.close()
            
            return True, {
                'id': user['id'], 
                'username': user['username'], 
                'email': user['email'],
                'subscription_tier': subscription_tier,
                'subscription_end': user['subscription_end'].isoformat() if user['subscription_end'] else None
            }
        
        cursor.close()
        conn.close()
        return False, None
        
    except Exception as e:
        print(f"Login error: {e}")
        cursor.close()
        conn.close()
        return False, None

def upgrade_to_premium(user_id, duration_days=30):
    """Upgrade user to premium"""
    conn = get_connection()
    cursor = conn.cursor()
    
    start_date = datetime.now()
    end_date = start_date + timedelta(days=duration_days)
    
    cursor.execute('''
        UPDATE users 
        SET subscription_tier = %s,
            subscription_start = %s,
            subscription_end = %s
        WHERE id = %s
    ''', ('premium', start_date, end_date, user_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def record_payment(user_id, amount, payment_method, transaction_id):
    """Record a payment"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO payment_history 
        (user_id, amount, payment_method, transaction_id, status)
        VALUES (%s, %s, %s, %s, 'completed')
    ''', (user_id, amount, payment_method, transaction_id))
    
    conn.commit()
    cursor.close()
    conn.close()

def save_analysis(user_id, analysis_type, file_name, results, metrics, file_size=0, duration=0):
    """Save analysis to history with file path"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get file path from results
        file_path = None
        if 'video_path' in results:
            file_path = str(results['video_path'])
        elif 'audio_path' in results:
            file_path = str(results['audio_path'])
        
        cursor.execute('''
            INSERT INTO analysis_history 
            (user_id, analysis_type, file_name, file_size, duration,
             predicted_emotion, confidence, transcript, results_json, metrics_json, file_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            user_id,
            analysis_type,
            file_name,
            file_size,
            duration,
            results.get('fusion', {}).get('predicted_emotion', results.get('combined', {}).get('predicted_emotion', 'unknown')),
            results.get('fusion', {}).get('confidence', results.get('combined', {}).get('confidence', 0)),
            results.get('transcript', {}).get('text', ''),
            json.dumps(results, default=str),
            json.dumps(metrics, default=str),
            file_path
        ))
        
        analysis_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return True, analysis_id
    except Exception as e:
        print(f"Save analysis error: {e}")
        return False, str(e)

def get_user_history(user_id, limit=50):
    """Get analysis history for a user"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT id, analysis_type, file_name, predicted_emotion, confidence,
               created_at, metrics_json, duration, file_size, file_path
        FROM analysis_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    ''', (user_id, limit))
    
    history = []
    for row in cursor.fetchall():
        history.append({
            'id': row['id'],
            'type': row['analysis_type'],
            'file_name': row['file_name'],
            'emotion': row['predicted_emotion'],
            'confidence': row['confidence'],
            'date': row['created_at'].isoformat(),
            'metrics': row['metrics_json'] or {},
            'duration': row['duration'] or 0,
            'file_size': row['file_size'] or 0,
            'file_path': row['file_path']
        })
    
    cursor.close()
    conn.close()
    return history

def get_analysis_by_id(analysis_id, user_id):
    """Get a specific analysis by ID"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT results_json, metrics_json, created_at, file_path, analysis_type
        FROM analysis_history
        WHERE id = %s AND user_id = %s
    ''', (analysis_id, user_id))
    
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if row:
        return {
            'results': row['results_json'],
            'metrics': row['metrics_json'],
            'date': row['created_at'].isoformat(),
            'file_path': row['file_path'],
            'analysis_type': row['analysis_type']
        }
    return None

def get_user_stats(user_id):
    """Get statistics for a user"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Total analyses
    cursor.execute('SELECT COUNT(*) as count FROM analysis_history WHERE user_id = %s', (user_id,))
    total = cursor.fetchone()['count']
    
    # Emotion distribution
    cursor.execute('''
        SELECT predicted_emotion, COUNT(*) as count
        FROM analysis_history
        WHERE user_id = %s
        GROUP BY predicted_emotion
        ORDER BY count DESC
    ''', (user_id,))
    emotion_dist = {row['predicted_emotion']: row['count'] for row in cursor.fetchall()}
    
    # Average confidence
    cursor.execute('''
        SELECT AVG(confidence) as avg_conf FROM analysis_history WHERE user_id = %s
    ''', (user_id,))
    avg_confidence = cursor.fetchone()['avg_conf'] or 0
    
    # Total duration analyzed
    cursor.execute('''
        SELECT SUM(duration) as total_dur FROM analysis_history WHERE user_id = %s
    ''', (user_id,))
    total_duration = cursor.fetchone()['total_dur'] or 0
    
    cursor.close()
    conn.close()
    
    return {
        'total_analyses': total,
        'emotion_distribution': emotion_dist,
        'average_confidence': float(avg_confidence),
        'total_duration': float(total_duration)
    }

def delete_analysis(analysis_id, user_id):
    """Delete an analysis"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM analysis_history
        WHERE id = %s AND user_id = %s
    ''', (analysis_id, user_id))
    
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    
    return deleted > 0

def check_subscription_limits(user_id):
    """Check if user has reached their subscription limits"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get subscription tier
    cursor.execute('SELECT subscription_tier FROM users WHERE id = %s', (user_id,))
    row = cursor.fetchone()
    tier = row['subscription_tier'] if row else 'free'
    
    if tier == 'premium':
        cursor.close()
        conn.close()
        return True, 'unlimited'
    
    # Free tier: check history count (limit 10)
    cursor.execute('SELECT COUNT(*) as count FROM analysis_history WHERE user_id = %s', (user_id,))
    count = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    if count >= 10:
        return False, 'history_limit'
    
    return True, 'ok'

# Initialize database on import
init_database()
