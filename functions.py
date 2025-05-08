import pandas as pd
import numpy as np
import os
from datetime import datetime
import calendar
import customtkinter as ctk
from dbfread import DBF
import csv
import sqlite3
import dbf
import re
from dotenv import load_dotenv

import functions as fn
from widgets.dialog_boxes import PasswordDialog

# Global variables
from globals import DATA_DIR, BACKUP_DIR, QUERY_DIR, SQLITE_DB, \
                    CALENDAR_DICT, CURRENT_SESSION, PREVIOUS_SESSION
load_dotenv()

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
#       - STUD99.csv
#       - clsbymon.csv
# The argument `save_as` is looking for either '.csv' or '.db'. If '.csv', the new dataframes will
# simply be exported as CSV files. If '.db', the dataframes will be saved to a SQLite database.
def transform_to_rdb(do_not_load=[], update_active=False, save_as='.csv'):
    try:
        # If necessary files are not found, throw error
        if not os.path.isfile(DATA_DIR + '\\dbf_format\\STUD00.csv'): raise FileNotFoundError('STUD00.csv')
        if not os.path.isfile(DATA_DIR + '\\dbf_format\\clsbymon.csv'): raise FileNotFoundError('clsbymon.csv')

        # Load .dbf files for students and classes
        STUD00 = pd.read_csv(os.path.join(DATA_DIR, 'dbf_format', 'STUD00.csv')).dropna(subset=['FNAME','LNAME']).reset_index(drop=True)
        STUD00.insert(0, 'STUDENT_ID', STUD00.index + 1)
        STUD99 = pd.read_csv(os.path.join(DATA_DIR, 'dbf_format', 'STUD99.csv')).dropna(subset=['FNAME','LNAME']).reset_index(drop=True)
        STUD99.insert(0, 'STUDENT_ID', STUD99.index + 1)

        # Rename REGFEE column to match other month pay columns
        STUD00 = STUD00.rename(columns={'REGFEE' : 'REGPAY', 'REGFEEDATE' : 'REGDATE'})
        STUD99 = STUD99.rename(columns={'REGFEE' : 'REGPAY', 'REGFEEDATE' : 'REGDATE'})

        clsbymon = pd.read_csv(os.path.join(DATA_DIR, 'dbf_format', 'clsbymon.csv'))

        # Connect to SQLite database
        conn = sqlite3.connect(SQLITE_DB)

        ### GUARDIAN ###
        # Since we only have first names, and a lot of the data is inconsistent
        # (i.e. address in two records for the same student/parents has 'Street' and 'St'),
        # I think the best way to identify unique guardians is by looking at mom/dad pairings
        # and dropping the duplicates (including last name). Each family has a unique 'FAMILY_ID'.
        families = STUD00.dropna(subset=['MOMNAME', 'DADNAME'], how='all'
                        ).drop_duplicates(subset=['MOMNAME', 'DADNAME', 'LNAME']
                        ).sort_values(by=['LNAME','MOMNAME','DADNAME']
                        ).fillna('')
        # Create a 'FAMILY_ID' by grouping by Last Name, Mom Name, and Dad Name
        # Note: this isn't foolproof as sometimes two siblings might have slightly different
        # names entered for the mom/dad due to user error, but this should capture most families
        families['FAMILY_ID'] = families.groupby(['LNAME','MOMNAME','DADNAME']).ngroup() + 1

        # Extract mom/dad info and create new column to represent relationship to student
        moms = families[families['MOMNAME'] != ''][['FAMILY_ID', 'MOMNAME', 'LNAME', 'PHONE', 'EMAIL']].rename(columns={'MOMNAME':'FNAME'})
        moms.insert(1,'RELATION','MOM')
        dads = families[families['DADNAME'] != ''][['FAMILY_ID', 'DADNAME', 'LNAME', 'PHONE', 'EMAIL']].rename(columns={'DADNAME':'FNAME'})
        dads.insert(1,'RELATION','DAD')

        # Combine moms/dads into new table 'guardian', which holds guardian contact info.
        # The guardian will be connected to their children via the 'FAMILY_ID' key.
        guardian = pd.concat([moms, dads]).sort_values(by=['LNAME','FNAME'])
        guardian = guardian.sort_values(by=['FAMILY_ID','RELATION'])
        
        # Create/update timestamps (placeholder)
        guardian.insert(len(guardian.columns),'CREA_TMS',[datetime.now()]*guardian.shape[0])
        guardian.insert(len(guardian.columns),'UPDT_TMS',[datetime.now()]*guardian.shape[0])


        ### STUDENT ###
        # New table 'student' which is very similar to 'STUD00', just with
        # parent and payment info extracted
        student = pd.DataFrame({'STUDENT_ID' : STUD00['STUDENT_ID'],
                                'CLASS'      : STUD00['CLASS'],
                                'STUDENTNO'  : STUD00['STUDENTNO'],
                                'FNAME'      : STUD00['FNAME'],
                                'LNAME'      : STUD00['LNAME'],
                                'BIRTHDAY'   : STUD00['BIRTHDAY'],
                                'ENROLLDATE' : STUD00['ENROLLDATE'],
                                'MONTHLYFEE' : STUD00['MONTHLYFEE'],
                                'BALANCE'    : STUD00['BALANCE'],
                                'PHONE'      : STUD00['PHONE'],
                                'EMAIL'      : STUD00['EMAIL'],
                                'ADDRESS'    : STUD00['ADDRESS'],
                                'CITY'       : STUD00['CITY'],
                                'STATE'      : STUD00['STATE'],
                                'ZIP'        : STUD00['ZIP'],
                                'CREA_TMS'   : [datetime.now()]*STUD00.shape[0],
                                'UPDT_TMS'   : [datetime.now()]*STUD00.shape[0],})

        # Insert FAMILY_ID into student
        student = student.merge(STUD00[['STUDENTNO','FNAME','LNAME','MOMNAME','DADNAME']].fillna(''), how='left',
                                on=['STUDENTNO','FNAME','LNAME']
                        ).merge(families[['MOMNAME','DADNAME','LNAME','FAMILY_ID']], how='left',
                                on=['MOMNAME','DADNAME','LNAME']
                        ).drop(columns=['MOMNAME','DADNAME']
                        ).drop_duplicates()
        # Move FAMILY_ID to second column
        family_id = student.pop('FAMILY_ID')
        student.insert(1, 'FAMILY_ID', family_id)

        # Apply formatting to date columns
        date_cols = [col for col in student.columns if 'DATE' in col or col=='BIRTHDAY']
        student[date_cols] = format_date_columns(student[date_cols])

        ### PAYMENT and BILL ###
        payment = pd.DataFrame()
        bill = pd.DataFrame()
        payment_cols = ['STUDENTNO', 'FNAME', 'LNAME'] + [month + suffix for month in CALENDAR_DICT.values() for suffix in ['PAY','DATE','BILL']]
        # Pivot payments for previous year and current year to create 'payment' table
        year = CURRENT_SESSION.year - 1
        for STUD in [STUD99, STUD00]:
            payment_df = STUD[payment_cols]
            # 'Melt' dataframe so that all month column names are put into one column called 'COLUMN'
            df_long = payment_df.melt(id_vars=['STUDENTNO', 'FNAME', 'LNAME'], var_name='COLUMN', value_name='VALUE')
            df_long['MONTH'] = df_long['COLUMN'].str[:3].map({month_name:month_num for month_num,month_name in CALENDAR_DICT.items()})
            df_long['TYPE'] = df_long['COLUMN'].str[3:]  # Remaining characters for the type
            df_long['row'] = df_long.groupby(['STUDENTNO', 'FNAME', 'LNAME', 'MONTH', 'TYPE']).cumcount()
            # Pivot payment columns so that the new table has columns: [PAYMENT_ID, STUDENT_ID, MONTH, 'PAY', 'DATE']
            df_pivot = df_long.pivot(index=['STUDENTNO', 'FNAME', 'LNAME', 'MONTH', 'row'], columns='TYPE', values='VALUE').rename_axis(columns=None).reset_index()
            df_pivot = df_pivot[['STUDENTNO', 'FNAME', 'LNAME', 'MONTH', 'PAY', 'DATE', 'BILL']]
            # Add year column
            df_pivot['YEAR'] = int(df_pivot['DATE'].str[:4].mode()[0])

            # When payment is 0 and BILL = '*', this indicates a payment is owed.
            # Create records in a new table 'bill' to represent owed payments
            bill_df = df_pivot.loc[((df_pivot['PAY'] == 0) | (pd.isna(df_pivot['PAY']))) & (df_pivot['BILL'] == '*')
                             ].loc[:,['STUDENTNO', 'FNAME', 'LNAME', 'MONTH', 'YEAR']
                             ].reset_index(drop=True)
            bill = pd.concat([bill, bill_df], ignore_index=True)
            # # Also add REGFEE bills from STUD tables to `bill`
            # regfee_bills = STUD.loc[STUD['REGBILL'] == '*', ['STUDENTNO', 'FNAME', 'LNAME']].assign(MONTH=13, YEAR=year)
            # bill = pd.concat([bill, regfee_bills], ignore_index=True)
            # move to current year before next loop
            year += 1

            # All remaining records with non-zero payments are saved to 'payment'
            payment = pd.concat([payment, df_pivot[((df_pivot['PAY'] != 0) & (~pd.isna(df_pivot['PAY'])))
                       ].reset_index(drop=True)], ignore_index=True)

        # Apply formatting to date columns
        payment['DATE'] = format_date_columns(payment[['DATE']])

        # Get STUDENT_ID from 'student'
        payment = student[['STUDENT_ID','STUDENTNO', 'FNAME', 'LNAME']
                        ].merge(payment, how='right', on=['STUDENTNO', 'FNAME', 'LNAME'])
        bill = student[['STUDENT_ID','STUDENTNO', 'FNAME', 'LNAME']
                     ].merge(bill, how='right', on=['STUDENTNO', 'FNAME', 'LNAME'])
        payment = payment.drop(columns=['STUDENTNO', 'FNAME', 'LNAME','BILL'])
        bill = bill.drop(columns=['STUDENTNO', 'FNAME', 'LNAME'])
        
        ### Active column in `STUDENT` needs to be calculated based on payments, or loaded from existing data ###
        if update_active:
            # Determine which students were paid or billed in current/previous sessions
            paid_students = payment.loc[((payment['MONTH']==CURRENT_SESSION.month) & (payment['YEAR']==CURRENT_SESSION.year))
                                        | ((payment['MONTH']==PREVIOUS_SESSION.month) & (payment['YEAR']==PREVIOUS_SESSION.year)),
                                        'STUDENT_ID'].unique()
            billed_students = bill.loc[((bill['MONTH']==CURRENT_SESSION.month) & (bill['YEAR']==CURRENT_SESSION.year))
                                        | ((bill['MONTH']==PREVIOUS_SESSION.month) & (bill['YEAR']==PREVIOUS_SESSION.year)),
                                        'STUDENT_ID'].unique()
            # Students who were not paid or billed in the current/previous sessions are considered INACTIVE
            inactive_students = student.loc[(~student['STUDENT_ID'].isin(paid_students)) & (~student['STUDENT_ID'].isin(billed_students)),'STUDENT_ID'].drop_duplicates()
        # Otherwise, get active student status from current version of `student.csv`
        else:
            inactive_students = pd.read_sql('SELECT DISTINCT STUDENT_ID FROM student WHERE NOT ACTIVE', conn).squeeze()

        # Declare 'ACTIVE' students as those who are NOT present in the `inactive_students` list.
        # We do it in this complicated way to handle the scenario where new students were added
        # in the old program; for those new students that appear in STUD00 but not in `student`,
        # we want their ACTIVE status to be TRUE. Therefore this method will catch all
        # the existing 'ACTIVE' students as well as the newly enrolled students, and label them all as active.
        student['ACTIVE'] = (~student['STUDENT_ID'].isin(inactive_students))*1

        # Alter 'ACTIVE', change to 'True' if student has a payment for current session
        # student = student.merge(payment.loc[(payment['MONTH']==CURRENT_SESSION.month)&(payment['YEAR']==CURRENT_SESSION.year),['STUDENT_ID','PAY']],
        #                         how='left', on='STUDENT_ID')
        # student['ACTIVE'] = np.where(student['PAY']>0,True,student['ACTIVE'])
        # student = student.drop(columns=['PAY'])
        
        student = student.merge(payment.loc[(payment['MONTH']==CURRENT_SESSION.month)&(payment['YEAR']==CURRENT_SESSION.year),['STUDENT_ID','PAY']],
                                how='left', on='STUDENT_ID')
        student['ACTIVE'] = np.where(student['PAY']>0, 1, student['ACTIVE'])
        student = student.drop(columns=['PAY'])


        ### CLASSES ###
        # Keep the first 11 columns from 'clsbymon', and FINAL column (CLASS_ID)
        classes = clsbymon.iloc[:,list(range(11)) + [clsbymon.shape[1]-1]].copy()
        # Timestamp columns (placeholder)
        classes.insert(len(classes.columns),'CREA_TMS',[datetime.now()]*classes.shape[0])
        classes.insert(len(classes.columns),'UPDT_TMS',[datetime.now()]*classes.shape[0])


        ### CLASS_STUDENT ###
        # Table to connect student with classes
        class_student = pd.DataFrame()
        
        # Go through each instructor/daytime combination, then join with 'clsbymon' to get corresponding CLASS_ID
        # (if the instructor/daytime does not exist in clsbymon, then no record is created in 'class_student')
        for teach_col, daytime_col in list(zip(['INSTRUCTOR', 'INST2', 'INST3'], ['DAYTIME','DAYTIME2','DAYTIME3'])):
            # Get students who have instructor
            students_with_class = STUD00.loc[~pd.isna(STUD00[teach_col])
                                    ].loc[:, ['STUDENT_ID', teach_col, daytime_col]
                                    ].rename(columns={teach_col : 'TEACH', daytime_col : 'CLASSTIME'})
            # Join to get CLASS_ID, then append
            class_student = pd.concat([class_student, students_with_class.merge(clsbymon[['CLASS_ID','TEACH','CLASSTIME']],
                                                                                how='inner', on=['TEACH','CLASSTIME']
                                                    ).loc[:, ['CLASS_ID','STUDENT_ID']]], ignore_index=True)

        # Sort values
        class_student = class_student.sort_values(by=['CLASS_ID', 'STUDENT_ID'])


        ### WAITLIST ###
        wait = pd.DataFrame()
        if 'wait' in do_not_load:
            # Simply pull current version of `wait` from database
            wait = pd.read_sql('SELECT * FROM wait', conn)
        else:
            # Extract waitlist 
            columns = ['CLASS_ID'] + [col for i in range(1, 5) for col in (f'WAIT{i}', f'W{i}PHONE')]
            wait_df = clsbymon[columns]

            # Step 1: Reshape the DataFrame using melt
            df_long = wait_df.melt(id_vars=['CLASS_ID'], var_name='variable', value_name='value')

            # Add ranking column to ensure rows are sorted properly within each class
            col_name_to_rank = {**{f'WAIT{i}'   : (2*(i-1)+1) for i in range(1,5)},
                                **{f'W{i}PHONE' : (2*i)       for i in range(1,5)}}
            df_long['COL_RANK'] = df_long['variable'].map(col_name_to_rank)
            df_long = df_long.sort_values(by=['CLASS_ID', 'COL_RANK'])

            # Add column to remember which waitlist each row corresponds to
            # (this is necessary for compatibility with DBF files)
            df_long['WAIT_NO'] = df_long['variable'].str.extract('(\\d+)')

            # Step 2: Extract TYPE from the column names
            df_long['TYPE'] = np.where(df_long['variable'].str.contains('WAIT'), 'NAME', 'PHONE')

            # Step 3: Group data by CLASS_ID and column type for alignment
            df_long['row'] = df_long.groupby(['CLASS_ID','TYPE']).cumcount()

            # Step 4: Pivot the table to align DATE, NAME, and PHONE
            df_pivot = df_long.pivot(index=['CLASS_ID', 'WAIT_NO', 'row'], columns='TYPE', values='value')
            df_pivot.columns.name = None
            df_pivot = df_pivot.reset_index()

            # Step 5: Drop the helper index, reorder columns, and create 'TRIAL_ID'
            wait = df_pivot[['CLASS_ID', 'WAIT_NO', 'NAME', 'PHONE']]

            # Finally, keep only the rows which have some data
            wait = wait.dropna(how='all', subset=['NAME','PHONE']).reset_index(drop=True)

            # Timestamp columns (placeholder)
            wait.insert(len(wait.columns),'CREA_TMS',[datetime.now()]*wait.shape[0])
            wait.insert(len(wait.columns),'UPDT_TMS',[datetime.now()]*wait.shape[0])


        ### TRIAL ###
        trial = pd.DataFrame()
        if 'trial' in do_not_load:
            # Simply pull current version of `trial` from database
            trial = pd.read_sql('SELECT * FROM trial', conn)
        else:
            columns = ['CLASS_ID'] + [col for i in range(1, 9) for col in (f'TRIAL{i}', f'T{i}PHONE', f'T{i}DATE')]
            trial_df = clsbymon[columns]

            # Step 1: Reshape the DataFrame using melt
            df_long = trial_df.melt(id_vars=['CLASS_ID'], var_name='variable', value_name='value')

            # Add ranking column to ensure rows are sorted properly within each class
            col_name_to_rank = {**{f'TRIAL{i}'  : (i + (2*i - 2)) for i in range(1,9)},
                                **{f'T{i}PHONE' : (i + (2*i - 1)) for i in range(1,9)},
                                **{f'T{i}DATE'  : (i + (2*i - 0)) for i in range(1,9)}}
            df_long['COL_RANK'] = df_long['variable'].map(col_name_to_rank)
            df_long = df_long.sort_values(by=['CLASS_ID', 'COL_RANK'])

            # Add column to remember which trial each row corresponds to
            # (this is necessary for compatibility with DBF files, where the trials
            # do not necessarily need to be edited in order, i.e. it is common for trials 7/8
            # to have data while all the other trials are blank, and we need to preserve this ordering)
            df_long['TRIAL_NO'] = df_long['variable'].str.extract('(\\d+)')

            # Step 2: Extract TYPE from the column names
            df_long['TYPE'] = np.where(df_long['variable'].str.contains('TRIAL'), 'NAME', np.where(
                                    df_long['variable'].str.contains('PHONE'), 'PHONE', 'DATE'
                                    ))

            # Step 3: Group data by CLASS_ID and column type for alignment
            df_long['row'] = df_long.groupby(['CLASS_ID','TYPE']).cumcount()

            # Step 4: Pivot the table to align DATE, NAME, and PHONE
            df_pivot = df_long.pivot(index=['CLASS_ID', 'TRIAL_NO', 'row'], columns='TYPE', values='value')
            df_pivot.columns.name = None
            df_pivot = df_pivot.reset_index()

            # Step 5: Drop the helper index, reorder columns, and create 'TRIAL_ID'
            trial = df_pivot[['CLASS_ID', 'TRIAL_NO', 'NAME', 'PHONE', 'DATE']]

            # Finally, keep only the rows which have some data
            trial = trial.dropna(how='all', subset=['NAME','PHONE','DATE']).reset_index(drop=True)
            # Timestamp columns (placeholder)
            trial.insert(len(trial.columns),'CREA_TMS',[datetime.now()]*trial.shape[0])
            trial.insert(len(trial.columns),'UPDT_TMS',[datetime.now()]*trial.shape[0])

            # Apply formatting to date columns
            date_cols = [col for col in trial.columns if 'DATE' in col]
            trial[date_cols] = format_date_columns(trial[date_cols])


        ### NOTES ###
        note = pd.DataFrame()
        if 'note' in do_not_load:
            # Load current version of `note` from database
            note = pd.read_sql('SELECT * FROM note', conn)
        else:
            # Column names for student notes (3 placeholder columns)
            note_cols = [f'NOTE{i}' for i in range(1,4)]
            # Extract student notes, dropping rows where all three note columns are blank
            student_note = STUD00[['STUDENT_ID'] + note_cols].dropna(subset=note_cols, how='all')
            # Combine all the non-blank notes into a single column, separating each note
            # with a newline so they will display the same as the old program
            student_note['NOTE_TXT'] = student_note[note_cols].apply(
                lambda x: '\n'.join(x.dropna().astype(str)), axis=1
            )
            # Drop the old columns
            student_note = student_note.drop(columns=note_cols)

            # Column names for class notes (3 placeholder columns)
            note_cols = [f'NOTE{i}' for i in range(1,5)]
            # Extract student notes, dropping rows where all four note columns are blank
            class_note = clsbymon[['CLASS_ID'] + note_cols].dropna(subset=note_cols, how='all')
            # Combine all the non-blank notes into a single column, separating each note
            # with a newline so they will display the same as the old program
            class_note['NOTE_TXT'] = class_note[note_cols].apply(
                lambda x: '\n'.join(x.dropna().astype(str)), axis=1
            )
            # Drop the old columns
            class_note = class_note.drop(columns=note_cols)

            # Add '0' CLASS_ID to 'stud_note' and '0' STUDENT_ID to 'class_note' so we can combine them
            student_note.insert(0, 'CLASS_ID', [0]*student_note.shape[0])
            class_note.insert(0, 'STUDENT_ID', [0]*class_note.shape[0])

            # Create final table `note` which contains both student and class notes
            note = pd.concat([student_note, class_note], axis=0).sort_values(by=['STUDENT_ID', 'CLASS_ID'])
            # Timestamp columns (placeholder)
            note.insert(len(note.columns),'CREA_TMS',[datetime.now()]*note.shape[0])
            note.insert(len(note.columns),'UPDT_TMS',[datetime.now()]*note.shape[0])


        ### SAVE TRANSFORMED TABLES TO CSV OR DB ###
        # Put all the dataframes into a list
        df_list = [guardian, student, payment, bill, classes, class_student, wait, trial, note]
        df_names = ['guardian', 'student', 'payment', 'bill', 'classes', 'class_student', 'wait', 'trial', 'note']

        for df, df_name in zip(df_list, df_names):
            # Override: if table name is in list `do_not_load`, we did not create a new version of that table and thus do not save anything
            if df_name.split('.')[0] in do_not_load:
                continue
            else:
                # Write to csv files if option chosen
                if '.csv' in save_as:
                    df.to_csv(os.path.join(BACKUP_DIR, f'{df_name}.csv'), index=False)
                # Write to SQLite database if option chosen
                if '.db' in save_as:
                    df.to_sql(df_name+'_temp', conn, if_exists='replace', index=False)
        
        # Close database connection
        conn.close()

    except FileNotFoundError as err:
        print(f"File '{err.args[0]}' not found at {DATA_DIR}.")


