from devready.inspector.root_detector import RootDetector
from devready.inspector.stack_detector import StackDetector
from devready.inspector.env_collector import EnvCollector
from devready.inspector.config_parser import ConfigParser

def test_root_detector(tmp_path):
    # Create a dummy project structure
    project = tmp_path / "my_project"
    project.mkdir()
    (project / ".git").mkdir()
    
    detector = RootDetector()
    root = detector.detect(start_path=str(project))
    assert root.lower() == str(project).replace("\\", "/").lower()

def test_stack_detector(tmp_path):
    # Create markers for multiple stacks
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text("{}")
    (project / "requirements.txt").write_text("")
    
    detector = StackDetector()
    stacks = detector.detect(str(project))
    assert "Node.js" in stacks
    assert "Python" in stacks

def test_env_collector_redaction():
    collector = EnvCollector()
    assert collector.redact_if_sensitive("GITHUB_TOKEN", "secret123") == "[REDACTED]"
    assert collector.redact_if_sensitive("DB_PASSWORD", "mypassword") == "[REDACTED]"
    assert collector.redact_if_sensitive("PATH", "/usr/bin") == "/usr/bin"

def test_parse_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("PORT=8080\nSTRIPE_KEY=sk_test_123\n#Comment\nINVALID_LINE")
    
    collector = EnvCollector()
    results = collector.parse_env_file(env_file)
    assert results["PORT"] == "8080"
    assert results["STRIPE_KEY"] == "[REDACTED]"
    assert "INVALID_LINE" not in results

def test_config_parser_markdown(tmp_path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("# Instructions\nDo X\n# Rules\nAlways Y")
    
    parser = ConfigParser()
    data = parser.parse_file(claude_md)
    assert "instructions" in data
    assert "rules" in data
    assert "Do X" in data["instructions"]
    assert "Always Y" in data["rules"]
