# ML_related_tools env - managed with uv (https://docs.astral.sh/uv/)
# Python is pinned in .python-version (3.14.7). Deps in pyproject.toml, locked in uv.lock.
#
# Requires: uv on PATH, and GNU make run through a POSIX shell (git-bash) for `clean`.
# Every other target is a plain `uv` call and works from any shell.

.DEFAULT_GOAL := help
.PHONY: help install sync upgrade lock export run python marimo notebook check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Create .venv and install the locked dependency set
	uv sync

sync: install ## Alias for install

upgrade: ## Bump every dependency to the newest allowed version, then re-sync
	uv lock --upgrade
	uv sync
	uv export --no-hashes --no-emit-project -o requirements.txt

lock: ## Refresh uv.lock from pyproject.toml without upgrading pins
	uv lock

export: ## Write a pip-compatible requirements.txt from the lock file
	uv export --no-hashes --no-emit-project -o requirements.txt

run: python ## Alias for `python`

python: ## Open a Python REPL inside the env
	uv run python

marimo: ## Launch the marimo notebook editor
	uv run marimo edit

check: ## Import every top-level library and print versions
	uv run python -c "import sys, torch, polars, langgraph, marimo, numpy; \
import importlib.metadata as m; \
print('python ', sys.version.split()[0]); \
print('torch  ', torch.__version__, '| cuda', torch.cuda.is_available()); \
print('polars ', polars.__version__); \
print('numpy  ', numpy.__version__); \
print('langgraph', m.version('langgraph')); \
print('marimo ', m.version('marimo'))"

clean: ## Remove the virtual environment
	rm -rf .venv
