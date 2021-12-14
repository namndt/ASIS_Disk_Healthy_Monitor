from sys import executable
import os.path
from configparser import ConfigParser


class INI_Configuration():
    INI_FILE_NAME = 'ASIS_Disk_Health_Monitor.ini'
    EXECUTEABLE_PATH = os.path.dirname(executable)
    INI_FILE_FULL_PATH = os.path.join(EXECUTEABLE_PATH, INI_FILE_NAME)

    def __init__(self):
        isExisting = os.path.isfile(self.INI_FILE_FULL_PATH)
        if isExisting is False:
            self.Create_Write_INIFile()

    def Read(self, section, key):
        config = ConfigParser()
        config.read(self.INI_FILE_FULL_PATH)

        value = config.get(section=section, option=key)
        return value

    def Create_Write_INIFile(self):
        config = ConfigParser()
        config['LINE_NOTIFY'] = {'line_token': 'A6B09BKhik0mHAaVvK51DG7pzsLCbiNIWSzrPNS6l3Z'}
        config['SETTING'] = {'om_report_time': '7:30'}

        with open(self.INI_FILE_FULL_PATH, mode='w') as configFile:
            config.write(configFile)


if __name__ == "__main__":
    print('run config')
    config = INI_Configuration()
    print('ini file is existing: ' + os.path.isfile(config.INI_FILE_FULL_PATH).__str__())
    line_token = config.Read('LINE_NOTIFY', 'line_token')
    interval = config.Read('SETTING', 'om_report_time')
    print('line_token: ' + line_token)
    print('om_report_time: ' + interval)
