import json
import logging
# Running Mode가 있는 config file import
import os

log_conf = {
    # logstash를 사용할 경우 project의 첫글자는 소문자 (ES에서 project값을 index값으로 지정하는데 ES의 index값의 첫글자는 대문자가 될 수 없음)
    "project": 'paige',
    "log_level": "info" if os.environ.get("LOG_LEVEL") is None else os.environ.get("LOG_LEVEL"),
    "handler": ['baseball_file'],
    "index_code_range": [
        {
            "start_idx": 0,
            "end_idx": 1,
            "range": range(1, 4)
        },
        {
            "start_idx": 1,
            "end_idx": 3,
            "range": list(range(0, 6)) + [99]
        },
        {
            "start_idx": 3,
            "end_idx": 5,
            "range": range(0, 100)
        }
    ],
}

log_handler = {
    'baseball_logstash': {
        'type': 'logstash',
        'formatter': json.dumps({
            'project': log_conf['project'],
            'level': "%(levelname)s",
            'datetime': "%(asctime)s",
            'index': "%(index)s",
            'code': "%(code)s",
            'user_id': "%(user_id)s",
            'request_id': "%(request_id)s",
            'filename': "%(fileName)s",
            'lineno': "%(lineNo)s",
            'msg': "%(message)s",
        }),
        "host": "172.19.137.252" if os.environ.get("LOG_HOST") is None else os.environ.get("LOG_HOST"),
        "port": 5044 if os.environ.get("LOG_PORT") is None else int(os.environ.get("LOG_PORT")),
        "db_path": "logstash.db",
    },
    'baseball_file': {
        'type': 'file',
        'formatter': '[' + log_conf[
            'project'] + '|%(levelname)s %(fileName)s:%(lineNo)s] %(asctime)s Index=%(index)s Code=%(code)s MSG=%(message)s Request_Id=%(request_id)s User_Id=%(user_id)s',
        "file_max_byte": 1024 * 1024 * 10,  # 10MB
        "file_backup_count": 5,
        "file_path": os.path.dirname(__file__) + "/logs/",
    }
}

log_level = {
    "test": 5,
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}
