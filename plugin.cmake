# We can't use the standard server tests since we have data files
add_standard_plugin_tests(NO_SERVER_TESTS)

add_python_style_test(python_static_analysis_${_pluginName}_tests "${_pluginDir}/plugin_tests")

add_python_test(assetstore PLUGIN database_assetstore BIND_SERVER EXTERNAL_DATA "plugins/database_assetstore/testdb.sql.gz")
add_python_test(dbs_mongo PLUGIN database_assetstore BIND_SERVER EXTERNAL_DATA "plugins/database_assetstore/mongodb.permits.json.bz2")
add_python_test(dbs_mysql PLUGIN database_assetstore BIND_SERVER)
add_python_test(dbs_sqlite PLUGIN database_assetstore BIND_SERVER EXTERNAL_DATA "plugins/database_assetstore/chinook_subset.db.bz2")
set_property(TEST server_database_assetstore.dbs_sqlite APPEND PROPERTY ENVIRONMENT
  "DATABASE_ASSETSTORE_DATA=${PROJECT_BINARY_DIR}/data/plugins/database_assetstore")
add_python_test(file PLUGIN database_assetstore BIND_SERVER EXTERNAL_DATA "plugins/database_assetstore/testdb.sql.gz")
