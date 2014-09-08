#
# Copyright (c) 2013-2014 QuarksLab.
# This file is part of IRMA project.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License in the top-level directory
# of this distribution and at:
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# No part of the project, including this file, may be copied,
# modified, propagated, or distributed except according to the
# terms contained in the LICENSE file.

import re
import os
import bottle
import importlib

from bottle import route, request, default_app, run

"""
    IRMA FRONTEND API
    defines all accessible route accessed via uwsgi..

    For test purpose set DEBUG to True and launch,
    the server will use mockup core class
    irma dependencies are no more required.

    To launch the Debug server just type:

    $ python -m frontend.web.api

    it will launch the server on 0.0.0.0 port 8080
"""

DEBUG = False
if DEBUG:
    s_utils = "mucore"
    s_core = "mucore"
else:
    s_utils = "lib.irma.common.utils"
    s_core = "frontend.web.core"

utils = importlib.import_module(s_utils)
core = importlib.import_module(s_core)

IrmaFrontendReturn = getattr(utils, "IrmaFrontendReturn")
IrmaFrontendError = getattr(core, "IrmaFrontendError")
IrmaFrontendWarning = getattr(core, "IrmaFrontendWarning")


# ==================
#  SERVER TEST MODE
# ==================

@bottle.error(405)
def method_not_allowed(res):
    """ allow CORS request for debug purpose """
    if request.method == 'OPTIONS':
        new_res = bottle.HTTPResponse()
        new_res.set_header('Access-Control-Allow-Origin', '*')
        return new_res
    res.headers['Allow'] += ', OPTIONS'
    req_app = request.app
    return req_app.default_error_handler(res)


@bottle.hook('after_request')
def enableCORSAfterRequestHook():
    """ allow CORS request for debug purpose """
    bottle.response.set_header('Access-Control-Allow-Origin', '*')


# =============
#  Server root
# =============

@route("/")
def svr_index():
    """ hello world

    :route: /
    :rtype: dict of 'code': int, 'msg': str
    :return: on success 'code' is 0
    """
    return IrmaFrontendReturn.success()


# =====================
#  Common param checks
# =====================

def validate_id(scanid):
    """ check scanid format - should be a str(ObjectId)"""
    if not re.match(r'^[0-9a-fA-F]{24}$', scanid):
        raise ValueError("Malformed Scanid")


def validate_sha256(sha256):
    """ check hashvalue format - should be a sha256 hexdigest"""
    if not re.match(r'^[0-9a-fA-F]{64}$', sha256):
        raise ValueError("Malformed Sha256")


# ==========
#  Scan api
# ==========

@route("/scan/new")
def scan_new():
    """ create new scan

    :route: /scan/new
    :rtype: dict of 'code': int, 'msg': str [, optional 'scan_id':str]
    :return:
        on success 'scan_id' contains the newly created scan id
        on error 'msg' gives reason message
    """
    try:
        scan_id = core.scan_new()
        return IrmaFrontendReturn.success(scan_id=scan_id)
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


@route("/scan/add/<scanid>", method='POST')
def scan_add(scanid):
    """ add posted file(s) to the specified scan

    :route: /scan/add/<scanid>
    :postparam: multipart form with filename(s) and file(s) data
    :param scanid: id returned by scan_new
    :note: files are posted as multipart/form-data
    :rtype: dict of 'code': int, 'msg': str [, optional 'nb_files':int]
    :return:
        on success 'nb_files' total number of files for the scan
        on error 'msg' gives reason message
    """
    try:
        validate_id(scanid)
        files = {}
        for f in request.files:
            upfile = request.files.get(f)
            filename = os.path.basename(upfile.filename)
            data = upfile.file.read()
            files[filename] = data
        nb_files = core.scan_add(scanid, files)
        return IrmaFrontendReturn.success(nb_files=nb_files)
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


@route("/scan/launch/<scanid>", method='GET')
def scan_launch(scanid):
    """ launch specified scan

    :route: /scan/launch/<scanid>
    :getparam: force=True or False
    :getparam: probe=probe1,probe2
    :param scanid: id returned by scan_new
    :rtype: dict of 'code': int, 'msg': str [, optional 'probe_list':list]
    :return:
        on success 'probe_list' is the list of probes used for the scan
        on error 'msg' gives reason message
    """
    try:
        validate_id(scanid)
        # handle 'force' parameter
        force = False
        if 'force' in request.params:
            if request.params['force'].lower() == 'true':
                force = True
        # handle 'probe' parameter
        in_probelist = None
        if 'probe' in request.params:
            in_probelist = request.params['probe'].split(',')
        out_probelist = core.scan_launch(scanid, force, in_probelist)
        return IrmaFrontendReturn.success(probe_list=out_probelist)
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


@route("/scan/result/<scanid>", method='GET')
def scan_result(scanid):
    """ get all results from files of specified scan

    :route: /scan/result/<scanid>
    :param scanid: id returned by scan_new
    :rtype: dict of 'code': int, 'msg': str
        [, optional 'scan_results': dict of [
            sha256 value: dict of
                'filenames':list of filename,
                'results': dict of [str probename: dict [results of probe]]]]
    :return:
        on success 'scan_results' is the dict of results for each filename
        on error 'msg' gives reason message
    """
    try:
        validate_id(scanid)
        results = core.scan_result(scanid)
        return IrmaFrontendReturn.success(scan_results=results)
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


