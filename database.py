import pandas as pd
import dbf
from datetime import datetime

class StudentDatabase:
    def __init__(self, path_to_csv):
        self.path_to_csv = path_to_csv
        self.student = pd.read_csv(path_to_csv)
        # Drop the rows where name is completely missing
        self.student = self.student.dropna(subset=['FNAME','LNAME']).reset_index(drop=True)
        # Format dates
        for col in ['BIRTHDAY', 'ENROLLDATE']:
            self.student[col] = pd.to_datetime(self.student[col], errors='coerce', format='mixed').dt.strftime('%m/%d/%Y')

        # DBF table
        self.dbf_table = dbf.Table('C:\\dbase\\gymtek\\STUD00.dbf')

    def save_students_to_csv(self):
        self.student.to_csv(self.path_to_csv, index=False)

    def search(self, query):
        # Force all uppercase
        for key in query.keys(): query[key] = query[key].upper()
        
        # If student number provided, perform search using only this field
        if len(query['Student Number']) > 0:
            matches = self.student[self.student['STUDENTNO'].astype('str').str.startswith(query['Student Number'])
                              ].sort_values(by='STUDENTNO'
                              ).loc[:, ['STUDENTNO', 'FNAME','MIDDLE','LNAME']].fillna('')
        # Otherwise, perform search using name fields
        else:
            matches = self.student[(((self.student['FNAME'].str.upper().str.startswith(query['First Name'], na=False)) | (len(query['First Name']) == 0))
                               & ((self.student['MIDDLE'].str.upper().str.startswith(query['Middle Name'], na=False)) | (len(query['Middle Name']) == 0))
                               & ((self.student['LNAME'].str.upper().str.startswith(query['Last Name'], na=False)) | (len(query['Last Name']) == 0)))
                              ].sort_values(by=['LNAME','FNAME'], key=lambda x: x.str.upper()
                              ).loc[:, ['STUDENTNO', 'FNAME','MIDDLE','LNAME']].fillna('')

        return matches

    def update_student_info(self, student_idx, entry_boxes):
        float_cols = ['MONTHLYFEE', 'BALANCE']
        int_cols = ['ZIP']
        numeric_cols = float_cols + int_cols

        new_values = [entry.get() for entry in entry_boxes.values()]
        new_student_info = pd.Series({k:v for (k,v) in zip(entry_boxes.keys(), new_values)})
        for col in float_cols: 
            new_student_info[col] = str(float(new_student_info[col]))
        for col in int_cols:
            new_student_info[col] = str(int(float(new_student_info[col])))
        for col in entry_boxes.keys() - numeric_cols:
            new_student_info[col] = new_student_info[col].upper()

        old_student_info = self.student.iloc[student_idx][[col for col in entry_boxes.keys()]].astype('string').fillna('').str.upper().astype('object')

        # Only update student info if changes were actually made
        if not (old_student_info==new_student_info).all():
            # Student number associated with the edited student
            studentno = self.student.iloc[student_idx]['STUDENTNO']

            ## Step 1: Update student info in the Pandas dataframe
            # Change dtype for non-strings
            for col in float_cols:
                new_student_info[col] = float(new_student_info[col])
            for col in int_cols:
                new_student_info[col] = int(float(new_student_info[col]))
            for col in entry_boxes.keys():
                if self.student.loc[student_idx, col] != new_student_info[col]:
                    self.student.loc[student_idx, col] = new_student_info[col]

            ## Step 2: Update student info in original database (DBF file)
            with self.dbf_table:
                studentno_idx = self.dbf_table.create_index(lambda rec: rec.studentno)
                # get a list of all matching records
                match = studentno_idx.search(match=studentno)
                # should only be one student with that studentno
                record = match[0]
                # Focus on this student's record
                with record:
                    # Loop through each field
                    for field in new_student_info.keys():
                        # Get info about this field in the dbf file
                        field_info = self.dbf_table.field_info(field)
                        # Convert date fields to proper format
                        if str(field_info.py_type) == "<class 'datetime.date'>":
                            new_student_info[field] = datetime.strptime(new_student_info[field], "%m/%d/%Y")
                        
                        # For this record, if the dbase field does not match the user-entered field,
                        # update that field in the dbf file (if the field is unchanged, ignore)
                        if record[field] != new_student_info[field]:
                            record[field] = new_student_info[field]

            ## Step 3: Update student info in new database structure
            student_csv = pd.read_csv('C:\\STMNU2\\data\\rdb_format\\student.csv')
            guardian_csv = pd.read_csv('C:\\STMNU2\\data\\rdb_format\\guardian.csv')
            # Family ID associated with edited student
            family_id = int(student_csv.loc[student_csv['STUDENTNO'] == studentno, 'FAMILY_ID'].iloc[0])

            # Find student record based on `studentno`, and update fields
            for field in new_student_info.keys():
                # Fields which belong to 'guardian'
                if field in ['MOMNAME', 'DADNAME']:
                    # Update info in `guardian.csv`
                    guardian_csv.loc[((guardian_csv['FAMILY_ID'] == family_id)
                                      & (guardian_csv['RELATION'] == field[:3])),
                                     'FNAME'] = new_student_info[field]
                else:
                    # Fields which belong to 'student'
                    if field in student_csv.columns:
                        student_csv.loc[student_csv['STUDENTNO'] == studentno, field] = new_student_info[field]
                    # Fields which belong to 'guardian
                    if field in guardian_csv.columns:
                        guardian_csv.loc[guardian_csv['FAMILY_ID'] == family_id, field] = new_student_info[field]
            
            # Write out changes
            student_csv.to_csv('C:\\STMNU2\\data\\rdb_format\\student.csv', index=False, header=True)
            guardian_csv.to_csv('C:\\STMNU2\\data\\rdb_format\\guardian.csv', index=False, header=True)

        
    # The dataframe is sorted chronologically by default. This function will sort the dataframe alphabetically,
    # dealing with the case-sensitivity which is built in to Pandas
    def sort_alphabetical(self):
        return self.student.sort_values(by=['LNAME','FNAME'], key=lambda x: x.str.upper())


