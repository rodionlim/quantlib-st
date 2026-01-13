APP_NAME := quantlib
ENTRY := quantlib_launcher.py
SPEC := quantlib.spec
DIST := dist
PYINSTALLER_OPTS := --clean --noconfirm
PYINSTALLER_OPTS_SPEC := --clean --noconfirm

PYTHON ?= python3
VERSION := $(shell $(PYTHON) scripts/get_version.py 2>/dev/null)
TARBALL_NAME := $(APP_NAME)-$(VERSION).tar.gz
TARBALL := $(DIST)/$(TARBALL_NAME)

# Default Linux build image; manual release workflow will override this to
# ghcr.io/astral-sh/uv:python3.12-alpine
LINUX_BUILD_IMAGE ?= python:3.12-slim

PYPI_DIST := dist-pypi
# In CI, set DOCKER_IMAGE=ghcr.io/<owner>/<repo>
# Default to GitHub Container Registry (ghcr.io). Override by setting DOCKER_IMAGE.
DOCKER_IMAGE ?= ghcr.io/rodionlim/quantlib-st

.PHONY: help build build-local build-linux build-windows clean distclean test ensure-venv ensure-activate version publish-pypi publish-docker

help:
	@echo "Makefile targets:"
	@echo "  make build-local     # Build locally (Linux/macOS native)"
	@echo "  make build-linux     # Build a Linux binary using Docker (recommended on non-Linux hosts)"
	@echo "  make build-windows   # Guidance: Windows build via CI or Windows host"
	@echo "  make clean           # remove pyinstaller build artifacts"
	@echo "  make distclean       # remove dist and build artifacts"
	@echo "  make ensure-venv     # create/sync .venv if missing"
	@echo "  make ensure-activate # print instructions to activate .venv and exit with error if not activated"
	@echo "  make test            # run tests using pytest"
	@echo "  make version         # print version from setup.py"
	@echo "  make publish         # build & publish to PyPI and Docker"
	@echo "  make publish-pypi    # build & upload sdist/wheel to PyPI (needs PYPI_TOKEN)"
	@echo "  make publish-docker  # build & push docker image (needs docker login)"

# Default build — attempts local build
build: build-local

version:
	@if [ -z "$(VERSION)" ]; then echo "ERROR: could not determine version"; exit 1; fi
	@echo $(VERSION)

# Ensure .venv exists (try uv venv + uv sync, fallback to python -m venv)
ensure-venv:
	@if [ ! -d .venv ]; then \
		echo ".venv not found — attempting to create using 'uv'..."; \
		if command -v uv >/dev/null 2>&1; then \
			echo "running: uv venv"; \
			uv venv || (echo "uv failed, falling back to python -m venv .venv" && $(PYTHON) -m venv .venv); \
			if [ -f pyproject.toml ]; then echo "running: uv sync"; uv sync; fi; \
		else \
			echo "uv not found, creating venv with python -m venv .venv"; \
			$(PYTHON) -m venv .venv; \
		fi; \
	else \
		echo ".venv exists"; \
	fi

# Print activation instructions and exit with an error (do not attempt to activate).
# In CI (e.g., GITHUB_ACTIONS) we prefer running the venv without activating the shell,
# so detect CI and don't fail the run. Also tolerate an existing .venv that isn't activated.
ensure-activate:
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		echo "Virtual environment is active: $$VIRTUAL_ENV"; \
		exit 0; \
	elif [ -n "$$CI" ] || [ -n "$$GITHUB_ACTIONS" ]; then \
		echo "CI environment detected; using .venv/bin/python directly"; \
		exit 0; \
	elif [ -f .venv/bin/activate ]; then \
		echo "Virtual environment exists but is not activated. Continuing without activating (use 'source .venv/bin/activate' locally to activate)."; \
		exit 0; \
	else \
		echo "ERROR: virtual environment not activated."; \
		echo "To activate, run in your shell:"; \
		echo "  source .venv/bin/activate"; \
		echo "or on Windows (PowerShell):"; \
		echo "  .venv\\Scripts\\Activate.ps1"; \
		exit 1; \
	fi

