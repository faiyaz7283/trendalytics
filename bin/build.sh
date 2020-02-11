#!/usr/bin/env bash
set -e

BASEDIR=$(dirname "$0")
DC_FILE=${BASEDIR}/../docker-compose.yml
SEC=20
re='^[0-9]+$'

if [ "${1:-}" = "--limit" ] && [[ ${2:-} =~ $re ]]; then
    export LIMIT="${2}"
fi

if [ "${1:-}" = "kill" ] || [ "${3:-}" = "kill" ]; then
    docker-compose -f ${DC_FILE} down
    exit 0
elif [ "${1:-}" = "start" ] || [ "${3:-}" = "start" ]; then
    docker-compose -f ${DC_FILE} up -d
    echo "Waiting ${SEC} seconds for db to finish loading..."
    sleep ${SEC}
fi

PY_CMD="python scripts/fix_tp_tsa_search_volume.py --limit=${LIMIT:-}"
docker-compose -f ${DC_FILE} exec -e COLUMNS="`tput cols`" -e LINES="`tput lines`" worker bash -l -c "${PY_CMD}"
