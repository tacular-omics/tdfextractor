"""Tests for the CLI entry points and the --ip2 / --casanovo presets."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

from tdfextractor import mgf_extractor, ms2_extractor, mzml_extractor
from tdfextractor.args import MgfArgs, Ms2Args
from tdfextractor.cli_args import apply_preset_settings, create_mgf_parser, create_ms2_parser

_logger = logging.getLogger(__name__)


def _preset(argv: list[str]):
    parser = create_ms2_parser() if "--ip2" in argv else create_mgf_parser()
    ns = parser.parse_args(["/tmp/foo.d", *argv])
    apply_preset_settings(_logger, ns)
    return ns


def test_casanovo_keeps_explicit_min_precursor_charge() -> None:
    """Regression: --casanovo overwrote --min-precursor-charge with 2."""
    assert _preset(["--casanovo", "--min-precursor-charge", "3"]).min_precursor_charge == 3


def test_casanovo_sets_min_precursor_charge_by_default() -> None:
    ns = _preset(["--casanovo"])
    assert ns.min_precursor_charge == 2
    assert ns.top_n_peaks == 150


def test_casanovo_leaves_min_precursor_intensity_alone() -> None:
    ns = _preset(["--casanovo", "--min-precursor-intensity", "1000"])
    assert ns.min_precursor_intensity == 1000
    assert ns.min_precursor_charge == 2


def test_ip2_keeps_explicit_values() -> None:
    ns = _preset(["--ip2", "--min-precursor-charge", "1", "--top-n-peaks", "50"])
    assert ns.min_precursor_charge == 1
    assert ns.top_n_peaks == 50


@pytest.fixture
def broken_d_parent(tmp_path: Path) -> Path:
    """A directory holding two .d folders whose analysis.tdf is not a database.

    Two folders so that ``--workers 2`` takes mgf-extractor's thread-pool path.
    """
    for name in ("broken_a.d", "broken_b.d"):
        bad = tmp_path / name
        bad.mkdir()
        (bad / "analysis.tdf").write_bytes(b"not a sqlite database")
        (bad / "analysis.tdf_bin").write_bytes(b"")
    return tmp_path


@pytest.mark.parametrize("module", [ms2_extractor, mgf_extractor, mzml_extractor])
@pytest.mark.parametrize("extra", [[], ["--workers", "2"]])
def test_cli_exits_nonzero_when_a_folder_fails(
    monkeypatch, broken_d_parent: Path, module, extra: list[str]
) -> None:
    """Regression: a failed .d folder was logged and the CLI still exited 0."""
    monkeypatch.setattr(sys, "argv", ["prog", str(broken_d_parent), *extra])
    assert module.main() == 1


@pytest.mark.parametrize(
    ("writer", "args_cls"),
    [(ms2_extractor.write_ms2_file, Ms2Args), (mgf_extractor.write_mgf_file, MgfArgs)],
)
def test_writer_reraises_producer_errors(
    monkeypatch, tmp_path: Path, dda_d_folder: Path, writer, args_cls
) -> None:
    """Regression: an exception in the producer thread was swallowed and the
    writer returned normally with a truncated file."""

    def boom(*args, **kwargs):
        raise RuntimeError("producer failed")
        yield  # pragma: no cover

    module = sys.modules[writer.__module__]
    monkeypatch.setattr(module, "get_ms2_dda_content", boom)
    with pytest.raises(RuntimeError, match="producer failed"):
        writer(args_cls(analysis_dir=str(dda_d_folder), output_file=str(tmp_path / "out")))
