"""
智能推荐系统

提供模式检测、解决方案发现、重复查询检测、新文件类型推荐、项目变更检测等功能。
"""

import asyncio
import hashlib
import os
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


class RecommendationEngine:
    """智能推荐引擎"""
    
    def __init__(self):
        self._operation_history: List[Dict] = []
        self._search_history: List[Dict] = []
        self._file_type_history: Dict[str, int] = {}
        self._error_solutions: Dict[str, Dict] = {}
    
    def record_operation(self, operation: Dict[str, Any]) -> None:
        """记录操作历史"""
        operation["timestamp"] = datetime.now().isoformat()
        self._operation_history.append(operation)
        
        if len(self._operation_history) > 1000:
            self._operation_history = self._operation_history[-500:]
    
    def record_search(self, query: str, results_count: int) -> None:
        """记录搜索历史"""
        self._search_history.append({
            "query": query,
            "results_count": results_count,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self._search_history) > 500:
            self._search_history = self._search_history[-200:]
    
    def record_file_type(self, file_path: str) -> None:
        """记录文件类型"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext:
            self._file_type_history[ext] = self._file_type_history.get(ext, 0) + 1
    
    def detect_patterns(self) -> List[Dict]:
        """检测操作模式"""
        if len(self._operation_history) < 3:
            return []
        
        patterns = []
        
        tool_counter = Counter(op.get("tool_name", "") for op in self._operation_history[-50:])
        for tool_name, count in tool_counter.items():
            if count >= 3:
                patterns.append({
                    "type": "tool_pattern",
                    "tool": tool_name,
                    "count": count,
                    "recommendation": f"检测到频繁使用 {tool_name}，建议创建工作流记忆"
                })
        
        file_patterns = {}
        for op in self._operation_history[-30:]:
            file_path = op.get("tool_input", {}).get("file_path", "")
            if file_path:
                dir_path = os.path.dirname(file_path)
                file_patterns[dir_path] = file_patterns.get(dir_path, 0) + 1
        
        for dir_path, count in file_patterns.items():
            if count >= 3:
                patterns.append({
                    "type": "directory_pattern",
                    "directory": dir_path,
                    "count": count,
                    "recommendation": f"检测到频繁操作目录 {dir_path}，建议创建项目结构记忆"
                })
        
        return patterns
    
    def detect_repeated_searches(self) -> List[Dict]:
        """检测重复搜索"""
        if len(self._search_history) < 2:
            return []
        
        query_counter = Counter(s["query"] for s in self._search_history[-50:])
        repeated = []
        
        for query, count in query_counter.items():
            if count >= 2:
                repeated.append({
                    "query": query,
                    "count": count,
                    "recommendation": f"检测到重复搜索 '{query}'，建议创建索引记忆"
                })
        
        return repeated
    
    def recommend_for_file_type(self, file_ext: str) -> Dict:
        """为新文件类型推荐"""
        ext = file_ext.lower()
        
        recommendations = {
            ".py": {
                "patterns": ["python://patterns", "project://python/config"],
                "suggestions": ["检查是否有 Python 项目配置记忆", "加载 Python 编码规范"]
            },
            ".js": {
                "patterns": ["javascript://patterns", "project://js/config"],
                "suggestions": ["检查是否有 JavaScript 项目配置记忆", "加载 JS 编码规范"]
            },
            ".ts": {
                "patterns": ["typescript://patterns", "project://ts/config"],
                "suggestions": ["检查是否有 TypeScript 项目配置记忆", "加载 TS 编码规范"]
            },
            ".md": {
                "patterns": ["docs://patterns", "project://documentation"],
                "suggestions": ["检查文档模板记忆", "加载 Markdown 规范"]
            },
            ".json": {
                "patterns": ["config://patterns", "project://config"],
                "suggestions": ["检查配置文件记忆", "加载项目配置"]
            },
            ".yaml": {
                "patterns": ["config://patterns", "project://yaml/config"],
                "suggestions": ["检查 YAML 配置记忆", "加载配置规范"]
            },
            ".sql": {
                "patterns": ["database://patterns", "project://sql/schema"],
                "suggestions": ["检查数据库 Schema 记忆", "加载 SQL 规范"]
            }
        }
        
        return recommendations.get(ext, {
            "patterns": [],
            "suggestions": [f"首次处理 {ext} 文件，建议创建相关记忆"]
        })
    
    def detect_project_changes(self, current_files: List[str]) -> Dict:
        """检测项目变更"""
        current_dirs = set()
        current_exts = set()
        
        for f in current_files:
            current_dirs.add(os.path.dirname(f))
            ext = os.path.splitext(f)[1].lower()
            if ext:
                current_exts.add(ext)
        
        changes = {
            "new_directories": [],
            "new_file_types": [],
            "recommendations": []
        }
        
        for ext in current_exts:
            if ext not in self._file_type_history:
                changes["new_file_types"].append(ext)
                changes["recommendations"].append(f"检测到新文件类型 {ext}，建议创建相关记忆")
        
        return changes
    
    def record_error_solution(self, error_pattern: str, solution: str, success: bool) -> None:
        """记录错误解决方案"""
        self._error_solutions[error_pattern] = {
            "solution": solution,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
    
    def find_similar_error(self, error_message: str) -> Optional[Dict]:
        """查找相似错误的解决方案"""
        for pattern, solution in self._error_solutions.items():
            if pattern.lower() in error_message.lower():
                return solution
        
        return None


class ConflictResolver:
    """冲突解决机制"""
    
    def __init__(self):
        self._conflict_strategies = {
            "keep_latest": self._resolve_keep_latest,
            "keep_oldest": self._resolve_keep_oldest,
            "merge": self._resolve_merge,
            "keep_both": self._resolve_keep_both,
        }
    
    def detect_content_conflict(self, memories: List[Dict]) -> List[Dict]:
        """检测内容冲突"""
        conflicts = []
        seen_content = {}
        
        for mem in memories:
            content_hash = hashlib.md5(mem.get("content", "").encode()).hexdigest()
            uri = mem.get("uri", "")
            
            if content_hash in seen_content:
                existing_uri = seen_content[content_hash]
                if existing_uri != uri:
                    conflicts.append({
                        "type": "content_conflict",
                        "memories": [existing_uri, uri],
                        "reason": "相同内容但不同 URI"
                    })
            else:
                seen_content[content_hash] = uri
        
        return conflicts
    
    def detect_time_conflict(self, memories: List[Dict]) -> List[Dict]:
        """检测时间冲突"""
        conflicts = []
        
        for i, mem1 in enumerate(memories):
            for mem2 in memories[i+1:]:
                uri1, uri2 = mem1.get("uri", ""), mem2.get("uri", "")
                
                if self._is_similar_uri(uri1, uri2):
                    content1 = mem1.get("content", "")
                    content2 = mem2.get("content", "")
                    
                    if content1 != content2:
                        updated1 = mem1.get("updated_at")
                        updated2 = mem2.get("updated_at")
                        
                        if updated1 and updated2:
                            conflicts.append({
                                "type": "time_conflict",
                                "memories": [uri1, uri2],
                                "reason": "相似 URI 但内容不同",
                                "newer": uri1 if updated1 > updated2 else uri2
                            })
        
        return conflicts
    
    def detect_dependency_conflict(self, memories: List[Dict], relations: List[Dict]) -> List[Dict]:
        """检测依赖冲突"""
        conflicts = []
        
        memory_status = {m.get("uri"): m.get("status") for m in memories}
        
        for rel in relations:
            from_uri = rel.get("from_uri")
            to_uri = rel.get("to_uri")
            
            if memory_status.get(from_uri) == "deleted" and memory_status.get(to_uri) == "active":
                conflicts.append({
                    "type": "dependency_conflict",
                    "memories": [from_uri, to_uri],
                    "reason": "已删除的记忆仍被活跃记忆引用"
                })
        
        return conflicts
    
    def resolve_conflict(self, conflict: Dict, strategy: str = "keep_latest") -> Dict:
        """解决冲突"""
        resolver = self._conflict_strategies.get(strategy, self._resolve_keep_latest)
        return resolver(conflict)
    
    def _resolve_keep_latest(self, conflict: Dict) -> Dict:
        """保留最新版本"""
        return {
            "strategy": "keep_latest",
            "action": "保留最新版本",
            "conflict": conflict
        }
    
    def _resolve_keep_oldest(self, conflict: Dict) -> Dict:
        """保留最老版本"""
        return {
            "strategy": "keep_oldest",
            "action": "保留最老版本",
            "conflict": conflict
        }
    
    def _resolve_merge(self, conflict: Dict) -> Dict:
        """合并内容"""
        return {
            "strategy": "merge",
            "action": "合并内容",
            "conflict": conflict
        }
    
    def _resolve_keep_both(self, conflict: Dict) -> Dict:
        """保留两者"""
        return {
            "strategy": "keep_both",
            "action": "保留两者，标记冲突",
            "conflict": conflict
        }
    
    def auto_resolve(self, conflict: Dict) -> Dict:
        """自动选择解决策略"""
        if conflict["type"] == "content_conflict":
            return self.resolve_conflict(conflict, "keep_both")
        
        if conflict["type"] == "time_conflict":
            return self.resolve_conflict(conflict, "keep_latest")
        
        if conflict["type"] == "dependency_conflict":
            return {
                "strategy": "manual",
                "action": "需要手动处理依赖关系",
                "conflict": conflict
            }
        
        return self.resolve_conflict(conflict, "keep_latest")
    
    def _is_similar_uri(self, uri1: str, uri2: str) -> bool:
        """判断 URI 是否相似"""
        parts1 = uri1.split("/")
        parts2 = uri2.split("/")
        
        if len(parts1) != len(parts2):
            return False
        
        same_count = sum(1 for p1, p2 in zip(parts1, parts2) if p1 == p2)
        return same_count >= len(parts1) - 1


class AnalyticsEngine:
    """记忆分析引擎"""
    
    def __init__(self):
        pass
    
    def generate_usage_analysis(self, memories: List[Dict]) -> Dict:
        """生成使用分析"""
        if not memories:
            return {"total": 0, "analysis": {}}
        
        access_counts = [m.get("access_count", 0) for m in memories]
        total_access = sum(access_counts)
        avg_access = total_access / len(memories) if memories else 0
        
        most_accessed = sorted(memories, key=lambda m: m.get("access_count", 0), reverse=True)[:5]
        never_accessed = [m for m in memories if m.get("access_count", 0) == 0]
        
        return {
            "total_memories": len(memories),
            "total_access_count": total_access,
            "average_access_count": round(avg_access, 2),
            "most_accessed": [
                {"uri": m.get("uri"), "count": m.get("access_count", 0)}
                for m in most_accessed
            ],
            "never_accessed_count": len(never_accessed),
            "never_accessed_percentage": round(len(never_accessed) / len(memories) * 100, 1) if memories else 0
        }
    
    def generate_quality_analysis(self, memories: List[Dict]) -> Dict:
        """生成质量分析"""
        if not memories:
            return {"total": 0, "analysis": {}}
        
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        outdated = []
        short_content = []
        no_disclosure = []
        
        for m in memories:
            updated_at = m.get("updated_at")
            if updated_at:
                if isinstance(updated_at, str):
                    updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                if updated_at < thirty_days_ago:
                    outdated.append(m.get("uri"))
            
            content = m.get("content", "")
            if len(content) < 20:
                short_content.append(m.get("uri"))
            
            if not m.get("disclosure"):
                no_disclosure.append(m.get("uri"))
        
        return {
            "total_memories": len(memories),
            "outdated_count": len(outdated),
            "outdated_percentage": round(len(outdated) / len(memories) * 100, 1) if memories else 0,
            "short_content_count": len(short_content),
            "no_disclosure_count": len(no_disclosure),
            "quality_score": round(
                (1 - len(outdated) / len(memories)) * 0.4 +
                (1 - len(short_content) / len(memories)) * 0.3 +
                (1 - len(no_disclosure) / len(memories)) * 0.3, 2
            ) * 100 if memories else 100
        }
    
    def generate_evolution_analysis(self, memories: List[Dict], versions: List[Dict]) -> Dict:
        """生成演化分析"""
        now = datetime.now()
        
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)
        
        recent_7_days = []
        recent_30_days = []
        
        for m in memories:
            created_at = m.get("created_at")
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created_at > last_7_days:
                    recent_7_days.append(m.get("uri"))
                if created_at > last_30_days:
                    recent_30_days.append(m.get("uri"))
        
        status_counts = {}
        for m in memories:
            status = m.get("status", "active")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_memories": len(memories),
            "created_last_7_days": len(recent_7_days),
            "created_last_30_days": len(recent_30_days),
            "total_versions": len(versions),
            "average_versions_per_memory": round(len(versions) / len(memories), 2) if memories else 0,
            "status_distribution": status_counts,
            "growth_rate_7_days": round(len(recent_7_days) / 7, 2),
            "growth_rate_30_days": round(len(recent_30_days) / 30, 2)
        }
    
    def generate_insights(self, usage: Dict, quality: Dict, evolution: Dict) -> List[Dict]:
        """生成洞察"""
        insights = []
        
        if quality.get("quality_score", 100) < 70:
            insights.append({
                "type": "quality_warning",
                "message": f"记忆质量分数较低 ({quality.get('quality_score')}%)，建议清理过时记忆",
                "priority": "high"
            })
        
        if usage.get("never_accessed_percentage", 0) > 50:
            insights.append({
                "type": "usage_warning",
                "message": f"{usage.get('never_accessed_percentage')}% 的记忆从未被访问，考虑归档或删除",
                "priority": "medium"
            })
        
        if evolution.get("growth_rate_7_days", 0) > 5:
            insights.append({
                "type": "growth_info",
                "message": f"记忆增长较快 (每天 {evolution.get('growth_rate_7_days')} 条)，建议定期整理",
                "priority": "low"
            })
        
        if quality.get("outdated_count", 0) > 10:
            insights.append({
                "type": "outdated_warning",
                "message": f"有 {quality.get('outdated_count')} 条记忆超过 30 天未更新",
                "priority": "medium"
            })
        
        return insights
    
    def generate_recommendations(self, usage: Dict, quality: Dict, evolution: Dict) -> List[Dict]:
        """生成推荐操作"""
        recommendations = []
        
        if quality.get("outdated_count", 0) > 0:
            recommendations.append({
                "action": "archive_outdated",
                "description": f"归档 {quality.get('outdated_count')} 条过时记忆",
                "priority": "medium"
            })
        
        if usage.get("never_accessed_count", 0) > 0:
            recommendations.append({
                "action": "review_unused",
                "description": f"审查 {usage.get('never_accessed_count')} 条从未访问的记忆",
                "priority": "low"
            })
        
        if quality.get("short_content_count", 0) > 0:
            recommendations.append({
                "action": "enrich_content",
                "description": f"充实 {quality.get('short_content_count')} 条内容过短的记忆",
                "priority": "low"
            })
        
        if quality.get("no_disclosure_count", 0) > 0:
            recommendations.append({
                "action": "add_disclosure",
                "description": f"为 {quality.get('no_disclosure_count')} 条记忆添加触发条件",
                "priority": "medium"
            })
        
        return recommendations
    
    def generate_report(self, memories: List[Dict], versions: List[Dict]) -> Dict:
        """生成完整分析报告"""
        usage = self.generate_usage_analysis(memories)
        quality = self.generate_quality_analysis(memories)
        evolution = self.generate_evolution_analysis(memories, versions)
        insights = self.generate_insights(usage, quality, evolution)
        recommendations = self.generate_recommendations(usage, quality, evolution)
        
        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_memories": len(memories),
                "total_versions": len(versions),
                "quality_score": quality.get("quality_score", 100)
            },
            "usage_analysis": usage,
            "quality_analysis": quality,
            "evolution_analysis": evolution,
            "insights": insights,
            "recommendations": recommendations
        }


recommendation_engine = RecommendationEngine()
conflict_resolver = ConflictResolver()
analytics_engine = AnalyticsEngine()


def get_recommendation_engine() -> RecommendationEngine:
    """获取推荐引擎实例"""
    return recommendation_engine


def get_conflict_resolver() -> ConflictResolver:
    """获取冲突解决器实例"""
    return conflict_resolver


def get_analytics_engine() -> AnalyticsEngine:
    """获取分析引擎实例"""
    return analytics_engine
