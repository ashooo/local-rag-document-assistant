from app.services import database


def configure_temp_database(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    db_path = data_dir / "app.db"

    monkeypatch.setattr(database, "DATA_DIR", data_dir)
    monkeypatch.setattr(database, "DB_PATH", db_path)

    database.init_db()

    return db_path


def test_init_db_creates_core_tables(monkeypatch, tmp_path):
    configure_temp_database(monkeypatch, tmp_path)

    with database.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

    table_names = {row["name"] for row in rows}

    assert "projects" in table_names
    assert "documents" in table_names
    assert "chat_sessions" in table_names
    assert "chat_documents" in table_names


def test_document_is_stored_with_project_id(monkeypatch, tmp_path):
    configure_temp_database(monkeypatch, tmp_path)
    timestamp = "2026-06-27T00:00:00+00:00"

    database.create_project(
        project_id="project_1",
        name="Project One",
        created_at=timestamp,
        updated_at=timestamp,
    )
    database.create_document(
        document_id="doc_1",
        project_id="project_1",
        filename="notes.txt",
        content_type="text/plain",
        file_path="uploads/doc_1_notes.txt",
        uploaded_at=timestamp,
    )

    document = database.get_document("doc_1")

    assert document == {
        "id": "doc_1",
        "project_id": "project_1",
        "filename": "notes.txt",
        "content_type": "text/plain",
        "file_path": "uploads/doc_1_notes.txt",
        "uploaded_at": timestamp,
    }


def test_chat_session_is_stored_with_project_id(monkeypatch, tmp_path):
    configure_temp_database(monkeypatch, tmp_path)
    timestamp = "2026-06-27T00:00:00+00:00"

    database.create_project(
        project_id="project_1",
        name="Project One",
        created_at=timestamp,
        updated_at=timestamp,
    )
    database.create_chat_session(
        chat_id="chat_1",
        project_id="project_1",
        title="Research",
        created_at=timestamp,
        updated_at=timestamp,
    )

    chat_session = database.get_chat_session("chat_1")

    assert chat_session == {
        "id": "chat_1",
        "project_id": "project_1",
        "title": "Research",
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def test_project_document_ids_returns_only_project_documents(monkeypatch, tmp_path):
    configure_temp_database(monkeypatch, tmp_path)
    timestamp = "2026-06-27T00:00:00+00:00"

    for project_id in ("project_1", "project_2"):
        database.create_project(
            project_id=project_id,
            name=None,
            created_at=timestamp,
            updated_at=timestamp,
        )

    database.create_document(
        document_id="doc_1",
        project_id="project_1",
        filename="one.txt",
        content_type="text/plain",
        file_path="uploads/doc_1_one.txt",
        uploaded_at=timestamp,
    )
    database.create_document(
        document_id="doc_2",
        project_id="project_2",
        filename="two.txt",
        content_type="text/plain",
        file_path="uploads/doc_2_two.txt",
        uploaded_at=timestamp,
    )

    assert database.get_project_document_ids("project_1") == ["doc_1"]
