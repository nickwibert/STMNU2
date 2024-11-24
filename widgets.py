import customtkinter as ctk
import pandas as pd
import functions as fn
from functools import partial
from datetime import datetime
import calendar

class MyFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

# Scrollable frame to display the results from a search 
class SearchResultsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, student_info_frame, max_row, **kwargs):
        super().__init__(master, **kwargs)
        # Link to student info frame
        self.student_info_frame = student_info_frame
        # Maximum number of rows to return
        self.max_row = max_row
        # List of labels
        self.labels = []

    def display_search_results(self, results):
        for label in self.labels:
            label.destroy()
        self.results = results
        # Boolean variable which is True when the number of matches
        # is greater than `max_row`, indicating that we need to truncate the results
        truncate_results = True if self.results.shape[0] > self.max_row else False
        # Number of rows in SearchResultsFrame including potential 'truncated results' message
        # and column headers
        row_count = truncate_results + 1 + min(self.max_row, self.results.shape[0])

        # Populate results into labels
        for row in range(row_count):
            # Configure row
            self.rowconfigure(row, weight=1)
            for col in range(self.results.shape[1]):
                # Create 'truncated results' message (if necessary)
                if row == 0 and truncate_results:
                    truncate_txt = f'Note: the result set below is limited to {self.max_row} records.'
                    label = ctk.CTkLabel(self, text=truncate_txt, text_color='gray40')
                    label.grid(row=row, column=0, columnspan=self.results.shape[1], sticky='nsew')
                    break
                # Create column headers
                elif ((row == 1 and truncate_results) or (row == 0 and not truncate_results)):
                    self.columnconfigure(col, weight=1)
                    label = ctk.CTkLabel(self, text=self.results.columns[col])
                # Labels for actual data
                else:
                    label_txt = self.results.iloc[row-1,col]
                    label = ctk.CTkLabel(self, text=label_txt)
                    student_idx = self.results.index[row-1]
                    label.bind("<Enter>", lambda event, row=row:
                                                self.highlight_label(row))
                    label.bind("<Leave>", lambda event, row=row:
                                                self.unhighlight_label(row))
                    label.bind("<Button-1>", lambda event, idx=student_idx:
                                                self.student_info_frame.update_labels(idx))

                label.grid(row=row, column=col, sticky='nsew')
                self.labels.append(label)
    
    # Highlight student row when mouse hovers over it
    def highlight_label(self, row):
        for child in self.winfo_children():
            info = child.grid_info()
            if info['row'] == row:
                child.configure(fg_color='white smoke')

    # Undo highlight when mouse moves off
    def unhighlight_label(self, row):
        for child in self.winfo_children():
            info = child.grid_info()
            if info['row'] == row:
                child.configure(fg_color='transparent')

