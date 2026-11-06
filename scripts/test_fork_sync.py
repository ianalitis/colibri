"""Exercise fork maintenance against disposable local repositories, without GitHub."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("fork-sync.sh").resolve()


class ForkSyncTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("JCODE_SCRATCH_DIR"))
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.repo = self.root / "checkout"
        self.source.mkdir()
        self.git(self.source, "init", "-b", "main")
        self.identity(self.source)
        self.commit(self.source, "base")
        self.git(self.source, "branch", "dev")
        self.git(self.root, "clone", str(self.source), str(self.repo))
        self.identity(self.repo)
        self.git(self.repo, "remote", "rename", "origin", "upstream")
        self.git(self.root, "clone", "--bare", str(self.source), "fork.git")
        self.git(self.repo, "remote", "add", "origin", str(self.root / "fork.git"))
        self.git(self.repo, "fetch", "origin")
        self.git(self.repo, "switch", "-c", "fork/development")

    def git(self, directory, *args):
        return subprocess.run(
            ["git", "-C", str(directory), *args], check=True,
            text=True, capture_output=True,
        ).stdout.strip()

    def identity(self, repo):
        for key, value in (("user.name", "Fixture"), ("user.email", "fixture@example.invalid"),
                           ("commit.gpgsign", "false"), ("core.hooksPath", "/dev/null")):
            self.git(repo, "config", key, value)

    def commit(self, repo, name):
        (repo / name).write_text(name + "\n")
        self.git(repo, "add", name)
        self.git(repo, "commit", "-m", name)
        return self.git(repo, "rev-parse", "HEAD")

    def run_sync(self, action):
        return subprocess.run(["bash", str(SCRIPT), action], cwd=self.repo,
                              capture_output=True, text=True)

    def test_status_is_offline_and_does_not_fetch(self):
        old_ref = self.git(self.repo, "rev-parse", "upstream/main")
        self.commit(self.source, "new")
        result = self.run_sync("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Cached refs only", result.stdout)
        self.assertEqual(self.git(self.repo, "rev-parse", "upstream/main"), old_ref)

    def test_sync_fast_forwards_only_local_main(self):
        head = self.git(self.repo, "rev-parse", "HEAD")
        published = self.git(self.root / "fork.git", "rev-parse", "main")
        latest = self.commit(self.source, "new")
        result = self.run_sync("sync-main")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.repo, "rev-parse", "main"), latest)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), head)
        self.assertEqual(self.git(self.root / "fork.git", "rev-parse", "main"), published)
        self.assertEqual(self.git(self.repo, "branch", "--show-current"), "fork/development")

    def test_fetch_refreshes_without_integrating(self):
        old_main = self.git(self.repo, "rev-parse", "main")
        latest = self.commit(self.source, "new")
        result = self.run_sync("fetch")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.git(self.repo, "rev-parse", "upstream/main"), latest)
        self.assertEqual(self.git(self.repo, "rev-parse", "main"), old_main)

    def test_dirty_index_and_untracked_files_are_refused(self):
        for staged in (False, True):
            with self.subTest(staged=staged):
                (self.repo / "dirty").write_text("preserve me\n")
                if staged:
                    self.git(self.repo, "add", "dirty")
                result = self.run_sync("sync-main")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("must be clean", result.stderr)
                self.assertEqual((self.repo / "dirty").read_text(), "preserve me\n")

    def test_wrong_branch_is_refused(self):
        self.git(self.repo, "switch", "main")
        result = self.run_sync("sync-main")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Run sync-main from fork/development", result.stderr)

    def test_divergent_main_is_preserved(self):
        self.git(self.repo, "switch", "main")
        local = self.commit(self.repo, "local")
        self.git(self.repo, "switch", "fork/development")
        self.commit(self.source, "upstream")
        result = self.run_sync("sync-main")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git(self.repo, "rev-parse", "main"), local)

    def test_unknown_action_is_refused(self):
        self.assertEqual(self.run_sync("push").returncode, 2)


if __name__ == "__main__":
    unittest.main()
