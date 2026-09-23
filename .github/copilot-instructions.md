# Copilot instructions for tdfextractor

The canonical guide is [`CLAUDE.md`](../CLAUDE.md) at the repo root: commands, module
layout, public API, conventions and gotchas. Read it before non-trivial changes.

Key rules:

1. Commands: `just check` (ruff + ty + pytest), `just testf` for the fast subset
   (`-m "not slow"`). Python >= 3.12, ruff line length 100.
2. A new option needs a dataclass field in `src/tdfextractor/args.py` **and** a CLI
   flag in `src/tdfextractor/cli_args.py` with the same name and the same default;
   `from_namespace` copies by name.
3. MS2 and MGF writers are DDA-only; DIA/PRM go through `write_mzml_file` only.
4. tdfpy has broken its API across majors (2.0 centroiding, 3.0 removed
   `readPasefMsMs`). The code targets tdfpy 4 (`tdfpy>=4.0,<5`); check `uv.lock`
   before relying on a tdfpy call.
5. Do not bump `__version__`, tag, or publish; the tacular-omics overseer releases.
