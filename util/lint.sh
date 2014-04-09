#!/usr/bin/env bash

# Checks PEP8 compliance for all Python files (style checks)
pep8 --ignore E203,E302,E303 --max-line-length 1000 `find jasy -name "*.py"`

# Import checks etc. (logical checks)
pyflakes `find jasy -name "*.py"
