"""Tiny schema/export fixtures; never synthetic comparison results."""
import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from forecast_interval_lab.core import metric_names
from forecast_interval_lab.reports import PROTOCOL_SHA256, RESOURCE_FIELDS, export_report, make_report, read_json


class ReportTests(unittest.TestCase):
    def fixture(self):
        return {'kind': 'benchmark-receipt', 'outcome': 'pass', 'source_sha256': 'a' * 64,
                'control_mode': 'trusted-local-python-operational-v1', 'memory_hard_limit': False,
                'measured_cpu_is_lower_bound_before_final_receipt_and_db': True,
                'result': {'checks': [{'name': 'fixture', 'passed': True}],
                           'metrics': {k: (i + 1) / 100 for i, k in enumerate(sorted(metric_names()))}},
                'private_marker': 'must never be exported',
                **{k: 1 for k in RESOURCE_FIELDS}}

    def report(self, receipt):
        return make_report(receipt, 'b' * 64, 'a' * 64, PROTOCOL_SHA256,
                           {'python': '3.14.7', 'os': 'Darwin', 'machine': 'arm64'})

    def test_exact_metric_copy_and_no_private_fields_or_evaluation(self):
        receipt = self.fixture()
        with patch('forecast_interval_lab.core.comparison', side_effect=AssertionError('no evaluation')):
            report = self.report(receipt)
            self.assertEqual(report['metrics'], receipt['result']['metrics'])
            self.assertNotIn('private_marker', json.dumps(report))
            self.assertNotIn('must never be exported', json.dumps(report))
            with tempfile.TemporaryDirectory() as directory:
                out = Path(directory) / 'results'
                export_report(report, out)
                self.assertEqual(json.loads((out / 'results.json').read_text()), report)
                with (out / 'per_seed.csv').open() as handle: per_seed = list(csv.DictReader(handle))
                with (out / 'aggregate.csv').open() as handle: aggregate = list(csv.DictReader(handle))
                self.assertEqual(len(per_seed), 18)
                self.assertEqual(len(aggregate), 18)
                for row in per_seed:
                    for metric in ('coverage', 'width', 'score'):
                        key = f"{row['family']}_s{row['seed']}_{row['method']}_{metric}"
                        self.assertEqual(float(row[metric]), report['metrics'][key])
                for row in aggregate:
                    prefix = f"{row['family']}_{row['method']}_{row['metric']}"
                    self.assertEqual(float(row['mean']), report['metrics'][prefix + '_mean'])
                    self.assertEqual(float(row['sample_sd']), report['metrics'][prefix + '_sd'])
                with self.assertRaises(FileExistsError): export_report(report, out)

    def test_failed_incomplete_mismatched_or_nonfinite_receipt_rejected(self):
        base = self.fixture()
        invalid = []
        for key, value in [('outcome', 'fail'), ('source_sha256', 'd' * 64),
                           ('memory_hard_limit', True), ('cpu_seconds', float('nan'))]:
            bad = copy.deepcopy(base); bad[key] = value; invalid.append(bad)
        bad = copy.deepcopy(base); bad['result']['checks'][0]['passed'] = False; invalid.append(bad)
        bad = copy.deepcopy(base); bad['result']['metrics'].pop(next(iter(metric_names()))); invalid.append(bad)
        bad = copy.deepcopy(base); bad['result']['metrics']['stationary_s7_frozen_coverage'] = 2; invalid.append(bad)
        for bad in invalid:
            with self.assertRaises(ValueError): self.report(bad)

    def test_changed_protocol_is_rejected(self):
        with self.assertRaises(ValueError):
            make_report(self.fixture(), 'b' * 64, 'a' * 64, 'c' * 64,
                        {'python': '3.14.7', 'os': 'Darwin', 'machine': 'arm64'})

    def test_huge_json_integers_rejected_as_value_errors(self):
        for location in ('metric', 'resource'):
            receipt = self.fixture()
            if location == 'metric':
                receipt['result']['metrics']['stationary_s7_frozen_score'] = 10 ** 400
            else:
                receipt['cpu_seconds'] = 10 ** 400
            decoded = json.loads(json.dumps(receipt))
            with self.assertRaises(ValueError):
                self.report(decoded)

    def test_receipt_nesting_error_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'receipt.json'
            path.write_text('{}')
            with patch('forecast_interval_lab.reports.json.loads', side_effect=RecursionError):
                with self.assertRaisesRegex(ValueError, 'nesting'):
                    read_json(path)
