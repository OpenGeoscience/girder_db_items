#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#  Copyright Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
##############################################################################

import os
import re
import sqlalchemy

from girder.models.file import File
from girder.utility import path as path_util
from girder import logger as log

from . import base
from .sqlalchemydb import SQLAlchemyConnector


SqliteOperators = {
    'eq': '=',
    'ne': '!=',
    'gte': '>=',
    'gt': '>',
    'lte': '<=',
    'lt': '<',
    'regex': 'MATCH',  # case sensitive
    'not_regex': 'NOT MATCH',  # case sensitive
    'search': 'REGEXP',  # case insenstive
    'not_search': 'NOT REGEXP',  # case insensitive
}

SqliteFunctions = {k: True for k in [
    'cast',
    'count',
    'distinct',

    # From https://sqlite.org/lang_corefunc.html
    'abs',
    'char',
    'coalesce',
    'glob',
    'hex',
    'ifnull',
    'instr',
    'last_insert_rowid',
    'length',
    'like',
    'likelihood',
    'likely',
    'lower',
    'ltrim',
    'max',
    'min',
    'nullif',
    'printf',
    'quote',
    'random',
    'randomblob',
    'replace',
    'round',
    'rtrim',
    'soundex',
    'substr',
    'trim',
    'typeof',
    'unicode',
    'unlikely'
    'upper',
    'zeroblob',

    'date',
    'datetime',
    'julianday',
    'strftime',
    'time',

    'avg',
    'group_concat',
    'sum',
    'total',

    'json',
    'json_array',
    'json_array_length',
    'json_each',
    'json_extract',
    'json_insert',
    'json_group_array',
    'json_group_object',
    'json_object',
    'json_patch',
    'json_quote',
    'json_remove',
    'json_replace',
    'json_set',
    'json_tree',
    'json_type',
    'json_valid',
]}


def regex_func(expr, value):
    """
    Check if a case-sensitive regular expression matches a string.

    :param expr: the regular expression
    :param value: a string
    :returns: True if the regular expression matches.
    """
    regex = re.compile(expr)
    return regex.search(value) is not None


def search_func(expr, value):
    """
    Check if a case-insensitive regular expression matches a string.

    :param expr: the regular expression
    :param value: a string
    :returns: True if the regular expression matches.
    """
    regex = re.compile(expr, re.I)
    return regex.search(value) is not None


class SqliteSAConnector(SQLAlchemyConnector):
    name = 'sqlalchemy_sqlite'
    databaseNameRequired = False

    def __init__(self, *args, **kwargs):
        # The super class also validates the connector
        super(SqliteSAConnector, self).__init__(*args, **kwargs)
        self.databaseName = kwargs.get(
            'database', base.databaseFromUri(kwargs.get('uri')))
        self.databaseOperators = SqliteOperators
        self._allowedFunctions = SqliteFunctions

    @classmethod
    def adjustDBUri(cls, uri, *args, **kwargs):
        """
        Adjust a uri to match the form sqlite requires.  This can convert a
        Girder resource path to an aprpopriate physical file reference.

        :param uri: the uri to adjust.
        :returns: the adjusted uri
        """
        uri = super(SqliteSAConnector, cls).adjustDBUri(uri, *args, **kwargs)
        if '://' in uri:
            uri = uri.split('://', 1)[0] + ':////' + uri.split('://', 1)[1].lstrip('/')
        uri = super(SqliteSAConnector, cls).adjustDBUri(uri, *args, **kwargs)
        # If we have a Girder resource path, convert it.  If this looks like a
        # file but doesn't exist, check if it is a resource path.  If this is
        # not a resoruce path to a file that we can read directly, treat this
        # the same as a missing file.
        if (':///' in uri and not os.path.exists(uri.split(':///', 1)[1])):
            resourcepath = path_util.lookUpPath(
                uri.split(':///', 1)[1], test=True, filter=False, force=True)
            if resourcepath and resourcepath['model'] == 'file':
                file = resourcepath['document']
                adapter = File().getAssetstoreAdapter(file)
                if hasattr(adapter, 'fullPath'):
                    filepath = adapter.fullPath(file)
                    if os.path.exists(filepath):
                        uri = uri.split(':///', 1)[0] + ':///' + filepath
                        log.debug('Using Girder file for SQLite database')
        return uri

    @classmethod
    def canonicalDatabaseUri(cls, uri):
        """
        Adjust a database uri to a canonical form.

        :param uri: the proposed uri.
        :returns: the adjusted uri.
        """
        # make sure we start with (dialect):///(absolute path) where the
        # absolute path starts with a slash.
        if '://' in uri:
            uri = uri.split('://', 1)[0] + ':////' + uri.split('://', 1)[1].lstrip('/')
        return uri

    def connect(self, *args, **kwargs):
        """
        Connect to the database.

        When we connect to the database, make sure we have regular expression
        support.  See the super class for more function details.

        :return: a SQLAlchemny session object.
        """
        sess = super(SqliteSAConnector, self).connect(*args, **kwargs)
        if not getattr(self.dbEngine, '_added_regex', None):

            @sqlalchemy.event.listens_for(self.dbEngine, "begin")
            def engine_begin(conn):
                # Add regular expression support
                conn.connection.create_function('REGEXP', 2, search_func)
                conn.connection.create_function('MATCH', 2, regex_func)

            setattr(self.dbEngine, '_added_regex', True)
        return sess

    def setSessionReadOnly(self, sess):
        """
        Set the specified session to read only if possible.  Subclasses should
        implement the appropriate behavior.

        :param sess: the session to adjust.
        """
        # Make flush do rollback, which is a hack, but better than not doing so
        sess.flush = sess.rollback


base.registerConnectorClass(SqliteSAConnector.name, SqliteSAConnector, {
    'dialects': {
        'sqlite': 'sqlite',
        'sqlitedb': 'sqlite',
    },
    'default_dialect': 'sqlite',
    'priority': 0,
})
