"""Tests for the DDA spectrum readers in :mod:`tdfextractor.utils`."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from conftest import DDA_MAX_RT

from tdfextractor.utils import _resolve_intensity_threshold, get_ms2_dda_content, get_tdf_df


class TestResolveIntensityThreshold:
    def test_fraction_is_relative_to_max(self) -> None:
        assert _resolve_intensity_threshold(0.5, np.array([10.0, 200.0])) == 100.0

    def test_int_one_is_relative(self) -> None:
        # Regression: int 1 matched neither branch and raised UnboundLocalError.
        assert _resolve_intensity_threshold(1, np.array([10.0, 200.0])) == 200.0

    def test_int_zero_is_relative(self) -> None:
        assert _resolve_intensity_threshold(0, np.array([10.0, 200.0])) == 0.0

    def test_above_one_is_absolute(self) -> None:
        assert _resolve_intensity_threshold(500, np.array([10.0, 200.0])) == 500
        assert _resolve_intensity_threshold(500.0, np.array([10.0, 200.0])) == 500.0

    def test_empty_spectrum_relative(self) -> None:
        assert _resolve_intensity_threshold(0.5, np.array([])) == 0.0


@pytest.fixture(scope="module")
def dda_merged_df(dda_d_folder: Path):
    return get_tdf_df(str(dda_d_folder), max_precursor_rt=DDA_MAX_RT).head(20)


def _spectra(dda_d_folder: Path, merged_df, **kwargs) -> list:
    return list(get_ms2_dda_content(str(dda_d_folder), merged_df, **kwargs))


@pytest.mark.slow
def test_top_n_peaks_trims_to_most_intense(dda_d_folder: Path, dda_merged_df) -> None:
    """Regression: the trimming branch was unreachable, so top_n_peaks did nothing."""
    full = _spectra(dda_d_folder, dda_merged_df)
    top = _spectra(dda_d_folder, dda_merged_df, top_n_peaks=5)
    assert any(len(s.mz_spectra) > 5 for s in full)
    for f, t in zip(full, top, strict=True):
        assert len(t.mz_spectra) == min(5, len(f.mz_spectra))
        assert t.mz_spectra == sorted(t.mz_spectra)
        assert sorted(t.intensity_spectra) == sorted(f.intensity_spectra, reverse=True)[:5][::-1]


@pytest.mark.slow
def test_top_n_peaks_zero_empties_spectra(dda_d_folder: Path, dda_merged_df) -> None:
    top = _spectra(dda_d_folder, dda_merged_df, top_n_peaks=0)
    assert all(len(s.mz_spectra) == 0 for s in top)


@pytest.mark.slow
def test_top_n_peaks_negative_raises(dda_d_folder: Path, dda_merged_df) -> None:
    with pytest.raises(ValueError, match="top_n_peaks"):
        _spectra(dda_d_folder, dda_merged_df, top_n_peaks=-1)


@pytest.mark.slow
def test_integer_min_spectra_intensity(dda_d_folder: Path, dda_merged_df) -> None:
    """Regression: an int min_spectra_intensity of 1 raised UnboundLocalError."""
    spectra = _spectra(dda_d_folder, dda_merged_df, min_spectra_intensity=1)
    # 1 is a fraction (100 % of the base peak), so only base-peak intensities survive.
    assert all(len(set(s.intensity_spectra)) <= 1 for s in spectra)
    absolute = _spectra(dda_d_folder, dda_merged_df, min_spectra_intensity=100)
    assert all(min(s.intensity_spectra, default=100) >= 100 for s in absolute)
