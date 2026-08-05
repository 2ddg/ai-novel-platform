"""可观测性模块 - 请求追踪、指标收集、安全审计"""
import json
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class RequestTracer:
    """请求追踪器 - 为每个RAG请求分配trace_id并记录全链路"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._traces = {}
            cls._instance._current_trace = {}
        return cls._instance

    def start_trace(self, request_id: Optional[str] = None, **metadata) -> str:
        """开始一个请求追踪"""
        trace_id = request_id or uuid.uuid4().hex
        self._traces[trace_id] = {
            "trace_id": trace_id,
            "start_time": datetime.utcnow().isoformat(),
            "start_ts": time.time(),
            "metadata": metadata,
            "steps": [],
            "status": "active",
            "error": None,
        }
        self._current_trace[trace_id] = trace_id
        return trace_id

    def add_step(self, trace_id: str, step_name: str, **kwargs):
        """记录一个处理步骤"""
        if trace_id not in self._traces:
            return
        step = {
            "name": step_name,
            "timestamp": datetime.utcnow().isoformat(),
            "ts": time.time(),
            **kwargs,
        }
        self._traces[trace_id]["steps"].append(step)

    def end_trace(self, trace_id: str, status: str = "success", **kwargs):
        """结束追踪"""
        if trace_id not in self._traces:
            return
        trace = self._traces[trace_id]
        trace["end_time"] = datetime.utcnow().isoformat()
        trace["end_ts"] = time.time()
        trace["duration_ms"] = round((trace["end_ts"] - trace["start_ts"]) * 1000, 2)
        trace["status"] = status
        trace.update(kwargs)

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """获取追踪详情"""
        return self._traces.get(trace_id)

    def get_recent_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的追踪"""
        traces = sorted(
            self._traces.values(),
            key=lambda x: x.get("start_ts", 0),
            reverse=True
        )
        return traces[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """获取追踪统计"""
        traces = list(self._traces.values())
        if not traces:
            return {"total": 0}

        completed = [t for t in traces if "duration_ms" in t]
        durations = [t["duration_ms"] for t in completed]

        status_counts = defaultdict(int)
        for t in traces:
            status_counts[t.get("status", "unknown")] += 1

        return {
            "total": len(traces),
            "completed": len(completed),
            "avg_duration_ms": round(sum(durations) / len(durations), 2) if durations else 0,
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "status_distribution": dict(status_counts),
        }

    def cleanup(self, max_traces: int = 500):
        """清理旧追踪"""
        if len(self._traces) > max_traces:
            sorted_ids = sorted(
                self._traces.keys(),
                key=lambda k: self._traces[k].get("start_ts", 0)
            )
            for tid in sorted_ids[:-max_traces]:
                del self._traces[tid]


class SecurityAuditor:
    """安全审计器 - 检查prompt注入、敏感信息泄露等"""

    DANGEROUS_PATTERNS = [
        "ignore previous",
        "ignore above",
        "ignore all previous",
        "you are now",
        "system prompt",
        "reveal your",
        "jailbreak",
        "bypass",
        "hack",
        "你现在是",
        "忽略之前",
        "忽略以上",
        "提示词",
        "系统提示",
        "越狱",
        "破解",
    ]

    SENSITIVE_PATTERNS = [
        ("api_key", r"api[_-]?key\s*[:=]\s*[a-zA-Z0-9_\-]{10,}"),
        ("password", r"password\s*[:=]\s*\S+"),
        ("secret", r"secret\s*[:=]\s*\S+"),
        ("token", r"token\s*[:=]\s*[a-zA-Z0-9_\-\.]{10,}"),
    ]

    @classmethod
    def check_prompt_injection(cls, text: str) -> Dict[str, Any]:
        """检查是否存在prompt注入攻击"""
        text_lower = text.lower()
        detected = []
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern in text_lower:
                detected.append(pattern)

        return {
            "is_safe": len(detected) == 0,
            "detected_patterns": detected,
            "risk_level": "high" if len(detected) >= 2 else ("medium" if detected else "low"),
        }

    @classmethod
    def check_sensitive_info(cls, text: str) -> Dict[str, Any]:
        """检查是否包含敏感信息"""
        import re
        found = []
        for name, pattern in cls.SENSITIVE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found.append({"type": name, "count": len(matches)})

        return {
            "has_sensitive": len(found) > 0,
            "findings": found,
            "risk_level": "high" if found else "low",
        }

    @classmethod
    def full_audit(cls, text: str) -> Dict[str, Any]:
        """完整安全审计"""
        injection = cls.check_prompt_injection(text)
        sensitive = cls.check_sensitive_info(text)

        overall_risk = "low"
        if injection["risk_level"] == "high" or sensitive["risk_level"] == "high":
            overall_risk = "high"
        elif injection["risk_level"] == "medium" or sensitive["risk_level"] == "medium":
            overall_risk = "medium"

        return {
            "overall_risk": overall_risk,
            "prompt_injection": injection,
            "sensitive_info": sensitive,
            "timestamp": datetime.utcnow().isoformat(),
        }


# 全局实例
tracer = RequestTracer()
