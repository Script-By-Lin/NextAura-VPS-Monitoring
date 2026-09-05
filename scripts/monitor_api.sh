#!/usr/bin/env bash
# Wrapper to execute monitor_api.py with python3
exec python3 "$(dirname "$0")/monitor_api.py" "$@"
