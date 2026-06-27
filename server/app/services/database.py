import sqlite3
from app.config import DB_PATH, DATA_DIR


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_column(conn, table_name: str, column_name: str, column_definition: str):
    columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing_column_names = {column["name"] for column in columns}

    if column_name not in existing_column_names:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT,
                file_path TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_documents (
                chat_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                PRIMARY KEY (chat_id, document_id),
                FOREIGN KEY (chat_id) REFERENCES chat_sessions(id),
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)

        _ensure_column(conn, "documents", "project_id", "TEXT")
        _ensure_column(conn, "chat_sessions", "project_id", "TEXT")


def create_project(
        project_id: str,
        name: str | None,
        created_at: str,
        updated_at: str
    ):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO projects (
                id,
                name,
                created_at,
                updated_at
            ) VALUES (
                ?,?,?,?
            )
            """,
            (
                project_id,
                name,
                created_at,
                updated_at,
            ),
        )


def create_document(
        document_id: str,
        project_id: str,
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
                project_id,
                filename,
                content_type,
                file_path,
                uploaded_at    
            ) VALUES (
                ?,?,?,?,?,?
            )
            """,
            (
                document_id,
                project_id,
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
                project_id,
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


def create_chat_session(
        chat_id: str,
        project_id: str,
        title: str | None,
        created_at: str,
        updated_at: str
    ):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO chat_sessions (
                id,
                project_id,
                title,
                created_at,
                updated_at
            ) VALUES (
                ?,?,?,?,?
            )
            """,
            (
                chat_id,
                project_id,
                title,
                created_at,
                updated_at,
            ),
        )


def get_chat_session(chat_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                id,
                project_id,
                title,
                created_at,
                updated_at
            FROM chat_sessions
            WHERE id = ?
            """,
            (chat_id,),
        ).fetchone()

    return dict(row) if row else None


def link_document_to_chat(
        chat_id: str,
        document_id: str
    ):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO chat_documents (
                chat_id,
                document_id
            ) VALUES (
                ?,?
            )
            """,
            (
                chat_id,
                document_id,
            ),
        )


def get_chat_document_ids(chat_id: str) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT document_id
            FROM chat_documents
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchall()

    return [row["document_id"] for row in rows]


def get_project_document_ids(project_id: str) -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id
            FROM documents
            WHERE project_id = ?
            """,
            (project_id,),
        ).fetchall()

    return [row["id"] for row in rows]
