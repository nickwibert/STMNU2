import customtkinter as ctk
import pandas as pd
import calendar
from datetime import datetime

import functions as fn
from widgets.search_results_frame import SearchResultsFrame
from widgets.password_dialog import PasswordDialog

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
        # self.buttons['PREV_STUDENT'].grid(row=0,column=0,pady=5,padx=5)
        # self.buttons['NEXT_STUDENT'].grid(row=1,column=0,pady=5,padx=5)
        # self.prev_next_frame.grid(row=0,column=0,sticky='nsew')

        # Populate frame with labels containing student information
        self.create_labels()
        
        student_buttons_frame = ctk.CTkFrame(self.personal_frame)
        student_buttons_frame.columnconfigure((0,1),weight=1)
        student_buttons_frame.grid(row=self.personal_frame.grid_size()[1], column=0)
        # Button to edit student info
        self.buttons['EDIT_STUDENT'] = ctk.CTkButton(student_buttons_frame,
                                         text="Edit Student",
                                         command = lambda frame=self.personal_frame, labels=self.personal_labels, type='STUDENT':
                                                      fn.edit_info(frame, labels, type))
        self.buttons['EDIT_STUDENT'].grid(row=0, column=1, padx=5)

        # Button to edit payment info
        self.buttons['EDIT_STUDENT_PAYMENT'] = ctk.CTkButton(self.payment_frame,
                                         text="Edit Payments",
                                         command = lambda frame=self.payment_frame, labels=self.payment_labels, type='STUDENT_PAYMENT':
                                                      fn.edit_info(frame, labels, type))
        self.buttons['EDIT_STUDENT_PAYMENT'].grid(row=self.payment_frame.grid_size()[1], column=0)

        # Button to edit payment info
        self.buttons['EDIT_NOTE_STUDENT'] = ctk.CTkButton(self.note_frame,
                                         text="Edit Notes",
                                         command = lambda frame=self.note_frame, labels=self.note_labels, type='NOTE_STUDENT':
                                                      fn.edit_info(frame, labels, type))
        self.buttons['EDIT_NOTE_STUDENT'].grid(row=self.note_frame.grid_size()[1], column=0)

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
        self.studentno_label = ctk.CTkLabel(self.personal_frame, text='', font=ctk.CTkFont('Britannic',18), width=400)
        self.studentno_label.grid(row=self.personal_frame.grid_size()[1],column=0,sticky='nsew')

        # Create frame for full student name
        self.name_frame = ctk.CTkFrame(self.personal_frame)
        self.name_frame.columnconfigure((0,1), weight=1)
        self.name_frame.grid(row=self.personal_frame.grid_size()[1], column=0, sticky='nsew')
        name_font = ctk.CTkFont('Britannic', 18)
        self.personal_labels['FNAME'] = ctk.CTkLabel(self.name_frame, text='', font=name_font, anchor='e')
        self.personal_labels['FNAME'].grid(row=0, column=0, padx=2, sticky='nsew')
        # self.personal_labels['MIDDLE'] = ctk.CTkLabel(self.name_frame, text='', font=name_font)
        # self.personal_labels['MIDDLE'].grid(row=0, column=1, sticky='nsew')
        self.personal_labels['LNAME'] = ctk.CTkLabel(self.name_frame, text='', font=name_font, anchor='w')
        self.personal_labels['LNAME'].grid(row=0, column=1, padx=2, sticky='nsew')

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
            payment_font = ctk.CTkFont('Britannica',16,'bold') if row in (0,13) else ctk.CTkFont('Britannica',16,'normal')
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
        self.note_frame.columnconfigure(0, weight=1)
        self.note_labels = {}
        note_font = ctk.CTkFont('Britannic',18)
        # Header and Up to 3 notes
        for row in range(4):
            suffix = '_HEADER' if row == 0 else row
            note_txt = 'NOTES:' if row == 0 else ''
            label = ctk.CTkLabel(self.note_frame, text=note_txt, font=note_font, anchor='w', width=400, wraplength=400)
            label.grid(row=row+1, column=0, sticky='nsew')
            label.is_header = True if row == 0 else False
            self.note_labels[f'NOTE{suffix}'] = label

    def reset_labels(self):
        # Wipe info from labels
        self.studentno_label.configure(text='')

        for label in self.personal_labels.values():
            if not label.is_header:
                label.configure(text='')

        for row in self.class_labels:
            for label in row:
                if not label.is_header:
                    label.configure(text='')
                    for binding in ['<Button-1>', '<Enter>', '<Leave>']:
                        label.unbind(binding)

        for label in self.payment_labels.values():
            if not label.is_header:
                label.configure(text='')

        for label in self.note_labels.values():
            if not label.is_header:
                label.configure(text='')

    # Update text in labels
    def update_labels(self, student_id):
        # Wipe info from labels
        self.reset_labels()

        # SPECIAL CASE: If student_id == -1, disable buttons and exit function  
        if student_id == -1:
            for button in self.buttons.values():
                button.configure(state='disabled')
            # Exit function
            return

        # Enable buttons
        for button in self.buttons.values():
            button.configure(state='normal')

        # Update student id
        self.id = student_id
        # Series containing all info for a single student (capitalize all strings for visual appeal)
        student_info = self.database.student[self.database.student['STUDENT_ID'] == student_id
                                                 ].squeeze(
                                                 ).astype('string'
                                                 ).fillna(''
                                                 ).str.title()
        # Get family ID
        family_id = student_info['FAMILY_ID']

        # Dataframe containing payments
        payment_info = self.database.payment[self.database.payment['STUDENT_ID'] == student_id]

        # Dataframe containing info for student's guardians
        if family_id == '' or pd.isna(family_id):
            guardian_info = pd.DataFrame(columns=self.database.guardian.columns)
        else:
            guardian_info = self.database.guardian.loc[self.database.guardian['FAMILY_ID'] == int(family_id)]

        # List of CLASS_IDs which this student is enrolled in
        class_ids = list(self.database.class_student.loc[self.database.class_student['STUDENT_ID'] == student_id, 'CLASS_ID'])

        # Class info for each class_id
        class_info = self.database.classes.loc[self.database.classes['CLASS_ID'].isin(class_ids)
                                               ].sort_values(by='CLASS_ID'
                                               ).loc[:,['CODE','TEACH','CLASSTIME']] 
        
        note_info = self.database.note[self.database.note['STUDENT_ID'] == student_id].reset_index()

        self.studentno_label.configure(text=f'#{student_info['STUDENTNO']}')
        # Configure text for labels
        for field in self.personal_labels.keys():
            # Update non-headers and guardian fields        
            if not any(x in field for x in ['HEADER', 'MOM', 'DAD']):
                if field in ['BALANCE', 'MONTHLYFEE']:
                    self.personal_labels[field].configure(text=f'{float(student_info[field]):.2f}')
                elif field == 'STATE':
                    self.personal_labels[field].configure(text=student_info[field].upper())
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
                # Get label
                label = self.class_labels[row][col]
                # Set text for label depending on certain conditions
                if row == 0 and col == 0:
                    label_txt = student_info['CLASS'].upper()
                elif row == 0 or col == 0:
                    continue
                # Configure labels for actual data
                else:
                    if class_info.empty or row >= class_info.shape[0]+1 or col >= class_info.shape[1]:
                        label_txt = ''
                    else:
                        label_txt = class_info.iloc[row-1, col]
                        label.bind("<Enter>",    lambda event, c=label.master, r=label.grid_info().get('row'):
                                                    fn.highlight_label(c,r))
                        label.bind("<Leave>",    lambda event, c=label.master, r=label.grid_info().get('row'):
                                                    fn.unhighlight_label(c,r))
                        # Using class ID, bind function so that user can click
                        # class instructor/time to pull up class record
                        label.bind("<Button-1>", lambda event, id=class_ids[row-1]:
                                                    self.open_class_record(id))
                        label.configure(cursor='hand2')
                        
                label.configure(text=label_txt)

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
            self.note_labels[f'NOTE{i}'].configure(text=note_txt)


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


    # Function to pull up class's record in ClassInfoFrame. This is bound to labels
    # in the student record 'class_frame' so that the user can simply click the class instructor/time
    # to tell the program that they want to pull up that class.
    def open_class_record(self, class_id):
        # If the tabs menu is currently disabled, the program is in edit mode, so do nothing
        if self.window.tabs._state == 'disabled':
            return
        # Get reference to class search results frame
        class_search_frame = self.window.screens['Classes'].search_results_frame

        # Populate class instructor / day of week filters
        class_info = self.database.classes.loc[self.database.classes['CLASS_ID'] == class_id].squeeze()
        class_search_frame.filter_dropdowns['INSTRUCTOR'].set(class_info['TEACH'].title())
        class_search_frame.filter_dropdowns['DAY'].set(calendar.day_name[class_info['DAYOFWEEK']-1])
        # Activate/disable filters as necessary
        for filter_type, checkbox in class_search_frame.checkboxes.items():
            # Activate instructor / day filters (if not already active)
            if filter_type in ['INSTRUCTOR', 'DAY']:
                if not checkbox.get():
                    checkbox.toggle()
            # Disable gender / level filters (if not already disabled)
            if filter_type in ['GENDER', 'LEVEL']:
                if checkbox.get():
                    checkbox.toggle()
        
        # Update search results using filters set above
        class_search_frame.update_labels()
        # Select class corresponding to class_id
        class_search_frame.select_result(class_id)

        # Change view to ClassInfoFrame
        self.window.change_view(new_screen='Classes')