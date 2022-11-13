#!/bin/bash -e

trap 'cleanup; exit 143' SIGINT SIGTERM

copyCertificates() {
  Log "A0000 Checking if certificates need to be copied from /etc/qradar_pki to /etc/pki"
  if [ -d /etc/qradar_pki ]
  then
    Log "A0000 /etc/qradar_pki exists, attempting to copy certificates from /etc/qradar_pki to /etc/pki"
    set +e
    as_root /bin/cp -rf /etc/qradar_pki/* /etc/pki
    result=$?
    set -e
    if [ $result -eq 0 ]
    then
      Log "A0000 Copied certificates successfully from /etc/qradar_pki to /etc/pki"
    else
      Log "A0000 Failed to copy certificates from /etc/qradar_pki to /etc/pki"
    fi
  else
    Log "A0000 /etc/qradar_pki does not exist, skipping"
  fi
}

updateHostsFileWithFQDN() {
  Log "A0000 Attempting to update hosts file with FQDN if present in environment variables"
  if ! { [ -z "${QRADAR_CONSOLE_IP}" ] || [ -z "${QRADAR_CONSOLE_FQDN}" ]; }
  then
    Log "A0000 FQDN and console ip found in environment variables, will add to hosts file if required"
    if ! grep -q "${QRADAR_CONSOLE_IP} ${QRADAR_CONSOLE_FQDN}" /etc/hosts
    then
      Log "A0000 Hosts entry not present for FQDN, adding to /etc/hosts"
      as_root "echo ${QRADAR_CONSOLE_IP} ${QRADAR_CONSOLE_FQDN} >> /etc/hosts"
    else
      Log "A0000 Hosts entry already present in /etc/hosts, skipping"
    fi
  else
    Log "A0000 FQDN and console ip environment variables not found, skipping adding entry to hosts file"
  fi
}

if [ "${LOG_STRATEGY}" = "stdout" ]
then
    # Dispatch logs to STDOUT in the background
    "$APP_ROOT"/bin/log_collector.py &
fi

if [ "${HOST_STRATEGY}" != "kubernetes" ]
then
  Log "A0000 Configurating default host strategy."
  copyCertificates
fi

updateHostsFileWithFQDN

if [ -n "${QRADAR_CONSOLE_PEM_CERT}" ]
then
  Log "A0000 Found console PEM cert in environment"
  Log "A0000 Writing cert to /store/consolecert.pem"
  echo -ne "${QRADAR_CONSOLE_PEM_CERT}" > '/store/consolecert.pem'
else
  Log "A0000 Did not find console PEM cert in environment"
fi

if [ -f "$APP_ROOT"/container/run/ordering.txt ]
then
  Log "A0000 Executing commands from $APP_ROOT/container/run/ordering.txt"
  while read -r line || [[ -n "$line" ]];
  do
    # shellcheck disable=SC2086
    # Don't quote $line. If it contains space-separated words,
    # Run won't be able to execute the command.
    Run $line;
  done < "$APP_ROOT"/container/run/ordering.txt
fi
