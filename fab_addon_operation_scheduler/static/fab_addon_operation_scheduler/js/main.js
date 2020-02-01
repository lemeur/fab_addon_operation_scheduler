function loadJsonEditorSlaves(elem) {
    $(".fab_addon_operation_manager_opargs").each(function( index ) {
        var elem = $(this);
        var master_id = elem.attr('master_id');
        var master_val = $('#' + master_id).val();
        if (master_val) {
                master_schema = list_operations_schema[master_val]
                theEditor = listOfJsonEditors['operation_args']
                theEditor.destroy();
                // master_schema might be undefined if there is no selected value
                if (master_schema !== undefined && Object.keys(master_schema).length != 0) {
                    //console.log(JSON.stringify(master_schema))
                    //listOfJsonEditors['operation_args'] = init_json_editor('operation_args',JSON.stringify(master_schema),"{}","{}")
                    starting_value = $('#operation_args').attr('value')
                    if (starting_value == "" || starting_value == "None") {
                        listOfJsonEditors['operation_args'] = init_json_editor('operation_args',JSON.stringify(master_schema),"{}","{}")
                    }
                    else {
                        listOfJsonEditors['operation_args'] = init_json_editor('operation_args',JSON.stringify(master_schema),starting_value,"{}")
                    }
                }
        }
        else {
        }
        $('#' + master_id).on("change", function(e) {
            if ($(e.target).val()) {
                //console.log(list_operations_schema[e.val])
                master_schema = list_operations_schema[$(e.target).val()]
                theEditor = listOfJsonEditors['operation_args']
                theEditor.destroy();
                starting_value = $('#operation_args').attr({value: ""})
                $('#operation_args').val('')
                if (master_schema !== undefined &&  Object.keys(master_schema).length != 0) {
                    //console.log(JSON.stringify(master_schema))
                    listOfJsonEditors['operation_args'] = init_json_editor('operation_args',JSON.stringify(master_schema),"{}","{}")
                }
            }
        })
    });
}

$(document).ready(function() {
    loadJsonEditorSlaves();
});