class StudentInfoFrame(ctk.CTkFrame):
    def __init__(self, master, database, **kwargs):
        # Create window
        super().__init__(master, **kwargs)
        # Instance of student database
        self.database = database

        # Configure rows/columns
        self.columnconfigure((0,1), weight=1)
        self.rowconfigure(tuple(range(5)), weight=1)
        # # Button to return to search results
        # self.return_to_matches_button = ctk.CTkButton(self,
        #                                     text="Return to Search Results",
        #                                     command=self.return_to_matches)
        # if self.master.matches.shape[0] > 1:
        #     self.master.matches_frame.grid_forget()
        #     self.return_to_matches_button.grid(row=0,column=0)

        # Frame which will contain student personal info
        self.personal_frame = MyFrame(self)
        # Frame which will contain class information
        self.class_frame = MyFrame(self)
        # Frame which will contain payment information
        self.payment_frame = MyFrame(self)
        # Frame which will contain notes
        self.note_frame = MyFrame(self)

        self.personal_frame.grid(row=2, column=0, padx=5, pady=5)
        self.class_frame.grid(row=3, column=0, padx=5, pady=5)
        self.payment_frame.grid(row=2, column=1, padx=(50,5), pady=5)
        self.note_frame.grid(row=3, column=1, padx=5, pady=5)

        # Buttons to scroll through students
        self.prev_next_frame = MyFrame(self.personal_frame)
        self.prev_next_frame.rowconfigure(0,weight=1)
        self.prev_next_frame.columnconfigure((0,1),weight=1)
        self.prev_student_button = ctk.CTkButton(self.prev_next_frame,
                                         text="Previous Student",
                                         command=self.go_prev_student)
        self.master.bind('<Prior>', lambda event: self.go_prev_student())
        self.master.bind('<Left>', lambda event: self.go_prev_student())
        self.next_student_button = ctk.CTkButton(self.prev_next_frame,
                                         text="Next Student",
                                         command=self.go_next_student)
        self.master.bind('<Next>', lambda event: self.go_next_student())
        self.master.bind('<Right>', lambda event: self.go_next_student())
        self.prev_student_button.grid(row=0,column=0,pady=5,padx=5)
        self.next_student_button.grid(row=0,column=1,pady=5,padx=5)
        self.prev_next_frame.grid(row=0,column=0)

        # Populate frame with labels containing student information
        self.create_labels()

        # Button to edit student info
        self.edit_button = ctk.CTkButton(self.personal_frame,
                                         text="Edit",
                                         command=self.edit_student_info)
        self.edit_button.grid(row=self.personal_frame.grid_size()[1], column=0)

        # Create switch to show/hide payments
        self.payment_switch = ctk.CTkSwitch(self.payment_frame,
                                            text='Show/Hide Payments',
                                            variable=ctk.StringVar(value='hide'),
                                            onvalue='show',offvalue='hide')
        self.payment_switch.configure(command = lambda switch=self.payment_switch: self.toggle_view(switch))
        self.payment_switch.grid(row=self.payment_frame.grid_size()[1], column=0)

        self.master.bind('<F2>', lambda event: self.payment_switch.toggle())

        # Create switch to show/hide notes
        self.note_switch = ctk.CTkSwitch(self.note_frame,
                                         text='Show/Hide Notes',
                                         variable=ctk.StringVar(value='hide'),
                                         onvalue='show',offvalue='hide')
        self.note_switch.configure(command = lambda switch=self.note_switch: self.toggle_view(switch))
        self.note_switch.grid(row=self.note_frame.grid_size()[1], column=0)

        # Note: payment_frame and note_frame start out hidden, until user requests to view
        self.toggle_view(self.payment_switch)
        self.toggle_view(self.note_switch)

    # Create a label for each bit of student information and place into the frame
    def create_labels(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(tuple(range(12)),weight=1)

        ### Personal Info Frame ###
        self.labels = {}
        # Display student number above name (cannot be edited)
        self.studentno_label = ctk.CTkLabel(self.personal_frame, text='', font=ctk.CTkFont('Britannic',18), width=self.winfo_reqwidth())
        self.studentno_label.grid(row=self.personal_frame.grid_size()[1],column=0,sticky='nsew')

        # Create frame for full student name
        self.name_frame = MyFrame(self.personal_frame)
        self.name_frame.columnconfigure((0,1,2), weight=1)
        self.name_frame.grid(row=self.personal_frame.grid_size()[1], column=0, sticky='nsew')
        name_font = ctk.CTkFont('Britannic', 18)
        self.labels['FNAME'] = ctk.CTkLabel(self.name_frame, text='', font=name_font, anchor='e')
        self.labels['FNAME'].grid(row=0, column=0, padx=2, sticky='nsew')
        self.labels['MIDDLE'] = ctk.CTkLabel(self.name_frame, text='', font=name_font)
        self.labels['MIDDLE'].grid(row=0, column=1, sticky='nsew')
        self.labels['LNAME'] = ctk.CTkLabel(self.name_frame, text='', font=name_font, anchor='w')
        self.labels['LNAME'].grid(row=0, column=2, padx=2, sticky='nsew')

        # Create frame for full address
        self.address_frame = MyFrame(self.personal_frame)
        self.address_frame.rowconfigure((0,1), weight=1)
        self.address_frame.columnconfigure((0,1,2), weight=1)
        self.address_frame.grid(row=self.personal_frame.grid_size()[1],column=0,rowspan=2, sticky='nsew')

        self.labels['ADDRESS'] = ctk.CTkLabel(self.address_frame,  text='',)
        self.labels['ADDRESS'].grid(row=0, column=0, columnspan=3, sticky='nsew')
        self.labels['CITY'] = ctk.CTkLabel(self.address_frame,  text='',)
        self.labels['CITY'].grid(row=1, column=0, padx=2, sticky='nsew')
        self.labels['STATE'] = ctk.CTkLabel(self.address_frame,  text='',)
        self.labels['STATE'].grid(row=1, column=1, padx=2, sticky='nsew')
        self.labels['ZIP'] = ctk.CTkLabel(self.address_frame,  text='',)
        self.labels['ZIP'].grid(row=1, column=2, padx=2, sticky='nsew')

        # Email address
        self.labels['EMAIL'] = ctk.CTkLabel(self.personal_frame,  text='',)
        self.labels['EMAIL'].grid(row=self.personal_frame.grid_size()[1], column=0, sticky='nsew')

        # Create frame for mother name
        self.mom_frame = MyFrame(self.personal_frame)
        self.mom_frame.columnconfigure((0,1), weight=1)
        self.mom_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.labels['MOM_HEADER'] = ctk.CTkLabel(self.mom_frame, text='Mom:')
        self.labels['MOM_HEADER'].grid(row=0, column=0, sticky='nse', padx=4)
        self.labels['MOMNAME'] = ctk.CTkLabel(self.mom_frame, text='', anchor='w')
        self.labels['MOMNAME'].grid(row=0, column=1, sticky='nsew')

        # Create frame for father name
        self.dad_frame = MyFrame(self.personal_frame)
        self.dad_frame.columnconfigure((0,1), weight=1)
        self.dad_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.labels['DAD_HEADER'] = ctk.CTkLabel(self.dad_frame, text='Dad:')
        self.labels['DAD_HEADER'].grid(row=0,column=0, padx=4, sticky='nse')
        self.labels['DADNAME'] = ctk.CTkLabel(self.dad_frame, text='', anchor='w')
        self.labels['DADNAME'].grid(row=0, column=1, sticky='nsew')

        self.labels['PHONE'] = ctk.CTkLabel(self.personal_frame, text='',)
        self.labels['PHONE'].grid(row=self.personal_frame.grid_size()[1], column=0, sticky='nsew')

        # Create frame for birthday
        self.bday_frame = MyFrame(self.personal_frame)
        self.bday_frame.columnconfigure((0,1), weight=1)
        self.bday_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.labels['BIRTHDAY_HEADER'] = ctk.CTkLabel(self.bday_frame, text='Birthday:', anchor='w')
        self.labels['BIRTHDAY_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['BIRTHDAY'] = ctk.CTkLabel(self.bday_frame, text='', anchor='e')
        self.labels['BIRTHDAY'].grid(row=0, column=1, sticky='nsew')

        # Create frame for enroll date
        self.enrolldate_frame = MyFrame(self.personal_frame)
        self.enrolldate_frame.columnconfigure((0,1), weight=1)
        self.enrolldate_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.labels['ENROLLDATE_HEADER'] = ctk.CTkLabel(self.enrolldate_frame, text='Enroll Date:', anchor='w')
        self.labels['ENROLLDATE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['ENROLLDATE'] = ctk.CTkLabel(self.enrolldate_frame, text='', anchor='e')
        self.labels['ENROLLDATE'].grid(row=0, column=1, sticky='nsew')

        # Create frame for monthly fee
        self.monthlyfee_frame = MyFrame(self.personal_frame)
        self.monthlyfee_frame.columnconfigure((0,1), weight=1)
        self.monthlyfee_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.labels['MONTHLYFEE_HEADER'] = ctk.CTkLabel(self.monthlyfee_frame, text='Monthly Fee:', anchor='w')
        self.labels['MONTHLYFEE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['MONTHLYFEE'] = ctk.CTkLabel(self.monthlyfee_frame, text='', anchor='e')
        self.labels['MONTHLYFEE'].grid(row=0, column=1, sticky='nsew')

        # Create frame for balance
        self.balance_frame = MyFrame(self.personal_frame)
        self.balance_frame.columnconfigure((0,1), weight=1)
        self.balance_frame.grid(row=self.personal_frame.grid_size()[1],column=0, sticky='nsew')
        self.labels['BALANCE_HEADER'] = ctk.CTkLabel(self.balance_frame, text='Balance:', anchor='w')
        self.labels['BALANCE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['BALANCE'] = ctk.CTkLabel(self.balance_frame, text='', anchor='e')
        self.labels['BALANCE'].grid(row=0, column=1, sticky='nsew')

        ### Class Frame ###
        self.class_labels = []
        headers = ['CODE', 'INSTRUCTOR', 'TIME']
        for row in range(3):
            row_labels = []
            for col in range(len(headers)):
                # Create column headers
                if row == 0:
                    row_labels.append(ctk.CTkLabel(self.class_frame, text=headers[col]))
                elif col == 0:
                    row_labels.append(ctk.CTkLabel(self.class_frame, text=f'Class #{row}'))
                # Labels for actual data
                else:
                    # label_txt = class_info.iloc[row-1,col] if not class_info.empty else ''
                    row_labels.append(ctk.CTkLabel(self.class_frame, text='',))

                row_labels[-1].grid(row=row, column=col, sticky='nsew', padx=5)
            
            self.class_labels.append(row_labels)

        ### Payment Frame ###
        self.month_frames = []
        self.payment_labels = [{} for _ in range(14)]
        month_column = ['Month'] + list(calendar.month_name)[1:] + ['Reg. Fee']
        
        # 14 rows (header row + 12 months + registration fee row)
        for row in range(14):
            payment_font = ctk.CTkFont('Britannica',14,'bold') if row in (0,13) else ctk.CTkFont('Britannica',12,'normal')
            # Create a frame for this row
            month_frame = MyFrame(self.payment_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')
            # Create labels for this row
            self.payment_labels[row] = {'MONTH' : ctk.CTkLabel(month_frame, text=month_column[row],
                                                             font=payment_font,
                                                             anchor='w', width=75),
                                        'PAY'   : ctk.CTkLabel(month_frame, text='',
                                                             font=payment_font,
                                                             anchor='e', width=50),
                                        'DATE'  : ctk.CTkLabel(month_frame, text='',
                                                             font=payment_font,
                                                             anchor='e', width=75)}
            # Put labels into grid
            self.payment_labels[row]['MONTH'].grid(row=0,column=0,padx=10,sticky='nsew')
            self.payment_labels[row]['PAY'].grid(row=0,column=1,padx=10,sticky='nsew')
            self.payment_labels[row]['DATE'].grid(row=0,column=2,padx=10,sticky='nsew')
            # Grid and store month frame
            month_frame.grid(row=row, column=0, sticky='nsew')
            self.month_frames.append(month_frame)

        ### Notes Frame ###
        self.note_labels = []
        # Header and Up to 3 notes
        for row in range(4):
            note_txt = 'Notes:' if row == 0 else ''
            label = ctk.CTkLabel(self.note_frame, text=note_txt, anchor='w', width=200, wraplength=200)
            label.grid(row=row, column=0, sticky='nsew')
            self.note_labels.append(label)


    # Update text in labels
    def update_labels(self, student_idx):
        self.student_idx = student_idx
        # Series containing all info for a single student (capitalize all strings for visual appeal)
        self.student_info = self.database.student.iloc[self.student_idx
                                                       ].astype('string'
                                                       ).fillna(''
                                                       ).str.title()
        # Get student ID and family IO
        self.stud_id = self.database.student.iloc[self.student_idx]['STUD_ID']
        self.family_id = self.student_info['FAMILY_ID']

        # Dataframe containing payments
        self.payment_info = self.database.payment[self.database.payment['STUD_ID'] == self.stud_id]

        # Dataframe containing info for student's guardians
        if self.family_id == '':
            self.guardian_info = pd.DataFrame(columns=self.database.guardian.columns)
        else:
            self.guardian_info = self.database.guardian.loc[self.database.guardian['FAMILY_ID'] == int(float(self.student_info['FAMILY_ID']))]


        # List of CLASS_IDs which this student is enrolled in
        class_id = self.database.class_student.loc[self.database.class_student['STUD_ID'] == self.stud_id, 'CLASS_ID']
        # Class info for each class_id
        self.class_info = self.database.classes.loc[self.database.classes['CLASS_ID'].isin(class_id),
                                               ['CODE','TEACH','CLASSTIME']]
        
        self.note_info = self.database.note[self.database.note['STUD_ID'] == self.stud_id].reset_index()

        self.studentno_label.configure(text=f'#{self.student_info['STUDENTNO']}')      
        # Configure text for labels
        for field in self.labels.keys():
            # Update non-headers and guardian fields
            if not any(x in field for x in ['HEADER', 'MOM', 'DAD']):
                if field in ['BALANCE', 'MONTHLYFEE']:
                    self.labels[field].configure(text=f'{float(self.student_info[field]):.2f}')
                else:
                    self.labels[field].configure(text=self.student_info[field])


        # Handle guardians separately
        momname = self.guardian_info.loc[self.guardian_info['RELATION'] == 'MOM', 'FNAME']
        momname_txt = '' if momname.empty else momname.values[0]
        self.labels['MOMNAME'].configure(text=momname_txt)

        dadname = self.guardian_info.loc[self.guardian_info['RELATION'] == 'DAD', 'FNAME']
        dadname_txt = '' if dadname.empty else dadname.values[0]
        self.labels['DADNAME'].configure(text=dadname_txt)

        for row in range(len(self.class_labels)):
            for col in range(len(self.class_labels[0])):
                if row == 0 and col == 0:
                    label_txt = self.student_info['CLASS']
                elif row == 0 or col == 0:
                    continue
                # Configure labels for actual data
                else:
                    if self.class_info.empty or row >= self.class_info.shape[0]+1 or col >= self.class_info.shape[1]:
                        label_txt = ''
                    else:
                        label_txt = self.class_info.iloc[row-1, col]
                self.class_labels[row][col].configure(text=label_txt)

        # Loop through header, 12 months, and registration fee
        for row in range(14):
            # Header row
            if row == 0:
                pay, date = ('Amount', 'Date')
            # Reg. Fee row
            elif row == 13:
                pay, date = (f'{float(self.student_info['REGFEE']):.2f}', self.student_info['REGFEEDATE'])
            # Check if a payment exists for this month
            elif row not in self.payment_info['MONTH'].values:
                pay, date = ('0.00', '')
            else:
                pay = f'{self.payment_info[self.payment_info['MONTH']==row]['PAY'].values[0]:.2f}'
                date = self.payment_info[self.payment_info['MONTH']==row]['DATE'].values[0]
            # Update pay/date text for this month
            self.payment_labels[row]['PAY'].configure(text=pay)
            self.payment_labels[row]['DATE'].configure(text=date)

        # Up to 3 notes
        for i in range(1,4):
            # If note doesn't exist, make text blank
            if i > self.note_info.shape[0]:
                note_txt = ''
            # Otherwise, pull note text from database
            else:
                note_txt = self.note_info.iloc[i-1]['NOTE_TXT']
            # Update text
            self.note_labels[i].configure(text=note_txt)


    # Edit student information currently displayed in window
    def edit_student_info(self):
        # Disable prev/next student buttons
        self.prev_student_button.configure(state='disabled')
        self.next_student_button.configure(state='disabled')
        #self.return_to_matches_button.configure(state='disabled')

        # Replace info labels with entry boxes, and populate with the current info
        self.entry_boxes = dict.fromkeys(self.labels)

        for key in self.labels.keys():
            # Ignore certain labels
            if 'HEADER' in key:
                self.entry_boxes.pop(key)
                continue

            default_text = ctk.StringVar()
            default_text.set(self.labels[key].cget('text'))

            # If field is numeric, enable data validation
            if key in ('ZIP','MONTHLYFEE','BALANCE'):
                vcmd = (self.register(fn.validate_float), '%d', '%P', '%s', '%S')
                self.entry_boxes[key] = ctk.CTkEntry(self.labels[key], textvariable=default_text,
                                                     validate='key', validatecommand=vcmd)
            else:
                self.entry_boxes[key] = ctk.CTkEntry(self.labels[key], textvariable=default_text)

            self.entry_boxes[key].place(x=0, y=0, relheight=1.0, relwidth=1.0)
           
        self.confirm_button = ctk.CTkButton(self.edit_button,
                                            text="Confirm Changes",
                                            command=self.confirm_edit)
        
        self.confirm_button.place(x=0, y=0, relheight=1.0, relwidth=1.0)

        # Also bind Enter to 'confirm'
        self.master.bind('<Return>', lambda event: self.confirm_button.invoke())

        # Initialize empty list for possible error messages
        self.error_labels = []


    # Function to finalize edits to student record, validate the entered data,
    # and then finally call function to update database if entries are valid
    def confirm_edit(self):
        # Get rid of any error labels, if they exist
        if len(self.error_labels) > 0:
            self.master.geometry(f'{self.master.winfo_width()}x{self.master.winfo_height() - 50*len(self.error_labels)}')
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
                                                    wraplength=self.personal_frame.winfo_width()))
                print(self.winfo_width())
                
                self.error_labels[-1].grid(row=self.grid_size()[1], column=0)
                


        # If any errors so far, exit function so user can fix entry
        if len(self.error_labels) > 0:
            # Adjust window size to accomodate
            self.master.geometry(f'{self.master.winfo_width()}x{self.master.winfo_height() + 50*len(self.error_labels)}')
            self.master.update()
            return
        else:
            # Unbind enter key
            self.unbind('<Return>')
            # Update student dataframe and dbf file to reflect changes
            self.database.update_student_info(self.student_idx, self.entry_boxes)
            for field in self.entry_boxes.keys():
                proposed_value = self.entry_boxes[field].get()
                if proposed_value != self.labels[field].cget("text"):
                    self.labels[field].configure(text=proposed_value)
                self.entry_boxes[field].destroy()
            # Get rid of confirm edits button
            self.confirm_button.destroy()
            # Re-enable the deactivated buttons
            self.prev_student_button.configure(state='normal')
            self.next_student_button.configure(state='normal')
            #self.return_to_matches_button.configure(state='normal')

    # Go back to search results window
    def return_to_matches(self):
        # Re-enable search results
        self.master.minsize(0,0)
        self.master.geometry(f'{100*self.master.matches.shape[1]}x600')
        self.master.matches_frame.grid(row=0,column=0,sticky='nsew')
        # Destroy student info frame and all contents
        self.destroy()

    # Change student info window to the previous student (alphabetically)
    def go_prev_student(self):
        # Since the indices are chronological and not alphabetical, first find 
        # the location of the current student after sorting alphabetically
        student_sorted_idx = self.database.sort_student_alphabetical().index.get_loc(self.student_idx)
        # If current student is the first student alphabetically, there are no previous students
        if student_sorted_idx == 0:
            return
        else:
            prev_student_idx = self.database.sort_student_alphabetical().index[student_sorted_idx - 1]
            self.student_idx = prev_student_idx
            self.update_labels()

    # Change student info window to the next student in dataframe
    def go_next_student(self):
        # Since the indices are chronological and not alphabetical, first find 
        # the location of the current student after sorting alphabetically
        student_sorted_idx = self.database.sort_student_alphabetical().index.get_loc(self.student_idx)
        # If current student is the last student alphabetically, there are no subsequent students
        if student_sorted_idx == (self.database.student.shape[0]-1):
            return
        else:
            next_student_idx = self.database.sort_student_alphabetical().index[student_sorted_idx + 1]
            self.student_idx = next_student_idx
            self.update_labels()

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


# Reusable class for the student information window. User searches for a student,
# and then picks an individual student from the resulting matches.
# Multiple windows can be open at once.
class StudentInfoWindow(ctk.CTkToplevel):
    def __init__(self, master, database, *args, **kwargs):
        self.database = database
        # Create and configure window 
        super().__init__(*args, **kwargs)
        self.geometry('400x300')
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=4)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)

        self.search_frame = MyFrame(self)
        self.search_frame.grid(row=0,column=0)

        # Dictionary of entry boxes to stay organized. The keys will act as the labels
        # next to each entry box, and the values will hold the actual EntryBox objects
        self.entry_boxes = dict.fromkeys(['Student Number', 'First Name', 'Middle Name', 'Last Name'])
        # Create and grid each entry box in a loop
        for row, key in list(zip(range(len(self.entry_boxes.keys())), self.entry_boxes.keys())):
            # Label to identify entry box
            label = ctk.CTkLabel(self.search_frame, text=key + ':', anchor='w')
            label.grid(row=row, column=0, sticky='nsew', pady=5, padx=5)
            # If field is numeric, enable data validation
            if row == 0:
                vcmd = (self.register(fn.validate_float), '%d', '%P', '%s', '%S')
                self.entry_boxes[key] = (ctk.CTkEntry(self.search_frame, validate='key', validatecommand=vcmd))
            else:
                self.entry_boxes[key] = (ctk.CTkEntry(self.search_frame))

            self.entry_boxes[key].grid(row=row, column=1, sticky='ew')

        # Frame which will contain all student information
        self.student_info_frame = StudentInfoFrame(self, self.database, width=self.winfo_width()-100)
        self.student_info_frame.grid(row=0, column=1, rowspan=2)

        # Frame which contains results from search
        self.matches_frame = SearchResultsFrame(self, self.student_info_frame, max_row=100)
        self.matches_frame.grid(row=1,column=0,sticky='nsew')
        
        # Button to perform search when clicked 
        self.search_button = ctk.CTkButton(self.search_frame, text='Search', command=self.update_search_results)
        self.search_button.grid(row=len(self.entry_boxes)+1, column=0, columnspan=2)

        # Also bind Enter key to the "Search" button
        self.bind('<Return>', lambda event: self.search_button.invoke())




        self.geometry('1000x700')
        self.update_idletasks()




    def update_search_results(self):
        # Get user input
        query = dict.fromkeys(self.entry_boxes.keys())
        for key in query.keys():
            query[key] = self.entry_boxes[key].get().strip()

        # If user provided no input whatsoever, do nothing
        if set(query.values()) == {''}: return

        # Search for matches
        self.matches = self.database.search_student(query)

        # Update matches in search results frame
        self.matches_frame.display_search_results(self.matches)


    def create_student_info_window(self, student_idx):
        # Selected student index and student id
        self.student_idx = student_idx
        # If no student match was found, display error message and exit function
        if self.student_idx is None:
            self.geometry('200x100')
            ctk.CTkLabel(self, text="No matches found.").pack()
            return
        
        self.minsize(self.student_info_frame.winfo_width(), self.student_info_frame.winfo_height())
        

    # # Create a "label" for each piece of class information that needs to be displayed,
    # # and then place them appropriately in the window
    # def create_class_info_labels(self):





            

    

