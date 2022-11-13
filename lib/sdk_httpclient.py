# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

from requests import Session
from requests.exceptions import RequestException, SSLError
import sdk_certificates
from sdk_exceptions import SdkServerSslError, SdkServerRequestError, SdkApiResponseError
from sdk_serverconfig import ServerConfig
import sdk_util

class SdkHttpClient():
    # See requests.adapters.HTTPAdapter.send() for timeout details.
    # REQUESTS_TIMEOUT is for all requests, except for uploads.
    REQUESTS_TIMEOUT = (10, None)
    # POST and PUT requests that send a payload use this timeout.
    UPLOAD_TIMEOUT = 60

    def __init__(self, qradar_console, username, password, cert_path):
        self.qradar_console = qradar_console
        self.username = username
        self.password = password
        self.cert_path = cert_path
        self.server_config = ServerConfig.from_host_json_file(qradar_console)
        self.upload_timeout = self.UPLOAD_TIMEOUT

    def set_upload_timeout(self, timeout):
        if timeout != self.UPLOAD_TIMEOUT:
            print('Using upload timeout {0}s'.format(timeout))
        self.upload_timeout = timeout

    @classmethod
    def create_certified_client(cls, qradar_console, username):
        cert_path = sdk_certificates.verify_certificate_bundle(qradar_console)
        password = sdk_util.read_password(username)
        return cls(qradar_console, username, password, cert_path)

    # Helper functions
    def _get_requests_session(self):
        session = Session()
        if self.server_config.has_socks_proxy():
            session.proxies.update(self.server_config.get_socks_config())
        return session

    def _server_host(self):
        server_hostname = self.server_config.get_server_hostname()
        return server_hostname if server_hostname else self.qradar_console

    def _build_endpoint_url(self, request_endpoint):
        return 'https://' + self._server_host() + request_endpoint

    def _handle_request_exception(self, exception):
        if isinstance(exception, SSLError):
            raise SdkServerSslError('SSL error from host {0}:\n{1}'.format(self._server_host(), exception))
        error_message = 'Request to host {0} failed:\n{1}'.format(self._server_host(), exception)
        hostname = self.server_config.get_server_hostname()
        if hostname and 'ConnectTimeoutError' in error_message:
            error_message += '\nPlease check that {0} is present in your hosts configuration'.format(hostname)
        elif 'write operation timed out' in error_message:
            error_message += '\nTry supplying a longer timeout via the -t option'
        raise SdkServerRequestError(error_message)

    def _check_for_invalid_response(self, response, valid_codes):
        if response.status_code in valid_codes:
            return
        if response.status_code == 401:
            raise SdkApiResponseError('Authentication failed for user {0}'.format(self.username), 401)

        response_json = response.json()
        try:
            if 'message' in response_json:
                message = response_json['message']
            else:
                message = response_json['http_response']['message']
        except KeyError:
            message = response.text

        try:
            api_code = response_json['code']
        except KeyError:
            api_code = 0

        raise SdkApiResponseError(message, response.status_code, api_code)

    # HTTP functions

    def get(self, request_endpoint, request_headers):
        session = self._get_requests_session()
        try:
            response = session.get(url=self._build_endpoint_url(request_endpoint),
                                   auth=(self.username, self.password),
                                   headers=request_headers,
                                   verify=self.cert_path,
                                   timeout=self.REQUESTS_TIMEOUT)
        except RequestException as re:
            self._handle_request_exception(re)
        else:
            self._check_for_invalid_response(response, [200])
        return response

    def post(self, request_endpoint, request_headers, request_json=None, request_package=None):
        session = self._get_requests_session()
        post_timeout = self.upload_timeout if request_package else self.REQUESTS_TIMEOUT
        try:
            response = session.post(url=self._build_endpoint_url(request_endpoint),
                                    auth=(self.username, self.password),
                                    headers=request_headers,
                                    json=request_json,
                                    verify=self.cert_path,
                                    data=request_package,
                                    timeout=post_timeout)
        except RequestException as re:
            self._handle_request_exception(re)
        else:
            self._check_for_invalid_response(response, [200, 201])
        return response

    def put(self, request_endpoint, request_headers, request_json=None, request_package=None):
        session = self._get_requests_session()
        put_timeout = self.upload_timeout if request_package else self.REQUESTS_TIMEOUT
        try:
            response = session.put(url=self._build_endpoint_url(request_endpoint),
                                   auth=(self.username, self.password),
                                   headers=request_headers,
                                   json=request_json,
                                   verify=self.cert_path,
                                   data=request_package,
                                   timeout=put_timeout)
        except RequestException as re:
            self._handle_request_exception(re)
        else:
            self._check_for_invalid_response(response, [200, 202])
        return response

    def delete(self, request_endpoint):
        session = self._get_requests_session()
        try:
            response = session.delete(url=self._build_endpoint_url(request_endpoint),
                                      auth=(self.username, self.password),
                                      verify=self.cert_path,
                                      timeout=self.REQUESTS_TIMEOUT)
        except RequestException as re:
            self._handle_request_exception(re)
        else:
            self._check_for_invalid_response(response, [204])
        return response
