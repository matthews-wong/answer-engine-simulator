"""End-to-end CLI test through the offline path."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from answersim.cli import main


def test_cli_runs_offline_and_reports_citation(corpus_dir: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "how does provisioned concurrency reduce cold starts",
            "--content",
            str(corpus_dir),
            "--no-claude",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Synthesis mode: extractive" in result.output
    assert "provisioned-concurrency.md" in result.output
    assert "Cited pages:" in result.output


def test_cli_errors_on_missing_corpus(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["any query", "--content", str(tmp_path / "does-not-exist"), "--no-claude"],
    )

    assert result.exit_code != 0
    assert "Content directory not found" in result.output
