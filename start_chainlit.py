#!/usr/bin/env python
"""Startup script for Chainlit with proper environment loading."""
import os
import subprocess
import sys
import threading
import time
import webbrowser

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to Python path
src_path = os.path.join(os.path.dirname(__file__), "src")
os.environ["PYTHONPATH"] = f"{src_path}:{os.environ.get('PYTHONPATH', '')}"

# Get the URL to open (prefer CHAINLIT_URL for dev tunnels)
chainlit_url = os.getenv("CHAINLIT_URL", "http://localhost:8080")


def open_browser():
    """Open browser after server starts."""
    time.sleep(3)
    webbrowser.open(chainlit_url)
    print(f"\n  Opening browser: {chainlit_url}\n")


# Start browser opener in background thread
threading.Thread(target=open_browser, daemon=True).start()

# Run chainlit
subprocess.run(
    [
        sys.executable,
        "-m",
        "chainlit",
        "run",
        "src/triagent/web/container/chainlit_app.py",
        "--port",
        "8080",
    ],
    cwd=os.path.dirname(__file__),
)
