from datetime import datetime
from WindowsServiceBase import ServiceBase
from ConfigHelper import INI_Configuration
from typing import Text
import servicemanager
import win32process
import requests
import os
from LogHelper import ConfigLogger
import sys
from time import sleep
import re
import logging


# Declare global variable
LINE_NOTIFY_API_URL = 'http://10.199.15.109:8080/api/line/notify.php'
LINE_TOKEN: Text
REPORT_TIME: Text
# For logger
logger: logging.Logger


class LINE_Notification():
    def Send_Notify(self, message: Text):
        data = {'token': LINE_TOKEN, 'message': message, 'stickerPackageId': 2, 'stickerId': 39}
        try:
            response = requests.post(url=LINE_NOTIFY_API_URL, data=data)

            if response.status_code == 200:
                logger.debug('Sent Line notify success: {}'.format(response.status_code))
            else:
                logger.warning('Send line notify failed: {}'.format(response.status_code))
        except Exception:
            logger.exception('Can not send LINE Notify')

    def Create_Message_Content(self, disk_info) -> Text:
        message = 'ASIS Data Server Disk is Failure\n' \
            '[Disk Name]: {0.p_Name}\n' \
            '[Status]: {0.p_Status}\n' \
            '[State]: {0.p_State}\n' \
            '[Event ID]: {0.p_EventID}\n'.format(disk_info)

        return message

    @staticmethod
    def Send_Moment(message: Text):
        data = {'token': LINE_TOKEN, 'message': message}
        try:
            requests.post(url=LINE_NOTIFY_API_URL, data=data)
        except Exception:
            logger.exception('Can not send Service Status Notify')


class Disk_Health_Monitor():
    sender = LINE_Notification()

    def Physical_Disk_Analysis(self):
        executable_path = os.path.dirname(sys.executable)
        omreport_log = os.path.join(executable_path, 'REALTIME_OMREPORT.log')

        try:
            cmd = 'cmd.exe /c omreport storage pdisk controller=0 | ' \
                'findstr /R \"^$ ^ID ^Status ^Name ^State ^Failure.Predicted ^Part.Number\" > \"{}\"'.format(omreport_log)

            win32process.CreateProcess(None, cmd, None, None, 1, win32process.CREATE_NO_WINDOW, None, None, win32process.STARTUPINFO())
        except Exception as ex:
            logger.exception(ex.args)
            LINE_Notification.Send_Moment(ex.args)
            return

        try:
            with open(omreport_log, mode='r') as log:
                all_block = re.split(r'^\s?$', log.read(), flags=re.MULTILINE)

                for block in all_block:
                    if not block.strip():  # Ignore empty item
                        continue
                    disk_info = self.Parsing_Disk_Info(block)

                    if disk_info.p_Status.lower() not in ('normal', 'ok'):
                        self.SaveToLog(disk_info)
                        data_to_send = self.sender.Create_Message_Content(disk_info)
                        self.sender.Send_Notify(data_to_send)
                    else:
                        good_disk_info = dict()
                        good_disk_info['Name'] = disk_info.p_Name
                        good_disk_info['Status'] = disk_info.p_Status
                        logger.info(good_disk_info)
        except Exception as ex:
            logger.exception(ex.args)

    def Parsing_Disk_Info(self, block: Text):
        _disk_info_ = Disk_Properties()

        try:
            lines = block.splitlines()
            for line in lines:
                if group := re.match(r'^ID\s+: (?P<id>.*)$', line):
                    _disk_info_.p_ID = group['id'].strip()
                elif group := re.match(r'^Status\s*: (?P<status>.*)$', line):
                    _disk_info_.p_Status = group['status'].strip()
                elif group := re.match(r'^State\s*: (?P<state>.*)$', line):
                    _disk_info_.p_State = group['state'].strip()
                elif group := re.match(r'^Name\s+: (?P<name>.*)$', line):
                    _disk_info_.p_Name = group['name'].strip()
                elif group := re.match(r'^Power Status\s+: (?P<power_status>.*)$', line):
                    _disk_info_.p_PowerStatus = group['power_status'].strip()
                elif group := re.match(r'^Failure Predicted.*: (?P<event_id>.*)$', line):
                    _disk_info_.p_EventID = group['event_id'].strip()
                elif group := re.match(r'^Part Number.*: (?P<part_number>.*)$', line):
                    _disk_info_.p_PartNumber = group['part_number'].strip()
                else:
                    continue
        except Exception as ex:
            logger.exception(ex.args)
        return _disk_info_

    def SaveToLog(self, disk):
        try:
            bad_disk_info = dict()
            bad_disk_info['id'] = disk.p_ID
            bad_disk_info['name'] = disk.p_Name
            bad_disk_info['status'] = disk.p_Status
            bad_disk_info['state'] = disk.p_State
            bad_disk_info['power_status'] = disk.p_PowerStatus
            bad_disk_info['failure_predicted'] = disk.p_EventID
            bad_disk_info['part_number'] = disk.p_PartNumber
            logger.warning(bad_disk_info)
        except AttributeError:
            logger.exception('Attribute not exist')


