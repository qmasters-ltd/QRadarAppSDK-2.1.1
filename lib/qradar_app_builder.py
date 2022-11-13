# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import sys
import click
import sdk_arghandler
import sdk_version
from sdk_exceptions import SdkVersionError

try:
    sdk_version.perform_version_check()
except SdkVersionError as sve:
    print('SDK version check failed: {0}'.format(sve))

arg_handler = sdk_arghandler.SdkArgHandler()

# Handle case where user enters 'qapp' and nothing else.
if len(sys.argv) == 1:
    arg_handler.print_help()
    sys.exit(0)

arg_handler.parse_args()

# pylint: disable=broad-except
try:
    arg_handler.execute_command()
except (KeyboardInterrupt, click.Abort):
    print('')
except Exception as unexpected:
    print('An unexpected error occurred: {0}'.format(unexpected))
