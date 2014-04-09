#!/usr/bin/env bash

# Checks PEP8 compliance for all Python files (style checks)
autopep8 -aa --in-place --ignore E303,E203 --max-line-length 1000 `find jasy -name "*.py"`