# Function to create SQLite database file named `database.db` at the path
# specified in `db_dir`. Tables are created by running `create_tables.sql`
# found in the path specified by `create_query_path`.
def create_sqlite():
    # Connect to sqlite database (or create if it does not exist)
    conn = sqlite3.connect(SQLITE_DB, timeout=10)

    # Read in SQL create statements as a single string
    with open(os.path.join(QUERY_DIR, 'create_tables.sql'), 'r') as sql_file:
        sql_script = sql_file.read()

    # Execute all create table statements in one transaction, then commit to database
    conn.executescript(sql_script)
    conn.commit()
    # Close database connection
    conn.close()

# Populate SQLite database from CSV files. This is function is necessary for interacting
# with the old dBASE program, to ensure that any changes made in the old program are 
# loaded fresh every time the new program is launched. Once the old program is decommissioned,
# this function will be deprecated.
#
# The function expects a path to the directory containing the relevant CSV files
# as well as a list of table names which should be populated (so that certain tables
# can be excluded from the populate action as desired)
def populate_sqlite_from_csv(do_not_load=[]):
    # Connect to sqlite database (or create if it does not exist)
    conn = sqlite3.connect(SQLITE_DB, timeout=10)
    cur = conn.cursor()
    # Get names of all tables which we are to populate
    # (all tables in SQLite excluding those in `do_not_load`)
    table_names = pd.read_sql(f"""SELECT name
                                  FROM sqlite_schema
                                  WHERE type='table'
                                        AND name NOT LIKE '%sqlite%'
                                        AND name NOT IN {tuple(t for t in do_not_load)}""",
                              conn
                   ).squeeze()
    # Loop through table names
    for table in table_names:
        # Path to CSV file containing this table
        table_csv_path  = os.path.join(BACKUP_DIR, f'{table}.csv')
        # Get field names for table
        columns = list(pd.read_csv(table_csv_path).columns)

        # Open the CSV file we wish to import
        with open(table_csv_path,'r') as fin:
            # Read records from csv file
            dr = csv.DictReader(fin)
            to_db = [tuple(i[col] for col in columns) for i in dr]

        # Dump table, then insert all records into SQLite table
        cur.execute(f"DELETE FROM {table}")
        cur.executemany(f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({', '.join(['?']*len(columns))});", to_db)
        # Save changes
        conn.commit()

    # Close connection when done
    conn.close()

# Backup SQLite database to individual CSV files. This is simply intended as an extra layer of caution
# in case something unexpected happens with the '.db' file. Every time the user exits the program, they
# will be prompted to perform this backup.
def backup_sqlite_to_csv():
    try:
        conn = sqlite3.connect(SQLITE_DB)

        # Get names of all database tables as Pandas Series
        table_names = pd.read_sql("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name", conn
                    ).squeeze()
        # Loop through table names
        for table_name in table_names:
            # Load into Pandas DataFrame and then save out to CSV
            table_df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
            table_df.to_csv(os.path.join(BACKUP_DIR, f'{table_name}.csv'), index=False)
        
        # Close database connection
        conn.close()
    except sqlite3.Error as err:
        print(f'Database error: {err}')
    except Exception as exc:
        print(f'Error occured: {exc}')


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
    # Only check if the field is not blank
    if len(date_text) > 0:
        try:
            datetime.strptime(date_text, "%m/%d/%Y")
        except ValueError as e:
            print(e)
            return False
    
    return True
    

# Apply "MM/DD/YYYY" formatting to a set of date columns (subset of df)
def format_date_columns(date_df):
    return date_df.apply(pd.to_datetime, format='mixed', errors='coerce'
                 ).apply(lambda x: x.dt.strftime('%m/%d/%Y'))
    
    
# Highlight row when mouse hovers over it
def highlight_label(container, row):
    for label in container.grid_slaves(row=row):
            label.configure(fg_color='white smoke')

# Undo highlight when mouse moves off
def unhighlight_label(container, row):
    for label in container.grid_slaves(row=row):
            label.configure(fg_color='transparent')


# Given a set of entry boxes, validate their input 
# (used in `functions.edit_info`, `NewStudentDialog`)
def validate_entryboxes(dbf_table, confirm_button, entry_boxes, error_frame, wait_var):
    # String variable to wait for valid input
    confirm_button.configure(command = lambda : wait_var.set('validate'))

    # Initialize empty list for possible error messages
    error_labels = []

    # SPECIAL CASE: Ignore data validation for certain columns
    cols_to_ignore = [col for i in range(1,10) for col in (f'TRIAL{i}', f'T{i}PHONE')] \
                     + [col for i in range(1,10) for col in (f'WAIT{i}', f'W{i}PHONE')] \
                     + [f'MAKEUP{i}' for i in range(1,5)]

    # Leave entry boxes on screen until all fields have been validated
    while wait_var.get() == 'validate':
        # Get rid of any error labels, if they exist
        if len(error_labels) > 0:
            for _ in range(len(error_labels)):
                label = error_labels.pop()
                label.destroy()
    
        # Check if the user entry in each box is valid according to data type and DBF field restrictions
        for field, entry in entry_boxes.items():
            # SPECIAL CASE: Columns to ignore 
            if field in cols_to_ignore:
                continue
            # SPECIAL CASE: change REG fields to REGFEE to match DBF
            elif field=='REGPAY':
                field = 'REGFEE'
            elif field=='REGDATE':
                field = 'REGFEEDATE'

            try:
                field_info = dbf_table.field_info(field)
            except dbf.exceptions.FieldMissingError:
                print(f'{field} not found in DBF')
                field_info = dbf_table.field_info('T1DATE')

            # Get user-entered value, ignoring whitespace at start and end
            proposed_value = entry.get().strip()
            dtype = entry.dtype
            # Special handling for payments: if value is blank, replace with '0.00'
            if dtype == 'float' and len(str(proposed_value)) == 0:
                # Try to set textvariable
                try:
                    entry.cget('textvariable').set('0.00')
                # If 'AttributeError' thrown, there is no textvariable. Instead, insert '0.00' directly
                except AttributeError:
                    entry.insert(0,'0.00')
                    
                proposed_value = '0.00'
            
            ## Data Validation ##

            # If length of user entry is beyond max limit in dbf file, display error
            if ((dtype == 'datetime.date' and not fn.validate_date(proposed_value))
                or (dtype == 'float' and (len(str(proposed_value)) == 0 or float(proposed_value) > 999.99))
                or ((dtype in ('string', 'int')) and (len(str(proposed_value)) > field_info.length))):

                # Set error message for date fields
                if dtype == 'datetime.date':
                    error_txt = f'Error: {field} must be entered in standard date format (MM/DD/YYYY).'
                elif dtype == 'float':
                    error_txt = f'Error: {field} must be a number between 0 and 999.99'
                # Set error message for string fields
                else:
                    error_txt = f'Error: {field} cannot be longer than {field_info.length} characters.'

                error_labels.append(ctk.CTkLabel(error_frame,
                                                    text=error_txt,
                                                    text_color='red',
                                                    wraplength=round(error_frame.winfo_width()*0.8)))
                
                error_labels[-1].grid(row=error_frame.grid_size()[1], column=0)

        # If any error messages have been displayed, wait for confirm button to be clicked again
        if len(error_labels) > 0:
            confirm_button.wait_variable(wait_var)
        elif wait_var.get() == 'exit':
            break
        # If no errors found, the data is valid, so we break out of the while loop to finalize edits
        else:
            # Change variable value so program continues
            wait_var.set('confirmed')

    # Get rid of any error labels, if they exist
    if len(error_labels) > 0:
        for _ in range(len(error_labels)):
            label = error_labels.pop()
            label.destroy()



# Edit information for a particular frame currently displayed in the window.
# The frame and relevant labels are passed as arguments, along with
# the string 'edit_type' which identifies the type of information that is
# being edited (i.e. student, payment, trials, waitlist, etc.)
#
# The relevant labels will be replaced with entry boxes so the user can 
# enter new data. The function will halt until the user provides valid data,
# at which point the relevant record(s) will be updated in the original DBF files
# (as well as the relevant dataframes being used by the program during runtime).
def edit_info(edit_frame, labels, edit_type, year=CURRENT_SESSION.year):
    # Store parent frame as 'info_frame'. This will be either the
    # StudentInfoFrame or ClassInfoFrame which contains 'edit_frame'.
    info_frame = edit_frame.master
    # Choose appropriate dbf table based on edit type
    if 'STUDENT' in edit_type:
        dbf_table = info_frame.database.student_dbf
    else:
        dbf_table = info_frame.database.classes_dbf

    # Wait variable to stop function until user makes a selection / confirms
    wait_var = ctk.StringVar()
    wait_var.set('validate')

    # To edit payments, user needs to enter a password.
    if edit_type == 'STUDENT_PAYMENT':
        if info_frame.database.request_password:
            dialog = PasswordDialog(window=info_frame.window, text="Enter password:", title="Edit Payments")
            password = dialog.get_input()
            if password != os.getenv('PAYMENT_PASSWORD'):
                return
            # Don't require the user to enter the password again until the program has been restarted
            info_frame.database.request_password = False
        
    # Disable relevant buttons and labels with click events
    for button_name, button in info_frame.buttons.items():
        # Change color of button to grey UNLESS it is the 'active' button
        button.configure(state='disabled', fg_color='grey' if button_name!='ACTIVATE_STUDENT' else button.cget('fg_color'))

    for row in info_frame.search_results_frame.result_rows:
        for label in row:
            label.unbind('<Button-1>')

    # Regardless of edit type, disable student search boxes
    student_query_frame = info_frame.window.screens['Students'].search_results_frame.query_frame
    for widget in student_query_frame.winfo_children():
        try:
            widget.configure(state='disabled')
        except ValueError:
            continue

    if 'STUDENT' in edit_type:
        for switch in info_frame.switches.values():
            switch.configure(state='disabled')
            
        for row in info_frame.class_labels:
            for label in row:
                label.configure(state='disabled')
    elif 'CLASS' in edit_type:
        for checkbox in info_frame.search_results_frame.checkboxes.values():
            checkbox.configure(state='disabled')

        for dropdown in info_frame.search_results_frame.filter_dropdowns.values():
            dropdown.configure(state='disabled')

        info_frame.search_results_frame.rollsheet_button.configure(state='disabled')

        for label in info_frame.roll_labels.values():
            label.unbind('<Button-1>')
    info_frame.window.tabs.configure(state='disabled')

    # Special handling for removing a student from a class they are enrolled in:
    # This is the information housed in `StudentInfoFrame.class_frame`
    if edit_type == 'UNENROLL_STUDENT':
        # Create a label instructing user to choose a class to delete
        choose_class_label = ctk.CTkLabel(edit_frame, text='Which class would you like to delete?',
                                          text_color='red')
        choose_class_label.grid(row=edit_frame.grid_size()[1], column=0, columnspan=3)

        # Temporarily change the function which class labels are bound to
        for row in range(len(labels)):
            for col in range(len(labels[0])):
                # Get label
                label = labels[row][col]
                if row != 0 and col != 0:
                    # If there is data in this label, change binding to unenroll student from selected class
                    if label.cget('text'):
                        label.bind("<Button-1>", lambda event, student_id=info_frame.id, class_id=label.class_id:
                                                    info_frame.database.unenroll_student(student_id, class_id, wait_var, class_roll_only=False))
                        
        # Place new 'cancel' button over the top of the original 'remove student' button
        cancel_button = ctk.CTkButton(info_frame.buttons[edit_type], text="Cancel",
                                       command = lambda : wait_var.set('cancel'))
        cancel_button.place(x=0, y=0, relheight=1.0, relwidth=1.0)

        cancel_button.wait_variable(wait_var)

        # Regardless of if user removed a class or cancelled, destroy widgets and reset
        choose_class_label.destroy()
        cancel_button.destroy()
    # Special handling for removing trial/waitlist/makeup from a class.
    elif 'REMOVE' in edit_type:
        buttons_frame = info_frame.buttons[edit_type].master
        # Create a label instructing user to choose a record to delete
        which_label = ctk.CTkLabel(buttons_frame, text='Which record would you like to delete?',
                                          text_color='white') 
        which_label.grid(row=0, column=0, columnspan=2, sticky='nsew')

        # Create dummy entry boxes that will not be displayed to the user, but still contain the existing data.
        # This is necessary to use the existing `database.update_class_info` function.
        entry_boxes = dict.fromkeys(labels.keys())

        for key in entry_boxes.keys():
            label = labels[key]
            default_text = ctk.StringVar()
            default_text.set(label.cget('text'))
            entry_boxes[key] = ctk.CTkEntry(label, textvariable=default_text)

        # Bind function to the trial/wait labels
        for key, lab in labels.items():
            record_no = re.search('[0-9]+', key).group()
            # Highlight label when mouse hovers over it
            lab.bind("<Enter>",    lambda event, c=lab.master, r=0:
                                            fn.highlight_label(c,r))
            lab.bind("<Leave>",    lambda event, c=lab.master, r=0:
                                            fn.unhighlight_label(c,r))
            # When user clicks on the record associated with `record_no`,
            # call `database.update_class_info` using a custom dictionary of entry boxes
            # where the entry boxes corresponding to `record_no` are all forced to be blank,
            # while all other entry boxes contain the pre-existing values
            # (this is essentially the same as the user editing the wait/trial info, and then
            # manually backspacking/deleting all of the data for a single record)
            custom_entry_boxes = {k : ctk.CTkEntry(lab) for k in entry_boxes.keys() if record_no in k} \
                                 | {k:e for k,e in entry_boxes.items() if record_no not in k}
            for field, entry in custom_entry_boxes.items():
                entry.dtype = 'datetime.date' if 'DATE' in field else 'string'

            lab.bind("<Button-1>", lambda event,
                                          class_id=info_frame.id,
                                          eb=custom_entry_boxes,
                                          et=edit_type,
                                          wv=wait_var:
                                    info_frame.database.update_class_info(class_id, eb, et, wv))
                        
        # Place new 'cancel' button over the top of the original 'remove student' button
        cancel_button = ctk.CTkButton(info_frame.buttons[edit_type], text="Cancel",
                                       command = lambda : wait_var.set('cancel'))
        cancel_button.place(x=0, y=0, relheight=1.0, relwidth=1.0)

        cancel_button.wait_variable(wait_var)

        # Regardless of if user removed a class or cancelled, destroy widgets and reset
        which_label.destroy()
        cancel_button.destroy()
    else:
        edit_button = info_frame.buttons[f'EDIT_{edit_type}']
        # Place new 'confirm' button over the top of the original 'edit' button
        confirm_button = ctk.CTkButton(edit_button, text="✔", fg_color='forest green')
        confirm_button.place(x=0, y=0, relheight=1.0, relwidth=0.5)
        # Bind "Control+End" to 'confirm' edit
        info_frame.window.bind('<Control-End>', lambda event: confirm_button.invoke())
        # Place new 'cancel' alongside the 'confirm' button
        cancel_button = ctk.CTkButton(edit_button, text="❌", fg_color='red',
                                       command = lambda : wait_var.set('cancel'))
        cancel_button.place(x=edit_button.cget('width')//2, y=0, relheight=1.0, relwidth=0.5)
        # Bind "Escape" to 'confirm' edit
        info_frame.window.bind('<Escape>', lambda event: cancel_button.invoke())
        
        # If a note is being edited, the `labels` object is actually a Textbox, and needs special handling.
        if 'NOTE' in edit_type:
            note_textbox = labels
            # Enable textbox so user can modify
            note_textbox.configure(state='normal', fg_color='white')
            # Focus textbox
            note_textbox.focus_set()

            # For the note field, no validation is needed; the user can enter whatever they want.
            # So, the confirm button will simply end edit mode without checking anything.
            confirm_button.configure(command = lambda : wait_var.set('confirmed'))
            # Wait for user to click confirm
            confirm_button.wait_variable(wait_var)
            # Make textbox read-only again
            note_textbox.configure(state='disabled', fg_color=note_textbox.master.cget('fg_color'))

            if wait_var.get() == 'confirmed':
                # Update relevant note field in database
                info_frame.database.update_note_info(id=info_frame.id, edit_type=edit_type, note_textbox=note_textbox)
        # Otherwise, replace relevant labels with entry boxes so user can modify them
        else:
            # Replace info labels with entry boxes, and populate with the current info
            entry_boxes = dict.fromkeys({key : label for key,label in labels.items() if 'HEADER' not in key and 'BILL' not in key})

            for key in entry_boxes.keys():
                # # Ignore certain labels
                # if 'HEADER' in key or 'BILL' in key:
                #     entry_boxes.pop(key)
                #     continue

                label = labels[key]
                default_text = ctk.StringVar()
                default_text.set(label.cget('text'))
                # Match text justification in entry box with the parent label's anchor
                match label.cget('anchor'):
                    case 'e':
                        entry_justify = 'right'
                    case 'w':
                        entry_justify = 'left'
                    case _:
                        entry_justify = 'center'

                entry_box = ctk.CTkEntry(label, textvariable=default_text, justify=entry_justify, font=label.cget("font"))

                # Date fields
                if any(substr in key for substr in ['DATE', 'BIRTHDAY']):
                    entry_box.dtype = 'datetime.date'
                # If field is numeric, enable data validation
                elif any(substr in key for substr in ['ZIP', 'MONTHLYFEE', 'BALANCE', 'PAY',]):
                    vcmd = (info_frame.register(fn.validate_float), '%d', '%P', '%s', '%S')
                    entry_box.configure(validate = 'key', validatecommand=vcmd)
                    entry_box.dtype = 'int' if key == 'ZIP' else 'float'
                # All other fields are plain strings
                else:
                    entry_box.dtype = 'string'

                # Place entry box and store
                entry_box.place(x=0, y=0, relheight=1.0, relwidth=1.0)
                entry_boxes[key] = entry_box
                # Bind keys to move to next/previous entry boxes
                entry_box.bind('<Return>', lambda event, dir='next': jump_to_entry(event,dir))
                entry_box.bind('<Down>',   lambda event, dir='next': jump_to_entry(event,dir))
                entry_box.bind('<Up>',     lambda event, dir='previous': jump_to_entry(event,dir))
                entry_box.bind('<Button-1>', focus_and_clear)

            # Focus the first entry box by focusing the entry that comes after the final entry
            edit_frame.update()
            entry_box.focus()
            entry_box.event_generate('<Return>')

            confirm_button.configure(command=lambda d=dbf_table, c=confirm_button, eb=entry_boxes, ef=edit_frame, v=wait_var:
                                                validate_entryboxes(d, c, eb, ef, v))
            
            # Wait for variable to change to continue
            confirm_button.wait_variable(wait_var)

            # If edits confirmed, finalize changes
            if wait_var.get() == 'confirmed':
                # For payments entered with no date, replace missing date with today's date
                if edit_type == 'STUDENT_PAYMENT':
                    for month in CALENDAR_DICT.values():
                        # Month abbreviation + pay/date (i.e. 'JANPAY', 'JANDATE')
                        pay_field = month + 'PAY'
                        date_field = month + 'DATE'
                        pay_value = entry_boxes[pay_field].get()
                        date_value = entry_boxes[date_field].get()
                        # If pay amount is blank, enter 0.00 as default
                        if len(pay_value) == 0:
                            pay_value = 0.00
                            entry_boxes[pay_field].cget('textvariable').set(pay_value)
                        # If non-zero payment entered for this month AND no payment date provided,
                        # enter today's date as the payment date by default
                        if float(pay_value) != 0.0 and len(date_value) == 0:
                            entry_boxes[date_field].cget('textvariable').set(datetime.today().strftime('%m/%d/%Y'))

                # Update dataframe and dbf file to reflect changes
                if 'STUDENT' in edit_type:
                    info_frame.database.update_student_info(student_id=info_frame.id, entry_boxes=entry_boxes, edit_type=edit_type, year=year)
                else:
                    info_frame.database.update_class_info(class_id=info_frame.id, entry_boxes=entry_boxes, edit_type=edit_type)

            # Destroy entry boxes
            for field in entry_boxes.keys():
                entry_boxes[field].destroy()

        # Get rid of confirm/cancel buttons
        confirm_button.destroy()
        cancel_button.destroy()
        # Unbind "Control+End"
        info_frame.window.unbind('<Control-End>')
        info_frame.window.unbind('<Escape>')

    # Re-enable the deactivated buttons
    for button_name, button in info_frame.buttons.items():
        # Only change color if button is not 'ACTIVE' button
        button.configure(state='normal', fg_color='steelblue3' if button_name!='ACTIVATE_STUDENT' else button.cget('fg_color'))

    for row in info_frame.search_results_frame.result_rows:
        for label in row:
            label.bind("<Button-1>", lambda event, id=label.id:
                                        info_frame.search_results_frame.select_result(id))
            
    for widget in student_query_frame.winfo_children():
        try:
            widget.configure(state='normal')
        except ValueError:
            continue

    if 'STUDENT' in edit_type:
        # Re-bind Enter to 'search'
        info_frame.window.bind('<Return>', lambda event: info_frame.search_results_frame.search_button.invoke())

        for switch in info_frame.switches.values():
            switch.configure(state='normal')

        for widget in info_frame.search_results_frame.query_frame.winfo_children():
            try:
                widget.configure(state='normal')
            except ValueError:
                continue

        for row in info_frame.class_labels:
            for label in row:
                label.configure(state='normal')
    elif 'CLASS' in edit_type:
        for filter_type, checkbox in info_frame.search_results_frame.checkboxes.items():
            # Enable checkbox
            checkbox.configure(state='normal')
            # If checkbox is currently checked, enable filter dropdown menu as well
            if checkbox.get():
                filter_dropdown = info_frame.search_results_frame.filter_dropdowns[filter_type]
                filter_dropdown.configure(state='normal')

        info_frame.search_results_frame.rollsheet_button.configure(state='normal')
    
        for label in info_frame.roll_labels.values():
            # Click student name in class roll to pull up student record
            label.bind("<Button-1>", lambda event, id=label.student_id:
                                                info_frame.open_student_record(id))
            
        # Unbind functions from trial and wait labels
        for label in (info_frame.wait_labels | info_frame.trial_labels).values():
            label.unbind('<Enter>'); label.unbind('<Leave>'); label.unbind('<Button-1>')

            
    info_frame.window.tabs.configure(state='normal')
    info_frame.update_labels(info_frame.id)
    # Finally, if we have made changes to payments or class info, we should update the information displaying in the class info frame
    # (This step ensures that selected student is added/removed from their class if user added/deleted a payment for current month)
    if 'PAYMENT' in edit_type or 'CLASS' in edit_type:
        info_frame.window.screens['Classes'].search_results_frame.update_labels(select_first_result=False)

# Move to next entry box
def jump_to_entry(event, direction):
    # Get next entry
    if direction=='next':
        new_entry = event.widget.tk_focusNext()
    elif direction=='previous':
        new_entry = event.widget.tk_focusPrev()
    # Focus entry and select or clear text
    new_entry.master.update()
    new_entry.event_generate('<Button-1>')
    new_entry.selection_range(0,'end')

def focus_and_clear(event):
    entry_box = event.widget
    # Focus entry
    entry_box.focus_set()
    # If entry is a money field and contains "0.00" as its value, delete the text to start blank
    if entry_box.get() == '0.00':
        entry_box.delete(0,'end')

def button_click():
    print("button clicked")
