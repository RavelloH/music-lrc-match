# -*- coding: utf-8 -*-
"""
Tests for music-lrc-match project.
Verifies core utility functions and LRC processing logic.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers to extract testable functions without triggering interactive startup
# ---------------------------------------------------------------------------

def _load_module_functions():
    """
    Return a namespace dict with the pure utility functions extracted
    from main.py without executing its module-level startup code.
    """
    import importlib
    import types

    with open(os.path.join(os.path.dirname(__file__), 'main.py'),
              'r', encoding='utf-8') as f:
        source = f.read()

    # Replace the module-level startup block so importing is safe
    startup_calls = (
        'check()\n'
        'setlog()\n'
        'importlog()\n'
        'setup()\n'
        'checkfile()\n'
        'writelog()'
    )
    safe_source = source.replace(startup_calls, '# startup suppressed for tests')

    module = types.ModuleType('main_test_shim')
    module.__dict__.update({
        '__name__': 'main_test_shim',
        '__file__': __file__,
    })

    # Patch interactive calls before executing
    with patch('builtins.input', return_value=''):
        from unittest.mock import MagicMock
        mock_urlopen = MagicMock()
        mock_urlopen.return_value.read.return_value = b''
        with patch('urllib.request.urlopen', mock_urlopen):
            exec(compile(safe_source, 'main.py', 'exec'), module.__dict__)

    return module


_m = _load_module_functions()


class TestSimilarFunction(unittest.TestCase):
    """Tests for the string similarity helper."""

    def test_identical_strings(self):
        ratio = _m.similar('neko', 'neko')
        self.assertEqual(ratio, 100.0)

    def test_completely_different(self):
        ratio = _m.similar('aaa', 'zzz')
        self.assertLess(ratio, 50.0)

    def test_partial_match(self):
        ratio = _m.similar('Taylor Swift - Shake It Off', 'Taylor Swift - Shake It Off')
        self.assertEqual(ratio, 100.0)

    def test_similar_but_not_equal(self):
        ratio = _m.similar('周杰伦 - 晴天', '周杰伦 - 晴天 (Live)')
        self.assertGreater(ratio, 60.0)


class TestLrcMake(unittest.TestCase):
    """Tests for the lrc_make() function (normal lyrics API path)."""

    def _run_lrc_make(self, lrc_json_data, tmp_dir, filename='Song Name'):
        """Helper: set globals and call lrc_make(), return side-effects."""
        _m.target_file = tmp_dir
        _m.file_name = filename
        _m.music_file = filename + '.mp3'
        _m.lrc_result = json.dumps(lrc_json_data)
        _m.errorlist = []
        _m.abso_music_list = []
        _m.success_list = []
        _m.lrc_make()

    def test_normal_lyrics_written(self):
        """When lyrics are present and nolyric is false, writes .lrc file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = {'lyric': '[00:01.00]Hello world\n', 'nolyric': False}
            self._run_lrc_make(payload, tmp_dir)
            lrc_path = os.path.join(tmp_dir, 'Song Name.lrc')
            self.assertTrue(os.path.isfile(lrc_path))
            with open(lrc_path, encoding='utf-8') as f:
                content = f.read()
            self.assertIn('Hello world', content)
            self.assertEqual(len(_m.success_list), 1)
            self.assertEqual(len(_m.abso_music_list), 0)
            self.assertEqual(len(_m.errorlist), 0)

    def test_nolyric_true_detected_as_pure_music(self):
        """When nolyric is True, song is added to abso_music_list (pure music)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = {'nolyric': True, 'lyric': ''}
            self._run_lrc_make(payload, tmp_dir)
            lrc_path = os.path.join(tmp_dir, 'Song Name.lrc')
            self.assertFalse(os.path.isfile(lrc_path))
            self.assertEqual(len(_m.abso_music_list), 1)
            self.assertEqual(len(_m.success_list), 0)

    def test_nolyric_false_not_treated_as_pure_music(self):
        """When nolyric is False, song should NOT be treated as pure music."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = {'nolyric': False, 'lyric': '[00:00.00]Test lyric\n'}
            self._run_lrc_make(payload, tmp_dir)
            lrc_path = os.path.join(tmp_dir, 'Song Name.lrc')
            self.assertTrue(os.path.isfile(lrc_path), 'LRC file should exist when nolyric=False')
            self.assertEqual(len(_m.abso_music_list), 0,
                             'Song must not be marked as pure music when nolyric=False')

    def test_missing_lyric_key_goes_to_errorlist(self):
        """When lyric key is missing the song is added to errorlist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = {'nolyric': False}  # missing 'lyric' key
            self._run_lrc_make(payload, tmp_dir)
            self.assertEqual(len(_m.errorlist), 1)
            self.assertEqual(len(_m.success_list), 0)

    def test_invalid_json_goes_to_errorlist(self):
        """When lrc_result is invalid JSON the song is added to errorlist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            _m.target_file = tmp_dir
            _m.file_name = 'Bad Song'
            _m.music_file = 'Bad Song.mp3'
            _m.lrc_result = 'NOT_JSON'
            _m.errorlist = []
            _m.abso_music_list = []
            _m.success_list = []
            _m.lrc_make()
            self.assertEqual(len(_m.errorlist), 1)


