# ICI_Detector_WAV

## WAV version of the ICI detector developed by [Richard Dréo](https://github.com/richardDreo/ICI_detector_demo).

This tool is designed for detecting baleen whale Inter-Click Intervals (ICI) in underwater acoustic data using WAV audiofiles. It is specifically optimized for whales emitting stereotyped songs with regular intervals, such as Fin whales and Blue whales.

**Note**: Data quality affects the detector's performance. It is better to use ``float 32-bit`` data rather than `int 16-bit` data. 

## References

If you use this tool in your research, please cite the following paper:

> Dréo, R., Crawford, W. C., Barruol, G., Bazin, S., Royer, J.-Y., & Samaran, F. (2025).  
> Singing around the volcano: Detecting baleen whales in the Mozambique channel based on their song rhythms, from seismic and hydroacoustic data.  
> *The Journal of the Acoustical Society of America, 157*(5), 3418–3435.  
> [https://pubs.aip.org/jasa/article/157/5/3418/3345827/Singing-around-the-volcano-Detecting-baleen-whales](https://pubs.aip.org/jasa/article/157/5/3418/3345827/Singing-around-the-volcano-Detecting-baleen-whales)  
> DOI: [10.1121/10.0036510](https://doi.org/10.1121/10.0036510)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/richardDreo/ICI_detector.git
cd ICI_detector_WAV
```

### 2. Environment setup (using `uv`)

```bash
# Create a virtual environment
uv venv

# Activate the environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
uv pip install osekit==1.0.0
```

## Usage

Each Jupyter notebook focuses on a specific species (fin whale, Antarctic blue whale, or Madagascan pygmy blue whale) based on the characteristics of its calls. 
The notebook name indicates the species being studied and, if necessary, the ICI, for example `fw10_detection.ipynb` for fin whale calls spaced 10 seconds apart
or `mpbw_detection.ipynb` for Madagascan pygmy blue whale calls. 

## Data Requirements

**Audio Format**
* **Format**: WAV
* **Naming convention**: The detector expects the filename to include a timestamp format indicating the date and time. 
In this code, the format used is `YYYY_MM_DD_HH_MM_SS_000000.wav` (for example: `2021_07_27_00_00_00_000000.wav` for a file starting on July 27, 2021, at midnight), but you might modify it to suit your dataset. 

## Parameters

An analysis of the various parameters is currently underway.
Preliminary results indicate that the valley parameters (`valley_min` and `valley_max`) and the `window` parameter have little impact on detections.
In contrast, the frequency parameters (`f_min` and `f_max`), the peak parameters (`peak_min` and `peak_max`), and the threshold parameter do have an impact, which is consistent with the physical nature of the signals under study. 