import pandas as pd
import numpy as np
import os
from datetime import datetime
import calendar
import customtkinter as ctk
from dbfread import DBF
import dbf

# Function to convert a given .dbf file to .csv
def dbf_to_csv(filename, save_to_path='C:\\STMNU2\\data\\dbf_format'):
    # Fixed file paths for old and new programs
    main_path = 'C:\\STMNU2'
    dbase_path = 'C:\\dbase'
    gymtek_path = dbase_path + '\\gymtek'

    try:
        # Ensure that both the current directory and the 'dbase' directory
        # are located on the topmost level of C: drive
        if not os.path.isdir(main_path): raise NameError('STMNU2')
        if not os.path.isdir(dbase_path): raise NameError('dbase')
        if not os.path.isdir(gymtek_path): raise NameError('dbase\\gymtek')
        
        # Collect records from .dbf file and then convert to dataframe
        records = DBF(gymtek_path + f'\\{filename}')
        data = [record for record in records]
        df = pd.DataFrame(data)
        # Save out dataframe as .csv file
        filename_trunc = os.path.splitext(filename)[0]
        df.to_csv(f'{save_to_path}\\{filename_trunc}.csv', index=False)

    except NameError as err:
        print(f'File path C:\\{err.args[0]} does not exist')

    except UnicodeDecodeError:
        print(f'Could not convert {filename}')

