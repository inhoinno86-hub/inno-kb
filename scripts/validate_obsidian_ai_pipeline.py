#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from inno_obsidian_ai.config import AppConfig, ConfigError, load_config


@dataclass(frozen=True)
class CheckResult:
    category: str
    status: str
    message: str


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to config YAML")
    parser.add_argument("--path-prefix", action="append", default=[], help="Restrict status/index checks to this path prefix")
    parser.add_argument("--check-env", action="store_true", help="Check runtime environment")
    parser.add_argument("--check-config", action="store_true", help="Check config schema and safe defaults")
    parser.add_argument("--check-vault", action="store_true", help="Check vault paths")
    parser.add_argument("--check-dashboard", action="store_true", help="Check dashboard path and markers")
    parser.add_argument("--check-index", action="store_true", help="Check index/gitignore/wrapper safety")
    parser.add_argument("--check-proposals", action="store_true", help="Check proposal directory status")
    parser.add_argument("--check-all", action="store_true", help="Run all checks")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="Treat WARN as non-zero")
    return parser


def _should_run(args: argparse.Namespace, field_name: str) -> bool:
    if args.check_all:
        return True
    return bool(getattr(args, field_name))


def _add(results: list[CheckResult], category: str, status: str, message: str) -> None:
    results.append(CheckResult(category=category, status=status, message=message))


def _safe_repo_relative(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def _git_run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_tracked(relative_path: str) -> bool | None:
    result = _git_run("ls-files", "--error-unmatch", "--", relative_path)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def _git_ignored(relative_path: str) -> bool | None:
    result = _git_run("check-ignore", "-q", "--", relative_path)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None


def _ancestor_writable(path: Path) -> bool:
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current.exists() and os.access(current, os.W_OK)


def _interpreter_in_venv() -> bool:
    venv_root = (ROOT / ".venv").resolve()
    try:
        Path(sys.executable).absolute().relative_to(ROOT / ".venv")
    except ValueError:
        return sys.prefix != getattr(sys, "base_prefix", sys.prefix) and Path(sys.prefix).resolve() == venv_root
    return True


def _check_git_protection(
    results: list[CheckResult],
    *,
    category: str,
    label: str,
    path: Path,
) -> None:
    relative_path = _safe_repo_relative(path)
    if relative_path is None:
        _add(results, category, "WARN", f"{label} is outside repo root; git ignore check skipped")
        return

    tracked = _git_tracked(relative_path)
    ignored = _git_ignored(relative_path)
    if tracked is None or ignored is None:
        _add(results, category, "WARN", f"git ignore status for {label} could not be determined")
        return
    if tracked:
        _add(results, category, "FAIL", f"{label} is tracked by git")
        return
    if ignored:
        _add(results, category, "OK", f"{label} is ignored by git")
        return
    _add(results, category, "WARN", f"{label} is not tracked but is not ignored by git")


def _check_wrapper_safety(results: list[CheckResult]) -> None:
    wrapper_path = ROOT / "scripts" / "run_obsidian_ai_pipeline.sh"
    if not wrapper_path.exists():
        _add(results, "index", "FAIL", "shell wrapper is missing")
        return

    content = wrapper_path.read_text(encoding="utf-8")
    unsafe_patterns = [
        r"set -x",
        r"printenv",
        r"env\s*\|",
        r"declare\s+-p\s+NVIDIA_API_KEY",
        r'echo\s+.*(\$NVIDIA_API_KEY|\$\{NVIDIA_API_KEY)',
        r'printf\s+.*(\$NVIDIA_API_KEY|\$\{NVIDIA_API_KEY)',
    ]
    if any(re.search(pattern, content) for pattern in unsafe_patterns):
        _add(results, "index", "FAIL", "shell wrapper may print NVIDIA_API_KEY")
    else:
        _add(results, "index", "OK", "shell wrapper does not echo NVIDIA_API_KEY")

    if "--write" in content:
        _add(results, "index", "WARN", "shell wrapper source mentions --write; verify operator intent")
    else:
        _add(results, "index", "OK", "shell wrapper default invocation does not force write mode")


def _check_status_smoke(
    results: list[CheckResult],
    *,
    config_path: Path,
    path_prefixes: list[str],
) -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run_obsidian_ai_pipeline.py"),
        "--config",
        str(config_path),
        "--status",
    ]
    for prefix in path_prefixes:
        command.extend(["--path-prefix", prefix])

    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if result.returncode == 0:
        _add(results, "index", "OK", "read-only pipeline status CLI is executable")
        return
    _add(results, "index", "FAIL", "read-only pipeline status CLI failed")


def _effective_prefixes(config: AppConfig, cli_prefixes: list[str]) -> list[str]:
    if cli_prefixes:
        return list(dict.fromkeys(cli_prefixes))
    return list(config.automation.default_index_path_prefixes)


