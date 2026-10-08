"""Export only allowlisted measured values from an already-admitted receipt.

This module never generates observations or invokes the comparison. Shape and
hash checks support traceability; they do not establish workflow admission.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re

from .cli import unique_object, reject_constant
from .core import FAMILIES, METHODS, METRICS, SEEDS, metric_names

PROTOCOL_SHA256 = '6381adbb7bd66cf3049e4637f0ef18161259ae8d1fba3639d377f79c9e18b2dc'
RESOURCE_FIELDS = ('cpu_seconds', 'measured_cpu_before_closeout_seconds',
                   'worker_cpu_seconds', 'supervisor_cpu_seconds', 'wall_seconds',
                   'peak_memory_bytes')


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


def nonnegative_finite(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def make_report(receipt, receipt_sha, source_sha, protocol_sha, runtime):
    if (not all(valid_sha(v) for v in (receipt_sha, source_sha, protocol_sha))
            or protocol_sha != PROTOCOL_SHA256
            or receipt.get('kind') != 'benchmark-receipt' or receipt.get('outcome') != 'pass'
            or receipt.get('source_sha256') != source_sha
            or receipt.get('control_mode') != 'trusted-local-python-operational-v1'
            or receipt.get('measured_cpu_is_lower_bound_before_final_receipt_and_db') is not True
            or receipt.get('memory_hard_limit') is not False):
        raise ValueError('a matching successful operational receipt and source are required')
    result = receipt.get('result')
    if not isinstance(result, dict):
        raise ValueError('receipt has no result object')
    checks = result.get('checks')
    if (not isinstance(checks, list) or not 0 < len(checks) <= 100
            or any(not isinstance(c, dict) or c.get('passed') is not True for c in checks)):
        raise ValueError('receipt checks are incomplete or failed')
    values = result.get('metrics')
    if (not isinstance(values, dict) or set(values) != metric_names()
            or any(not nonnegative_finite(v) for v in values.values())):
        raise ValueError('all ninety finite nonnegative numeric metrics are required')
    if any(v > 1 for k, v in values.items()
           if k.endswith('_coverage') or k.endswith('_coverage_mean')):
        raise ValueError('coverage is outside zero to one')
    resources = {}
    for key in RESOURCE_FIELDS:
        value = receipt.get(key)
        if not nonnegative_finite(value):
            raise ValueError('missing or invalid measured resource field: ' + key)
        resources[key] = value
    if not isinstance(runtime, dict) or set(runtime) != {'python', 'os', 'machine'}:
        raise ValueError('runtime must contain only python, os and machine')
    if any(not isinstance(v, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,40}', v)
           for v in runtime.values()):
        raise ValueError('runtime labels must be simple bounded identifiers')
    return {'schema': 'forecast-interval-lab-results/1', 'alpha': 0.1,
            'seeds': list(SEEDS), 'observations_per_path': 384, 'test_targets_per_path': 128,
            'source_sha256': source_sha, 'protocol_sha256': protocol_sha,
            'receipt_sha256': receipt_sha, 'runtime': dict(runtime),
            'resources': resources,
            'resource_notes': {'cpu_seconds': 'conservative ledger charge',
                               'measured_cpu_before_closeout_seconds': 'lower bound before final receipt and database work',
                               'peak_memory_bytes': 'sum of process peaks; operational guard may overshoot'},
            'metrics': dict(sorted(values.items()))}


def export_report(report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'results.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    values = report['metrics']
    with (output / 'per_seed.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['family', 'seed', 'method', *METRICS])
        for family in FAMILIES:
            for seed in SEEDS:
                for method in METHODS:
                    writer.writerow([family, seed, method, *(
                        values[f'{family}_s{seed}_{method}_{metric}'] for metric in METRICS)])
    with (output / 'aggregate.csv').open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['family', 'method', 'metric', 'mean', 'sample_sd'])
        for family in FAMILIES:
            for method in METHODS:
                for metric in METRICS:
                    writer.writerow([family, method, metric,
                                     values[f'{family}_{method}_{metric}_mean'],
                                     values[f'{family}_{method}_{metric}_sd']])


def read_json(path):
    with Path(path).open('rb') as handle:
        raw = handle.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError('receipt or proof exceeds one MiB')
    try:
        value = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except RecursionError as error:
        raise ValueError('JSON nesting exceeds the parser limit') from error
    return raw, value


def main(argv=None):
    parser = argparse.ArgumentParser(description='Copy measured receipt values into sanitized CSV/JSON.')
    parser.add_argument('receipt', type=Path)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        raw, receipt = read_json(args.receipt)
        proof_raw, proof = read_json(args.proof)
        if receipt.get('proof_sha256') != sha256(proof_raw):
            raise ValueError('resource proof digest mismatch')
        fingerprint = proof['runtime_fingerprint']
        runtime = {k: fingerprint[k] for k in ('python', 'os', 'machine')}
        report = make_report(receipt, sha256(raw), sha256(Path(__file__).with_name('core.py').read_bytes()),
                             sha256(args.protocol.read_bytes()), runtime)
        export_report(report, args.output)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, OSError) as error:
        parser.exit(2, 'error: ' + str(error) + '\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
