from flask import render_template, redirect
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView
from .models import SchedulableOperation, ScheduledOperation
from .schema import get_schema, get_function_test_schema
from wtforms import StringField, SelectField

from .addon_scheduler import AddonScheduler

from datetime import datetime

from fab_addon_turbowidgets.widgets import JsonEditorWidget

from flask_appbuilder.actions import action

import logging

log = logging.getLogger(__name__)

"""
    Create your Views (but don't register them here, do it on the manager::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)

    
"""

class ScheduledOperationView(ModelView):
    datamodel = SQLAInterface(ScheduledOperation)
    scheduler_schema = get_schema()
    function_test_schema = get_function_test_schema()
    before_js = ""
    # Pre-fill the date when changing the 'trigger' in the JsonEditor
    after_js = (
        "function watchMode() {"
            "dt = new Date();"
            "dt_formatted = `${"
            "dt.getFullYear().toString().padStart(4, '0')}/${"
            "dt.getMonth().toString().padStart(2, '0')}/${"
            "(dt.getDate()+1).toString().padStart(2, '0')} ${"
            "dt.getHours().toString().padStart(2, '0')}:${"
            "dt.getMinutes().toString().padStart(2, '0')}:${"
            "dt.getSeconds().toString().padStart(2, '0')}`;"
            " newmode=this.getEditor('root.trigger').getValue();"
            " default_value = {};"
            " switch(newmode) {"
            "  case 'interval': " 
            "    default_value = {weeks:0, days:1, hours:0, minutes:0, seconds:0, start_date:dt_formatted, end_date:dt_formatted};"
            "    break; " 
            "  case 'cron': " 
            "    default_value = {year:'*', month:'*', day:'*', week:'*', day_of_week:'*', hour:'*', minute:'5', second:'*', start_date:dt_formatted, end_date:dt_formatted};"
            "    break; " 
            "  case 'date': " 
            "    default_value = {run_date:dt_formatted};"
            "    break; " 
            " }"
            "current_value = this.getValue();"
            "current_value = Object.keys(current_value).forEach(key => current_value[key] === undefined && delete current_value[key]);"
            "newval = {...default_value, ...current_value, trigger:newmode};"
            "this.setValue(newval);"
        "}"
        "editor_scheduler_arg.watch('root.trigger',watchMode.bind(editor));"
    )

    before_js2 = ""
    after_js2 = ""
    edit_form_extra_fields = {
        "scheduler_args": StringField(
            "Scheduler",
            widget=JsonEditorWidget(scheduler_schema, before_js, after_js),
        ),
        "operation_args": StringField(
            "OperationArgs",
            widget=JsonEditorWidget(function_test_schema, before_js2, after_js2),
        ),
    }
    add_form_extra_fields = edit_form_extra_fields

    list_columns = ['operation_name','schedule_enabled']


    @action("enableOperation","Enable tasks scheduling","Confirm activation of selected tasks ?","fa-rocket", single=False, multiple=True)
    def enableOperation(self, items):
        scheduler = AddonScheduler.get_scheduler()
        if scheduler:
            for item in items:
                item.activate(scheduler)
            self.update_redirect()
        return redirect(self.get_redirect())

    @action("disableOperation","Disable tasks scheduling","Confirm deactivation of selected tasks ?","fa-rocket", single=False, multiple=True)
    def disableOperation(self, items):
        scheduler = AddonScheduler.get_scheduler()
        if scheduler:
            for item in items:
                item.deactivate(scheduler)
        self.update_redirect()
        return redirect(self.get_redirect())

    def __activate_operation_if_required(self, item):
        if item.schedule_enabled == "Yes":
            item.activate(AddonScheduler.get_scheduler())
        else:
            item.deactivate(AddonScheduler.get_scheduler())

    def post_update(self, item):
        self.__activate_operation_if_required(item)

    def process_form(self, form, is_created):
        pass

    def post_add(self, item):
        self.__activate_operation_if_required(item)

class SchedulableOperationView(ModelView):
    datamodel = SQLAInterface(SchedulableOperation)
    related_views = [ScheduledOperationView]

