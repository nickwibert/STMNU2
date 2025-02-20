# `globals.py`
#
# File containing various global variables that are used all throughout the program
# (i.e. dates, class size limits, etc.)

# Libraries
from datetime import datetime, timedelta

### Determine current and previous sessions ###
# Change to next month after the 25th (i.e. if today is Jan 26th, program will consider it as February)
CURRENT_MONTH = datetime.now().month if datetime.now().day <= 25 else datetime.now().month + 1
# The current year will simply reflect the real-life current year; technically this could cause problems
# in the program between December 26th and 31st, so need to revisit this during that time
CURRENT_YEAR = datetime.now().year

# Declare current session as the first day of the session month
CURRENT_SESSION = datetime(year=CURRENT_YEAR, month=CURRENT_MONTH, day=1)

### Class size limits ###
MAX_CLASS_SIZE = 19
MAX_WAIT_SIZE = 4
MAX_TRIAL_SIZE = 8
MAX_MAKEUP_SIZE = 4

# Cutoff date for students to be excluded
MONTHS_SINCE_PAYMENT_LIMIT = 8
CUTOFF_DATE = datetime.now() - timedelta(days=30*MONTHS_SINCE_PAYMENT_LIMIT)
