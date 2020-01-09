from flask import render_template, redirect, url_for
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView
from .models import SchedulableOperation, ScheduledOperation, ListOfOperations
from .schema import get_scheduler_schema
from wtforms import StringField, SelectField

from flask_appbuilder import BaseView, expose, has_access

from .addon_scheduler import AddonScheduler, SCHEDULER_TIMEZONE, SCHEDULER_SELFCHECK_INTERVAL, scheduler_selfcheck

from datetime import datetime
import pytz

from fab_addon_turbowidgets.widgets import JsonEditorWidget

from flask_appbuilder.actions import action

import logging
import json

utc=pytz.UTC

log = logging.getLogger(__name__)

"""
    Create your Views (but don't register them here, do it on the manager::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)

    
"""


def get_operation_args_schema_js():
    list_oper_schema_json = json.dumps(ListOfOperations.get_dict())
    before_js2 = "list_operations_schema = JSON.parse('{}')".format(list_oper_schema_json)
    return before_js2

class ScheduledOperationView(ModelView):
    datamodel = SQLAInterface(ScheduledOperation)
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
        "editor_scheduler_args.watch('root.trigger',watchMode.bind(editor_scheduler_args));"
        "editor_scheduler_args_init = watchMode.bind(editor_scheduler_args);"
        "editor_scheduler_args_init();"
    )

    after_js2 = ""
    edit_form_extra_fields = {
        "scheduler_args": StringField(
            "Scheduler",
            widget=JsonEditorWidget(get_scheduler_schema, before_js, after_js),
        ),
        "operation_args": StringField(
            "OperationArgs",
            widget=JsonEditorWidget("{}", before_js=get_operation_args_schema_js, after_js=after_js2, master_id="operation", extra_classes="fab_addon_operation_manager_opargs"),
        ),
    }
    add_form_extra_fields = edit_form_extra_fields

    list_columns = ['operation_name','schedule_enabled','status']


    @action("enableOperation","Enable tasks scheduling","Confirm activation of selected tasks ?","fa-rocket", single=False, multiple=True)
    def enableOperation(self, items):
        scheduler = AddonScheduler.get_scheduler()
        if scheduler:
            for item in items:
                item.schedule_enabled = "Yes"
                self.datamodel.edit(item)
                item.activate(scheduler)
            self.update_redirect()
        return redirect(self.get_redirect())

    @action("disableOperation","Disable tasks scheduling","Confirm deactivation of selected tasks ?","fa-rocket", single=False, multiple=True)
    def disableOperation(self, items):
        scheduler = AddonScheduler.get_scheduler()
        if scheduler:
            for item in items:
                item.schedule_enabled = "No"
                self.datamodel.edit(item)
                item.deactivate(scheduler)
        self.update_redirect()
        return redirect(self.get_redirect())

    def __activate_operation_if_required(self, item):
        try:
            print(item)
        except Exception as e:
            print(e)
        if item.schedule_enabled == "Yes":
            log.debug("Must activate {}".format(item))
            item.activate(AddonScheduler.get_scheduler())
        else:
            log.debug("Must DE-activate {}".format(item))
            item.deactivate(AddonScheduler.get_scheduler())

    def prefill_form(self, form, pk):
        pass

    def post_update(self, item):
        self.__activate_operation_if_required(item)

    def process_form(self, form, is_created):
        pass

    def post_add(self, item):
        self.__activate_operation_if_required(item)

class SchedulableOperationView(ModelView):
    datamodel = SQLAInterface(SchedulableOperation)
    related_views = [ScheduledOperationView]


class SchedulerManagerView(BaseView):
    route_base = "/fab_addon_opseched_schedulermanager"
    default_view = 'manager'
    state_to_string =  ["STATE_STOPPED", "STATE_RUNNING","STATE_PAUSED"]

    @expose("/manager/")
    @has_access
    def manager(self):
        scheduler = AddonScheduler.get_scheduler()
        state = scheduler.state
        jobs=scheduler.get_jobs()
        #scheduler.scheduler.print_jobs()
        jobs_str=""
        jobs_info = []
        for job in jobs:
            #trig = job.trigger
            #trig_next_date = trig.get_next_fire_time(None, datetime.now(utc)).strftime("%Y-%m-%d %H:%M:%S")
            trig_next_date = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
            jobs_str += "{} (next at {}),".format(job.name,trig_next_date)
            jobs_info.append({
                'job_name':job.name,
                'job_next_start': trig_next_date
            })
            
        schedulers_info = [
            {
                'scheduler_name': 'default_scheduler',
                'scheduler_state': self.state_to_string[state],
                'scheduler_jobs': jobs_str
            }
        ]
        #return self.render_template("fab_addon_operation_scheduler/operation_scheduler_management.html", schedulers=schedulers_info)
        return self.render_template("operation_scheduler_management.html", scheduler_status= self.state_to_string[state], scheduler_jobs=jobs_info)

    @expose("/pause/")
    @has_access
    def pause(self):
        scheduler = AddonScheduler.get_scheduler()
        #AddonScheduler.remove_all_jobs()
        scheduler.pause()
        return redirect(url_for('SchedulerManagerView.manager'))
        return redirect(self.get_redirect())

    @expose("/resume/")
    @has_access
    def resume(self):
        scheduler = AddonScheduler.get_scheduler()
        scheduler.resume()
        return redirect(url_for('SchedulerManagerView.manager'))
        return redirect(self.get_redirect())

    @expose("/shutdown/")
    @has_access
    def shutdown(self):
        scheduler = AddonScheduler.get_scheduler()
        #AddonScheduler.remove_all_jobs()
        if scheduler.running:
            scheduler.shutdown()
        return redirect(url_for('SchedulerManagerView.manager'))

    @expose("/start/")
    @has_access
    def start(self):
        scheduler = AddonScheduler.get_scheduler()
        if self.state_to_string[scheduler.state] == "STATE_STOPPED":
            scheduler.start(paused=False)
        log.debug("APScheduler: adding selfcheck task")
        selfcheck_job = AddonScheduler.get_job('selfcheck')
        if selfcheck_job:
            selfcheck_job.remove()
        AddonScheduler.add_job('selfcheck', scheduler_selfcheck, trigger='interval', seconds=SCHEDULER_SELFCHECK_INTERVAL, max_instances=6, misfire_grace_time=SCHEDULER_SELFCHECK_INTERVAL)
        db = ListOfOperations.db
        ListOfOperations.reschedule_operations(db)
        return redirect(url_for('SchedulerManagerView.manager'))
