"""Hypothesis strategies for generating test data."""
from hypothesis import strategies as st
from hypothesis.strategies import composite

from devready.daemon.models import (
    DriftReport,
    TeamPolicy,
    ToolRequirement,
    ToolVersion,
    VersionChange,
)

_tool_names = st.sampled_from(["node", "python", "go", "rust", "java", "ruby", "php"])
_managers = st.one_of(st.none(), st.sampled_from(["nvm", "mise", "asdf", "pyenv", "rbenv"]))
_semver = st.from_regex(r"\d{1,2}\.\d{1,2}\.\d{1,2}", fullmatch=True)
_path = st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="/_-."))


@composite
def tool_version_strategy(draw: st.DrawFn) -> ToolVersion:
    return ToolVersion(
        name=draw(_tool_names),
        version=draw(_semver),
        path=draw(_path),
        manager=draw(_managers),
    )


@composite
def version_change_strategy(draw: st.DrawFn) -> VersionChange:
    return VersionChange(
        tool_name=draw(_tool_names),
        old_version=draw(_semver),
        new_version=draw(_semver),
        severity=draw(st.sampled_from(["major", "minor", "patch"])),
    )


@composite
def drift_report_strategy(draw: st.DrawFn) -> DriftReport:
    return DriftReport(
        snapshot_a_id=draw(st.uuids()).hex,
        snapshot_b_id=draw(st.uuids()).hex,
        added_tools=draw(st.lists(tool_version_strategy(), max_size=5)),
        removed_tools=draw(st.lists(tool_version_strategy(), max_size=5)),
        version_changes=draw(st.lists(version_change_strategy(), max_size=5)),
        drift_score=draw(st.integers(min_value=0, max_value=100)),
    )


@composite
def team_policy_strategy(draw: st.DrawFn) -> TeamPolicy:
    required = [
        ToolRequirement(name=draw(_tool_names), min_version=draw(st.one_of(st.none(), _semver)))
        for _ in range(draw(st.integers(min_value=0, max_value=3)))
    ]
    return TeamPolicy(
        required_tools=required,
        forbidden_tools=draw(st.lists(_tool_names, max_size=2)),
        version_constraints={},
        env_var_requirements=[],
    )
