#!/bin/sh
set -eu

python /opt/demo/check_demo.py
exec "$@"
