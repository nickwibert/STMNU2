import os
import shutil
import re
import pandas as pd
import functions as fn
import dbf
import sqlite3
import calendar
from datetime import datetime

# Global variables
from globals import CURRENT_SESSION, CALENDAR_DICT, QUERY_DIR

class StudentDatabase:
    def __init__(self, student_dbf_path, student_prev_year_dbf_path, clsbymon_dbf_path, do_not_load=[], update_active=False):
        self.update_active = update_active
        self.do_not_load = do_not_load
        # DBF Table object for STUD00
        self.student_dbf = dbf.Table(student_dbf_path)
         # Add or modify 'ACTIVE' in DBF
        with self.student_dbf:
            if update_active:
                if 'ACTIVE' not in self.student_dbf.field_names:
                    self.student_dbf.add_fields('ACTIVE L')
                for record in self.student_dbf:
                    dbf.write(record, ACTIVE=False)
        # DBF Table object for STUD99 (student/payment records for previous year)
        self.student_prev_year_dbf = dbf.Table(student_prev_year_dbf_path)
        # DBF Table object for clsbymon.dbf
        self.classes_dbf = dbf.Table(clsbymon_dbf_path)
         # Add 'CLASS_ID' to clsbymon DBF file (if it doesn't exist)
        with self.classes_dbf:
            if 'CLASS_ID' not in self.classes_dbf.field_names:
                self.classes_dbf.add_fields('CLASS_ID N(3,0)')
                class_id = 1
                for record in self.classes_dbf: 
                    dbf.write(record, CLASS_ID=class_id)
                    class_id += 1

        # Variable to track whether the user has entered the payment password yet.
        # Once the user has entered the password once, they should not be asked again
        self.request_password = True
        
        # SQLite database connection
        self.conn = sqlite3.connect('C:\\STMNU2\\data\\database.db')
        self.cursor = self.conn.cursor()

    # Load data from DBF files (old dBASE program), transform to relational database,
    # then create and populate a SQLite database. 
    # (Note: once the old program is decommissioned, this function wil be deprecated,
    # as the data will always be current in the SQLite database and we will no longer
    # need to perform a data load upon launch)
    def load_data_from_dbase(self):
        # Transform current versions of DBF files to CSV
        fn.dbf_to_csv('STUD00.dbf')
        fn.dbf_to_csv('STUD99.dbf')
        fn.dbf_to_csv('clsbymon.dbf')

        # Transform from old representation to relational database structure,
        # and save as CSV files to `BACKUP_DIR`
        fn.transform_to_rdb(do_not_load=self.do_not_load, update_active=self.update_active, save_as='.csv')

        # Create empty tables in SQLite database
        fn.create_sqlite()
        # Populate tables with data (for tables included in `do_not_load`, this will
        # simply be the existing data from SQLite; otherwise it is overwritten with 
        # data loaded from dBASE)
        fn.populate_sqlite_from_csv(self.do_not_load)


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
    

    # Create new student record in `student` and `STUD00`
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
                                 'CREA_TMS'   : datetime.now(),
                                 'UPDT_TMS'   : datetime.now()})
        
        ## Step 1: Insert into SQLite database
        self.sqlite_insert('student', {k:v for k,v in new_student_info.items() if k not in ['MOMNAME','DADNAME']})

        # Create guardian records (if provided)
        for guardian_type in ['MOM','DAD']:
            if f'{guardian_type}NAME' in new_student_info.keys():
                # Collect data into dict
                guardian_info = {'GUARDIAN_ID' : self.guardian.shape[0]+1,
                                'FAMILY_ID'    : new_family_id,
                                'RELATION'     : guardian_type,
                                'FNAME'        : new_student_info[f'{guardian_type}NAME'],
                                'LNAME'        : new_student_info['LNAME'],
                                'CREA_TMS'     : datetime.now(),
                                'UPDT_TMS'     : datetime.now()}
                # Insert into database
                self.sqlite_insert('guardian', guardian_info)

        ## Step 2: Create new record for this student in original database (DBF file)
        # Special handling for dates
        for field in ['ENROLLDATE', 'BIRTHDAY']:
            if field in new_student_info.keys():
                new_student_info[field] = datetime.strptime(new_student_info[field], "%m/%d/%Y")

        # For string fields, make sure they are in all-uppercase before updating DBF file
        for field, entry in entry_boxes.items():
            if entry.get() and entry.dtype == 'string':
                new_student_info[field] = entry.get().upper()

        ## (Note: create this student in both current/previous year databases, in case user enters payments for last year)
        for table_to_update in (self.student_dbf, self.student_prev_year_dbf):
            with table_to_update:
                # Drop any fields that appear in `new_student_info` which are not present in the DBF file
                new_student_info = {field:value for field,value in new_student_info.items() if field in table_to_update.field_names}
                # Append record to DBF table
                table_to_update.append(new_student_info) 

    # Update student info in both old/new databases
    # (Note: In old DBF database, payments and guardian info are stored with the student record,
    # so when the user edits any student or payment info, this function is run)
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
        
        # Determine new guardian ID if we need to create a new record
        self.cursor.execute("SELECT MAX(CAST(GUARDIAN_ID AS integer))+1 AS NEW_GUARDIAN_ID FROM guardian")
        new_guardian_id = self.cursor.fetchone()[0]

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


        ## Step 1: Update student info in the Pandas dataframe
        # Update payments
        if 'PAYMENT' in edit_type:
            self.update_payment_info(student_id, new_student_info, year)
            # SPECIAL HANDLING: Rename reg fee fields to match DBF before Step 2
            new_student_info['REGFEE'] = new_student_info.pop('REGPAY')
            new_student_info['REGFEEDATE'] = new_student_info.pop('REGDATE')
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
                        new_guardian_record = {'GUARDIAN_ID'  : new_guardian_id if guardian_record.empty else guardian_record['GUARDIAN_ID'],
                                           'FAMILY_ID'    : family_id,
                                           'RELATION'     : relation,
                                           'FNAME'        : new_student_info[f'{relation}NAME'],
                                           'LNAME'        : new_student_info['LNAME'],
                                           'CREA_TMS'     : datetime.now(),
                                           'UPDT_TMS'     : datetime.now()}
                        unique_idx = ['FAMILY_ID', 'RELATION']
                        self.sqlite_upsert('guardian', new_guardian_record, unique_idx)
                        # If we created a new guardian record, increment new_guardian_id
                        if new_guardian_id == new_guardian_record['GUARDIAN_ID']:
                            new_guardian_id += 1

            new_student_info_sqlite = {k:v for k,v in new_student_info.items() if k not in ['MOMNAME','DADNAME']}

            new_student_info_sqlite.update({'UPDT_TMS' : datetime.now()})
            self.sqlite_update('student',
                               new_student_info_sqlite,
                               where_dict={'STUDENT_ID' : student_id})

        ## Step 2: Update student info in original database (DBF file)
        
        # Determine which STUD dbf to use (current year or previous year)
        if year == CURRENT_SESSION.year:
            table_to_update = self.student_dbf
        else:
            table_to_update = self.student_prev_year_dbf

        with table_to_update:
            studentno_idx = table_to_update.create_index(lambda rec: rec.studentno)
            # get a list of all matching records
            match = studentno_idx.search(match=studentno)
            # should only be one student with that studentno
            record = match[0]
            # Focus on this student's record
            with record:
                # Loop through each field
                for field in new_student_info.keys():
                    # Get info about this field in the dbf file
                    field_info = table_to_update.field_info(field)
                    # Convert date fields to proper format
                    if str(field_info.py_type) == "<class 'datetime.date'>":
                        if new_student_info[field] is not None:
                            new_student_info[field] = datetime.strptime(new_student_info[field], "%m/%d/%Y")
                    # Special case: there may be fields which have no restrictions in the new program,
                    # but still must be truncated to fit in the old program.
                    elif len(str(new_student_info[field])) > field_info.length:
                        new_student_info[field] = str(new_student_info[field])[:field_info.length]
                        
                    # Special case: for payment dates, if the payment value is blank or zero, delete date
                    if 'DATE' in field and 'ENROLL' not in field:
                        prefix = field[:-4]
                        pay_field = prefix + 'PAY' if 'REG' not in prefix else 'REGFEE'
                        pay = new_student_info[pay_field]
                        record[field] = new_student_info[field] if pay not in (None,'',0,'0.00') else None
                    # For this record, if the dbase field does not match the user-entered field,
                    # update that field in the dbf file (if the field is unchanged, ignore)
                    elif record[field] != new_student_info[field]:
                        record[field] = new_student_info[field]


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

        ## Step 1: Update SQLite
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


        ## Step 2: Update student info in original database (DBF file)
        if year == CURRENT_SESSION.year:
            table_to_update = self.student_dbf
        else:
            table_to_update = self.student_prev_year_dbf

        self.cursor.execute(f'SELECT STUDENTNO FROM student WHERE STUDENT_ID={student_id}')
        studentno = self.cursor.fetchone()[0]
        with table_to_update:
            studentno_idx = table_to_update.create_index(lambda rec: rec.studentno)
            # get a list of all matching records
            match = studentno_idx.search(match=studentno)
            # should only be one student with that studentno
            record = match[0]
            # Focus on this student's record
            with record:
                bill_txt = '*' if bill_record.empty else ''
                record[f'{month}BILL'] = bill_txt


    # Create/delete/modify payments for a given student in the `payment` table
    def update_payment_info(self, student_id, new_info, year):
        ## SQLite database
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
                        'CREA_TMS'     : datetime.now(),
                        'UPDT_TMS'     : datetime.now()}
            self.sqlite_upsert('note', new_info, unique_idx)
        # Otherwise, attempt to delete note 
        else:
            self.sqlite_delete('note', where_dict={id_field : id})

        ## Step 2: Update DBF file
        if 'STUDENT' in edit_type:
            table_to_update = self.student_dbf
            # 'STUD00' has 3 columns for notes
            note_cols = [f'NOTE{i}' for i in range(1,4)]
            field = 'STUDENTNO'
            self.cursor.execute(f'SELECT STUDENTNO FROM student WHERE STUDENT_ID={id}')
            record_no = self.cursor.fetchone()[0]
        else:
            table_to_update = self.classes_dbf
            # 'clsbymon.dbf' has 4 columns for notes
            note_cols = [f'NOTE{i}' for i in range(1,5)]
            # For classes, CLASS_ID is the same in `classes.csv` and in the `clsbymon.dbf`
            field = 'CLASS_ID'
            record_no = id

        # Get rid of any newline characters (causes issues in old program)
        note_txt = note_txt.replace('\n', ' ')

        with table_to_update:
            idx = table_to_update.create_index(lambda rec: rec[field])
            # get a list of all matching records
            match = idx.search(match=record_no)
            # should only be one student with that studentno
            record = match[0]

            with record:
                # Loop through every note column
                for col in note_cols:
                    # Determine max byte size of this field in the DBF file
                    max_length = table_to_update.field_info(col).length
                    # Store up to `max_length` characters in column
                    record[col] = note_txt[:max_length].strip()
                    # Delete first `max_length` characters and continue
                    note_txt = note_txt[max_length:].strip()
                        

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


        ## Step 1: Send to other functions to update relevant tables in SQLite
        if 'WAIT' in edit_type:
            self.update_wait_info(class_id, new_info)
        elif 'TRIAL' in edit_type:
            self.update_trial_info(class_id, new_info)
        elif 'MAKEUP' in edit_type:
            self.update_makeup_info(class_id, new_info)
            # Break out of function, since there are no makeups in DBF files
            return


        ## Step 2: Update student info in original database (DBF file)
        with self.classes_dbf:
            class_id_idx = self.classes_dbf.create_index(lambda rec: rec.class_id)
            # get a list of all matching records
            match = class_id_idx.search(match=class_id)
            # should only be one student with that studentno
            record = match[0]
            # Focus on this student's record
            with record:
                # Loop through each field
                for field in new_info.keys():
                    try:
                        # Get info about this field in the dbf file
                        field_info = self.classes_dbf.field_info(field)

                        # Convert date fields to proper format
                        if str(field_info.py_type) == "<class 'datetime.date'>":
                            if new_info[field] is not None and len(new_info[field]) > 0:
                                new_info[field] = datetime.strptime(new_info[field], "%m/%d/%Y")
                        # Special case: there may be fields which have no restrictions in the new program,
                        # but still must be truncated to fit in the old program.
                        elif len(str(new_info[field])) > field_info.length:
                            new_info[field] = str(new_info[field])[:field_info.length]
                        # For this record, if the dbase field does not match the user-entered field,
                        # update that field in the dbf file (if the field is unchanged, ignore)
                        if record[field] != new_info[field]:
                            record[field] = new_info[field]
                    # If field does not exist in DBF file, ignore this data and move to the next field
                    except dbf.exceptions.FieldMissingError as err:
                        print(err.args[0])
                        continue



    def update_wait_info(self, class_id, new_info):
        # `wait_counter` tracks how many waitlists have been entered as we loop through
        # all 4 placeholder fields. This is done so that if a gap exists in the 
        # middle of the waitlist, all the entries will shift upward.
        wait_counter = 1
        wait_columns = [col_name for col_name in new_info.index if 'WAIT' in col_name]
        for field in wait_columns:
            # Extract wait number from field name
            wait_no = int(field[-1])
            # Get existing record for this waitlist entry (if exists)
            wait_record = pd.read_sql(f"""SELECT *
                                          FROM wait 
                                          WHERE CLASS_ID={class_id} AND WAIT_NO={wait_no}""",
                                    self.conn).squeeze()

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
                                 'CREA_TMS' : datetime.now(),
                                 'UPDT_TMS' : datetime.now()}
                unique_idx = ['CLASS_ID', 'WAIT_NO']
                self.sqlite_upsert('wait', new_wait_info, unique_idx)
                wait_counter += 1

    def update_trial_info(self, class_id, new_info):
        # `trial_counter` tracks how many trials have been entered as we loop through
        # all 8 placeholder fields. This is done so that if a gap exists in the 
        # middle of the trials, all the entries will shift upward.
        trial_counter = 1 
        trial_columns = [col_name for col_name in new_info.index if 'TRIAL' in col_name]
        for field in trial_columns:
            # Extract trial number from field name
            trial_no = int(field[-1])
            # Get existing record for this trial entry (if exists)
            trial_record = pd.read_sql(f"""SELECT *
                                          FROM trial 
                                          WHERE CLASS_ID={class_id} AND TRIAL_NO={trial_no}""",
                                    self.conn).squeeze()

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
                                 'CREA_TMS' : datetime.now(),
                                 'UPDT_TMS' : datetime.now()}
                unique_idx = ['CLASS_ID', 'TRIAL_NO']
                self.sqlite_upsert('trial', new_trial_info, unique_idx)
                trial_counter += 1


    def update_makeup_info(self, class_id, new_info):
        makeup_counter = 1 
        makeup_columns = [col_name for col_name in new_info.index if 'MAKEUP' in col_name]
        for field in makeup_columns:
            # Extract makeup number from field name
            makeup_no = int(field[-1])
            # Get existing record for this makeup entry (if exists)
            makeup_record = pd.read_sql(f"""SELECT *
                                            FROM makeup 
                                            WHERE CLASS_ID={class_id} AND MAKEUP_NO={makeup_no}""",
                                        self.conn).squeeze()

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
                                   'CREA_TMS' : datetime.now(),
                                   'UPDT_TMS' : datetime.now()}
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


    # Enroll student in class associated with `class_id`
    # This function appends the relevant record to `class_student` before modifying the DBF files
    # to 1) add student to `clsbymon.dbf` if they are paid for the current month,
    # and 2) add instructor/daytime information to the student's record in `STUD00.dbf`
    def enroll_student(self, student_id, class_id):
        ## STEP 1: Update SQLite
        upsert_dict = {'CLASS_ID' : class_id,
                       'STUDENT_ID' : student_id}
        unique_idx = list(upsert_dict.keys())
        self.sqlite_upsert('class_student', upsert_dict, unique_idx)

        ## STEP 2: Update original database (DBF file)
        # Get 'STUDENTNO' and name corresponding to the selected 'student_id'
        student_info = pd.read_sql(f"SELECT * FROM student WHERE STUDENT_ID={student_id}",
                                   self.conn).squeeze()
        studentno = int(student_info['STUDENTNO'])
        student_name = student_info['FNAME'] + ' ' + student_info['LNAME']
        # STUDENTNO columns (NUMB1, NUMB2, ...)
        studentno_cols = [col for col in self.classes_dbf.field_names if 'NUMB' in col]

        # Get class info for new class
        new_class_info = pd.read_sql(f"SELECT * FROM classes WHERE CLASS_ID={class_id}",
                                     self.conn).squeeze()
        teach_cols, daytime_cols = ['INSTRUCTOR', 'INST2', 'INST3'], ['DAYTIME','DAYTIME2','DAYTIME3']
        # Store student's payment for the current month/year, if it exists
        pay_record = pd.read_sql(f"""SELECT *
                                     FROM payment
                                     WHERE STUDENT_ID={student_id}
                                        AND MONTH={CURRENT_SESSION.month}
                                        AND YEAR={CURRENT_SESSION.year}""",
                                 self.conn).squeeze()

        # Open 'clsbymon.dbf'
        with self.classes_dbf:
            class_id_idx = self.classes_dbf.create_index(lambda rec: rec.class_id)

            # Get DBF record corresponding to new class
            # We should only enroll the student in the new class (place them in `clsbymon`) if they are paid for the current month.
            # If they haven't paid yet, do not modify the DBF file.
            if not pay_record.empty:
                # Get DBF record corresponding to new class
                record = class_id_idx.search(match=class_id)[0]
                with record:
                    # Loop through each student column
                    for field in studentno_cols:
                        # If student is already present, end function (this prevents enrolling the student in the same class twice)
                        if record[field] == studentno:
                            break
                        # Put student into the first blank spot
                        elif record[field] == 0:
                            record[field] = studentno
                            record[f'STUDENT{field[4:]}'] = student_name
                            # Fill a spot by subtracting 1 from 'AVAILABLE' column
                            record['AVAILABLE'] -= 1
                            break

        # Next, we need to modify STUD00.dbf, as the instructor/daytime which are displayed in a student's record
        # are stored here in the old program. For this step, we do not care if the student has paid or not,
        # whether they are active or not, etc. This allows the user to move students from one class to another,
        # or enroll them in a new class, regardless of their active or payment status. The student will
        # get populated into relevant class rolls later whenever they are marked active and a payment is entered for current month.

        # Open `STUD00.dbf`
        with self.student_dbf:
            studentno_idx = self.student_dbf.create_index(lambda rec: rec.studentno)
            # Get DBF record corresponding to student
            record = studentno_idx.search(match=studentno)[0]

            # Add new instructor/daytime to student's record
            with record:
                # Track duplicate classtimes
                student_enrolled = False
                # Loop through each instructor/daytime pair in STUD00
                for teach_col, daytime_col in list(zip(teach_cols, daytime_cols)):
                    # Check if instructor/daytime is already present
                    if record[teach_col].strip() == new_class_info['TEACH'] and record[daytime_col].strip() == new_class_info['CLASSTIME']:
                        # If this is a DUPLICATE classtime for the student, make sure we reset it to blank
                        if student_enrolled:
                            record[teach_col] = ''
                            record[daytime_col] = ''
                        else:
                            student_enrolled = True
                    # Put instructor/daytime into first blank spot (if not already enrolled)
                    elif record[teach_col].strip() == '' and not student_enrolled:
                        record[teach_col] = new_class_info['TEACH']
                        record[daytime_col] = new_class_info['CLASSTIME']
                        student_enrolled = True
    

    # Remove student from class associated with `class_id`
    # This function deletes the relevant record to `class_student` before modifying the DBF files
    # to 1) remove student from `clsbymon.dbf` if they are present,
    # and 2) remove instructor/daytime information from the student's record in `STUD00.dbf`
    def unenroll_student(self, student_id, class_id, wait_var=None,class_roll_only=True):
        ## STEP 1B: Update SQLite
        if not class_roll_only:
            self.sqlite_delete('class_student',
                            where_dict={'CLASS_ID' : class_id,
                                        'STUDENT_ID' : student_id})

        ## STEP 2: Remove student from class roll in DBF file
        self.cursor.execute(f'SELECT STUDENTNO FROM student WHERE STUDENT_ID={student_id}')
        studentno = self.cursor.fetchone()[0]
        studentno_cols = [col for col in self.classes_dbf.field_names if 'NUMB' in col]

        # Open 'clsbymon.dbf'
        with self.classes_dbf:
            class_id_idx = self.classes_dbf.create_index(lambda rec: rec.class_id)

            # Get DBF record corresponding to current (old) class
            record = class_id_idx.search(match=class_id)[0]
            with record:
                # Loop through each student column
                for field in studentno_cols:
                    # Check if this is the student we wish to remove
                    if record[field] == studentno:
                        # If so, delete this studentno and student name from the class
                        record[field] = 0
                        record[f'STUDENT{field[4:]}'] = None
                        # Open up a spot by adding 1 to 'AVAILABLE' column
                        record['AVAILABLE'] += 1
                        break

        # If class_roll_only == True, we are just removing the student from the class roll,
        # but want to leave the class information in their student record.
        if not class_roll_only:
            class_info = pd.read_sql(f"SELECT * FROM classes WHERE CLASS_ID={class_id}",
                                     self.conn).squeeze()
            teach_cols, daytime_cols = ['INSTRUCTOR', 'INST2', 'INST3'], ['DAYTIME','DAYTIME2','DAYTIME3']

            # Open `STUD00.dbf`
            with self.student_dbf:
                studentno_idx = self.student_dbf.create_index(lambda rec: rec.studentno)
                # Get DBF record corresponding to student
                record = studentno_idx.search(match=studentno)[0]

                # Remove instructor/daytime from student's record
                with record:
                    # Loop through each instructor/daytime pair in STUD00
                    for teach_col, daytime_col in list(zip(teach_cols, daytime_cols)):
                        # Check if this is the class we wish to remove
                        if record[teach_col].strip() == class_info['TEACH'] and record[daytime_col].strip() == class_info['CLASSTIME']:
                            # If so, delete this instructor and daytime from the student's record
                            record[teach_col] = ''
                            record[daytime_col] = ''

                    # Loop through each instructor/daytime pair AGAIN to make sure the classes get shifted up (if needed)
                    previous_class_info = {'TEACH_placeholder' : 'teach', 'CLASSTIME_placeholder' : 'classtime'}
                    for teach_col, daytime_col in list(zip(teach_cols, daytime_cols)):
                        # If the previous classtime values are blank...
                        if not any([val.strip() for val in previous_class_info.values()]):
                            # And the current classtime values are NOT blank, shift them to the previous pair of fields
                            if record[teach_col].strip() != '':
                                for field in previous_class_info.keys():
                                    record[field] = record[teach_col] if 'INS' in field else record[daytime_col]
                                    
                                record[teach_col] = ''
                                record[daytime_col] = ''
                        # Set the current classtime values to 'previous' and continue
                        previous_class_info = {teach_col : record[teach_col], daytime_col : record[daytime_col]}



                            
                            

    
        # Change wait variable value to exit edit mode
        if wait_var:
            wait_var.set('done')

    # Function to insert record into SQLite database table.
    def sqlite_insert(self, table, row):
        cols = ', '.join(col for col in row.keys())
        vals = ', '.join(f"'{val}'" if val is not None else 'NULL' for val in row.values())
        sql = f'INSERT INTO {table} ({cols})\n VALUES ({vals})'
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
        sql = f'UPDATE {table} SET {set_clause} WHERE {where_clause}'
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
        sql = f'DELETE FROM {table} WHERE {where_clause}'
        self.cursor.execute(sql)
        self.conn.commit()


