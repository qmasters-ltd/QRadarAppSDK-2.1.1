# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import requests
from datetime import date, datetime
from packaging.version import Version, InvalidVersion
from sdk_exceptions import SdkVersionError
import sdk_util

ISO_DATE_FORMAT = '%Y-%m-%d'
SDK_APP_EXCHANGE_URL = 'https://exchange.xforce.ibmcloud.com/api/hub/extensions/517ff786d70b6dfa39dde485af6cbc8b'

LAST_VERSION_CHECK_FILENAME = '.last_version_check'
VERSION_FILENAME = 'version.txt'
CONF_DIR = 'conf'

WARN_MSG = '''WARNING: Please upgrade your SDK to version %s, available on X-Force Exchange.
Upgrading will ensure you are up-to-date with the latest fixes, features, and base image version.
If your app uses an older base image version, it might not pass the app verification process.'''
ERROR_MESSAGE_CHECKING_APP_EXCHANGE = 'Unable to retrieve SDK version information from the App Exchange'
ERROR_MESSAGE_RETRIEVING_LAST_VERSION = 'Unable to retrieve version check information'
ERROR_MESSAGE_WRITING_LAST_VERSION = 'Unable to store version check information'
ERROR_MESSAGE_RETRIEVING_SDK_VERSION = 'Unable to determine current SDK version, file version.txt is missing'
ERROR_MESSAGE_COMPARING_VERSIONS = 'Unable to resolve dates for version check'
CHECK_MESSAGE = 'Checking SDK version...'
CHECK_MSG_UPTODATE = 'SDK is up-to-date'

def build_version_path():
    return sdk_util.build_sdk_path(VERSION_FILENAME)

def build_last_version_check_path():
    return sdk_util.build_sdk_path(CONF_DIR, LAST_VERSION_CHECK_FILENAME)

def today_date_string():
    return date.today().isoformat()

# When 3.7 is Python minimum version for SDK, this function
# can be replaced by date.fromisoformat()
def convert_date_string_to_date(date_string):
    return datetime.strptime(date_string, ISO_DATE_FORMAT).date()

def read_last_version_check():
    try:
        with open(build_last_version_check_path()) as last_version:
            return convert_date_string_to_date(last_version.readline().strip())
    except (FileNotFoundError, ValueError):
        write_today_to_last_version_file()
        return date.today()
    except OSError:
        raise SdkVersionError(ERROR_MESSAGE_RETRIEVING_LAST_VERSION)

def write_today_to_last_version_file():
    try:
        with open(build_last_version_check_path(), 'w') as last_version:
            last_version.write(today_date_string())
    except OSError:
        raise SdkVersionError(ERROR_MESSAGE_WRITING_LAST_VERSION)

def need_to_check_version():
    if sdk_util.env_var_is_true('SDK_SKIP_VERSION_CHECK'):
        return False
    return read_last_version_check() < date.today()

# pylint: disable=inconsistent-return-statements
def retrieve_latest_app_exchange_version():
    try:
        sdk_info_exchange = requests.get(SDK_APP_EXCHANGE_URL, timeout=10)
        if sdk_info_exchange.status_code == 200:
            sdk_versions = sdk_info_exchange.json()['extensions'][0]['value']['app_versions']
            for key in sdk_versions:
                if sdk_versions[key]['status'] == 'published':
                    return key
        raise SdkVersionError(ERROR_MESSAGE_CHECKING_APP_EXCHANGE)
    except (requests.exceptions.RequestException, KeyError):
        raise SdkVersionError(ERROR_MESSAGE_CHECKING_APP_EXCHANGE)

def retrieve_sdk_installed_version():
    try:
        with open(build_version_path()) as version_file:
            return version_file.readline().strip()
    except OSError:
        raise SdkVersionError(ERROR_MESSAGE_RETRIEVING_SDK_VERSION)

def needs_upgraded(sdk_installed, sdk_latest_on_exchange):
    try:
        return Version(sdk_installed) < Version(sdk_latest_on_exchange)
    except InvalidVersion:
        raise SdkVersionError(ERROR_MESSAGE_COMPARING_VERSIONS)

def perform_version_check():
    if need_to_check_version():
        print(CHECK_MESSAGE)
        write_today_to_last_version_file()
        sdk_latest_on_exchange = retrieve_latest_app_exchange_version()
        sdk_installed = retrieve_sdk_installed_version()
        if needs_upgraded(sdk_installed, sdk_latest_on_exchange):
            print(WARN_MSG % sdk_latest_on_exchange)
        else:
            print(CHECK_MSG_UPTODATE)
        print('')
