import pandas as pd
import dbf
from datetime import datetime

class StudentDataFrame:
    def __init__(self, path_to_csv):
        self.path_to_csv = path_to_csv
        self.df = pd.read_csv(path_to_csv)
        # Drop the rows where name is completely missing
        self.df = self.df.dropna(subset=['FNAME','LNAME']).reset_index(drop=True)
        # Format dates
        for col in ['BIRTHDAY', 'ENROLLDATE']:
            self.df[col] = pd.to_datetime(self.df[col], errors='coerce', format='mixed').dt.strftime('%m/%d/%Y')

        # DBF table
        self.dbf_table = dbf.Table('C:\\dbase\\gymtek\\STUD00.dbf')

    def save_students_to_csv(self):
        self.df.to_csv(self.path_to_csv, index=False)

    def search(self, query):
        # Force all uppercase
        for key in query.keys(): query[key] = query[key].upper()
        
        # If student number provided, perform search using only this field
        if len(query['Student Number']) > 0:
            matches = self.df[self.df['STUDENTNO'].astype('str').str.startswith(query['Student Number'])
                              ].sort_values(by='STUDENTNO'
                              ).loc[:, ['STUDENTNO', 'FNAME','MIDDLE','LNAME']].fillna('')
        # Otherwise, perform search using name fields
        else:
            matches = self.df[(((self.df['FNAME'].str.upper().str.startswith(query['First Name'], na=False)) | (len(query['First Name']) == 0))
                               & ((self.df['MIDDLE'].str.upper().str.startswith(query['Middle Name'], na=False)) | (len(query['Middle Name']) == 0))
                               & ((self.df['LNAME'].str.upper().str.startswith(query['Last Name'], na=False)) | (len(query['Last Name']) == 0)))
                              ].sort_values(by=['LNAME','FNAME'], key=lambda x: x.str.upper()
                              ).loc[:, ['STUDENTNO', 'FNAME','MIDDLE','LNAME']].fillna('')

        return matches

    def update_student_info(self, student_idx, entry_boxes):
        float_cols = ['MONTHLYFEE', 'BALANCE']
        int_cols = ['ZIP']
        numeric_cols = float_cols + int_cols

        new_values = [entry.get() for entry in entry_boxes.values()]
        new_student_info = pd.Series({k:v for (k,v) in zip(entry_boxes.keys(), new_values)})
        for col in numeric_cols: 
            new_student_info[col] = str(float(new_student_info[col]))

        old_student_info = self.df.iloc[student_idx][[col for col in entry_boxes.keys()]].astype('string').fillna('').str.title()
        old_student_info['STATE'] = old_student_info['STATE'].upper()

        # Only update student info if changes were actually made
        if not (old_student_info==new_student_info).all():
            ## Step 1: Update student info in the Pandas dataframe
            # Change dtype for non-strings
            for col in float_cols:
                new_student_info[col] = float(new_student_info[col])
            for col in int_cols:
                new_student_info[col] = int(float(new_student_info[col]))
            for col in entry_boxes.keys():
                if self.df.loc[student_idx, col] != new_student_info[col]:
                    self.df.loc[student_idx, col] = new_student_info[col]

            ## Step 2: Update student info in original database (DBF file)
            studentno = self.df.iloc[student_idx]['STUDENTNO']
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
                            
            


    # The dataframe is sorted chronologically by default. This function will sort the dataframe alphabetically,
    # dealing with the case-sensitivity which is built in to Pandas
    def sort_alphabetical(self):
        return self.df.sort_values(by=['LNAME','FNAME'], key=lambda x: x.str.upper())