@route("/scan/progress/<scanid>", method='GET')
def scan_progress(scanid):
    """ get scan progress for specified scan

    :route: /scan/progress/<scanid>
    :param scanid: id returned by scan_new
    :rtype: dict of 'code': int, 'msg': str
        [, optional 'progress_details':
            'total':int,
            'finished':int,
            'successful':int]
    :return:
        on success 'progress_details' contains informations \
        about submitted jobs by irma-brain
        on warning 'msg' gives scan status that does not required \
        progress_details like 'processed' or 'finished'
        on error 'msg' gives reason message
    """
    try:
        validate_id(scanid)
        progress = core.scan_progress(scanid)
        details = progress.get('progress_details', None)
        if details is not None:
            return IrmaFrontendReturn.success(progress_details=details)
        else:
            return IrmaFrontendReturn.warning(progress['status'])
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


@route("/scan/cancel/<scanid>", method='GET')
def scan_cancel(scanid):
    """ cancel all remaining jobs for specified scan

    :route: /scan/cancel/<scanid>
    :param scanid: id returned by scan_new
    :rtype: dict of 'code': int, 'msg': str
        [, optional 'cancel_details':
            total':int,
            'finished':int,
            'cancelled':int]
    :return:
        on success 'cancel_details' contains informations \
        about cancelled jobs by irma-brain
        on error 'msg' gives reason message
    """
    try:
        validate_id(scanid)
        cancel = core.scan_cancel(scanid)
        return IrmaFrontendReturn.success(cancel_details=cancel)
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


@route("/scan/finished/<scanid>", method='GET')
def scan_finished(scanid):
    """ tell if scan specified is finished

    :route: /scan/finished/<scanid>
    :param scanid: id returned by scan_new
    :rtype: dict of 'code': int, 'msg': str
    :return:
        on success results are ready
        on error 'msg' gives reason message
    """
    try:
        validate_id(scanid)
        if core.scan_finished(scanid):
            return IrmaFrontendReturn.success(msg="finished")
        else:
            return IrmaFrontendReturn.warning("not finished")
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


# ===========
#  Probe api
# ===========

@route("/probe/list")
def probe_list():
    """ get active probe list

    :route: /probe/list
    :rtype: dict of 'code': int, 'msg': str
        [, optional 'probe_list': list of str]
    :return:
        on success 'probe_list' contains list of probes names
        on error 'msg' gives reason message
    """
    try:
        probelist = core.probe_list()
        return IrmaFrontendReturn.success(probe_list=probelist)
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


# ==========
#  File api
# ==========
@route("/file/exists/<sha256>")
def file_exists(sha256):
    """ lookup file by sha256 and tell if it exists

    :route: /file/exists/<sha256>
    :param sha256 of the file
    :rtype: dict of 'code': int, 'msg': str
        [, optional 'exists':boolean]
    :return:
        on success 'exists' contains a boolean telling if
        file exists or not
        on error 'msg' gives reason message
    """
    try:
        validate_sha256(sha256)
        exists = core.file_exists(sha256)
        return IrmaFrontendReturn.success(exists=exists)
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


@route("/file/result/<sha256>")
def file_result(sha256):
    """ lookup file by sha256

    :route: /file/search/<scanid>
    :param sha256 of the file
    :rtype: dict of 'code': int, 'msg': str
        [, optional 'scan_results': dict of [
            sha256 value: dict of
                'filenames':list of filename,
                'results': dict of [str probename: dict [results of probe]]]]
    :return:
        on success 'scan_results' contains results for file
        on error 'msg' gives reason message
    """
    try:
        validate_sha256(sha256)
        res = core.file_result(sha256)
        return IrmaFrontendReturn.success(scan_results=res)
    # handle all errors/warning as errors
    # file existence should be tested before calling this route
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


@route("/file/infected/<sha256>")
def file_infected(sha256):
    """ lookup file by sha256 and tell if av detect it as
        infected

    :route: /file/suspicious/<sha256>
    :param sha256 of the file
    :rtype: dict of 'code': int, 'msg': str
        [, optional 'infected':boolean, 'nb_detected':int, 'nb_scan':int]
    :return:
        on success 'infected' contains boolean results
        with details in 'nb_detected' and 'nb_scan'
        on error 'msg' gives reason message
    """
    try:
        validate_sha256(sha256)
        res = core.file_infected(sha256)
        return IrmaFrontendReturn.success(infected=res['infected'],
                                          nb_scan=res['nb_scan'],
                                          nb_detected=res['nb_detected'])
    except Exception as e:
        return IrmaFrontendReturn.error(str(e))

# ==============
#  Documentation
# ==============
@route("/api-docs")
def resource_listing():
    try:
        import yaml
        import json

        with open('docs/api/specs/api-docs.yml') as file:
            data = yaml.load(file)

            bottle.response.content_type = "application/json"
            return json.dumps(data)

    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


@route("/api-docs/<file_name:re:(files|probes|scans)>")
def api_declaration(file_name):
    try:
        import yaml
        import json

        with open('docs/api/specs/' + file_name + '.yml') as file:
            data = yaml.load(file)
            data.update(yaml.load(open('docs/api/specs/common.yml')))

            bottle.response.content_type = "application/json"
            return json.dumps(data)

    except Exception as e:
        return IrmaFrontendReturn.error(str(e))


# ======
#  Main
# ======

# deprecated launched via uwsgi now
application = default_app()

if __name__ == "__main__":
    print "Irma Web Api",
    if DEBUG:
        print " /!\\ Debug MODE /!\\"
    run(host='0.0.0.0', port=8080)
