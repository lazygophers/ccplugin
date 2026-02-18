"""
高级特性模块测试
"""

import os
import sys
from datetime import datetime, timedelta

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from memory.advanced import (
    RecommendationEngine,
    ConflictResolver,
    AnalyticsEngine,
    get_recommendation_engine,
    get_conflict_resolver,
    get_analytics_engine,
)


class TestRecommendationEngine:
    """测试推荐引擎"""
    
    def test_initialization(self):
        engine = RecommendationEngine()
        assert engine._operation_history == []
        assert engine._search_history == []
        assert engine._file_type_history == {}
    
    def test_record_operation(self):
        engine = RecommendationEngine()
        engine.record_operation({"tool_name": "Read", "tool_input": {"file_path": "/test/file.py"}})
        
        assert len(engine._operation_history) == 1
        assert engine._operation_history[0]["tool_name"] == "Read"
    
    def test_record_search(self):
        engine = RecommendationEngine()
        engine.record_search("test query", 5)
        
        assert len(engine._search_history) == 1
        assert engine._search_history[0]["query"] == "test query"
    
    def test_record_file_type(self):
        engine = RecommendationEngine()
        engine.record_file_type("/test/file.py")
        engine.record_file_type("/test/file.py")
        
        assert engine._file_type_history[".py"] == 2
    
    def test_detect_patterns_insufficient_data(self):
        engine = RecommendationEngine()
        patterns = engine.detect_patterns()
        
        assert patterns == []
    
    def test_detect_patterns_tool_pattern(self):
        engine = RecommendationEngine()
        for _ in range(5):
            engine.record_operation({"tool_name": "Read"})
        
        patterns = engine.detect_patterns()
        
        assert len(patterns) > 0
        assert patterns[0]["type"] == "tool_pattern"
        assert patterns[0]["tool"] == "Read"
    
    def test_detect_repeated_searches_insufficient_data(self):
        engine = RecommendationEngine()
        repeated = engine.detect_repeated_searches()
        
        assert repeated == []
    
    def test_detect_repeated_searches_found(self):
        engine = RecommendationEngine()
        engine.record_search("test", 5)
        engine.record_search("test", 3)
        engine.record_search("test", 2)
        
        repeated = engine.detect_repeated_searches()
        
        assert len(repeated) > 0
        assert repeated[0]["query"] == "test"
    
    def test_recommend_for_file_type_python(self):
        engine = RecommendationEngine()
        recs = engine.recommend_for_file_type(".py")
        
        assert "patterns" in recs
        assert "suggestions" in recs
        assert "python" in recs["patterns"][0].lower() or "py" in recs["patterns"][0].lower()
    
    def test_recommend_for_file_type_unknown(self):
        engine = RecommendationEngine()
        recs = engine.recommend_for_file_type(".xyz")
        
        assert "patterns" in recs
        assert "suggestions" in recs
    
    def test_detect_project_changes(self):
        engine = RecommendationEngine()
        changes = engine.detect_project_changes(["/test/file.py", "/test/file.js"])
        
        assert "new_directories" in changes
        assert "new_file_types" in changes
        assert "recommendations" in changes
    
    def test_record_error_solution(self):
        engine = RecommendationEngine()
        engine.record_error_solution("ModuleNotFoundError", "pip install module", True)
        
        assert "ModuleNotFoundError" in engine._error_solutions
    
    def test_find_similar_error(self):
        engine = RecommendationEngine()
        engine.record_error_solution("ModuleNotFoundError", "pip install module", True)
        
        solution = engine.find_similar_error("ModuleNotFoundError: No module named 'test'")
        
        assert solution is not None
        assert solution["solution"] == "pip install module"


class TestConflictResolver:
    """测试冲突解决器"""
    
    def test_initialization(self):
        resolver = ConflictResolver()
        assert "keep_latest" in resolver._conflict_strategies
    
    def test_detect_content_conflict(self):
        resolver = ConflictResolver()
        memories = [
            {"uri": "test://a", "content": "same content"},
            {"uri": "test://b", "content": "same content"},
        ]
        
        conflicts = resolver.detect_content_conflict(memories)
        
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == "content_conflict"
    
    def test_detect_content_no_conflict(self):
        resolver = ConflictResolver()
        memories = [
            {"uri": "test://a", "content": "content a"},
            {"uri": "test://b", "content": "content b"},
        ]
        
        conflicts = resolver.detect_content_conflict(memories)
        
        assert len(conflicts) == 0
    
    def test_detect_time_conflict(self):
        resolver = ConflictResolver()
        now = datetime.now()
        earlier = now - timedelta(days=1)
        
        memories = [
            {"uri": "test://similar/a", "content": "content a", "updated_at": now},
            {"uri": "test://similar/b", "content": "content b", "updated_at": earlier},
        ]
        
        conflicts = resolver.detect_time_conflict(memories)
        
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == "time_conflict"
    
    def test_resolve_conflict_keep_latest(self):
        resolver = ConflictResolver()
        conflict = {
            "type": "time_conflict",
            "memories": ["test://a", "test://b"],
        }
        
        result = resolver.resolve_conflict(conflict, "keep_latest")
        
        assert result["strategy"] == "keep_latest"
    
    def test_resolve_conflict_merge(self):
        resolver = ConflictResolver()
        conflict = {
            "type": "content_conflict",
            "memories": ["test://a", "test://b"],
        }
        
        result = resolver.resolve_conflict(conflict, "merge")
        
        assert result["strategy"] == "merge"
    
    def test_auto_resolve_content_conflict(self):
        resolver = ConflictResolver()
        conflict = {
            "type": "content_conflict",
            "memories": ["test://a", "test://b"],
        }
        
        result = resolver.auto_resolve(conflict)
        
        assert result["strategy"] == "keep_both"
    
    def test_auto_resolve_time_conflict(self):
        resolver = ConflictResolver()
        conflict = {
            "type": "time_conflict",
            "memories": ["test://a", "test://b"],
        }
        
        result = resolver.auto_resolve(conflict)
        
        assert result["strategy"] == "keep_latest"
    
    def test_is_similar_uri(self):
        resolver = ConflictResolver()
        
        assert resolver._is_similar_uri("test://a/b", "test://a/c") is True
        assert resolver._is_similar_uri("test://a/b", "test://x/y") is False


