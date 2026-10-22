"""Exercise the installed Paseo CLI and Linux desktop in isolated user dirs."""

import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def renderer_sandbox(root_pid, proc_root=Path("/proc")):
    parent_map = {}
    args_by_pid = {}
    for entry in proc_root.iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            pid = int(entry.name)
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            parent_map[pid] = int(fields[1])
            args_by_pid[pid] = (entry / "cmdline").read_bytes().split(b"\0")
        except (OSError, ValueError, IndexError):
            continue
    descendants = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent in parent_map.items():
            if parent in descendants and pid not in descendants:
                descendants.add(pid)
                changed = True
    scoped_processes = []
    renderer_without_status = None
    for pid in descendants - {root_pid}:
        args = args_by_pid.get(pid, [])
        joined_args = b" ".join(arg for arg in args if arg)
        options = joined_args.split()
        args_text = joined_args.decode(errors="replace")
        scoped_processes.append(f"{pid}: {args_text[:240]}")
        if b"--type=renderer" not in options:
            continue
        enabled = b"--enable-sandbox" in options and b"--no-sandbox" not in options
        try:
            status = (proc_root / str(pid) / "status").read_text()
        except OSError:
            renderer_without_status = {
                "pid": pid, "sandbox_flag": enabled,
                "no_sandbox_flag": b"--no-sandbox" in options,
                "enforced": False, "status_readable": False,
                "args": args_text,
            }
            continue
        seccomp = re.search(r"^Seccomp:\s+(\d+)$", status, re.MULTILINE)
        no_new_privs = re.search(r"^NoNewPrivs:\s+(\d+)$", status, re.MULTILINE)
        enforced = bool(seccomp and seccomp[1] == "2"
                        and no_new_privs and no_new_privs[1] == "1")
        return {"pid": pid, "sandbox_flag": enabled,
                "no_sandbox_flag": b"--no-sandbox" in options,
                "enforced": enforced,
                "status_readable": True, "args": args_text}, scoped_processes
    return renderer_without_status, scoped_processes


def stop_group(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


def main():
    with tempfile.TemporaryDirectory(prefix="paseo-smoke-") as directory:
        home = Path(directory)
        env = os.environ.copy()
        env.update({
            "HOME": str(home),
            "PASEO_HOME": str(home / ".paseo"),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "XDG_DATA_HOME": str(home / ".local/share"),
            "GDK_BACKEND": "x11",
            "LIBGL_ALWAYS_SOFTWARE": "1",
            "PASEO_ELECTRON_FLAGS": (
                "--disable-gpu --use-gl=swiftshader --enable-unsafe-swiftshader"),
        })
        for key in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
            Path(env[key]).mkdir(parents=True)
        subprocess.run(["paseo", "--help"], env=env, check=True,
                       stdout=subprocess.DEVNULL)
        version = subprocess.check_output(["paseo", "--version"], env=env, text=True).strip()
        expected = os.environ["PASEO_EXPECTED_VERSION"]
        reported_versions = re.findall(r"(?<![\d.])v?(\d+(?:\.\d+)+)(?![\d.])", version)
        if expected not in reported_versions:
            raise RuntimeError(f"CLI reports {version!r}; cask version is {expected}")
        with tempfile.TemporaryFile(mode="w+t") as log:
            namespace_probe = subprocess.run(
                ["unshare", "--user", "--map-root-user", "--net", "true"],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            namespace_available = namespace_probe.returncode == 0
            process = subprocess.Popen(["paseo-desktop"], env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError(f"Paseo desktop exited early: {process.returncode}")
                    windows = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True)
                    if '"Paseo"' in windows:
                        break
                    time.sleep(0.5)
                else:
                    raise RuntimeError("Paseo desktop window did not appear within 45 seconds")
                deadline = time.monotonic() + 3
                renderer = None
                test_processes = []
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise RuntimeError("Paseo desktop exited shortly after opening")
                    windows = subprocess.check_output(["xwininfo", "-root", "-tree"], text=True)
                    if '"Paseo"' not in windows:
                        raise RuntimeError("Paseo desktop window disappeared after opening")
                    current_renderer, current_processes = renderer_sandbox(process.pid)
                    if current_renderer and (
                            not renderer or current_renderer["status_readable"]):
                        renderer = current_renderer
                    test_processes = current_processes
                    time.sleep(0.5)
                if not renderer:
                    raise RuntimeError(
                        "Could not find Paseo's renderer among the desktop process descendants; "
                        f"matching test processes: {test_processes}")
                if namespace_available and not renderer["status_readable"]:
                    raise RuntimeError(
                        "Found Paseo's renderer but could not read its sandbox status; "
                        f"renderer process: {renderer['args']}")
                if renderer["sandbox_flag"] and renderer["enforced"]:
                    print(f"Installed Paseo {version}; window stayed open with renderer sandbox active")
                elif namespace_available or not renderer["no_sandbox_flag"]:
                    raise RuntimeError(
                        f"Paseo renderer sandbox state did not match the runner probe: {renderer['args']}")
                else:
                    reason = namespace_probe.stderr.strip() or "user namespace probe was denied"
                    print(f"Paseo {version} window stayed open; runner denied unshare so the upstream sandbox fallback was used: {reason}")
            except Exception:
                log.flush()
                log.seek(0)
                details = log.read()[-12000:]
                if details:
                    print(details, file=sys.stderr)
                raise
            finally:
                try:
                    subprocess.run(
                        ["paseo", "daemon", "stop", "--home", env["PASEO_HOME"], "--json"],
                        env=env, stdout=log, stderr=subprocess.STDOUT,
                        timeout=20, check=False)
                except subprocess.TimeoutExpired:
                    log.write("Paseo daemon stop timed out; terminating the smoke process group.\n")
                finally:
                    stop_group(process)


if __name__ == "__main__":
    main()
