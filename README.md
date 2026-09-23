# tdfextractor

[![Python Package](https://github.com/tacular-omics/tdfextractor/actions/workflows/python-package.yml/badge.svg)](https://github.com/tacular-omics/tdfextractor/actions/workflows/python-package.yml)
[![PyPI](https://img.shields.io/pypi/v/tdfextractor)](https://pypi.org/project/tdfextractor/)
[![License](https://img.shields.io/github/license/tacular-omics/tdfextractor)](https://github.com/tacular-omics/tdfextractor/blob/main/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/tdfextractor)](https://pypi.org/project/tdfextractor/)

Converts Bruker timsTOF `.d` folders into MS2, MGF, or mzML files that downstream search engines and de novo sequencing tools already know how to read. It's built on [tdfpy](https://github.com/tacular-omics/tdfpy) for the raw PASEF data access, so you get filtering, precursor handling, and batch processing without writing any Bruker SDK code yourself.

## Highlights

- **Three output formats** — MS2 (MS-GF+, Comet), MGF (general-purpose, Casanovo-tuned), and mzML (includes MS1 and MS2 PASEF spectra with configurable compression/encoding).
- **Built-in presets** — `--ip2` for IP2 search engine defaults, `--casanovo` for de novo sequencing defaults.
- **Extensive spectrum and precursor filtering** — intensity, m/z, charge, retention time, CCS, and neutral mass thresholds, plus optional precursor peak removal and top-N peak trimming.
- **Batch processing** — point at a directory of `.d` folders and process them with multiple `--workers`.
- **mzML centroiding and compression controls** — choose noise filters, m/z/ion-mobility tolerances, and per-array compression (`zlib`, `zstd`, `numpress-*`).
- **Also usable as a library** — `write_ms2_file`, `write_mgf_file`, and `write_mzml_file` take the same typed argument dataclasses as the CLI.

## Installation

```bash
pip install tdfextractor
```

## Usage

tdfextractor provides three command-line tools for extracting spectra:

### MS2 Extraction
Extract MS2 format files (compatible with MS-GF+, Comet, etc.):

```bash
ms2-extractor /path/to/sample.d

# shorthand
ms2-ex 
ms2-ex /path/to/sample.d --output custom_output.ms2 --min-intensity 100 --min-charge 2
ms2-ex /path/to/directory_with_multiple_d_folders --output /path/to/output_directory
```

### MGF Extraction  
Extract MGF format files

```bash
mgf-extractor /path/to/sample.d

#shorthand
mgf-ex
mgf-ex /path/to/sample.d --casanovo  # Optimized for Casanovo de novo sequencing
mgf-ex /path/to/directory_with_multiple_d_folders --output /path/to/output_directory
```

### mzML Extraction
Extract mzML format files (includes both MS1 and MS2 PASEF spectra):

```bash
mzml-extractor /path/to/sample.d

# shorthand
mzml-ex /path/to/sample.d
mzml-ex /path/to/sample.d --no-ms1  # MS2 spectra only
mzml-ex /path/to/sample.d --mz-compression zstd --intensity-encoding 32
mzml-ex /path/to/directory_with_multiple_d_folders --output /path/to/output_directory
```

## Output Options

Both extractors support flexible output options:

1. **No output specified**: Files are created within each .D folder with auto-generated names
2. **Specific file path**: Use `-o filename.ms2` or `-o filename.mgf` for single .D folder processing
3. **Output directory**: Use `-o /path/to/output_dir` for batch processing multiple .D folders
4. **Overwrite protection**: Use `--overwrite` to replace existing output files

### Batch Processing

When processing multiple .D folders, the extractors will:
- Automatically find all .D folders in the specified directory
- Create output files with names matching the .D folder names
- Skip existing files unless `--overwrite` is specified
- Create the output directory if it doesn't exist

## Command Line Arguments

Both MS2 and MGF extractors share the same arguments, with only a few format-specific options:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `analysis_dir` | str | - | Path to the .D analysis directory or directory containing .D folders |
| `-o, --output` | str | `<analysis_dir_name>.<ext>` | Output file path or directory |
| `--remove-precursor` | flag | False | Remove precursor peaks from MS/MS spectra |
| `--precursor-peak-width` | float | 2.0 | Width around precursor m/z to remove (Da) |
| `--batch-size` | int | 100 | Batch size for processing spectra |
| `--top-n-peaks` | int | None | Keep only top N most intense peaks per spectrum |
| `--min-spectra-intensity` | float | None | Minimum intensity threshold for MS/MS peaks (absolute or 0.0-1.0 for percentage) |
| `--max-spectra-intensity` | float | None | Maximum intensity threshold for MS/MS peaks (absolute or 0.0-1.0 for percentage) |
| `--min-spectra-mz` | float | None | Minimum m/z filter for MS/MS peaks |
| `--max-spectra-mz` | float | None | Maximum m/z filter for MS/MS peaks |
| `--min-precursor-intensity` | float | None | Minimum precursor intensity filter |
| `--max-precursor-intensity` | float | None | Maximum precursor intensity filter |
| `--min-precursor-charge` | int | None | Minimum precursor charge state filter |
| `--max-precursor-charge` | int | None | Maximum precursor charge state filter |
| `--min-precursor-mz` | float | None | Minimum precursor m/z filter |
| `--max-precursor-mz` | float | None | Maximum precursor m/z filter |
| `--min-precursor-rt` | float | None | Minimum precursor retention time filter (seconds) |
| `--max-precursor-rt` | float | None | Maximum precursor retention time filter (seconds) |
| `--min-precursor-ccs` | float | None | Minimum precursor CCS filter |
| `--max-precursor-ccs` | float | None | Maximum precursor CCS filter |
| `--min-precursor-neutral-mass` | float | None | Minimum precursor neutral mass filter |
| `--max-precursor-neutral-mass` | float | None | Maximum precursor neutral mass filter |
| `--mz-precision` | int | 5 | Number of decimal places for m/z values |
| `--intensity-precision` | int | 0 | Number of decimal places for intensity values |
| `--keep-empty-spectra` | flag | False | Write empty spectra to output file |
| `--overwrite` | flag | False | Overwrite existing output files |
| `--workers` | int | 1 | Number of worker threads for processing multiple .d folders |
| `-v, --verbose` | flag | False | Enable verbose logging |

### Format-Specific Arguments

**MS2 Extractor Only:**
- `--ip2`: Use IP2 preset settings (sets min charge to 2, top 500 peaks)

**MGF Extractor Only:**
- `--casanovo`: Use Casanovo preset settings (enables precursor removal, top-150 peaks, min intensity 0.01, m/z range 50-2500, min charge 2)

**mzML Extractor Only:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--no-ms1` | flag | False | Skip MS1 spectra; write only MS2 PASEF spectra |
| `--mz-compression` | str | `zlib` | Compression for m/z arrays (`none`, `zlib`, `zstd`, `numpress-linear`, `numpress-slof`, `numpress-pic`) |
| `--intensity-compression` | str | `zlib` | Compression for intensity arrays |
| `--mobility-compression` | str | `zlib` | Compression for per-peak ion mobility arrays (MS1) |
| `--mz-encoding` | int | `64` | Bit width for m/z values (`32` or `64`) |
| `--intensity-encoding` | int | `32` | Bit width for intensity values (`32` or `64`) |
| `--centroid-noise-filter` | str | `none` | Noise filter before centroiding (`none`, `mad`, `percentile`, `histogram`, `baseline`, `iterative_median`) |
| `--centroid-mz-tolerance` | float | `8.0` | m/z tolerance for centroiding |
| `--centroid-mz-tolerance-type` | str | `ppm` | Unit for m/z tolerance (`ppm` or `da`) |
| `--centroid-im-tolerance` | float | `0.05` | Ion mobility tolerance for centroiding |
| `--centroid-im-tolerance-type` | str | `relative` | Unit for ion mobility tolerance (`relative` or `absolute`) |
| `--centroid-min-peaks` | int | `5` | Minimum raw peaks required to form a centroided MS1 peak |
| `--centroid-ms2-min-peaks` | int | `1` | Minimum raw peaks required to form a centroided peak in DIA windows / PRM transitions |

### Performance Options

The `--workers` argument allows parallel processing of multiple .d folders:

```bash
# Process multiple .d folders with 4 worker threads
mgf-ex /path/to/directory_with_multiple_d_folders --workers 4
```

**Note**: Workers only affect processing when multiple .d folders are being processed simultaneously. Each worker processes one complete .d folder independently.

## Python API

Every extractor is also importable as a function, driven by the same typed argument dataclass the CLI builds internally:

```python
from tdfextractor import Ms2Args, write_ms2_file

args = Ms2Args(
    analysis_dir="/path/to/sample.d",
    output_file="sample.ms2",
    min_precursor_charge=2,
    top_n_peaks=500,
)
write_ms2_file(args)
```

`MgfArgs` and `write_mgf_file` / `MzmlArgs` and `write_mzml_file` follow the same pattern. `BaseExtractorArgs` documents the fields shared by all three.

## License

[MIT](https://github.com/tacular-omics/tdfextractor/blob/main/LICENSE)
