def mypy() -> None:
    import tempfile
    import subprocess
    from pathlib import Path

    tempdir = tempfile.gettempdir()
    target = Path(__file__)
    subprocess.run(["mypy", target, "--cache-dir", tempdir, "--pretty", "--strict"])
