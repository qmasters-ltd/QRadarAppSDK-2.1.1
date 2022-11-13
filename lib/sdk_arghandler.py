# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import argparse
import uuid
from sdk_actions import (create_workspace, build_image, run_app, clean, server_details,
                         preregister, register, deregister, package, deploy,
                         authorize, check_app_status, cancel_app_install, delete_app)
from sdk_argactions import (VersionAction, ReadmeAction, PortAction, UuidAction,
                            IPAction, AppIdAction, TimeoutAction)
from sdk_httpclient import SdkHttpClient


class SdkArgHandler():
    def __init__(self):
        self.parser = self._build_parser()
        self._add_subparsers()
        self.parsed_args = None

    def parse_args(self):
        self.parsed_args = self.parser.parse_args()

    def execute_command(self):
        ''' parse_args() must be called before calling this function. '''
        self.parsed_args.function(self.parsed_args)

    def print_help(self):
        self.parser.print_help()

    def _build_parser(self):
        parser = argparse.ArgumentParser(prog='qapp',
                                         usage='qapp [option]\n       qapp [subcommand] [options]',
                                         description='Develop and manage QRadar apps',
                                         formatter_class=argparse.RawTextHelpFormatter)
        self._change_options_title(parser)
        parser.add_argument('-v', '--version', action=VersionAction, help='show version')
        parser.add_argument('-d', '--docs', action=ReadmeAction,
                            help='open SDK documentation in a browser')
        return parser

    def _add_subparsers(self):
        self.subparsers = self.parser.add_subparsers(prog='qapp', title='Subcommands')
        self._add_subparser_create()
        self._add_subparser_build()
        self._add_subparser_run()
        self._add_subparser_clean()
        self._add_subparser_server()
        self._add_subparser_preregister()
        self._add_subparser_register()
        self._add_subparser_deregister()
        self._add_subparser_package()
        self._add_subparser_deploy()
        self._add_subparser_authorize()
        self._add_subparser_status()
        self._add_subparser_cancel()
        self._add_subparser_delete()

    def _add_subparser_create(self):
        parser = self._add_subparser('create', 'Instantiate a new QRadar app workspace')
        self._add_argument_workspace(parser)
        parser.add_argument('-k', '--key', action=UuidAction, dest='key', default=str(uuid.uuid4()),
                            help=('Application uuid key.\nLeave blank to allow the SDK '
                                  'to generate a uuid for your app.'))
        parser.set_defaults(function=create_workspace)

    def _add_subparser_build(self):
        parser = self._add_subparser('build', 'Build a Docker image for an app')
        self._add_argument_workspace(parser)
        parser.set_defaults(function=build_image)

    def _add_subparser_run(self):
        parser = self._add_subparser('run', 'Run an app locally in a Docker container')
        self._add_argument_workspace(parser)
        self._add_argument_console(
            parser, help_text=('Supply this option to identify a development app\'s QRadar server,\n'
                               'and/or to mount the certificate bundle from that server into the container.'))
        parser.add_argument('-p', '--port', action=PortAction, dest='host_port', type=int,
                            help=('Host port to bind to port 5000 in the container.\n'
                                  'If not supplied, a random port is assigned.\n'
                                  'If the app does not use Flask, this argument is ignored.'))
        parser.add_argument('-d', '--development', action='store_true', dest='use_dev_env',
                            help=('Run Flask app in development mode.\n'
                                  'This is useful when developing a Flask-based app.'))
        parser.add_argument('-l', '--log', action='store_true', dest='show_logs',
                            help=('Show container logs.\n'
                                  'This is useful for debugging container startup.'))
        parser.set_defaults(function=run_app)

    def _add_subparser_clean(self):
        parser = self._add_subparser('clean',
                                     'Remove the app Docker container and, optionally, the app image')
        self._add_argument_workspace(parser)
        parser.add_argument('-i', '--image-remove', action='store_true', dest='image_remove',
                            help='Remove app image')
        parser.set_defaults(function=clean)

    def _add_subparser_server(self):
        parser = self._add_subparser('server', 'Identify default QRadar server and user values for app development')
        self._add_argument_console(parser)
        self._add_argument_user(parser)
        parser.set_defaults(function=server_details)

    def _add_subparser_preregister(self):
        parser = self._add_subparser('preregister', 'Preregister a development app with QRadar')
        self._add_argument_console(parser)
        self._add_argument_user(parser)
        self._add_argument_workspace(parser)
        parser.set_defaults(function=preregister)

    def _add_subparser_register(self):
        parser = self._add_subparser('register', 'Register a development app with QRadar')
        self._add_argument_console(parser)
        self._add_argument_user(parser)
        self._add_argument_workspace(parser)
        parser.add_argument('-i', '--ip', action=IPAction, dest='local_ip', default='127.0.0.1',
                            help=('Address of local computer used by QRadar server.\n'
                                  'Defaults to 127.0.0.1 with assumption that remote port forwarding '
                                  'is being used.'))
        parser.set_defaults(function=register)

    def _add_subparser_deregister(self):
        parser = self._add_subparser('deregister', 'Deregister a development app with QRadar')
        self._add_argument_console(parser)
        self._add_argument_user(parser)
        self._add_argument_workspace(parser)
        parser.set_defaults(function=deregister)

    def _add_subparser_package(self):
        parser = self._add_subparser('package', 'Package app files into a zip archive')
        self._add_argument_workspace(parser)
        self._add_argument_package(parser)
        parser.set_defaults(function=package)

    def _add_subparser_deploy(self):
        parser = self._add_subparser('deploy', 'Deploy app zip file to QRadar server')
        self._add_argument_package(parser)
        self._add_argument_console(parser)
        self._add_argument_user(parser)
        self._add_argument_auth_user(parser)
        parser.add_argument('-t', '--timeout', action=TimeoutAction, dest='upload_timeout', type=int,
                            default=SdkHttpClient.UPLOAD_TIMEOUT,
                            help=('The number of seconds before connection timeout occurs.\n'
                                  'Defaults to {0}.\n'
                                  'Use this when uploading a large zip archive.'
                                  .format(SdkHttpClient.UPLOAD_TIMEOUT)))
        parser.set_defaults(function=deploy)

    def _add_subparser_authorize(self):
        parser = self._add_subparser('authorize',
                                     'Finish deployment of an app by supplying an authorization user')
        self._add_argument_console(parser)
        self._add_argument_user(parser)
        self._add_argument_app_id(parser)
        self._add_argument_auth_user(parser)
        parser.set_defaults(function=authorize)

    def _add_subparser_status(self):
        parser = self._add_subparser('status', 'Check the status of a deployed app')
        self._add_argument_console(parser)
        self._add_argument_user(parser)
        self._add_argument_app_id(parser)
        parser.set_defaults(function=check_app_status)

    def _add_subparser_cancel(self):
        parser = self._add_subparser('cancel', 'Cancel an app deploy')
        self._add_argument_console(parser)
        self._add_argument_user(parser)
        self._add_argument_app_id(parser)
        parser.set_defaults(function=cancel_app_install)

    def _add_subparser_delete(self):
        parser = self._add_subparser('delete', 'Delete a deployed app')
        self._add_argument_console(parser)
        self._add_argument_user(parser)
        self._add_argument_app_id(parser, help_text=('Instance ID of the QRadar app to delete.\n'
                                                     'Both the app definition and instance will be deleted.'))
        parser.set_defaults(function=delete_app)

    def _add_subparser(self, subparser_name, help_text):
        # help: displayed by qapp -h
        # description: displayed by qapp <action> -h
        # RawTextHelpFormatter enables control of how help text is formatted.
        parser = self.subparsers.add_parser(subparser_name, help=help_text, description=help_text,
                                            formatter_class=argparse.RawTextHelpFormatter)
        self._change_options_title(parser)
        return parser

    @staticmethod
    def _change_options_title(parser):
        # pylint: disable=protected-access
        parser._optionals.title = 'Options'

    @staticmethod
    def _add_argument_workspace(parser):
        parser.add_argument('-w', '--workspace', action='store', dest='workspace', default='.',
                            help='Path to app workspace folder.\nDefaults to the current directory.')

    @staticmethod
    def _add_argument_package(parser):
        parser.add_argument('-p', '--package', action='store', dest='package', required=True,
                            help='Package name destination\ne.g. com.ibm.app.1.0.0.zip')

    @staticmethod
    def _add_argument_console(parser, help_text='Address of QRadar server'):
        parser.add_argument('-q', '--qradar-console', action='store', dest='qradar_console',
                            help=help_text)

    @staticmethod
    def _add_argument_user(parser):
        parser.add_argument('-u', '--user', action='store', dest='user',
                            help=('QRadar user name.\n'
                                  'Used for connecting to the App Framework on QRadar server'))

    @staticmethod
    def _add_argument_app_id(parser, help_text='ID of the QRadar app instance'):
        parser.add_argument('-a', '--application-id', action=AppIdAction, dest='application_id', required=True,
                            help=help_text)

    @staticmethod
    def _add_argument_auth_user(parser):
        parser.add_argument('-o', '--auth-user', action='store', dest='auth_user',
                            help='QRadar app authorization user')
