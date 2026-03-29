"""Tests for nightly_update job."""
import sys
sys.path.insert(0, 'server')

import os
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock

# Setup temp file before import
temp_dir = tempfile.mkdtemp()
temp_file = os.path.join(temp_dir, "last_update")
os.environ["LAST_UPDATE_FILE"] = temp_file

from jobs.nightly_update import read_last_update, write_last_update, nightly_update


class TestReadLastUpdate:
    """Tests for read_last_update function."""

    def test_read_no_file(self):
        """文件不存在时返回默认时间"""
        os.remove(temp_file) if os.path.exists(temp_file) else None
        result = read_last_update()
        assert result.year == 1970  # Default to 1970

    def test_read_empty_file(self):
        """空文件返回默认时间"""
        with open(temp_file, "w") as f:
            f.write("")
        result = read_last_update()
        assert result.year == 1970

    def test_read_valid_timestamp(self):
        """正确读取有效时间戳"""
        test_time = datetime(2026, 3, 28, 0, 5, 0)
        with open(temp_file, "w") as f:
            f.write(test_time.isoformat())
        result = read_last_update()
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 28


class TestWriteLastUpdate:
    """Tests for write_last_update function."""

    def test_write_creates_file(self):
        """写入时间戳创建文件"""
        test_time = datetime(2026, 3, 29, 0, 5, 0)
        write_last_update(test_time)
        assert os.path.exists(temp_file)

        with open(temp_file, "r") as f:
            content = f.read()
        assert "2026-03-29" in content

    def test_write_overwrites(self):
        """写入覆盖之前的内容"""
        time1 = datetime(2026, 3, 28, 0, 5, 0)
        time2 = datetime(2026, 3, 29, 0, 5, 0)

        write_last_update(time1)
        write_last_update(time2)

        with open(temp_file, "r") as f:
            content = f.read()
        assert "2026-03-29" in content
        assert "2026-03-28" not in content


class TestNightlyUpdate:
    """Tests for nightly_update function."""

    @patch('jobs.nightly_update.execute_sql')
    @patch('jobs.nightly_update.read_last_update')
    @patch('jobs.nightly_update.write_last_update')
    def test_no_new_ratings(self, mock_write, mock_read, mock_execute):
        """没有新评分时直接返回"""
        mock_read.return_value = datetime(2026, 3, 28, 0, 5, 0)
        mock_execute.return_value = []  # No new ratings

        nightly_update()

        mock_write.assert_called_once()
        mock_execute.assert_called_once()

    @patch('jobs.nightly_update.execute_sql')
    @patch('jobs.nightly_update.read_last_update')
    @patch('jobs.nightly_update.write_last_update')
    def test_new_tool_first_time(self, mock_write, mock_read, mock_execute):
        """新工具第一次评分"""
        mock_read.return_value = datetime(2026, 3, 28, 0, 5, 0)

        # First call returns new ratings, second returns no existing stats, third is INSERT
        mock_execute.side_effect = [
            [  # New ratings
                {'tool_name': 'tavily', 'accuracy': 5, 'efficiency': 4, 'usability': 4, 'stability': 5, 'overall': 4.7}
            ],
            None,  # No existing stats
            None   # INSERT result
        ]

        nightly_update()

        # Should insert new tool_stats (3 calls: SELECT ratings, SELECT stats, INSERT)
        assert mock_execute.call_count == 3

    @patch('jobs.nightly_update.execute_sql')
    @patch('jobs.nightly_update.read_last_update')
    @patch('jobs.nightly_update.write_last_update')
    def test_existing_tool_merge(self, mock_write, mock_read, mock_execute):
        """已有工具合并新评分"""
        mock_read.return_value = datetime(2026, 3, 28, 0, 5, 0)

        # First call returns new ratings, second returns existing stats, third is UPDATE
        mock_execute.side_effect = [
            [  # New ratings
                {'tool_name': 'tavily', 'accuracy': 5, 'efficiency': 4, 'usability': 4, 'stability': 5, 'overall': 4.7}
            ],
            {  # Existing stats
                'tool_name': 'tavily',
                'total_ratings': 10,
                'avg_accuracy': 4.5,
                'avg_efficiency': 4.2,
                'avg_usability': 4.4,
                'avg_stability': 4.1,
                'avg_overall': 4.3
            },
            None  # UPDATE result
        ]

        nightly_update()

        # Should update existing tool_stats (3 calls: SELECT ratings, SELECT stats, UPDATE)
        assert mock_execute.call_count == 3