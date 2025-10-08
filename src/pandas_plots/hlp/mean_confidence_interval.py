
import numpy as np
import scipy.stats

# from devtools import debug

URL_REGEX = r"^(?:http|ftp)s?://"

def mean_confidence_interval(data, confidence=0.95, use_median=False, n_bootstraps=1000):
    """
    Calculate the mean or median and confidence interval.
    For median, uses bootstrapping for a more robust confidence interval.

    Parameters:
    data (array-like): The input data.
    confidence (float, optional): The confidence level for the interval. Defaults to 0.95.
    use_median (bool, optional): If True, calculates median and its confidence interval. Defaults to False.
    n_bootstraps (int, optional): Number of bootstrap samples for median CI. Only used if use_median is True.

    Returns:
    tuple: A tuple containing the central value (mean or median), margin of error, lower bound, and upper bound.
    """
    from .to_series import to_series
    data = to_series(data)
    if data is None or len(data) == 0:
        return np.nan, np.nan, np.nan, np.nan
    a = 1.0 * np.array(data)
    n = len(a)

    if use_median:
        if n < 2: # Cannot bootstrap with n < 2
            return np.median(a), np.nan, np.nan, np.nan

        bootstrapped_medians = []
        for _ in range(n_bootstraps):
            sample = np.random.choice(a, size=n, replace=True)
            bootstrapped_medians.append(np.median(sample))

        median = np.median(a)
        alpha = (1 - confidence) / 2
        lower_bound = np.percentile(bootstrapped_medians, alpha * 100)
        upper_bound = np.percentile(bootstrapped_medians, (1 - alpha) * 100)
        margin = (upper_bound - lower_bound) / 2 # Simple approximation for margin based on interval width
        return median, margin, lower_bound, upper_bound
    else:
        mean = np.mean(a)
        if n <= 1:
            return mean, np.nan, np.nan, np.nan
        se = scipy.stats.sem(a)
        margin = se * scipy.stats.t.ppf((1 + confidence) / 2.0, n - 1)
        return mean, margin, mean - margin, mean + margin