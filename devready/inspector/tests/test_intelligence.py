import time
from devready.inspector.policy_checker import PolicyChecker
from devready.inspector.freshness_analyzer import FreshnessAnalyzer
from devready.inspector.cache_manager import CacheManager
from devready.inspector.performance_monitor import PerformanceMonitor

def test_policy_checker():
    checker = PolicyChecker()
    policy = {
        "required_tools": {"node": ">=18.0.0"},
        "forbidden_tools": ["telnet"]
    }
    scan_result = {
        "tools": {"node": "20.5.0", "telnet": "1.0.0"}
    }
    
    violations = checker.check(policy, scan_result)
    assert len(violations) == 1
    assert violations[0]["rule_id"] == "forbidden_tool"
    
    # Test version mismatch
    scan_result_bad = {"tools": {"node": "16.0.0"}}
    violations = checker.check(policy, scan_result_bad)
    assert any(v["rule_id"] == "version_mismatch" for v in violations)

def test_freshness_analyzer():
    analyzer = FreshnessAnalyzer(latest_versions_cache={"fastapi": "0.109.0"})
    deps = [{"name": "fastapi", "version": "0.100.0"}]
    
    result = analyzer.analyze(deps)
    assert result["freshness_score"] < 100
    assert result["analysis"][0]["status"] == "minor_update_available"

def test_cache_manager():
    cache = CacheManager()
    cache.set("key1", "data1", ttl_seconds=1)
    assert cache.get("key1") == "data1"
    
    time.sleep(1.1)
    assert cache.get("key1") is None
    assert cache.get_stats()["hits"] == 1
    assert cache.get_stats()["misses"] == 1

def test_performance_monitor():
    monitor = PerformanceMonitor(total_budget_seconds=0.1)
    monitor.start_total_timer()
    
    with monitor.measure("test_comp", budget_seconds=0.05):
        time.sleep(0.11)
        
    summary = monitor.get_summary()
    assert "test_comp" in summary["component_timings_ms"]
    assert summary["component_timings_ms"]["test_comp"] >= 100
    # Should flag as over budget
    assert summary["within_budget"] is False
