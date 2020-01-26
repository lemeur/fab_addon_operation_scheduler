from flask_apscheduler import APScheduler
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers import SchedulerAlreadyRunningError
from apscheduler.jobstores.base import ConflictingIdError

from ilock import ILock, ILockException


import errno
import rpyc
import time
from rpyc.utils.server import ThreadedServer
from rpyc.utils.helpers import classpartial

from datetime import datetime

import logging
log = logging.getLogger(__name__)

SCHEDULER_TIMEZONE="Europe/Paris"
SCHEDULER_SELFCHECK_INTERVAL=30
SCHEDULER_RPYC_PORT = 12345
SCHEDULER_RPYC_HOST = "localhost"

def scheduler_selfcheck():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    AddonScheduler().set_last_check(now)
    log.debug("fab_addon_operation_scheduler selfcheck:{}".format(now))

class SchedulerService(rpyc.Service):

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.available_operations = {}
        self.activated_jobs = {}

        try:
            with ILock('fab_addon_operation_manager_register_operation_lock', timeout=20):
                log.debug("AddonScheduler got Lock 'fab_addon_operation_manager_register_operation_lock'")

                if self.exposed_get_state_str() != "STATE_RUNNING":
                    log.debug("APScheduler: starting scheduler")
                    scheduler.start()
                    log.debug("APScheduler: scheduler STARTED scheduler")
                else:
                    log.debug("APScheduler: scheduler already STARTED")
        except ILockException:
            log.debug("SchedulerService: can't get ILock 'fab_addon_operation_manager_register_operation_lock'")

    def exposed_run_selfcheck(self):
        self.exposed_add_job('selfcheck', 'fab_addon_operation_scheduler.addon_scheduler:scheduler_selfcheck', trigger='interval', seconds=SCHEDULER_SELFCHECK_INTERVAL, max_instances=6, misfire_grace_time=SCHEDULER_SELFCHECK_INTERVAL)

    def exposed_add_job(self, jobid, func, *args, **kwargs):
        if not jobid or not self.scheduler:
            return None
        # Check if the 'func' takes any arguments (args or kwargs keys present inside this method kwargs)
        if 'kwargs' in kwargs:
            # transform the rpyc-netref of the 'func' kwargs to a static dict
            inside_kwargs_netref = kwargs['kwargs']
            inside_kwargs = {key: inside_kwargs_netref[key] for key in inside_kwargs_netref}
            kwargs['kwargs'] = inside_kwargs
        if 'args' in kwargs:
            # transform the rpyc-netref of the 'func' args to a static dict
            inside_args_netref = kwargs['args']
            inside_args = {key: inside_args_netref[key] for key in inside_args_netref}
            kwargs['args'] = inside_args

        try:
            with ILock('fab_addon_operation_manager_register_operation_lock', timeout=60):
                log.debug("SchedulerService adding scheduler job '{}'".format(jobid))
                if not self.activated_jobs.get(jobid,None):
                    self.activated_jobs[jobid] = {'func':func, 'args': args, 'kwargs': kwargs} 
                    new_job =  self.scheduler.add_job(jobid, func, *args, **kwargs)
                    log.debug("AddonScheduler registered new function '{}'".format(jobid))
                else:
                    log.debug("AddonScheduler function '{}' already registered".format(jobid))
        except ILockException:
            log.debug("AddonScheduler Error can't get Lock 'fab_addon_operation_manager_register_operation_lock' for 60 seconds")

    def exposed_modify_job(self, job_id, jobstore=None, **changes):
        if self.scheduler:
            return self.scheduler.modify_job(job_id, jobstore, **changes)

    def exposed_reschedule_job(self, job_id, jobstore=None, trigger=None, **trigger_args):
        # TODO if trigger_args has sub dicts, then transform the rpyc-netref to a static local copy 
        if self.scheduler:
            return self.scheduler.reschedule_job(job_id, jobstore, trigger, **trigger_args)

    def exposed_pause_job(self, job_id, jobstore=None):
        if self.scheduler:
            return self.scheduler.pause_job(job_id, jobstore)

    def exposed_resume_job(self, job_id, jobstore=None):
        if self.scheduler:
            return self.scheduler.resume_job(job_id, jobstore)

    def exposed_remove_job(self, job_id, jobstore=None):
        if self.scheduler:
            self.scheduler.remove_job(job_id, jobstore)

    def exposed_remove_all_jobs(self, jobstore=None):
        if self.scheduler:
            self.scheduler.remove_all_jobs(jobstore)

    def exposed_get_job(self, job_id):
        if self.scheduler:
            return self.scheduler.get_job(job_id)

    def exposed_get_func(self, oper_name):
        if self.available_operations.get(oper_name, None):
            return self.available_operations[oper_name]['function']

    def exposed_get_operations_args_schemas(self):
        return { k:k['args_schema'] for k in self.available_operations}

    def exposed_is_job_activated(self, job_id):
        if self.scheduler:
            if self.scheduler.get_job(job_id):
                res = True
            else:
                res = False
            return res

    def exposed_get_jobs(self, jobstore=None):
        if self.scheduler:
            return self.scheduler.get_jobs(jobstore)

    def exposed_get_job_ids(self, jobstore=None):
        if self.scheduler:
            return [ids for ids in self.activated_jobs]

    def exposed_get_state(self):
        if self.scheduler:
            return self.scheduler.state

    def exposed_get_state_str(self):
        if self.scheduler:
            state_to_string =  ["STATE_STOPPED", "STATE_RUNNING","STATE_PAUSED"]
            return state_to_string[self.scheduler.state]

    def exposed_pause(self):
        if self.scheduler:
            return self.scheduler.pause()

    def exposed_resume(self):
        if self.scheduler:
            return self.scheduler.resume()

    def exposed_shutdown(self):
        if self.scheduler:
            return self.scheduler.shutdown()

    def exposed_start(self):
        if self.scheduler:
            try:
                self.scheduler.start()
                log.debug("AddonScheduler starting")
                return "Starting"
            except SchedulerAlreadyRunningError:
                log.debug("AddonScheduler is already started")
                return "Already Started"

    def exposed_register_operation(self, name, description, func, args_schema={}):
        # Note that func is either a string representing an importable callable
        # or a callable that has been replaced by a netref by the RPyC call
        try:
            # RPyC servers spawns a new thread for each request
            # use a Lock to avoid conflicts when accessing th shared self.members attribute
            with ILock('fab_addon_operation_manager_register_operation_lock', timeout=60):
                log.debug("SchedulerService register_operation new function '{}'".format(name))
                new_entry = None
                if self.available_operations.get(name, None):
                    log.debug("SchedulerService register_operation, function already exists:"+name)
                    return None
                log.debug("AddonScheduler got Lock 'fab_addon_operation_manager_register_operation_lock'")
                new_entry = {'name': name, 'description': description, 'function': func, 'args_schema': args_schema}
                self.available_operations[name] = new_entry
        except ILockException:
            log.debug("AddonScheduler Error can't get Lock 'fab_addon_operation_manager_register_operation_lock' for 60 seconds")
        return new_entry
            
