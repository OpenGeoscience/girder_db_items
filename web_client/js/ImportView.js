girder.views.dbas_assetstore_ImportView = girder.View.extend({
    events: {
        'submit .g-dbas-import-form': function (e) {
            e.preventDefault();
            this.$('.g-validation-failed-message').empty();
            this.$('.g-submit-dbas-import').addClass('disabled');

            var parentType = this.$('#g-dbas-import-dest-type').val(),
                parentId = this.$('#g-dbas-import-dest-id').val(),
                tableValue = this.$('#g-dbas-table-name').val() || [],
                tables = [], entry, value, i;
            for (i = 0; i < tableValue.length; i += 1) {
                value = tableValue[i];
                entry = '';
                if (value.indexOf('database:') === 0) {
                    entry = {};
                    value = value.substr(9);  // remove 'database:'
                    if (value.indexOf(':table:') >= 0) {
                        entry['name'] = value.substr(value.indexOf(':table:') + 7);
                        value = value.substr(0, value.indexOf(':table:'));
                    }
                    entry['database'] = value;
                }
                tables.push(entry);
            }
            this.model.off().on('g:imported', function () {
                girder.router.navigate(parentType + '/' + parentId, {trigger: true});
            }, this).on('g:error', function (err) {
                this.$('.g-submit-dbas-import').removeClass('disabled');
                this.$('.g-validation-failed-message').text(err.responseJSON.message);
            }, this).databaseImport({
                table: JSON.stringify(tables),
                sort: this.$('#g-dbas-sort-param').val(),
                fields: this.$('#g-dbas-fields-param').val(),
                filters: this.$('#g-dbas-filters-param').val(),
                limit: this.$('#g-dbas-limit-param').val(),
                format: this.$('#g-dbas-format-param').val(),
                parentType: parentType,
                parentId: parentId,
                progress: true
            });
        }
    },

    initialize: function () {
        this.model
            .off('g:error').once('g:error', function (err) {
                girder.events.trigger('g:alert', {
                    icon: 'cancel',
                    text: err.responseJSON.message,
                    type: 'danger'
                });
                girder.router.navigate('assetstores', {trigger: true});
            })
            .off('g:databaseGetTables').on('g:databaseGetTables',
                function (resp) {
                    this.tableList = resp;
                    this.render();
                }, this)
            .databaseGetTables();
    },

    render: function () {
        this.$el.html(girder.templates.db_assetstore_import({
            assetstore: this.model,
            tableList: this.tableList
        }));
    }
});

girder.router.route('database_assetstore/:id/import', 'dbasImport', function (id) {
    // Fetch the folder by id, then render the view.
    var assetstore = new girder.models.AssetstoreModel({
        _id: id
    }).once('g:fetched', function () {
        girder.events.trigger('g:navigateTo', girder.views.dbas_assetstore_ImportView, {
            model: assetstore
        });
    }).once('g:error', function () {
        girder.router.navigate('assetstores', {trigger: true});
    }).fetch();
});
