import logging
import logging.handlers
from inspect import getframeinfo, stack

from logger import log_config
from logger.log_config import log_conf
from logstash_async.handler import AsynchronousLogstashHandler

INDEX_CODE_LENGTH = 5  # index code length
TEST_LEVEL = log_config.log_level['test']


class log_factory():
    def __init__(self, index):
        # logger 항목에 test추가
        logging.addLevelName(TEST_LEVEL, "TEST")

        def test(self, message, *args, **kws):
            if self.isEnabledFor(TEST_LEVEL):
                self._log(TEST_LEVEL, message, args, **kws)

        logging.Logger.test = test

        self.__logger = logging.getLogger("logger")
        self.__logger.setLevel(log_config.log_level.get(log_conf.get("log_level")))
        if not self.__logger.hasHandlers():
            self.addHandler(log_conf['handler'])

        self.index = str(index)

    def get(self, index_code):
        if isinstance(index_code, int):
            index_code = str(index_code)
        if self.indexValidation(str(self.index) + index_code):
            logger = self.__getChild(index_code[:2]).__getChild(index_code[2:])
            return logger

    def addHandler(self, handler_list):
        for handler_name in handler_list:
            try:
                handler = log_config.log_handler[handler_name]
                if handler['type'] == 'logstash':
                    subHandler = AsynchronousLogstashHandler(handler['host'], handler['port'],
                                                             database_path=handler['db_path'])
                elif handler['type'] == 'file':
                    subHandler = logging.handlers.RotatingFileHandler(handler['file_path'] + "/paige.log",
                                                                      maxBytes=handler['file_max_byte'],
                                                                      backupCount=handler['file_backup_count'])
                else:
                    print('error config type')
                    exit()
                formatter = logging.Formatter(handler['formatter'])
                subHandler.setFormatter(formatter)
                self.__logger.addHandler(subHandler)
            except AttributeError as e:
                print(e)
                exit()

    def __getChild(self, index_code, handler_list=[]):
        logger = log_factory(self.index + str(index_code))
        logger.__logger = self.__logger.getChild(index_code)
        logger.addHandler(handler_list)
        return logger

    def indexValidation(self, index_code):
        try:
            if len(index_code) != INDEX_CODE_LENGTH:
                print("invalid log index length")
                exit()
            else:
                for rule in log_conf['index_code_range']:
                    if int(index_code[rule['start_idx']:rule['end_idx']]) not in rule['range']:
                        print("invalid log index code range")
                        exit()
                return True
        except ValueError as e:
            print(e)
            exit()

    def codeValidaton(self, code):
        try:
            if isinstance(code, int) and code in range(0, 1000):
                pass
            elif isinstance(code, str) and int(code) in range(0, 1000):
                pass
            else:
                self.error("invalid log code %s" % str(code))
                return False
            return True
        except ValueError as e:
            self.error(e)
            return False

    def getIndex(self):
        return self.index

    def test(self, msg, code=0, request_id=None, user_id=None):
        caller = getframeinfo(stack()[1][0])
        if self.codeValidaton(code):
            self.__logger.test(msg,
                               extra={'index': self.index, 'code': str(code).zfill(3), 'fileName': caller.filename,
                                      'lineNo': caller.lineno, 'request_id': request_id, 'user_id': user_id})
        else:
            self.__logger.test(msg, extra={'index': self.index, 'code': '999', 'fileName': caller.filename,
                                           'lineNo': caller.lineno, 'request_id': request_id, 'user_id': user_id})

    def debug(self, msg, code=0, request_id=None, user_id=None):
        caller = getframeinfo(stack()[1][0])
        if self.codeValidaton(code):
            self.__logger.debug(msg,
                                extra={'index': self.index, 'code': str(code).zfill(3), 'fileName': caller.filename,
                                       'lineNo': caller.lineno, 'request_id': request_id, 'user_id': user_id})
        else:
            self.__logger.debug(msg, extra={'index': self.index, 'code': '999', 'fileName': caller.filename,
                                            'lineNo': caller.lineno, 'request_id': request_id, 'user_id': user_id})

    def info(self, msg, code=0, request_id=None, user_id=None):
        caller = getframeinfo(stack()[1][0])
        if self.codeValidaton(code):
            self.__logger.info(msg,
                               extra={'index': self.index, 'code': str(code).zfill(3), 'fileName': caller.filename,
                                      'lineNo': caller.lineno, 'request_id': request_id, 'user_id': user_id})
        else:
            self.__logger.info(msg, extra={'index': self.index, 'code': '999', 'fileName': caller.filename,
                                           'lineNo': caller.lineno, 'request_id': request_id, 'user_id': user_id})

    def warning(self, msg, code=0, request_id=None, user_id=None):
        caller = getframeinfo(stack()[1][0])
        if self.codeValidaton(code):
            self.__logger.warning(msg, extra={'index': self.index, 'code': str(code).zfill(3),
                                              'fileName': caller.filename, 'lineNo': caller.lineno,
                                              'request_id': request_id, 'user_id': user_id})
        else:
            self.__logger.warning(msg, extra={'index': self.index, 'code': '999', 'fileName': caller.filename,
                                              'lineNo': caller.lineno, 'request_id': request_id,
                                              'user_id': user_id})

    def error(self, msg, code=0, request_id=None, user_id=None):
        caller = getframeinfo(stack()[1][0])
        if self.codeValidaton(code):
            self.__logger.error(msg,
                                extra={'index': self.index, 'code': str(code).zfill(3), 'fileName': caller.filename,
                                       'lineNo': caller.lineno, 'request_id': request_id, 'user_id': user_id})
        else:
            self.__logger.error(msg, extra={'index': self.index, 'code': '999', 'fileName': caller.filename,
                                            'lineNo': caller.lineno, 'request_id': request_id, 'user_id': user_id})

    def critical(self, msg, code=0, request_id=None, user_id=None):
        caller = getframeinfo(stack()[1][0])
        if self.codeValidaton(code):
            self.__logger.critical(msg, extra={'index': self.index, 'code': str(code).zfill(3),
                                               'fileName': caller.filename, 'lineNo': caller.lineno,
                                               'request_id': request_id, 'user_id': user_id})
        else:
            self.__logger.critical(msg, extra={'index': self.index, 'code': '999', 'fileName': caller.filename,
                                               'lineNo': caller.lineno, 'request_id': request_id,
                                               'user_id': user_id})


root_logger = log_factory(4)
