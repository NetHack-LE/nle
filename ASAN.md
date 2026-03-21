# Address Sanitizer (ASAN) Guide

This project supports Address Sanitizer (ASAN) to help detect memory corruption,
use-after-free, and buffer overflows in the C/C++ NetHack engine and its Python
extensions.

## Enabling ASAN

ASAN is integrated into the CMake build system and can be enabled by editing
`pyproject.toml`.

### Current Configuration

```toml
[tool.scikit-build]
cmake.build-type = "Release"
cmake.args = ["-DHACKDIR=nle/nethackdir", "-DPYTHON_PACKAGE_NAME=nle"]
```

To enable ASAN, add the cmake argument `-DENABLE_ASAN=On` and switch
`cmake.build-type` to `Debug`.

## Running Tests with ASAN

Because the Python interpreter itself is not built with ASAN, you must preload
the ASAN runtime library when running tests.

```bash
LD_PRELOAD=$(gcc -print-file-name=libasan.so):$(gcc -print-file-name=libstdc++.so) \
ASAN_OPTIONS=detect_leaks=0 \
uv run pytest
```

_Note: Preloading `libstdc++.so` may be necessary on some platforms (like
aarch64 Linux) to avoid crashes when C++ exceptions are thrown._

### Why `detect_leaks=0`?

We disable the LeakSanitizer (`detect_leaks=0`) for several reasons:

1. Python Shutdown: CPython does not free all memory at exit (e.g., global
   singletons, interned strings). This is intentional for performance but is
   flagged as a "leak" by ASAN.
2. Pytest State: `pytest` keeps tracebacks, local variables, and fixture data in
   memory until the end of the session to generate reports.
3. Standard Interpreter: Since we are running a sanitized C extension inside a
   non-sanitized Python interpreter, the leak detector cannot accurately track
   the ownership boundary between the two.

Disabling leak detection still allows ASAN to catch critical memory corruption
errors (Buffer Overflows, Use-After-Free, etc.) as they happen.

## Other Sanitizers

The build system also supports:

- Thread Sanitizer (TSAN): Use `-DENABLE_TSAN=ON`.
- Undefined Behavior Sanitizer (UBSAN): Use `-DENABLE_UBSAN=ON`.

To use these, update `pyproject.toml` accordingly and preload the corresponding
library (e.g., `libtsan.so`).
