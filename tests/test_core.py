import math
import random
import unittest
from forecast_interval_lab.core import (IntervalForecaster, forecast, generate_series,
    interval_metrics, mean_metrics, quantile_rank, residual_quantile)


class QuantileTests(unittest.TestCase):
    def test_hand_computed_rank_and_order_statistic(self):
        self.assertEqual(quantile_rank(9, .1), 9)
        self.assertEqual(quantile_rank(128, .1), 117)
        self.assertEqual(residual_quantile([9, 1, 4, 3, 2, 5, 7, 6, 8]), 9)
        self.assertEqual(residual_quantile([3, 1, 8, 2], .4), 3)

    def test_exact_decimal_boundary(self):
        self.assertEqual(quantile_rank(9, .7), 3)
        self.assertEqual(quantile_rank(9, .699999999999), 4)
        self.assertEqual(quantile_rank(9, .700000000001), 3)

    def test_warmup_and_invalid_alpha(self):
        for n in (0, 8, -1, True, 9.0):
            with self.subTest(n=n), self.assertRaises(ValueError):
                quantile_rank(n, .1)
        for alpha in (0, 1, -1, 2, True, '.1', None, math.nan, math.inf):
            with self.subTest(alpha=alpha), self.assertRaises(ValueError):
                quantile_rank(9, alpha)

    def test_residual_validation_and_no_mutation(self):
        values = list(range(9, 0, -1))
        residual_quantile(values)
        self.assertEqual(values, list(range(9, 0, -1)))
        for bad in (-1, math.nan, math.inf, True, '1'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                residual_quantile([bad] + [1] * 8)


class MetricTests(unittest.TestCase):
    def test_hand_calculated_metrics(self):
        rows = [interval_metrics(0, 2, y, .1) for y in (-1, 1, 3)]
        self.assertEqual([r['score'] for r in rows], [22, 2, 22])
        self.assertEqual([r['coverage'] for r in rows], [0, 1, 0])
        self.assertEqual([r['width'] for r in rows], [2, 2, 2])
        average = mean_metrics(rows)
        self.assertAlmostEqual(average['coverage'], 1 / 3)
        self.assertEqual(average['width'], 2)
        self.assertAlmostEqual(average['score'], 46 / 3)

    def test_inclusive_endpoints_and_zero_width(self):
        for target in (0, 2):
            self.assertEqual(interval_metrics(0, 2, target),
                             {'coverage': 1, 'width': 2, 'score': 2})
        self.assertEqual(interval_metrics(2, 2, 2), {'coverage': 1, 'width': 0, 'score': 0})
        self.assertEqual(interval_metrics(2, 2, 3)['score'], 20)

    def test_invalid_bounds_target_and_arithmetic(self):
        for args in ((2, 0, 1), (0, 2, math.nan), (-1e308, 1e308, 0),
                     (0, 1, 1e308), (True, 2, 1), (0, math.inf, 1)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                interval_metrics(*args)
        with self.assertRaises(ValueError):
            mean_metrics([])


class TemporalTests(unittest.TestCase):
    def test_demo_intervals_and_scores_by_hand(self):
        rows = forecast(list(range(10)), [10, 12, 11], 9)
        self.assertEqual([r['time'] for r in rows], [10, 11, 12])
        self.assertEqual([r['point'] for r in rows], [9, 10, 12])
        self.assertEqual([(r['frozen']['lower'], r['frozen']['upper']) for r in rows],
                         [(8, 10), (9, 11), (11, 13)])
        self.assertEqual([(r['rolling']['lower'], r['rolling']['upper']) for r in rows],
                         [(8, 10), (9, 11), (10, 14)])
        self.assertEqual([r['frozen']['score'] for r in rows], [2, 22, 2])
        self.assertEqual([r['rolling']['score'] for r in rows], [2, 22, 4])

    def test_rolling_evicts_oldest_after_observation(self):
        engine = IntervalForecaster([0, 9, 10, 11, 12, 13, 14, 15, 16, 17], 9)
        self.assertEqual(engine.predict()['rolling'], {'lower': 8, 'upper': 26})
        engine.observe(18)
        second = engine.predict()
        self.assertEqual(second['rolling'], {'lower': 17, 'upper': 19})
        self.assertEqual(second['frozen'], {'lower': 9, 'upper': 27})

    def test_calibration_excludes_older_history_errors(self):
        engine = IntervalForecaster([1000] * 4 + list(range(10)), 9)
        self.assertEqual(engine.predict()['rolling'], {'lower': 8, 'upper': 10})

    def test_full_split_boundaries_without_comparison(self):
        engine = IntervalForecaster([999] * 127 + [0] + list(range(1, 129)), 128)
        self.assertEqual(engine.index, 256)
        self.assertEqual(engine.residuals, [1] * 128)
        self.assertEqual(engine.predict()['rolling'], {'lower': 127, 'upper': 129})
        engine.observe(140)
        self.assertEqual(engine.residuals, [1] * 127 + [12])
        self.assertEqual(engine.predict()['frozen'], {'lower': 139, 'upper': 141})

    def test_future_perturbation_preserves_current_and_past_prediction(self):
        original = forecast(list(range(10)), [10, 11, 30, 31], 9)
        changed = forecast(list(range(10)), [10, 11, -30, -31], 9)
        self.assertEqual(original[:2], changed[:2])
        self.assertEqual(original[2]['point'], changed[2]['point'])
        for method in ('frozen', 'rolling'):
            for bound in ('lower', 'upper'):
                self.assertEqual(original[2][method][bound], changed[2][method][bound])
        self.assertNotEqual(original[3]['point'], changed[3]['point'])

    def test_constant_series_and_determinism(self):
        args = ([4] * 10, [4] * 3, 9)
        rows = forecast(*args)
        self.assertEqual(rows, forecast(*args))
        for row in rows:
            for method in ('frozen', 'rolling'):
                self.assertEqual(row[method], {'lower': 4, 'upper': 4, 'coverage': 1,
                                               'width': 0, 'score': 0})

    def test_transition_errors_and_detached_returned_prediction(self):
        engine = IntervalForecaster(list(range(10)), 9)
        with self.assertRaises(ValueError): engine.observe(10)
        prediction = engine.predict()
        prediction['rolling']['lower'] = -999
        with self.assertRaises(ValueError): engine.predict()
        self.assertEqual(engine.observe(10)['rolling']['lower'], 8)
        with self.assertRaises(ValueError): engine.observe(11)

    def test_failed_observation_is_recoverable(self):
        for bad in (math.nan, math.inf, True, None, '10', 1e308, 10 ** 400):
            with self.subTest(bad=str(bad)[:15]):
                engine = IntervalForecaster(list(range(10)), 9)
                engine.predict()
                with self.assertRaises(ValueError): engine.observe(bad)
                self.assertEqual(engine.observe(10), forecast(list(range(10)), [10], 9)[0])

    def test_invalid_history_window_and_observations(self):
        for history, window in [([], 9), (list(range(9)), 9), (list(range(10)), True),
                (list(range(10)), 0), (list(range(10)), 8),
                ([math.nan] + list(range(9)), 9), ([True] + list(range(9)), 9),
                ('0123456789', 9), (list(range(10)), 9.0)]:
            with self.subTest(window=window), self.assertRaises(ValueError):
                IntervalForecaster(history, window)
        for observations in ([], '10', None):
            with self.assertRaises(ValueError): forecast(list(range(10)), observations, 9)

    def test_nonfinite_prediction_leaves_no_pending_state(self):
        engine = IntervalForecaster([0] * 9 + [1e308], 9)
        with self.assertRaises(ValueError): engine.predict()
        self.assertIsNone(engine.pending)


class GeneratorTests(unittest.TestCase):
    def test_tiny_generators_follow_equations(self):
        rng = random.Random(7)
        noise = [rng.gauss(0, 1) for _ in range(4)]
        self.assertEqual(generate_series('stationary', 7, 4), noise)
        ar = generate_series('ar', 7, 4)
        self.assertEqual(ar[0], noise[0] / math.sqrt(1 - .8 ** 2))
        for t in range(1, 4): self.assertEqual(ar[t], .8 * ar[t - 1] + noise[t])
        self.assertEqual(generate_series('ar', 7, 4), ar)

    def test_change_point_at_288_without_forecasts(self):
        stationary = generate_series('stationary', 23, 290)
        drift = generate_series('drift', 23, 290)
        self.assertEqual(drift[:288], stationary[:288])
        self.assertEqual(drift[288:], [3 + 2 * v for v in stationary[288:]])

    def test_local_prng_preserves_global_state(self):
        before = random.getstate()
        generate_series('stationary', 7, 3)
        self.assertEqual(random.getstate(), before)

    def test_invalid_generator_inputs(self):
        for args in [('unknown', 7, 4), ('ar', True, 4), ('ar', 7, 0), ('ar', 7, 4.0)]:
            with self.assertRaises(ValueError): generate_series(*args)
