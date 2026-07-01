from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_obsidian_ai_pipeline.py"
SPEC = importlib.util.spec_from_file_location("validate_obsidian_ai_pipeline_script", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _prepare_validator_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(MODULE, "ROOT", tmp_path)
    monkeypatch.setattr(MODULE, "_interpreter_in_venv", lambda: True)
    monkeypatch.setattr(
        MODULE,
        "_check_git_protection",
        lambda results, **kwargs: MODULE._add(results, "index", "OK", f"{kwargs['label']} is ignored by git"),
    )
    monkeypatch.setattr(
        MODULE,
        "_check_status_smoke",
        lambda results, **kwargs: MODULE._add(results, "index", "OK", "read-only pipeline status CLI is executable"),
    )
    (tmp_path / ".venv/bin").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts/run_obsidian_ai_pipeline.sh").write_text(
        """#!/usr/bin/env bash
set -euo pipefail
exec .venv/bin/python scripts/run_obsidian_ai_pipeline.py --stats "$@"
""",
        encoding="utf-8",
    )


def _write_dashboard_with_markers(vault: Path) -> None:
    (vault / "10_Projects/INNO_KIS_Trading/Project Dashboard.md").write_text(
        "# Dashboard\n\n<!-- BEGIN_AUTO_OBSIDIAN_AI_DASHBOARD -->\nold\n<!-- END_AUTO_OBSIDIAN_AI_DASHBOARD -->\n",
        encoding="utf-8",
    )


def test_validator_is_read_only(config_path: Path, vault: Path, tmp_path: Path, monkeypatch) -> None:
    _prepare_validator_root(tmp_path, monkeypatch)
    _write_dashboard_with_markers(vault)
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-value")

    before = sorted(str(path.relative_to(vault)) for path in vault.rglob("*"))
    assert MODULE.main(["--config", str(config_path), "--check-all"]) == 0
    after = sorted(str(path.relative_to(vault)) for path in vault.rglob("*"))

    assert before == after
    assert not (vault / ".inno_rag").exists()


def test_validator_returns_nonzero_for_missing_config(tmp_path: Path, capsys) -> None:
    assert MODULE.main(["--config", str(tmp_path / "missing.yaml"), "--check-config"]) == 2
    assert "config file is missing" in capsys.readouterr().out


def test_validator_missing_key_reports_state_only(
    config_path: Path,
    vault: Path,
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _prepare_validator_root(tmp_path, monkeypatch)
    _write_dashboard_with_markers(vault)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    assert MODULE.main(["--config", str(config_path), "--check-env"]) == 2
    output = capsys.readouterr().out
    assert "NVIDIA_API_KEY is not set" in output
    assert "secret-value" not in output


def test_validator_json_output_is_valid(config_path: Path, vault: Path, tmp_path: Path, monkeypatch, capsys) -> None:
    _prepare_validator_root(tmp_path, monkeypatch)
    _write_dashboard_with_markers(vault)
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-value")

    assert MODULE.main(["--config", str(config_path), "--check-all", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["exit_code"] == 0
    assert isinstance(payload["checks"], list)


def test_validator_strict_turns_warn_into_nonzero(config_path: Path, tmp_path: Path, monkeypatch) -> None:
    _prepare_validator_root(tmp_path, monkeypatch)
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-value")

    assert MODULE.main(["--config", str(config_path), "--check-dashboard", "--strict"]) == 3


def test_validator_recognizes_safe_full_vault_default(config_path: Path, capsys) -> None:
    assert MODULE.main(["--config", str(config_path), "--check-config"]) == 0
    output = capsys.readouterr().out
    assert "full vault index is disabled by default" in output


def test_validator_fails_when_operation_log_escapes_vault(config_path: Path, capsys) -> None:
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            '  destination: "10_Projects/INNO_KIS_Trading/06_Logs/Obsidian AI Pipeline Log.md"',
            '  destination: "../escape.md"',
        ),
        encoding="utf-8",
    )

    assert MODULE.main(["--config", str(config_path), "--check-config"]) == 2
    assert "Path escapes vault confinement" in capsys.readouterr().out


def test_validator_warns_when_dashboard_markers_missing(
    config_path: Path,
    vault: Path,
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    _prepare_validator_root(tmp_path, monkeypatch)
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-value")
    (vault / "10_Projects/INNO_KIS_Trading/Project Dashboard.md").write_text("# Dashboard\n", encoding="utf-8")

    assert MODULE.main(["--config", str(config_path), "--check-dashboard"]) == 0
    assert "dashboard file exists but markers are missing" in capsys.readouterr().out


def test_validator_detects_git_tracked_artifact(config_path: Path, vault: Path, tmp_path: Path, monkeypatch) -> None:
    _prepare_validator_root(tmp_path, monkeypatch)
    _write_dashboard_with_markers(vault)
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-value")

    def _fake_git(results, *, label: str, **kwargs) -> None:
        status = "FAIL" if label == ".env" else "OK"
        message = f"{label} is tracked by git" if label == ".env" else f"{label} is ignored by git"
        MODULE._add(results, "index", status, message)

    monkeypatch.setattr(MODULE, "_check_git_protection", _fake_git)
    assert MODULE.main(["--config", str(config_path), "--check-index"]) == 1


def test_validator_detects_unsafe_wrapper(config_path: Path, vault: Path, tmp_path: Path, monkeypatch) -> None:
    _prepare_validator_root(tmp_path, monkeypatch)
    _write_dashboard_with_markers(vault)
    monkeypatch.setenv("NVIDIA_API_KEY", "secret-value")
    (tmp_path / "scripts/run_obsidian_ai_pipeline.sh").write_text(
        "#!/usr/bin/env bash\nset -x\necho \"$NVIDIA_API_KEY\"\n",
        encoding="utf-8",
    )

    assert MODULE.main(["--config", str(config_path), "--check-index"]) == 1
