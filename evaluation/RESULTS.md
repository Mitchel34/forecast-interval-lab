# Measured results

These measurements come from one admitted invocation of protocol v1 on CPython
3.14.7 (Darwin arm64). All 90 metrics and 12 acceptance checks passed. Three
fixed seeds (7, 23, 101) per family each contribute 128 sequential test targets.
The table reports mean ± sample SD across seeds; coverage is expressed in percent
(its SD in percentage points). SD is neither a standard error nor a confidence
interval. Values below are rounded only for display.

| Family | Method | Coverage (%) | Width | Interval score |
| --- | --- | ---: | ---: | ---: |
| stationary | frozen | 89.583 ± 0.451 | 4.960 ± 0.334 | 5.929 ± 0.352 |
| stationary | rolling | 89.583 ± 1.193 | 4.952 ± 0.398 | 5.982 ± 0.377 |
| ar | frozen | 90.365 ± 2.511 | 3.656 ± 0.123 | 4.573 ± 0.042 |
| ar | rolling | 90.104 ± 1.193 | 3.730 ± 0.179 | 4.618 ± 0.062 |
| drift | frozen | 69.010 ± 6.552 | 4.960 ± 0.334 | 15.394 ± 1.900 |
| drift | rolling | 78.125 ± 3.125 | 6.619 ± 0.497 | 12.582 ± 1.337 |

Read the [complete per-seed CSV](results/per_seed.csv), [aggregate CSV](results/aggregate.csv)
and [exact JSON values](results/results.json). All values were copied from the
verified receipt by a separate exporter; export did not rerun the experiment.

## Interpretation and limits

The stationary and autoregressive cases have mean coverage near the nominal 90%.
Under the specified mean/variance change, frozen coverage falls to 69.01%. Rolling
coverage rises to 78.13%, with wider intervals and lower mean interval score than
frozen intervals. Both still miss the nominal target. Frozen intervals have slightly
lower mean score in the stationary and autoregressive cases.

This is a bounded demonstration of adaptation, not a general method ranking.
Three seeds give weak simulation precision. The families share seeded draws and
are not independent replications. No real-world data or forecasting outcome was
tested. Temporal dependence and drift prevent a claimed exchangeability-based
coverage guarantee. The [frozen protocol](PROTOCOL.md) specifies all seeds, splits,
generators, metrics and checks; no performance threshold was added after seeing results.

## Execution and provenance

* Admitted invocations: 1; failed/incomplete admitted comparison attempts: 0.
* Exact reproducibility: two complete comparisons inside that single invocation.
* Runtime: CPython 3.14.7, Darwin arm64, local CPU; no external service calls.
* Conservative CPU ledger charge: 60.0 seconds.
* Measured CPU before final receipt/database closeout: 0.173796 seconds.
* Runner wall time: 0.18980312487110496 seconds.
* Sum of process peak memory: 60,932,096 bytes.

The measured CPU field is a lower bound on the whole operation. The ledger charge
is a conservative accounting amount, not measured compute use. Memory combines
process high-water marks and need not have occurred simultaneously. Resource
guards are operational bounds, not hard guarantees. The owned child exited
successfully, was reaped, and its shared compute lease was released.

Core SHA-256: `435c4bc645f9a0a7f762554b1f8467a52d63a851917409959c3543a9968d5c51`.

Protocol SHA-256: `6381adbb7bd66cf3049e4637f0ef18161259ae8d1fba3639d377f79c9e18b2dc`.

Private receipt SHA-256: `24933fc412a2e75edbe94f2bf769beaa3804eacba91f5e0fbbfa95291d8387c3`.

Only allowlisted measurements and platform/version labels are published. The
private receipt, host paths, process identities and workflow registry are excluded.
The [validation record](../docs/VALIDATION.md) retains earlier ordinary-test
failures and the temporary execution-hold deviation; none was a comparison attempt.
