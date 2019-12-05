function loadJsonEditorSlaves(elem) {
    $(".fab_addon_operation_manager_opargs").each(function( index ) {
        var elem = $(this);
        var master_id = elem.attr('master_id');
        var master_val = $('#' + master_id).val();
        if (master_val) {
                master_schema = list_operations_schema[master_val]
                theEditor = listOfJsonEditors['operation_args']
                theEditor.destroy();
                console.log(JSON.stringify(master_schema))
                listOfJsonEditors['operation_args'] = init_json_editor('operation_args',JSON.stringify(master_schema),"{}","{}")
        }
        else {
        }
        $('#' + master_id).on("change", function(e) {
            if (e.val) {
                console.log(list_operations_schema[e.val])
                master_schema = list_operations_schema[e.val]
                theEditor = listOfJsonEditors['operation_args']
                theEditor.destroy();
                console.log(JSON.stringify(master_schema))
                listOfJsonEditors['operation_args'] = init_json_editor('operation_args',JSON.stringify(master_schema),"{}","{}")
            }
        })
    });
}

$(document).ready(function() {
    loadJsonEditorSlaves();
});

