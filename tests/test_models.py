import sys
sys.path.insert(0, 'server')

import pytest
from pydantic import ValidationError
from models import (
    RatingSubmit, RatingResponse, AgentRegisterResponse,
    ToolStatsResponse, ErrorDetail, ErrorResponse
)

class TestRatingSubmit:
    """RatingSubmit 验证测试"""

    def test_valid_rating(self):
        """有效评分应该通过"""
        rating = RatingSubmit(
            tool_name="test-tool",
            accuracy=5,
            efficiency=4,
            usability=4,
            stability=5,
            comment="好"
        )
        assert rating.tool_name == "test-tool"
        assert rating.accuracy == 5

    def test_tool_name_required(self):
        """tool_name 必填"""
        with pytest.raises(ValidationError):
            RatingSubmit(
                accuracy=5, efficiency=4, usability=4, stability=5
            )

    def test_tool_name_max_length(self):
        """tool_name 最大 255 字符"""
        with pytest.raises(ValidationError):
            RatingSubmit(
                tool_name="x" * 256,
                accuracy=5, efficiency=4, usability=4, stability=5
            )

    def test_accuracy_range(self):
        """accuracy 必须在 1-5"""
        # 太小
        with pytest.raises(ValidationError):
            RatingSubmit(
                tool_name="test", accuracy=0, efficiency=4, usability=4, stability=5
            )
        # 太大
        with pytest.raises(ValidationError):
            RatingSubmit(
                tool_name="test", accuracy=6, efficiency=4, usability=4, stability=5
            )
        # 有效值
        for val in [1, 2, 3, 4, 5]:
            r = RatingSubmit(
                tool_name="test", accuracy=val, efficiency=4, usability=4, stability=5
            )
            assert r.accuracy == val

    def test_comment_optional(self):
        """comment 可选"""
        r = RatingSubmit(
            tool_name="test", accuracy=5, efficiency=4, usability=4, stability=5
        )
        assert r.comment is None

    def test_comment_max_length(self):
        """comment 最大 20 字符"""
        with pytest.raises(ValidationError):
            RatingSubmit(
                tool_name="test",
                accuracy=5, efficiency=4, usability=4, stability=5,
                comment="x" * 21
            )


class TestAgentRegisterResponse:
    """AgentRegisterResponse 测试"""

    def test_valid_response(self):
        resp = AgentRegisterResponse(api_key="ek_test123")
        assert resp.api_key == "ek_test123"


class TestRatingResponse:
    """RatingResponse 测试"""

    def test_valid_response(self):
        resp = RatingResponse(id="uuid-123", success=True, message="OK")
        assert resp.id == "uuid-123"
        assert resp.success is True


class TestToolStatsResponse:
    """ToolStatsResponse 测试"""

    def test_valid_response(self):
        resp = ToolStatsResponse(
            tool_name="test-tool",
            stats={
                "total_ratings": 10,
                "avg_overall": 4.5,
                "avg_accuracy": 4.5,
                "avg_efficiency": 4.5,
                "avg_usability": 4.5,
                "avg_stability": 4.5,
                "last_updated": "2026-03-28T00:05:00"
            }
        )
        assert resp.tool_name == "test-tool"
        assert resp.stats["total_ratings"] == 10


class TestErrorDetail:
    """ErrorDetail 测试"""

    def test_valid_error(self):
        err = ErrorDetail(code="NOT_FOUND", message="Tool not found")
        assert err.code == "NOT_FOUND"


class TestErrorResponse:
    """ErrorResponse 测试"""

    def test_valid_error_response(self):
        err = ErrorResponse(error=ErrorDetail(code="ERROR", message="Error"))
        assert err.error.code == "ERROR"
