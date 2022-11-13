#!/bin/bash

set -e

APPCERTFOLDER=/opt/app-root/store/certs
ANCHORSFOLDER=/etc/pki/ca-trust/source/anchors

timestamp()
{
  date +"%Y-%m-%d %H:%M:%S"
}

if [ -n "$(ls -A $APPCERTFOLDER 2>/dev/null)" ]
then
  echo "$(timestamp) Found certificates under $APPCERTFOLDER, adding certificates to list of trusted CAs"
  if cp -rf $APPCERTFOLDER/* $ANCHORSFOLDER
  then
    if /bin/update-ca-trust -f
    then
      echo "$(timestamp) Certificates added to trusted CA list successfully"
    else
      echo "$(timestamp) Failed to update trusted CA list"
    fi
  else
    echo "$(timestamp) Unable to copy certificates from $APPCERTFOLDER"
  fi
else
  echo "$(timestamp) No certificates found under $APPCERTFOLDER, skipping..."
fi
