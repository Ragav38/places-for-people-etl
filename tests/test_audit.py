from unittest.mock import MagicMock, patch

from chapter_etl.audit import start_run, complete_run, fail_run


@patch("chapter_etl.audit.database_connection")
def test_start_run(mock_connection):
    connection = MagicMock()
    cursor = MagicMock()

    mock_connection.return_value.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor

    start_run("test-run-001", "university_chapters_dag")

    cursor.execute.assert_called_once()
    assert "RUNNING" in cursor.execute.call_args[0][0]


@patch("chapter_etl.audit.database_connection")
def test_complete_run(mock_connection):
    connection = MagicMock()
    cursor = MagicMock()
    cursor.rowcount = 1

    mock_connection.return_value.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor

    complete_run("test-run-001", 3, 3, 3, 1)

    cursor.execute.assert_called_once()
    assert "SUCCESS" in cursor.execute.call_args[0][0]


@patch("chapter_etl.audit.database_connection")
def test_fail_run(mock_connection):
    connection = MagicMock()
    cursor = MagicMock()
    cursor.rowcount = 1

    mock_connection.return_value.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor

    fail_run("test-run-001", "API connection failed")

    cursor.execute.assert_called_once()
    assert "FAILED" in cursor.execute.call_args[0][0]
