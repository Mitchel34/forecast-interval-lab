# Forecast Interval Lab

Inspect how prediction intervals change when calibration errors are frozen or
updated after every observation. Both methods use the last observation as their
point forecast. The project is an original Python standard-library lab with
hand-checkable examples and a predeclared synthetic comparison.

The nominal interval level is 90%; it is not a coverage guarantee under temporal
dependence or drift. The measured comparison illustrates that limit: rolling
intervals improve coverage after a change point, but still miss the nominal target.

## Try the three-step demo

With Python 3.11 or newer, from the source directory:

```sh
python3 -B -m forecast_interval_lab demo
python3 -B -m forecast_interval_lab forecast examples/demo.json
python3 -B -m unittest discover -s tests -v
```

The two CLI commands produce the same JSON. The history is 0..9, with three new
observations 10,12,11 and a nine-residual calibration window:

| Target time | Point | Frozen interval | Rolling interval | Observed target |
| --- | ---: | --- | --- | ---: |
| 10 | 9 | [8,10] | [8,10] | 10 |
| 11 | 10 | [9,11] | [9,11] | 12 |
| 12 | 12 | [11,13] | [10,14] | 11 |

The error at time 11 widens the rolling interval at time 12. It cannot affect the
interval already emitted at time 11. The JSON includes each interval's inclusive
coverage indicator, width and interval score.

## Use your own finite sequence

`forecast` accepts a JSON object with exactly four keys:

```json
{"history":[0,1,2,3,4,5,6,7,8,9],"observations":[10,12,11],"alpha":0.1,"window":9}
```

`history` supplies at least `window+1` observations; the last `window` errors form
calibration. `observations` is a nonempty array of subsequent targets. Invalid
numbers, booleans, insufficient calibration, duplicate or unknown keys and
nonfinite arithmetic are errors. Input files are bounded to one MiB. The public
Python API makes the order explicit:

```python
from forecast_interval_lab import IntervalForecaster

model = IntervalForecaster(list(range(10)), window=9, alpha=0.1)
intervals = model.predict()  # available before observing the target
scored = model.observe(10)  # updates history only after scoring
```

See [methods and hand calculations](docs/METHODS.md) for the rank convention,
warm-up, temporal boundaries and coverage assumptions.

## The predeclared experiment

[Protocol v1](evaluation/PROTOCOL.md) freezes three toy families: independent
Gaussian noise, an autoregression and a mean/variance change point. Each has three
fixed seeds, 256 historical observations and 128 sequential test targets. All
54 per-seed coverage/width/score values, 18 means and 18 sample standard deviations
must be retained. The workload was reduced from 20 seeds per family to fit an
unchanged 100-metric result contract. Three seeds give weak simulation precision.
No method is required to win.

[Measured results](evaluation/RESULTS.md) retain every seed, mean and sample
standard deviation. Mean test coverage and interval score (lower is better) are:

| Family | Frozen coverage | Rolling coverage | Frozen score | Rolling score |
| --- | ---: | ---: | ---: | ---: |
| Independent noise | 89.58% | 89.58% | 5.929 | 5.982 |
| Autoregression | 90.36% | 90.10% | 4.573 | 4.618 |
| Mean/variance drift | 69.01% | 78.13% | 15.394 | 12.582 |

Rolling intervals widen under drift, improving coverage and score in this small
experiment. Both methods still under-cover. These three-seed results do not
establish a generally superior method.

[Evaluation instructions](evaluation/README.md) explain reproduction and receipt
exports. One admitted invocation passed all 12 correctness/reproducibility checks;
all 90 measured values were exported without rerunning the comparison. The
source passes 31 ordinary tests on CPython 3.14.7. See the
[validation record](docs/VALIDATION.md) for evidence and retained verification history.

## Installation and provenance

The runtime uses only Python's standard library. Packaging uses an already
available setuptools/wheel toolchain; no runtime dependencies are declared.
Offline build commands and the verification record are in
[installation](docs/INSTALL.md).

All data are original synthetic toy sequences; see [data provenance](data/manifest.json).
No real-world forecast, financial input, private dataset, hosted CI, paid API or
license grant is included. Public visibility does not itself grant a license.
