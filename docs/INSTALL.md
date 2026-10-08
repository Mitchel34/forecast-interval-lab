# Offline installation

A fresh offline installation passed on CPython 3.14.7. All five installed module
files match the reviewed source byte for byte. All 31 original behavior tests ran
outside the source directory and imported the package from the new virtual
environment. The installed console demo and strict JSON fixture produced identical
output, with hand-checked intervals and scores. Evaluation entry points were
guarded against execution during the install checks; no comparison was rerun.

The package was built with an existing CPython 3.11.13 toolchain: pip 25.1.1,
setuptools 80.9.0 and wheel 0.45.1. Runtime verification used CPython 3.14.7.
Python 3.11 is the declared minimum, not a verified runtime compatibility claim.
The runtime imports only standard-library modules and declares no dependencies.

One wheel was built and installed with package indexes, dependency downloads,
build isolation and caches disabled. Build staging contained exactly the five
modules, `pyproject.toml` and `README.md`; user build configuration was disabled
and system distutils configuration was checked absent. The fresh environment
used the interpreter's bundled pip. No package was downloaded or published.

See the [sanitized installation record](INSTALLATION.json) for source, installed
module and test hashes. The verified wheel SHA-256 is
`1580becff182236915bc6f7f30f44a67861976b54cc6d0079c431d8e4fb03ba5`.
The private wheel and logs are not shipped. This is an observed artifact hash,
not a claim that rebuilding produces an identical wheel: archive timestamps and
installation paths can differ. Later documentation-only status updates are not
part of the build inputs; the verified README, packaging and module bytes remain
unchanged.

## Reproduce in an existing local toolchain

From the source directory, with setuptools and wheel already available:

```sh
PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 python3 -m pip wheel --no-deps --no-build-isolation --wheel-dir DIST_DIRECTORY .
python3 -m venv ENV_DIRECTORY
PIP_NO_INDEX=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 ENV_DIRECTORY/bin/python -m pip install --no-index --no-deps WHEEL_FILE
```

Substitute your own output paths and the generated wheel filename. Then run
`ENV_DIRECTORY/bin/forecast-interval-lab demo` from outside the source directory.
These concise commands describe the offline build/install path; the recorded
managed verification additionally isolated build configuration, bounded resources,
checked wheel contents/RECORD and copied the exact tests outside the source tree.
If the local build tools are absent, these offline commands fail rather than fetch
them. The source demo in the README needs no packaging toolchain.

Observed child CPU was 3.491423 seconds and active execution wall time was
4.461842 seconds. CPU excludes supervisor and receipt work. Staging used
13,864,960 allocated bytes. Availability checks preceded each subprocess; this
light packaging stage did not acquire a heavy-work lease and did not provide
atomic exclusion against another owner's later work. The watchdog and process
resource checks are operational bounds, not hard process-tree or memory limits.
Normal synchronous tool returns were observed; no independent descendant census
was performed.