class TestTransLrcMake(unittest.TestCase):
    """Tests for the trans_lrc_make() function (translated lyrics path)."""

    def _run_trans_lrc_make(self, lrc_json_data, tmp_dir, filename='Song Name'):
        _m.target_file = tmp_dir
        _m.file_name = filename
        _m.music_file = filename + '.mp3'
        _m.lrc_result = json.dumps(lrc_json_data)
        _m.errorlist = []
        _m.abso_music_list = []
        _m.success_list = []
        _m.trans_lrc_make()

    def test_translation_written(self):
        """When tlyric key is present, writes the translated .lrc file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = {
                'lrc': {'lyric': '[00:01.00]Original\n'},
                'tlyric': {'lyric': '[00:01.00]Translation\n'},
            }
            self._run_trans_lrc_make(payload, tmp_dir)
            lrc_path = os.path.join(tmp_dir, 'Song Name.lrc')
            self.assertTrue(os.path.isfile(lrc_path))
            with open(lrc_path, encoding='utf-8') as f:
                content = f.read()
            self.assertIn('Translation', content)
            self.assertEqual(len(_m.success_list), 1)
            self.assertEqual(len(_m.errorlist), 0)

    def test_pure_music_detection(self):
        """When lrc_json contains '纯音乐，', marks as pure music."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = {
                'lrc': {'lyric': '[00:00.00]纯音乐，请欣赏\n'},
                'tlyric': {'lyric': ''},
            }
            self._run_trans_lrc_make(payload, tmp_dir)
            self.assertEqual(len(_m.abso_music_list), 1)
            self.assertEqual(len(_m.success_list), 0)

    def test_missing_tlyric_goes_to_errorlist(self):
        """When tlyric key is missing the song is added to errorlist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload = {'lrc': {'lyric': '[00:01.00]Original\n'}}
            self._run_trans_lrc_make(payload, tmp_dir)
            self.assertEqual(len(_m.errorlist), 1)

    def test_os_remove_called_with_single_arg(self):
        """
        Regression test: os.remove() must not be called with two arguments.
        The bug was: os.remove(path, 'w+') which raises TypeError.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Payload missing 'tlyric' key to force the except branch
            payload = {'lrc': {'lyric': '[00:01.00]Original\n'}}
            # If the bug were present this would raise TypeError inside os.remove
            # and the test would fail with an unexpected exception.
            try:
                self._run_trans_lrc_make(payload, tmp_dir)
            except TypeError as exc:
                self.fail(f'os.remove raised TypeError (regression): {exc}')
            # File should not exist (nothing was written successfully)
            lrc_path = os.path.join(tmp_dir, 'Song Name.lrc')
            self.assertFalse(os.path.isfile(lrc_path))


class TestLogCycle(unittest.TestCase):
    """Basic round-trip test for log init / import cycle."""

    def test_initlog_and_importlog_roundtrip(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log',
                                         delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name

        try:
            _m.log_file = tmp_path
            _m.initlog()

            # File should now contain the template anchors
            with open(tmp_path, encoding='utf-8') as f:
                content = f.read()
            self.assertIn('[setting]>>', content)
            self.assertIn('[absolute music]>>', content)
            self.assertIn('[raw log]>>', content)

            # importlog should parse without errors
            _m.importlog()
            self.assertIsInstance(_m.log_setting, list)
            self.assertIsInstance(_m.log_abso_music, list)
            self.assertIsInstance(_m.log_wrong_music, list)
            self.assertIsInstance(_m.log_history, list)
            self.assertIsInstance(_m.log_raw, list)
        finally:
            os.unlink(tmp_path)


if __name__ == '__main__':
    unittest.main()
