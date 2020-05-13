class CKANException(Exception):
    def __init__(self,err_message):
        self.err_message=err_message