from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

from inno_obsidian_ai.audit import AuditLogger
from inno_obsidian_ai.manifest import ManifestStore
from inno_obsidian_ai.pipeline import (
    PipelineSummary,
    append_operation_log,
    render_operation_log,
    update_dashboard,
)


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_obsidian_ai_pipeline.py"
SPEC = importlib.util.spec_from_file_location("run_obsidian_ai_pipeline_script", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_operation_log_is_append_only(config, vault: Path) -> None:
    summary = PipelineSummary(
        run_id="run-1",
        mode="pipeline",
        write=True,
        dry_run=False,
        scanned_codex_logs=1,
    )

    first = append_operation_log(config, summary)
    second = append_operation_log(config, summary)

    assert first == second
    content = first.read_text(encoding="utf-8")
    assert content.count("## Obsidian AI Pipeline - ") == 2
    assert content.count("* Run ID: run-1") == 2


def test_dashboard_replaces_marker_only(config, vault: Path) -> None:
    dashboard = vault / "10_Projects/INNO_KIS_Trading/Project Dashboard.md"
    dashboard.write_text(
        "# Dashboard\n\nKeep me\n\n<!-- BEGIN_AUTO_OBSIDIAN_AI_DASHBOARD -->\nold\n<!-- END_AUTO_OBSIDIAN_AI_DASHBOARD -->\n\nPreserve me\n",
        encoding="utf-8",
    )
    summary = PipelineSummary(
        run_id="run-2",
        mode="pipeline",
        write=True,
        dry_run=False,
        notes_changed=1,
        notes_indexed=1,
    )

    update_dashboard(config, ManifestStore(config.manifest_path), summary, path_prefixes=["10_Projects/INNO_KIS_Trading"])

    content = dashboard.read_text(encoding="utf-8")
    assert "Keep me" in content
    assert "Preserve me" in content
    assert "old" not in content
    assert "## Obsidian AI Auto Summary" in content


def test_pipeline_dry_run_does_not_write_files(config_path: Path, vault: Path) -> None:
    source = vault / "00_Inbox/codex_logs/2026-06-30/working_list_2026_06_30_phase-3.md"
    source.write_text("Project: INNO_KIS_Trading\n", encoding="utf-8")
    dashboard = vault / "10_Projects/INNO_KIS_Trading/Project Dashboard.md"
    dashboard.write_text("# Dashboard\n", encoding="utf-8")

    before_dashboard = dashboard.read_text(encoding="utf-8")
    assert MODULE.main(["--config", str(config_path), "--dry-run", "--stats"]) == 0

    assert not any((vault / "00_Inbox/_review").rglob("*.proposal.md"))
    assert not (vault / "10_Projects/INNO_KIS_Trading/06_Logs/Obsidian AI Pipeline Log.md").exists()
    assert dashboard.read_text(encoding="utf-8") == before_dashboard


def test_pipeline_passes_changed_notes_only_to_index(monkeypatch, config_path: Path) -> None:
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        MODULE,
        "run_organizer",
        lambda **kwargs: [],
    )
    monkeypatch.setattr(
        MODULE,
        "apply_approved_proposals",
        lambda *args, **kwargs: [
            SimpleNamespace(
                proposal_file="a.proposal.md",
                changed_notes=("10_Projects/INNO_KIS_Trading/06_Logs/a.md",),
                skipped=False,
                reason="applied",
            )
        ],
    )

    def _fake_index(config, **kwargs):
        captured["candidate_paths"] = kwargs.get("candidate_paths")
        return SimpleNamespace(
            target_files=1,
            skipped_files=0,
            indexed_files=1,
            failed_files=0,
            estimated_chunks=1,
            cleaned_files=0,
            dry_run=True,
            exit_code=0,
        )

    monkeypatch.setattr(MODULE, "run_indexing", _fake_index)

    assert MODULE.main(["--config", str(config_path), "--dry-run"]) == 0
    assert captured["candidate_paths"] == ["10_Projects/INNO_KIS_Trading/06_Logs/a.md"]


def test_pipeline_blocks_full_vault_index_by_default(config_path: Path, capsys) -> None:
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            '  default_index_path_prefixes:\n    - "10_Projects/INNO_KIS_Trading"\n',
            "  default_index_path_prefixes: []\n",
        ),
        encoding="utf-8",
    )
    assert MODULE.main(["--config", str(config_path), "--index-only", "--dry-run"]) == 2
    assert "Full-vault indexing is blocked by default" in capsys.readouterr().err


def test_pipeline_rejects_force_full_index_when_config_disables_it(config_path: Path, capsys) -> None:
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            '  default_index_path_prefixes:\n    - "10_Projects/INNO_KIS_Trading"\n',
            "  default_index_path_prefixes: []\n",
        ),
        encoding="utf-8",
    )
    assert (
        MODULE.main(["--config", str(config_path), "--index-only", "--dry-run", "--force-full-index"]) == 2
    )
    assert "automation.allow_full_vault_index=false" in capsys.readouterr().err


def test_pipeline_stats_include_expected_fields(config_path: Path, capsys) -> None:
    assert MODULE.main(["--config", str(config_path), "--summary-only", "--dry-run", "--stats"]) == 0
    output = capsys.readouterr().out
    assert "PIPELINE " in output
    assert "run_id=" in output
    assert "mode=summary-only" in output
    assert "indexed=" in output
    assert "cleaned=" in output


def test_audit_log_records_pipeline_run_id(config, vault: Path) -> None:
    audit = AuditLogger(config.audit_log_dir)
    audit.log(action="index", vault_relative_path="a.md", status="indexed", run_id="run-9")
    content = audit.log_path.read_text(encoding="utf-8")
    assert '"run_id": "run-9"' in content


def test_operation_log_redacts_sensitive_warning() -> None:
    summary = PipelineSummary(
        run_id="run-3",
        mode="pipeline",
        write=False,
        dry_run=True,
        warnings=["Authorization: Bearer secret-token-value-123456"],
    )
    rendered = render_operation_log(summary)
    assert "secret-token-value-123456" not in rendered
    assert "[REDACTED]" in rendered


def test_shell_wrapper_missing_venv_returns_clear_error(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True)
    wrapper = scripts_dir / "run_obsidian_ai_pipeline.sh"
    wrapper.write_text(
        (Path(__file__).resolve().parents[1] / "scripts" / "run_obsidian_ai_pipeline.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    wrapper.chmod(0o755)

    result = subprocess.run(
        [str(wrapper)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "NVIDIA_API_KEY": "secret-value"},
    )

    assert result.returncode == 3
    assert ".venv not found" in result.stderr
    assert "secret-value" not in result.stderr


def test_shell_wrapper_missing_config_returns_clear_error(tmp_path: Path) -> None:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True)
    wrapper = scripts_dir / "run_obsidian_ai_pipeline.sh"
    wrapper.write_text(
        (Path(__file__).resolve().parents[1] / "scripts" / "run_obsidian_ai_pipeline.sh").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    (tmp_path / ".venv/bin").mkdir(parents=True)
    (tmp_path / ".venv/bin/activate").write_text("true\n", encoding="utf-8")

    result = subprocess.run(
        [str(wrapper)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={**os.environ, "NVIDIA_API_KEY": "secret-value"},
    )

    assert result.returncode == 4
    assert "config/obsidian_ai.yaml not found" in result.stderr
    assert "secret-value" not in result.stderr
