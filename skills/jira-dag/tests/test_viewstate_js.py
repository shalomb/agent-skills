"""Runs the DOM-free view-state tests (tests/js/*.test.js, scenarios S-flt-1..9) with `node --test`. Skipped when node is missing."""
import glob, os, shutil, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
NODE = shutil.which("node")


class ViewStateJs(unittest.TestCase):
    @unittest.skipIf(not NODE, "node not found")
    def test_node_tests_pass(self):
        files = sorted(glob.glob(os.path.join(HERE, "js", "*.test.js")))
        self.assertTrue(files)
        run = subprocess.run([NODE, "--test", *files], capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_module_can_be_embedded_in_a_script_element(self):
        src = open(os.path.join(HERE, "..", "scripts", "viewstate.js")).read()
        self.assertNotIn("</script", src.lower())


if __name__ == "__main__":
    unittest.main()
