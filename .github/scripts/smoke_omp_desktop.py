"""Require an installed desktop window and a successful real OMP RPC handshake."""

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


def proxy():
    """Forward unchanged stdio to the real installed engine; log handshake only."""
    engine = os.environ["OMP_TAP_SMOKE_ENGINE"]
    args = sys.argv[1:]
    if "--mode" not in args:
        os.execv(engine, [engine, *args])
    child = subprocess.Popen([engine, *args], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=sys.stderr)

    def feed():
        try:
            for line in sys.stdin.buffer:
                child.stdin.write(line)
                child.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            child.stdin.close()

    def stop(signum, frame):
        child.terminate()
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGTERM, stop)
    threading.Thread(target=feed, daemon=True).start()
    try:
        for line in child.stdout:
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
            try:
                response = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if (isinstance(response, dict) and response.get("type") == "response"
                    and response.get("command") == "get_state"):
                record = {
                    "command": "get_state", "success": response.get("success"),
                    "has_model": bool((response.get("data") or {}).get("model")),
                }
                descriptor = os.open(os.environ["OMP_TAP_SMOKE_RPC_LOG"],
                                     os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
                try:
                    os.write(descriptor, (json.dumps(record) + "\n").encode())
                finally:
                    os.close(descriptor)
        return child.wait()
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


def inspect_installation(prefix):
    launcher = (prefix / "bin/omp-desktop").resolve(strict=True)
    app = launcher.parent / "squashfs-root"
    executable = app / "usr/bin/omp-desktop"
    binary = executable.read_bytes()
    if not binary.startswith(b"\x7fELF") or not os.access(executable, os.X_OK):
        raise RuntimeError("The extracted Linux desktop executable is missing")
    if (binary.count(b"__TAURI_BUNDLE_TYPE_VAR_UNK") != 1
            or b"__TAURI_BUNDLE_TYPE_VAR_APP" in binary):
        raise RuntimeError("Homebrew must own updates; the bundle marker changed upstream")
    text = launcher.read_text()
    if (f'export PATH="{prefix}/bin:{prefix}/sbin:' not in text
            or f'exec "{app}/AppRun" "$@"' not in text):
        raise RuntimeError("The launcher must discover Homebrew OMP and preserve project arguments")
    app_run = (app / "AppRun").read_text()
    if ('exec "$this_dir"/AppRun.wrapped "$@"' in app_run
            or 'exec "$this_dir/usr/bin/omp-desktop" "$@"' not in app_run
            or 'export LD_LIBRARY_PATH=' not in app_run):
        raise RuntimeError("Use bundled GUI libraries without redirecting external Python tools")
    print("Extracted desktop, Homebrew PATH, and notify-only update marker verified")


def connected(log_path):
    if not log_path.exists():
        return False
    for line in log_path.read_text().splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if (record.get("command") == "get_state" and record.get("success") is True
                and record.get("has_model") is True):
            return True
    return False


def smoke(prefix):
    engine = prefix / "bin/omp"
    real_engine = engine.resolve(strict=True)
    backup = prefix / "bin/omp-tap-smoke-original"
    if backup.exists() or backup.is_symlink():
        raise RuntimeError("Refusing to overwrite an existing smoke-test backup")
    with tempfile.TemporaryDirectory(prefix="omp-desktop-smoke-") as directory:
        root = Path(directory)
        project = root / "project"
        project.mkdir()
        agent = root / "agent"
        agent.mkdir()
        # Upstream's bootstrap permits RPC initialization without credentials.
        # We never send a prompt or make an inference request.
        (agent / "models.yml").write_text("providers:\n  anthropic:\n    auth: none\n")
        env = os.environ.copy()
        for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
            env[key] = str(root / key.lower())
        env["OMP_CODING_AGENT_DIR"] = str(agent)
        env["PI_CODING_AGENT_DIR"] = str(agent)
        env["PATH"] = "/usr/bin:/bin"
        env["GDK_BACKEND"] = "x11"
        env["OMP_TAP_SMOKE_PROXY"] = "1"
        env["OMP_TAP_SMOKE_ENGINE"] = str(real_engine)
        env["OMP_TAP_SMOKE_RPC_LOG"] = str(root / "rpc.jsonl")
        script = Path(__file__).resolve()
        engine.rename(backup)
        process = None
        try:
            # This proxy runs the actual Homebrew engine, including help probes.
            engine.write_text(
                "#!/usr/bin/python3\nimport runpy\n"
                f"runpy.run_path({str(script)!r}, run_name='__main__')\n"
            )
            engine.chmod(0o755)
            with (root / "launch.log").open("w+") as log:
                process = subprocess.Popen([str(prefix / "bin/omp-desktop"), str(project)],
                                           env=env, stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True)
                try:
                    deadline = time.monotonic() + 90
                    while time.monotonic() < deadline:
                        if process.poll() is not None:
                            raise RuntimeError(f"Desktop exited during startup: {process.returncode}")
                        windows = subprocess.check_output(
                            ["xwininfo", "-root", "-tree"], text=True,
                        )
                        if ('"OMP Desktop"' in windows
                                and connected(root / "rpc.jsonl")):
                            time.sleep(5)
                            if process.poll() is not None:
                                raise RuntimeError("Desktop crashed after its RPC handshake")
                            windows = subprocess.check_output(
                                ["xwininfo", "-root", "-tree"], text=True,
                            )
                            if '"OMP Desktop"' not in windows:
                                raise RuntimeError("Desktop closed its window after startup")
                            print("Desktop window connected to real OMP from a minimal menu PATH")
                            break
                        time.sleep(1)
                    else:
                        raise RuntimeError("No desktop window and real get_state handshake within 90s")
                finally:
                    log.seek(0)
                    print(log.read())
                    if (root / "rpc.jsonl").exists():
                        print((root / "rpc.jsonl").read_text())
        finally:
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
            engine.unlink(missing_ok=True)
            backup.rename(engine)


if __name__ == "__main__":
    if os.environ.get("OMP_TAP_SMOKE_PROXY") == "1":
        sys.exit(proxy())
    prefix = Path(subprocess.check_output(["brew", "--prefix"], text=True).strip())
    inspect_installation(prefix)
    if "--inspect" not in sys.argv[1:]:
        smoke(prefix)
