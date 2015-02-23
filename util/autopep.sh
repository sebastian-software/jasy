#!/usr/bin/env bash

# Automatically applies PEP8 compliance for all Python files
autopep8 --aggressive --aggressive --aggressive --in-place --ignore E203,E302,E303,E402 --max-line-length 1000 `find jasy -name "*.py"`

# Automatically format docs
docformatter --in-place --pre-summary-newline --wrap-summaries 120 --wrap-descriptions 120 `find jasy -name "*.py"`
