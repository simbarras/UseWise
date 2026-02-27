from pathlib import Path


def static_analysis() -> None:
    import logging
    import shutil
    import subprocess
    import sys
    import tempfile

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


    tempdir = tempfile.gettempdir()
    target = Path(__file__).parent
    logger.info(" Running mypy...")
    subprocess.run(
        [sys.executable, "-m", "mypy", str(target), "--cache-dir", tempdir,
            "--pretty", "--strict"],
        check=False,
    )
    logger.info(" Running ruff...")
    subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(target), "--fix"],
        check=False,
    )

    if Path(".ruff_cache").exists():
        shutil.rmtree(".ruff_cache")



def test() -> None:
    import shutil

    import pytest

    try:
        pytest.main(["-v", "tests"])
    finally:
        if Path("coverage.xml").exists():
            Path("coverage.xml").unlink()
        if Path(".coverage").exists():
            Path(".coverage").unlink()
        if Path(".pytest_cache").exists():
            shutil.rmtree(".pytest_cache")


def try_privacy_policy_explainer() -> None:
    from usewise.llm.privacy_policy_explainer import PrivacyPolicyExplainer

    with Path("test_data/sample_privacy_policy.txt").open("r") as f:
        privacy_policy = f.read()
    explainer = PrivacyPolicyExplainer(privacy_policy)
    explainer.invoke(
        "does the privacy policy says if they will steals or/and sell my data?"
    )
