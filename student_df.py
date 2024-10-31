import pandas as pd
import customtkinter as ctk

class StudentDataFrame:
    def __init__(self, path_to_csv):
        self.path_to_csv = path_to_csv
        self.df = pd.read_csv(path_to_csv)
        # Drop the rows where name is completely missing
        self.df = self.df.dropna(subset=['FNAME','LNAME']).reset_index()

    def save_students_to_csv(self):
        self.df.to_csv(self.path_to_csv, index=False)

    def search(self, lname):
        # Force all uppercase
        lname = lname.upper()
        # Find all students with a match, and then select index of first row (alphabetically?)
        try:
            first_match = self.df[self.df['LNAME'].str.upper().str.startswith(lname, na=False)
                                ].sort_values(by=['LNAME','FNAME'], key=lambda x: x.str.upper()
                                ).index[0]
        except IndexError:
            first_match = None

        return first_match

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

        # Only update student dataframe if changes were actually made
        if not (old_student_info==new_student_info).all():
            # Change dtype for non-strings
            for col in float_cols:
                new_student_info[col] = float(new_student_info[col])
            for col in int_cols:
                new_student_info[col] = int(float(new_student_info[col]))
            for col in entry_boxes.keys():
                if self.df.loc[student_idx, col] != new_student_info[col]:
                    self.df.loc[student_idx, col] = new_student_info[col]

    # The dataframe is sorted chronologically by default. This function will sort the dataframe alphabetically,
    # dealing with the case-sensitivity which is built in to Pandas
    def sort_alphabetical(self):
        return self.df.sort_values(by=['LNAME','FNAME'], key=lambda x: x.str.upper())


