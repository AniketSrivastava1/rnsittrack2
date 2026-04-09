"""Unit tests for project context detection."""
import json
import tempfile
from pathlib import Path

from devready.daemon.context import ContextDetector


def test_detects_git_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / ".git").mkdir()
        subdir = root / "src" / "app"
        subdir.mkdir(parents=True)

        detector = ContextDetector()
        path, name = detector.detect(str(subdir))
        assert path == str(root)
        assert name == root.name


def test_extracts_name_from_package_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "package.json").write_text(json.dumps({"name": "my-app"}))

        detector = ContextDetector()
        path, name = detector.detect(str(root))
        assert name == "my-app"


def test_fallback_to_directory_name():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "my-project"
        root.mkdir()

        detector = ContextDetector()
        path, name = detector.detect(str(root))
        assert name == "my-project"


def test_explicit_working_directory_used():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / ".git").mkdir()

        detector = ContextDetector()
        path, _ = detector.detect(str(root))
        assert path == str(root)
