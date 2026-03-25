import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def load_eval_module() -> ModuleType:
    eval_path = Path(__file__).resolve().parents[1] / "eval.py"
    spec = importlib.util.spec_from_file_location("usewise_eval_script", eval_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_resolve_models_prefers_cli_values() -> None:
    eval_module = load_eval_module()

    result = eval_module.resolve_models(
        ["openai/gpt-4.1-mini", "anthropic/claude-3.5-sonnet"],
        env_models="should,not,use",
    )

    assert result == ["openai/gpt-4.1-mini", "anthropic/claude-3.5-sonnet"]


def test_discover_policy_paths_defaults_to_privacy_policy_files_only(
    tmp_path: Path,
) -> None:
    eval_module = load_eval_module()
    (tmp_path / "apple_privacy_policy.txt").write_text("Apple", encoding="utf-8")
    (tmp_path / "sample_privacy_policy.txt").write_text("Sample", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("Ignore", encoding="utf-8")

    result = eval_module.discover_policy_paths(tmp_path)

    assert result == [
        tmp_path / "apple_privacy_policy.txt",
        tmp_path / "sample_privacy_policy.txt",
    ]


def test_discover_policy_paths_raises_for_unknown_policy(tmp_path: Path) -> None:
    eval_module = load_eval_module()
    (tmp_path / "apple_privacy_policy.txt").write_text("Apple", encoding="utf-8")

    with pytest.raises(ValueError, match="Unknown policies: missing"):
        eval_module.discover_policy_paths(tmp_path, selected_policies=["missing"])


def test_consumer_question_banks_have_expected_sizes() -> None:
    eval_module = load_eval_module()

    assert len(eval_module.CONSUMER_FLASH_QUESTIONS) == 7
    assert len(eval_module.CONSUMER_FOLLOW_UP_QUESTIONS) == 12
