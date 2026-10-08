import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from forecast_interval_lab.cli import main, parse_input


class CliTests(unittest.TestCase):
    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err): code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_demo_matches_strict_file(self):
        expected = self.invoke(['demo'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text(json.dumps({'history': list(range(10)), 'observations': [10, 12, 11],
                                        'alpha': .1, 'window': 9}))
            self.assertEqual(self.invoke(['forecast', str(path)]), expected)
        code, out, err = expected
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(len(json.loads(out)['predictions']), 3)
        self.assertEqual(json.loads(out)['predictions'][-1]['rolling']['score'], 4)

    def test_malformed_duplicate_missing_unknown_nonfinite(self):
        for text in ['{', '[]', '{}', '{"history":[],"history":[]}',
                     '{"history":[],"observations":[1],"alpha":0.1,"window":9,"x":1}',
                     '{"history":[],"observations":[NaN],"alpha":0.1,"window":9}',
                     'x' * (1024 * 1024 + 1)]:
            with self.subTest(text=text[:70]), self.assertRaises(ValueError): parse_input(text)

    def test_bad_input_has_error_without_partial_json(self):
        for observations in [[True], ['10'], [1e308], []]:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'input.json'
                path.write_text(json.dumps({'history': list(range(10)), 'observations': observations,
                                            'alpha': .1, 'window': 9}))
                code, out, err = self.invoke(['forecast', str(path)])
                self.assertEqual((code, out), (2, ''))
                self.assertTrue(err.startswith('error: '))

    def test_missing_file_and_invalid_encoding(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'missing.json'
            self.assertEqual(self.invoke(['forecast', str(path)])[0], 2)
            path.write_bytes(b'\xff')
            self.assertEqual(self.invoke(['forecast', str(path)])[0], 2)

    def test_excessive_nesting_is_an_explicit_input_error(self):
        # Interpreter recursion limits vary; this input must still be rejected.
        with self.assertRaises(ValueError):
            parse_input('[' * 2000 + '0' + ']' * 2000)
        with patch('forecast_interval_lab.cli.json.loads', side_effect=RecursionError):
            with self.assertRaisesRegex(ValueError, 'nesting'):
                parse_input('{}')
