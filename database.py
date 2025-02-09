import os
import shutil
import re
import pandas as pd
import functions as fn
import dbf
import calendar
from datetime import datetime

# Global variables
from globals import CURRENT_SESSION

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

    def load_data(self):
        # Transform current versions of DBF files to CSV
        fn.dbf_to_csv('STUD00.dbf')
        fn.dbf_to_csv('STUD99.dbf')
        fn.dbf_to_csv('clsbymon.dbf')
        # Update files representing relational database structure
        fn.transform_to_rdb(data_path='C:\\STMNU2\\data', save_to_path='C:\\STMNU2\\data\\rdb_format', write_to_csv=True,
                            do_not_load=self.do_not_load, update_active=self.update_active)

        # CSV paths
        rdb_folder_path = 'C:\\STMNU2\\data\\rdb_format'
        filenames = [filename for filename in os.listdir('C:\\STMNU2\\data\\rdb_format') if filename != 'BACKUP']
        self.csv_paths = {filename.split('.')[0] : os.path.join(rdb_folder_path,filename) for filename in filenames}
        self.backup_paths = {filename.split('.')[0] : os.path.join(rdb_folder_path,'BACKUP',filename) for filename in filenames}

        # Load student
        self.student = pd.read_csv(self.csv_paths['student']).convert_dtypes()
        # Drop the rows where name is completely missing
        self.student = self.student.dropna(subset=['FNAME','LNAME']).reset_index(drop=True)
        # Format dates
        for col in ['BIRTHDAY', 'ENROLLDATE', 'REGFEEDATE']:
            self.student[col] = pd.to_datetime(self.student[col], errors='coerce', format='mixed').dt.strftime('%m/%d/%Y')

        self.student['ACTIVE'] = self.student['ACTIVE'].astype(bool)
        if self.update_active:
            with self.student_dbf:
                for record in self.student_dbf:
                    with record:
                        studentno = record['STUDENTNO']
                        if studentno in self.student['STUDENTNO'].values:
                            record['ACTIVE'] = self.student.loc[self.student['STUDENTNO']==studentno,'ACTIVE'].values[0]
                        else:
                            record['ACTIVE'] = False

        # Load payment
        self.payment = pd.read_csv(self.csv_paths['payment'])
        # Format dates
        for col in ['DATE']:
            self.payment[col] = pd.to_datetime(self.payment[col], errors='coerce', format='mixed').dt.strftime('%m/%d/%Y')

        # Load bill
        self.bill = pd.read_csv(self.csv_paths['bill'])

        # Load classes
        self.classes = pd.read_csv(self.csv_paths['classes'])

        # Load class_student
        self.class_student = pd.read_csv(self.csv_paths['class_student'])

        # Load guardian
        self.guardian = pd.read_csv(self.csv_paths['guardian'])

        # Load note
        self.note = pd.read_csv(self.csv_paths['note'])

        # Load trial students
        self.trial = pd.read_csv(self.csv_paths['trial'])
        for col in ['DATE']:
            self.trial[col] = pd.to_datetime(self.trial[col], errors='coerce', format='mixed').dt.strftime('%m/%d/%Y')

        # Load waitlist students
        self.wait = pd.read_csv(self.csv_paths['wait'])

    # Export all of the tables as csv files
    def save_data(self, backup=False):
        # Save out all changes made during current run of program
        self.guardian.to_csv(self.csv_paths['guardian'],index=False)
        self.student.to_csv(self.csv_paths['student'],index=False)
        self.payment.to_csv(self.csv_paths['payment'],index=False)
        self.bill.to_csv(self.csv_paths['bill'],index=False)
        self.classes.to_csv(self.csv_paths['classes'],index=False)
        self.class_student.to_csv(self.csv_paths['class_student'],index=False)
        self.wait.to_csv(self.csv_paths['wait'],index=False)
        self.trial.to_csv(self.csv_paths['trial'],index=False)
        self.note.to_csv(self.csv_paths['note'],index=False)

        # If backup requested, copy the above files into the BACKUP folder
        if backup:
            for table in self.csv_paths.keys():
                shutil.copy(src=self.csv_paths[table], dst=self.backup_paths[table])


    def search_student(self, query, show_inactive=False):
        # Force all uppercase
        for key in query.keys(): query[key] = query[key].upper()
        
        # Perform search using name fields
        matches = self.student[(((self.student['FNAME'].str.upper().str.startswith(query['First Name'], na=False)) | (len(query['First Name']) == 0))
                            & ((self.student['LNAME'].str.upper().str.startswith(query['Last Name'], na=False)) | (len(query['Last Name']) == 0))
                            & (self.student['ACTIVE'] | show_inactive))
                            ].sort_values(by=['LNAME','FNAME'], key=lambda x: x.str.upper()
                            ).loc[:, ['STUDENT_ID', 'FNAME','LNAME']
                            ].fillna(''
                            ).reset_index(drop=True)
        
        return matches
    

    # Create new student record in `student` and `STUD00`
    def create_student(self, entry_boxes):
        # Extract all (non-blank) user entries
        new_student_info = {field : entry.get() for (field,entry) in entry_boxes.items() if entry.get()}
        new_family_id = self.student['FAMILY_ID'].max()+1
        # Add other fields in `student` table
        new_student_info.update({'STUDENT_ID' : self.student.shape[0]+1,
                                 'ACTIVE'     : True,
                                 'FAMILY_ID'  : new_family_id,
                                 'STUDENTNO'  : self.student['STUDENTNO'].max()+1,
                                 'ENROLLDATE' : datetime.today().strftime('%m/%d/%Y'),
                                 'REGFEE'     : 0,
                                 'MONTHLYFEE' : 0,
                                 'BALANCE'    : 0,
                                 'CREA_TMS'   : datetime.now(),
                                 'UPDT_TMS'   : datetime.now()})
        
        ## Step 1: Create new record for this student in Pandas DataFrame
        self.student.loc[len(self.student)] = new_student_info
        self.student.to_csv(self.csv_paths['student'], index=False)

        # Create guardian records (if provided)
        for guardian_type in ['MOM','DAD']:
            if f'{guardian_type}NAME' in new_student_info.keys():
                guardian_info = {'GUARDIAN_ID' : self.guardian.shape[0]+1,
                                'FAMILY_ID'    : new_family_id,
                                'RELATION'     : guardian_type,
                                'FNAME'        : new_student_info[f'{guardian_type}NAME'],
                                'LNAME'        : new_student_info['LNAME'],
                                'CREA_TMS'     : datetime.now(),
                                'UPDT_TMS'     : datetime.now()}
                self.guardian.loc[len(self.guardian)] = guardian_info

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


    def update_student_info(self, student_id, entry_boxes, edit_type, year=CURRENT_SESSION.year):
        # Get dataframe index associated with 'student_id'
        student_idx = self.student[self.student['STUDENT_ID'] == student_id].index[0]
        # Student number associated with the edited student
        studentno = self.student.iloc[student_idx]['STUDENTNO']
        family_id = self.student.iloc[student_idx]['FAMILY_ID']

        # Guardian index
        guardian_info = self.guardian.loc[self.guardian['FAMILY_ID'] == family_id]

        new_values = [entry.get().strip() for entry in entry_boxes.values()]
        new_student_info = pd.Series({k:v for (k,v) in zip(entry_boxes.keys(), new_values)})
        for field in new_student_info.index:
            if len(new_student_info[field]) == 0:
                new_student_info[field] = 0 if entry_boxes[field].dtype == 'float' else None
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
        # Otherwise, update student and guardian tables
        else:
            # Loop through fields
            for field in entry_boxes.keys():
                # For MOMNAME and DADNAME, we update `guardian`
                if field in ['MOMNAME','DADNAME']:
                    relation = field[:3]
                    is_blank = new_student_info[f'{relation}NAME'] is None or new_student_info[f'{relation}NAME'].strip()==''
                    guardian_record = guardian_info.loc[guardian_info['RELATION']==relation]
                    # Check that guardian record exists
                    if not guardian_record.empty:
                        # If new value is blank, delete guardian record
                        if is_blank:
                            self.guardian = self.guardian.drop(guardian_record.index).reset_index(drop=True)
                        # Otherwise, modify existing guardian record
                        else:
                            self.guardian.loc[
                                ((self.guardian['FAMILY_ID'] == family_id)
                                & (self.guardian['RELATION'] == relation)), 'FNAME'] = new_student_info[field]
                    # If guardian record does not exist...
                    else:
                        # ... and new value is not blank...
                        if not is_blank:
                            # ...create new guardian record
                            family_id = family_id if not pd.isna(family_id) else self.guardian['FAMILY_ID'].max(skipna=True)+1
                            self.student.loc[student_idx,'FAMILY_ID'] = family_id
                            guardian_record = {'GUARDIAN_ID' : self.guardian.shape[0]+1,
                                            'FAMILY_ID'    : family_id,
                                            'RELATION'     : relation,
                                            'FNAME'        : new_student_info[f'{relation}NAME'],
                                            'LNAME'        : new_student_info['LNAME'],
                                            'CREA_TMS'     : datetime.now(),
                                            'UPDT_TMS'     : datetime.now()}
                            self.guardian.loc[len(self.guardian)] = guardian_record
                # Otherwise edit 'student' table
                else:
                    self.student.loc[student_idx, field] = new_student_info[field] 
        

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
                    # Special case: for payment dates, if the payment value is blank or zero, delete date
                    if 'DATE' in field and 'ENROLL' not in field:
                        prefix = field[:-4]
                        pay_field = prefix + 'PAY' if prefix!='REGFEE' else 'REGFEE'
                        pay = new_student_info[pay_field]
                        record[field] = new_student_info[field] if pay not in (None,'',0,'0.00') else None
                    # For this record, if the dbase field does not match the user-entered field,
                    # update that field in the dbf file (if the field is unchanged, ignore)
                    elif record[field] != new_student_info[field]:
                        record[field] = new_student_info[field]

    # Toggle 'ACTIVE' value for selected student between True/False
    def activate_student(self, student_id):
        # Step 1: Pandas DataFrame
        student_record = self.student[self.student['STUDENT_ID'] == student_id]
        self.student.loc[student_record.index, 'ACTIVE'] = not student_record['ACTIVE'].values[0]
        

    # Create/delete a `bill` record for the selected student, month, year
    def bill_student(self, student_id, month_num, year):
        month = calendar.month_abbr[month_num].upper() if month_num < 13 else 'REG'
        # Step 1: Pandas DataFrame
        bill_record = self.bill.loc[((self.bill['STUDENT_ID'] == student_id)
                                     & (self.bill['MONTH'] == month_num)
                                     & (self.bill['YEAR'] == year))]
        # If this bill does not exist, create record
        if bill_record.empty:
            self.bill.loc[len(self.bill)] = {'STUDENT_ID' : student_id,
                                             'MONTH'      : month_num,
                                             'YEAR'       : year}
        # If this month/year appears in 'bill' for this student (meaning they owed),
        # delete that bill record to indicate that the payment has been made
        if not bill_record.empty:
            self.bill = self.bill.drop(bill_record.index).reset_index(drop=True)

        ## Step 2: Update student info in original database (DBF file)
        if year == CURRENT_SESSION.year:
            table_to_update = self.student_dbf
        else:
            table_to_update = self.student_prev_year_dbf

        studentno = self.student.loc[self.student['STUDENT_ID'] == student_id, 'STUDENTNO'].squeeze()
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
        for field in new_info.index:
            # For now, reg. fee is stored in `student`
            if 'REG' in field:
                self.student.loc[self.student['STUDENT_ID']==student_id,field] = new_info[field]
                continue
    
            # Integer corresponding to the month this payment applies to
            month_num = list(calendar.month_abbr).index(field[:3].title())
            # Get existing record for this payment/bill (if exists)
            pay_record = self.payment[(self.payment['STUDENT_ID'] == student_id)
                                    & (self.payment['MONTH'] == month_num)
                                    & (self.payment['YEAR'] == year)]
            bill_record = self.bill[(self.bill['STUDENT_ID'] == student_id)
                                & (self.bill['MONTH'] == month_num)
                                & (self.bill['YEAR'] == year)]
            
            if pay_record.empty:
                # If payment record does not exist, and payment is non-zero, create new payment record
                if 'PAY' in field and new_info[field] not in (None, 0.0, '0.00'):
                    self.payment.loc[len(self.payment)] = {'STUDENT_ID' : student_id,
                                                           'MONTH'      : month_num,
                                                           'PAY'        : new_info[field],
                                                           'YEAR'       : year}
                    # If this month/year appears in 'bill' for this student (meaning they owed),
                    # delete that bill record to indicate that the payment has been made
                    if not bill_record.empty:
                        self.bill = self.bill.drop(bill_record.index).reset_index(drop=True)

                    # If payment record has been created for CURRENT MONTH, place student in class roll
                    # and make sure they are marked as active
                    if month_num == CURRENT_SESSION.month:
                        self.student.loc[self.student['STUDENT_ID']==student_id,'ACTIVE'] = True
                        for class_id in self.class_student.loc[self.class_student['STUDENT_ID']==student_id,'CLASS_ID'].values:
                            self.enroll_student(student_id, class_id)

            # If record already exists, but the new amount entered is zero, delete the record
            # (therefore changing a payment amount to 0 is equivalent to deleting the payment)
            elif 'PAY' in field and new_info[field] in (None, 0.0, '0.00'):
                # Drop the record from the table by using its index
                self.payment = self.payment.drop(pay_record.index).reset_index(drop=True)

                # If a payment record has been deleted for CURRENT MONTH, remove student from class roll
                if month_num == CURRENT_SESSION.month:
                    for class_id in self.class_student.loc[self.class_student['STUDENT_ID']==student_id,'CLASS_ID'].values:
                        self.unenroll_student(student_id, class_id,)
            # Otherwise, record already exists + new amount entered is NON-ZERO, so we edit the existing record
            else:
                self.payment.loc[pay_record.index, field[3:]] = new_info[field]

    # Create/delete/modify notes for a given student/class in the `note` table
    # The type of note we are dealing with is provided by edit_type (either 'NOTE_STUDENT' or 'NOTE_CLASS')
    # and the relevant ID field (STUDENT_ID or CLASS_ID) is given by 'id'
    def update_note_info(self, id, edit_type, note_textbox):
        # Get all text from the textbox
        note_txt = note_textbox.get('1.0', 'end-1c')
        # Determine name of ID column we will use
        id_field = edit_type.split('_')[0] + '_ID'
        # Pull note record for this ID (if exists)
        note_record = self.note[self.note[id_field] == id]

        ## Step 1: Update `note` Pandas DataFrame
        # If record exists...
        if not note_record.empty:
            # If new text is not blank, update note record
            if note_txt.strip():
                self.note.loc[note_record.index, 'NOTE_TXT'] = note_txt
                self.note.loc[note_record.index, 'UPDT_TMS'] = datetime.now()
            # If new text is blank, delete record
            else:
                self.note = self.note.drop(note_record.index).reset_index(drop=True)
        # Otherwise, create new note record using the user entry
        else:
            self.note.loc[len(self.note)] = {'NOTE_ID' : len(self.note),
                                             id_field : id,
                                             'NOTE_TXT' : note_txt,
                                             'CREA_TMS' : datetime.now(),
                                             'UPDT_TMS' : datetime.now()
                                             }

        # Save out to csv file
        self.note.to_csv(self.csv_paths['note'], index=False)
            
        ## Step 2: Update DBF file
        if 'STUDENT' in edit_type:
            table_to_update = self.student_dbf
            # 'STUD00' has 3 columns for notes
            note_cols = [f'NOTE{i}' for i in range(1,4)]
            field = 'STUDENTNO'
            record_no = self.student.loc[self.student['STUDENT_ID'] == id, field].squeeze()
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
                        

    def update_class_info(self, class_id, entry_boxes, edit_type):
        new_values = [entry.get().strip() for entry in entry_boxes.values()]
        new_info = pd.Series({k:v for (k,v) in zip(entry_boxes.keys(), new_values)})
        for field in entry_boxes.keys():
            if len(new_info[field]) == 0:
                new_info[field] = 0 if entry_boxes[field].dtype == 'float' else None
            elif entry_boxes[field].dtype == 'float':
                new_info[field] = float(new_info[field])
            elif entry_boxes[field].dtype == 'int':
                new_info[field] = int(float(new_info[field]))
            else:
                new_info[field] = new_info[field].upper()


        ## Step 1: Update student info in the Pandas dataframes
        if 'WAIT' in edit_type:
            self.update_wait_info(class_id, new_info)
        elif 'TRIAL' in edit_type:
            self.update_trial_info(class_id, new_info)


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


    def update_wait_info(self, class_id, new_info):
        for field in [col_name for col_name in new_info.index if 'WAIT' in col_name]:
            # Extract wait number from field name
            wait_no = int(field[-1])
            # Get existing record for this waitlist entry (if exists)
            wait_record = self.wait.loc[((self.wait['CLASS_ID']==class_id)
                                        & (self.wait['WAIT_NO']==wait_no))]

            # If waitlist entry doesn't exist...
            if wait_record.empty:
                # If both name and phone fields are blank, do nothing
                if ((new_info[f'WAIT{wait_no}'] is None or len(new_info[f'WAIT{wait_no}'])==0)
                    and (new_info[f'W{wait_no}PHONE'] is None or len(new_info[f'W{wait_no}PHONE'])==0)):
                    continue
                else:
                    self.wait.loc[len(self.wait)] = {'WAIT_ID'  : self.wait.shape[0]+1,
                                                     'CLASS_ID' : class_id,
                                                     'WAIT_NO'  : wait_no,
                                                     'NAME'     : new_info[f'WAIT{wait_no}'],
                                                     'PHONE'    : new_info[f'W{wait_no}PHONE'],
                                                     'CREA_TMS' : datetime.now(),
                                                     'UPDT_TMS' : datetime.now()}
            # If record already exists, modify
            else:
                self.wait.loc[wait_record.index, 'NAME'] = new_info[f'WAIT{wait_no}']
                self.wait.loc[wait_record.index, 'PHONE'] = new_info[f'W{wait_no}PHONE']
                self.wait.loc[wait_record.index, 'UPDT_TMS'] = datetime.now()


    def update_trial_info(self, class_id, new_info):
        for field in [col_name for col_name in new_info.index if 'TRIAL' in col_name]:
            # Extract wait number from field name
            trial_no = int(field[-1])
            # Get existing record for this trial entry (if exists)
            trial_record = self.trial.loc[((self.trial['CLASS_ID']==class_id)
                                         & (self.trial['TRIAL_NO']==trial_no))]

            # If waitlist entry doesn't exist...
            if trial_record.empty:
                # If all fields are blank, do nothing
                if ((new_info[f'TRIAL{trial_no}'] is None or len(new_info[f'TRIAL{trial_no}'])==0)
                    and (new_info[f'T{trial_no}PHONE'] is None or len(new_info[f'T{trial_no}PHONE'])==0)
                    and (new_info[f'T{trial_no}DATE'] is None or len(new_info[f'T{trial_no}DATE'])==0)):
                    continue
                else:
                    self.trial.loc[len(self.trial)] = {'TRIAL_ID'  : self.trial.shape[0]+1,
                                                     'CLASS_ID' : class_id,
                                                     'TRIAL_NO' : trial_no,
                                                     'NAME'     : new_info[f'TRIAL{trial_no}'],
                                                     'PHONE'    : new_info[f'T{trial_no}PHONE'],
                                                     'DATE'     : new_info[f'T{trial_no}DATE'],
                                                     'CREA_TMS' : datetime.now(),
                                                     'UPDT_TMS' : datetime.now()}
            # If record already exists, modify
            else:
                self.trial.loc[trial_record.index, 'NAME'] = new_info[f'TRIAL{trial_no}']
                self.trial.loc[trial_record.index, 'PHONE'] = new_info[f'T{trial_no}PHONE']
                self.trial.loc[trial_record.index, 'DATE'] = new_info[f'T{trial_no}DATE']
                self.trial.loc[trial_record.index, 'UPDT_TMS'] = datetime.now()



    # The dataframe is sorted chronologically by default. This function will sort the dataframe alphabetically,
    # dealing with the case-sensitivity which is built in to Pandas
    def sort_student_alphabetical(self):
        return self.student.sort_values(by=['LNAME','FNAME'], key=lambda x: x.str.upper())
    

    # Similar to `search_students`, but for classes. User selects options to filter down
    # list of classes (i.e. gender, class level, day of week)
    def filter_classes(self, filters):
        # `filters` is a dictionary where the key is the filter type (GENDER, DAY, LEVEL)
        # and the corresponding value is some pattern to match on ('GIRL', 2, 'ADV')
        matches = self.classes[(((self.classes['TEACH'] == filters['INSTRUCTOR']) | (len(filters['INSTRUCTOR']) == 0))
                                & ((self.classes['CLASSNAME'].str.contains(filters['GENDER'])) | (len(filters['GENDER']) == 0))
                                & ((self.classes['DAYOFWEEK'] == filters['DAY']) | (len(str(filters['DAY'])) == 0))
                                & ((self.classes['CLASSNAME'].str.contains(filters['LEVEL'])) | (self.classes['CLASSTIME'].str.contains(filters['LEVEL'])) | (len(filters['LEVEL']) == 0)))
                              ].sort_values(by=['DAYOFWEEK', 'TIMEOFDAY']
                              ).loc[:, ['CLASS_ID', 'TEACH', 'CLASSTIME', 'CLASSNAME', 'MAX']]
        
        return matches
    
    # Search for family by last name
    def search_family(self, query):
        # Force all uppercase
        for key in query.keys(): query[key] = query[key].upper()
        
        # Perform search using name fields
        matches = self.student[self.student['LNAME'].str.upper().str.startswith(query['Last Name'], na=False)
                            ].sort_values(by='LNAME', key=lambda x: x.str.upper()
                            ).sort_values(by='FAMILY_ID'
                            ).loc[:, ['FAMILY_ID','LNAME']
                            ].reset_index(drop=True)
        
        # Determine number of students in each family
        matches['NUM_CHILDREN'] = matches.groupby('FAMILY_ID', dropna=True).transform('size')
        # If family ID could not be determined, make sure number of children is listed as 1
        matches.loc[pd.isna(matches['FAMILY_ID']), 'NUM_CHILDREN'] = 1

        return matches
    
    # Move student from one class to another based on the user's selected options.
    # This function is called by the `MoveStudentDialog` widget, so that we can retrieve 
    # the user-selected options here before the pop-up window closes.
    def move_student(self, student_id, current_class_id, new_class_id):
        current_record = self.class_student[((self.class_student['STUDENT_ID'] == student_id) & (self.class_student['CLASS_ID'] == current_class_id))]
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
        ## STEP 1: Update in Pandas dataframe
        # Create a new record in `class_student` using the new class_id (if it does not exist)
        record = self.class_student[((self.class_student['STUDENT_ID'] == student_id) & (self.class_student['CLASS_ID'] == class_id))]
        if record.empty:
            self.class_student.loc[len(self.class_student)] = {'CLASS_ID' : class_id,
                                                            'STUDENT_ID' : student_id,}
            # Fill a spot in the 'new' class by subtracting 1 from the 'AVAILABLE' column
            self.classes.loc[self.classes['CLASS_ID'] == class_id, 'AVAILABLE'] -= 1

        ## STEP 2: Update original database (DBF file)
        # Get 'STUDENTNO' and name corresponding to the selected 'student_id'
        student_info = self.student[self.student['STUDENT_ID'] == student_id].squeeze()
        studentno = int(student_info['STUDENTNO'])
        student_name = student_info['FNAME'] + ' ' + student_info['LNAME']
        # STUDENTNO columns (NUMB1, NUMB2, ...)
        studentno_cols = [col for col in self.classes_dbf.field_names if 'NUMB' in col]
        # Get class info for new class
        new_class_info = self.classes[self.classes['CLASS_ID']==class_id].squeeze()
        teach_cols, daytime_cols = ['INSTRUCTOR', 'INST2', 'INST3'], ['DAYTIME','DAYTIME2','DAYTIME3']
        # Store student's payment for the current month/year, if it exists
        pay_record = self.payment[(self.payment['STUDENT_ID'] == student_id)
                                & (self.payment['MONTH'] == CURRENT_SESSION.month)
                                & (self.payment['YEAR'] == CURRENT_SESSION.year)]

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
                # Loop through each instructor/daytime pair in STUD00
                for teach_col, daytime_col in list(zip(teach_cols, daytime_cols)):
                    # If instructor/daytime is already present, end function (this prevents enrolling the student in the same class twice)
                    if record[teach_col].strip() == new_class_info['TEACH'] and record[daytime_col].strip() == new_class_info['CLASSTIME']:
                        break
                    # Put instructor/daytime into first blank spot
                    elif record[teach_col].strip() == '':
                        record[teach_col] = new_class_info['TEACH']
                        record[daytime_col] = new_class_info['CLASSTIME']
                        break
    

    # Remove student from class associated with `class_id`
    # This function deletes the relevant record to `class_student` before modifying the DBF files
    # to 1) remove student from `clsbymon.dbf` if they are present,
    # and 2) remove instructor/daytime information from the student's record in `STUD00.dbf`
    def unenroll_student(self, student_id, class_id, wait_var=None,class_roll_only=True):
        ## Step 1: Remove student from class in `class_student`
        record = self.class_student[((self.class_student['STUDENT_ID'] == student_id) & (self.class_student['CLASS_ID'] == class_id))]
        if not class_roll_only:
            # Remove student from class (function arguments are already validated, so student_id / class_id are a valid pair)
            self.class_student = self.class_student.drop(record.index).reset_index(drop=True)
            # Open up a spot in the current class by adding 1 to the 'AVAILABLE' column
            self.classes.loc[self.classes['CLASS_ID'] == class_id, 'AVAILABLE'] += 1

        ## STEP 2: Remove student from class roll in DBF file
        studentno = self.student.loc[self.student['STUDENT_ID']==student_id,'STUDENTNO'].values[0]
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
            class_info = self.classes[self.classes['CLASS_ID']==class_id].squeeze()
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
                            break
    
        # Change wait variable value to exit edit mode
        if wait_var:
            wait_var.set('done')

