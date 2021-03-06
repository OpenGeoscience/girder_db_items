==================================================
Database Assetstore |build-status| |license-badge|
==================================================

.. |build-status| image:: https://travis-ci.org/OpenGeoscience/database_assetstore.svg?branch=master
    :target: https://travis-ci.org/OpenGeoscience/database_assetstore
    :alt: Build Status

.. |license-badge| image:: https://raw.githubusercontent.com/girder/girder/master/docs/license.png
    :target: https://pypi.python.org/pypi/girder
    :alt: License

A Girder_ Plugin
----------------

.. _Girder: https://github.com/girder/girder

A Girder plugin to provide access to database tables via assetstores and extra file endpoints.

You can create an assetstore that references a database, and import Girder 'files' from that assetstore.  Each file connects to a table or collection in the database.  When downloaded, the file returns a default selection from the database.

Alternately, the database assetstore file can be acted on directly.

Mongo, MySQL, Postgres, and SQLite databases are supported fully.  Additional sql varients are supported if the appropriate sqlalchemy python modules are installed.

The ``POST`` ``file/{id}/database`` endpoint sets the default query parameters for the database table connection, including fields, filters, sort, format, and limit.  These are of the same form as used in the ``select`` endpoint.

The ``GET`` ``file/{id}/database`` endpoint reports the values set with POST.

The ``GET`` ``file/{id}/database/fields`` endpoint reports a list of known fields and their datatypes.

The ``GET`` ``file/{id}/database/select`` endpoint performs queries and returns data.  See its documentation for more information.  If the data in the database is actively changing, polling can be used to wait for data to appear.

The ``PUT`` ``file/{id}/database/refresh`` endpoint should be used if the available fields (columns) or functions of a database have changed.

When downloading a file or item in Girder that uses a database assetstore, clients that are unaware of the database options get the results as the default query for the file.  The query can be modified by adding ``extraParameters`` to the download endpoint, so that ``GET`` ``item/{id}/download?extraParameters=<url encoded parameters>`` can be used to change the returned data.  The parameters can be any of the select options.  All of the select parmeters are url-encoded so that they can be passed as a single value to ``extraParameters``.

Select Options
==============

The ``GET`` ``file/{id}/database/select`` endpoint has numerous options:

* *limit* - how many results to return.  0 for none (this stills performs the select).  Default is 50.
* *offset* - the offset to the first result to return.  Not really useful unless a sort is applied.
* *sort* - either a single field (column) name, in which case the *sortdir* option is used, **or** a comma-separated list of field names, **or** a JSON list of sort parameters.  When using a JSON list, each entry in the list can either be a column name, or can be a list with the first value the column name (or a function), and the second value the sort direction.

  For instance, ``type,town``, ``["type","town"]``, ``[["type",1],["town",1]]`` all sort the output first by type and then by town, both ascending.

  An example of a sort using a function: ``["type", [{"func": "lower", "param": {"field": "town"}}, -1]]`` will sort first by ascending type then by descending lower-case town.

* *sortdir* - this is only used if a single sort field is given in *sort*.  A positive number will sort in ascending order; a negative number in descending order.

* *fields* - the list of field (columns) to return.  By default, all known fields are returned in an arbitrary order.  This ensures a particular order and will only return the specified fields.  This may be either a comma-separated list of field names **or** a JSON list with either field names or functions.  If a function is specified, it can be given a ``reference`` key that will be used as a column name.

  An example of fetching fields including a function: ``["town", {"func": "lower", "param": {"field": "town"}, "reference": "lowertown"}]``

* *group* - an optional list of field (columns) used to group results.  This has the same format as the *fields* parameter.  This is equivalent to SQL ``GROUP BY``.  If it is used, the fields that are returned must either be fields used in the grouping or must be transformed using an aggregation function.

