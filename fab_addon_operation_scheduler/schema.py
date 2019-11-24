from datetime import datetime

def get_schema():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    scheduler_schema = {
        "type": "object",
        "title": " ",
        "required": ["trigger","timezone"],
        "properties": {
            "trigger": {
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
                        "trigger": "interval"
                    }
                }
            },
            "days": {
                "type": "integer",
                "propertyOrder": 11,
                "default": 1,
                "options": {
                    "dependencies": {
                        "trigger": "interval"
                    }
                }
            },
            "minutes": {
                "type": "integer",
                "propertyOrder": 12,
                "default": 0,
                "options": {
                    "dependencies": {
                        "trigger": "interval"
                    }
                }
            },
            "seconds": {
                "type": "integer",
                "propertyOrder": 13,
                "default": 0,
                "options": {
                    "dependencies": {
                        "trigger": "interval"
                    }
                }
            },
            "year": {
                "type": "string",
                "propertyOrder": 20,
                "default": "*",
                "options": {
                    "dependencies": {
                        "trigger": "cron"
                    }
                }
            },
            "month": {
                "type": "string",
                "propertyOrder": 21,
                "default": "*",
                "options": {
                    "dependencies": {
                        "trigger": "cron"
                    }
                }
            },
            "day": {
                "type": "string",
                "propertyOrder": 22,
                "default": "*",
                "options": {
                    "dependencies": {
                        "trigger": "cron"
                    }
                }
            },
            "week": {
                "type": "string",
                "propertyOrder": 23,
                "default": "*",
                "options": {
                    "dependencies": {
                        "trigger": "cron"
                    }
                }
            },
            "day_of_week": {
                "type": "string",
                "propertyOrder": 24,
                "default": "*",
                "options": {
                    "dependencies": {
                        "trigger": "cron"
                    }
                }
            },
            "hour": {
                "type": "string",
                "propertyOrder": 25,
                "default": "*",
                "options": {
                    "dependencies": {
                        "trigger": "cron"
                    }
                }
            },
            "minute": {
                "type": "string",
                "propertyOrder": 26,
                "default": "*",
                "options": {
                    "dependencies": {
                        "trigger": "cron"
                    }
                }
            },
            "second": {
                "type": "string",
                "propertyOrder": 27,
                "default": "*",
                "options": {
                    "dependencies": {
                        "trigger": "cron"
                    }
                }
            },
            "start_date": {
                "type": "string",
                "propertyOrder": 3,
                "default": '',
                "format": "datetime",
                "options": {
                    "dependencies": {
                        "trigger": ["interval","cron"]
                    },
                    "inputAttributes": {
                        "class":  "date",
                        "placeholder": now
                    }
                }
            },
            "end_date": {
                "type": "string",
                "propertyOrder": 4,
                "default": '',
                "format": "datetime",
                "options": {
                    "dependencies": {
                        "trigger": ["interval","cron"]
                    },
                    "inputAttributes": {
                        "class":  "date",
                        "placeholder": now
                    }
                }
            },
            "run_date": {
                "type": "string",
                "propertyOrder": 30,
                "default": now,
                "format": "datetime",
                "options": {
                    "dependencies": {
                        "trigger": "date"
                    }
                }
            }
        },
        "defaultProperties": ["trigger","weeks","days","minutes","seconds","start_date","end_date","year","month","day","week","day_of_week","hour","minute","second","timezone","date"]
    }

    return scheduler_schema
