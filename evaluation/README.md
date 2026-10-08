# Evaluation and reporting

The predeclared [protocol](PROTOCOL.md) is frozen at SHA-256
`6381adbb7bd66cf3049e4637f0ef18161259ae8d1fba3639d377f79c9e18b2dc`.
It defines the generators, alpha, calibration rank, update order, seeds, splits,
metrics and correctness checks before implementation. The independent plan review
and coordinator accepted the three-seed reduction; the original queued workload
was 20 seeds per family. This changes precision, not the methods or metrics.

The implementation lives in `forecast_interval_lab/core.py`. Its `evaluate()`
returns exactly 90 numeric metrics and 12 Boolean acceptance checks. It performs
the comparison twice inside one invocation to check exact reproducibility. Both
passes belong to the single admitted workload. Neither the CLI demo nor ordinary
tests calls `evaluate()` or `comparison()`.

For an independent reproduction in your own computing environment, the package
exposes this entry point:

```sh
python3 -B -c 'import json; from forecast_interval_lab.core import evaluate; print(json.dumps(evaluate(), sort_keys=True, indent=2, allow_nan=False))'
```

This is a complete comparison command, not a smoke test. It does not provide the
managed workflow's metering, lease or admission evidence. Within the managed shared
host workflow, run it only through the exact admitted production runner; a direct
invocation is not an alternative to that admission. The published results come
from one admitted invocation on CPython 3.14.7, Darwin arm64. All 12 checks passed,
including exact repetition inside that invocation. Exact random sequences are
only asserted for that verified interpreter.

## Export an admitted receipt

The separate exporter never generates series or invokes evaluation. After an
admitted successful run, it verifies the receipt's core source digest, proof digest
and exact frozen protocol hash, requires all 90 values, and copies those values:

```sh
python3 -B -m forecast_interval_lab.reports RECEIPT.json \
  --proof PROOF.json --protocol evaluation/PROTOCOL.md --output evaluation/results
```

The output directory must be new. It contains:

* `per_seed.csv`: 18 family/seed/method rows, each with coverage, width and score.
* `aggregate.csv`: 18 family/method/metric rows, each with the measured mean and
  sample standard deviation across seeds.
* `results.json`: all 90 exact numeric values, source/protocol/receipt hashes,
  the verified interpreter labels and allowlisted resource values.

The private receipt and proof are not publication inputs. Only the separately
reviewed allowlisted exports may be published. An exporter accepting a shape/hash
is not evidence that a runner was admitted or that a project is complete.

Coverage counts endpoints. Width and interval score accompany coverage because
wide intervals can cover more while being less useful. Sample SD describes three
seed-level outcomes; it is neither a standard error nor a confidence interval.
Poor drift coverage and all failed/incomplete admitted attempts must remain
visible. No performance threshold is chosen after looking at results.

## Resource evidence

The single invocation was charged 60 CPU seconds conservatively. Measured CPU
before final receipt/database closeout was 0.173796 seconds, a lower bound on
full-operation usage; runner wall time was 0.18980312487110496 seconds. Summed
process peak memory was 60,932,096 bytes. The owned child exited successfully and
was reaped, and the shared lease was released. There were no failed or incomplete
admitted comparison attempts.

Peak memory is the sum of process high-water marks, not necessarily simultaneous
memory use. CPU/memory monitoring is operational and may overshoot. Resource
targets are not results or hard guarantees. See [the full measured report](RESULTS.md).
