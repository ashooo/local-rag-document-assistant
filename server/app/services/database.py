import sqlite3
from app.config import DB_PATH, DATA_DIR

def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                content_type TEXT,
                file_path TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            )
        """)
        
def create_document(
        document_id: str,
        filename: str,
        content_type: str | None,
        file_path: str,
        uploaded_at: str
    ):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO documents(
                id,
                filename,
                content_type,
                file_path,
                uploaded_at    
            ) VALUES (
                ?,?,?,?,?
            )
            """,
            (
                document_id,
                filename,
                content_type,
                file_path,
                uploaded_at    
            )
        )
        

def get_document(
        document_id: str    
    ):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                filename,
                content_type,
                file_path,
                uploaded_at
            FROM
                documents
            WHERE
                id = ?
            """,
            (
                document_id,
            ),
        ).fetchone()
        
    return dict(row) if row else None

def delete_document(
        document_id: str    
    ):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM documents
            WHERE id = ?
            """,
            (
                document_id,
            ),
        )
    
    return cursor.rowcount > 0