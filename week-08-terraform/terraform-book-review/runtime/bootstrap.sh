#!/bin/sh
set -eu
umask 077
if [ "$#" -ne 1 ] || [ "$1" != /etc/book-review/config.json ]; then
    printf '%s\n' 'bootstrap_config_path_denied' >&2
    exit 1
fi
exec /usr/bin/python3 -B /opt/book-review/configuration/bootstrap.py "$1"
