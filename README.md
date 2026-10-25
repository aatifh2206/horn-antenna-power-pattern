# Measuring the Power Pattern of a Horn Antenna

This project studies the measured power pattern of a horn antenna across the 1 to 4 GHz frequency range. Measurements were taken in an anechoic chamber using a horn antenna as the transmitter, a dipole antenna as the receiver, a vector network analyzer (VNA), and a motor controller for antenna rotation.

The analysis focuses on the E-plane and H-plane in co-polarized and cross-polarized configurations. The repository contains the measured CSV files and a MATLAB tool for selecting a configuration and frequency and plotting its normalized angular response.

## My Contribution

I carried out the experimental measurements and the post-processing represented by the data and code in this repository. This included working with the antenna measurement setup, collecting the VNA measurements, and analysing the measured response as a function of angle and frequency. The lab report was prepared separately by my teammates.

## Experimental Setup

- The horn antenna was connected to Port 1 of the VNA through an amplifier.
- The receiving dipole was connected to Port 2.
- Measurements were conducted in an anechoic chamber.
- A motor controller rotated the antenna setup to collect angular measurements.
- The VNA transmission measurement, S21, was recorded over angle and frequency.

The four measurement configurations are E-plane co-polarized, E-plane cross-polarized, H-plane co-polarized, and H-plane cross-polarized.

## Repository Structure

```text
horn-antenna-power-pattern/
├── data/
│   ├── radiationPattern_corrected_eplane_co_new.csv
│   ├── radiationPattern_eplane_cross_new.csv
│   ├── radiationPattern_hplane_co_new.csv
│   └── radiationPattern_hplane_cross_new.csv
├── matlab/
│   └── postprocessing.m
├── .gitignore
└── README.md
```

## Data Format

Each CSV file stores a measurement matrix:

- The first row contains the frequency samples in Hz. Its first cell is empty/NaN.
- The first column contains the angular positions in degrees.
- The remaining cells contain measured S21 values in dB.

The files in this repository contain 73 angular samples from 0 to 360 degrees in 5 degree steps, and 401 frequency samples from 1 to 4 GHz in 7.5 MHz steps. The analysis uses the frequency grid stored in the CSV files.

| File | Configuration |
|---|---|
| `radiationPattern_corrected_eplane_co_new.csv` | E-plane co-polarized |
| `radiationPattern_eplane_cross_new.csv` | E-plane cross-polarized |
| `radiationPattern_hplane_co_new.csv` | H-plane co-polarized |
| `radiationPattern_hplane_cross_new.csv` | H-plane cross-polarized |

## Running the MATLAB Analysis

1. Clone or download this repository.
2. Open MATLAB and set the Current Folder to the repository root.
3. Run the following commands in the MATLAB Command Window:

   ```matlab
   addpath(fullfile(pwd, 'matlab'));
   postprocessing
   ```

4. Use the configuration menu to select one of the four datasets.
5. Use the frequency menu to choose a frequency. The script displays the selected angular response as a polar plot.

The script locates the `data` folder relative to its own location, so the repository can be placed in another directory without editing the file paths.

## Analysis Method

For each selected configuration and frequency, the measured S21 curve is normalized by subtracting its maximum value over angle:

```text
Normalized S21 (dB) = Measured S21 (dB) - Maximum S21 (dB at that frequency)
```

This sets the strongest measured response at that frequency to 0 dB and shows other angles relative to that maximum.

## Important Notes

- These plots show normalized measured S21 in the experimental link. They are not absolute antenna-gain or directivity measurements.
- Absolute gain, efficiency, or polarization-isolation claims require appropriate calibration and measurement assumptions.
- The measurements at 0 and 360 degrees are retained as recorded. Small differences between these endpoints can arise in measured data and are not silently forced to match.
- Results depend on the antenna alignment, polarization setup, chamber conditions, instrumentation, and measurement repeatability.

## Software

The analysis tool requires MATLAB with support for `readmatrix`, `polaraxes`, and `uicontrol`. No Python packages are required to run the MATLAB analysis.
