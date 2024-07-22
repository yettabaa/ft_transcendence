import datetime

class Logger:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file = open(file_path, "a")

    def info(self, msg='test'):
        time = datetime.datetime.now().strftime('%H:%M')
        self.file.write(f'[INFO] {time} {msg}\n')
        self.file.flush()

    def error(self, msg='test'):
        time = datetime.datetime.now().strftime('%H:%M')
        self.file.write(f'[ERROR] {time} {msg}\n')
        self.flush()

    def warning(self, msg='test'):
        time = datetime.datetime.now().strftime('%H:%M')
        self.file.write(f'[WARNING] {time} {msg}\n')
    def close(self):
        self.file.close()
log = Logger('./data.log')