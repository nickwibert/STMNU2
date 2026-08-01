# `globals.py`
#
# File containing various global variables that are used all throughout the program
# (i.e. dates, class size limits, etc.)

# Libraries
from datetime import datetime, timedelta
from pathlib import Path

# Gets the directory where the `main.py` is running
# (works on both Mac and Windows)
MAIN_DIR = Path(__file__).resolve().parent

### Absolute file paths used throughout the program ###
DATA_DIR = MAIN_DIR / 'data'
SQLITE_DB = DATA_DIR / 'database.db'
BACKUP_DIR = DATA_DIR / 'BACKUP'

QUERY_DIR = MAIN_DIR / 'queries'

### Determine current and previous sessions ###
# Change to next month after the 25th (i.e. if today is Jan 26th, program will consider it as February)
if datetime.now().day <= 25:
    CURRENT_MONTH = datetime.now().month
    CURRENT_YEAR = datetime.now().year 
else:
    # Special handling for EOY; if current month is December and it is after the 25th,
    # consider session as January of the following year
    if datetime.now().month == 12:
        CURRENT_MONTH = 1
        CURRENT_YEAR = datetime.now().year + 1
    # Otherwise just add 1 to current month num
    else:
        CURRENT_MONTH = datetime.now().month + 1
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

