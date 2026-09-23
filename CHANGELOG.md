# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.4.2] - 2026-09-23
### Added
- `MzmlArgs.centroid_ms2_min_peaks` / `--centroid-ms2-min-peaks` (default 1):
  minimum raw peaks per centroid for DIA windows and PRM transitions.
  `centroid_min_peaks` (default 5) now applies to MS1 frames only.

### Fixed
- `top_n_peaks` never trimmed DDA spectra (the trimming branch was unreachable),
  so `--top-n-peaks` and the top-N part of `--ip2` / `--casanovo` did nothing in
  MS2, MGF and DDA mzML output. `top_n_peaks=0` now empties spectra; negative
  values raise `ValueError`.
- `--casanovo` overwrote an explicit `--min-precursor-charge` with 2 (it checked
  `--min-precursor-intensity` instead).
- An integer `min_spectra_intensity` / `max_spectra_intensity` of 0 or 1 raised
  `UnboundLocalError`. Values in `[0, 1]` are now relative whether `int` or `float`.
- DIA/PRM mzML declared a `spectrumList count` from the unfiltered window count,
  more than the spectra actually written.
- DIA/PRM MS2 windows were centroided with `centroid_min_peaks=5`, which emptied
  most DIA windows and every transition of the bundled PRM file (0 MS2 spectra).
- The CLIs exited 0 when a `.d` folder failed; they now exit 1 if any folder failed.
- `write_ms2_file` / `write_mgf_file` swallowed exceptions raised while reading
  spectra (in the producer thread) and returned normally with a truncated file;
  they now re-raise them.

## [0.4.1]
### Added
- Archived on Zenodo (`CITATION.cff`, `.zenodo.json`).

### Changed
- `tdfpy` dependency raised from `>=1.2.0` (uncapped) to `>=4.0,<5` per the
  org's sibling pin policy. This is a major-version jump; adapted the
  affected code (see Fixed).

### Fixed
- `get_ms2_dda_content` and `get_ms2_prm_content` (the latter not yet wired
  into a CLI) used `TimsData.readPasefMsMs` and
  `TimsData.extractCentroidedSpectrumForFrame`, both removed in tdfpy 3.0.0
  along with Bruker's `libtimsdata`. Replaced with
  `tdfpy.get_mobility_collapsed_spectrum` over the same per-precursor
  frame/scan range, which reproduces the same centroided-per-precursor
  spectrum shape.
- mzML centroiding (`_build_centroid_kwargs` in `mzml_extractor`) passed
  flat `mz_tolerance`/`im_tolerance`/`noise_filter` kwargs to
  `Frame.centroid()` / `DiaWindow.centroid()`, which tdfpy 2.0.0's
  composable centroiding API replaced with `centroid: Centroider` and
  `noise: NoiseSpec` parameters. Now builds a `tdfpy.MergePeaksCentroider`
  from the existing `MzmlArgs` fields and maps `--centroid-noise-filter`
  onto the matching `tdfpy.noise` filter class.
- `MzmlArgs.centroid_mz_tolerance_type` / `centroid_im_tolerance_type` are
  now typed `Literal["ppm", "da"]` / `Literal["relative", "absolute"]`
  (matching their CLI `choices`) instead of plain `str`, which `ty` flagged
  once they were passed to `MergePeaksCentroider`.

## [0.4.0]
### Changed (BREAKING)
- `write_ms2_file`, `write_mgf_file`, and `write_mzml_file` now take a single
  dataclass argument (`Ms2Args`, `MgfArgs`, `MzmlArgs`) instead of 25-31
  individual keyword arguments. The dataclasses live in
  `tdfextractor.args` and are re-exported from the package root.
- `generate_header` in `ms2_extractor` now takes an `Ms2Args` instead of 23
  individual kwargs.
- `mz_encoding` and `intensity_encoding` are now typed
  `EncodingBitWidth = Literal[32, 64]`. Invalid values raise `ValueError`
  at `MzmlArgs` construction time instead of inside the writer.
- `mz_compression` / `intensity_compression` / `mobility_compression` are
  typed `CompressionName` (a `Literal` over the supported codec names).
- CLI defaults for `--mz-precision` / `--intensity-precision` are now `5` /
  `0` to match the dataclass defaults (previously `None`, downstream code
  treated `None` as 5/0 anyway, so behavior is unchanged for CLI users).
- mzML extractor: `--min-precursor-rt` / `--max-precursor-rt` now also bound
  the MS1 frames written to the mzML file. Previously these flags only
  filtered MS2 spectra/windows, leaving every MS1 frame in the file
  regardless of the RT window. The new behavior produces a coherent RT-
  bounded slice of the run for both DDA and DIA/PRM acquisitions.

### Added
- New `tdfextractor.args` module exposing `BaseExtractorArgs`, `Ms2Args`,
  `MgfArgs`, `MzmlArgs`, `EncodingBitWidth`, and `CompressionName`. Each
  args class has a `from_namespace(argparse.Namespace)` classmethod.
- `write_ms2_file` and `write_mgf_file` are now part of the public API
  (`from tdfextractor import ...`).
- New `tests/test_mgf_extractor.py` with full MGF format coverage.
- New `tests/test_args.py` with fast unit tests for the new dataclasses.
- New `tests/conftest.py` with session-scoped extraction fixtures so each
  acquisition type only runs through the writer once per test session.
- Added a `slow` pytest marker; run `pytest -m "not slow"` to skip the
  end-to-end extraction tests during iteration.
- `--workers` arg for parallel processing of multiple `.d` folders.

### Migration
```python
# before
write_mzml_file("/path/to/foo.d", output_file="foo.mzML", top_n_peaks=150)

# after
from tdfextractor import MzmlArgs, write_mzml_file
write_mzml_file(MzmlArgs(
    analysis_dir="/path/to/foo.d",
    output_file="foo.mzML",
    top_n_peaks=150,
))
```

## [0.3.0]
### Added
- more args
- mgf-ex & ms2-ex command shorthand
- fixed mgf pepmass

## [0.2.0]
### Added
- mgf file
- cli
- more args
- readme
- updated ms2 args
- rm linting action
- formatted with black

## [0.1.3]
### Added
- switched to serenipy as the backend for ms2 file creation
- removed string templates for ddams2spectra and ddapeakline
- get_contents now returns ms2_spectra, rather than strings
- added tests
- using context manager for timsdata

## [0.1.4]
### Added
- batch process msms spectra
- updated serenipy to 0.2.6

## [0.1.5]
### Added
- added iso width and mz
- converted intensity values to ints
- added min_intensity option
- added tqdm support
- improved logging/readability
- changed constants.MS2_VERSION to be extractor version

## [0.1.6]
### Added
- updated to tdfpy==0.1.6 

## [0.1.7]
### Added
- fixed requirements

## [0.1.7]
### Changed
- src based
- tdfpy==0.1.7
- Ms2 header
- Merged dataframes instead of keeping dicts
### Added
- workflows: pylint, pytest, pypi
- PRM workflow to ms2 extractor
- More I lines 
