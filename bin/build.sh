#!/usr/bin/env bash
set -e

BASEDIR=$(dirname "$0")
DC_FILE=${BASEDIR}/../docker-compose.yml
re='^[0-9]+$'

if [ "${1:-}" = "--limit" ] && [[ ${2:-} =~ $re ]]; then
    export LIMIT="${2}"
fi

if [ "${1:-}" = "kill" ] || [ "${3:-}" = "kill" ]; then
    docker-compose -f ${DC_FILE} down
    exit 0
elif [ "${1:-}" = "start" ] || [ "${3:-}" = "start" ]; then
    docker-compose -f ${DC_FILE} up -d
fi

PY_CMD="python scripts/trendpulse.py --limit=${LIMIT:-}"
docker-compose -f ${DC_FILE} exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" worker bash -l -c "${PY_CMD}"
