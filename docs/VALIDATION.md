# Validation record

The current source passed 31 ordinary behavior tests on CPython 3.14.7. The latest
complete run occurred after verified shared-host clearance and completed with zero
failures or errors. Its unittest-reported time was 0.014 seconds; that is a small
test-suite observation, not a measured comparison or total CPU accounting.

The tests cover:

* Exact decimal quantile ranks, minimum calibration and hand-calculated scores.
* Calibration boundaries, rolling eviction and prediction-before-observation order.
* Future perturbations, constant series, deterministic generators and isolated PRNGs.
* Invalid finite/numeric inputs, recoverable observation errors and detached outputs.
* Strict JSON fields, CLI demo, malformed encoding and explicit nesting errors.
* Exact JSON/CSV metric mapping with distinct fixture values, protocol digest
  mismatch, private-field exclusion, huge integer and parser recursion errors.

A separate reviewer inspected the exact code and tests and reran targeted checks.
See [the independent review record](INDEPENDENT_REVIEW.json). Its technical result
does not establish evaluation admission, clean installation or publication.

## Retained verification history

An initial test-authoring command used incorrect relative paths and discovered no
tests. It was corrected before any test acceptance claim. A later nesting test
incorrectly assumed a particular interpreter recursion threshold and failed. The
revised test checks actual deep-input rejection and separately checks explicit
parser-error translation. The final complete suite passes.

Small ordinary checks also ran during a temporary shared-compute hold after its
scope was misread. That deviation was reported and the records retained. Later
capacity clearance does not retroactively make those runs compliant. A fresh,
timestamped complete run after clearance supplies the current test observation;
workflow acceptance remains separate. No full comparison or installation ran
during that hold.

## Measured comparison

One admitted invocation completed successfully on CPython 3.14.7, Darwin arm64,
with 90 finite numeric measurements and 12 passing acceptance checks. The
comparison is repeated within that one invocation to verify deterministic output.
No separate comparison rerun or failed/incomplete admitted attempt occurred.
The process was reaped and its shared compute lease released. All 90 values in
the [public JSON and CSV exports](../evaluation/results/results.json) were checked
against the actual receipt. Synthetic exporter fixtures remain separate schema
tests, not experimental results. See [results and resource scope](../evaluation/RESULTS.md).

## Clean installation

One offline build/install passed using existing local tools. All 31 original
tests passed against installed imports outside the source tree; the demo and
five installed module hashes were also verified. Evaluation entry points were
guarded against execution, so this check did not repeat the comparison. The
[installation record](INSTALL.md) distinguishes the build interpreter from the
verified runtime and documents resource-accounting limitations.

The [publication scope](PUBLICATION_CHECKLIST.md) describes the final review and
remote verification requirements. The plan/implementation/test evidence and
gate ledger are historical snapshots; descriptions of later work being pending
refer to the time those snapshots were recorded.
