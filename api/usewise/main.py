import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import uvicorn

from llm.privacy_policy_explainer import PrivacyPolicyExplainer
from llm.schemas import FlashSummaryReturnType

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def static_analysis() -> None:
    parser = argparse.ArgumentParser(prog="usewise-sa")
    parser.add_argument(
        "ignore_path",
        nargs="?",
        default=None,
        help="Path/pattern to exclude from both mypy and ruff.",
    )
    args = parser.parse_args()

    ignore_path = args.ignore_path
    mypy_cmd = [sys.executable, "-m", "mypy"]
    ruff_cmd = [sys.executable, "-m", "ruff", "check"]

    if ignore_path:
        mypy_cmd.extend(["--exclude", ignore_path])
        ruff_cmd.extend(["--exclude", ignore_path])

    logger.info(" Running mypy...")
    subprocess.run(mypy_cmd, check=False)
    logger.info(" Running ruff...")
    subprocess.run(ruff_cmd, check=False)

    if Path(".ruff_cache").exists():
        shutil.rmtree(".ruff_cache")


def test() -> None:
    try:
        subprocess.run([sys.executable, "-m", "pytest"], check=False)
    finally:
        if Path("coverage.xml").exists():
            Path("coverage.xml").unlink()
        if Path(".coverage").exists():
            Path(".coverage").unlink()
        if Path(".pytest_cache").exists():
            shutil.rmtree(".pytest_cache")


def try_privacy_policy_explainer() -> None:
    with Path("test_data/sample_privacy_policy.txt").open("r") as f:
        privacy_policy = f.read()
    explainer = PrivacyPolicyExplainer(privacy_policy, "llama-3.3-70b-versatile")

    summary_questions = [
        ("Data is shared with third parties.", FlashSummaryReturnType.FLAG),
        ("Cookies or tracking technologies are used.", FlashSummaryReturnType.FLAG),
        ("For how much time the data gonna be stored.", FlashSummaryReturnType.TIME),
        ("Users can request deletion of their data.", FlashSummaryReturnType.FLAG),
        ("The policy can change without notice.", FlashSummaryReturnType.FLAG),
    ]

    flash_summary = explainer.get_flash_summary(summary_questions)

    print("\n=== Flash Summary ===")  # noqa: T201

    for idx, ((question, _), answer) in enumerate(
        zip(summary_questions, flash_summary.answers, strict=False),
        start=1,
    ):
        if answer.type == FlashSummaryReturnType.FLAG:
            value = "Yes" if answer.value else "No"
        else:
            value = cast("str", answer.value)

        print(f"{idx:>2}. {question}")  # noqa: T201
        print(f"    → {value}")  # noqa: T201

    print(f"\nPrivacy risk score: {flash_summary.score}/10")  # noqa: T201
    print("=====================\n")  # noqa: T201

    questions = [
        "does the privacy policy says if they will steals or/and sell my data?",
        "does they will track me?"
    ]

    for response in explainer.get_questions_answers(questions):
        print(response) # noqa: T201
        print("\n\n#############################################\n\n") # noqa: T201

    print() # noqa: T201


def main() -> None:
    logger.info("Starting UseWise API...")
    uvicorn.run("restApi.router:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
