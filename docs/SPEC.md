# Specification

Forecast Interval Lab makes the temporal information used by simple prediction
intervals inspectable. It compares a frozen absolute-residual radius with a
rolling radius around the same last-observation point forecast. The authoritative
method and bounded synthetic workload are in [protocol v1](../evaluation/PROTOCOL.md).

The planned deliverable is an original pure-Python package, a three-prediction
CLI demo, a strict JSON forecasting interface, behavior tests, a receipt-to-CSV/JSON
exporter and a measured comparison report. It has no third-party runtime
dependencies, training service or network requirement.

The CLI forecast input is one object with exactly `history`, `observations`,
`alpha` and `window`. History and observations are arrays of finite JSON numbers;
booleans are not observations. Window is a positive integer and alpha is strictly
between zero and one. History must supply at least window+1 observations and
the finite-sample rank must fit within window. Duplicate/unknown/missing keys,
malformed JSON, nonfinite arithmetic and invalid state transitions are errors.
The sequential API exposes prediction before observation, making information
availability explicit. Output records contain time, point forecast, each method's
interval, observed target and scores. Report exports preserve all measured
per-seed values and aggregates from the admitted receipt.

The work uses synthetic toy constants only. The package does not claim nominal
coverage for correlated or drifting residuals, real-world forecasting validity,
investment suitability or state-of-the-art results. Three seeds per family limit
Monte Carlo precision. Width and interval score accompany coverage throughout.

Acceptance requires an independently reviewed frozen plan, correct temporal
behavior and hand calculations, deterministic valid output, explicit errors,
complete admitted evaluation accounting, clean offline installation, documentation,
and independent review plus exact-byte verification of the public commit.
No license grant or hosted CI is included.
