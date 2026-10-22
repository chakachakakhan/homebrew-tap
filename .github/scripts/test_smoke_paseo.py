"""Regression checks for renderer discovery during the installed-app smoke test."""

import tempfile
import unittest
from pathlib import Path

from smoke_paseo import renderer_sandbox


class PaseoRendererTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.proc = Path(self.tempdir.name)
        self.write_process(100, 1, b"desktop\0")

    def tearDown(self):
        self.tempdir.cleanup()

    def write_process(self, pid, ppid, cmdline, status=None):
        process = self.proc / str(pid)
        process.mkdir(exist_ok=True)
        (process / "stat").write_text(f"{pid} (paseo) S {ppid} 0 0 0 0\n")
        (process / "cmdline").write_bytes(cmdline)
        if status is not None:
            (process / "status").write_text(status)

    def test_standard_argv_requires_kernel_sandbox_evidence(self):
        self.write_process(101, 100, b"Paseo.bin\0--type=renderer\0--enable-sandbox\0",
                          "Seccomp:\t2\nNoNewPrivs:\t1\n")

        renderer, _ = renderer_sandbox(100, self.proc)

        self.assertTrue(renderer["sandbox_flag"])
        self.assertTrue(renderer["enforced"])
        self.assertTrue(renderer["status_readable"])

    def test_consolidated_cmdline_still_matches_exact_renderer_option(self):
        self.write_process(101, 100,
                          b"Paseo.bin --type=renderer --enable-sandbox",
                          "Seccomp:\t2\nNoNewPrivs:\t1\n")

        renderer, _ = renderer_sandbox(100, self.proc)

        self.assertIsNotNone(renderer)
        self.assertTrue(renderer["enforced"])

    def test_status_race_keeps_renderer_but_cannot_claim_sandbox(self):
        self.write_process(101, 100, b"Paseo.bin\0--type=renderer\0--no-sandbox\0")

        renderer, _ = renderer_sandbox(100, self.proc)

        self.assertIsNotNone(renderer)
        self.assertFalse(renderer["status_readable"])
        self.assertFalse(renderer["enforced"])
        self.assertTrue(renderer["no_sandbox_flag"])

    def test_renderer_option_must_be_an_exact_token(self):
        self.write_process(101, 100,
                          b"Paseo.bin\0--type=renderer-helper\0--enable-sandbox\0",
                          "Seccomp:\t2\nNoNewPrivs:\t1\n")

        renderer, _ = renderer_sandbox(100, self.proc)

        self.assertIsNone(renderer)


if __name__ == "__main__":
    unittest.main()
