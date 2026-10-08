"""Original, self-contained interval engine and admitted synthetic evaluation.

The complete comparison is only to be invoked through its admitted runner.
Importing this module does not evaluate or read any data.
"""

import math
import random
import statistics
from fractions import Fraction

ALPHA = 0.10
WINDOW = 128
HISTORY_SIZE = 256
TEST_SIZE = 128
SEEDS = (7, 23, 101)
FAMILIES = ("stationary", "ar", "drift")
METHODS = ("frozen", "rolling")
METRICS = ("coverage", "width", "score")


def finite_number(value, name="observation"):
    """Accept real built-in numbers, excluding bool and nonfinite values."""
    if type(value) not in (int, float):
        raise ValueError(name + " must be a finite number, not a boolean or string")
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError(name + " is outside finite floating-point range") from error
    if not math.isfinite(result):
        raise ValueError(name + " must be finite")
    return result


def valid_alpha(alpha):
    value = finite_number(alpha, "alpha")
    if not 0 < value < 1:
        raise ValueError("alpha must be strictly between zero and one")
    return value


def quantile_rank(count, alpha=ALPHA):
    """One-based ceil((n+1)*(1-alpha)), exact for decimal alpha text."""
    valid_alpha(alpha)
    if type(count) is not int or count < 1:
        raise ValueError("residual count must be a positive integer")
    rank = math.ceil((count + 1) * (1 - Fraction(str(alpha))))
    if rank > count:
        raise ValueError("insufficient calibration residuals for alpha")
    return rank


def residual_quantile(residuals, alpha=ALPHA):
    values = [finite_number(v, "residual") for v in residuals]
    if any(v < 0 for v in values):
        raise ValueError("residuals must be nonnegative")
    return sorted(values)[quantile_rank(len(values), alpha) - 1]


def interval_metrics(lower, upper, target, alpha=ALPHA):
    """Inclusive coverage, width and interval score for one interval."""
    lower = finite_number(lower, "lower bound")
    upper = finite_number(upper, "upper bound")
    target = finite_number(target)
    alpha = valid_alpha(alpha)
    if lower > upper:
        raise ValueError("lower bound must not exceed upper bound")
    width = finite_number(upper - lower, "interval width")
    penalty = 0.0
    if target < lower:
        penalty = (2.0 / alpha) * (lower - target)
    elif target > upper:
        penalty = (2.0 / alpha) * (target - upper)
    return {"coverage": float(lower <= target <= upper), "width": width,
            "score": finite_number(width + penalty, "interval score")}


def mean_metrics(rows):
    if not rows:
        raise ValueError("at least one scored interval is required")
    return {key: finite_number(statistics.mean(row[key] for row in rows), key)
            for key in METRICS}


class IntervalForecaster:
    """Emit a prediction, then observe exactly one target before predicting again.

    State attributes are implementation details; use predict/observe to update.
    Returned records are separate from the internal pending prediction.
    """

    def __init__(self, history, window=WINDOW, alpha=ALPHA):
        self.alpha = valid_alpha(alpha)
        if type(window) is not int or window < 1:
            raise ValueError("window must be a positive integer")
        quantile_rank(window, alpha)
        if not isinstance(history, (list, tuple)):
            raise ValueError("history must be an array")
        values = [finite_number(v) for v in history]
        if len(values) < window + 1:
            raise ValueError("history needs at least window+1 observations")
        start = len(values) - window
        residuals = [finite_number(abs(values[t] - values[t - 1]), "residual")
                     for t in range(start, len(values))]
        self.window = window
        self.residuals = residuals
        self.frozen_radius = residual_quantile(residuals, alpha)
        self.last = values[-1]
        self.index = len(values)
        self.pending = None

    def predict(self):
        if self.pending is not None:
            raise ValueError("observe the pending prediction before predicting again")
        radii = {"frozen": self.frozen_radius,
                 "rolling": residual_quantile(self.residuals, self.alpha)}
        prediction = {"time": self.index, "point": self.last}
        for method, radius in radii.items():
            lower = finite_number(self.last - radius, "lower bound")
            upper = finite_number(self.last + radius, "upper bound")
            finite_number(upper - lower, "interval width")
            prediction[method] = {"lower": lower, "upper": upper}
        self.pending = prediction
        return {"time": prediction["time"], "point": prediction["point"],
                **{m: dict(prediction[m]) for m in METHODS}}

    def observe(self, target):
        if self.pending is None:
            raise ValueError("predict before observing a target")
        target = finite_number(target)
        residual = finite_number(abs(target - self.last), "residual")
        prediction = self.pending
        result = {"time": prediction["time"], "point": prediction["point"],
                  "target": target}
        for method in METHODS:
            interval = prediction[method]
            result[method] = {**interval, **interval_metrics(
                interval["lower"], interval["upper"], target, self.alpha)}
        # All validation/scoring has succeeded before any state change.
        self.residuals = self.residuals[1:] + [residual]
        self.last = target
        self.index += 1
        self.pending = None
        return result


