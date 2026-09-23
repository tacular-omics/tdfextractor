# tdfextractor — Claude Code Guide

## Project overview

tdfextractor converts Bruker timsTOF `.d` folders (`analysis.tdf` + `analysis.tdf_bin`)
into MS2, MGF, or mzML files for search engines (IP2, MS-GF+, Comet) and de novo
tools (Casanovo). It ships three CLIs and a small Python API built on typed argument
dataclasses.

Place in the tacular-omics graph:

- **Upstream:** `tdfpy>=4.0,<5` (raw TDF/PASEF access, `PandasTdf`, `timsdata_connect`,
  `get_mobility_collapsed_spectrum`, `DDA`/`DIA`/`PRM` readers, `MergePeaksCentroider`
  and the `NoiseSpec` threshold classes). Also `serenipy` (the `Ms2Spectra`
  record and MS2 serialization) and `psims` (mzML writer). None of these is
  vendored.
- **Downstream:** none in the org. It is an end-user tool.

What each writer supports:

| writer | DDA (PASEF) | DIA | PRM |
|---|---|---|---|
| `write_ms2_file` / `ms2-extractor` | yes | no (`TypeError: Unknown TDF format`) | no (no `Precursors` table) |
| `write_mgf_file` / `mgf-extractor` | yes | no (no `Precursors` table) | no |
| `write_mzml_file` / `mzml-extractor` | yes | yes | yes |

## Commands

Run from the repo root (checked with the repo's own `uv.lock`, Python 3.13):

```bash
just install        # uv sync (dev group: pytest, ruff, ty, pynumpress, pyzstd)
just test           # uv run pytest tests/ -v          (77 tests, ~15 s)
just testf          # uv run pytest tests/ -v -m "not slow"   (46 fast tests, ~2 s)
just test-cov       # pytest with branch coverage (term + html + xml)
just lint           # uv run ruff check src/ tests/
just format         # ruff isort + F401 fix + ruff format on src/ tests/
just ty             # uv run ty check src/
just check          # lint + ty + test (what CI runs, plus `just install`)
just build          # uv build
```

`just publish` and `just upgrade` also exist; do not run `publish` (see Releasing).

CLI entry points (all defined in `[project.scripts]`):

```bash
uv run ms2-extractor  path/to/sample.d    # alias: ms2-ex
uv run mgf-extractor  path/to/sample.d    # alias: mgf-ex
uv run mzml-extractor path/to/sample.d    # alias: mzml-ex
uv run mzml-ex --help
```

The `analysis_dir` argument is either one folder ending in `.d`, or a directory whose
`*.d` children are all processed. `-o` is a file (single `.d` only; must end in
`.ms2` / `.mgf` / `.mzML`/`.mzml`) or an output directory (created if missing). With no
`-o`, output goes inside each `.d` folder as `<stem>.<ext>`. Existing outputs are
skipped unless `--overwrite`.

## Architecture

```
src/tdfextractor/
  __init__.py        # __version__ (hatch version source) + public re-exports
  args.py            # BaseExtractorArgs, Ms2Args, MgfArgs, MzmlArgs dataclasses,
                     #   EncodingBitWidth / CompressionName Literals, from_namespace()
  cli_args.py        # argparse parsers (create_{ms2,mgf,mzml}_parser), the --ip2 /
                     #   --casanovo presets (apply_preset_settings), log_common_args
  utils.py           # TDF -> pandas: get_tdf_df (precursor table + filters + CCS),
                     #   get_ms2_dda_content (per-precursor peaks -> Ms2Spectra),
                     #   get_ms2_dda_spectra (both in one call), scan-number maps,
                     #   get_ms2_prm_content (not wired into any CLI; TODO in code)
  ms2_extractor.py   # generate_header, write_ms2_file, main (ms2-extractor)
  mgf_extractor.py   # write_mgf_file, process_single_d_folder, main (mgf-extractor)
  mzml_extractor.py  # write_mzml_file (psims MzMLWriter) with DDA and DIA/PRM
                     #   writers, compression/encoding maps, main (mzml-extractor)
  constants.py       # PROTON_MASS
tests/
  conftest.py        # session-scoped fixtures: each writer runs once per session on
                     #   an RT-bounded slice of the bundled .d files
  data/              # 200ngHeLaPASEF_1min.d (DDA, 60 MB), example_dia.d (11 MB),
                     #   example_prm.d (29 MB), committed to git
  test_args.py, test_cli.py, test_utils.py, test_ms2_extractor.py,
  test_mgf_extractor.py, test_mzml_extractor.py
benchmark_workers.py # ad-hoc MGF --workers benchmark, not packaged; currently broken
                     #   (imports src.tdfextractor.mgf_exctractor, which does not exist)
```

Data flow for MS2/MGF (DDA only):

1. `get_tdf_df` merges `Precursors` x `Frames` x `PasefFrameMsMsInfo` (one row per
   precursor), drops rows with no `MonoisotopicMz`/`Charge`, adds `NeutralMass`,
   `IP2ScanNumber`, `OOK0` and `CCS`, and applies every `*_precursor_*` filter.
2. `get_ms2_dda_content` reads each precursor's MS2 peaks in batches (one
   `tdfpy.get_mobility_collapsed_spectrum(td, [(frame, scan_begin, scan_end)])` call
   per precursor, on the single PASEF window kept per precursor), applies the
   `*_spectra_*` filters, optional precursor-peak removal and top-N, sorts by m/z, and
   yields `serenipy.Ms2Spectra`.
