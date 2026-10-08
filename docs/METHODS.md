# What the intervals mean

For a target at time t, both methods predict the previous observation:

    point[t] = y[t-1]
    residual[t] = abs(y[t] - point[t])

An interval's center therefore changes after each observation. Its radius is
computed from errors whose targets have already been observed.

The frozen method uses the initial calibration errors throughout the test period.
The rolling method replaces its oldest error with the newly observed error after
each prediction. These choices let us inspect the cost of keeping old information
versus adapting to recent errors. Neither choice is universally better.

For n calibration errors, sort from smallest to largest and select the one-based
rank `ceil((n+1)*(1-alpha))`. The interval is `[point-radius, point+radius]`.
With alpha 0.10 and n=128, the rank is 117. A requested rank beyond the sample is
an error. Nine errors are the minimum for this finite interval convention at 90%.
The rank calculation treats the supplied decimal alpha exactly; it does not round
an intermediate floating-point product before taking the ceiling.

The finite-sample adjustment resembles a conformal calibration rank, but this
lab does not assert a distribution-free temporal coverage guarantee. Adjacent
last-value errors can be dependent even for independent observations, and the
change-point generator changes the error distribution. Exchangeability of the
calibration and future residuals is not established here. The nominal 90% is a
chosen target to compare against measured coverage, not a promise.

## Observe after predicting

The 384-observation experiment uses context 0..127, calibration targets 128..255,
and test targets 256..383. The first calibration prediction uses y[127]. The
first test radius sees residuals through target 255 only. To predict target 257,
the rolling method may use the just-observed error at 256. It may never use the
error at 257 itself. The frozen radius does not update, while its center does.

Changing y[t] can change the score of the interval already emitted at t and
predictions at later times. It cannot change the interval emitted at t or before.
This distinction is tested directly with future perturbations.

## Read the three metrics together

Coverage is the fraction of test targets inside their intervals, including
endpoints. Mean width is the average upper bound minus lower bound. Interval
score adds a miss penalty to width:

    score = width
            + (2/alpha)*(lower-y), if y < lower
            + (2/alpha)*(y-upper), if y > upper

The two penalty conditions are mutually exclusive. For a covered target the score
is exactly the width. Lower interval score is preferable under this scoring rule;
narrower width without regard to misses is not necessarily preferable. The report
retains all metrics together and has no requirement for either method to win.

For interval [0,2] at alpha .10, targets -1,1,3 have scores 22,2,22 and coverage
0,1,0. Mean score is 46/3, coverage is 1/3 and width is 2. Both endpoints are
covered and have score 2. Residuals [1,2,3,4,5,6,7,8,9] select radius 9.

For history [0,1,2,3,4,5,6,7,8,9], nine initial errors equal one. Both methods emit
[8,10] for the next target. After observing 10, both emit [9,11]. Observing 12
adds an error of two, so the next rolling interval is [10,14], while the frozen
interval is [11,13]. The difference is driven by a past error, not the next target.

## Limits of the experiment

All inputs are generated toy data. Three fixed seeds per family give little
precision about simulation variability. Sample standard deviation uses denominator
n-1 across the three seed-level metric values; it is not a standard error or a
confidence interval. Families share random draws for transparent paired
construction, so they are not independent replications. Results apply to the
specified generators and verified interpreter only. No real asset, weather,
business, safety or investment forecast is produced or validated by this lab.
