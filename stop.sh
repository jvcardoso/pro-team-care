#!/bin/bash
# Launcher para garantir que o script execute com bash
exec bash "$(dirname "$0")/stop_servers.sh" "$@"