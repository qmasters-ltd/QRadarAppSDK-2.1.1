#!/bin/bash -e

trap 'cleanup; exit 143' SIGINT SIGTERM

configure_log_strategy() {
  if [ "$LOG_STRATEGY" == stdout ]
  then
    # Dispatch logs to STDOUT in the background
    "$APP_ROOT"/bin/log_collector.py &
  fi
}

copy_certificates() {
  if [ ! -d /etc/qradar_pki ]
  then
    return
  fi

  Log 'A0000 Copying mounted certificates from /etc/qradar_pki to /etc/pki'
  set +e
  as_root /bin/cp -rf /etc/qradar_pki/* /etc/pki
  local result=$?
  set -e

  if [ $result -ne 0 ]
  then
    Log 'A0000 Failed to copy certificates from /etc/qradar_pki to /etc/pki'
  fi
}

configure_host_strategy() {
  if [ "$HOST_STRATEGY" == kubernetes ]
  then
    Log 'A0000 HOST_STRATEGY is kubernetes'
  else
    copy_certificates
  fi
}

process_hosts_override() {
  local hosts_override="$APP_ROOT"/store/hosts.override

  if [ ! -f "$hosts_override" ]
  then
    return
  fi

  Log "A0000 Processing entries from $hosts_override"
  while read -r host_entry
  do
    if [ "$host_entry" ]
    then
      # shellcheck disable=SC2086
      # In both lines below, the syntax removes superfluous whitespace from $host_entry,
      # leaving a single space between ip and hostname.
      Log "A0000 Adding /etc/hosts entry from hosts.override:" $host_entry
      as_root "echo $host_entry >> /etc/hosts"
    fi
  done < "$hosts_override"
}

update_hosts_from_environment() {
  # Add a hosts entry for IP/FQDN, but only if one doesn't already exist.
  if [ -n "$QRADAR_CONSOLE_IP" ] && [ -n "$QRADAR_CONSOLE_FQDN" ] &&
     ! grep -qxF "$QRADAR_CONSOLE_IP $QRADAR_CONSOLE_FQDN" /etc/hosts
  then
    Log "A0000 Adding /etc/hosts entry from environment: $QRADAR_CONSOLE_IP $QRADAR_CONSOLE_FQDN"
    as_root "echo $QRADAR_CONSOLE_IP $QRADAR_CONSOLE_FQDN >> /etc/hosts"
  fi
}

execute_container_run_scripts() {
  local run_ordering="$APP_ROOT"/container/run/ordering.txt

  if [ ! -f "$run_ordering" ]
  then
    return
  fi

  Log "A0000 Executing commands from $run_ordering"
  while read -r run_entry || [[ -n "$run_entry" ]]
  do
    if [ "$run_entry" ]
    then
      # shellcheck disable=SC2086
      # Don't quote $run_entry. If it contains space-separated words,
      # Run won't be able to execute the command.
      Run $run_entry
    fi
  done < "$run_ordering"
}

configure_log_strategy
configure_host_strategy
process_hosts_override
update_hosts_from_environment
execute_container_run_scripts
