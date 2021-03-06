(function($) {
    'use strict';

    var initBasicTableClaims = function() {
        var table = $('#basicTableClaims');
        var settings = {
            "sDom": "t",
            "destroy": true,
            "paging": false,
            "scrollCollapse": true,
            // "aoColumnDefs": [{
            //     'bSortable': false,
            //     'aTargets': [0]
            // }],
            "order": [
                [0, "desc"]
            ]
        };
        table.dataTable(settings);
        $('#basicTableClaims input[type=checkbox]').click(function() {
            if ($(this).is(':checked')) {
                $(this).closest('tr').addClass('selected');
            } else {
                $(this).closest('tr').removeClass('selected');
            }
        });
    }
    
        var initBasicTableBenefits = function() {
        var table = $('#basicTableBenefits');
        var settings = {
            "sDom": "t",
            "destroy": true,
            "paging": false,
            "scrollCollapse": true,
            // "aoColumnDefs": [{
            //     'bSortable': false,
            //     'aTargets': [0]
            // }],
            "order": [
                [0, "desc"]
            ]
        };
        table.dataTable(settings);
        $('#basicTableBenefits input[type=checkbox]').click(function() {
            if ($(this).is(':checked')) {
                $(this).closest('tr').addClass('selected');
            } else {
                $(this).closest('tr').removeClass('selected');
            }
        });
    }
    
        var initBasicTableCommunication = function() {
        var table = $('#basicTableCommunication');
        var settings = {
            "sDom": "t",
            "destroy": true,
            "paging": false,
            "scrollCollapse": true,
            // "aoColumnDefs": [{
            //     'bSortable': false,
            //     'aTargets': [0]
            // }],
            "order": [
                [0, "desc"]
            ]
        };
        table.dataTable(settings);
        $('#basicTableCommunication input[type=checkbox]').click(function() {
            if ($(this).is(':checked')) {
                $(this).closest('tr').addClass('selected');
            } else {
                $(this).closest('tr').removeClass('selected');
            }
        });
    }


    var initBasicTable = function() {
        var table = $('#basicTable');
        var settings = {
            "sDom": "t",
            "destroy": true,
            "paging": false,
            "scrollCollapse": true,
            // "aoColumnDefs": [{
            //     'bSortable': false,
            //     'aTargets': [0]
            // }],
            "order": [
                [0, "desc"]
            ]
        };
        table.dataTable(settings);
        $('#basicTable input[type=checkbox]').click(function() {
            if ($(this).is(':checked')) {
                $(this).closest('tr').addClass('selected');
            } else {
                $(this).closest('tr').removeClass('selected');
            }
        });
    }
    
    
    
    
    var initBasicTableUsers = function() {
        var table = $('#basicTableUsers');
        var settings = {
            "sDom": "t",
            "destroy": true,
            "paging": false,
            "scrollCollapse": true,
            // "aoColumnDefs": [{
            //     'bSortable': false,
            //     'aTargets': [0]
            // }],
            "order": [
                [2, "desc"]
            ]
        };
        table.dataTable(settings);
        $('#basicTableUsers input[type=checkbox]').click(function() {
            if ($(this).is(':checked')) {
                $(this).closest('tr').addClass('selected');
            } else {
                $(this).closest('tr').removeClass('selected');
            }
        });
    }
    var initStripedTable = function() {
        var table = $('#stripedTable');
        var settings = {
            "sDom": "t",
            "destroy": true,
            "paging": false,
            "scrollCollapse": true
        };
        table.dataTable(settings);
    }
    var initDetailedViewTable = function() {
        var _format = function(d) {
            return '<table class="table table-inline">' + '<tr>' + '<td>Learn from real test data <span class="label label-important">ALERT!</span></td>' + '<td>USD 1000</td>' + '</tr>' + '<tr>' + '<td>PSDs included</td>' + '<td>USD 3000</td>' + '</tr>' + '<tr>' + '<td>Extra info</td>' + '<td>USD 2400</td>' + '</tr>' + '</table>';
        }
        var table = $('#detailedTable');
        table.DataTable({
            "sDom": "t",
            "scrollCollapse": true,
            "paging": false,
            "bSort": false
        });
        $('#detailedTable tbody').on('click', 'tr', function() {
            if ($(this).hasClass('shown') && $(this).next().hasClass('row-details')) {
                $(this).removeClass('shown');
                $(this).next().remove();
                return;
            }
            var tr = $(this).closest('tr');
            var row = table.DataTable().row(tr);
            $(this).parents('tbody').find('.shown').removeClass('shown');
            $(this).parents('tbody').find('.row-details').remove();
            row.child(_format(row.data())).show();
            tr.addClass('shown');
            tr.next().addClass('row-details');
        });
    }
    var initCondensedTable = function() {
        var table = $('#condensedTable');
        var settings = {
            "sDom": "t",
            "destroy": true,
            "paging": false,
            "scrollCollapse": true
        };
        table.dataTable(settings);
    }
    initBasicTableClaims();
    initBasicTableBenefits();
    initBasicTableCommunication();
    initBasicTable();
    initBasicTableUsers();
    initStripedTable();
    initDetailedViewTable();
    initCondensedTable();
})(window.jQuery);