class TestAnalyticsEngine:
    """测试分析引擎"""
    
    def test_initialization(self):
        engine = AnalyticsEngine()
        assert engine is not None
    
    def test_generate_usage_analysis_empty(self):
        engine = AnalyticsEngine()
        result = engine.generate_usage_analysis([])
        
        assert result["total"] == 0
    
    def test_generate_usage_analysis(self):
        engine = AnalyticsEngine()
        memories = [
            {"uri": "test://a", "access_count": 10},
            {"uri": "test://b", "access_count": 5},
            {"uri": "test://c", "access_count": 0},
        ]
        
        result = engine.generate_usage_analysis(memories)
        
        assert result["total_memories"] == 3
        assert result["total_access_count"] == 15
        assert result["never_accessed_count"] == 1
    
    def test_generate_quality_analysis_empty(self):
        engine = AnalyticsEngine()
        result = engine.generate_quality_analysis([])
        
        assert result["total"] == 0
    
    def test_generate_quality_analysis(self):
        engine = AnalyticsEngine()
        now = datetime.now()
        old = now - timedelta(days=60)
        
        memories = [
            {"uri": "test://a", "content": "short", "disclosure": None, "updated_at": old},
            {"uri": "test://b", "content": "this is a longer content that is good", "disclosure": "when needed", "updated_at": now},
        ]
        
        result = engine.generate_quality_analysis(memories)
        
        assert result["total_memories"] == 2
        assert "quality_score" in result
    
    def test_generate_evolution_analysis_empty(self):
        engine = AnalyticsEngine()
        result = engine.generate_evolution_analysis([], [])
        
        assert result["total_memories"] == 0
    
    def test_generate_evolution_analysis(self):
        engine = AnalyticsEngine()
        now = datetime.now()
        
        memories = [
            {"uri": "test://a", "created_at": now, "status": "active"},
            {"uri": "test://b", "created_at": now - timedelta(days=10), "status": "archived"},
        ]
        versions = [
            {"uri": "test://a", "version": 1},
            {"uri": "test://a", "version": 2},
        ]
        
        result = engine.generate_evolution_analysis(memories, versions)
        
        assert result["total_memories"] == 2
        assert result["total_versions"] == 2
    
    def test_generate_insights(self):
        engine = AnalyticsEngine()
        usage = {"never_accessed_percentage": 60}
        quality = {"quality_score": 50, "outdated_count": 15}
        evolution = {"growth_rate_7_days": 10}
        
        insights = engine.generate_insights(usage, quality, evolution)
        
        assert len(insights) > 0
    
    def test_generate_recommendations(self):
        engine = AnalyticsEngine()
        usage = {"never_accessed_count": 10}
        quality = {"outdated_count": 5, "short_content_count": 3, "no_disclosure_count": 2}
        evolution = {}
        
        recommendations = engine.generate_recommendations(usage, quality, evolution)
        
        assert len(recommendations) > 0
    
    def test_generate_report(self):
        engine = AnalyticsEngine()
        now = datetime.now()
        
        memories = [
            {"uri": "test://a", "content": "content", "status": "active", "priority": 5, "disclosure": None, "access_count": 10, "created_at": now, "updated_at": now},
        ]
        versions = []
        
        report = engine.generate_report(memories, versions)
        
        assert "generated_at" in report
        assert "summary" in report
        assert "usage_analysis" in report
        assert "quality_analysis" in report
        assert "evolution_analysis" in report
        assert "insights" in report
        assert "recommendations" in report


class TestGlobalInstances:
    """测试全局实例"""
    
    def test_get_recommendation_engine(self):
        engine = get_recommendation_engine()
        assert isinstance(engine, RecommendationEngine)
    
    def test_get_conflict_resolver(self):
        resolver = get_conflict_resolver()
        assert isinstance(resolver, ConflictResolver)
    
    def test_get_analytics_engine(self):
        engine = get_analytics_engine()
        assert isinstance(engine, AnalyticsEngine)
