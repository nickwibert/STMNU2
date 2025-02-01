import customtkinter as ctk
import pandas as pd
import calendar
from datetime import datetime

import functions as fn
from widgets.search_results_frame import SearchResultsFrame
from widgets.dialog_boxes import MoveStudentDialog, NewStudentDialog

# Global variables
from globals import CURRENT_SESSION

class StudentInfoFrame(ctk.CTkFrame):
    def __init__(self, window, master, database, **kwargs):
        # Create frame
        super().__init__(master, **kwargs)
        # Application window
        self.window = window

        # Instance of student database
        self.database = database
        self.id = None
        self.year = CURRENT_SESSION.year

        self.buttons = {}
        self.switches = {}

        # Configure rows/columns
        self.columnconfigure((0,1,2), weight=1)
        self.rowconfigure((0,1), weight=1)

        # Frame which will contain search boxes / results to perform student search
        self.search_results_frame = SearchResultsFrame(self, type='student', max_row=100)
        # Frame which will contain student personal info
        self.personal_frame = ctk.CTkFrame(self)
        # Frame which will contain class information
        self.class_frame = ctk.CTkFrame(self,)
        # Outer and inner frames which will contain payment information
        self.payment_frame = ctk.CTkFrame(self,)
        self.payment_hide_frame = ctk.CTkFrame(self.payment_frame)
        # Frame which will contain notes
        self.note_frame = ctk.CTkFrame(self,)

        self.search_results_frame.grid(row=0,column=0,rowspan=2, sticky='nsew')
        self.personal_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        self.class_frame.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')
        self.payment_frame.grid(row=0, column=2, padx=5, pady=5, sticky='nsew')
        self.note_frame.grid(row=1, column=2, padx=5, pady=5, sticky='nsew')

        # Buttons to scroll through students (not visible, mapped to keys)
        self.buttons['PREV_STUDENT'] = ctk.CTkButton(self.personal_frame,
                                         text="↑ Previous Student", anchor='w',
                                         command=self.search_results_frame.prev_result)
        self.buttons['NEXT_STUDENT'] = ctk.CTkButton(self.personal_frame,
                                         text="↓ Next Student", anchor='w',
                                         command=self.search_results_frame.next_result)

        # Button to toggle student between active/inactive
        self.active_frame = ctk.CTkFrame(self.personal_frame, fg_color='transparent')
        self.active_frame.columnconfigure((0,1),weight=1)
        ctk.CTkLabel(self.active_frame, text='Status: ',).grid(row=0,column=0,sticky='e')
        self.buttons['ACTIVATE_STUDENT'] = ctk.CTkButton(self.active_frame,
                                                         text='INACTIVE', fg_color='red2', text_color='white',
                                                         command=self.toggle_active)
        self.buttons['ACTIVATE_STUDENT'].grid(row=0,column=1,sticky='w')
        self.active_frame.grid(row=0,column=0,sticky='nsew')

        # Create switch to show/hide payments
        payment_switch = ctk.CTkSwitch(self.payment_frame,
                                            text='Show/Hide Payments',
                                            variable=ctk.StringVar(value='hide'),
                                            onvalue='show',offvalue='hide')
        payment_switch.configure(command = lambda switch=payment_switch, hide=self.payment_hide_frame:
                                                    self.toggle_view(switch,hide))
        payment_switch.grid(row=0, column=0)
        self.payment_hide_frame.grid(row=1, column=0, sticky='ns',padx=0,pady=0)
        self.switches['PAYMENT'] = payment_switch

        # Populate frame with labels containing student information
        self.create_labels()

        # Create switch to show/hide notes
        note_switch = ctk.CTkSwitch(self.note_frame,
                                         text='Show/Hide Notes',
                                         variable=ctk.StringVar(value='hide'),
                                         onvalue='show',offvalue='hide')
        note_switch.select()
        note_switch.configure(command = lambda switch=note_switch, hide=self.note_textbox:
                                                self.toggle_view(switch,hide))
        note_switch.grid(row=0, column=0)
        self.switches['NOTE'] = note_switch

        # Create button to switch between payments for current year and previous year
        self.year_frame = ctk.CTkFrame(self.payment_hide_frame)
        self.year_frame.columnconfigure((0,1),weight=1)
        ctk.CTkLabel(self.year_frame, text='Currently displaying payments for:',).grid(row=0,column=0,sticky='e')
        self.buttons['PAYMENT_YEAR'] = ctk.CTkButton(self.year_frame,
                                        text=self.year,
                                        font=ctk.CTkFont('Segoe UI Light', 14),
                                        command=self.toggle_year)
        self.buttons['PAYMENT_YEAR'].grid(row=0, column=1,sticky='w',padx=5,pady=5)
        self.year_frame.grid(row=0,column=0,sticky='nsew')
        
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
                                                      fn.edit_info(frame, labels, type, year=self.year))
        self.buttons['EDIT_STUDENT_PAYMENT'].grid(row=self.payment_frame.grid_size()[1], column=0)

        # Button to edit payment info
        self.buttons['EDIT_NOTE_STUDENT'] = ctk.CTkButton(self.note_frame,
                                         text="Edit Notes",
                                         command = lambda frame=self.note_frame, labels=self.note_textbox, type='NOTE_STUDENT':
                                                      fn.edit_info(frame, labels, type))
        self.buttons['EDIT_NOTE_STUDENT'].grid(row=self.note_frame.grid_size()[1], column=0)

        # Button to add/remove student from class (to move between classes, see ClassInfoFrame)
        self.buttons['ENROLL_STUDENT'] = ctk.CTkButton(self.class_frame, text='Enroll in Class', command=self.create_move_student_dialog)
        self.buttons['ENROLL_STUDENT'].grid(row=self.class_frame.grid_size()[1], column=0, columnspan=3)

        # Disable all buttons at the start
        for button in self.buttons.values():
            button.configure(state='disabled')

        # Note: payment_frame and note_frame start out hidden, until user requests to view
        self.toggle_view(payment_switch,self.payment_hide_frame)
        # self.toggle_view(note_switch)


    # Create a label for each bit of student information and place into the frame
    def create_labels(self):
        ### Personal Info Frame ###
        self.personal_frame.columnconfigure(0, weight=1)
        self.personal_labels = {}
        # Display student number above name (cannot be edited)
        self.personal_labels['STUDENTNO_HEADER'] = ctk.CTkLabel(self.personal_frame, text='', font=ctk.CTkFont('Britannic',18), width=400)
        self.personal_labels['STUDENTNO_HEADER'].grid(row=self.personal_frame.grid_size()[1],column=0,sticky='nsew')

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
        headers = ['Code', 'Instructor', 'Class Time']
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
        self.payment_hide_frame.columnconfigure(0,weight=1)
        # self.payment_hide_frame.rowconfigure(tuple(range(14)), weight=1)

        self.payment_labels = {}
        # Values that will populate month column
        month_column = ['Month'] + list(calendar.month_name)[1:] + ['Reg. Fee']
        # Prefixes/suffixes to store labels and also access data from STUD00.dbf (JANPAY, JANDATE, etc.)
        prefix = ['HEADER'] + [month.upper() for month in calendar.month_abbr[1:]] + ['REG']
        suffix = [['HEADER','PAY','DATE', 'BILL'] for _ in range(13)]
        # Special row of suffixes for REGFEE (because column with pay is simply 'REGFEE' rather than 'REGFEEPAY', and 'REGBILL')
        suffix.append(['FEEHEADER', 'FEE', 'FEEDATE', 'BILL'])

        # 14 rows (header row + 12 months + registration fee row)
        for row in range(14):
            payment_font = ctk.CTkFont('Britannica',16,'bold') if row in (0,13) else ctk.CTkFont('Britannica',16,'normal')
            # Create a frame for this row
            month_frame = ctk.CTkFrame(self.payment_hide_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')

            month_frame.columnconfigure((0,1,2), weight=1)
            month_frame.grid(row=row+1, column=0, sticky='nsew')

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
            self.payment_labels[prefix[row] + suffix[row][3]] = ctk.CTkLabel(month_frame, text='',
                                                                font=payment_font,
                                                                anchor='e', width=10)
            # Put labels into grid
            self.payment_labels[prefix[row] + suffix[row][0]].grid(row=0,column=0,padx=10,sticky='nsew')
            self.payment_labels[prefix[row] + suffix[row][1]].grid(row=0,column=1,padx=10,sticky='nsew')
            self.payment_labels[prefix[row] + suffix[row][2]].grid(row=0,column=2,padx=10,sticky='nsew')
            self.payment_labels[prefix[row] + suffix[row][3]].grid(row=0,column=3,padx=10,sticky='nsew')


        for field in self.payment_labels.keys():
            if 'HEADER' in field:
                self.payment_labels[field].is_header = True
            else:
                self.payment_labels[field].is_header = False

        ### Notes Frame ###
        # This is handled differently than the other frames, as there is one note field per student.
        # This has no limit on length, so we want a scrollable textbox rather than a label.
        self.note_frame.columnconfigure(0, weight=1)
        self.note_frame.rowconfigure((0,1,2,3),weight=1)
        note_header = ctk.CTkLabel(self.note_frame, text='Notes:', anchor='w')
        note_header.grid(row=1, column=0, sticky='nsew')

        self.note_textbox = ctk.CTkTextbox(self.note_frame, height=200, width=400, wrap='word',
                                           font=ctk.CTkFont('Britannic',24), fg_color=self.note_frame.cget('fg_color'))
        self.note_textbox.grid(row=2,column=0,sticky='nsew')
        # Set to 'disabled' so the displayed text cannot be edited
        self.note_textbox.configure(state='disabled')


    def reset_labels(self):
        # Wipe info from labels
        self.personal_labels['STUDENTNO_HEADER'].configure(text='')

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
            for binding in ['<Button-1>', '<Enter>', '<Leave>']:
                label.unbind(binding)

        # Delete text displayed in note textbox
        self.note_textbox.configure(state='normal')   
        self.note_textbox.delete('1.0', ctk.END)
        self.note_textbox.configure(state='disabled')   


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

        # Dataframe containing payments (for selected year, could be current or previous year)
        payment_info = self.database.payment[(self.database.payment['STUDENT_ID'] == student_id)
                                             & (self.database.payment['YEAR'] == self.year)]
        bill_info = self.database.bill[(self.database.bill['STUDENT_ID'] == student_id)
                                       & (self.database.bill['YEAR'] == self.year)]

        # Dataframe containing info for student's guardians
        if family_id == '' or pd.isna(family_id):
            guardian_info = pd.DataFrame(columns=self.database.guardian.columns)
        else:
            guardian_info = self.database.guardian.loc[self.database.guardian['FAMILY_ID'] == int(family_id)]

        # Class info for each class_id
        class_info = self.database.class_student.loc[self.database.class_student['STUDENT_ID'] == student_id
                                               ].merge(self.database.classes, on='CLASS_ID', how='left'
                                               ).sort_values(by='CLASS_ID'
                                               ).reset_index(drop=True
                                               ).loc[:,['CODE','TEACH','CLASSTIME','CLASS_ID']]
        
        # This will either be empty, or contain exactly one note
        note_info = self.database.note[self.database.note['STUDENT_ID'] == student_id].squeeze()


        # Active Status: change button appearance to match data (if necessary)
        if ((student_info['ACTIVE'] == 'True' and self.buttons['ACTIVATE_STUDENT'].cget('text') == 'INACTIVE')
            or (student_info['ACTIVE'] == 'False' and self.buttons['ACTIVATE_STUDENT'].cget('text') == 'ACTIVE')):
            self.toggle_active(visual_only=True)

        # Student Number
        self.personal_labels['STUDENTNO_HEADER'].configure(text=f'#{student_info['STUDENTNO']}')
        # Configure text for labels
        for field in self.personal_labels.keys():
            # Update non-headers and guardian fields        
            if not any(x in field for x in ['HEADER', 'MOM', 'DAD']):
                if field in ['BALANCE', 'MONTHLYFEE']:
                    label_txt = '' if student_info[field]=='' else f'{float(student_info[field]):.2f}'
                    self.personal_labels[field].configure(text=label_txt)
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
                    if class_info.empty or row >= class_info.shape[0]+1 or col >= class_info.shape[1]-1:
                        label_txt = ''
                    else:
                        label_txt = class_info.iloc[row-1, col]
                        label.bind("<Enter>",    lambda event, c=label.master, r=label.grid_info().get('row'):
                                                    fn.highlight_label(c,r))
                        label.bind("<Leave>",    lambda event, c=label.master, r=label.grid_info().get('row'):
                                                    fn.unhighlight_label(c,r))
                        # Using class ID, bind function so that user can click
                        # class instructor/time to pull up class record
                        label.bind("<Button-1>", lambda event, id=class_info.loc[row-1,'CLASS_ID']:
                                                    self.open_class_record(id))
                        label.configure(cursor='hand2')
                        
                label.configure(text=label_txt)


        # Change color of payment_frame based on which year is displayed
        if self.year == CURRENT_SESSION.year:
            self.payment_hide_frame.configure(fg_color = 'transparent')
            self.year_frame.configure(fg_color = 'transparent')
        else:
            self.payment_hide_frame.configure(fg_color = 'indian red')
            self.year_frame.configure(fg_color = 'indian red')
            

        # Prefixes/suffixes to store labels and also access data from STUD00.dbf (JANPAY, JANDATE, etc.)
        prefix = ['HEADER'] + [month.upper() for month in calendar.month_abbr[1:]] + ['REG']
        suffix = [['HEADER','PAY','DATE', 'BILL'] for _ in range(13)]
        # Special row of suffixes for REGFEE (because column with pay is simply 'REGFEE' rather than 'REGFEEPAY', and 'REGBILL')
        suffix.append(['FEEHEADER', 'FEE', 'FEEDATE', 'BILL'])
        
        # Loop through header, 12 months, and registration fee
        for row in range(14):
            pay_label = self.payment_labels[prefix[row] + suffix[row][1]]
            date_label = self.payment_labels[prefix[row] + suffix[row][2]]
            bill_label = self.payment_labels[prefix[row] + suffix[row][3]]
            # Header row
            if row == 0:
                pay, date, bill = ('Amount', 'Date', 'Bill')
            # Reg. Fee row
            elif row == 13:
                pay = '' if student_info['REGFEE']=='' else f'{float(student_info['REGFEE']):.2f}'
                date = student_info['REGFEEDATE']
                bill = '*' if row in bill_info['MONTH'].values else ''
            # Check if a payment exists for this month
            elif row not in payment_info['MONTH'].values:
                pay, date = ('0.00', '')
                bill = '*' if row in bill_info['MONTH'].values else ''
            else:
                pay = f'{payment_info[payment_info['MONTH']==row]['PAY'].values[0]:.2f}'
                date = payment_info[payment_info['MONTH']==row]['DATE'].values[0]
                bill = '*' if row in bill_info['MONTH'].values else ''
            # Update pay/date text for this month
            pay_label.configure(text=pay)
            date_label.configure(text=date)
            bill_label.configure(text=bill)
            # Change color of alternating rows based on which year is displayed
            if row % 2 == 0:
                pay_label.master.configure(fg_color='salmon' if self.year != CURRENT_SESSION.year else 'grey70')

        # If note exists, insert into textbox
        if not note_info.empty:
            self.note_textbox.configure(state='normal')   
            self.note_textbox.insert('1.0', note_info['NOTE_TXT'])
            self.note_textbox.configure(state='disabled')   


    # Show/hide student's payment info or notes
    def toggle_view(self, switch, widget_to_hide):
        if switch.get() == 'show':
            widget_to_hide.lift()
        elif switch.get() == 'hide':
            widget_to_hide.lower()

    # Toggle student between active/inactive
    # If `visual_only`=True, we just change the button's appearance to match the data.
    # Otherwise, the value stored in the database under 'ACTIVE' will also be changed.
    def toggle_active(self, visual_only=False):
        button = self.buttons['ACTIVATE_STUDENT']
        # Change button text and color
        if button.cget('text') == 'INACTIVE':
            button.configure(text='ACTIVE', fg_color='forest green')
        else:
            button.configure(text='INACTIVE', fg_color='red2')

        # Update 'ACTIVE' in database
        if not visual_only:
            self.database.activate_student(student_id=self.id)
            # Refresh class info frame 
            self.window.screens['Classes'].search_results_frame.update_labels(select_first_result=False)

    # Toggle bill status
    # In the payment_frame, under `bill` column, there will be an asterisk (*) if a payment
    # is owed for that month. This function toggles the asterisk on/off when the month is clicked.
    def toggle_bill(self, month_num):
        if month_num == 13:
            month = 'REG'
        else:
            # Integer corresponding to the month this payment applies to
            month = calendar.month_abbr[month_num].upper()
        label = self.payment_labels[f'{month}BILL']
        label_txt = '' if label.cget('text') == '*' else '*'
        # Toggle (*) in view
        label.configure(text=label_txt)

        # Update 'bill' in database
        self.database.bill_student(student_id=self.id, month_num=month_num, year=self.year)

        # Refresh class info frame 
        self.window.screens['Classes'].search_results_frame.update_labels(select_first_result=False)

    
    # Toggle payment year between current/previous year
    def toggle_year(self):
        # Change the stored year and update labels
        self.year = CURRENT_SESSION.year - 1 if self.year == CURRENT_SESSION.year else CURRENT_SESSION.year
        button = self.buttons['PAYMENT_YEAR']
        new_color = 'steelblue3' if self.year == CURRENT_SESSION.year else 'salmon'
        button.configure(text=self.year, fg_color=new_color)
        self.update_labels(self.id)


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


    # Create pop-up window for adding student to a class.
    # In this window the user will select the parameters for the class they wish to add the student to.
    def create_move_student_dialog(self):
        # In this case, there is only one student label (the currently selected student)
        # But we need to pass it in to MoveStudentDialog as a list containing one label
        student_info = self.database.student.loc[self.database.student['STUDENT_ID'] == self.id].squeeze()
        label = ctk.CTkLabel(self, text=f"1. {student_info['FNAME']} {student_info['LNAME']}")
        label.student_id = self.id
        student_labels = [label]

        move_window = MoveStudentDialog(window=self.window,
                                        title='Enroll Student',
                                        database=self.database,
                                        current_class_id=-1,
                                        student_labels=student_labels)
        # Wait for the move student dialog window to be closed
        self.wait_window(move_window)
        # Update the displayed classes
        self.update_labels(self.id)


    def create_student(self):
        new_window = NewStudentDialog(window=self.window,
                                      title='New Student',
                                      database=self.database)
    