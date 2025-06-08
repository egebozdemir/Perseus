import unittest
import tempfile
import os
from perseus import Perseus


class TestBulkAddMethods(unittest.TestCase):

    def setUp(self):
        self.test_files = []

    def tearDown(self):
        for f in self.test_files:
            os.remove(f)

    def _create_temp_file(self, content: str) -> str:
        tmp = tempfile.NamedTemporaryFile(delete=False, mode='w+')
        tmp.write(content)
        tmp.close()
        self.test_files.append(tmp.name)
        return tmp.name

    def _get_finder(self, path: str):
        # Create dummy finder that won’t run actual search
        finder = Perseus(search_path=".", keywords=["dummy"])
        finder.matches = [path]
        finder._confirm_action = lambda msg: True  # auto-confirm for tests
        return finder

    def test_bulk_add_after_all_matches(self):
        content = "line one\nmatch here\nline three\nmatch here\n"
        expected = "line one\nmatch here\ninserted line\nline three\nmatch here\ninserted line\n"

        path = self._create_temp_file(content)
        finder = self._get_finder(path)

        modified = finder.bulk_add_after("match", "inserted line", first_only=False, dry_run=False)
        self.assertEqual(modified, 1)

        with open(path) as f:
            result = f.read()
        self.assertEqual(result, expected)

    def test_bulk_add_after_first_only(self):
        content = "match one\nline\nmatch two\n"
        expected = "match one\ninserted\nline\nmatch two\n"

        path = self._create_temp_file(content)
        finder = self._get_finder(path)

        modified = finder.bulk_add_after("match", "inserted", first_only=True, dry_run=False)
        self.assertEqual(modified, 1)

        with open(path) as f:
            result = f.read()
        self.assertEqual(result, expected)

    def test_bulk_add_before_all_matches(self):
        content = "start\nmatch\nmiddle\nmatch\nend\n"
        expected = "start\ninserted\nmatch\nmiddle\ninserted\nmatch\nend\n"

        path = self._create_temp_file(content)
        finder = self._get_finder(path)

        modified = finder.bulk_add_before("match", "inserted", first_only=False, dry_run=False)
        self.assertEqual(modified, 1)

        with open(path) as f:
            result = f.read()
        self.assertEqual(result, expected)

    def test_bulk_add_before_first_only(self):
        content = "match one\nskip\nmatch two\n"
        expected = "inserted\nmatch one\nskip\nmatch two\n"

        path = self._create_temp_file(content)
        finder = self._get_finder(path)

        modified = finder.bulk_add_before("match", "inserted", first_only=True, dry_run=False)
        self.assertEqual(modified, 1)

        with open(path) as f:
            result = f.read()
        self.assertEqual(result, expected)

    def test_no_modification_when_no_match(self):
        content = "no match here\nstill no match\n"
        path = self._create_temp_file(content)
        finder = self._get_finder(path)

        modified = finder.bulk_add_after("notfound", "inserted", dry_run=False)
        self.assertEqual(modified, 0)

        with open(path) as f:
            result = f.read()
        self.assertEqual(result, content)

    def test_dry_run_does_not_write(self):
        content = "match line\nanother\n"
        path = self._create_temp_file(content)
        finder = self._get_finder(path)

        modified = finder.bulk_add_after("match", "inserted", dry_run=True)
        self.assertEqual(modified, 0)

        with open(path) as f:
            result = f.read()
        self.assertEqual(result, content)


if __name__ == "__main__":
    unittest.main()