class AddonScheduler(object):
    server_instance = None

    def set_last_check(self, datestamp):
        if self.server_instance:
            self.server_instance.last_check = datestamp

    class __AddonSchedulerServer:
        last_check = None

        def __init__(self, appbuilder):
            self.appbuilder = appbuilder
            self.members = dict()
            try:
                thread = Thread(target=self.__start_rpyc_server, args=(appbuilder,))
                #thread.daemon = True
                thread.start()
            except OSError as error:
                if error.errno == errno.EADDRINUSE:
                    log.debug("APScheduler: Scheduler ALREADY instantiated")
                else:
                    log.debug("APScheduler: Other Error '{}'".format(str(error)))

        def __str__(self):
            return repr(self) + " appbuilder=" + repr(self.appbuilder)

        def __start_rpyc_server(self, appbuilder):
                    # Check if rpyc Server is already running in another process on the same machine
                    # trying to instantiate one will fail because the port is already taken
                    protocol_config = {'allow_public_attrs': True}
                    bgsched = BackgroundScheduler(timezone=SCHEDULER_TIMEZONE, daemon=True)
                    scheduler = APScheduler(scheduler=bgsched)
                    scheduler.init_app(appbuilder.get_app)
                    try:
                        #server = ThreadedServer(classpartial(SchedulerService,scheduler) , port=SCHEDULER_RPYC_PORT, protocol_config=protocol_config)
                        # since we want the same SchedulerService instance to be shared for all connections, 
                        # we must pass in an instance an not a class
                        # see https://rpyc.readthedocs.io/en/latest/tutorial/tut3.html
                        server = ThreadedServer(SchedulerService(scheduler) , port=SCHEDULER_RPYC_PORT, protocol_config=protocol_config)
                        log.debug("APScheduler: Starting RPyC server")
                        server.start()
                        # The above is blocking, so no instruction is run below unless an exception occurs
                    except OSError as error:
                        if error.errno == errno.EADDRINUSE:
                            log.debug("APScheduler: Scheduler ALREADY instantiated")
                        else:
                            log.debug("APScheduler: Other Error '{}'".format(str(error)))
                        

    def __init__(self, appbuilder=None):
        if not AddonScheduler.server_instance and appbuilder:
            # There is no instance of the singleton AddonScheduler yet
            AddonScheduler.server_instance = AddonScheduler.__AddonSchedulerServer(appbuilder)
            # Wait untill connection to RPyC can be established
            conn = None
            retry_attempt=0
            while retry_attempt < 3 and not conn:
                try:
                    conn = rpyc.connect(SCHEDULER_RPYC_HOST, SCHEDULER_RPYC_PORT)
                except ConnectionRefusedError:
                    time.sleep(1)

            if conn:
                log.debug("APScheduler: RPCy Scheduler service responding")
                self.start()
            else:
                log.debug("APScheduler: can't connect to RPCy Scheduler service")

        else:
            # There is already an instance for this singleton
            pass

    def __getattr__(self, name):
        return getattr(self.server_instance, name)

    def connect(self):
        try:
            conn = rpyc.connect(SCHEDULER_RPYC_HOST, SCHEDULER_RPYC_PORT)
            return conn
        except ConnectionRefusedError:
            log.debug("APScheduler: can't connect to RPCy Scheduler service")
            return None