3. The writer runs a producer thread (step 2) and a consumer thread (file writing)
   through a `queue.Queue(maxsize=100)`.

mzML: `write_mzml_file` reads `PandasTdf` flags and dispatches to `_write_dda`
(MS1 via `tdfpy.DDA`, MS2 via `get_ms2_dda_content`) or `_write_dia_or_prm`
(`tdfpy.DIA` windows / `tdfpy.PRM` transitions, centroided with the `centroid_*`
fields, which `_build_centroid_kwargs` turns into `centroid=MergePeaksCentroider(...)`
plus `noise=` one of `MadThreshold`/`PercentileThreshold`/`HistogramThreshold`/
`BaselineThreshold`/`IterativeMedianThreshold` or `None`). MS1 spectra carry a per-peak "mean inverse reduced ion mobility array".
`--min/--max-precursor-rt` bound the MS1 frames as well as the MS2 spectra.

## Public API

Everything in `tdfextractor.__all__`:

- **Argument dataclasses** (`args.py`): `BaseExtractorArgs` (shared I/O, filter and
  processing fields), `Ms2Args`, `MgfArgs` (add `mz_precision=5`,
  `intensity_precision=0`), `MzmlArgs` (adds `include_ms1`, per-array compression and
  encoding, `centroid_*`; `__post_init__` rejects encodings other than 32/64). Each has
  `from_namespace(argparse.Namespace)`.
- **Type aliases:** `EncodingBitWidth = Literal[32, 64]`, `CompressionName =
  Literal["none", "zlib", "zstd", "numpress-linear", "numpress-slof", "numpress-pic"]`.
- **Writers:** `write_ms2_file(args: Ms2Args) -> None`,
  `write_mgf_file(args: MgfArgs) -> None`, `write_mzml_file(args: MzmlArgs) -> None`.
- **Lower-level readers** (`utils.py`): `get_tdf_df(analysis_dir, <12 precursor
  filters>) -> pd.DataFrame`, `get_ms2_dda_content(analysis_dir, merged_df, ...) ->
  Generator[Ms2Spectra]`, `get_ms2_dda_spectra(analysis_dir, ...) ->
  Generator[Ms2Spectra]`.
- `__version__`.

## Conventions

- Python >= 3.12, `from __future__ import annotations` in new modules, PEP 604 unions.
- Ruff, line length 100, target py312. `ty` ignores `unresolved-import` because
  `psims` has no `py.typed`.
- Docstrings: Google style (`Args:`, `Returns:`, `Raises:`); many utils helpers have
  none yet.
- **Adding an option:** add the field to the right dataclass in `args.py` **and** the
  flag in `cli_args.py` with the same name (dashes -> underscores) and the **same
  default**. `from_namespace` copies by field name; a mismatched default silently
  changes behavior. CLI-only flags (`workers`, `verbose`, `overwrite`, `ip2`,
  `casanovo`) are dropped by `from_namespace`; `MzmlArgs.from_namespace` maps
  `--no-ms1` to `include_ms1=False` and `--centroid-noise-filter none` to `None`.
