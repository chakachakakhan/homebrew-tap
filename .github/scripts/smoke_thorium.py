"""Launch the installed reader with isolated data and require a visible X window."""

import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="thorium-smoke-") as directory:
    env = os.environ.copy()
    env.pop("ELECTRON_RUN_AS_NODE", None)
    for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
        env[key] = str(Path(directory) / key.lower())
    log_path = Path(directory) / "launch.log"
    with log_path.open("w+") as log:
        process = subprocess.Popen(["thorium-reader"], env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"Thorium exited before opening a window: {process.returncode}")
                windows = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True)
                if '"Thorium"' in windows or '"Thorium Reader"' in windows:
                    # Catch crashes immediately after window creation too.
                    time.sleep(5)
                    windows = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True)
                    if process.poll() is not None or not (
                        '"Thorium"' in windows or '"Thorium Reader"' in windows
                    ):
                        raise RuntimeError("Thorium exited or closed its window after startup")
                    print("Installed Thorium Reader opened its desktop window")
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Thorium did not open a window within 60 seconds")
        finally:
            # Capture launch diagnostics before our shutdown affects child processes.
            log.seek(0)
            print(log.read())
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
