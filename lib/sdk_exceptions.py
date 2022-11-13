# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

class SdkFatalError(Exception):
    """An error that cannot be recovered from"""

class SdkCertError(SdkFatalError):
    """Local cert bundle is not usable"""

class SdkServerConnectionError(SdkFatalError):
    """Socket connection to server failed"""

class SdkServerRequestError(SdkFatalError):
    """Request to server failed"""

class SdkServerSslError(Exception):
    """Cannot verify server connection due to an SSL error. Triggers PEM refresh."""

class SdkApiResponseError(SdkFatalError):
    """API response indicates unsuccessful operation"""
    def __init__(self, message, http_status=0, api_code=0):
        ''' Store 2 items from response:
              HTTP status code e.g. 404
              API framework code e.g. 4
            This allows specific action to be taken. '''
        super().__init__(message)
        self.http_status = http_status
        self.api_code = api_code

class SdkManifestException(SdkFatalError):
    """The app manifest.json file is not valid"""

class SdkDockerError(SdkFatalError):
    """A Docker error occurred"""

class SdkContainerError(SdkFatalError):
    """An app container error occurred"""

class SdkQradarVersionError(SdkFatalError):
    """The requested action is not supported by the QRadar version"""

class SdkServerConfigError(SdkFatalError):
    """Error managing server configuration when using certificates"""

class SdkWorkspaceError(SdkFatalError):
    """Error managing app workspace"""

class SdkBaseImageError(SdkFatalError):
    """Error retrieving base image version"""

class SdkVersionError(Exception):
    """Error retrieving current SDK version"""
