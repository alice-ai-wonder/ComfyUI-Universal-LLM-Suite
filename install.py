import subprocess
import sys

def install():
    """Auto-install dependencies for Universal LLM Suite."""
    packages = ["google-genai", "openai"]
    for pkg in packages:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg],
                stdout=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            print(f"[Universal LLM Suite] Failed to install {pkg}. Please run manually:")
            print(f"  {sys.executable} -m pip install {pkg}")

install()