build-local: ensure-venv ensure-activate
	@echo "Building locally using PyInstaller..."
	@. .venv/bin/activate >/dev/null 2>&1 || true
	@python -m pip install --upgrade pip pyinstaller >/dev/null
	# Install the package into the venv so PyInstaller can discover imports from src/
	@python -m pip install -e . >/dev/null
	@if [ -f $(SPEC) ]; then \
		pyinstaller $(PYINSTALLER_OPTS_SPEC) $(SPEC); \
	else \
		pyinstaller $(PYINSTALLER_OPTS) --name $(APP_NAME) $(ENTRY); \
	fi
	@echo "Creating tarball $(TARBALL)..."
	@tar -czf $(TARBALL) -C $(DIST) $(APP_NAME)

# Build a Linux executable using an official Python Docker image. This is the
# recommended approach when your host is non-Linux but you want a Linux binary.
build-linux:
	@echo "Building Linux binary inside Docker (requires Docker installed)..."
	@docker run --rm -v "$(PWD)":/src -w /src $(LINUX_BUILD_IMAGE) sh -lc "\
		if command -v apk >/dev/null 2>&1; then apk add --no-cache gcc musl-dev python3-dev; fi; \
		if command -v uv >/dev/null 2>&1; then uv pip install --system pyinstaller; else python -m pip install --upgrade pip pyinstaller; fi; \
		# Install the project so imports under src/ are discoverable by PyInstaller
		python -m pip install .; \
		if [ -f $(SPEC) ]; then pyinstaller $(PYINSTALLER_OPTS_SPEC) $(SPEC); else pyinstaller $(PYINSTALLER_OPTS) --name $(APP_NAME) $(ENTRY); fi; \
		echo \"Creating tarball $(TARBALL)...\"; \
		tar -czf $(TARBALL) -C dist quantlib \
	\"

# Windows builds are not supported by this Makefile. Use a Windows host or CI.
build-windows:
	@echo "Windows builds should be produced on Windows or via CI (GitHub Actions)."
	@exit 1

clean:
	@rm -rf build dist __pycache__

distclean: clean
	@rm -rf $(DIST) *.spec

test: ensure-venv ensure-activate
	@echo "Running tests..."
	@if command -v uv >/dev/null 2>&1 && [ -f .venv/pyvenv.cfg ]; then \
		echo "Using uv-managed venv; assuming dependencies are installed via 'uv sync'"; \
		.venv/bin/python -m pytest -q; \
	elif [ -f .venv/bin/python ]; then \
		.venv/bin/python -m pip install --upgrade pip pytest >/dev/null && \
		.venv/bin/python -m pip install -e . >/dev/null && \
		.venv/bin/python -m pytest -q; \
	else \
		pytest -q; \
	fi

publish: publish-pypi publish-docker

publish-pypi:
	@if [ -z "$(PYPI_TOKEN)" ]; then echo "ERROR: PYPI_TOKEN is required"; exit 1; fi
	@if [ -z "$(VERSION)" ]; then echo "ERROR: could not determine version"; exit 1; fi
	@echo "Building sdist/wheel for version $(VERSION)..."
	@$(PYTHON) -m pip install --upgrade pip build twine >/dev/null
	@rm -rf $(PYPI_DIST)
	@$(PYTHON) -m build --outdir $(PYPI_DIST)
	@echo "Uploading to PyPI..."
	@TWINE_USERNAME=__token__ TWINE_PASSWORD=$(PYPI_TOKEN) $(PYTHON) -m twine upload $(PYPI_DIST)/*

publish-docker:
	@if [ -z "$(VERSION)" ]; then echo "ERROR: could not determine version"; exit 1; fi
	@if ! echo "$(DOCKER_IMAGE)" | grep -Eq '/'; then \
        echo "ERROR: DOCKER_IMAGE must be namespaced (e.g. ghcr.io/username/$(APP_NAME))"; exit 1; \
    fi
	@echo "Building docker image $(DOCKER_IMAGE):$(VERSION)"
	@docker build --build-arg VERSION=$(VERSION) -t $(DOCKER_IMAGE):$(VERSION) .
	@echo "Pushing to registry $(DOCKER_IMAGE) (ensure you are logged in: 'echo $${GHCR_PAT} | docker login ghcr.io -u <user> --password-stdin')"
	@docker push $(DOCKER_IMAGE):$(VERSION)
	@echo "Tagging image as latest and pushing"
	@docker tag $(DOCKER_IMAGE):$(VERSION) $(DOCKER_IMAGE):latest
	@docker push $(DOCKER_IMAGE):latest
