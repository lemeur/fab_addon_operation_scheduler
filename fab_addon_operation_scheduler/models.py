import json

from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship

from .addon_scheduler import AddonScheduler

import logging

log = logging.getLogger(__name__)



class ListOfOperations:
    members = dict()

    @classmethod
    def register_operation(cls, db, name, description, func, args_schema={}):
        log.debug('APScheduler registering new function:'+name)
        cls.members[name]={'name': name, 'description': description, 'function': func, 'args_schema': args_schema}
        schedop = SchedulableOperation(name, description, json.dumps(args_schema))
        db.session.add(schedop)
        db.session.commit()

        jobs_to_activate = db.session.query(ScheduledOperation).filter(ScheduledOperation.schedule_enabled == "Yes").filter(ScheduledOperation.operation_name == name).all()
        for j in jobs_to_activate:
            log.debug('APScheduler activating job "{}" for function "{}":'.format(str(j.id)+"-"+j.operation_name, name))
            j.activate(AddonScheduler.get_scheduler())

    @classmethod
    def get_all(cls):
        return cls.members

    @classmethod
    def get_one(cls, name):
        if name in cls.members:
            return cls.members[name]
        else:
            return None


class SchedulableOperation(Model):
    oper_name = Column(String(50), primary_key=True)
    oper_description = Column(String(500), nullable=True)
    oper_schema = Column(String(900), nullable=True)

    def __init__(self, name, description, args_schema):
        self.oper_name = name
        self.oper_description = description
        self.oper_schema = args_schema

    def __repr__(self):
        return self.oper_name

class ScheduledOperation(Model):
    id = Column(Integer, primary_key=True)
    operation_name = Column(Integer, ForeignKey('schedulable_operation.oper_name'), nullable=True)
    operation = relationship("SchedulableOperation")
    operation_args = Column(String(200), nullable=True)
    scheduler_args = Column(String(200), nullable=True)
    schedule_enabled = Column(Enum('Yes','No'), unique=False, nullable=False, default='No')

    def __repr__(self):
        return "{} {}({})".format(self.operation_name, self.scheduler_trigger, self.scheduler_args)

    def activate(self, scheduler):
        self.schedule_enabled = "Yes"
        oper = ListOfOperations.get_one(self.operation_name)
        taskSchedulerArgs = json.loads(self.scheduler_args)
        if 'start_date' in taskSchedulerArgs and taskSchedulerArgs['start_date'] == "":
            del taskSchedulerArgs['start_date']
        if 'end_date' in taskSchedulerArgs and taskSchedulerArgs['end_date'] == "":
            del taskSchedulerArgs['end_date']
        if oper:
            current_job = scheduler.get_job(str(self.id)+'-'+self.operation_name)
            if current_job:
                current_job.remove()
            scheduler.add_job(str(self.id)+'-'+self.operation_name, oper['function'], **taskSchedulerArgs, max_instances=6)
        else:
            log.debug("APScheduler can't find oper for:"+self.operation_name)

        log.debug("APScheduler jobs after ADD:"+str([k.id for k in scheduler.get_jobs()]))

    def deactivate(self, scheduler):
        self.schedule_enabled = "No"
        oper = ListOfOperations.get_one(self.operation_name)
        taskSchedulerArgs = json.loads(self.scheduler_args)
        if oper:
            current_job = scheduler.get_job(str(self.id)+'-'+self.operation_name)
            if current_job:
                current_job.remove()
        log.debug("APScheduler jobs after REMOVE:"+str([k.id for k in scheduler.get_jobs()]))
