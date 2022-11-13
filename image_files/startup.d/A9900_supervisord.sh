#!/bin/bash -e

trap 'cleanup; exit 143' SIGINT SIGTERM

Log "A9900 Starting supervisord"
supervisord -c /etc/supervisord.conf &
wait $!
