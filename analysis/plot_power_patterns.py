#!/usr/bin/env python3
"""Generate plots from the four measured horn-antenna S21 CSV datasets."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


DATASETS = {
    "E-plane co-polarized": "radiationPattern_corrected_eplane_co_new.csv",
    "E-plane cross-polarized": "radiationPattern_eplane_cross_new.csv",
    "H-plane co-polarized": "radiationPattern_hplane_co_new.csv",
    "H-plane cross-polarized": "radiationPattern_hplane_cross_new.csv",
}


@dataclass
class PatternData:
    angles_deg: np.ndarray
    frequencies_hz: np.ndarray
    s21_db: np.ndarray

    @property
    def frequencies_ghz(self) -> np.ndarray:
        return self.frequencies_hz / 1e9

    @property
    def normalized_s21_db(self) -> np.ndarray:
        maxima = np.nanmax(self.s21_db, axis=0, keepdims=True)
        return self.s21_db - maxima


def load_pattern_csv(path: Path) -> PatternData:
    """Read frequency values from the first row and angles from the first column."""
    if not path.is_file():
        raise FileNotFoundError(f"Measurement CSV not found: {path}")

    raw = np.genfromtxt(path, delimiter=",", dtype=float)
    if raw.ndim != 2 or raw.shape[0] < 2 or raw.shape[1] < 2:
        raise ValueError(f"Unexpected CSV shape in {path}: {raw.shape}")

    frequencies_hz = raw[0, 1:]
    angles_deg = raw[1:, 0]
    s21_db = raw[1:, 1:]

    if frequencies_hz.size != s21_db.shape[1] or angles_deg.size != s21_db.shape[0]:
        raise ValueError(f"Inconsistent header/data dimensions in {path}")
    if not np.all(np.isfinite(frequencies_hz)) or not np.all(np.isfinite(angles_deg)):
        raise ValueError(f"Non-finite frequency or angle values in {path}")
    if not np.any(np.isfinite(s21_db)):
        raise ValueError(f"No finite S21 measurements in {path}")
    if np.any(np.diff(frequencies_hz) <= 0):
        raise ValueError(f"Frequencies are not strictly increasing in {path}")

    return PatternData(angles_deg, frequencies_hz, s21_db)


def load_all_data(data_dir: Path) -> Dict[str, PatternData]:
    """Load all datasets and check that their measurement grids match."""
    data = {
        label: load_pattern_csv(data_dir / filename)
        for label, filename in DATASETS.items()
    }
    reference = next(iter(data.values()))

    for label, current in data.items():
        if (
            current.angles_deg.shape != reference.angles_deg.shape
            or not np.allclose(current.angles_deg, reference.angles_deg, rtol=0, atol=1e-9)
        ):
            raise ValueError(f"Angle grid in {label} does not match the other datasets.")
        if (
            current.frequencies_hz.shape != reference.frequencies_hz.shape
            or not np.allclose(current.frequencies_hz, reference.frequencies_hz, rtol=0, atol=1e-3)
        ):
            raise ValueError(f"Frequency grid in {label} does not match the other datasets.")

    return data


def frequency_tag(frequency_ghz: float) -> str:
    return f"{frequency_ghz:g}".replace(".", "p") + "GHz"


def choose_frequency(frequencies_ghz: np.ndarray, requested_ghz: float) -> int:
    index = int(np.argmin(np.abs(frequencies_ghz - requested_ghz)))
    actual = frequencies_ghz[index]
    if not np.isclose(actual, requested_ghz, atol=1e-6):
        print(f"Requested {requested_ghz:g} GHz. Using nearest sample: {actual:.6f} GHz.")
    return index


def plot_polar_patterns(data: Dict[str, PatternData], index: int,
                        frequency_ghz: float, output_dir: Path) -> Path:
    fig, axes = plt.subplots(
        2, 2, figsize=(12, 10), subplot_kw={"projection": "polar"},
        constrained_layout=True,
    )
    theta = np.deg2rad(next(iter(data.values())).angles_deg)

    for ax, (label, pattern) in zip(axes.flat, data.items()):
        normalized = pattern.normalized_s21_db[:, index]
        radius = np.clip(normalized, -40, 0) + 40
        radius[~np.isfinite(normalized)] = np.nan
        ax.plot(theta, radius, linewidth=1.8)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 40)
        ax.set_rticks([0, 10, 20, 30, 40])
        ax.set_yticklabels(["-40", "-30", "-20", "-10", "0 dB"])
        ax.set_title(label, pad=18)
        ax.grid(True, alpha=0.65)

    fig.suptitle(f"Normalized Measured S21 Patterns at {frequency_ghz:.4f} GHz", fontsize=15)
    output = output_dir / f"normalized_polar_patterns_{frequency_tag(frequency_ghz)}.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_e_vs_h(data: Dict[str, PatternData], index: int,
                frequency_ghz: float, output_dir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True, constrained_layout=True)
    comparisons = [
        ("Co-polarized", "E-plane co-polarized", "H-plane co-polarized"),
        ("Cross-polarized", "E-plane cross-polarized", "H-plane cross-polarized"),
    ]

    for ax, (title, e_label, h_label) in zip(axes, comparisons):
        for label in (e_label, h_label):
            pattern = data[label]
            ax.plot(
                pattern.angles_deg,
                np.clip(pattern.normalized_s21_db[:, index], -40, 0),
                linewidth=1.8,
                label=label,
            )
        ax.set_title(title)
        ax.set_xlabel("Angle (degrees)")
        ax.set_ylabel("Normalized measured S21 (dB)")
        ax.set_xlim(0, 360)
        ax.set_xticks(np.arange(0, 361, 45))
        ax.set_ylim(-40, 0)
        ax.grid(True, linestyle=":", alpha=0.7)
        ax.legend()

    fig.suptitle(f"E-plane vs H-plane at {frequency_ghz:.4f} GHz", fontsize=14)
    output = output_dir / f"e_vs_h_pattern_comparison_{frequency_tag(frequency_ghz)}.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_heatmaps(data: Dict[str, PatternData], output_dir: Path) -> Path:
    fig, axes = plt.subplots(
        2, 2, figsize=(14, 9), constrained_layout=True, sharex=True, sharey=True
    )
    reference = next(iter(data.values()))
    frequencies = reference.frequencies_ghz
    angles = reference.angles_deg
    image = None

    for ax, (label, pattern) in zip(axes.flat, data.items()):
        heatmap = np.clip(pattern.normalized_s21_db, -40, 0)
        image = ax.imshow(
            heatmap, origin="lower", aspect="auto",
            extent=[frequencies[0], frequencies[-1], angles[0], angles[-1]],
            cmap="viridis", vmin=-40, vmax=0, interpolation="nearest",
        )
        ax.set_title(label)
        ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("Angle (degrees)")
        ax.set_xlim(1, 4)
        ax.set_ylim(0, 360)
        ax.set_xticks(np.arange(1, 4.01, 0.5))
        ax.set_yticks([0, 90, 180, 270, 360])

    if image is not None:
        colorbar = fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.92, pad=0.02)
        colorbar.set_label("Normalized measured S21 (dB; each frequency normalized to its own maximum)")

    fig.suptitle("Measured Pattern versus Angle and Frequency", fontsize=15)
    output = output_dir / "angle_frequency_heatmaps.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_peak_s21(data: Dict[str, PatternData], output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    for label, pattern in data.items():
        ax.plot(
            pattern.frequencies_ghz,
            np.nanmax(pattern.s21_db, axis=0),
            linewidth=1.8,
            label=label,
        )
    ax.set_title("Peak Measured S21 versus Frequency")
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Peak measured S21 (dB)")
    ax.set_xlim(1, 4)
    ax.grid(True, linestyle=":", alpha=0.7)
    ax.legend()

    output = output_dir / "peak_measured_s21_vs_frequency.png"
    fig.savefig(output, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output


def save_summary(data: Dict[str, PatternData], index: int,
                 frequency_ghz: float, output_dir: Path) -> Path:
    output = output_dir / f"pattern_summary_{frequency_tag(frequency_ghz)}.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "configuration", "frequency_GHz", "peak_angle_deg",
            "peak_measured_S21_dB", "minimum_normalized_S21_dB",
        ])
        for label, pattern in data.items():
            values = pattern.s21_db[:, index]
            valid = np.isfinite(values)
            values = values[valid]
            angles = pattern.angles_deg[valid]
            peak_index = int(np.argmax(values))
            peak = float(values[peak_index])
            writer.writerow([
                label,
                f"{frequency_ghz:.6f}",
                f"{angles[peak_index]:.1f}",
                f"{peak:.3f}",
                f"{np.min(values - peak):.3f}",
            ])
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate plots from the four measured horn-antenna S21 CSV datasets."
    )
    repository_root = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--data-dir", type=Path, default=repository_root / "data",
        help="Folder containing the four CSV files.",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=repository_root / "figures",
        help="Folder where plots and the summary CSV will be saved.",
    )
    parser.add_argument(
        "--frequency-ghz", type=float, default=1.6,
        help="Frequency for the polar and E-plane versus H-plane plots. Default: 1.6 GHz.",
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data = load_all_data(args.data_dir)
    reference = next(iter(data.values()))
    index = choose_frequency(reference.frequencies_ghz, args.frequency_ghz)
    selected_frequency = float(reference.frequencies_ghz[index])

    print("Data checks passed.")
    print(f"Angle samples: {reference.angles_deg.size}")
    print(f"Frequency samples: {reference.frequencies_ghz.size}")
    if reference.frequencies_ghz.size > 1:
        spacing_mhz = np.median(np.diff(reference.frequencies_ghz)) * 1000
        print(f"Frequency spacing: {spacing_mhz:.4f} MHz")
    print(f"Selected frequency: {selected_frequency:.6f} GHz")

    outputs = [
        plot_polar_patterns(data, index, selected_frequency, args.output_dir),
        plot_e_vs_h(data, index, selected_frequency, args.output_dir),
        plot_heatmaps(data, args.output_dir),
        plot_peak_s21(data, args.output_dir),
        save_summary(data, index, selected_frequency, args.output_dir),
    ]

    print("\nGenerated files:")
    for path in outputs:
        print(f"- {path}")
    print("\nNote: plots show measured S21, not absolute antenna gain or directivity.")


if __name__ == "__main__":
    main()
