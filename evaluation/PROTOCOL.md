# Forecast Interval Lab protocol v1

This protocol is proposed for coordinator and independent plan review before
implementation or comparison execution. It freezes the choices below. Changes
after acceptance require an explicit reviewed amendment and new evidence.

## Question and scope

How do frozen and rolling absolute-residual intervals around a last-value forecast
trade off coverage, width and interval score on three toy stochastic processes?
This is an original, offline, standard-library Python engineering lab. No external
datasets, fitted large models, API calls, private parameters or real asset forecasts
are used. Both methods share the same last-value point prediction.

## Time and intervals

Use zero-based indices and nominal coverage 0.90, alpha = 0.10. Each series has
384 observations: context/train indices 0..127, calibration targets 128..255,
and test targets 256..383. The first 128 observations provide past context only;
there are no fitted parameters. For every target t, point prediction p[t] = y[t-1]
and absolute error r[t] = abs(y[t] - p[t]). Calibration includes 128 residuals,
r[128]..r[255]; r[128] uses the last context value y[127]. No test observation
is used for initial calibration.

For n residuals sorted ascending as a[1]..a[n], use
k = ceil((n+1)*(1-alpha)), q = a[k]. Compute the rank with exact rational
arithmetic from the decimal representation of alpha, avoiding floating-point
ceil artifacts. Require 0 < alpha < 1 and 1 <= k <= n. A rank beyond n is an
explicit insufficient-calibration error, never a capped rank or infinite interval.
At alpha 0.10 the minimum is nine residuals; n=128 gives k=117.

Frozen uses q from the initial calibration residuals for every test target.
Rolling uses the latest 128 *past* residuals, initialized by the calibration set.
Before observing y[t], emit [p[t]-q, p[t]+q]. Only after emission and scoring,
append r[t], discard the oldest rolling residual, and make y[t] the next lagged
observation. Frozen's radius remains fixed; its point prediction still updates.

Public sequential API: initialize from finite history, calibration size and alpha;
request the next prediction; observe its target; repeat. Reject nonnumeric/bool
or nonfinite observations, nonfinite arithmetic, invalid alpha/window sizes,
insufficient history, repeated prediction without observation, and observation
without a pending prediction. Failed observations must leave state recoverable.
The batch wrapper must apply the same sequential API. CSV/JSON wrappers must
reject missing, duplicate, unknown or malformed fields rather than silently
coerce them. Do not emit JSON NaN/Infinity.

## Metrics

For each test interval [L,U] and target y, inclusive coverage is 1{L <= y <= U};
width is U-L. Interval score is
IS = (U-L) + (2/alpha)*(L-y)*1{y<L} + (2/alpha)*(y-U)*1{y>U}.
Report each metric's arithmetic mean across the 128 test targets. Smaller score
and width have different meanings from coverage; a wide interval is not deemed
better merely because it covers more targets. No coverage or superiority cutoff
is an acceptance condition.

Hand checks: residuals 1..9 at alpha .10 give rank 9 and q=9. For [0,2],
targets -1,1,3 give coverages 0,1,0; widths 2,2,2; scores 22,2,22.
Thus means are 1/3 coverage, 2 width and 46/3 score. Endpoints 0 and 2 are covered
with score 2. History 0..9 has nine residuals all equal to one: the first
prediction is [8,10]; observing 10 gives the next interval [9,11]. A later
changed observation must not affect intervals emitted at or before its own time.

## Synthetic processes

Use an isolated random.Random(seed) per family and seed, generating exactly 384
standard normal draws via gauss(0,1). No burn-in or parameter estimation. Seeds
are the fixed integers [7,23,101] for each family; use the same draws across
families for transparent paired construction, without treating families as
independent replications.

* stationary: y[t] = e[t], e[t] ~ N(0,1).
* ar: phi=.8; y[0]=e[0]/sqrt(1-phi^2); y[t]=phi*y[t-1]+e[t].
* drift: y[t]=e[t] for t<288; y[t]=3+2*e[t] for t>=288. The change occurs
  after 32 test targets, leaving 96 post-change targets. It is a stress test.

All parameters are authored toy constants, unrelated to any private record.
Record actual Python version: random.gauss reproducibility is only asserted for
the verified interpreter, with no promise across Python implementations/versions.

## Reporting and workload reconciliation

The queued brief requested 20 seeds per family, which would require 360 per-seed
numeric values alone. The unchanged runner allows 100 metrics. This v1 proposes
a downward adjustment to three seeds per family: 3 families x 3 seeds x 2 methods
x 3 metrics = 54 per-seed values, plus 18 means and 18 sample standard deviations
(denominator 3-1), exactly 90 numeric metrics. Preserve all 90. Use identifiers
{family}_s{seed}_{method}_{metric}, {family}_{method}_{metric}_mean and
{family}_{method}_{metric}_sd. Families: stationary, ar, drift; methods: frozen,
rolling; metrics: coverage, width, score. Standard deviation describes seed-to-seed
variation, not a standard error or a calibrated uncertainty interval.

Three seeds offer weak evidence about simulation variability. This is a bounded
engineering comparison, not a high-precision Monte Carlo study. The original
queued brief remains unchanged in the coordinator's private records. Do not
increase runner limits, hide numeric results in check names, partition unapproved
attempts or regenerate evaluation data in report exporters. CSV/JSON exports
must copy exact values from the single admitted receipt, with explicit provenance.

## Acceptance and execution

Before implementation, obtain coordinator and independent plan review and the
plan gate. Meaningful ordinary tests must cover hand calculations, rank edges,
split/calibration boundaries, update order, initial and rolling windows, constant
series, finite ordered intervals, invalid inputs, determinism and future
perturbation. Test generation uses tiny fixtures, never the complete comparison.

Inside the single admitted evaluate() invocation, run all nine paths and both
methods, check 128 predictions per path/method, finite ordered intervals, metrics
in their mathematical domains (coverage [0,1], nonnegative width/score), and
exactly the 90 expected keys. As an explicit reproducibility check, regenerate
the same paths and recalculate the same metrics a second time *inside that same
metered invocation*, requiring exact equality. This is included in the workload;
no evaluation or substantive rerun is allowed outside the production runner.

No estimator must win. Poor drift coverage remains in the report. Checks measure
correctness, determinism and complete reporting, never a desired scientific result.

The self-contained original core module defines evaluate() and contains the exact
pure implementation used by the package and unit tests. Only allowed stdlib
imports; no files, subprocesses, networking, introspection or dynamic code in core.
CLI and receipt exporters remain separate. The demo uses history 0..9 and targets
[10,12,11], alpha .10, window nine: three deterministic predictions per method.

After independent code/test review and passed implementation/tests gates, admit
one production attempt under the exact qualified runner, source/proof manifest,
stage operation and shared host lease. Target <=60 aggregate CPU-seconds, 256 MiB
operational measured memory and 120 wall-seconds. Limits may only decrease. No
heavy work or installation while priority diagnostic availability is uncertain.
Failed or incomplete attempts remain in resource/reporting records; no automatic
retry or reset. Operational guards may overshoot; they are not hard guarantees.

Then verify a clean, fully offline install with already-installed tools and an
exact operation grant. Run installed imports/CLI from outside the source tree,
record source/artifact hashes, and require all behavior tests to pass. Publication
requires documentation, independent review of the exact tree/history, the exact
publication grant/claim, public owner/mapping verification and remote byte readback.
No license grant, CI workflows, paid service, schedule or package upload is included.
