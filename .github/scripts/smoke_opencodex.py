"""Exercise an installed runtime and dashboard, optionally the Linux desktop window."""

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path


def smoke(desktop):
    version = subprocess.check_output(["ocx", "--version"], text=True).strip().split()[-1]
    with tempfile.TemporaryDirectory(prefix="opencodex-smoke-") as directory:
        root = Path(directory)
        env = os.environ.copy()
        for key in ("OPENCODEX_HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR",
                    "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
            location = root / key.lower()
            location.mkdir(mode=0o700)
            env[key] = str(location)
        env.update(NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost",
                   WEBKIT_DISABLE_COMPOSITING_MODE="1", GDK_BACKEND="x11")
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            port = reserved.getsockname()[1]
        config = Path(env["OPENCODEX_HOME"])
        (config / "config.json").write_text(json.dumps({"port": port}))
        command = ["opencodex-desktop"] if desktop else ["ocx", "start", "--port", str(port)]
        # Bypass any unrelated proxy configuration on the hosted runner.
        http = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with (root / "launch.log").open("w+") as log:
            process = subprocess.Popen(command, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError(f"OpenCodex exited early: {process.returncode}")
                    try:
                        with http.open(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
                            health = json.load(response)
                        ready = (health.get("service") == "opencodex"
                                 and health.get("version") == version and health.get("port") == port)
                        if desktop:
                            windows = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True)
                            ready = ready and '"OpenCodex"' in windows
                        if ready:
                            break
                    except (OSError, ValueError):
                        pass
                    time.sleep(0.5)
                else:
                    raise RuntimeError("Installed OpenCodex did not become ready within 60 seconds")
                with http.open(f"http://127.0.0.1:{port}/", timeout=5) as response:
                    dashboard = response.read().decode()
                if "<html" not in dashboard.lower():
                    raise RuntimeError("The installed dashboard is missing")
                # Verify a built asset too; an index alone can hide a broken resource path.
                asset = re.search(r'(?:src|href)="(/assets/[^\"]+\.(?:js|css))"', dashboard)
                if not asset:
                    raise RuntimeError("The installed dashboard has no bundled asset reference")
                with http.open(f"http://127.0.0.1:{port}{asset[1]}", timeout=5) as response:
                    if not response.read():
                        raise RuntimeError("Empty dashboard asset")
                time.sleep(3)
                if process.poll() is not None:
                    raise RuntimeError("OpenCodex crashed after startup")
                print(f"Installed OpenCodex {version}: healthy proxy and dashboard"
                      + (", desktop window opened" if desktop else ""))
            finally:
                log.seek(0)
                print(log.read())
                subprocess.run(["ocx", "stop"], env=env, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=20, check=False)
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--desktop", action="store_true")
    smoke(parser.parse_args().desktop)
