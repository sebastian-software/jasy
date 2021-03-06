#!/usr/bin/env bash

# Checks PEP8 compliance for all Python files (style checks)
pep8 --ignore E203,E302,E303,E402 --max-line-length 1000 jasy

# Import checks etc. (logical checks)
pyflakes jasy
