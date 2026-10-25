"""Tests for workspace manifests and scaffolding. Pure Python: also runs with `python -m unittest`."""
import tempfile
import textwrap
import unittest
from pathlib import Path

from projects.manifests import ManifestError, discover, load_manifest
from projects.scaffold import create_workspace

SHIPPED = Path(__file__).resolve().parents[2] / "qml_projects"

GOOD = """
number = 3
title = "Kernel study"
track = "kernels"
difficulty = "hard"
tools = "PennyLane"
builds_on = [6, 8]
summary = "Measure kernel concentration."

[[experiments]]
slug = "sweep"
title = "Qubit sweep"
script = "experiments/e01_sweep.py"
figure = "sweep.png"

[experiments.params]
max_qubits = 8
noisy = false
"""


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def workspace(self, slug, manifest, scripts=("experiments/e01_sweep.py",)):
        folder = self.root / slug
        for script in scripts:
            (folder / script).parent.mkdir(parents=True, exist_ok=True)
            (folder / script).write_text("print('hi')\n")
        folder.mkdir(exist_ok=True)
        (folder / "project.toml").write_text(textwrap.dedent(manifest))
        return folder

    def test_valid_manifest(self):
        m = load_manifest(self.workspace("kernel-study", GOOD))
        self.assertEqual((m.slug, m.number, m.track, m.builds_on), ("kernel-study", 3, "kernels", (6, 8)))
        self.assertEqual(m.experiments[0].params, {"max_qubits": 8, "noisy": False})

    def test_all_problems_are_reported_together(self):
        bad = GOOD.replace('track = "kernels"', 'track = "magic"').replace('difficulty = "hard"', "difficulty = 3") \
                  .replace('script = "experiments/e01_sweep.py"', 'script = "../escape.py"')
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(self.workspace("kernel-study", bad))
        text = str(ctx.exception)
        for fragment in ["track 'magic'", "'difficulty' must be text", "../escape.py"]:
            self.assertIn(fragment, text)

    def test_invalid_toml_and_missing_file(self):
        with self.assertRaisesRegex(ManifestError, "invalid TOML"):
            load_manifest(self.workspace("broken", "title = \n"))
        (self.root / "empty").mkdir()
        with self.assertRaisesRegex(ManifestError, "missing"):
            load_manifest(self.root / "empty")

    def test_bad_folder_name_and_duplicate_experiment(self):
        dup = GOOD + '\n[[experiments]]\nslug = "sweep"\ntitle = "Again"\nscript = "experiments/e01_sweep.py"\n'
        with self.assertRaises(ManifestError) as ctx:
            load_manifest(self.workspace("Bad_Name", dup))
        self.assertIn("folder name", str(ctx.exception))
        self.assertIn("used twice", str(ctx.exception))

    def test_discover_keeps_going_past_bad_folders_and_flags_duplicate_numbers(self):
        self.workspace("one", GOOD)
        self.workspace("two", GOOD)
        self.workspace("three", "title = 1\n")
        (self.root / "_drafts").mkdir()
        manifests, errors = discover(self.root)
        self.assertEqual(sorted(m.slug for m in manifests), ["one", "two"])
        messages = " ".join(str(e) for e in errors)
        self.assertIn("three", messages)
        self.assertIn("number 3 is used by one, two", messages)

    def test_scaffold_creates_a_valid_runnable_workspace(self):
        folder = create_workspace(self.root, "new-idea", 'Title with "quotes"', "hybrid", "easy", "Line one",
                                  tools="PennyLane", builds_on=[7])
        m = load_manifest(folder)
        self.assertEqual(m.title, 'Title with "quotes"')
        self.assertEqual(m.experiments[0].slug, "starter")
        self.assertTrue((folder / "README.md").exists())
        with self.assertRaises(FileExistsError):
            create_workspace(self.root, "new-idea", "x", "hybrid", "easy", "y")
        with self.assertRaises(ValueError):
            create_workspace(self.root, "Bad Slug", "x", "hybrid", "easy", "y")

    def test_shipped_workspaces_are_valid(self):
        manifests, errors = discover(SHIPPED)
        self.assertEqual(errors, [])
        self.assertEqual(sorted(m.number for m in manifests), list(range(1, 17)))


if __name__ == "__main__":
    unittest.main()
