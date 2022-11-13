# Licensed Materials - Property of IBM
# 5725I71-CC011829
# (C) Copyright IBM Corp. 2015, 2020. All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.

import os
import sdk_util

PROGRAM_ATTRIBUTES = ['command',
                      'process_name',
                      'numprocs',
                      'numprocs_start',
                      'priority',
                      'autostart',
                      'startsecs',
                      'startretries',
                      'autorestart',
                      'exitcodes',
                      'stopsignal',
                      'stopwaitsecs',
                      'stopasgroup',
                      'killasgroup',
                      'user',
                      'redirect_stderr',
                      'stdout_logfile',
                      'stdout_logfile_maxbytes',
                      'stdout_logfile_backups',
                      'stdout_capture_maxbytes',
                      'stdout_events_enabled',
                      'stdout_syslog',
                      'stderr_logfile',
                      'stderr_logfile_maxbytes',
                      'stderr_logfile_backups',
                      'stderr_capture_maxbytes',
                      'stderr_events_enabled',
                      'stderr_syslog',
                      'environment',
                      'directory',
                      'umask',
                      'serverurl']

PROGRAM_TEMPLATE = '\n[program:{0}]\n'
DEFAULT_PROGRAM_SETTINGS = {'user': 'appuser', 'autorestart': 'true'}

def prepare_supervisord_conf(manifest, build_root_path):
    programs = generate_programs(manifest)
    supervisord_conf_path = os.path.join(build_root_path, 'init', 'supervisord.conf')
    sdk_util.replace_string_in_file(supervisord_conf_path, 'PROGRAM-PLACE-HOLDER', programs)

def generate_programs(manifest):
    programs = ''
    if manifest.uses_flask:
        programs = _create_flask_program()
    if 'services' in manifest.json:
        for named_service in manifest.json['services']:
            programs = programs + _create_named_service_program(named_service)
    return programs

def _create_flask_program():
    settings = dict(DEFAULT_PROGRAM_SETTINGS)
    settings['command'] = '/opt/app-root/bin/start_flask.sh'
    print('Creating Supervisor program entry for Flask')
    return _create_program('startflask', settings)

def _create_named_service_program(named_service):
    if not 'command' in named_service:
        print('Service {0} has no command and will be ignored'.format(named_service['name']))
        return ''
    settings = dict(DEFAULT_PROGRAM_SETTINGS)
    for program_attribute in PROGRAM_ATTRIBUTES:
        if program_attribute in named_service:
            settings[program_attribute] = named_service[program_attribute]
    print('Creating Supervisor program entry for service {0}'.format(named_service['name']))
    return _create_program(named_service['name'], settings)

def _create_program(program_name, program_settings):
    settings = ''
    if program_settings:
        settings = "\n".join("{}={}".format(k,v) for k,v in program_settings.items())
    return PROGRAM_TEMPLATE.format(program_name) + settings + '\n'
