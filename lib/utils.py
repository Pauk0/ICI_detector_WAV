from pandas import Timestamp
from datetime import datetime
from .whaleIciDetection import *

def parse_filename_datetime(filename, timestamp_pattern):
    match = timestamp_pattern.search(filename)
    if not match:
        raise ValueError(f"Filename {filename} doesn't match expected pattern")
    date_part, time_part = match.groups()

    time_elements = time_part.split('_')
    time_str = f"{time_elements[0]}:{time_elements[1]}:{time_elements[2]}"
    dt_str = f"{date_part.replace('_', '-')} {time_str}"
    return Timestamp(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"))

def process_f_range(f, peak, valley_min, valley_max, valley_step, window_size, thresholds, ref_hours, FFT_SIZE, begin_date):
    local_results = []

    print("in ! ")

    for fmin, fmax in zip(f['f_min'], f['f_max']):
        # Cepstrogramme
        t, q, c = compute_longterm_cepstro(FFT_SIZE, fmin, fmax)

        # Moyenne horaire
        c_hourly = compute_mean_cepstrum(t, c, q)
        t_hourly = pd.date_range(start=begin_date, periods=len(c_hourly), freq='h')

        for pmin, pmax in zip(peak['peak_min'], peak['peak_max']):
            v_min = [ i for i in np.arange(valley_min, pmin, valley_step) ]
            v_max = [ i for i in np.arange(pmax, valley_max, valley_step) ]
            for vmin, vmax in zip(v_min, v_max) :
                for window in window_size:
                    print(f"fmin = {fmin}, fmax = {fmax}, pmin = {pmin}, pmax = {pmax}, window = {window}, vmin = {vmin}, vmax = {vmax}")
                    p2vr = compute_p2vr(c_hourly, q, [pmin, pmax], [vmin, vmax], window)

                    # On garde les lignes présentes dans le fichier de référence
                    mask_ref = np.isin(t_hourly, ref_hours)
                    p2vr_filtered = p2vr[mask_ref]

                    for thresh in thresholds:
                        positive_detection = apply_threshold(thresh, p2vr_filtered)

                        # Formatage et Filtrage
                        local_results.append({
                            'params': f"F{fmin}_{fmax}_P{pmin}_{pmax}_V{vmin}_{vmax}_W{window}_T{thresh}",
                            'detections': positive_detection
                        })
    return local_results