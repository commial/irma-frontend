#
# Copyright (c) 2013-2015 QuarksLab.
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

from celery import exceptions as celery_exceptions
from lib.irma.common.exceptions import IrmaTaskError


def sync_call(celery_app, taskpath, taskname, timeout, **kwargs):
    """ send a task to the celery app with specified args
        and wait until timeout param for result
    """
    try:
        full_task_path = "{0}.{1}".format(taskpath, taskname)
        task = celery_app.send_task(full_task_path, **kwargs)
        (status, res) = task.get(timeout=timeout)
        return (status, res)
    except celery_exceptions.TimeoutError:
        raise IrmaTaskError("Celery timeout - {0}".format(taskname))


def async_call(celery_app, taskpath, taskname, **kwargs):
    """ send a task to the celery app with specified args
        without waiting for results.
    """
    try:
        full_task_path = "{0}.{1}".format(taskpath, taskname)
        return celery_app.send_task(full_task_path, **kwargs)
    except:
        raise IrmaTaskError("Celery error - {0}".format(taskname))
