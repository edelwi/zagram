#!/usr/bin/env python3
# Simple Zabbix notifier for Telegram.

# Script receive 3 positional arguments: telega.py telegram_id subject message
#   - telegram_id: Telegram account ID to send to. (Use @my_id_bot to find it.)
#   - subject: Zabbix notification subject.
#   - message: Zabbix notification message.

import argparse
import logging
import re
import sys
from logging.handlers import RotatingFileHandler

import requests

from tele_config import TELEGRAM_TOKEN, IS_DEBUG, LOG_FILE_BACKUP_COUNT, LOG_FILE_MAXBYTES, LOG_FILE_NAME, PROXIES

logger = logging.getLogger('Telega.notifier')
if IS_DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.WARNING)
logfile_handler = RotatingFileHandler(LOG_FILE_NAME, maxBytes=LOG_FILE_MAXBYTES, backupCount=LOG_FILE_BACKUP_COUNT)
logfile_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s '
                                               '[in %(pathname)s:%(lineno)d]'))
logger.addHandler(logfile_handler)
logger.debug(f'Run  {str(sys.argv)}')

TG_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

STATUS_PAT = re.compile('^Trigger status:\s(?P<status>.+)$', re.MULTILINE)
SEVERITY_PAT = re.compile('^Trigger severity:\s(?P<severity>.+)$', re.MULTILINE)

emoji_map = {
    "OK": "✅",
    "Average": "❗",
    "Information": "ℹ",
    "Warning": "⚠",
    "High": "❌",
    "Disaster": "☠🆘",
}

parser = argparse.ArgumentParser()
parser.add_argument("telegram_id", help="Telegram account ID to send to. (Use @my_id_bot to find it.)", type=int)
parser.add_argument("subject", help="Zabbix notification subject.")
parser.add_argument("message", help="Zabbix notification message.", )
args = parser.parse_args()

emoji = ''
status = re.search(STATUS_PAT, args.message)
if status:
    status_value = status.group('status').rstrip('\r')
    logger.debug(f"Found starus={status_value}.")
    if status_value == 'OK':
        emoji = emoji_map['OK'] + ' '
    else:
        severity = re.search(SEVERITY_PAT, args.message)
        if severity:
            severity_value = severity.group('severity').rstrip('\r')
            logger.debug(f"Found severity={severity_value}.")
            if severity_value in emoji_map.keys():
                emoji = emoji_map[severity_value] + ' '
            else:
                logger.warning(f"Unknown severity:{severity_value}.")
        else:
            logger.warning(f"Severity not found.")
else:
    logger.warning(f"Status not found.")
payload = {"chat_id": f"{args.telegram_id}", "text": f"{emoji}{args.subject}\n\n{args.message}"}
try:
    response = requests.post(TG_API_URL, json=payload, proxies=PROXIES)
except requests.RequestException as e:
    logger.exception(f"Request to Telegram API failed: {str(e)}.")
else:
    logger.debug(f'Request to Telegram API - OK.')
