import customtkinter as ctk
import pandas as pd
import functions as fn
import calendar
from datetime import datetime

from widgets.search_results_frame import SearchResultsFrame

class StudentInfoFrame(ctk.CTkFrame):
    def __init__(self, window, master, database, **kwargs):
        # Create frame
        super().__init__(master, **kwargs)
        # Application window
        self.window = window

        # Instance of student database
        self.database = database
        self.id = None

        self.buttons = {}

        # Configure rows/columns
        self.columnconfigure((0,1,2), weight=1)
        self.rowconfigure((0,1), weight=1)

        # Frame which will contain search boxes / results to perform student search
        self.search_results_frame = SearchResultsFrame(self, type='student', max_row=100)
        # Frame which will contain student personal info
        self.personal_frame = ctk.CTkFrame(self)
        # Frame which will contain class information
        self.class_frame = ctk.CTkFrame(self)
        # Frame which will contain payment information
        self.payment_frame = ctk.CTkFrame(self)
        # Frame which will contain notes
        self.note_frame = ctk.CTkFrame(self)

        self.search_results_frame.grid(row=0,column=0,rowspan=2, sticky='nsew')
        self.personal_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        self.class_frame.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')
        self.payment_frame.grid(row=0, column=2, padx=(50,5), pady=5, sticky='nsew')
        self.note_frame.grid(row=1, column=2, padx=5, pady=5, sticky='nsew')

        # Buttons to scroll through students
        self.prev_next_frame = ctk.CTkFrame(self.personal_frame)
        self.prev_next_frame.columnconfigure(0,weight=1)
        self.prev_next_frame.rowconfigure((0,1),weight=1)
        self.buttons['PREV_STUDENT'] = ctk.CTkButton(self.prev_next_frame,
                                         text="↑ Previous Student", anchor='w',
                                         command=self.search_results_frame.prev_result)
        self.buttons['NEXT_STUDENT'] = ctk.CTkButton(self.prev_next_frame,
                                         text="↓ Next Student", anchor='w',
                                         command=self.search_results_frame.next_result)
        self.buttons['PREV_STUDENT'].grid(row=0,column=0,pady=5,padx=5)
        self.buttons['NEXT_STUDENT'].grid(row=1,column=0,pady=5,padx=5)
        self.prev_next_frame.grid(row=0,column=0,sticky='nsew')

        # Populate frame with labels containing student information
        self.create_labels()

        # Button to edit student info
        self.buttons['EDIT_STUDENT'] = ctk.CTkButton(self.personal_frame,
                                         text="Edit",
                                         command = lambda labels=self.personal_labels: self.edit_info(labels))
        self.buttons['EDIT_STUDENT'].grid(row=self.personal_frame.grid_size()[1], column=0)

        # Button to edit payment info
        self.buttons['EDIT_PAYMENT'] = ctk.CTkButton(self.payment_frame,
                                         text="Edit",
                                         command = lambda labels=self.payment_labels: self.edit_info(labels))
        self.buttons['EDIT_PAYMENT'].grid(row=self.payment_frame.grid_size()[1], column=0)

        # Create switch to show/hide payments
        self.payment_switch = ctk.CTkSwitch(self.payment_frame,
                                            text='Show/Hide Payments',
                                            variable=ctk.StringVar(value='hide'),
                                            onvalue='show',offvalue='hide')
        self.payment_switch.configure(command = lambda switch=self.payment_switch: self.toggle_view(switch))
        self.payment_switch.grid(row=0, column=0)

        # Create switch to show/hide notes
        self.note_switch = ctk.CTkSwitch(self.note_frame,
                                         text='Show/Hide Notes',
                                         variable=ctk.StringVar(value='hide'),
                                         onvalue='show',offvalue='hide')
        self.note_switch.configure(command = lambda switch=self.note_switch: self.toggle_view(switch))
        self.note_switch.grid(row=0, column=0)

        # Note: payment_frame and note_frame start out hidden, until user requests to view
        self.toggle_view(self.payment_switch)
        self.toggle_view(self.note_switch)

        # Disable all buttons at the start
        for button in self.buttons.values():
            button.configure(state='disabled')

    # Create a label for each bit of student information and place into the frame
    def create_labels(self):
        ### Personal Info Frame ###
        self.personal_frame.columnconfigure(0, weight=1)
        self.personal_labels = {}
        # Display student number above name (cannot be edited)
        self.studentno_label = ctk.CTkLabel(self.personal_frame, text='', font=ctk.CTkFont('Britannic',18), width=self.winfo_reqwidth())
        self.studentno_label.grid(row=self.personal_frame.grid_size()[1],column=0,sticky='nsew')

        # Create frame for full student name
        self.name_frame = ctk.CTkFrame(self.personal_frame)
        self.name_frame.columnconfigure((0,1,2), weight=1)
        self.name_frame.grid(row=self.personal_frame.grid_size()[1], column=0, sticky='nsew')
        name_font = ctk.CTkFont('Britannic', 18)
        self.personal_labels['FNAME'] = ctk.CTkLabel(self.name_frame, text='', font=name_font, anchor='e')
        self.personal_labels['FNAME'].grid(row=0, column=0, padx=2, sticky='nsew')
        self.personal_labels['MIDDLE'] = ctk.CTkLabel(self.name_frame, text='', font=name_font)
        self.personal_labels['MIDDLE'].grid(row=0, column=1, sticky='nsew')
        self.personal_labels['LNAME'] = ctk.CTkLabel(self.name_frame, text='', font=name_font, anchor='w')
        self.personal_labels['LNAME'].grid(row=0, column=2, padx=2, sticky='nsew')

        # Create frame for full address
        self.address_frame = ctk.CTkFrame(self.personal_frame)
        self.address_frame.rowconfigure((0,1), weight=1)
        self.address_frame.columnconfigure((0,1,2), weight=1)
        self.address_frame.grid(row=self.personal_frame.grid_size()[1],column=0,rowspan=2, sticky='nsew')

        self.personal_labels['ADDRESS'] = ctk.CTkLabel(self.address_frame,  text='',)
        self.personal_labels['ADDRESS'].grid(row=0, column=0, columnspan=3, sticky='nsew')
        self.personal_labels['CITY'] = ctk.CTkLabel(self.address_frame,  text='',)
        self.personal_labels['CITY'].grid(row=1, column=0, padx=2, sticky='nsew')
        self.personal_labels['STATE'] = ctk.CTkLabel(self.address_frame,  text='',)
        self.personal_labels['STATE'].grid(row=1, column=1, padx=2, sticky='nsew')
        self.personal_labels['ZIP'] = ctk.CTkLabel(self.address_frame,  text='',)
        self.personal_labels['ZIP'].grid(row=1, column=2, padx=2, sticky='nsew')

        # Email address
        self.personal_labels['EMAIL'] = ctk.CTkLabel(self.personal_frame,  text='',)
        self.personal_labels['EMAIL'].grid(row=self.personal_frame.grid_size()[1], column=0, sticky='nsew')

        # Create frame for mother name
        self.mom_frame = ctk.CTkFrame(self.personal_frame)
        self.mom_frame.columnconfigure((0,1), weight=1)
        self.mom_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.personal_labels['MOM_HEADER'] = ctk.CTkLabel(self.mom_frame, text='Mom:')
        self.personal_labels['MOM_HEADER'].grid(row=0, column=0, sticky='nse', padx=4)
        self.personal_labels['MOMNAME'] = ctk.CTkLabel(self.mom_frame, text='', anchor='w')
        self.personal_labels['MOMNAME'].grid(row=0, column=1, sticky='nsew')

        # Create frame for father name
        self.dad_frame = ctk.CTkFrame(self.personal_frame)
        self.dad_frame.columnconfigure((0,1), weight=1)
        self.dad_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.personal_labels['DAD_HEADER'] = ctk.CTkLabel(self.dad_frame, text='Dad:')
        self.personal_labels['DAD_HEADER'].grid(row=0,column=0, padx=4, sticky='nse')
        self.personal_labels['DADNAME'] = ctk.CTkLabel(self.dad_frame, text='', anchor='w')
        self.personal_labels['DADNAME'].grid(row=0, column=1, sticky='nsew')

        self.personal_labels['PHONE'] = ctk.CTkLabel(self.personal_frame, text='', width=400)
        self.personal_labels['PHONE'].grid(row=self.personal_frame.grid_size()[1], column=0, sticky='nsew')

        # Create frame for birthday
        self.bday_frame = ctk.CTkFrame(self.personal_frame)
        self.bday_frame.columnconfigure((0,1), weight=1)
        self.bday_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.personal_labels['BIRTHDAY_HEADER'] = ctk.CTkLabel(self.bday_frame, text='Birthday:', anchor='w')
        self.personal_labels['BIRTHDAY_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.personal_labels['BIRTHDAY'] = ctk.CTkLabel(self.bday_frame, text='', anchor='e')
        self.personal_labels['BIRTHDAY'].grid(row=0, column=1, sticky='nsew')

        # Create frame for enroll date
        self.enrolldate_frame = ctk.CTkFrame(self.personal_frame)
        self.enrolldate_frame.columnconfigure((0,1), weight=1)
        self.enrolldate_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.personal_labels['ENROLLDATE_HEADER'] = ctk.CTkLabel(self.enrolldate_frame, text='Enroll Date:', anchor='w')
        self.personal_labels['ENROLLDATE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.personal_labels['ENROLLDATE'] = ctk.CTkLabel(self.enrolldate_frame, text='', anchor='e')
        self.personal_labels['ENROLLDATE'].grid(row=0, column=1, sticky='nsew')

        # Create frame for monthly fee
        self.monthlyfee_frame = ctk.CTkFrame(self.personal_frame)
        self.monthlyfee_frame.columnconfigure((0,1), weight=1)
        self.monthlyfee_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.personal_labels['MONTHLYFEE_HEADER'] = ctk.CTkLabel(self.monthlyfee_frame, text='Monthly Fee:', anchor='w')
        self.personal_labels['MONTHLYFEE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.personal_labels['MONTHLYFEE'] = ctk.CTkLabel(self.monthlyfee_frame, text='', anchor='e')
        self.personal_labels['MONTHLYFEE'].grid(row=0, column=1, sticky='nsew')

        # Create frame for balance
        self.balance_frame = ctk.CTkFrame(self.personal_frame)
        self.balance_frame.columnconfigure((0,1), weight=1)
        self.balance_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.personal_labels['BALANCE_HEADER'] = ctk.CTkLabel(self.balance_frame, text='Balance:', anchor='w')
        self.personal_labels['BALANCE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.personal_labels['BALANCE'] = ctk.CTkLabel(self.balance_frame, text='', anchor='e')
        self.personal_labels['BALANCE'].grid(row=0, column=1, sticky='nsew')

        for field in self.personal_labels.keys():
            if 'HEADER' in field:
                self.personal_labels[field].is_header = True
            else:
                self.personal_labels[field].is_header = False

        ### Class Frame ###
        self.class_frame.columnconfigure((0,1,2), weight=1)
        # self.class_frame.rowconfigure((0,1,2), weight=1)
        self.class_labels = []
        headers = ['CODE', 'INSTRUCTOR', 'TIME']
        for row in range(4):
            payment_font = ctk.CTkFont('Britannica',18,'bold') if row == 0 else ctk.CTkFont('Britannica',18,'normal')
            row_labels = []
            for col in range(len(headers)):
                # Create column headers
                if row == 0:
                    class_txt = headers[col]
                    is_header = True
                elif col == 0:
                    class_txt = f'Class #{row}'
                    is_header = True
                # Labels for actual data
                else:
                    class_txt = ''
                    is_header = False
                # Create label and store
                row_labels.append(ctk.CTkLabel(self.class_frame, text=class_txt))
                row_labels[-1].is_header = is_header
                row_labels[-1].grid(row=row, column=col, sticky='nsew', padx=5)
            
            self.class_labels.append(row_labels)

        ### Payment Frame ###
        self.payment_frame.columnconfigure(0,weight=1)
        self.payment_frame.rowconfigure(tuple(range(14)), weight=1)
        self.month_frames = []
        self.payment_labels = {}
        # Values that will populate month column
        month_column = ['Month'] + list(calendar.month_name)[1:] + ['Reg. Fee']
        # Prefixes/suffixes to store labels and also access data from STUD00.dbf (JANPAY, JANDATE, etc.)
        prefix = ['HEADER'] + [month.upper() for month in calendar.month_abbr[1:]] + ['REGFEE']
        suffix = [['HEADER','PAY','DATE'] for _ in range(13)]
        # Special row of suffixes for REGFEE (because column with pay is simply 'REGFEE' rather than 'REGFEEPAY')
        suffix.append(['HEADER', '', 'DATE'])

        # 14 rows (header row + 12 months + registration fee row)
        for row in range(14):
            payment_font = ctk.CTkFont('Britannica',18,'bold') if row in (0,13) else ctk.CTkFont('Britannica',14,'normal')
            # Create a frame for this row
            month_frame = ctk.CTkFrame(self.payment_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')
            month_frame.columnconfigure((0,1,2), weight=1)
            # Create labels for this row
            self.payment_labels[prefix[row] + suffix[row][0]] = ctk.CTkLabel(month_frame, text=month_column[row],
                                                                 font=payment_font,
                                                                 anchor='w', width=75)
            self.payment_labels[prefix[row] + suffix[row][1]] = ctk.CTkLabel(month_frame, text='',
                                                               font=payment_font,
                                                               anchor='e', width=50)
            self.payment_labels[prefix[row] + suffix[row][2]] = ctk.CTkLabel(month_frame, text='',
                                                                font=payment_font,
                                                                anchor='e', width=75)
            # Put labels into grid
            self.payment_labels[prefix[row] + suffix[row][0]].grid(row=0,column=0,padx=10,sticky='nsew')
            self.payment_labels[prefix[row] + suffix[row][1]].grid(row=0,column=1,padx=10,sticky='nsew')
            self.payment_labels[prefix[row] + suffix[row][2]].grid(row=0,column=2,padx=10,sticky='nsew')
            # Grid and store month frame
            month_frame.grid(row=row+1, column=0, sticky='nsew')
            self.month_frames.append(month_frame)

        for field in self.payment_labels.keys():
            if 'HEADER' in field:
                self.payment_labels[field].is_header = True
            else:
                self.payment_labels[field].is_header = False

        ### Notes Frame ###
        self.note_labels = []
        # Header and Up to 3 notes
        for row in range(4):
            note_txt = 'Notes:' if row == 0 else ''
            label = ctk.CTkLabel(self.note_frame, text=note_txt, anchor='w', width=200, wraplength=200)
            label.grid(row=row+1, column=0, sticky='nsew')
            label.is_header = True if row == 0 else False
            self.note_labels.append(label)


    # Update text in labels
    def update_labels(self, student_id):
        # SPECIAL CASE: If student_id == -1, disable buttons and reset all the labels to blank
        if student_id == -1:
            for button in self.buttons.values():
                button.configure(state='disabled')
            for label in self.personal_labels.values():
                if not label.is_header:
                    label.configure(text='')
            for row in self.class_labels:
                for label in row:
                    if not label.is_header:
                        label.configure(text='')
            for label in self.payment_labels.values():
                if not label.is_header:
                    label.configure(text='')
            for label in self.note_labels:
                if not label.is_header:
                    label.configure(text='')

            # Exit function
            return

        # If student_id is valid, populate labels with information
        # Enable buttons
        for button in self.buttons.values():
            button.configure(state='normal')


        # Update student id
        self.id = student_id
        # Series containing all info for a single student (capitalize all strings for visual appeal)
        student_info = self.database.student[self.database.student['STUD_ID'] == student_id
                                                 ].iloc[0
                                                 ].astype('string'
                                                 ).fillna(''
                                                 ).str.title()
        # Get family ID
        self.family_id = student_info['STUD_ID']

        # Dataframe containing payments
        payment_info = self.database.payment[self.database.payment['STUD_ID'] == student_id]

        # Dataframe containing info for student's guardians
        if self.family_id == '':
            guardian_info = pd.DataFrame(columns=self.database.guardian.columns)
        else:
            guardian_info = self.database.guardian.loc[self.database.guardian['FAMILY_ID'] == int(float(student_info['FAMILY_ID']))]


        # List of CLASS_IDs which this student is enrolled in
        class_id = self.database.class_student.loc[self.database.class_student['STUD_ID'] == student_id, 'CLASS_ID']
        # Class info for each class_id
        class_info = self.database.classes.loc[self.database.classes['CLASS_ID'].isin(class_id),
                                               ['CODE','TEACH','CLASSTIME']]
        
        note_info = self.database.note[self.database.note['STUD_ID'] == student_id].reset_index()

        self.studentno_label.configure(text=f'#{student_info['STUDENTNO']}')      
        # Configure text for labels
        for field in self.personal_labels.keys():
            # Update non-headers and guardian fields        
            if not any(x in field for x in ['HEADER', 'MOM', 'DAD']):
                if field in ['BALANCE', 'MONTHLYFEE']:
                    self.personal_labels[field].configure(text=f'{float(student_info[field]):.2f}')
                else:
                    self.personal_labels[field].configure(text=student_info[field])


        # Handle guardians separately
        momname = guardian_info.loc[guardian_info['RELATION'] == 'MOM', 'FNAME']
        momname_txt = '' if momname.empty else momname.values[0]
        self.personal_labels['MOMNAME'].configure(text=momname_txt)

        dadname = guardian_info.loc[guardian_info['RELATION'] == 'DAD', 'FNAME']
        dadname_txt = '' if dadname.empty else dadname.values[0]
        self.personal_labels['DADNAME'].configure(text=dadname_txt)

        for row in range(len(self.class_labels)):
            for col in range(len(self.class_labels[0])):
                if row == 0 and col == 0:
                    label_txt = student_info['CLASS']
                elif row == 0 or col == 0:
                    continue
                # Configure labels for actual data
                else:
                    if class_info.empty or row >= class_info.shape[0]+1 or col >= class_info.shape[1]:
                        label_txt = ''
                    else:
                        label_txt = class_info.iloc[row-1, col]
                self.class_labels[row][col].configure(text=label_txt)

        # Prefixes/suffixes to store labels and also access data from STUD00.dbf (JANPAY, JANDATE, etc.)
        prefix = ['HEADER'] + [month.upper() for month in calendar.month_abbr[1:]] + ['REGFEE']
        suffix = [['HEADER','PAY','DATE'] for _ in range(13)]
        # Special row of suffixes for REGFEE (because column with pay is simply 'REGFEE' rather than 'REGFEEPAY')
        suffix.append(['HEADER', '', 'DATE'])
        
        # Loop through header, 12 months, and registration fee
        for row in range(14):
            # Header row
            if row == 0:
                pay, date = ('Amount', 'Date')
            # Reg. Fee row
            elif row == 13:
                pay, date = (f'{float(student_info['REGFEE']):.2f}', student_info['REGFEEDATE'])
            # Check if a payment exists for this month
            elif row not in payment_info['MONTH'].values:
                pay, date = ('0.00', '')
            else:
                pay = f'{payment_info[payment_info['MONTH']==row]['PAY'].values[0]:.2f}'
                date = payment_info[payment_info['MONTH']==row]['DATE'].values[0]
            # Update pay/date text for this month
            self.payment_labels[prefix[row] + suffix[row][1]].configure(text=pay)
            self.payment_labels[prefix[row] + suffix[row][2]].configure(text=date)

        # Up to 3 notes
        for i in range(1,4):
            # If note doesn't exist, make text blank
            if i > note_info.shape[0]:
                note_txt = ''
            # Otherwise, pull note text from database
            else:
                note_txt = note_info.iloc[i-1]['NOTE_TXT']
            # Update text
            self.note_labels[i].configure(text=note_txt)

    # Edit information currently displayed in window
    def edit_info(self, labels):
        # Disable prev/next student buttons and search button
        for button in self.buttons.values():
            button.configure(state='disabled')
        self.search_results_frame.search_button.configure(state='disabled')

        # Determine which frame we are editing based on the label keys
        if 'MOMNAME' in labels.keys():
            edit_type = 'STUDENT'
        elif 'JANPAY' in labels.keys():
            edit_type = 'PAYMENT'

        # Replace info labels with entry boxes, and populate with the current info
        self.entry_boxes = dict.fromkeys(labels)

        for key in labels.keys():
            # Ignore certain labels
            if 'HEADER' in key:
                self.entry_boxes.pop(key)
                continue

            default_text = ctk.StringVar()
            default_text.set(labels[key].cget('text'))

            # Date fields
            if any(substr in key for substr in ['DATE', 'BIRTHDAY']):
                self.entry_boxes[key] = ctk.CTkEntry(labels[key], textvariable=default_text)
                self.entry_boxes[key].dtype = 'datetime.date'
            # If field is numeric, enable data validation
            elif any(substr in key for substr in ['ZIP', 'MONTHLYFEE', 'BALANCE', 'PAY', 'REGFEE']):
                vcmd = (self.register(fn.validate_float), '%d', '%P', '%s', '%S')
                self.entry_boxes[key] = ctk.CTkEntry(labels[key], textvariable=default_text,
                                                     validate='key', validatecommand=vcmd)
                self.entry_boxes[key].dtype = 'int' if key == 'ZIP' else 'float'
            # All other fields are plain strings
            else:
                self.entry_boxes[key] = ctk.CTkEntry(labels[key], textvariable=default_text)
                self.entry_boxes[key].dtype = 'string'

            self.entry_boxes[key].place(x=0, y=0, relheight=1.0, relwidth=1.0) 
           
        self.confirm_button = ctk.CTkButton(self.buttons[f'EDIT_{edit_type}'],
                                            text="Confirm Changes")
        # Configure button command based on edit type
        if edit_type == 'STUDENT':
            self.confirm_button.configure(command = lambda labels=self.personal_labels: self.confirm_edit(labels))
        elif edit_type == 'PAYMENT':
            self.confirm_button.configure(command = lambda labels=self.payment_labels:  self.confirm_edit(labels))
        
        self.confirm_button.place(x=0, y=0, relheight=1.0, relwidth=1.0)

        # Change binding for Enter key to 'confirm' edit
        self.window.bind('<Return>', lambda event: self.confirm_button.invoke())

        # Initialize empty list for possible error messages
        self.error_labels = []


    # Function to finalize edits to student record, validate the entered data,
    # and then finally call function to update database if entries are valid
    def confirm_edit(self, labels):
        # Determine which frame we are editing based on the label keys
        if 'MOMNAME' in labels.keys():
            edit_type = 'STUDENT'
        elif 'JANPAY' in labels.keys():
            edit_type = 'PAYMENT'

        # Get rid of any error labels, if they exist
        if len(self.error_labels) > 0:
            # self.master.geometry(f'{self.master.winfo_width()}x{self.master.winfo_height() - 50*len(self.error_labels)}')
            for _ in range(len(self.error_labels)):
                label = self.error_labels.pop()
                label.destroy()
            self.update()
        
        # Update labels (where necessary) and then destroy entry boxes
        for field in self.entry_boxes.keys():
            field_info = self.database.student_dbf.field_info(field)
            proposed_value = self.entry_boxes[field].get()
            is_date = (str(field_info.py_type) == "<class 'datetime.date'>")
            is_float = proposed_value.replace('.','',1).isdigit() and field != 'ZIP'
            is_string = (not is_date and not is_float)

            # If length of user entry is beyond max limit in dbf file, display error
            if ((is_string and (len(str(proposed_value)) > field_info.length))
                or (is_date and not fn.validate_date(proposed_value))
                or (is_float and float(proposed_value) > 999.99)):

                # Set error message for date fields
                if is_date:
                    error_txt = f'Error: {field} must be entered in standard date format (MM/DD/YYYY).'
                elif is_float:
                    error_txt = f'Error: {field} cannot be greater that 999.99'
                # Set error message for string fields
                else:
                    error_txt = f'Error: {field} cannot be longer than {field_info.length} characters.'

                self.error_labels.append(ctk.CTkLabel(self,
                                                    text=error_txt,
                                                    text_color='red',
                                                    wraplength=300))
                
                self.error_labels[-1].grid(row=self.grid_size()[1], column=0)

        # If any errors so far, exit function so user can fix entry
        if len(self.error_labels) > 0:
            # Adjust window size to accomodate
            # self.master.geometry(f'{self.master.winfo_width()}x{self.master.winfo_height() + 50*len(self.error_labels)}')
            # self.master.update()
            return
        else:
            # Re-bind Enter to 'search'
            self.window.bind('<Return>', lambda event: self.search_results_frame.search_button.invoke())

            # Populate payment dates where necessary
            if edit_type == 'PAYMENT':
                for month in list(calendar.month_abbr[1:]) + ['REGFEE']:
                    # Month abbreviation + pay/date (i.e. 'JANPAY', 'JANDATE')
                    pay_field = month.upper() if month == 'REGFEE' else month.upper() + 'PAY'
                    date_field = month.upper() + 'DATE'
                    pay_value = self.entry_boxes[pay_field].get()
                    date_value = self.entry_boxes[date_field].get()
                    # If pay amount is blank, enter 0.00 as default
                    if len(pay_value) == 0:
                        pay_value = '0.00'
                        self.entry_boxes[pay_field].cget('textvariable').set(pay_value)
                    # If non-zero payment entered for this month AND no payment date provided,
                    # enter today's date as the payment date by default
                    if float(pay_value) != 0.0 and len(date_value) == 0:
                        self.entry_boxes[date_field].cget('textvariable').set(datetime.today().strftime('%m/%d/%Y'))

            # Update student dataframe and dbf file to reflect changes
            self.database.update_student_info(student_id=self.id, entry_boxes=self.entry_boxes)

            for field in self.entry_boxes.keys():
                proposed_value = self.entry_boxes[field].get()
                if proposed_value != labels[field].cget("text"):
                    labels[field].configure(text=proposed_value)
                self.entry_boxes[field].destroy()

            # Get rid of confirm edits button
            self.confirm_button.destroy()
            # Re-enable the deactivated buttons
            for button in self.buttons.values():
                button.configure(state='normal')
            self.search_results_frame.search_button.configure(state='normal')

    # Show/hide student's payment info or notes
    def toggle_view(self, switch):
        if switch.get() == 'show':
            # Show all widgets contained in parent frame by "lifting" them back into view
            # (ignoring the switch itself)
            for child in switch.master.winfo_children():
                if child.winfo_name() != '!ctkswitch':
                    child.lift()
        elif switch.get() == 'hide':
            # Hide all widgets contained in parent frame by "lowering" them out of view
            # (ignoring the switch itself)
            for child in switch.master.winfo_children():
                if child.winfo_name() != '!ctkswitch':
                    child.lower()