# Function to transform old data structure to a new relational database structure
# Note: for this function to work, the following files must be saved to 'C:\STMNU2\Data\':
#       - STUD00.csv
#       - clsbymon.csv
def transform_to_rdb(data_path, save_to_path='C:\\STMNU2\\data\\rdb_format', write_to_csv=False):
    try:
        # If necessary files are not found, throw error
        if not os.path.isfile(data_path + '\\dbf_format\\STUD00.csv'): raise FileNotFoundError('STUD00.csv')
        if not os.path.isfile(data_path + '\\dbf_format\\clsbymon.csv'): raise FileNotFoundError('clsbymon.csv')

        # Load .dbf files for students and classes
        STUD00 = pd.read_csv('data\\dbf_format\\STUD00.csv').dropna(subset=['FNAME','LNAME']).reset_index(drop=True)
        STUD00.insert(0, 'STUD_ID', STUD00.index + 1)
        clsbymon = pd.read_csv('data\\dbf_format\\clsbymon.csv')
        clsbymon.insert(0, 'CLASS_ID', clsbymon.index + 1)

        ### GUARDIAN ###
        # Since we only have first names, and a lot of the data is inconsistent
        # (i.e. address in two records for the same student/parents has 'Street' and 'St'),
        # I think the best way to identify unique guardians is by looking at mom/dad pairings
        # and dropping the duplicates (including last name). Each family has a unique 'FAMILY_ID'.
        families = STUD00.dropna(subset=['MOMNAME', 'DADNAME'], how='all'
                        ).drop_duplicates(subset=['MOMNAME', 'DADNAME', 'LNAME']).sort_values(by=['LNAME','MOMNAME','DADNAME']).copy()
        families.insert(0, 'FAMILY_ID', list(range(1, families.shape[0]+1)))

        # Extract mom/dad info and create new column to represent relationship to student
        moms = families[~pd.isna(families['MOMNAME'])][['FAMILY_ID', 'MOMNAME', 'LNAME', 'PHONE', 'EMAIL']].rename(columns={'MOMNAME':'FNAME'})
        moms.insert(1,'RELATION','MOM')
        dads = families[~pd.isna(families['DADNAME'])][['FAMILY_ID', 'DADNAME', 'LNAME', 'PHONE', 'EMAIL']].rename(columns={'DADNAME':'FNAME'})
        dads.insert(1,'RELATION','DAD')

        # Combine moms/dads into new table 'guardian', which holds guardian contact info.
        # The guardian will be connected to their children via the 'FAMILY_ID' key.
        guardian = pd.concat([moms, dads]).sort_values(by=['LNAME','FNAME'])
        guardian.insert(0, 'GUARDIAN_ID', list(range(1,guardian.shape[0]+1)))
        guardian = guardian.sort_values(by=['FAMILY_ID','GUARDIAN_ID'])
        
        # Create/update timestamps (placeholder)
        guardian.insert(len(guardian.columns),'CREA_TMS',[datetime.now()]*guardian.shape[0])
        guardian.insert(len(guardian.columns),'UPDT_TMS',[datetime.now()]*guardian.shape[0])


        ### STUDENT ###
        # New table 'student' which is very similar to 'STUD00', just with
        # parent and payment info extracted
        student = pd.DataFrame({'STUD_ID' : STUD00['STUD_ID'],
                                'CLASS' : STUD00['CLASS'],
                                'STUDENTNO' : STUD00['STUDENTNO'],
                                'FNAME' : STUD00['FNAME'],
                                'MIDDLE' : STUD00['MIDDLE'],
                                'LNAME' :  STUD00['LNAME'],
                                'SEX' :  STUD00['SEX'],
                                'BIRTHDAY' :  STUD00['BIRTHDAY'],
                                'ENROLLDATE' :  STUD00['ENROLLDATE'],
                                'LEVEL' :  STUD00['LEVEL'],
                                'REGFEE' :  STUD00['REGFEE'],
                                'REGFEEDATE' : STUD00['REGFEEDATE'],
                                'MONTHLYFEE' :  STUD00['MONTHLYFEE'],
                                'BALANCE' :  STUD00['BALANCE'],
                                'PHONE' :  STUD00['PHONE'],
                                'EMAIL' :  STUD00['EMAIL'],
                                'ADDRESS' : STUD00['ADDRESS'],
                                'CITY' : STUD00['CITY'],
                                'STATE' : STUD00['STATE'],
                                'ZIP' : STUD00['ZIP'],
                                'CREA_TMS' : [datetime.now()]*STUD00.shape[0],
                                'UPDT_TMS' : [datetime.now()]*STUD00.shape[0],})

        # Insert FAMILY_ID into student
        student = student.merge(STUD00.merge(families[['MOMNAME','DADNAME','LNAME','FAMILY_ID']], how='left'
                                            ).loc[:, ['STUDENTNO','FAMILY_ID']],
                                how='left', on='STUDENTNO')
        # Move FAMILY_ID to second column
        family_id = student.pop('FAMILY_ID')
        student.insert(1, 'FAMILY_ID', family_id)


        ### PAYMENT ###
        payment_df = STUD00[['STUDENTNO'] + [month.upper() + suffix for month in list(calendar.month_abbr[1:]) for suffix in ['PAY','DATE','BILL']]]

        # 'Melt' dataframe so that all month column names are put into one column called 'COLUMN'
        df_long = payment_df.melt(id_vars=['STUDENTNO'], var_name='COLUMN', value_name='VALUE')
        df_long['MONTH'] = df_long['COLUMN'].str[:3].map({calendar.month_abbr[i].upper() : i for i in range(1,13)})
        df_long['TYPE'] = df_long['COLUMN'].str[3:]  # Remaining characters for the type
        df_long['row'] = df_long.groupby(['STUDENTNO', 'MONTH', 'TYPE']).cumcount()

        df_pivot = df_long.pivot(index=['STUDENTNO','MONTH', 'row'], columns='TYPE', values='VALUE').rename_axis(columns=None).reset_index()
        df_pivot = df_pivot[['STUDENTNO', 'MONTH', 'PAY', 'DATE', 'BILL']]
        # Pivot payment columns so that the new table has columns: [PAYMENT_ID, STUD_ID, MONTH, 'PAY', 'DATE']
        payment = df_pivot[(df_pivot['PAY'] != 0) | ~pd.isna(df_pivot['BILL'])].reset_index(drop=True)
        # Get STUD_ID from 'student'
        payment = student[['STUD_ID','STUDENTNO']].merge(payment, how='right', on='STUDENTNO')


        ### CLASSES ###
        # Keep the first 11 columns from 'clsbymon'
        classes = clsbymon.iloc[:,:11].copy()
        # Timestamp columns (placeholder)
        classes.insert(len(classes.columns),'CREA_TMS',[datetime.now()]*classes.shape[0])
        classes.insert(len(classes.columns),'UPDT_TMS',[datetime.now()]*classes.shape[0])

        ### CLASS_STUDENT ###
        # Table to connect student with classes
        class_student = []
        
        # In 'clsbymon' there are 32 placeholder columns for students.
        # For each class, iterate through every student column, pull student number,
        # create record in class_student to record that this student is enrolled in this class.
        for class_id in clsbymon['CLASS_ID']:
            for student_num_col in [f'NUMB{i}' for i in range(1,33)]:   
                student_num = clsbymon.loc[clsbymon['CLASS_ID']==class_id, student_num_col].values[0]
                # If student is enrolled in this class, created record in class_student
                if student_num != 0:
                    stud_id = student.loc[student['STUDENTNO'] == student_num]['STUD_ID'].values[0]
                    class_student.append({'CLASS_ID' : class_id, 'STUD_ID' : stud_id})
        # Convert to dataframe
        class_student = pd.DataFrame.from_dict(class_student)
        
        ### WAITLIST ###
        # Extract waitlist 
        waitlist = clsbymon[['CLASS_ID'] + [col for i in range(1, 5) for col in (f'WAIT{i}', f'W{i}PHONE')]]
        waits = []
        # In 'clsbymon' there are 4 placeholder columns for waitlist.
        # For each class, iterate through every waitlist column
        # and extract their individual info
        for i in range(1,5):
            waits.append(waitlist[~pd.isna(waitlist[f'WAIT{i}'])][['CLASS_ID', f'WAIT{i}', f'W{i}PHONE']
                                                                ].rename(columns={f'WAIT{i}':'NAME',
                                                                                  f'W{i}PHONE' : 'PHONE'}))
        # Create new table 'wait' which stores info for those on waitlist.
        # Each row simply contains a CLASS_ID, Name, and Phone Number
        wait = pd.concat(waits).sort_values(by='CLASS_ID')
        wait.insert(0, 'WAIT_ID', list(range(1, wait.shape[0]+1)))
        # Timestamp columns (placeholder)
        wait.insert(len(wait.columns),'CREA_TMS',[datetime.now()]*wait.shape[0])
        wait.insert(len(wait.columns),'UPDT_TMS',[datetime.now()]*wait.shape[0])

        ### TRIAL ###
        # Extract trials
        trial_list = clsbymon[['CLASS_ID'] + [col for i in range(1, 9) for col in (f'TRIAL{i}', f'T{i}PHONE', f'T{i}DATE')]]
        trials = []
        # In 'clsbymon' there are 8 placeholder columns for trials.
        # For each class, iterate through every trial column
        # and extract their individual info
        for i in range(1,9):
            trials.append(trial_list[~pd.isna(trial_list[f'TRIAL{i}'])][['CLASS_ID', f'TRIAL{i}', f'T{i}PHONE', f'T{i}DATE']
                                                                ].rename(columns={f'TRIAL{i}' : 'NAME',
                                                                                  f'T{i}PHONE' : 'PHONE',
                                                                                  f'T{i}DATE' : 'DATE'}))
        # Create new table 'trial' which stores info for class members who are trials.
        # Each row simply contains a CLASS_ID, Name, Phone Number, and Date
        trial = pd.concat(trials).sort_values(by='CLASS_ID')
        trial.insert(0, 'TRIAL_ID', list(range(1, trial.shape[0]+1)))
        # Timestamp columns (placeholder)
        trial.insert(len(trial.columns),'CREA_TMS',[datetime.now()]*trial.shape[0])
        trial.insert(len(trial.columns),'UPDT_TMS',[datetime.now()]*trial.shape[0])

        ### NOTES ###
        # Extract student notes
        note_list = STUD00[['STUD_ID'] + [f'NOTE{i}' for i in range(1,4)]]
        notes = []
        # In 'clsbymon', there are 4 placeholder columns for notes.
        # For each class, iterate through every note column
        # and extract the text
        for i in range(1,4):
            notes.append(note_list[~pd.isna(note_list[f'NOTE{i}'])][['STUD_ID', f'NOTE{i}']
                                                                ].rename(columns={f'NOTE{i}':'NOTE_TXT'}))
        # Each row simply contains a STUD_ID and the contents of the note.
        stud_note = pd.concat(notes)

        # Extract class notes
        note_list = clsbymon[['CLASS_ID'] + [f'NOTE{i}' for i in range(1,5)]]
        notes = []
        # In 'clsbymon', there are 4 placeholder columns for notes.
        # For each class, iterate through every note column
        # and extract the text
        for i in range(1,5):
            notes.append(note_list[~pd.isna(note_list[f'NOTE{i}'])][['CLASS_ID', f'NOTE{i}']
                                                                ].rename(columns={f'NOTE{i}':'NOTE_TXT'}))
        # Create new table 'note' which stores notes for classes.
        # Each row simply contains a CLASS_ID and the contents of the note.
        class_note = pd.concat(notes)
        # Add blank CLASS_ID to 'stud_note' and blank STUD_ID to 'class_note' so we can combine them
        stud_note.insert(0, 'CLASS_ID', [pd.NA]*stud_note.shape[0])
        class_note.insert(0, 'STUD_ID', [pd.NA]*class_note.shape[0])

        # Create new table 'note' which contains both class and student notes
        note = pd.concat([stud_note, class_note], axis=0).sort_values(by=['STUD_ID', 'CLASS_ID'])
        note.insert(0, 'NOTE_ID', list(range(1, note.shape[0]+1)))
        # Timestamp columns (placeholder)
        note.insert(len(note.columns),'CREA_TMS',[datetime.now()]*note.shape[0])
        note.insert(len(note.columns),'UPDT_TMS',[datetime.now()]*note.shape[0])
        
        
        # Write to csv files if option chosen
        if write_to_csv:
            for df, csv_name in zip([guardian, student, payment, classes, class_student, wait, trial, note],
                                    ['guardian.csv','student.csv','payment.csv','classes.csv','class_student.csv','wait.csv','trial.csv','note.csv']):
                df.to_csv(save_to_path + '\\' + csv_name, index=False)

    except FileNotFoundError as err:
        print(f"File '{err.args[0]}' not found at {data_path}.")

# Validate if the user entry is a number (used for numeric fields)
# This will run every time a key is pressed, so that if the user tries to enter
# a letter or other invalid character, nothing happens
def validate_float(action, value_if_allowed, prior_value, text):
    # action=1 -> insert
    if(action=='1'):
        if text in '0123456789.-+':
            try:
                float(value_if_allowed)

                return True
            except ValueError:
                return False
        else:
            return False
    else:
        return True

# Validate that a date field is entered in the correct format "MM/DD/YYYY"
def validate_date(date_text):
    try:
        if len(date_text) > 0 and date_text != datetime.strptime(date_text, "%m/%d/%Y").strftime("%m/%d/%Y"):
            raise ValueError
        return True
    except ValueError:
        return False


def button_click():
    print("button clicked")
