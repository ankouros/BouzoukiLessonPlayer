PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else command -v python3; fi)

APP_MAIN := main.py
PY_DIRS := core ui metronome
PY_FILES := $(shell find $(PY_DIRS) -name '*.py') $(APP_MAIN)

.PHONY: help run docs-check code-check lint test check build-linux package-linux build-windows package-windows

help:
	@echo "Using PYTHON=$(PYTHON)"
	@echo "Available targets:"
	@echo "  run            - Run the Bouzouki Lesson Player GUI"
	@echo "  docs-check     - Verify key documentation files exist"
	@echo "  code-check     - Basic Python syntax checks (py_compile)"
	@echo "  lint           - Run flake8 if available"
	@echo "  test           - Run tests with pytest if tests/ exists"
	@echo "  smoke-check    - Simple GUI smoke test (start + close app)"
	@echo "  deps-review    - Show outdated Python dependencies (best-effort)"
	@echo "  check          - Run docs-check, code-check, lint, and test"
	@echo "  build-linux    - Build a standalone Linux executable with PyInstaller"
	@echo "  package-linux  - Package the Linux build into a zip archive"
	@echo "  build-windows  - (On Windows) Build a standalone EXE with PyInstaller"
	@echo "  package-windows- (On Windows) Package the Windows build into a zip archive"

run:
	@echo "[run] Starting Bouzouki Lesson Player with $(PYTHON)..."
	$(PYTHON) $(APP_MAIN)

smoke-check:
	@echo "[smoke-check] Running GUI smoke test with $(PYTHON)..."
	$(PYTHON) scripts/smoke_check.py

docs-check:
	@echo "[docs-check] Verifying documentation files..."
	@test -f README.md || (echo "Missing README.md" && exit 1)
	@test -f AGENTS.md || (echo "Missing AGENTS.md" && exit 1)
	@test -f ROADMAP.md || (echo "Missing ROADMAP.md" && exit 1)
	@test -f OPEN-ISSUES.mg || (echo "Missing OPEN-ISSUES.mg" && exit 1)
	@test -f REVIEW.md || (echo "Missing REVIEW.md" && exit 1)
	@test -f CONTRACTS.md || (echo "Missing CONTRACTS.md" && exit 1)
	@test -d specs || (echo "Missing specs/ directory" && exit 1)
	@echo "[docs-check] OK"

code-check:
	@echo "[code-check] Running python -m py_compile on source files with $(PYTHON)..."
	$(PYTHON) -m py_compile $(PY_FILES)
	@echo "[code-check] OK"

deps-review:
	@echo "[deps-review] Listing outdated packages for the active interpreter..."
	@echo "  (Run inside .venv for project-specific results.)"
	@$(PYTHON) -m pip list --outdated || echo 'pip list --outdated failed; ensure pip is installed and you have network access.'

lint:
	@echo "[lint] Running flake8 if available..."
	@command -v flake8 >/dev/null 2>&1 \
		&& flake8 $(PY_DIRS) $(APP_MAIN) \
		|| echo "flake8 not installed; skipping lint."

test:
	@echo "[test] Running tests if tests/ exists with $(PYTHON)..."
	@if [ -d tests ]; then \
		$(PYTHON) -m pytest; \
	else \
		echo "No tests directory; skipping tests."; \
	fi

check: docs-check code-check lint test
	@echo "[check] All checks completed."

# --- Build and packaging ---

build-linux:
	@echo "[build-linux] Building standalone executable with PyInstaller..."
	@which pyinstaller >/dev/null 2>&1 || { echo "pyinstaller not found; install it inside .venv (pip install pyinstaller)."; exit 1; }
	pyinstaller --noconfirm --clean \
		--name BouzoukiLessonPlayer \
		--onefile \
		--windowed \
		$(APP_MAIN)
	@echo "[build-linux] Build complete. See dist/BouzoukiLessonPlayer."

package-linux: build-linux
	@echo "[package-linux] Creating zip package for Linux build..."
	@mkdir -p dist
	@cd dist && zip -r BouzoukiLessonPlayer-linux.zip BouzoukiLessonPlayer || { echo "Zip creation failed"; exit 1; }
	@echo "[package-linux] Package created: dist/BouzoukiLessonPlayer-linux.zip"

# On Windows, run these targets in PowerShell or cmd with pyinstaller installed
build-windows:
	@echo "[build-windows] Building Windows executable with PyInstaller..."
	@where pyinstaller >NUL 2>&1 || (echo pyinstaller not found. Install with "pip install pyinstaller" inside .venv. && exit 1)
	pyinstaller --noconfirm --clean \
		--name BouzoukiLessonPlayer \
		--onefile \
		--windowed \
		$(APP_MAIN)
	@echo "[build-windows] Build complete. See dist\\BouzoukiLessonPlayer.exe."

package-windows: build-windows
	@echo "[package-windows] Creating zip package for Windows build..."
	@if not exist dist (echo dist directory not found & exit 1)
	@cd dist && powershell -Command "Compress-Archive -Force BouzoukiLessonPlayer.exe BouzoukiLessonPlayer-windows.zip"
	@echo "[package-windows] Package created: dist\BouzoukiLessonPlayer-windows.zip"
