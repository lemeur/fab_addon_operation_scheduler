import json

from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError

from .addon_scheduler import AddonScheduler

import logging

log = logging.getLogger(__name__)



##class ListOfOperations:
##    members = dict()
##    db = None
##
##    @classmethod
##    def register_operation(cls, db, name, description, func, args_schema={}):
##        log.debug('APScheduler registering new function:'+name)
##        cls.members[name]={'name': name, 'description': description, 'function': func, 'args_schema': args_schema}
##        #try:
##            #schedop = SchedulableOperation(name, description, json.dumps(args_schema))
##            #cls.db= db
##            #db.session.add(schedop)
##            #db.session.commit()
##        #except IntegrityError:
##        #    log.debug("APScheduler already registered function:"+name)
##        #    db.session.rollback()
##
##        #jobs_to_activate = db.session.query(ScheduledOperation).filter(ScheduledOperation.schedule_enabled == "Yes").filter(ScheduledOperation.operation_name == name).all()
##        jobs_to_activate = db.session.query(ScheduledOperation).filter(ScheduledOperation.schedule_enabled == "Yes").filter(ScheduledOperation.operation == name).all()
##        for j in jobs_to_activate:
##            log.debug('APScheduler activating job "{}" for function "{}":'.format(str(j.id)+"-"+j.operation_name, name))
##            scheduler = AddonScheduler()
##            j.activate(scheduler)
##
##    @classmethod
##    def list_names(cls):
##        list_of_names = [k['name'] for k in cls.members]
##        return list_of_names
##
##    @classmethod
##    def reschedule_operations(cls, db):
##        jobs_to_activate = db.session.query(ScheduledOperation).filter(ScheduledOperation.schedule_enabled == "Yes").all()
##        scheduler = AddonScheduler()
##        for j in jobs_to_activate:
##            if j.operation_name in cls.members:
##                j.activate(scheduler)
##
##    @classmethod
##    def get_all(cls):
##        return cls.members
##
##    @classmethod
##    def get_one(cls, name):
##        if name in cls.members:
##            return cls.members[name]
##        else:
##            return None
##
##    @classmethod
##    def get_dict(cls):
##        res = {k:cls.members[k]['args_schema'] for k in cls.members}
##        return res
##            


#class SchedulableOperation(Model):
#    oper_name = Column(String(50), primary_key=True)
#    oper_description = Column(String(500), nullable=True)
#    oper_schema = Column(String(900), nullable=True)
#
#    def __init__(self, name, description, args_schema):
#        self.oper_name = name
#        self.oper_description = description
#        self.oper_schema = args_schema
#
#    def __repr__(self):
#        return self.oper_name

class ScheduledOperation(Model):
    id = Column(Integer, primary_key=True)
    #operation_name = Column(Integer, ForeignKey('schedulable_operation.oper_name'), nullable=True)
    #operation = relationship("SchedulableOperation")
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

        return "{} {}({})".format(self.operation_name, trigger, self.scheduler_args)

    def activate(self, addon_scheduler):
        jobid = "{}-{}".format(str(self.id),self.operation)
        is_job_activated = addon_scheduler.is_job_activated(jobid)
        taskSchedulerArgs = json.loads(self.scheduler_args)

        if 'start_date' in taskSchedulerArgs and taskSchedulerArgs['start_date'] == "":
            del taskSchedulerArgs['start_date']
        if 'end_date' in taskSchedulerArgs and taskSchedulerArgs['end_date'] == "":
            del taskSchedulerArgs['end_date']

        operation_function = addon_scheduler.get_func(self.operation_name)

        if operation_function:
            if is_job_activated:
                addon_scheduler.remove_job(jobid)
                self.status="Unregistered"

            try:
                addon_scheduler.add_job(jobid, operation_function, **taskSchedulerArgs, max_instances=6, kwargs=operation_args_dict)
                self.status="Registered"
            except Exception as e:
                log.error("Error activating '{}' with error '{}'".format(self.operation_name, e))
                self.status="Error '{}'".format(self.operation_name, e)
        else:
            log.debug("APScheduler can't find oper function for:"+self.operation_name)

        log.debug("APScheduler jobs after ADD:'{}'".format(";".join(addon_scheduler.get_job_ids())))

    def deactivate(self, addon_scheduler):
        jobid = "{}-{}".format(str(self.id),self.operation)
        is_job_activated = addon_scheduler.is_job_activated(jobid)
        if is_job_activated:
            addon_scheduler.remove_job(jobid)
            self.status="Unregistered"
        log.debug("APScheduler jobs after REMOVE:'{}'".format(";".join(addon_scheduler.get_job_ids())))
