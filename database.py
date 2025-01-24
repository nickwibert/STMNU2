import pandas as pd
import functions as fn
import dbf
import calendar
from datetime import datetime

CURRENT_YEAR = datetime.now().year

class StudentDatabase:
    def __init__(self, student_dbf_path, student_prev_year_dbf_path, clsbymon_dbf_path):
        # DBF Table object for STUD00
        self.student_dbf = dbf.Table(student_dbf_path)
         # Add 'ACTIVE' to student DBF file (if it doesn't exist)
        with self.student_dbf:
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


    def load_data(self):
        # Transform current versions of DBF files to CSV
        fn.dbf_to_csv('STUD00.dbf')
        fn.dbf_to_csv('STUD99.dbf')
        fn.dbf_to_csv('clsbymon.dbf')
        # Update files representing relational database structure
        fn.transform_to_rdb(data_path='C:\\STMNU2\\data', write_to_csv=True)

        # Load student
        student_csv_path = 'C:\\STMNU2\\data\\rdb_format\\student.csv' 
        self.student = pd.read_csv(student_csv_path).convert_dtypes()
        self.student.csv_path = student_csv_path
        # Drop the rows where name is completely missing
        self.student = self.student.dropna(subset=['FNAME','LNAME']).reset_index(drop=True)
        # Format dates
        for col in ['BIRTHDAY', 'ENROLLDATE', 'REGFEEDATE']:
            self.student[col] = pd.to_datetime(self.student[col], errors='coerce', format='mixed').dt.strftime('%m/%d/%Y')

        self.student['ACTIVE'] = self.student['ACTIVE'].astype(bool)

        # Load payment
        payment_csv_path = 'C:\\STMNU2\\data\\rdb_format\\payment.csv'
        self.payment = pd.read_csv(payment_csv_path)
        self.payment.csv_path = payment_csv_path
        # Format dates
        for col in ['DATE']:
            self.payment[col] = pd.to_datetime(self.payment[col], errors='coerce', format='mixed').dt.strftime('%m/%d/%Y')

        # Load bill
        bill_csv_path = 'C:\\STMNU2\\data\\rdb_format\\bill.csv'
        self.bill = pd.read_csv(bill_csv_path)
        self.bill.csv_path = bill_csv_path

        # Load classes
        classes_csv_path = 'C:\\STMNU2\\data\\rdb_format\\classes.csv'
        self.classes = pd.read_csv(classes_csv_path)
        self.classes.csv_path = classes_csv_path

        # Load class_student
        class_student_csv_path = 'C:\\STMNU2\\data\\rdb_format\\class_student.csv'
        self.class_student = pd.read_csv(class_student_csv_path)
        self.class_student.csv_path = class_student_csv_path

        # Load guardian
        guardian_csv_path = 'C:\\STMNU2\\data\\rdb_format\\guardian.csv'
        self.guardian = pd.read_csv(guardian_csv_path)
        self.guardian.csv_path = guardian_csv_path

        # Load note
        note_csv_path = 'C:\\STMNU2\\data\\rdb_format\\note.csv'
        self.note = pd.read_csv(note_csv_path)
        self.note.csv_path = note_csv_path

        # Load trial students
        trial_csv_path = 'C:\\STMNU2\\data\\rdb_format\\trial.csv'
        self.trial = pd.read_csv(trial_csv_path)
        self.trial.csv_path = trial_csv_path
        for col in ['DATE']:
            self.trial[col] = pd.to_datetime(self.trial[col], errors='coerce', format='mixed').dt.strftime('%m/%d/%Y')

        # Load waitlist students
        wait_csv_path = 'C:\\STMNU2\\data\\rdb_format\\wait.csv'
        self.wait = pd.read_csv(wait_csv_path)
        self.wait.csv_path = wait_csv_path

    def save_students_to_csv(self):
        self.student.to_csv(self.path_to_csv, index=False)

    def search_student(self, query):
        # Force all uppercase
        for key in query.keys(): query[key] = query[key].upper()
        
        # Perform search using name fields
        matches = self.student[(((self.student['FNAME'].str.upper().str.startswith(query['First Name'], na=False)) | (len(query['First Name']) == 0))
                            & ((self.student['LNAME'].str.upper().str.startswith(query['Last Name'], na=False)) | (len(query['Last Name']) == 0)))
                            ].sort_values(by=['LNAME','FNAME'], key=lambda x: x.str.upper()
                            ).loc[:, ['STUDENT_ID', 'FNAME','LNAME']
                            ].fillna(''
                            ).reset_index(drop=True)
        
        return matches

    def update_student_info(self, student_id, entry_boxes, edit_type, year=CURRENT_YEAR):
        # Get dataframe index associated with 'student_id'
        student_idx = self.student[self.student['STUDENT_ID'] == student_id].index[0]
        # Student number associated with the edited student
        studentno = self.student.iloc[student_idx]['STUDENTNO']
        family_id = self.student.iloc[student_idx]['FAMILY_ID']

        # Guardian index
        guardian_idx = self.guardian.loc[self.guardian['FAMILY_ID'] == family_id].index

        new_values = [entry.get() for entry in entry_boxes.values()]
        new_student_info = pd.Series({k:v for (k,v) in zip(entry_boxes.keys(), new_values)})
        for col in entry_boxes.keys():
            if len(new_student_info[col]) == 0:
                new_student_info[col] = 0 if entry_boxes[col].dtype == 'float' else None
            elif entry_boxes[col].dtype == 'float':
                new_student_info[col] = float(new_student_info[col])
            elif entry_boxes[col].dtype == 'int':
                new_student_info[col] = int(float(new_student_info[col]))
            else:
                new_student_info[col] = new_student_info[col].upper()


        ## Step 1: Update student info in the Pandas dataframe
        # Change dtype for non-strings
        for col in entry_boxes.keys():
            if col == 'MOMNAME':
                # Check that guardian exists
                if (len(guardian_idx) > 0) and ('MOM' in self.guardian.iloc[guardian_idx]['RELATION'].values):
                    self.guardian.loc[
                        ((self.guardian['FAMILY_ID'] == family_id)
                        & (self.guardian['RELATION'] == 'MOM')), 'FNAME'] = new_student_info[col]
                # If mom doesn't exist, create new record in 'guardian'
                else:
                    # To be added later
                    pass
            elif col == 'DADNAME':
                # Check that guardian exists
                if (len(guardian_idx) > 0) and ('DAD' in self.guardian.iloc[guardian_idx]['RELATION'].values):
                    self.guardian.loc[
                        ((self.guardian['FAMILY_ID'] == family_id)
                        & (self.guardian['RELATION'] == 'DAD')), 'FNAME'] = new_student_info[col]
                # If dad doesn't exist, create new record in 'guardian'
                else:
                    # To be added later
                    pass
            # If this is payment info, update 'payment' table according to `year` argument
            elif ('PAYMENT' in edit_type) and ('REG' not in col):
                # Integer corresponding to the month this payment applies to
                month_num = list(calendar.month_abbr).index(col[:3].title())
                # Get existing record for this payment/bill (if exists)
                pay_record = self.payment[(self.payment['STUDENT_ID'] == student_id)
                                        & (self.payment['MONTH'] == month_num)
                                        & (self.payment['YEAR'] == year)]
                bill_record = self.bill[(self.bill['STUDENT_ID'] == student_id)
                                      & (self.bill['MONTH'] == month_num)
                                      & (self.bill['YEAR'] == year)]
                
                if pay_record.empty:
                    # If payment record does not exist, and payment is non-zero, create new payment record
                    if 'PAY' in col and new_student_info[col] not in (None, 0.0, '0.00'):
                        self.payment.loc[len(self.payment)] = {'STUDENT_ID' : student_id,
                                                               'MONTH'      : month_num,
                                                               'PAY'        : new_student_info[col],
                                                               'YEAR'       : year}
                    # If this month/year appears in 'bill' for this student (meaning they owed),
                    # delete that bill record to indicate that the payment has been made
                    if not bill_record.empty:
                        self.bill = self.bill.drop(bill_record.index).reset_index(drop=True)
                # If record already exists, but the new amount entered is zero, delete the record
                # (therefore changing a payment amount to 0 is equivalent to deleting the payment)
                elif 'PAY' in col and new_student_info[col] in (None, 0.0, '0.00'):
                    # Drop the record from the table by using its index
                    self.payment = self.payment.drop(pay_record.index).reset_index(drop=True)
                # Otherwise, record already exists + new amount entered is NON-ZERO, so we edit the existing record
                else:
                    self.payment.loc[pay_record.index, col[3:]] = new_student_info[col]
            # Otherwise edit 'student' table
            else:
                self.student.loc[student_idx, col] = new_student_info[col] 
        

        ## Step 2: Update student info in original database (DBF file)
        if year == CURRENT_YEAR:
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
                    # For this record, if the dbase field does not match the user-entered field,
                    # update that field in the dbf file (if the field is unchanged, ignore)
                    if record[field] != new_student_info[field]:
                        record[field] = new_student_info[field]


    def activate_student(self, student_id):
        # Toggle 'ACTIVE' value for selected student between True/False

        # Step 1: Pandas DataFrame
        student_record = self.student[self.student['STUDENT_ID'] == student_id]
        self.student.loc[student_record.index, 'ACTIVE'] = not student_record['ACTIVE'].values[0]

        # Step 2: DBF file
        studentno = student_record['STUDENTNO'].values[0]
        with self.student_dbf:
            studentno_idx = self.student_dbf.create_index(lambda rec: rec.studentno)
            # get a list of all matching records
            match = studentno_idx.search(match=studentno)
            # should only be one student with that studentno
            record = match[0]
            # Focus on this student's record
            with record:
                record['ACTIVE'] = not record['ACTIVE']

    # Create/delete a `bill` record for the selected student, month, year
    def bill_student(self, student_id, month, year):
        if month == 'REG':
            month_num = 13
        else:
            # Integer corresponding to the month this payment applies to
            month_num = list(calendar.month_abbr).index(month.title())
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
        if year == CURRENT_YEAR:
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




    def update_class_info(self, class_id, entry_boxes):
        # Get dataframe index associated with 'class_id'
        class_idx = self.classes[self.classes['CLASS_ID'] == class_id].index[0]

        new_values = [entry.get() for entry in entry_boxes.values()]
        new_info = pd.Series({k:v for (k,v) in zip(entry_boxes.keys(), new_values)})
        for col in entry_boxes.keys():
            if len(new_info[col]) == 0:
                new_info[col] = 0 if entry_boxes[col].dtype == 'float' else None
            elif entry_boxes[col].dtype == 'float':
                new_info[col] = float(new_info[col])
            elif entry_boxes[col].dtype == 'int':
                new_info[col] = int(float(new_info[col]))
            else:
                new_info[col] = new_info[col].upper()


        ## Step 1: Update student info in the Pandas dataframe
        for col in entry_boxes.keys():
            self.classes.loc[class_idx, col] = new_info[col]

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
                        if new_info[field] is not None:
                            new_info[field] = datetime.strptime(new_info[field], "%m/%d/%Y")
                    # For this record, if the dbase field does not match the user-entered field,
                    # update that field in the dbf file (if the field is unchanged, ignore)
                    if record[field] != new_info[field]:
                        record[field] = new_info[field]        


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
        ## STEP 1: Update in Pandas dataframe
        current_record = self.class_student[((self.class_student['STUDENT_ID'] == student_id) & (self.class_student['CLASS_ID'] == current_class_id))]
        # Now, create a new record in `class_student` using the new_class_id
        self.class_student.loc[len(self.class_student)] = {'CLASS_ID' : new_class_id,
                                                           'STUDENT_ID' : student_id,
                                                           'ACTIVE' : current_record['ACTIVE'].values[0]}
        # Remove student from 'current class'
        self.class_student = self.class_student.drop(current_record.index).reset_index(drop=True)
        # Open up a spot in the current class by adding 1 to the 'AVAILABLE' column
        self.classes.loc[self.classes['CLASS_ID'] == current_class_id, 'AVAILABLE'] += 1
        # Fill a spot in the 'new' class by subtracting 1 from the 'AVAILABLE' column
        self.classes.loc[self.classes['CLASS_ID'] == new_class_id, 'AVAILABLE'] -= 1

        ## STEP 2: Update original database (DBF file)
        # Get 'STUDENTNO' and name corresponding to the selected 'student_id'
        student_info = self.student[self.student['STUDENT_ID'] == student_id].squeeze()
        studentno = int(student_info['STUDENTNO'])
        student_name = student_info['FNAME'] + ' ' + student_info['LNAME']
        # STUDENTNO columns (NUMB1, NUMB2, ...)
        studentno_cols = [col for col in self.classes_dbf.field_names if 'NUMB' in col]

        # Open 'clsbymon.dbf'
        with self.classes_dbf:
            class_id_idx = self.classes_dbf.create_index(lambda rec: rec.class_id)
            # Get DBF record corresponding to current (old) class
            record = class_id_idx.search(match=current_class_id)[0]
            # Focus on this class's record
            with record:
                # Loop through each student column
                for field in studentno_cols:
                    # Check if this is the student we wish to move
                    if record[field] == studentno:
                        # If so, delete this studentno and student name from the class
                        record[field] = 0
                        record[f'STUDENT{field[4:]}'] = None
                        # Open up a spot by adding 1 to 'AVAILABLE' column
                        record['AVAILABLE'] += 1
                        break

            # Get DBF record corresponding to current (old) class
            record = class_id_idx.search(match=new_class_id)[0]
            # Focus on this class's record
            with record:
                # Loop through each student column
                for field in studentno_cols:
                    # Put student into the first blank spot
                    if record[field] == 0:
                        record[field] = studentno
                        record[f'STUDENT{field[4:]}'] = student_name
                        # Fill a spot by subtracting 1 from 'AVAILABLE' column
                        record['AVAILABLE'] -= 1
                        break


    # Create a new record
    def create_record(self, entry_boxes, record_type):
        pass
        ## Step 1: Create record in Pandas dataframe

        ## Step 2: Create record in original database (DBF file)

                        






