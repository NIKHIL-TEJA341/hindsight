import sqlite3
import uuid
from datetime import datetime

DB_FILE = "chats.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id)
        )
    ''')
    conn.commit()
    conn.close()

def create_conversation(user_id, title="New Chat"):
    conv_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = get_connection()
    conn.execute(
        "INSERT INTO conversations (conversation_id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (conv_id, user_id, title, now, now)
    )
    conn.commit()
    conn.close()
    return conv_id

def get_conversations(user_id):
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC", 
        (user_id,)
    )
    convs = cursor.fetchall()
    conn.close()
    return [dict(c) for c in convs]

def add_message(conversation_id, role, content):
    msg_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (message_id, conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
        (msg_id, conversation_id, role, content, now)
    )
    conn.execute(
        "UPDATE conversations SET updated_at = ?, title = ? WHERE conversation_id = ? AND title = 'New Chat'",
        (now, f"{content[:30]}...", conversation_id)
    )
    conn.commit()
    conn.close()

def get_messages(conversation_id):
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
        (conversation_id,)
    )
    msgs = cursor.fetchall()
    conn.close()
    return [dict(m) for m in msgs]

def delete_conversation(conversation_id):
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
    conn.commit()
    conn.close()
