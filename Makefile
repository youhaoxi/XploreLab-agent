SHELL := /bin/bash
.SHELLFLAGS := -e -c

# https://mirrors.tencent.com/#/private/pypi/detail?repo_id=155&project_name=utu-agent
.PHONY: publish
publish:
	source .venv/bin/activate && python scripts/publish_pip.py .