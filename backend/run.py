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

    # Installing requirements
    subprocess.run([str(PYTHON), "-m", "pip", "install", ".[dev]"], check=True)

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
    print("    Starting Docker services...")

    process_env = os.environ.copy()

    process_env["ENV_FILE"] = ".env.prod"

    docker_command = [
        "docker",
        "compose",
        "--profile",
        "prod",
        "up",
        "-d",
        "--build",
        "backend",
    ]

    subprocess.run(
        docker_command, check=True, cwd=SCRIPT_DIR, env=process_env, shell=IS_WINDOWS
    )

    print("    Project started.")


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

    print("    [1/2] Running tests...")
    test()

    print("    [2/2] Formatting code...")
    format()

    print("--> Pre-commit checks passed. Safe to commit.")


def show_help():
    print("Available commands:")
    print(
        "  python run.py install     - Create virtual environment and install dependencies"
    )
    print(
        "  python run.py prod        - Execute the main application in production mode"
    )
    print(
        "  python run.py dev         - Execute the main application in development mode"
    )
    print("  python run.py test        - Run the test suite with pytest")
    print("  python run.py format      - Format code with black")
    print("  python run.py pre-commit  - Run tests and format")
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
