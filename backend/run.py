import os
import sys
import subprocess
import shutil
from pathlib import Path

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# Detect the operating system to set the correct virtual environment directory
IS_WINDOWS = sys.platform == "win32"
VENV_SUBDIR = ".venv/Scripts" if IS_WINDOWS else ".venv/bin"

# Define paths to executables inside the virtual environment
VENV_BIN = SCRIPT_DIR / VENV_SUBDIR
PYTHON = VENV_BIN / ("python.exe" if IS_WINDOWS else "python")
PIP = VENV_BIN / ("pip.exe" if IS_WINDOWS else "pip")
PYTEST = VENV_BIN / ("pytest.exe" if IS_WINDOWS else "pytest")
BLACK = VENV_BIN / ("black.exe" if IS_WINDOWS else "black")


def install():
    print("--> Creating virtual environment and installing dependencies...")

    venv_path = SCRIPT_DIR / ".venv"

    # Use the system's current Python executable to create the venv
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    # Upgrade pip using the venv's Python (avoids relying on the pip shim)
    subprocess.run(
        [str(PYTHON), "-m", "pip", "install", "--upgrade", "pip"], check=True
    )

    file_name = "requirements.txt"

    if IS_WINDOWS:
        file_name = "requirements-windows.txt"

    req = SCRIPT_DIR / file_name

    if req.exists():
        print(f"--> Installing from dependencies from {file_name} file.")
        subprocess.run(
            [str(PYTHON), "-m", "pip", "install", "-r", str(req)], check=True
        )

    print("--> Installation complete.")


def dev():
    print("--> Starting the project in dev mode...")
    if not PYTHON.exists():
        print(
            "Error: Virtual environment not found. Please run 'python run.py install' first."
        )
        sys.exit(1)

    print("    Starting Docker services...")
    subprocess.run(["docker", "compose", "up", "-d"], check=True, cwd=SCRIPT_DIR)
    print("    Docker services started.")

    subprocess.run([str(PYTHON), str(SCRIPT_DIR / "main.py")], check=True)


def prod():
    print("--> Starting the project in prod mode...")
    if not PYTHON.exists():
        print(
            "Error: Virtual environment not found. Please run 'python run.py install' first."
        )
        sys.exit(1)

    print("    Starting Docker services...")
    subprocess.run(["docker", "compose", "--profile", "prod", "up", "-d"], check=True, cwd=SCRIPT_DIR)
    print("    Docker services started.")


def test():
    print("--> Running tests...")
    if not PYTEST.exists():
        print("Error: Pytest not found. Please run 'python run.py install' first.")
        sys.exit(1)
    subprocess.run([str(PYTEST)], check=True)


def clean():
    print("--> Cleaning up temporary files...")

    venv_path = SCRIPT_DIR / ".venv"
    if venv_path.exists():
        shutil.rmtree(venv_path)
        print(f"    Removed {venv_path}")

    # Walk through the project and remove Python/testing caches
    cache_dirs = {"__pycache__", ".pytest_cache"}
    for root, dirs, _ in os.walk(SCRIPT_DIR):
        for d in list(dirs):
            if d in cache_dirs:
                dir_path = Path(root) / d
                shutil.rmtree(dir_path)
                print(f"    Removed {dir_path}")
                dirs.remove(d)  # prevent descending into just-deleted dir

    print("--> Clean up complete.")


def format():
    print("--> Formatting code with black...")
    if not BLACK.exists():
        print("Error: black not found. Please run 'python run.py install' first.")
        sys.exit(1)
    subprocess.run([str(BLACK), "."], check=True)
    print("--> Formatting complete.")


def pre_commit():
    print("--> Running pre-commit checks...")

    file_name = "requirements.txt"

    if IS_WINDOWS:
        file_name = "requirements-windows.txt"

    print(f"    [1/3] Updating {file_name}...")

    req = SCRIPT_DIR / file_name

    result = subprocess.run(
        [str(PYTHON), "-m", "pip", "freeze"],
        check=True,
        capture_output=True,
        text=True,
    )
    req.write_text(result.stdout, encoding="utf-8")
    print(f"          Written to {req}")

    print("    [2/3] Running tests...")
    test()

    print("    [3/3] Formatting code...")
    format()

    print("--> Pre-commit checks passed. Safe to commit.")


def show_help():
    print("Available commands:")
    print(
        "  python run.py install     - Create virtual environment and install dependencies"
    )
    print("  python run.py prod        - Execute the main application in production mode")
    print("  python run.py dev         - Execute the main application in development mode")
    print("  python run.py test        - Run the test suite with pytest")
    print("  python run.py format      - Format code with black")
    print(
        "  python run.py pre-commit  - Update requirements.txt, run tests, and format"
    )
    print(
        "  python run.py clean       - Remove virtual environment, caches, and temp files"
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    task = sys.argv[1].lower()

    if task == "install":
        install()
    elif task == "prod":
        prod()
    elif task == "dev":
        dev()
    elif task == "test":
        test()
    elif task == "format":
        format()
    elif task == "pre-commit":
        pre_commit()
    elif task == "clean":
        clean()
    else:
        print(f"Unknown task: '{task}'")
        show_help()
