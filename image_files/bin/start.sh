#!/bin/bash
set -e

trap 'cleanup; exit 143' SIGINT SIGTERM

as_root chown -R "${APP_USER_ID}":"${APP_GROUP_ID}" "$APP_ROOT"

logdir="$APP_ROOT"/store/log

if [ ! -d "$logdir" ]
then
  mkdir -p "$logdir"
fi
chmod 755 "$logdir"

STARTLOG="$logdir/startup.log"
export STARTLOG

if [ ! -f "$STARTLOG" ]
then
  touch "$STARTLOG"
fi
chmod 644 "$STARTLOG"

Log() {
  NOW=$(date +"%Y-%m-%d %H:%M:%S")
  echo "$NOW $*" >> "$STARTLOG"
}
export -f Log

Run() {
  Log "$*"
  "$@" >> "$STARTLOG" 2>&1
}
export -f Run

cleanup() {
  cleanup_script="$APP_ROOT"/container/clean/cleanup.sh
  if [ -e "${cleanup_script}" ]
  then
    Log "Executing ${cleanup_script}"
    sh "${cleanup_script}"
  else
    Log "No ${cleanup_script} script found, skipping cleanup"
  fi
  kill -TERM "${CHILD_PID}"
}
export -f cleanup

script_uses_log() {
  local scriptname=$1
  ! [[ $scriptname =~ supervisord ]]
}

cd "$APP_ROOT"
for script in "$APP_ROOT"/startup.d/A[0-9][0-9[0-9[0-9]*
do
  scriptfile=$(basename "$script")
  set +e
  if script_uses_log "$scriptfile"
  then
    scriptlog="$logdir"/"$scriptfile".log
    $script > "$scriptlog" 2>&1 &
  else
    $script &
  fi
  export CHILD_PID=$!
  Log "$scriptfile running with pid ${CHILD_PID}"
  wait "${CHILD_PID}"
  exit_code=$?
  set -e
  Log "$scriptfile exited with status $exit_code"

  if [ $exit_code -ne 0 ]
  then
    if script_uses_log "$scriptfile"
    then
      cat "$scriptlog"
    fi
    exit $exit_code
  fi
done
