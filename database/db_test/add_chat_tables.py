#!/usr/bin/env python3
"""
Add chat tables to existing database
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="/app/.env.local")

def add_chat_tables():
    """
    Add chat_sessions and chat_messages tables to existing database
    """
    # Determine which database to use
    db_type = os.getenv("DB_TYPE", "sqlite").lower()
    
    if db_type == "postgresql":
        postgres_url = os.getenv("POSTGRES_URL")
        if not postgres_url:
            raise ValueError("POSTGRES_URL environment variable is required")
        engine = create_engine(postgres_url, pool_size=5, max_overflow=10, pool_recycle=3600)
    else:
        sqlite_path = os.getenv("SQLITE_DB_PATH", "./backend/test.db")
        engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
    
    print(f"Adding chat tables to {db_type} database...")
    
    # SQL commands to create chat tables
    if db_type == "postgresql":
        create_chat_tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                room_id VARCHAR(255) UNIQUE NOT NULL,
                participant_id VARCHAR(255) NOT NULL,
                agent_id VARCHAR(50) REFERENCES models(model_id) ON DELETE SET NULL,
                agent_name VARCHAR(255) NOT NULL,
                customer_name VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                is_active BOOLEAN DEFAULT TRUE,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                session_metadata JSONB
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) REFERENCES chat_sessions(session_id) ON DELETE CASCADE NOT NULL,
                message_id VARCHAR(255) UNIQUE NOT NULL,
                message_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                sender VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                message_metadata JSONB
            );
            """,
            # Create indexes
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status);",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_started_at ON chat_sessions(started_at);",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_message_id ON chat_messages(message_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp);",
        ]
    else:  # SQLite
        create_chat_tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(255) UNIQUE NOT NULL,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                room_id VARCHAR(255) UNIQUE NOT NULL,
                participant_id VARCHAR(255) NOT NULL,
                agent_id VARCHAR(50) REFERENCES models(model_id) ON DELETE SET NULL,
                agent_name VARCHAR(255) NOT NULL,
                customer_name VARCHAR(255) NOT NULL,
                status VARCHAR(50) DEFAULT 'active',
                is_active BOOLEAN DEFAULT 1,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                session_metadata TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(255) REFERENCES chat_sessions(session_id) ON DELETE CASCADE NOT NULL,
                message_id VARCHAR(255) UNIQUE NOT NULL,
                message_type VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                sender VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                message_metadata TEXT
            );
            """,
            # Create indexes
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status);",
            "CREATE INDEX IF NOT EXISTS idx_chat_sessions_started_at ON chat_sessions(started_at);",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_message_id ON chat_messages(message_id);",
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_timestamp ON chat_messages(timestamp);",
        ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            for sql in create_chat_tables_sql:
                print(f"Executing: {sql.strip()[:50]}...")
                conn.execute(text(sql))
            
            trans.commit()
            print("✅ Chat tables created successfully!")
            
            # Verify tables were created
            if db_type == "postgresql":
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name IN ('chat_sessions', 'chat_messages')
                    ORDER BY table_name
                """))
            else:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('chat_sessions', 'chat_messages')
                    ORDER BY name
                """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"Created tables: {tables}")
            
            # Test the tables
            conn.execute(text("SELECT COUNT(*) FROM chat_sessions"))
            conn.execute(text("SELECT COUNT(*) FROM chat_messages"))
            print("✅ Tables are functional!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ Error creating chat tables: {e}")
            raise

def main():
    print("🚀 Adding Chat Tables to Database")
    print("=" * 50)
    
    try:
        add_chat_tables()
        print("\n🎉 SUCCESS: Chat tables added successfully!")
        print("Your database is now ready for the floating chat widget.")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()