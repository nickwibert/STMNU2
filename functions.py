import pandas as pd
import numpy as np
import os
from datetime import datetime
import calendar
import customtkinter as ctk
import csv
import sqlite3
import re
from dotenv import load_dotenv

import functions as fn
from widgets.dialog_boxes import PasswordDialog

# Global variables
from globals import DATA_DIR, BACKUP_DIR, QUERY_DIR, SQLITE_DB, \
                    CALENDAR_DICT, CURRENT_SESSION, PREVIOUS_SESSION
load_dotenv()

# Global variable to store the last time password was entered
password_last_entered_time = datetime.min 

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

# Populate SQLite database from CSV files. This is a helper function that is not used 
# during runtime, but will be helpful if/when we wish to recreate the SQLite database
# using one of our CSV backups.
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

# Validate that a time is entered in format "HH:MM"
def validate_time(time_text):
    if len(time_text) > 0:
        try:
            datetime.strptime(time_text, '%H:%M')
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
def validate_entryboxes(confirm_button, entry_boxes, error_frame, wait_var):
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
    
        # Check if the user entry in each box is valid according to data type and other custom restrictions
        for field, entry in entry_boxes.items():
            # SPECIAL CASE: Columns to ignore 
            if field in cols_to_ignore:
                continue

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

            # Validate dates and floats 
            if ((dtype == 'datetime.date' and not fn.validate_date(proposed_value))
                or (dtype == 'float' and (len(str(proposed_value)) == 0 or float(proposed_value) > 999.99))
                or (dtype == 'time' and not validate_time(proposed_value))
                or (dtype == 'daytime'
                    and (not validate_time(proposed_value.split(' ')[1])
                         or proposed_value.split(' ')[0] not in ['M','T','W','TH','F','S'])
                    )
            ):
                # Set error message for date fields
                if dtype == 'datetime.date':
                    error_txt = f'Error: {field} must be entered in standard date format (MM/DD/YYYY).'
                elif dtype == 'float':
                    error_txt = f'Error: {field} must be a number between 0 and 999.99'
                elif dtype == 'time':
                    error_txt = f'Error: {field} must be entered in standard time format (HH:MM).'
                elif dtype == 'daytime':
                    error_txt = f'Error: {field} must be entered in standard day/time format (i.e. "M 4:00")'


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
# at which point the relevant record(s) will be updated in the database.
def edit_info(edit_frame, labels, edit_type, year=CURRENT_SESSION.year):
    # Store parent frame as 'info_frame'. This will be either the
    # StudentInfoFrame or ClassInfoFrame which contains 'edit_frame'.
    info_frame = edit_frame.master

    # Wait variable to stop function until user makes a selection / confirms
    wait_var = ctk.StringVar()
    wait_var.set('validate')

    # To edit payments, user needs to enter a password.
    # Reference global payment time variable to check last time password was entered
    global password_last_entered_time
    min_since_last_password = (datetime.now() - password_last_entered_time).seconds / 60.0
    print(min_since_last_password)
    if edit_type in ('STUDENT_PAYMENT', 'CLASS'):
        if min_since_last_password > 60 or edit_type == 'CLASS':
            dialog = PasswordDialog(window=info_frame.window, text="Enter password:", title="Edit Payments")
            password = dialog.get_input()
            if password != os.getenv('PAYMENT_PASSWORD'):
                return
            # Update password enter time
            password_last_entered_time = datetime.now()
        
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

        for student in info_frame.roll_labels.keys():
            for label in [info_frame.roll_labels[student],
                          info_frame.age_labels[student],
                          info_frame.pay_labels[student],
                          info_frame.bill_labels[student]]:
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
            # Replace apostrophes as needed
            note_txt = note_textbox.get('1.0', 'end-1c')
            note_txt = note_txt.replace('\'', '\'\'')
            note_textbox.delete('1.0', 'end')
            note_textbox.insert('1.0', note_txt)
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
                default_text.set(label.cget('text') if label.cget('text') is not None else '')
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
                # Special case: day/time from clases screen (i.e. M 4:00)
                elif any(substr in key for substr in ['CLASSTIME','TIME']):
                    entry_box.dtype = 'daytime'
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

            confirm_button.configure(command=lambda c=confirm_button, eb=entry_boxes, ef=edit_frame, v=wait_var:
                                                validate_entryboxes(c, eb, ef, v))
            
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
                
                # For strings, make sure to replace apostrophes appropriately (avoids SQLite errors)
                for field, entry in entry_boxes.items():
                    if entry.dtype=='string':
                        entry.cget('textvariable').set(entry.get().replace('\'', '\'\''))

                # Update database with user's entries
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
    
        for student, roll_label in info_frame.roll_labels.items():
            for label in [roll_label,
                          info_frame.age_labels[student],
                          info_frame.pay_labels[student],
                          info_frame.bill_labels[student]]:
                # Click student name in class roll to pull up student record
                label.bind("<Button-1>", lambda event, id=roll_label.student_id:
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

def get_weekday_index(first_letter):
    # Standardize to uppercase for matching
    letter = first_letter.upper()
    
    # Iterate through day names (Monday=0, Tuesday=1, etc.)
    for index, name in enumerate(calendar.day_name):
        if name.startswith(letter):
            return index + 1
    return None

def button_click():
    print("button clicked")
