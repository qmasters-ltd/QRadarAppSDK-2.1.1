# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import sys
import argparse
import ipaddress
import uuid
import webbrowser
from sdk_baseimage import SdkBaseImageConfig, SdkBaseImageError
from sdk_exceptions import SdkVersionError
import sdk_util
import sdk_version

class VersionAction(argparse.Action):
    ''' Shows the SDK version, then exits. '''
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            print(sdk_version.retrieve_sdk_installed_version())
        except SdkVersionError as sve:
            print(sve)
            sys.exit(1)
        sys.exit(0)

class ReadmeAction(argparse.Action):
    ''' Opens the SDK README in a browser, then exits. '''
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        readme_path = sdk_util.build_sdk_path('docs', 'qradar-app-sdk.html')
        if not os.path.exists(readme_path):
            print('{0} not found'.format(readme_path))
            sys.exit(1)
        print('Opening {0}'.format(readme_path))
        if not os.getenv('SDK_TEST_SKIP_README'):
            if not webbrowser.open('file://' + readme_path):
                print('Unable to open {0}'.format(readme_path))
                sys.exit(1)
        sys.exit(0)

class ImagesAction(argparse.Action):
    ''' Shows SDK base image version details, then exits. '''
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        try:
            SdkBaseImageConfig().print_image_details()
        except SdkBaseImageError as sbe:
            print(sbe)
            sys.exit(1)
        sys.exit(0)

class PortAction(argparse.Action):
    ''' Validates a port number, raising ArgumentError if invalid. '''
    def __call__(self, parser, namespace, values, option_string=None):
        if values < 1 or values > 65535:
            raise argparse.ArgumentError(self, 'invalid port number {0}'.format(values))
        setattr(namespace, self.dest, values)

class UuidAction(argparse.Action):
    ''' Validates a UUID if supplied, raising ArgumentError if invalid. '''
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            uuid.UUID(values)
        except ValueError:
            raise argparse.ArgumentError(self, 'invalid uuid {0}'.format(values))
        setattr(namespace, self.dest, values)

class IPAction(argparse.Action):
    ''' Validates an IP address, raising ArgumentError if invalid. '''
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            ipaddress.ip_address(values)
        except ValueError:
            raise argparse.ArgumentError(self, 'invalid address {0}'.format(values))
        setattr(namespace, self.dest, values)

class AppIdAction(argparse.Action):
    ''' Validates an app ID, raising ArgumentError if invalid. '''
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            int(values)
        except ValueError:
            raise argparse.ArgumentError(self, 'invalid application ID {0}'.format(values))
        setattr(namespace, self.dest, values)

class TimeoutAction(argparse.Action):
    ''' Validates a timeout value, raising ArgumentError if invalid. '''
    def __call__(self, parser, namespace, values, option_string=None):
        if values <= 0:
            raise argparse.ArgumentError(self, 'invalid timeout value {0}'.format(values))
        setattr(namespace, self.dest, values)
