# 공통 부분 에러
class CrawlerError(Exception):
    def __init__(self, msg, code):
        self.msg = msg
        try:
            self.errorcode = self.CODES[code]
        except:
            self.errorcode = 999

    def text(self):
        return self.msg

    def code(self):
        return self.errorcode

    # 사용할 모듈 코드
    MODULE_CODE = '0000'

    # 에러 코드 리스트
    CODES = dict(SUCCESS=0,
                 UNKNOWN=999)

