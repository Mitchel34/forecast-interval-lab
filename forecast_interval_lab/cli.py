"""Small offline demo and strict JSON input wrapper; never runs the benchmark."""
import argparse
import json
import sys
from pathlib import Path

from .core import forecast

MAX_INPUT_BYTES = 1024 * 1024


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key: " + key)
        value[key] = item
    return value


def reject_constant(value):
    raise ValueError("nonfinite JSON constant is not allowed")


def parse_input(raw):
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds one MiB")
    try:
        value = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except RecursionError as error:
        raise ValueError("JSON nesting exceeds the parser limit") from error
    if not isinstance(value, dict) or set(value) != {"history", "observations", "alpha", "window"}:
        raise ValueError("input must contain exactly history, observations, alpha and window")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect past-only forecast intervals offline.")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="three hand-checkable predictions")
    run = commands.add_parser("forecast", help="forecast a strict JSON input file")
    run.add_argument("input", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            data = {"history": list(range(10)), "observations": [10, 12, 11],
                    "window": 9, "alpha": 0.10}
        else:
            with args.input.open("rb") as handle:
                raw = handle.read(MAX_INPUT_BYTES + 1)
            data = parse_input(raw)
        result = {"alpha": data["alpha"], "window": data["window"],
                  "predictions": forecast(**data)}
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, TypeError, OverflowError, OSError) as error:
        print("error: " + str(error), file=sys.stderr)
        return 2
