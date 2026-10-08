"""Past-only forecast intervals using original synthetic examples."""
from .core import IntervalForecaster, forecast, interval_metrics, residual_quantile

__version__ = "0.1.0"
__all__ = ["IntervalForecaster", "forecast", "interval_metrics", "residual_quantile"]
