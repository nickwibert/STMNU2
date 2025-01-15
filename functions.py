import pandas as pd
import numpy as np
import os
from datetime import datetime
import calendar
import customtkinter as ctk
from dbfread import DBF

import functions as fn
from widgets.password_dialog import PasswordDialog

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
        STUD00.insert(0, 'STUDENT_ID', STUD00.index + 1)
        clsbymon = pd.read_csv('data\\dbf_format\\clsbymon.csv')

        ### GUARDIAN ###
        # Since we only have first names, and a lot of the data is inconsistent
        # (i.e. address in two records for the same student/parents has 'Street' and 'St'),
        # I think the best way to identify unique guardians is by looking at mom/dad pairings
        # and dropping the duplicates (including last name). Each family has a unique 'FAMILY_ID'.
        families = STUD00.dropna(subset=['MOMNAME', 'DADNAME'], how='all'
                        ).drop_duplicates(subset=['MOMNAME', 'DADNAME', 'LNAME']
                        ).sort_values(by=['LNAME','MOMNAME','DADNAME']
                        ).fillna(''
                        ).copy()
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
        guardian.insert(0, 'GUARDIAN_ID', list(range(1,guardian.shape[0]+1)))
        guardian = guardian.sort_values(by=['FAMILY_ID','GUARDIAN_ID'])
        
        # Create/update timestamps (placeholder)
        guardian.insert(len(guardian.columns),'CREA_TMS',[datetime.now()]*guardian.shape[0])
        guardian.insert(len(guardian.columns),'UPDT_TMS',[datetime.now()]*guardian.shape[0])


        ### STUDENT ###
        # New table 'student' which is very similar to 'STUD00', just with
        # parent and payment info extracted
        student = pd.DataFrame({'STUDENT_ID' : STUD00['STUDENT_ID'],
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
        student = student.merge(families[['STUDENT_ID','FAMILY_ID']], how='left', on='STUDENT_ID')
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
        # Pivot payment columns so that the new table has columns: [PAYMENT_ID, STUDENT_ID, MONTH, 'PAY', 'DATE']
        payment = df_pivot[df_pivot['PAY'] != 0].reset_index(drop=True)
        # Get STUDENT_ID from 'student'
        payment = student[['STUDENT_ID','STUDENTNO']].merge(payment, how='right', on='STUDENTNO')
        # Add year column
        payment['YEAR'] = payment['DATE'].str[:4].mode()[0]


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
            class_student = pd.concat([class_student, students_with_class.merge(clsbymon[['CLASS_ID','TEACH','CLASSTIME']], how='inner'
                                                    ).loc[:, ['CLASS_ID','STUDENT_ID']]], ignore_index=True)

        # Sort values
        class_student = class_student.sort_values(by=['CLASS_ID', 'STUDENT_ID'])
        

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
        trial.insert(0, 'TRIAL_ID', trial.index + 1)
        # Timestamp columns (placeholder)
        trial.insert(len(trial.columns),'CREA_TMS',[datetime.now()]*trial.shape[0])
        trial.insert(len(trial.columns),'UPDT_TMS',[datetime.now()]*trial.shape[0])


        ### NOTES ###
        # Extract student notes
        note_list = STUD00[['STUDENT_ID'] + [f'NOTE{i}' for i in range(1,4)]]
        notes = []
        # In 'STUD00', there are 3 placeholder columns for notes.
        # For each student, iterate through every note column
        # and extract the text
        for i in range(1,4):
            notes.append(note_list[~pd.isna(note_list[f'NOTE{i}'])][['STUDENT_ID', f'NOTE{i}']
                                                                ].rename(columns={f'NOTE{i}':'NOTE_TXT'}))
        # Each row simply contains a STUDENT_ID and the contents of the note.
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
        # Add blank CLASS_ID to 'stud_note' and blank STUDENT_ID to 'class_note' so we can combine them
        stud_note.insert(0, 'CLASS_ID', [pd.NA]*stud_note.shape[0])
        class_note.insert(0, 'STUDENT_ID', [pd.NA]*class_note.shape[0])

        # Create new table 'note' which contains both class and student notes
        note = pd.concat([stud_note, class_note], axis=0).sort_values(by=['STUDENT_ID', 'CLASS_ID'])
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
    
# Highlight row when mouse hovers over it
def highlight_label(container, row):
    for label in container.grid_slaves(row=row):
            label.configure(fg_color='white smoke')

# Undo highlight when mouse moves off
def unhighlight_label(container, row):
    for label in container.grid_slaves(row=row):
            label.configure(fg_color='transparent')

# Edit information for a particular frame currently displayed in the window.
# The frame and relevant labels are passed as arguments, along with
# the string 'edit_type' which identifies the type of information that is
# being edited (i.e. student, payment, trials, waitlist, etc.)
#
# The relevant labels will be replaced with entry boxes so the user can 
# enter new data. The function will halt until the user provides valid data,
# at which point the relevant record(s) will be updated in the original DBF files
# (as well as the relevant dataframes being used by the program during runtime).
def edit_info(edit_frame, labels, edit_type):
    # Store parent frame as 'info_frame'. This will be either the
    # StudentInfoFrame or ClassInfoFrame which contains 'edit_frame'.
    info_frame = edit_frame.master
    # Choose appropriate dbf table based on edit type
    if 'STUDENT' in edit_type:
        dbf_table = info_frame.database.student_dbf
    else:
        dbf_table = info_frame.database.classes_dbf

    # To edit payments, user needs to enter a password.
    if edit_type == 'STUDENT_PAYMENT':
        dialog = PasswordDialog(info_frame.window, text="Enter password:", title="Edit Payments")
        password = dialog.get_input()
        if password != '***REMOVED***':
            return

    # Disable relevant buttons and labels with click events
    for button in info_frame.buttons.values():
        button.configure(state='disabled')
    if 'STUDENT' in edit_type:
        info_frame.search_results_frame.search_button.configure(state='disabled')
        for row in info_frame.class_labels:
            for label in row:
                label.configure(state='disabled')
    info_frame.window.tabs.configure(state='disabled')
    # Replace info labels with entry boxes, and populate with the current info
    entry_boxes = dict.fromkeys(labels)

    for key in labels.keys():
        # Ignore certain labels
        if 'HEADER' in key:
            entry_boxes.pop(key)
            continue
        
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

        # Only use text variable if there is existing data; otherwise, 
        entry_box = ctk.CTkEntry(label, textvariable=default_text, justify=entry_justify, font=label.cget("font"))

        # Date fields
        if any(substr in key for substr in ['DATE', 'BIRTHDAY']):
            entry_box.dtype = 'datetime.date'
        # If field is numeric, enable data validation
        elif any(substr in key for substr in ['ZIP', 'MONTHLYFEE', 'BALANCE', 'PAY', 'REGFEE']):
            vcmd = (info_frame.register(fn.validate_float), '%d', '%P', '%s', '%S')
            entry_box.configure(validate = 'key', validatecommand=vcmd)
            entry_box.dtype = 'int' if key == 'ZIP' else 'float'
        # All other fields are plain strings
        else:
            entry_box.dtype = 'string'

        # Place entry box and store
        entry_box.place(x=0, y=0, relheight=1.0, relwidth=1.0)
        entry_boxes[key] = entry_box
        
    confirm_button = ctk.CTkButton(info_frame.buttons[f'EDIT_{edit_type}'],
                                   text="Confirm Changes")

    # Button to confirm edits
    var = ctk.StringVar()
    confirm_button.configure(command = lambda : var.set('validate'))
    confirm_button.place(x=0, y=0, relheight=1.0, relwidth=1.0)

    # Change binding for Enter key to 'confirm' edit
    info_frame.window.bind('<Return>', lambda event: confirm_button.invoke())
    # Initialize empty list for possible error messages
    error_labels = []
    # Wait until confirm button is clicked before continuing
    confirm_button.wait_variable(var)

    # Leave entry boxes on screen until all fields have been validated
    while var.get() == 'validate':
        # Get rid of any error labels, if they exist
        if len(error_labels) > 0:
            for _ in range(len(error_labels)):
                label = error_labels.pop()
                label.destroy()
            info_frame.update()
    
        # Check if the user entry in each box is valid according to data type and DBF field restrictions
        for field in entry_boxes.keys():
            field_info = dbf_table.field_info(field)
            proposed_value = entry_boxes[field].get()
            dtype = entry_boxes[field].dtype
            # If length of user entry is beyond max limit in dbf file, display error
            if ((dtype == 'datetime.date' and not fn.validate_date(proposed_value))
                or (dtype == 'float' and float(proposed_value) > 999.99)
                or ((dtype in ('string', 'int')) and (len(str(proposed_value)) > field_info.length))):

                # Set error message for date fields
                if dtype == 'datetime.date':
                    error_txt = f'Error: {field} must be entered in standard date format (MM/DD/YYYY).'
                elif dtype == 'float':
                    error_txt = f'Error: {field} cannot be greater that 999.99'
                # Set error message for string fields
                else:
                    error_txt = f'Error: {field} cannot be longer than {field_info.length} characters.'

                error_labels.append(ctk.CTkLabel(edit_frame,
                                                 text=error_txt,
                                                 text_color='red',
                                                 wraplength=round(edit_frame.winfo_width()*0.8)))
                
                error_labels[-1].grid(row=edit_frame.grid_size()[1], column=0)

        # If any error messages have been displayed, wait for confirm button to be clicked again
        if len(error_labels) > 0:
            confirm_button.wait_variable(var)
        # If no errors found, the data is valid, so we break out of the while loop to finalize edits
        else:
            break
    
    # Re-bind Enter to 'search'
    info_frame.window.bind('<Return>', lambda event: info_frame.search_results_frame.search_button.invoke())

    # For payments entered with no date, replace missing date with today's date
    if edit_type == 'STUDENT_PAYMENT':
        for month in list(calendar.month_abbr[1:]) + ['REGFEE']:
            # Month abbreviation + pay/date (i.e. 'JANPAY', 'JANDATE')
            pay_field = month.upper() if month == 'REGFEE' else month.upper() + 'PAY'
            date_field = month.upper() + 'DATE'
            pay_value = entry_boxes[pay_field].get()
            date_value = entry_boxes[date_field].get()
            # If pay amount is blank, enter 0.00 as default
            if len(pay_value) == 0:
                pay_value = '0.00'
                entry_boxes[pay_field].cget('textvariable').set(pay_value)
            # If non-zero payment entered for this month AND no payment date provided,
            # enter today's date as the payment date by default
            if float(pay_value) != 0.0 and len(date_value) == 0:
                entry_boxes[date_field].cget('textvariable').set(datetime.today().strftime('%m/%d/%Y'))

    # Update dataframe and dbf file to reflect changes
    if 'STUDENT' in edit_type:
        info_frame.database.update_student_info(student_id=info_frame.id, entry_boxes=entry_boxes, edit_type=edit_type)
    else:
        info_frame.database.update_class_info(class_id=info_frame.id, entry_boxes=entry_boxes)

    # Update labels with new data (where necessary) and destroy entry boxes
    for field in entry_boxes.keys():
        entry = entry_boxes[field]
        if entry.dtype == 'float':
            proposed_value = '{:.2f}'.format(float(entry.get()))
        else:
            proposed_value = entry.get()

        if proposed_value != labels[field].cget("text"):
            labels[field].configure(text=proposed_value)
        entry_boxes[field].destroy()

    # Get rid of confirm edits button
    confirm_button.destroy()

    # Re-enable the deactivated buttons
    for button in info_frame.buttons.values():
        button.configure(state='normal')
    if 'STUDENT' in edit_type:
        info_frame.search_results_frame.search_button.configure(state='normal') 
        for row in info_frame.class_labels:
            for label in row:
                label.configure(state='normal')
    info_frame.window.tabs.configure(state='normal')

    # Finally, if we have made changes to payments, we should update the information displaying in the class info frame
    # (This step ensures that selected student is added/removed from their class if user added/deleted a payment for current month)
    info_frame.window.screens['Classes'].search_results_frame.update_labels()




def button_click():
    print("button clicked")