class Disk_Properties():
    p_ID: Text
    p_Status: Text
    p_Name: Text
    p_State: Text
    p_PowerStatus: Text
    p_EventID: Text
    p_PartNumber: Text


class ASIS_Service(ServiceBase):
    # Define service information
    _svc_name_ = 'ASISDiskHealthMonitor'
    _svc_display_name_ = 'ASIS Disk Health Monitor'
    _svc_description_ = 'ASIS data server disk health monitor, possibly send LINE notify to L2 member group'

    # Service status flag
    is_service_alive = False

    def Inform_Log(self):
        logger.debug('---------ASIS services---------')
        logger.debug('服務名稱: {}'.format(self._svc_name_))
        logger.debug('顯示名稱: {}'.format(self._svc_display_name_))
        logger.debug('描述: {}'.format(self._svc_description_))

    def isReportTime(self):
        try:
            current_time = datetime.now().time().strftime('%H:%M')
            expected_time = datetime.strptime(REPORT_TIME, '%H:%M').time().strftime('%H:%M')

            if current_time == expected_time:
                return True
            else:
                return False
        except Exception as ex:
            logger.exception(ex.args)

    def start(self):
        # Apply ini config file
        INI_Apply_Config()
        # Inform to log file
        self.Inform_Log()
        logger.info('Service is started')
        LINE_Notification.Send_Moment('Start ASIS Disk Health Monitor!')
        self.is_service_alive = True

    def stop(self):
        logger.critical('Service is stopped')
        LINE_Notification.Send_Moment('Stop ASIS Disk Health Monitor!')
        self.is_service_alive = False

    def main(self):
        try:
            isExecuted = False
            disk_carer = Disk_Health_Monitor()
            while self.is_service_alive:
                while self.isReportTime():
                    if isExecuted is False:
                        disk_carer.Physical_Disk_Analysis()
                        isExecuted = True
                    sleep(10)
                isExecuted = False
                sleep(10)
        except Exception as ex:
            logger.exception(ex.args)


def INI_Apply_Config():
    logger.debug('---------Apply INI config file---------')

    global LINE_TOKEN
    global REPORT_TIME

    config = INI_Configuration()
    try:
        LINE_TOKEN = config.Read('LINE_NOTIFY', 'line_token')
        REPORT_TIME = config.Read('SETTING', 'om_report_time')
    except Exception:
        logger.exception('Can not read argument config from ini file')

    logger.debug('LINE_NOTIFY: {}'.format(LINE_TOKEN))
    logger.debug('REPORT_TIME: {}'.format(REPORT_TIME))
    logger.debug('------------------End------------------')


if __name__ == '__main__':
    # For config logging
    ConfigLogger()
    logger = logging.getLogger(__name__)

    if len(sys.argv) == 1:  # by pass error 1503
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ASIS_Service)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        ASIS_Service.parse_command_line(ASIS_Service)
