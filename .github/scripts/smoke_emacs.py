"""Exercise the poured Emacs bottle without loading personal configuration."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import tempfile
import termios
import time


def wait_for(check, process, seconds=30):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Process exited during startup: {process.args}")
        if check():
            return
        time.sleep(0.2)
    raise TimeoutError(f"Process did not become ready: {process.args}")


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def terminal_client(client, server, env):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
    process = subprocess.Popen(
        [str(client), f"--socket-name={server}", "--tty"],
        stdin=slave, stdout=slave, stderr=slave, env=env,
    )
    os.close(slave)
    try:
        output = b""
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and process.poll() is None:
            if select.select([master], [], [], 0.2)[0]:
                output += os.read(master, 65536)
            frames = subprocess.run(
                [str(client), f"--socket-name={server}", "--eval",
                 "(cl-some (lambda (f) (and (not (display-graphic-p f)) "
                 "(frame-visible-p f))) (frame-list))"],
                env=env, text=True, capture_output=True, timeout=10,
            )
            if frames.returncode == 0 and frames.stdout.strip() == "t":
                break
        else:
            raise RuntimeError(f"No terminal client frame: {output[-2000:]!r}")
        if not output:
            raise RuntimeError("Terminal client produced no display output")
        # C-x C-c closes the client frame, leaving the daemon alive.
        os.write(master, b"\x18\x03")
        process.wait(timeout=10)
        if process.returncode:
            raise RuntimeError(f"Terminal client exited with {process.returncode}")
    finally:
        stop(process)
        os.close(master)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wayland", action="store_true")
    args = parser.parse_args()
    prefix = Path(subprocess.check_output(["brew", "--prefix"], text=True).strip()) / "opt/emacs-pgtk"
    emacs, client = prefix / "bin/emacs", prefix / "bin/emacsclient"
    info = json.loads(subprocess.check_output([
        "brew", "info", "--json=v2", "chakachakakhan/tap/emacs-pgtk",
    ], text=True))["formulae"][0]
    service = info["service"]["run"]
    if service != [str(prefix / "bin/emacs"), "--fg-daemon"]:
        raise RuntimeError(f"Unexpected daemon service: {service}")

    with tempfile.TemporaryDirectory(prefix="emacs-smoke-") as directory:
        root = Path(directory)
        runtime = root / "runtime"
        runtime.mkdir(mode=0o700)
        env = os.environ.copy()
        env.update({
            "HOME": directory, "XDG_CONFIG_HOME": str(root / "config"),
            "XDG_CACHE_HOME": str(root / "cache"), "XDG_DATA_HOME": str(root / "data"),
            "XDG_RUNTIME_DIR": str(runtime), "TERM": "xterm-256color",
        })
        # A package must find its own libraries and Lisp without a launcher wrapper.
        for variable in ("LD_LIBRARY_PATH", "EMACSDATA", "EMACSDOC", "EMACSPATH",
                         "EMACSLOADPATH", "GSETTINGS_SCHEMA_DIR", "GDK_BACKEND"):
            env.pop(variable, None)
        processes = []
        with (root / "process.log").open("w+") as log:
            try:
                if args.wayland:
                    env.pop("DISPLAY", None)
                    env["WAYLAND_DISPLAY"] = "emacs-ci"
                    weston = subprocess.Popen([
                        "weston", "--backend=headless-backend.so", "--socket=emacs-ci",
                        "--idle-time=0", "--width=1280", "--height=800",
                    ], env=env, stdout=log, stderr=log)
                    processes.append(weston)
                    wait_for(lambda: (runtime / "emacs-ci").exists(), weston)
                else:
                    env.pop("WAYLAND_DISPLAY", None)

                ready = root / "gui-ready"
                form = (
                    "(unless (and (eq window-system 'pgtk) (frame-visible-p)) "
                    '(error "No visible PGTK frame")) '
                    f'(write-region "ready" nil {json.dumps(str(ready))} nil \'silent)'
                )
                gui = subprocess.Popen(
                    [str(emacs), "-Q", "--eval", f"(progn {form})"],
                    env=env, stdout=log, stderr=log,
                )
                processes.append(gui)
                wait_for(ready.exists, gui)
                time.sleep(2)
                if gui.poll() is not None:
                    raise RuntimeError("GUI did not survive startup")
                stop(gui)

                server = f"tap-ci-{os.getpid()}"
                daemon = subprocess.Popen([
                    str(emacs), "-Q", f"--fg-daemon={server}",
                    "--eval", "(require 'cl-lib)",
                ], env=env, stdout=log, stderr=log)
                processes.append(daemon)

                def evaluate(form):
                    return subprocess.run([
                        str(client), f"--socket-name={server}", "--eval", form,
                    ], env=env, text=True, capture_output=True, timeout=10)

                wait_for(lambda: evaluate("(+ 20 22)").stdout.strip() == "42", daemon)
                subprocess.run([
                    str(client), f"--socket-name={server}", "--no-wait", "--create-frame",
                ], env=env, check=True, timeout=20, stdout=log, stderr=log)
                wait_for(lambda: evaluate(
                    "(cl-some (lambda (f) (and (display-graphic-p f) "
                    "(frame-visible-p f))) (frame-list))",
                ).stdout.strip() == "t", daemon)
                terminal_client(client, server, env)
                result = evaluate("(+ 20 22)")
                if result.returncode or result.stdout.strip() != "42":
                    raise RuntimeError("Daemon stopped after the terminal client closed")
                result = evaluate("(kill-emacs)")
                daemon.wait(timeout=10)
                if daemon.returncode:
                    raise RuntimeError(f"Daemon exited with {daemon.returncode}")
                print(f"GUI, daemon, graphical client, and terminal client passed on "
                      f"{'Wayland' if args.wayland else 'X11'}")
            finally:
                for process in reversed(processes):
                    stop(process)
                log.seek(0)
                print(log.read())


if __name__ == "__main__":
    main()
