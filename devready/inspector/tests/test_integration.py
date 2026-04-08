from devready.inspector.scan_orchestrator import ScanOrchestrator

def test_full_scan_flow(tmp_path):
    # Setup dummy project
    project = tmp_path / "full_project"
    project.mkdir()
    (project / ".git").mkdir()
    (project / "pyproject.toml").write_text("[project]\nname='test'")
    (project / "CLAUDE.md").write_text("# Rules\nTest Rules")
    
    orchestrator = ScanOrchestrator()
    # We run the scan (it will use mocked or detected tools)
    # Since Syft and Osquery are missing, they should return empty results but NOT crash
    result = orchestrator.run_scan(project_path=str(project))
    
    assert result["success"] is True
    assert result["project_name"] == "full_project"
    assert "Python" in result["tech_stack"]
    assert "Test Rules" in result["ai_configs"]["instructions"]
    assert "performance" in result
    assert result["performance"]["within_budget"] is True
    assert result["freshness_score"] == 100.0 # No deps found

def test_scan_with_missing_root():
    orchestrator = ScanOrchestrator()
    # Should fallback to current dir or '.'
    result = orchestrator.run_scan(project_path="non_existent_path_!!!")
    assert result["project_path"] == "non_existent_path_!!!"
    assert result["success"] is True # Errors are recorded in 'errors' list, scan itself continues
