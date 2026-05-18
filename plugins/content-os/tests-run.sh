#!/usr/bin/env bash
# Run Content-OS test suite
# Tests are at /usr/local/lib/hermes-agent/plugins/content-os-tests/
set -e
cd /usr/local/lib/hermes-agent/plugins/content-os-tests
python3 -m pytest -v -o "addopts=" "$@"
