#!/usr/bin/env bash

# Automatically applies PEP8 compliance for all Python files
autopep8 -aaa --in-place --ignore E203,E302,E303 --max-line-length 1000 `find jasy -name "*.py"`