- `None` means "no filter" for every min/max field.
- Logging: module loggers (`logging.getLogger(__name__)`); `main()` calls
  `logging.basicConfig`. `ms2_extractor` and `mzml_extractor` force their logger to
  INFO.
- Tests: pytest, fixtures in `tests/conftest.py`. End-to-end tests carry
  `@pytest.mark.slow` and reuse the session-scoped output fixtures; keep new
  extraction tests on those fixtures and keep RT windows tight (see `DDA_MAX_RT`,
  `DIA_MAX_RT`, `PRM_MIN_RT`/`PRM_MAX_RT` in `conftest.py`) so the suite stays around 15 s.

## Gotchas

- **MS2 and MGF are DDA-only.** Both go through `get_tdf_df`, which needs the
  `Precursors` table. DIA/PRM input only works with `mzml-extractor`. The module
  docstring of `ms2_extractor.py` / `mgf_extractor.py` says "DDA and PRM"; that is
  not true.
- **CLI exit codes.** Each `main()` logs an exception per `.d` folder and continues
  with the next one, then returns 1 if any folder failed (0 otherwise).
- **`--workers` only does anything in `mgf-extractor`**, and only with more than one
  `.d` folder (one thread per folder). `ms2-extractor` and `mzml-extractor` accept the
  flag and ignore it.
- **`--min/--max-spectra-intensity` in `[0.0, 1.0]` are relative** (fraction of the
  spectrum's max peak), above 1.0 absolute, whether `int` or `float`
  (`_resolve_intensity_threshold`).
- **MS1 and MS2 centroiding differ.** `centroid_min_peaks` (default 5) applies to MS1
  frames; DIA windows and PRM transitions use `centroid_ms2_min_peaks` (default 1),
  because they span few mobility scans and 5 empties most of them. The bundled PRM
  file is so sparse that its MS1 frames centroid to nothing at 5, so the
  `mzml_prm_output` fixture sets `centroid_min_peaks=1`.
- `_write_dia_or_prm` plans every spectrum (centroiding each MS2 window once to drop
  empty ones) before writing, because psims writes `spectrumList count` up front.
- `Ms2Spectra.mass` is the singly protonated mass (M+H, `calculate_p1mass`); MGF
  `PEPMASS` is the precursor m/z.
- **tdfpy API breaks across majors.** tdfpy 2.0 replaced the flat `centroid()` kwargs
  with centroider/`NoiseSpec` objects and 3.0 removed Bruker's libtimsdata
  (`TimsData.readPasefMsMs`, `extractCentroidedSpectrumForFrame`). Since 0.4.1 the
  code targets tdfpy 4 (`pyproject.toml`: `tdfpy>=4.0,<5`; `uv.lock`: 4.0.2) and
  uses `get_mobility_collapsed_spectrum` for DDA/PRM MS2 peaks. Peak lists differ from
  0.4.0 output (e.g. the first bundled DDA spectrum went from 1782 to 4292 peaks), so
  don't compare against files written by older versions. Do not raise the cap without
  running the full test suite on the new tdfpy major.
- `tests/data/*.d` are real acquisitions (100 MB total). Don't add more; slice by RT.
- The CI workflow checks out `tdfpy`, `serenipy` and `psims` next to the repo and its
  comment mentions `[tool.uv.sources]`, but `pyproject.toml` has no such table; deps
  come from PyPI via `uv.lock`.

## Releasing

Only the tacular-omics overseer bumps versions or publishes. See `just --list`
(`build`, `publish`) and `.github/workflows/python-publish.yml` (runs on a published
GitHub release). The version source is `__version__` in
`src/tdfextractor/__init__.py` (`[tool.hatch.version]`); also update `CHANGELOG.md`
and `CITATION.cff`. Releases are archived on Zenodo (`.zenodo.json`).

## Workspace note

tdfextractor is **not** part of the tacular-omics uv workspace
(`~/Repos/tacular-omics`); it is a downstream consumer of `tdfpy` and always resolves
tdfpy from PyPI through its own `uv.lock`. `uv run` here uses this repo's own `.venv`.
A breaking tdfpy release must be tested here separately (see the workspace
CLAUDE.md).