##    def connect(self):
##        conn = None
##        retry_attempt = 0
##        while retry_attempt < 3 and not conn:
##            try:
##                conn = rpyc.connect(SCHEDULER_RPYC_HOST, SCHEDULER_RPYC_PORT)
##            except ConnectionRefusedError:
##                time.sleep(1)
##
##        if conn:
##            log.debug("APScheduler: RPCy Scheduler service responding")
##            return conn
##        else:
##            log.debug("APScheduler: can't connect to RPCy Scheduler service")
##            return None
            
    def add_job(self, jobid, func, *args, **kwargs):
        conn = self.connect()
        ret = conn.root.add_job(func, *args, **kwargs)    
        conn.close()
        return ret
            
    def get_job(self, jobid):
        conn = self.connect()
        return conn.root.get_job(jobid)

    def get_func(self, oper_name):
        conn = self.connect()
        return conn.root.get_func(oper_name)

    def is_job_activated(self, jobid):
        conn = self.connect()
        return conn.root.is_job_activated(jobid)

    def get_jobs(self):
        conn = self.connect()
        return conn.root.get_jobs()

    def get_job_ids(self):
        conn = self.connect()
        if conn:
            return conn.root.get_job_ids()
        else:
            return {}

    def remove_all_jobs(self):
        conn = self.connect()
        return conn.root.remove_all_jobs()

    def remove_job(self, jobid):
        conn = self.connect()
        return conn.root.remove_job(jobid)

    def get_state(self):
        conn = self.connect()
        return conn.root.get_state()

    def pause(self):
        self.__check_client_connection()
        return self.client.root.pause()

    def resume(self):
        conn = self.connect()
        return conn.root.resume()

    def shutdown(self):
        conn = self.connect()
        return conn.root.shutdown()

    def start(self):
        conn = self.connect()
        if conn:
            conn.root.run_selfcheck()
            conn.root.start()
        else:
            log.debug("Can't start and run selfcheck until RPyC is started")

    def register_operation(self, name, description, func, args_schema={}):
        conn = self.connect()
        res = conn.root.register_operation(name, description, func, args_schema={})
        return res

    def get_operations_args_schemas(self):
        conn = self.connect()
        res = conn.root.get_operations_args_schemas()
        return res
