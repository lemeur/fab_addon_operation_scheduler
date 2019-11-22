import json

from flask_appbuilder import Model
from flask_appbuilder.models.mixins import AuditMixin, FileColumn, ImageColumn
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship


class ListOfOperations:
    members = dict()

    @classmethod
    def register_operation(cls, db, name, description, func, args_schema={}):
        cls.members[name]={'name': name, 'description': description, 'function': func, 'args_schema': args_schema}
        schedop = SchedulableOperation(name, description, json.dumps(args_schema))
        db.session.add(schedop)
        db.session.commit()

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

    def enable_schedule(self):
        self.schedule_enabled = 1
        pass

    def disable_schedule(self):
        self.schedule_enabled = 0
        pass
