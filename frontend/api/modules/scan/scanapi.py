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

import os
import re
from bottle import Bottle, request
from frontend.api.modules.webapi import WebApi
from lib.common.utils import UUID
from lib.irma.common.utils import IrmaFrontendReturn
import frontend.controllers.scanctrl as scan_ctrl
import frontend.controllers.frontendtasks as celery_frontend


scan_app = Bottle()


# =====================
#  Common param checks
# =====================

def validate_id(scanid):
    """ check scanid format - should be a str(ObjectId)"""
    if not UUID.validate(scanid):
        raise ValueError("Malformed Scanid")


# ==========
#  Scan api
# ==========

class ScanApi(WebApi):
    _mountpath = "/scan"
    _app = Bottle()

    def __init__(self):
        self._app.route('/new', callback=self._new)
        self._app.route('/add/<scanid>', method='POST', callback=self._add)
        self._app.route('/launch/<scanid>', callback=self._launch)
        self._app.route('/progress/<scanid>', callback=self._progress)
        self._app.route('/cancel/<scanid>', callback=self._cancel)
        self._app.route('/finished/<scanid>', callback=self._finished)
        self._app.route('/info/<scanid>', callback=self._info)
        self._app.route('/<scanid>/results', callback=self._results)
        self._app.route('/<scanid>/results/<file_idx>', callback=self._result)

    def _new(self):
        """ create new scan
        :route: /new
        :rtype: dict of 'code': int, 'msg': str [, optional 'scan_id':str]
        :return:
            on success 'scan_id' contains the newly created scan id
            on error 'msg' gives reason message
        """
        try:
            ip = request.remote_addr
            scan_id = scan_ctrl.new(ip)
            return IrmaFrontendReturn.success(scan_id=scan_id)
        except Exception as e:
            return IrmaFrontendReturn.error(str(e))

    def _add(self, scanid):
        """ add posted file(s) to the specified scan

        :route: /add/<scanid>
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
                # NOTE: using raw_filename instead of filename as filename has
                # been sanitized by bottle.py to avoid FS filename issues. As
                # files are stored with their hash value instead of name, this
                # should not introduce errors.
                filename = upfile.raw_filename
                filename = os.path.basename(filename)
                data = upfile.file.read()
                files[filename] = data
            nb_files = scan_ctrl.add_files(scanid, files)
            return IrmaFrontendReturn.success(nb_files=nb_files)
        except Exception as e:
            return IrmaFrontendReturn.error(str(e))

    def _launch(self, scanid):
        """ launch specified scan

        :route: /launch/<scanid>
        :getparam: force=True or False
        :getparam: probe=probe1,probe2
        :param scanid: id returned by scan_new
        :rtype: dict of 'code': int, 'msg': str
                [, optional 'probe_list':list]
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
            out_probelist = scan_ctrl.launch_synchronous(scanid,
                                                         force,
                                                         in_probelist)
            # launch_asynchronous scan via frontend task
            celery_frontend.scan_launch(scanid)
            return IrmaFrontendReturn.success(probe_list=out_probelist)
        except Exception as e:
            return IrmaFrontendReturn.error(str(e))

    def _progress(self, scanid):
        """ get scan progress for specified scan

        :route: /progress/<scanid>
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
            progress = scan_ctrl.progress(scanid)
            details = progress.get('progress_details', None)
            if details is not None:
                return IrmaFrontendReturn.success(progress_details=details)
            else:
                return IrmaFrontendReturn.warning(progress['status'])
        except Exception as e:
            return IrmaFrontendReturn.error(str(e))

    def _cancel(self, scanid):
        """ cancel all remaining jobs for specified scan

        :route: /cancel/<scanid>
        :param scanid: id returned by scan_new
        :rtype: dict of 'code': int, 'msg': str
            [, optional 'cancel_details':
                'total':int,
                'finished':int,
                'cancelled':int]
        :return:
            on success 'cancel_details' contains informations \
            about cancelled jobs by irma-brain
            on error 'msg' gives reason message
        """
        try:
            validate_id(scanid)
            cancel = scan_ctrl.cancel(scanid)
            return IrmaFrontendReturn.success(cancel_details=cancel)
        except Exception as e:
            return IrmaFrontendReturn.error(str(e))

    def _finished(self, scanid):
        """ tell if scan specified is finished

        :route: /finished/<scanid>
        :param scanid: id returned by scan_new
        :rtype: dict of 'code': int, 'msg': str
        :return:
            on success results are ready
            on error 'msg' gives reason message
        """
        try:
            validate_id(scanid)
            if scan_ctrl.finished(scanid):
                return IrmaFrontendReturn.success(msg="finished")
            else:
                return IrmaFrontendReturn.warning("not finished")
        except Exception as e:
            return IrmaFrontendReturn.error(str(e))

    def _info(self, scanid):
        """ returns all info about scan

        :route: /info/<scanid>
        :param scanid: id returned by scan_new
        :rtype: dict of 'code': int, 'msg': str [, optional 'scan_info':
                'probelist': list,
                'finished': bool,
                'file_sha256': dict]
        :return:
            on success results are ready
            on error 'msg' gives reason message
        """
        try:
            validate_id(scanid)
            scan_info = scan_ctrl.info(scanid)
            return IrmaFrontendReturn.success(scan_info=scan_info)
        except Exception as e:
            return IrmaFrontendReturn.error(str(e))

    def _results(self, scanid):
        """ returns an array of results from a scan

        :route: /scan/<scanid>/results
        :param scanid: id returned by scan_new
        :param formatted boolean to get formatted results or not
               (default to True)
        :rtype: dict of 'code': int, 'msg': str [, optional 'scan_results':
                'status': int,
                'finished': int,
                'total': int,
                'files': list]
        :return:
            on success results are ready
            on error 'msg' gives reason message
        """
        try:
            validate_id(scanid)
            formatted = True
            if 'formatted' in request.params:
                if request.params['formatted'].lower() == 'false':
                    formatted = False
            results = scan_ctrl.get_results(scanid, formatted)
            return IrmaFrontendReturn.success(scan_results=results)
        except Exception as e:
            return IrmaFrontendReturn.error(str(e))

    def _result(self, scanid, file_idx):
        """ returns a specified results from a scan

        :route: /scan/<scanid>/results/<file_idx>
        :param scanid: id returned by scan_new
        :param file_idx: file index in scan returned by _scan_results
        :param formatted boolean to get formatted results or not
               (default to True)
        :rtype: dict of 'code': int, 'msg': str [, optional 'results':
                'tools_finished': int,
                'tools_total': int,
                'file_infos': list,
                'probe_results': list]
        :return:
            on success results are ready
            on error 'msg' gives reason message
        """
        try:
            validate_id(scanid)
            formatted = True
            if 'formatted' in request.params:
                if request.params['formatted'].lower() == 'false':
                    formatted = False
            file_idx = int(file_idx)
            results = scan_ctrl.get_result(scanid, file_idx, formatted)
            return IrmaFrontendReturn.success(results=results)
        except Exception as e:
            return IrmaFrontendReturn.error(str(e))
