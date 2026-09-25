#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 0
exec "${DMI_REVIEW_PYTHON:?Operator must set the review Python}" ./run_review.py
