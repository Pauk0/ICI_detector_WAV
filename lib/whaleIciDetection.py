import numpy as np
import pandas as pd
from scipy import signal
import logging
import numpy as np
from pandas import Timedelta
from datetime import timedelta
from osekit.core.audio_data import AudioData
from osekit.core.audio_file import AudioFile
import scipy.signal as sp
from pathlib import Path
import pandas as pd
from pandas import Timestamp

from .signalProcessing import *

def compute_longterm_cepstro(audio_files, begin_date, end_date,FFT_SIZE, F_MIN, F_MAX):
    # Initialize empty lists to store concatenated results
    all_frequencies = []
    all_times = []
    all_spectrograms = []

    OVERLAP = 0.95

    for d in pd.date_range(begin_date, end_date - Timedelta(days=1), freq='D'):
        audio_data_day = AudioData.from_files(
            files=audio_files,
            begin= d,
            end= d + pd.Timedelta(days=1)
        )

        noverlap = int(FFT_SIZE * OVERLAP)
        additional_freq = 0
        sampling_rate = audio_data_day.sample_rate
        demBounds = [F_MIN, F_MAX]
        integration = 5

        if audio_data_day.is_empty:
            print("no data")
            break
        audio_data_day_value = audio_data_day.get_value()

        if demBounds:
            try:
                audio_data_day_value, sampling_rate = get_demodulated_samples(audio_data_day_value, sampling_rate, demBounds)
                additional_freq = demBounds[0]
            except Exception as e:
                print(e)

        # Ensure the input signal is long enough for the FFT window
        if len(audio_data_day_value) < int(FFT_SIZE):
            audio_data_day_value = np.pad(audio_data_day_value, (0, int(FFT_SIZE) - len(audio_data_day_value)), mode='constant')

        frequencies, times, spectrogram = sp.stft(audio_data_day_value, fs=sampling_rate, nperseg=int(FFT_SIZE), noverlap=noverlap)
        frequencies += additional_freq

        times = pd.to_datetime(d) + pd.to_timedelta(times, unit='s')
        times = times - pd.Timedelta(microseconds=1)

        if integration:
            times, spectrogram = integrate_tf_representation(times, np.abs(spectrogram), integration)

        amp = 10000 * np.abs(spectrogram)

        all_frequencies.append(frequencies)
        all_times.append(times)
        all_spectrograms.append(amp)

        # Concatenate all results
        f = all_frequencies[0]  # Frequencies are the same for all traces
        t = np.concatenate(all_times)
        s = np.concatenate(all_spectrograms, axis=1)

    # Compute the cepstrogram for the concatenated spectrogram
    t,q,c = get_cepstro(t, f, s)

    return t,q,c

def compute_mean_cepstrum(t,c,q, begin_date, end_date):
    t_hourly, c_hourly = [], []
    delta = timedelta(seconds=3600)

    for hour in pd.date_range(start=begin_date, end=end_date, freq='h'):
        mask = (t >= hour) & (t < hour + delta)
        if np.any(mask):
            c_hour = get_mean_cepstrum(c[:, mask], q)
            t_hourly.append(hour)
            c_hourly.append(c_hour)
    c_hourly = np.transpose(c_hourly)

    return c_hourly, t_hourly

def compute_p2vr(c_hourly, q, PEAK_BOUNDARIES, VALLEY_BOUNDARIES, WINDOW_SIZE) :
    cepstrogram_df = pd.DataFrame(np.abs(c_hourly))

    # Define the regions for peak and valley
    peak_region = np.logical_and(q > PEAK_BOUNDARIES[0], q < PEAK_BOUNDARIES[1])
    valley_low_region = np.logical_and(q > VALLEY_BOUNDARIES[0], q < PEAK_BOUNDARIES[0])
    valley_high_region = np.logical_and(q > PEAK_BOUNDARIES[1], q < VALLEY_BOUNDARIES[1])

    valley_mean = 0.5 * cepstrogram_df.iloc[valley_low_region].mean(axis=0).rolling(WINDOW_SIZE,
                                                                                    min_periods=1, center=True).mean() + \
                  0.5 * cepstrogram_df.iloc[valley_high_region].mean(axis=0).rolling(WINDOW_SIZE,
                                                                                     min_periods=1, center=True).mean()

    peak_mean = cepstrogram_df.iloc[peak_region].mean(axis=0).rolling(WINDOW_SIZE, min_periods=1,
                                                                      center=True).mean()
    # Compute the peak to valley ratio
    p2vr = (peak_mean ** 3 / valley_mean ** 3) - 1

    return p2vr

def apply_threshold(THRESHOLD, p2vr):
    above_THRESHOLD_indices = np.where(p2vr > THRESHOLD)[0]

    positive_detection = np.zeros_like(p2vr, dtype=int)
    positive_detection[above_THRESHOLD_indices] = 1

    return positive_detection

def get_mean_cepstrum(cepstrum: np.ndarray, quefrency: np.ndarray = None) -> np.ndarray:
    """
    Compute the mean cepstrum and remove the linear trend.

    Parameters
    ----------
    cepstrum : np.ndarray
        The cepstrum data.
    quefrency : np.ndarray, optional
        The quefrency values. If None, it is assumed to be the same length as the cepstrum.

    Returns
    -------
    np.ndarray
        The mean cepstrum with the linear trend removed.
    """
    logging.debug("Call Function: get_mean_cepstrum")
    if quefrency is None:
        quefrency = np.arange(cepstrum.shape[0])

    qmin = int(0.1 * len(quefrency))
    qmax = int(0.9 * len(quefrency))

    cepstrum_abs = np.abs(cepstrum)
    mean_cepstrum = np.nanmean(cepstrum_abs, axis=1)

    sub_quefrency = quefrency[qmin:qmax]
    sub_mean_cepstrum = signal.medfilt(mean_cepstrum[qmin:qmax], 5)

    poly_coefficients = np.polyfit(sub_quefrency, sub_mean_cepstrum, deg=1)
    linear_trend = np.polyval(poly_coefficients, quefrency)

    return mean_cepstrum - linear_trend


def get_preset_parameters(species=None):    
    logging.debug("Call Function: get_preset_parameters")
    params = [
        ['abw', 2**10, 0.95, 5, 24, 26, [67, 77], [57,87],'abw'],
        ['mpbw', 2**12, 0.95, 5, 20, 26, [100, 120], [80,140],'mpbw'],
        ['minke', 2**9, 0.8, 20, 100, 117, [2.7,3.3], [2,4.],'minke'],
        #['fw', 2 ** 9, 0.75, 5, 18, 22, [10, 12], [8, 14],'fw'],
        ['fw_10', 2**9, 0.75, 5,18,22,[9.7,11.5],[8.,13.],'fw_10'],
        ['fw_15', 2**9, 0.75, 5,18,22,[14.5,17],[12.,19.5],'fw_15'],
        ['atl_bw', 2 ** 10, 0.95, 5, 16, 18, [10, 12], [8, 14], 'atl_bw'], #2004 XI => pas l ame chose sur 5L en 2018
        ['ind', 2 ** 10, 0.95, 5, 16, 18, [10, 12], [8, 14], 'ind'], #2004 XI => pas l ame chose sur 5L en 2018
    ]
    params = pd.DataFrame(params,
                          columns=['species', 'fftsize', 'overlap', 'integration', 'fmin', 'fmax', 'peak_boundaries',
                                   'valley_boundaries', 'species_id'])
    params.set_index('species', inplace=True)
    if species:
        return params.loc[species]
    return params

