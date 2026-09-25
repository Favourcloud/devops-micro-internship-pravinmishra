#!/usr/bin/env bash
set -euo pipefail
test "$#" -eq 0
exec "${DMI_TRIAGE_PYTHON:?Operator supplies a trusted Python}" "${DMI_TRIAGE_WRAPPER:?Operator supplies the fixed private wrapper}"
