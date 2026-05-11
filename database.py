import os
import pandas as pd
import numpy as np
import sqlite3
import calendar
from datetime import datetime

import functions as fn 

# Global variables
from globals import CURRENT_SESSION, CALENDAR_DICT, \
                    QUERY_DIR, SQLITE_DB, BACKUP_DIR

class StudentDatabase:
    def __init__(self):
        # Variable to track whether the user has entered the payment password yet.
        # Once the user has entered the password once, they should not be asked again
        self.request_password = True
        
        # SQLite database connection
        self.conn = sqlite3.connect(SQLITE_DB)
        self.cursor = self.conn.cursor()


    def search_student(self, query, show_inactive=False):
        # Force all uppercase
        for key in query.keys(): query[key] = query[key].upper()

         # Read in query from 'search_student.sql' as string
        with open(os.path.join(QUERY_DIR,'search_student.sql'), 'r') as sql_file:
            sql_script = sql_file.read()

        # Parameters used in query
        params = {'first_name'    : f"%{query['First Name']}%",
                  'last_name'     : f"%{query['Last Name']}%", 
                  'show_inactive' : show_inactive}

        # Query database and return results as DataFrame
        matches = pd.read_sql(sql_script, self.conn, params=params)
        return matches
    

    # Create new student record in `student` table
    def create_student(self, entry_boxes):
        # Extract all (non-blank) user entries
        new_student_info = {field : entry.get().strip() for (field,entry) in entry_boxes.items() if entry.get()}
        # Determine what the new STUDENTNO should be (max STUDENTNO plus 1)
        self.cursor.execute("SELECT MAX(CAST(STUDENTNO AS integer))+1 AS NEW_STUDENTNO FROM student")
        new_studentno = self.cursor.fetchone()[0]
        # Determine what the new family ID should be (max family ID plus 1)
        self.cursor.execute("SELECT MAX(CAST(FAMILY_ID AS integer))+1 AS NEW_FAMILY_ID FROM student")
        new_family_id = self.cursor.fetchone()[0]

        # Add other fields in `student` table
        new_student_info.update({'ACTIVE'     : 1,
                                 'FAMILY_ID'  : new_family_id,
                                 'STUDENTNO'  : new_studentno,
                                 'ENROLLDATE' : datetime.today().strftime('%m/%d/%Y'),
                                 'MONTHLYFEE' : 0,
                                 'BALANCE'    : 0,
                                 'CREA_TMS'   : datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
                                 'UPDT_TMS'   : datetime.now().strftime('%m/%d/%Y %H:%M:%S')})
        
        ## Insert into SQLite database
        self.sqlite_insert('student', {k:v for k,v in new_student_info.items() if k not in ['MOMNAME','DADNAME']})

        # Create guardian records (if provided)
        for guardian_type in ['MOM','DAD']:
            if f'{guardian_type}NAME' in new_student_info.keys():
                # Collect data into dict
                guardian_info = {'FAMILY_ID'    : new_family_id,
                                'RELATION'     : guardian_type,
                                'FNAME'        : new_student_info[f'{guardian_type}NAME'],
                                'LNAME'        : new_student_info['LNAME'],
                                'CREA_TMS'     : datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
                                'UPDT_TMS'     : datetime.now().strftime('%m/%d/%Y %H:%M:%S')}

                # Insert into database
                self.sqlite_insert('guardian', guardian_info)


    # Update existing student record in `student`
    def update_student_info(self, student_id, entry_boxes, edit_type, year=CURRENT_SESSION.year):
        # Get student number / family ID associated with the edited student
        self.cursor.execute(f"""SELECT DISTINCT STUDENTNO, FAMILY_ID FROM student WHERE STUDENT_ID={student_id}""")
        studentno, family_id = self.cursor.fetchall()[0]
        # If family ID is blank, create a new one
        if pd.isna(family_id) or family_id=='':
            self.cursor.execute("SELECT MAX(CAST(FAMILY_ID AS integer))+1 AS NEW_FAMILY_ID FROM student")
            family_id = self.cursor.fetchone()[0]

        # Guardian info
        guardian_info = pd.read_sql(f"""SELECT *
                                        FROM guardian 
                                        WHERE FAMILY_ID='{family_id}'""",
                                    self.conn)

        new_student_info = {field : entry.get().strip() for (field,entry) in entry_boxes.items()}
        for field in new_student_info.keys():
            if len(new_student_info[field]) == 0:
                new_student_info[field] = 0 if entry_boxes[field].dtype =='float' else None
            elif entry_boxes[field].dtype == 'float':
                new_student_info[field] = float(new_student_info[field])
            elif entry_boxes[field].dtype == 'int':
                new_student_info[field] = int(float(new_student_info[field]))
            else:
                new_student_info[field] = new_student_info[field].upper()


        # Update payments
        if 'PAYMENT' in edit_type:
            self.update_payment_info(student_id, new_student_info, year)
        # Otherwise, update student and guardian tables
        else:
            # Loop through fields
            for field in entry_boxes.keys():
                # For MOMNAME and DADNAME, we update `guardian`
                if field in ['MOMNAME','DADNAME']:
                    relation = field[:3]
                    is_blank = field not in new_student_info.keys()
                    guardian_record = guardian_info.loc[guardian_info['RELATION']==relation].squeeze() if not guardian_info.empty else pd.DataFrame()
                    # If guardian exists, and new value is blank, delete record from database
                    if not guardian_record.empty and is_blank:
                        self.sqlite_delete('guardian', {'FAMILY_ID' : family_id, 'RELATION' : relation})
                    # Otherwise, update existing guardian record or insert a new one
                    elif not is_blank:
                        new_guardian_record = {'FAMILY_ID'    : family_id,
                                           'RELATION'     : relation,
                                           'FNAME'        : new_student_info[f'{relation}NAME'],
                                           'LNAME'        : new_student_info['LNAME'],
                                           'CREA_TMS'     : datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
                                           'UPDT_TMS'     : datetime.now().strftime('%m/%d/%Y %H:%M:%S')}
                        unique_idx = ['FAMILY_ID', 'RELATION']
                        self.sqlite_upsert('guardian', new_guardian_record, unique_idx)

            new_student_info_sqlite = {k:v for k,v in new_student_info.items() if k not in ['MOMNAME','DADNAME']}

            new_student_info_sqlite.update({'UPDT_TMS' : datetime.now().strftime('%m/%d/%Y %H:%M:%S')})
            self.sqlite_update('student',
                               new_student_info_sqlite,
                               where_dict={'STUDENT_ID' : student_id})


    # Toggle 'ACTIVE' value for selected student between True/False
    def activate_student(self, student_id):
        update_query = f"""
            UPDATE student
            SET ACTIVE = NOT ACTIVE
            WHERE STUDENT_ID={student_id}
        """
        self.cursor.execute(update_query)
        self.conn.commit()
        

    # Create/delete a `bill` record for the selected student, month, year
    def bill_student(self, student_id, month_num, year):
        month = calendar.month_abbr[month_num].upper() if month_num < 13 else 'REG'

        select_sql = f'''
            SELECT *
            FROM bill
            WHERE STUDENT_ID={student_id}
                  AND MONTH={month_num}
                  AND YEAR={year}
        '''
        bill_record = pd.read_sql(select_sql, self.conn)
        bill_info = {'STUDENT_ID' : student_id,
                     'MONTH'      : month_num,
                     'YEAR'       : year}

        # If this bill does not exist, create record
        if bill_record.empty:
            self.sqlite_insert('bill', bill_info)
        # If this month/year appears in 'bill' for this student (meaning they owed),
        # delete that bill record to indicate that the payment has been made
        else:
            self.sqlite_delete('bill', bill_info)


    # Create/delete/modify payments for a given student in the `payment` table
    def update_payment_info(self, student_id, new_info, year):
        pay_bill_query = f"""
            SELECT STUDENT_ID, MONTH, YEAR, PAY, BILL
            FROM (
                SELECT MONTH_YEAR.*, PAY, IIF(B.STUDENT_ID IS NULL, 0, 1) AS BILL
                FROM (
                    SELECT DISTINCT {student_id} AS STUDENT_ID, MONTH, YEAR
                    FROM payment
                ) AS MONTH_YEAR
                    LEFT JOIN payment AS P ON MONTH_YEAR.STUDENT_ID=P.STUDENT_ID
                                        AND MONTH_YEAR.MONTH=P.MONTH
                                        AND MONTH_YEAR.YEAR=P.YEAR
                    LEFT JOIN bill AS B ON MONTH_YEAR.STUDENT_ID=B.STUDENT_ID
                                        AND MONTH_YEAR.MONTH=B.MONTH
                                        AND MONTH_YEAR.YEAR=B.YEAR
            ) AS FINAL
            -- Only pull month/year where there is a payment or a bill
            WHERE (PAY IS NOT NULL OR BILL = 1) AND (YEAR={year})
            ORDER BY YEAR, MONTH
        """

        pay_and_bills = pd.read_sql(pay_bill_query, self.conn)

        # Loop through pay fields
        for field in [key for key in new_info.keys() if 'PAY' in key]:    
            # Integer corresponding to the month this payment applies to
            month_num = list(CALENDAR_DICT.values()).index(field[:3]) + 1
            pay = new_info[field]
            date = '' if pay in (None, 0.0, '0.00') else new_info[f'{field[:3]}DATE']

            # If new value is non-zero, insert/update payment in database
            if new_info[field] not in (None, 0.0, '0.00'):
                # Perform insert/update
                upsert_dict = {'STUDENT_ID' : student_id,
                               'MONTH'      : month_num,
                               'PAY'        : pay,
                               'DATE'       : date,
                               'YEAR'       : year}
                unique_idx = ['STUDENT_ID', 'MONTH', 'YEAR']
                self.sqlite_upsert('payment', upsert_dict, unique_idx)

                # Next, if student had been billed for this month, delete bill record
                if pay_and_bills.loc[pay_and_bills['BILL']==1,'MONTH'].isin([month_num]).any():
                    self.sqlite_delete('bill',
                                       where_dict={'STUDENT_ID' : student_id,
                                                   'MONTH' : month_num,
                                                   'YEAR' : year})
                
                # Finally, if payment record was created for CURRENT MONTH, place student in class roll
                # and ensure they are marked as active
                if month_num==CURRENT_SESSION.month:
                    self.sqlite_update('student', new_info={'ACTIVE':1}, where_dict={'STUDENT_ID':student_id})
                    for class_id in pd.read_sql(f'SELECT * FROM class_student WHERE STUDENT_ID={student_id}', self.conn)['CLASS_ID'].values:
                        self.enroll_student(student_id, class_id)
            else:
                # Delete the payment record (if it exists)
                self.sqlite_delete('payment',
                                   where_dict={'STUDENT_ID' : student_id,
                                               'MONTH'      : month_num,
                                               'YEAR'       : year})

                # If a payment record has been deleted for CURRENT MONTH, remove student from class roll
                if month_num == CURRENT_SESSION.month:
                    for class_id in pd.read_sql(f'SELECT * FROM class_student WHERE STUDENT_ID={student_id}', self.conn)['CLASS_ID'].values:
                        self.unenroll_student(student_id, class_id,)


    # Create/delete/modify notes for a given student/class in the `note` table
    # The type of note we are dealing with is provided by edit_type (either 'NOTE_STUDENT' or 'NOTE_CLASS')
    # and the relevant ID field (STUDENT_ID or CLASS_ID) is given by 'id'
    def update_note_info(self, id, edit_type, note_textbox):
        # Get all text from the textbox
        note_txt = note_textbox.get('1.0', 'end-1c')
        # Determine name of ID column we will use
        id_field = edit_type.split('_')[0] + '_ID'
        # Determine the other ID field, which we should fill with 0
        other_id_field = 'CLASS_ID' if id_field=='STUDENT_ID' else 'STUDENT_ID'

        # Existing note record
        note_record = pd.read_sql(f"""SELECT *
                                      FROM note 
                                      WHERE {id_field}={id}""",
                                  self.conn).squeeze()

        # If new note_txt contains data, update/insert
        if note_txt.strip():
            unique_idx = ['CLASS_ID', 'STUDENT_ID']
            new_info = {id_field       : id,
                        other_id_field : 0,
                        'NOTE_TXT'     : note_txt,
                        'CREA_TMS'     : datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
                        'UPDT_TMS'     : datetime.now().strftime('%m/%d/%Y %H:%M:%S')}
            self.sqlite_upsert('note', new_info, unique_idx)
        # Otherwise, attempt to delete note 
        else:
            self.sqlite_delete('note', where_dict={id_field : id})


    # Create new class record in `classes` table
    def create_class(self, entry_boxes):
        # Extract all (non-blank) user entries
        new_class_info = {field : entry.get().strip() for (field,entry) in entry_boxes.items() if entry.get()}

        # Derive am_pm by assuming 8-11:59 are AM times, and all else are PM
        class_hour = int(new_class_info['CLASSTIME'].split(':')[0])
        am_pm = 'AM' if 8 < class_hour and class_hour < 12 else 'PM'

        # We receive CLASSTIME as just the hour/minute -- add day abbrev at start
        # TODO: eventually need to clean up classes table to have separate columns
        # rather than using the outdated dbase representation
        weekday_int = list(calendar.day_name).index(new_class_info['WEEKDAY']) + 1
        weekday_abbr = 'TH' if weekday_int == 4 else calendar.day_abbr[weekday_int-1][0]
        new_class_info['CLASSTIME'] = weekday_abbr + ' ' + new_class_info['CLASSTIME']

        # Capitalize instructor name
        new_class_info['TEACH'] = new_class_info['TEACH'].upper()

        # Add other fields in `classes` table
        new_class_info.update({
            'DAYOFWEEK'  : weekday_int,
            'AM_PM'      : am_pm,
            'CREA_TMS'   : datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
            'UPDT_TMS'   : datetime.now().strftime('%m/%d/%Y %H:%M:%S')
        })

        # Drop 'weekday' name column
        new_class_info.pop('WEEKDAY', None)
        
        ## Insert into SQLite database
        self.sqlite_insert('classes', {k:v for k,v in new_class_info.items()})


    def update_class_info(self, class_id, entry_boxes, edit_type, wait_var=None):
        # Change wait variable value to exit edit mode
        if wait_var:
            wait_var.set('done')

        new_values = [entry.get().strip() for entry in entry_boxes.values()]
        new_info = pd.Series({k:v for (k,v) in zip(entry_boxes.keys(), new_values)}).squeeze()

        # Cast data types
        for field in entry_boxes.keys():
            if len(new_info[field]) == 0:
                new_info[field] = 0 if entry_boxes[field].dtype == 'float' else None
            elif entry_boxes[field].dtype == 'float':
                new_info[field] = float(new_info[field])
            elif entry_boxes[field].dtype == 'int':
                new_info[field] = int(float(new_info[field]))
            else:
                new_info[field] = new_info[field].upper()


        ## Step 1: Send to other functions to update relevant tables in database
        if 'WAIT' in edit_type:
            self.update_wait_info(class_id, new_info)
        elif 'TRIAL' in edit_type:
            self.update_trial_info(class_id, new_info)
        elif 'MAKEUP' in edit_type:
            self.update_makeup_info(class_id, new_info)

        ## Otherwise, update class directly
        # Extract weekday abbr and class time 
        weekday_abbr, class_time = new_info['CLASSTIME'].split(' ')
        weekday_int = 4 if weekday_abbr == 'TH' else fn.get_weekday_index(weekday_abbr)
        # Derive AM_PM again incase the time changed
        class_hour = int(class_time.split(':')[0])
        am_pm = 'AM' if 8 < class_hour and class_hour < 12 else 'PM'

        new_class_info = {'CLASS_ID' : class_id,
                          'TEACH'    : new_info['TEACH'],
                          'DAYOFWEEK': weekday_int,
                          'CLASSTIME': new_info['CLASSTIME'],
                          'CLASSNAME': new_info['CLASSNAME'],
                          'AM_PM'    : am_pm,
                          'UPDT_TMS' : datetime.now().strftime('%m/%d/%Y %H:%M:%S')}

        self.sqlite_update('classes',
                            new_class_info,
                            where_dict={'CLASS_ID' : class_id})


    def update_wait_info(self, class_id, new_info):
        # `wait_counter` tracks how many waitlists have been entered as we loop through
        # all 4 placeholder fields. This is done so that if a gap exists in the 
        # middle of the waitlist, all the entries will shift upward.
        wait_counter = 1
        wait_columns = [col_name for col_name in new_info.index if 'WAIT' in col_name]
        wait_columns.sort()
        for field in wait_columns:
            # Extract wait number from field name
            wait_no = int(field[-1])

            # New information
            new_wait_name = new_info[f'WAIT{wait_no}']
            new_wait_phone = new_info[f'W{wait_no}PHONE']

            # If both name and phone fields are blank, attempt to delete wait record
            if all([(info is None or info.strip()=='') for info in [new_wait_name,new_wait_phone]]):
                self.sqlite_delete('wait', where_dict={'CLASS_ID':class_id, 'WAIT_NO':wait_no})
            # Otherwise, insert/update waitlist record
            else:
                # Note: in the special case that a single waitlist is being added, we don't need to track
                # anything, so we use the true `wait_no` when creating the record
                new_wait_info = {'CLASS_ID' : class_id,
                                 'WAIT_NO'  : wait_counter if len(wait_columns) > 1 else wait_no,
                                 'NAME'     : new_wait_name,
                                 'PHONE'    : new_wait_phone,
                                 'CREA_TMS' : datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
                                 'UPDT_TMS' : datetime.now().strftime('%m/%d/%Y %H:%M:%S')}
                unique_idx = ['CLASS_ID', 'WAIT_NO']
                self.sqlite_upsert('wait', new_wait_info, unique_idx)

            wait_counter += 1


    def update_trial_info(self, class_id, new_info):
        # `trial_counter` tracks how many trials have been entered as we loop through
        # all 8 placeholder fields. This is done so that if a gap exists in the 
        # middle of the trials, all the entries will shift upward.
        trial_counter = 1 
        trial_columns = [col_name for col_name in new_info.index if 'TRIAL' in col_name]
        trial_columns.sort()
        for field in trial_columns:
            # Extract trial number from field name
            trial_no = int(field[-1])

            # New info
            new_trial_name = new_info[f'TRIAL{trial_no}']
            new_trial_phone = new_info[f'T{trial_no}PHONE']
            new_trial_date = new_info[f'T{trial_no}DATE']

            # If new data is all blank, attempt to delete trial record
            if all([(info is None or info.strip()=='') for info in [new_trial_name,new_trial_phone,new_trial_date]]):
                self.sqlite_delete('trial', where_dict={'CLASS_ID':class_id, 'TRIAL_NO':trial_no})
            # Otherwise, insert/update trial record
            else:
                # Note: in the special case that a single trial is being added, we don't need to track
                # anything, so we use the true `trial_no` when creating the record
                new_trial_info = {'CLASS_ID' : class_id,
                                 'TRIAL_NO'  : trial_counter if len(trial_columns) > 1 else trial_no,
                                 'NAME'     : new_trial_name,
                                 'PHONE'    : new_trial_phone,
                                 'DATE'     : new_trial_date,
                                 'CREA_TMS' : datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
                                 'UPDT_TMS' : datetime.now().strftime('%m/%d/%Y %H:%M:%S')}
                unique_idx = ['CLASS_ID', 'TRIAL_NO']
                self.sqlite_upsert('trial', new_trial_info, unique_idx)

            trial_counter += 1


    def update_makeup_info(self, class_id, new_info):
        makeup_counter = 1 
        makeup_columns = [col_name for col_name in new_info.index if 'MAKEUP' in col_name]
        makeup_columns.sort()
        for field in makeup_columns:
            # Extract makeup number from field name
            makeup_no = int(field[-1])

            # New info
            new_makeup_name = new_info[f'MAKEUP{makeup_no}']
            new_makeup_date = new_info[f'M{makeup_no}DATE']

            # If both name and phone fields are blank, attempt to delete wait record
            if all([(info is None or info.strip()=='') for info in [new_makeup_name,new_makeup_date]]):
                self.sqlite_delete('makeup', where_dict={'CLASS_ID':class_id, 'MAKEUP_NO':makeup_no})
            # Otherwise, insert/update makeup record
            else:
                # Note: in the special case that a single makeup is being added, we don't need to track
                # anything, so we use the true `makeup_no` when creating the record
                new_makeup_info = {'CLASS_ID' : class_id,
                                   'MAKEUP_NO'  : makeup_counter if len(makeup_columns) > 1 else makeup_no,
                                   'NAME'     : new_makeup_name,
                                   'DATE'    : new_makeup_date,
                                   'CREA_TMS' : datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
                                   'UPDT_TMS' : datetime.now().strftime('%m/%d/%Y %H:%M:%S')}
                unique_idx = ['CLASS_ID', 'MAKEUP_NO']
                self.sqlite_upsert('makeup', new_makeup_info, unique_idx)

            makeup_counter += 1
    

    # Similar to `search_students`, but for classes. User selects options to filter down
    # list of classes (i.e. gender, class level, day of week)
    def filter_classes(self, filters):
         # Read in query from 'filter_classes.sql' as string
        with open(os.path.join(QUERY_DIR,'filter_classes.sql'), 'r') as sql_file:
            sql_script = sql_file.read()

        # Parameters used in query
        params = {'current_month'     : CURRENT_SESSION.month,
                  'current_year'      : CURRENT_SESSION.year, 
                  'instructor_filter' : f"%{filters['INSTRUCTOR']}%",
                  'gender_filter'     : f"%{filters['GENDER']}%",
                  'day_filter'        : f"%{filters['DAY']}%",
                  'level_filter'      : f"%{filters['LEVEL']}%"}

        # Query database and return results as DataFrame
        matches = pd.read_sql(sql_script, self.conn, params=params)
        return matches
    

    # Move student from one class to another based on the user's selected options.
    # This function is called by the `MoveStudentDialog` widget, so that we can retrieve 
    # the user-selected options here before the pop-up window closes.
    def move_student(self, student_id, current_class_id, new_class_id):
        current_record = pd.read_sql(f"SELECT * FROM class_student WHERE CLASS_ID={current_class_id} AND STUDENT_ID={student_id}",
                                     self.conn).squeeze()
        # Remove student from 'current class' (for new enrollments, current_record will be empty, and we do nothing)
        if not current_record.empty:
            self.unenroll_student(student_id, current_class_id, class_roll_only=False)

        # Next, enroll student in class associated with `new_class_id`
        self.enroll_student(student_id, new_class_id)


    # Enroll given student in the class associated with `class_id`
    def enroll_student(self, student_id, class_id):
        upsert_dict = {'CLASS_ID' : class_id,
                       'STUDENT_ID' : student_id}
        unique_idx = list(upsert_dict.keys())
        self.sqlite_upsert('class_student', upsert_dict, unique_idx)
    

    # Remove student from class associated with `class_id`
    def unenroll_student(self, student_id, class_id, wait_var=None,class_roll_only=True):
        if not class_roll_only:
            self.sqlite_delete('class_student',
                            where_dict={'CLASS_ID' : class_id,
                                        'STUDENT_ID' : student_id})
    
        # Change wait variable value to exit edit mode
        if wait_var:
            wait_var.set('done')


    # Function to insert record into SQLite database table.
    def sqlite_insert(self, table, row):
        cols = ', '.join(col for col in row.keys())
        vals = ', '.join(f"'{val}'" if val is not None else 'NULL' for val in row.values())
        sql = f"""INSERT INTO {table} ({cols})\n VALUES ({vals})"""
        self.cursor.execute(sql)
        self.conn.commit()


    # Function to update an existing record in SQLite database table.
    # If the record we request to update does not exist, nothing happens.
    def sqlite_update(self, table, new_info, where_dict):
        # `where_dict` is a dictionary that allows us to locate the record(s) which must be updated
        # The dictionary key is the column name(s), and the values are the actual values
        # (i.e. if we are updating the student table, where_dict={'STUDENT_ID' : <student id>}
        # and for a trial, where_dict={'CLASS_ID':<class id>, 'TRIAL_NO':<trial #>}
        set_clause = ', '.join([f'{field}="{value if value is not None else ''}"'\
                                for field,value in new_info.items()])
        where_clause = ' AND '.join([f'{field}="{value}"' for field,value in where_dict.items()])
        sql = f"""UPDATE {table} SET {set_clause} WHERE {where_clause}"""
        self.cursor.execute(sql)
        self.conn.commit()


    # Function to perform an insert/update in SQLite database depending on what is necessary.
    # The argument `unique_idx` is a list of column names which are considered to be a unique set
    # in the given `table`. If we attempt to insert a new record using values for the `unique_idx`
    # columns that already exist as a set in the database, the query will instead UPDATE
    # the existing record with the other values in `new_info`.
    #
    # (In simple terms, this function updates the relevant record if it already exists, otherwise
    #  it goes ahead and creates a new record)
    def sqlite_upsert(self, table, new_info, unique_idx):
        cols = ', '.join(col for col in new_info.keys())
        vals = ', '.join(f"'{val}'" if val is not None else 'NULL' for val in new_info.values())
        conflict_cols = ', '.join(col for col in unique_idx)
        set_clause = ', '.join(f'{col}=EXCLUDED.{col}' for col in new_info.keys() if col not in unique_idx)

        # Typically, resolve CONFLICT with an UPDATE, but if every key in `new_info`
        # also appears in `unique_idx`, resolve CONFLICTs with IGNORE
        conflict_clause = 'NOTHING' if len(set_clause)==0 else f'UPDATE SET\n {set_clause}'
        sql = f"""
            INSERT INTO {table} ({cols})
            VALUES ({vals})
            ON CONFLICT({conflict_cols}) DO {conflict_clause}
        """

        self.cursor.execute(sql)
        self.conn.commit()


    # Function to delete record from SQLite database table. If the record that we request
    # to delete does not exist, then nothing will happen.
    def sqlite_delete(self, table, where_dict):
        where_clause = ' AND '.join([f'{field}="{value}"' for field,value in where_dict.items()])
        sql = f"""DELETE FROM {table} WHERE {where_clause}"""
        self.cursor.execute(sql)
        self.conn.commit()


    # Backup SQLite database to individual CSV files. This is simply intended as an extra layer of caution
    # in case something unexpected happens with the '.db' file. Every time the user exits the program, they
    # will be prompted to perform this backup.
    def backup_sqlite_to_csv(self):
        # Create folder inside BACKUP_DIR based on current session (if doesn't exist)
        session =  f"{calendar.month_abbr[CURRENT_SESSION.month].upper()}{CURRENT_SESSION.year}"
        session_dir = os.path.join(BACKUP_DIR, session)
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
        # Create folder inside `session_dir` based on current day
        date_dir = os.path.join(session_dir, datetime.now().strftime('%b%d_%y').upper())
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)

        # Get names of all database tables as Pandas Series
        table_names = pd.read_sql("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name",
                                  self.conn
                       ).squeeze()
        
        # Loop through table names
        for table_name in table_names:
            # Load into Pandas DataFrame and then save out to CSV
            table_df = pd.read_sql(f"SELECT * FROM {table_name}", self.conn)
            table_df.to_csv(os.path.join(date_dir, f'{table_name}.csv'), index=False)


    # Given a date lower bound, grab student emails for all students enrolled since then
    def export_emails_to_csv(self, enrolldate_lower_bound, file_path):
         # Read in query from 'get_emails.sql' as string
        with open(os.path.join(QUERY_DIR,'get_emails.sql'), 'r') as sql_file:
            sql_script = sql_file.read()

        # Parameters used in query
        params = {'enrolldate_lower_bound' : enrolldate_lower_bound}

        # Query database and return results as DataFrame
        email_df = pd.read_sql(sql_script, self.conn, params=params)

        # 4. Save the file if a path was selected
        if file_path:
            email_df.to_csv(file_path, index=False)
            print(f"File saved at: {file_path}")
        else:
            print("Save cancelled.")


    def get_financial_summary(self, year):
         # Read in query from 'financial_summary.sql' as string
        with open(os.path.join(QUERY_DIR,'financial_summary.sql'), 'r') as sql_file:
            sql_script = sql_file.read()

        # Parameters used in query
        params = {'session_year' : year}

        # Query database and return results as DataFrame
        df = pd.read_sql(
            sql_script,
            self.conn,
            params=params,
            dtype={
                'year'                  : np.int32,
                'month'                 : np.int32,
                'paid_student_count'    : np.int32,
                'gross_paid'            : np.float64,
                'billed_student_count'  : np.int32,
                'gross_owed'            : np.float64,
            }    
        )
        return df
    

    def get_financial_as_of_today(self, year):
         # Read in query from 'financial_summary.sql' as string
        with open(os.path.join(QUERY_DIR,'financial_as_of_today.sql'), 'r') as sql_file:
            sql_script = sql_file.read()

        # Parameters used in query
        params = {'session_year' : year}

        # Query database and return results as DataFrame
        df = pd.read_sql(
            sql_script,
            self.conn,
            params=params,
            dtype={
                'year'                  : np.int32,
                'month'                 : np.int32,
                'paid_student_count'    : np.int32,
                'gross_paid'            : np.float64,
            }    
        )
        return df.squeeze()