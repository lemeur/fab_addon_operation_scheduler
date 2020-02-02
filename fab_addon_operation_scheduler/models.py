import json

from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError

import logging

log = logging.getLogger(__name__)


class ScheduledOperation(Model):
    id = Column(Integer, primary_key=True)
    operation = Column(String(200), nullable=True)
    operation_args = Column(String(200), nullable=True)
    scheduler_args = Column(String(200), nullable=True)
    schedule_enabled = Column(Enum('Yes','No'), unique=False, nullable=False, default='No')
    status = Column(String(200), default="Unregistered")

    def __repr__(self):
        trigger = "Unknown"
        try:
            scheduler_args_dict = json.loads(self.scheduler_args)
            trigger = scheduler_args_dict['trigger']
        except:
            pass

        return "{} {}({})".format(self.operation, trigger, self.scheduler_args)

    def get_dict(self):
        return {'id':self.id, 'operation':self.operation, 'operation_args':self.operation_args, 'scheduler_args':self.scheduler_args}

    def activate(self, addon_scheduler):
        jobid = "{}-{}".format(str(self.id),self.operation)
        is_job_activated = addon_scheduler.is_job_activated(jobid)
        taskSchedulerArgs = json.loads(self.scheduler_args)

        if 'start_date' in taskSchedulerArgs and taskSchedulerArgs['start_date'] == "":
            del taskSchedulerArgs['start_date']
        if 'end_date' in taskSchedulerArgs and taskSchedulerArgs['end_date'] == "":
            del taskSchedulerArgs['end_date']

        operation_function = addon_scheduler.get_func(self.operation)

        if operation_function:
            if is_job_activated:
                addon_scheduler.remove_job(jobid)
                self.status="Unregistered"

            if self.operation_args:
                try:
                    operation_args_dict = json.loads(self.operation_args)
                    addon_scheduler.add_job(jobid, operation_function, **taskSchedulerArgs, max_instances=6, kwargs=operation_args_dict)
                    self.status="Registered"
                except Exception as e:
                    log.error("Error activating '{}' with error '{}'".format(self.operation, e))
                    self.status="Error '{}'".format(self.operation, e)
            else:
                try:
                    addon_scheduler.add_job(jobid, operation_function, **taskSchedulerArgs, max_instances=6)
                    self.status="Registered"
                except Exception as e:
                    log.error("Error activating '{}' with error '{}'".format(self.operation, e))
                    self.status="Error '{}'".format(self.operation, e)
        else:
            log.debug("APScheduler can't find oper function for:"+self.operation)

        log.debug("APScheduler jobs after ADD:'{}'".format(";".join(addon_scheduler.get_job_ids())))

    def deactivate(self, addon_scheduler):
        jobid = "{}-{}".format(str(self.id),self.operation)
        is_job_activated = addon_scheduler.is_job_activated(jobid)
        if is_job_activated:
            addon_scheduler.remove_job(jobid)
            self.status="Unregistered"
        log.debug("APScheduler jobs after REMOVE:'{}'".format(";".join(addon_scheduler.get_job_ids())))
