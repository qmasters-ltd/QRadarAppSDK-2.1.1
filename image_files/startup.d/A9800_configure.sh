#!/bin/bash -e

Log "A9800 Altering sudo access for appuser to allow only update_ca_bundle.sh"
as_root "sed -i 's/appuser ALL=(ALL) NOPASSWD:ALL/appuser ALL=(ALL) NOPASSWD: \/opt\/app-root\/bin\/update_ca_bundle.sh/g'" /etc/sudoers
