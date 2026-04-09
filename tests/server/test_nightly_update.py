import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock
from contextlib import contextmanager

import pytest

from jobs.nightly_update import read_last_update, write_last_update, nightly_update


class TestReadLastUpdate:

    def test_read_no_file(self):
        with patch('jobs.nightly_update.LAST_UPDATE_FILE', '/nonexistent/path/last_update'):
            result = read_last_update()
            assert result.year == 1970

    def test_read_empty_file(self):
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "last_update")
        with open(temp_file, "w") as f:
            f.write("")

        with patch('jobs.nightly_update.LAST_UPDATE_FILE', temp_file):
            result = read_last_update()
            assert result.year == 1970

    def test_read_valid_timestamp(self):
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "last_update")
        test_time = datetime(2026, 3, 28, 0, 5, 0)
        with open(temp_file, "w") as f:
            f.write(test_time.isoformat())

        with patch('jobs.nightly_update.LAST_UPDATE_FILE', temp_file):
            result = read_last_update()
            assert result.year == 2026
            assert result.month == 3
            assert result.day == 28


class TestWriteLastUpdate:

    def test_write_creates_file(self):
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "last_update")
        test_time = datetime(2026, 3, 29, 0, 5, 0)

        with patch('jobs.nightly_update.LAST_UPDATE_FILE', temp_file):
            write_last_update(test_time)
            assert os.path.exists(temp_file)

            with open(temp_file, "r") as f:
                content = f.read()
            assert "2026-03-29" in content

    def test_write_overwrites(self):
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "last_update")
        time1 = datetime(2026, 3, 28, 0, 5, 0)
        time2 = datetime(2026, 3, 29, 0, 5, 0)

        with patch('jobs.nightly_update.LAST_UPDATE_FILE', temp_file):
            write_last_update(time1)
            write_last_update(time2)

            with open(temp_file, "r") as f:
                content = f.read()
            assert "2026-03-29" in content
            assert "2026-03-28" not in content


class TestNightlyUpdate:

    def _mock_get_db(self, cursor_results):
        mock_cur = MagicMock()
        mock_cur.execute = MagicMock()
        mock_cur.fetchall.side_effect = cursor_results.get('fetchall', [])
        mock_cur.fetchone.side_effect = cursor_results.get('fetchone', [])

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.commit = MagicMock()
        mock_conn.rollback = MagicMock()

        @contextmanager
        def fake_get_db():
            yield mock_conn

        return fake_get_db, mock_conn, mock_cur

    @patch('jobs.nightly_update.write_last_update')
    @patch('jobs.nightly_update.read_last_update')
    @patch('jobs.nightly_update.get_db')
    def test_no_new_ratings(self, mock_get_db_fn, mock_read, mock_write):
        mock_read.return_value = datetime(2026, 3, 28, 0, 5, 0)

        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = []
        mock_cur.execute = MagicMock()

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.commit = MagicMock()
        mock_conn.rollback = MagicMock()

        mock_get_db_fn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_db_fn.return_value.__exit__ = MagicMock(return_value=False)

        nightly_update()

        mock_write.assert_called_once()

    @patch('jobs.nightly_update.write_last_update')
    @patch('jobs.nightly_update.read_last_update')
    @patch('jobs.nightly_update.get_db')
    def test_new_tool_first_time(self, mock_get_db_fn, mock_read, mock_write):
        mock_read.return_value = datetime(2026, 3, 28, 0, 5, 0)

        mock_cur = MagicMock()
        mock_cur.execute = MagicMock()
        mock_cur.fetchall.return_value = [
            {'tool_name': 'tavily', 'accuracy': 5, 'efficiency': 4, 'usability': 4, 'stability': 5, 'overall': 4.7}
        ]
        mock_cur.fetchone.return_value = None

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.commit = MagicMock()
        mock_conn.rollback = MagicMock()

        mock_get_db_fn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_db_fn.return_value.__exit__ = MagicMock(return_value=False)

        nightly_update()

        mock_conn.commit.assert_called_once()
        mock_write.assert_called_once()

    @patch('jobs.nightly_update.write_last_update')
    @patch('jobs.nightly_update.read_last_update')
    @patch('jobs.nightly_update.get_db')
    def test_existing_tool_merge(self, mock_get_db_fn, mock_read, mock_write):
        mock_read.return_value = datetime(2026, 3, 28, 0, 5, 0)

        mock_cur = MagicMock()
        mock_cur.execute = MagicMock()
        mock_cur.fetchall.return_value = [
            {'tool_name': 'tavily', 'accuracy': 5, 'efficiency': 4, 'usability': 4, 'stability': 5, 'overall': 4.7}
        ]
        mock_cur.fetchone.return_value = {
            'tool_name': 'tavily',
            'total_ratings': 10,
            'avg_accuracy': 4.5,
            'avg_efficiency': 4.2,
            'avg_usability': 4.4,
            'avg_stability': 4.1,
            'avg_overall': 4.3
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.commit = MagicMock()
        mock_conn.rollback = MagicMock()

        mock_get_db_fn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_db_fn.return_value.__exit__ = MagicMock(return_value=False)

        nightly_update()

        mock_conn.commit.assert_called_once()
        mock_write.assert_called_once()

    @patch('jobs.nightly_update.write_last_update')
    @patch('jobs.nightly_update.read_last_update')
    @patch('jobs.nightly_update.get_db')
    def test_rollback_on_error(self, mock_get_db_fn, mock_read, mock_write):
        mock_read.return_value = datetime(2026, 3, 28, 0, 5, 0)

        mock_cur = MagicMock()
        mock_cur.execute = MagicMock()
        mock_cur.fetchall.return_value = [
            {'tool_name': 'tavily', 'accuracy': 5, 'efficiency': 4, 'usability': 4, 'stability': 5, 'overall': 4.7}
        ]
        mock_cur.fetchone.side_effect = Exception("DB error")

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.commit = MagicMock()
        mock_conn.rollback = MagicMock()

        mock_get_db_fn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_db_fn.return_value.__exit__ = MagicMock(return_value=False)

        with pytest.raises(Exception, match="DB error"):
            nightly_update()

        mock_conn.rollback.assert_called_once()
        mock_write.assert_not_called()
