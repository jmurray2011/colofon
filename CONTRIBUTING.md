# Contributing to Colofon

Thank you for helping improve Colofon. Bug reports, documentation corrections, new
tests, and focused feature proposals are welcome.

## Before opening a change

- Search the existing issues first.
- Keep shared engine behavior brand-neutral. Public examples must use fictional names,
  assets, and content and must identify themselves as fictional and AI-generated.
- Do not submit private customer, employer, infrastructure, domain, or credential data.
- Discuss large template or public-API changes in an issue before implementing them.

## Development setup

Install the host dependencies listed in the README, then install the Python libraries:

```sh
python3 -m pip install -r tools/requirements.txt
```

To work on optional fillable forms, deliberately install the AGPL-licensed extra:

```sh
python3 -m pip install -r tools/requirements-form.txt
```

The static check script also expects Ruff, ShellCheck, actionlint, and Go 1.25 or later.
CI installs pinned versions; local equivalents are acceptable for development.

## Required checks

Run targeted checks while working, then run the full suite before opening a pull request:

```sh
./tools/check.sh
python3 -m unittest discover -s tests -v
go test ./...
./build.sh
./build.sh --with-forms  # only when the optional form extra is installed
docker build --check .
docker build -t colofon:local .
docker run --rm colofon:local test
docker build --target forms -t colofon-form:local .
docker run --rm colofon-form:local test
```

The document gate must continue to compile with `--pdf-standard ua-1` without warnings,
pass veraPDF's PDF/UA-1 validation, and contain no U+200B zero-width spaces. Fillable
forms are the documented exception: their post-compile widget layer is reported but is
not currently gate-verified as PDF/UA-1.

Generated `build/`, `.factory-build/`, cache, and local environment files do not belong
in commits. Preserve license files for vendored packages and fonts.

## Pull requests

Keep changes narrowly scoped and explain observable behavior, tests, and compatibility
impact. Update the README, examples, and `CHANGELOG.md` when users would notice the
change. Release preparation follows [RELEASING.md](RELEASING.md).
