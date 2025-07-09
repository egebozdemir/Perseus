import unittest
import tempfile
import os
from unittest.mock import patch
from io import StringIO
from typing import List
from perseus import Perseus


class TestPerseus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*60)
        print("STARTING TEST SUITE".center(60))
        print("="*60 + "\n")

    def setUp(self):
        self.test_files = []
        print("\n")
        print("-"*50)
        print(f"\n[START] {self._testMethodName}")

    def tearDown(self):
        for f in self.test_files:
            if os.path.exists(f):
                os.remove(f)
        print(f"[END] {self._testMethodName}\n")

    def _create_temp_file(self, content: str) -> str:
        tmp = tempfile.NamedTemporaryFile(delete=False, mode='w+')
        tmp.write(content)
        tmp.close()
        self.test_files.append(tmp.name)
        return tmp.name

    def _get_finder(self, paths: List[str]):
        """Helper to create finder with mocked matches and confirm_action"""
        finder = Perseus(search_path=".", keywords=["dummy"])
        finder.matches = paths
        return finder

    def test_bulk_remove_files_confirmed(self):
        """Test file removal with confirmation"""
        content1 = "test file content\n"
        content2 = "another test file\n"
        path1 = self._create_temp_file(content1)
        path2 = self._create_temp_file(content2)

        finder = self._get_finder([path1, path2])
        
        with patch('builtins.input', return_value='y'):
            removed = finder.bulk_remove_files(dry_run=False, bulk_confirm=True)

        self.assertEqual(removed, 2)
        self.assertFalse(os.path.exists(path1))
        self.assertFalse(os.path.exists(path2))
        print("✓ Successfully removed files with bulk confirmation")

    def test_bulk_remove_files_aborted(self):
        """Test file removal cancellation"""
        content = "test file content\n"
        path = self._create_temp_file(content)

        finder = self._get_finder([path])
        
        with patch('builtins.input', return_value='n'):
            removed = finder.bulk_remove_files(dry_run=False, bulk_confirm=True)

        self.assertEqual(removed, 0)
        self.assertTrue(os.path.exists(path))
        print("✓ Correctly aborted file removal")

    def test_bulk_remove_files_dry_run(self):
        """Test dry run file removal"""
        content = "test file content\n"
        path = self._create_temp_file(content)

        finder = self._get_finder([path])
        
        with patch('builtins.input', return_value='y'):
            removed = finder.bulk_remove_files(dry_run=True, bulk_confirm=True)

        self.assertEqual(removed, 0)
        self.assertTrue(os.path.exists(path))
        print("✓ Dry run correctly skipped file removal")

    def test_bulk_remove_files_individual_confirmation(self):
        """Test individual file confirmation"""
        content1 = "test file 1\n"
        content2 = "test file 2\n"
        path1 = self._create_temp_file(content1)
        path2 = self._create_temp_file(content2)

        finder = self._get_finder([path1, path2])
        
        with patch('builtins.input', side_effect=['y', 'n']):
            removed = finder.bulk_remove_files(dry_run=False, bulk_confirm=False)

        self.assertEqual(removed, 1)
        self.assertFalse(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))
        print("✓ Correctly handled individual file confirmations")

    # Existing tests remain unchanged...
    def test_bulk_confirm_replaces_in_all_files(self):
        """Test bulk replacement with confirmation"""
        content1 = "line with @old\n"
        content2 = "other @old text\n"
        path1 = self._create_temp_file(content1)
        path2 = self._create_temp_file(content2)

        finder = self._get_finder([path1, path2])
        
        with patch('builtins.input', return_value='y'):
            modified = finder.bulk_replace("@old", "@new", dry_run=False, bulk_confirm=True)

        self.assertEqual(modified, 2)
        print(f"✓ Replaced in {modified} files")

    def test_bulk_confirm_aborts_if_user_rejects(self):
        """Test bulk operation cancellation"""
        content = "line with @old\n"
        path = self._create_temp_file(content)

        finder = self._get_finder([path])
        
        with patch('builtins.input', return_value='n'):
            modified = finder.bulk_replace("@old", "@new", dry_run=False, bulk_confirm=True)

        self.assertEqual(modified, 0)
        print("✓ Correctly aborted operation")

    def test_non_bulk_mode_confirms_per_file(self):
        """Test individual file confirmation"""
        content1 = "line with @old\n"
        content2 = "other @old text\n"
        path1 = self._create_temp_file(content1)
        path2 = self._create_temp_file(content2)

        finder = self._get_finder([path1, path2])
        
        with patch('builtins.input', side_effect=['y', 'n']):
            modified = finder.bulk_replace("@old", "@new", dry_run=False, bulk_confirm=False)

        self.assertEqual(modified, 1)
        print(f"✓ Modified {modified} files with individual confirmations")

    def test_bulk_confirm_with_dry_run(self):
        """Test dry run behavior"""
        content = "line with @old\n"
        path = self._create_temp_file(content)

        finder = self._get_finder([path])
        
        with patch('builtins.input', return_value='y'):
            modified = finder.bulk_replace("@old", "@new", dry_run=True, bulk_confirm=True)

        self.assertEqual(modified, 0)
        print("✓ Dry run completed without modifications")

    def test_bulk_confirm_with_remove_lines(self):
        """Test bulk line removal"""
        content = "keep\nremove this\nkeep\n"
        path = self._create_temp_file(content)

        finder = self._get_finder([path])
        
        with patch('builtins.input', return_value='y'):
            modified = finder.bulk_remove_lines("remove", dry_run=False, bulk_confirm=True)

        self.assertEqual(modified, 1)
        print("✓ Bulk line removal successful")

    def test_bulk_confirm_with_add_after(self):
        """Test bulk line addition"""
        content = "line\nmatch\nnext\n"
        path = self._create_temp_file(content)

        finder = self._get_finder([path])
        
        with patch('builtins.input', return_value='y'):
            modified = finder.bulk_add_after("match", "added", dry_run=False, bulk_confirm=True)

        self.assertEqual(modified, 1)
        print("✓ Bulk line addition successful")


if __name__ == "__main__":
    unittest.main(verbosity=2)
