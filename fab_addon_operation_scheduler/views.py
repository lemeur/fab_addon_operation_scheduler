from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView
from .models import *
from .widgets import JsonEditorWidget
from wtforms import StringField, SelectField

from datetime import datetime

"""
    Create your Views (but don't register them here, do it on the manager::


    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)

    
"""

class ScheduledOperationView(ModelView):
    datamodel = SQLAInterface(ScheduledOperation)
    scheduler_schema = {
        "type": "object",
        "title": " ",
        "required": ["mode","timezone"],
        "properties": {
            "mode": {
                "type": "string",
                "default": "interval",
                "propertyOrder": 1,
                "enum": [
                    "cron",
                    "interval",
                    "date"
                ]
            },
            "timezone": {
                "type": "string",
                "propertyOrder": 2,
                "default": "Europe/Paris",
                "options": {
                    "inputAttributes": {
                        "placeholder":  "Europe/Paris",
                    }
                }
            },
            "weeks": {
                "type": "integer",
                "propertyOrder": 10,
                "default": 0,
                "options": {
                    "dependencies": {
                        "mode": "interval"
                    }
                }
            },
            "days": {
                "type": "integer",
                "propertyOrder": 11,
                "default": 1,
                "options": {
                    "dependencies": {
                        "mode": "interval"
                    }
                }
            },
            "minutes": {
                "type": "integer",
                "propertyOrder": 12,
                "default": 0,
                "options": {
                    "dependencies": {
                        "mode": "interval"
                    }
                }
            },
            "seconds": {
                "type": "integer",
                "propertyOrder": 13,
                "default": 0,
                "options": {
                    "dependencies": {
                        "mode": "interval"
                    }
                }
            },
            "year": {
                "type": "string",
                "propertyOrder": 20,
                "default": "*",
                "options": {
                    "dependencies": {
                        "mode": "cron"
                    }
                }
            },
            "month": {
                "type": "string",
                "propertyOrder": 21,
                "default": "*",
                "options": {
                    "dependencies": {
                        "mode": "cron"
                    }
                }
            },
            "day": {
                "type": "string",
                "propertyOrder": 22,
                "default": "*",
                "options": {
                    "dependencies": {
                        "mode": "cron"
                    }
                }
            },
            "week": {
                "type": "string",
                "propertyOrder": 23,
                "default": "*",
                "options": {
                    "dependencies": {
                        "mode": "cron"
                    }
                }
            },
            "day_of_week": {
                "type": "string",
                "propertyOrder": 24,
                "default": "*",
                "options": {
                    "dependencies": {
                        "mode": "cron"
                    }
                }
            },
            "hour": {
                "type": "string",
                "propertyOrder": 25,
                "default": "*",
                "options": {
                    "dependencies": {
                        "mode": "cron"
                    }
                }
            },
            "minute": {
                "type": "string",
                "propertyOrder": 26,
                "default": "*",
                "options": {
                    "dependencies": {
                        "mode": "cron"
                    }
                }
            },
            "second": {
                "type": "string",
                "propertyOrder": 27,
                "default": "*",
                "options": {
                    "dependencies": {
                        "mode": "cron"
                    }
                }
            },
            "start_date": {
                "type": "string",
                "propertyOrder": 3,
                "default": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "format": "datetime",
                "options": {
                    "dependencies": {
                        "mode": ["interval","cron"]
                    },
                    "inputAttributes": {
                        "class":  "date",
                    }
                }
            },
            "end_date": {
                "type": "string",
                "propertyOrder": 4,
                "default": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "format": "datetime",
                "options": {
                    "dependencies": {
                        "mode": ["interval","cron"]
                    },
                    "inputAttributes": {
                        "class":  "date",
                    }
                }
            },
            "run_date": {
                "type": "string",
                "propertyOrder": 30,
                "default": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "format": "datetime",
                "options": {
                    "dependencies": {
                        "mode": "date"
                    }
                }
            }
        },
        "defaultProperties": ["mode","weeks","days","minutes","seconds","start_date","end_date","year","month","day","week","day_of_week","hour","minute","second","timezone","date"]
    }
    before_js = ""
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
            " newmode=this.getEditor('root.mode').getValue();"
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
            "newval = {...default_value, ...current_value, mode:newmode};"
            "this.setValue(newval);"
        "}"
        "editor.watch('root.mode',watchMode.bind(editor));"
    )

    edit_form_extra_fields = {
        "scheduler_args": StringField(
            "Scheduler",
            widget=JsonEditorWidget(scheduler_schema, before_js, after_js),
        ),
    }
    add_form_extra_fields = edit_form_extra_fields

class SchedulableOperationView(ModelView):
    datamodel = SQLAInterface(SchedulableOperation)
    related_views = [ScheduledOperationView]

