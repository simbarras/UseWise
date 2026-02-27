import logging
import shutil
import subprocess
import sys
from pathlib import Path

from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def static_analysis() -> None:
    logger.info(" Running mypy...")
    subprocess.run([sys.executable, "-m", "mypy"], check=False)
    logger.info(" Running ruff...")
    subprocess.run([sys.executable, "-m", "ruff", "check"], check=False)

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
    explainer = PrivacyPolicyExplainer(privacy_policy)

    for chunk in explainer.invoke(
        "does the privacy policy says if they will steals or/and sell my data?"
    ):
        if chunk.content:
            print(chunk.content, end="", flush=True) # noqa: T201
    print("\n") # noqa: T201
