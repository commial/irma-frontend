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

from bottle import response, request

from frontend.api.errors import process_error
from frontend.helpers.utils import guess_hash_type
from frontend.models.sqlobjects import FileWeb, File
from frontend.helpers.schemas import FileWebSchema


file_web_schema = FileWebSchema()
file_web_schema.context = {'formatted': True}


def files(db):
    """ Search a file using query filters (hash or name). Support
        pagination.
    :param all params are send using query method
    :rtype: dict of 'total': int, 'page': int, 'per_page': int,
        'items': list of file(s) found
    :return:
        on success 'items' contains a list of files found
        on error 'msg' gives reason message
    """
    try:
        name = request.query.name or None
        h_value = request.query.hash or None

        if name is not None and h_value is not None:
            raise ValueError("Can't find using both name and hash")

        # Options query
        offset = int(request.query.offset) if request.query.offset else 0
        limit = int(request.query.limit) if request.query.limit else 25

        if name is not None:
            base_query = FileWeb.query_find_by_name(name, db)
        elif h_value is not None:
            h_type = guess_hash_type(h_value)

            if h_type is None:
                raise ValueError("Hash not supported")

            base_query = FileWeb.query_find_by_hash(h_type, h_value, db)
        else:
            # FIXME this is just a temporary way to output
            # all files, need a dedicated
            # file route and controller
            base_query = FileWeb.query_find_by_name("", db)

        # TODO: Find a way to move pagination as a BaseQuery like in
        #       flask_sqlalchemy.
        # https://github.com/mitsuhiko/flask-sqlalchemy/blob/master/flask_sqlalchemy/__init__.py#L422
        items = base_query.limit(limit).offset(offset).all()

        if offset == 0 and len(items) < limit:
            total = len(items)
        else:
            total = base_query.count()

        response.content_type = "application/json; charset=UTF-8"
        return {
            'total': total,
            'offset': offset,
            'limit': limit,
            'items': file_web_schema.dump(items, many=True).data,
        }
    except Exception as e:
        process_error(e)


def get_file(filesha256, db):
    """Retrieve a file based on its filesha256"""
    try:
        fobj = File.load_from_sha256(filesha256, db)

        # Force download
        response.content_type = 'application/octet-stream; charset=UTF-8'
        response.content_disposition = 'attachment; filename=' + filesha256
        return open(fobj.path).read()

    except Exception as e:
        process_error(e)
