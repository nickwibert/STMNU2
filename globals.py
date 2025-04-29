# `globals.py`
#
# File containing various global variables that are used all throughout the program
# (i.e. dates, class size limits, etc.)

# Libraries
from datetime import datetime, timedelta

### Absolute file paths used throughout the program ###
DATA_DIR = 'C:\\STMNU2\\data'
SQLITE_DB = DATA_DIR + '\\database.db'
BACKUP_DIR = DATA_DIR + '\\BACKUP'

QUERY_DIR = 'C:\\STMNU2\\queries'

### Determine current and previous sessions ###
# Change to next month after the 25th (i.e. if today is Jan 26th, program will consider it as February)
CURRENT_MONTH = datetime.now().month if datetime.now().day <= 25 else datetime.now().month + 1
# The current year will simply reflect the real-life current year; technically this could cause problems
# in the program between December 26th and 31st, so need to revisit this during that time
CURRENT_YEAR = datetime.now().year
# Declare current session as the first day of the session month
CURRENT_SESSION = datetime(year=CURRENT_YEAR, month=CURRENT_MONTH, day=1)

PREVIOUS_MONTH = CURRENT_MONTH - 1 if CURRENT_MONTH != 1 else 12
PREVIOUS_YEAR = CURRENT_YEAR - 1 if CURRENT_MONTH == 1 else CURRENT_YEAR
# Declare previous session
PREVIOUS_SESSION = datetime(year=PREVIOUS_YEAR, month=PREVIOUS_MONTH, day=1)

### Custom calendar dictionary with 'REGFEE' considered month 13
CALENDAR_DICT = {1 : 'JAN', 2 : 'FEB', 3 : 'MAR', 4 : 'APR', 5 : 'MAY', 6 : 'JUN', 7 : 'JUL',
                 8 : 'AUG', 9 : 'SEP', 10 : 'OCT', 11 : 'NOV', 12 : 'DEC', 13 : 'REG'}

### Class size limits ###
MAX_CLASS_SIZE = 19
MAX_WAIT_SIZE = 9
MAX_TRIAL_SIZE = 9
MAX_MAKEUP_SIZE = 9