def _run_checks(args: argparse.Namespace) -> tuple[list[CheckResult], AppConfig | None]:
    results: list[CheckResult] = []
    config_path = Path(args.config).expanduser().resolve()
    config: AppConfig | None = None

    if _should_run(args, "check_config"):
        if not config_path.exists():
            _add(results, "config", "FAIL", "config file is missing")
        else:
            _add(results, "config", "OK", "config file exists")
            try:
                config = load_config(config_path)
            except (ConfigError, FileNotFoundError) as exc:
                _add(results, "config", "FAIL", f"config could not be loaded: {exc}")
            else:
                _add(results, "config", "OK", "config loaded")
                if config.safety.dry_run and config.automation.default_mode != "write":
                    _add(results, "config", "OK", "write mode is not default")
                else:
                    _add(results, "config", "FAIL", "write mode is enabled by default")

                if not config.automation.allow_full_vault_index:
                    _add(results, "config", "OK", "full vault index is disabled by default")
                else:
                    _add(results, "config", "FAIL", "full vault index is enabled by default")

                if _effective_prefixes(config, args.path_prefix):
                    _add(results, "config", "OK", "default path prefixes configured")
                else:
                    _add(results, "config", "FAIL", "default path prefixes are empty")

    if config is None:
        try:
            config = load_config(config_path)
        except (ConfigError, FileNotFoundError):
            config = None

    if _should_run(args, "check_env"):
        if (ROOT / ".venv").exists():
            _add(results, "env", "OK", ".venv exists")
        else:
            _add(results, "env", "WARN", ".venv is missing")

        if _interpreter_in_venv():
            _add(results, "env", "OK", "validator is running from .venv")
        else:
            _add(results, "env", "WARN", "run validator via .venv/bin/python for live preflight")

        if os.environ.get("NVIDIA_API_KEY"):
            _add(results, "env", "OK", "NVIDIA_API_KEY is set")
        else:
            _add(results, "env", "FAIL", "NVIDIA_API_KEY is not set")

    if config is None:
        return results, None

    if _should_run(args, "check_vault"):
        if config.codex_logs_dir.exists():
            _add(results, "vault", "OK", "00_Inbox/codex_logs exists")
        else:
            _add(results, "vault", "FAIL", "00_Inbox/codex_logs is missing")

        operation_log_path = config.operation_log_path
        if operation_log_path is None:
            _add(results, "vault", "WARN", "operation log destination is not configured")
        elif operation_log_path.exists() or _ancestor_writable(operation_log_path.parent):
            _add(results, "vault", "OK", "operation log destination stays inside vault")
        else:
            _add(results, "vault", "FAIL", "operation log destination is not safely creatable")

    if _should_run(args, "check_dashboard"):
        dashboard_path = config.dashboard_path
        if not config.dashboard.auto_section_start.strip() or not config.dashboard.auto_section_end.strip():
            _add(results, "dashboard", "FAIL", "dashboard markers are not configured")
        else:
            _add(results, "dashboard", "OK", "dashboard markers configured")

        if dashboard_path is None:
            _add(results, "dashboard", "WARN", "dashboard path is not configured")
        elif dashboard_path.exists():
            content = dashboard_path.read_text(encoding="utf-8")
            if (
                config.dashboard.auto_section_start in content
                and config.dashboard.auto_section_end in content
            ):
                _add(results, "dashboard", "OK", "dashboard file and markers exist")
            else:
                _add(results, "dashboard", "WARN", "dashboard file exists but markers are missing")
        elif _ancestor_writable(dashboard_path.parent):
            _add(results, "dashboard", "WARN", "dashboard file does not exist yet")
        else:
            _add(results, "dashboard", "FAIL", "dashboard path is not safely creatable")

    if _should_run(args, "check_proposals"):
        if config.review_dir.exists():
            proposal_count = len(list(config.review_dir.rglob("*.proposal.md")))
            _add(results, "proposals", "OK", f"proposal directory exists ({proposal_count} proposal files found)")
        elif _ancestor_writable(config.review_dir.parent):
            _add(results, "proposals", "WARN", "proposal directory does not exist yet")
        else:
            _add(results, "proposals", "FAIL", "proposal directory is not safely creatable")

    if _should_run(args, "check_index"):
        _check_git_protection(results, category="index", label="live config", path=ROOT / "config/obsidian_ai.yaml")
        _check_git_protection(results, category="index", label=".env", path=ROOT / ".env")
        _check_git_protection(results, category="index", label=".venv", path=ROOT / ".venv")
        _check_git_protection(results, category="index", label=".inno_rag", path=ROOT / ".inno_rag")
        _check_git_protection(results, category="index", label="manifest path", path=config.manifest_path)
        _check_git_protection(results, category="index", label="Chroma persist dir", path=config.chroma_dir)
        _check_wrapper_safety(results)
        _check_status_smoke(
            results,
            config_path=config_path,
            path_prefixes=_effective_prefixes(config, args.path_prefix),
        )

    return results, config


def _exit_code(results: list[CheckResult], *, strict: bool) -> int:
    has_fail = any(result.status == "FAIL" for result in results)
    has_warn = any(result.status == "WARN" for result in results)
    has_config_or_env_fail = any(
        result.status == "FAIL" and result.category in {"config", "env"}
        for result in results
    )
    if has_config_or_env_fail:
        return 2
    if has_fail:
        return 1
    if strict and has_warn:
        return 3
    return 0


def _print_text(results: list[CheckResult]) -> None:
    print("OBSIDIAN AI PIPELINE PREFLIGHT")
    print()
    for result in results:
        print(f"[{result.status}] {result.message}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not any(
        [
            args.check_env,
            args.check_config,
            args.check_vault,
            args.check_dashboard,
            args.check_index,
            args.check_proposals,
            args.check_all,
        ]
    ):
        args.check_all = True

    try:
        results, config = _run_checks(args)
        code = _exit_code(results, strict=args.strict)
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": code == 0,
                        "exit_code": code,
                        "config_path": str(Path(args.config).expanduser().resolve()),
                        "vault_path": str(config.vault_path) if config is not None else "",
                        "checks": [asdict(result) for result in results],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            _print_text(results)
        return code
    except Exception as exc:  # pragma: no cover
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "exit_code": 4,
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print("OBSIDIAN AI PIPELINE PREFLIGHT")
            print()
            print(f"[FAIL] unexpected validator exception: {exc}")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