* *filters* - a JSON list of filters to apply.  Each filter is a list or an object.  If a list, the filter is of the form [(field or object with function or value), (operator), (value or object with field, function, or value)].  If a filter is specified with an object, it needs either "field", "func" and "param", or "lvalue" for the left side, "operator", and either "value" or "rfunc" and "rparam" for the right side.  The operator is optional, and if not specified is the equality test.  The "field" and "value" entries can be objects with "field", "value" or "func" and "param".

  Alternately, a filter can be a group of filters that are combined via either "and" or "or".  A grouping filter must be an object, either with "group" specifying "and" or "or" and "value" containing a list of filters, or with a single key of either "and" or "or" which contains a list of filters.  Grouping filters can be nested to any depth.

  A single filter may be used instead of a list of filters as the main object or as the value parameter of a filter group, but only if the single filter is itself and object or a list whose first eleemnt is a string.

  Operators are dependant of field datatypes and the database connector that is used.  The following operators are available:

  * eq (=)
  * ne (!=, <>)
  * gte (>=, min)
  * gt (>)
  * lt (<, max)
  * lte (<=)
  * in - can have a list of values on the right side
  * not_in (notin) - can have a list of values on the right side
  * regex (~)
  * not_regex (notregex, !~)
  * search (~*) - generally a case-insensitive regex.  Some connectors could implement a stemming search instead
  * not_search (notsearch, !~*)
  * is 
  * notis (not_is, isnot, is_not)

  Example filters:
  
  * ``[["town", "BOSTON"]]`` - the town field must equal "BOSTON".
  * ``[{"field": "town", "operator": "eq", "value": "BOSTON"}]`` - the same filter as the previous one, just constructed differently.
  * ``[{"lvalue": "BOSTON", "value": {"field": "town"}}]`` - yet another way to construct the same filter.
  * ``[{"func": "lower", "param": [{"field": "town"}], "value": "boston"}]`` - the lower-case version of the town field must equal "boston".
  * ``[["pop2010", ">", 100000], {"field": "town", "operator": "ne", "value": "BOSTON"}]`` - the population in 2010 must be greater than 100,000, but don't mention Boston.
  * ``[{"or": [["town", "BOSTON"], ["pop2010", "<", "4000"]]}]`` - the town field must equal "BOSTON" *OR* the population in 2010 must be less than 4000.
  * ``[{"group: "or", "value": [["town", "BOSTON"], ["pop2010", "<", "4000"]]}]`` - another way to construct the previous filter.

* *format* - data can be returned in a variety of formats:

  * ``list`` - a list of lists, where each entry is a list of the returned fields.  There is information about the query and fields in some top-level keys.  This is usually the most efficient return method.
  
  * ``dict`` - a list of dictionaries, where each entry is a map of the field names and the values.  There is information about the query and fields in some top-level keys.

  * ``csv`` - a comma-separated value text format.

  * ``json`` - the same as ``dict`` without the top-level information.

  * ``jsonlines`` - each row is a stand-alone JSON object.

  * ``geojson`` - any value that could be GeoJSON is combined into a single ``GeometryCollection`` or ``FeatureCollection`` object.  The result is a ``FeatureCollection`` if the first row contains a ``Feature``.  Values that are not GeoJSON are ignored.  This is only useful if the database returns GeoJSON strings or dictionaries.  All values in all rows are combined together in order.

    For instance, when using a Postgres database with the PostGIS extension, if there is a column with geometry information called ``geom``, asking for the GeoJSON output of the fields ``[{"func": "ST_AsGeoJSON", "param": [{"func": "st_transform", "param": [{"field": "geom"}, 4326]}]}]`` would get a single GeoJSON object of all of the rows in the EPSG:4326 coordinate system.

* *clientid* - an optional client ID can be specified with each request.  If this is included, and there is a pending select request from the same client ID, the pending request will be cancelled if possible.  This can be used when a client no longer needs the data from a first request because the new request will replace it.

* *wait* - if the data source is being actively changed, select can poll it periodically until there is data available.  If specified, this is a duration in seconds to poll the data.  As soon as data is found, it is returned.  If no data is found, the results are the same as not using wait.

* *poll* - if *wait* is used, this is the interval in seconds to check if data has changed based on the other select parameters.  Making this value too small will produce a high load on the database server.

* *initwait* - if *wait* is used, don't check for data for this duration in seconds, then start polling.  This can be used to reduce server load.

Database Functions
------------------

The ``sort``, ``fields``, ``group``, and ``filters`` select parameters can use database functions.  Only non-internal, non-volatile functions are permitted.  For instance, when using Postgresql, you cannot use ``pg_*`` functions, nor a function like ``nextval``.

Functions can be nested -- a function can be used as the parameter of another function.

When using a SQL database, ``distinct``, ``cast``, and ``count`` are always available as functions.  When ``distinct`` is used as a field, it must be the first field in field list, and other fields usually need to be the result of aggregate functions.  ``cast`` takes two parameters; the first if the data to cast and the second is the name of the datatype, which is typically a string in all capital letters, such as ``INT`` or ``TEXT``.

When using a Postgres database, many Postgres operations are exposed as functions.  For instance, using ``float8mul`` allows double-precision multiplication.

If a function takes a single parameter, the ``param`` value can be a single item.  Otherwise, it is a list of the values for the function.

Anywhere a function can be used (which includes the parameters of another function), a field (column) or a specified value can be used instead: ``{"field": (name of field)`` or ``{"value": (value)}``.

Here is example of a filter with a nested function (using PostGIS functions):

``[{"func": "st_intersects", "param": [{"func": "st_setsrid", "param": [{"func": "st_makepoint", "param": [-72, 42.36]}, 4326]}, {"func": "st_transform", "param": [{"field": "geom"}, 4326]}], "operator": "is", "value": true}]``

SQLite on Files Stored in Girder
--------------------------------

SQLite works with files rather than a database server.  To specify a file that is in Girder's local file system, use a Database URI of ``sqlite://<absolute path to file>`` (e.g., ``sqlite:///home/pliny/natural_history/zoology.db``).

SQLLite can also work with files stored in a Girder filesystem assetstore.  Instead of a local file path, use a Girder resource path.  This will be of the form ``sqlite:///<'user' or 'collection'>/<user or collection name>/<folder name>/[<subfolder name>/ ...]<item name>/<file name>``.  For example ``sqlite:///user/pliny/Public/Natural History/zoology.db/zoology.db``.


Installation
------------

To install this plugin in girder, use a command like ``girder-install plugin . --symlink --dev`` from within the root repository directory.  This won't install extras_require packages.  To add those, use something like `pip install -e .[mysql,postgres,sqlite]` with just the desired list of supported databases, or `pip install -e .[all]` for all extras.