def forecast(history, observations, window=WINDOW, alpha=ALPHA):
    if not isinstance(observations, (list, tuple)) or not observations:
        raise ValueError("observations must be a nonempty array")
    engine = IntervalForecaster(history, window, alpha)
    rows = []
    for target in observations:
        engine.predict()
        rows.append(engine.observe(target))
    return rows


def generate_series(family, seed, length=HISTORY_SIZE + TEST_SIZE):
    """Generate only original toy data; no burn-in or fitted parameters."""
    if family not in FAMILIES:
        raise ValueError("unknown synthetic family")
    if type(seed) is not int or type(length) is not int or length < 1:
        raise ValueError("seed must be an integer and length a positive integer")
    rng = random.Random(seed)
    noise = [rng.gauss(0, 1) for _ in range(length)]
    if family == "stationary":
        return noise
    if family == "drift":
        return [e if t < 288 else 3 + 2 * e for t, e in enumerate(noise)]
    series = [noise[0] / math.sqrt(1 - 0.8 ** 2)]
    for e in noise[1:]:
        series.append(0.8 * series[-1] + e)
    return series


def metric_names():
    names = {f"{family}_s{seed}_{method}_{metric}"
             for family in FAMILIES for seed in SEEDS
             for method in METHODS for metric in METRICS}
    names.update(f"{family}_{method}_{metric}_{summary}"
                 for family in FAMILIES for method in METHODS
                 for metric in METRICS for summary in ("mean", "sd"))
    return names


def comparison():
    """One complete protocol pass; called twice only inside admitted evaluate."""
    metrics = {}
    checks = []
    for family in FAMILIES:
        for seed in SEEDS:
            values = generate_series(family, seed)
            rows = forecast(values[:HISTORY_SIZE], values[HISTORY_SIZE:], WINDOW, ALPHA)
            ordered = all(math.isfinite(row[m][k])
                          for row in rows for m in METHODS
                          for k in ("lower", "upper", "coverage", "width", "score"))
            ordered = ordered and all(row[m]["lower"] <= row[m]["upper"]
                                      for row in rows for m in METHODS)
            checks.append({"name": f"{family} seed {seed} finite ordered 128 predictions",
                           "passed": len(rows) == TEST_SIZE and ordered})
            for method in METHODS:
                for metric, value in mean_metrics([row[method] for row in rows]).items():
                    metrics[f"{family}_s{seed}_{method}_{metric}"] = value
        for method in METHODS:
            for metric in METRICS:
                values = [metrics[f"{family}_s{s}_{method}_{metric}"] for s in SEEDS]
                metrics[f"{family}_{method}_{metric}_mean"] = float(statistics.mean(values))
                metrics[f"{family}_{method}_{metric}_sd"] = float(statistics.stdev(values))
    checks.append({"name": "complete ninety finite numeric metric values",
                   "passed": set(metrics) == metric_names() and len(metrics) == 90
                   and all(type(v) in (int, float) and math.isfinite(v)
                           for v in metrics.values())})
    checks.append({"name": "per seed metrics satisfy mathematical domains",
                   "passed": all(v >= 0 and (not k.endswith("_coverage") or v <= 1)
                                 for k, v in metrics.items())})
    return {"metrics": metrics, "checks": checks}


def evaluate():
    """The frozen comparison plus exact reproduction in one metered invocation."""
    first = comparison()
    second = comparison()
    first["checks"].append({"name": "same invocation exact reproducibility",
                            "passed": first == second})
    return first
