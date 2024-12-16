import customtkinter as ctk
import functions as fn

from widgets.search_results_frame import SearchResultsFrame

# Hard-coded global values 
MAX_CLASS_SIZE = 16
MAX_WAIT_SIZE = 4
MAX_TRIAL_SIZE = 8

# Reusable frame for class information (intended to mimic the screen from the dBASE
# program after using class search)
class ClassInfoFrame(ctk.CTkFrame):
    def __init__(self, window, master, database, **kwargs):
        # Create frame
        super().__init__(master, **kwargs)
        # Application window
        self.window = window
        # Instance of student database
        self.database = database
        # Class
        self.id = None
        # Dictionary for buttons
        self.buttons = {}

        # Configure rows/columns
        self.columnconfigure((0,1,2), weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure((1,2), weight=3)

        # Containers for various information
        self.header_frame = ctk.CTkFrame(self)
        self.roll_frame = ctk.CTkFrame(self, border_width=5)
        self.wait_frame = ctk.CTkFrame(self, border_width=5)
        self.trial_frame = ctk.CTkFrame(self, border_width=5)
        self.note_frame = ctk.CTkFrame(self)
        # Create labels for frames created above
        self.create_labels()
        # Add frames to grid, leaving first column (column 0) open for search results
        self.header_frame.grid(row=0, column=1, sticky='nsew')
        self.roll_frame.grid_propagate(False)
        self.roll_frame.grid(row=1, column=1, rowspan=2, sticky='nsew')
        self.wait_frame.grid(row=0, column=2, sticky='nsew')
        self.trial_frame.grid(row=1, column=2, sticky='nsew')
        self.note_frame.grid(row=2, column=2, sticky='nsew')

        # Create and add search results frame to grid
        self.search_results_frame = SearchResultsFrame(self, type='class', max_row=100)
        self.search_results_frame.grid(row=0, column=0, rowspan=3, sticky='nsew')

        # Button to edit waitlist
        self.buttons['EDIT_WAIT'] = ctk.CTkButton(self.wait_frame,
                                                  text="Edit Waitlist",
                                                  command = lambda frame=self.wait_frame, labels=self.wait_labels, type='WAIT':
                                                               fn.edit_info(frame, labels, type))
        self.buttons['EDIT_WAIT'].grid(row=self.wait_frame.grid_size()[1], column=0, pady=10)
        # Button to edit trials
        self.buttons['EDIT_TRIAL'] = ctk.CTkButton(self.trial_frame,
                                                  text="Edit Trials",
                                                  command = lambda frame=self.trial_frame, labels=self.trial_labels, type='TRIAL':
                                                               fn.edit_info(frame, labels, type))
        self.buttons['EDIT_TRIAL'].grid(row=self.trial_frame.grid_size()[1], column=0, pady=10)
        # Button to edit notes
        self.buttons['EDIT_NOTE_CLASS'] = ctk.CTkButton(self.note_frame,
                                                  text="Edit Notes",
                                                  command = lambda frame=self.note_frame, labels=self.note_labels, type='NOTE_CLASS':
                                                               fn.edit_info(frame, labels, type))
        self.buttons['EDIT_NOTE_CLASS'].grid(row=self.note_frame.grid_size()[1], column=0, pady=10)



    def create_labels(self):
        ### Class Header Frame ###
        self.header_frame.columnconfigure(0, weight=1)
        self.header_labels = {}
        for header in ['TEACH', 'CLASSTIME', 'CLASSNAME', 'SESSION']:
            # Create label and add to grid
            label = ctk.CTkLabel(self.header_frame, text='', width=300, anchor='w')
            label.grid(row=self.header_frame.grid_size()[1], column=0, sticky='nsew')
            # Store header label
            self.header_labels[header] = label


        ### Class Roll Frame ###
        self.roll_frame.columnconfigure(0, weight=1)
        self.roll_labels = {}

        # Create placeholder labels based on global variable for max class size
        for row in range(1,MAX_CLASS_SIZE+1):
            label = ctk.CTkLabel(self.roll_frame, width=300,
                                 text=f'{row}. ', anchor='w',
                                 bg_color='grey70' if row % 2 == 0 else 'transparent',
                                 cursor='hand2')
            label.grid(row=self.roll_frame.grid_size()[1], column=0, padx=10, pady=(5,0), sticky='nsew')
            # Store label using field name from DBF file
            self.roll_labels[f'STUDENT{row}'] = label

        
        ### Waitlist Frame ###
        self.wait_frame.columnconfigure(0, weight=1)
        self.wait_labels = {}
        # Create placeholder labels based on global variable for max waitlist size
        for row in range(1,MAX_WAIT_SIZE+1):
            row_frame = ctk.CTkFrame(self.wait_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')
            row_frame.columnconfigure((0,1), weight=1)
            row_frame.grid(row=self.wait_frame.grid_size()[1], column=0, padx=10, pady=(5,0), sticky='nsew')
            # Waitlist name
            name_label = ctk.CTkLabel(row_frame, width=300, text=f'{row}. ', anchor='w')
            name_label.grid(row=0, column=0, sticky='nsew')
            # Waitlist phone number
            phone_label = ctk.CTkLabel(row_frame, width=100, text='', anchor='e')
            phone_label.grid(row=0, column=1, sticky='nsew')
            # Store labels using field names from DBF 
            self.wait_labels[f'WAIT{row}'] = name_label
            self.wait_labels[f'W{row}PHONE'] = phone_label


        ### Trial Frame ###
        self.trial_frame.columnconfigure(0, weight=1)
        self.trial_labels = {}
        # Create placeholder labels based on global variable for max trial size
        for row in range(1,MAX_TRIAL_SIZE+1):
            row_frame = ctk.CTkFrame(self.trial_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')
            row_frame.columnconfigure((0,1), weight=1)
            row_frame.grid(row=self.trial_frame.grid_size()[1], column=0, padx=10, pady=(5,0), sticky='nsew')
            # Trial name
            name_label = ctk.CTkLabel(row_frame, width=250, text=f'{row}. ', anchor='w')
            name_label.grid(row=0, column=0, sticky='nsew')
            # Trial phone number
            phone_label = ctk.CTkLabel(row_frame, width=100, text='', anchor='w')
            phone_label.grid(row=0, column=1, sticky='nsew')
            # Trial date
            date_label = ctk.CTkLabel(row_frame, width=100, text='', anchor='w')
            date_label.grid(row=0, column=2, sticky='nsew')
            # Store labels using field names from DBF
            self.trial_labels[f'TRIAL{row}']  = name_label
            self.trial_labels[f'T{row}PHONE'] = phone_label
            self.trial_labels[f'T{row}DATE']  = date_label


        ### Notes Frame ###
        self.note_labels = {}
        # Header and Up to 4 notes
        for row in range(5):
            suffix = '_HEADER' if row == 0 else row
            note_txt = 'Notes:' if row == 0 else ''
            label = ctk.CTkLabel(self.note_frame, text=note_txt, anchor='w', width=200, wraplength=200)
            label.grid(row=row+1, column=0, sticky='nsew')
            label.is_header = True if row == 0 else False
            self.note_labels[f'NOTE{suffix}'] = label


    def update_labels(self, class_id):
        # SPECIAL CASE: If student_id == -1, disable buttons and reset all the labels to blank
        if class_id == -1:
            for label in self.header_labels.values():
                label.configure(text='')
            for label in self.roll_labels.values():
                label.configure(text='')

            # Exit function
            return

        # Currently selected class
        self.id = class_id

        header_info = self.database.classes[self.database.classes['CLASS_ID'] == class_id].squeeze()
        roll_info = self.database.class_student[self.database.class_student['CLASS_ID'] == class_id
                            ].merge(self.database.student, how='left', on='STUDENT_ID'
                            ).loc[:,['STUDENT_ID','FAMILY_ID','STUDENTNO','FNAME','LNAME','BIRTHDAY']
                            ].reset_index(drop=True)
        wait_info = self.database.wait[self.database.wait['CLASS_ID'] == class_id
                            ].reset_index(drop=True
                            ).fillna('')
        trial_info = self.database.trial[self.database.trial['CLASS_ID'] == class_id
                            ].reset_index(drop=True
                            ).fillna('')
        note_info = self.database.note[self.database.note['CLASS_ID'] == class_id].reset_index()

        ### Class Header Frame ###
        for field in self.header_labels.keys():
            label = self.header_labels[field]
            label.configure(text=header_info[field])

        ### Class Roll Frame ###
        # First, wipe all roll labels and remove from grid
        for label in self.roll_labels.values():
            label.configure(text='')
            for binding in ['<Button-1>', '<Enter>', '<Leave>']:
                label.unbind(binding)
            label.grid_remove()
        # Get max class size from `classes`
        max_class_size = header_info['MAX']
        # Populate roll labels
        for row in range(len(self.roll_labels)):
            roll_label = self.roll_labels[f'STUDENT{row+1}']
            # If we have not yet reached max_class_size, update roll label
            if row < max_class_size:
                # Start label with roll #
                roll_txt = f"{row+1}. "
                # If student exists for this row, add their name
                if row < roll_info.shape[0]:
                    roll_txt += f"{roll_info.loc[row,'FNAME']} {roll_info.loc[row,'LNAME']}"

                    roll_label.bind("<Enter>",    lambda event, c=roll_label.master, r=row:
                                                     fn.highlight_label(c,r))
                    roll_label.bind("<Leave>",    lambda event, c=roll_label.master, r=row:
                                                     fn.unhighlight_label(c,r))
                    # Bind function so that user can click student name in class roll to pull up student record
                    roll_label.bind("<Button-1>", lambda event, student_id=roll_info.loc[row,'STUDENT_ID']:
                                                     self.open_student_record(student_id))

                # Update and grid roll label
                roll_label.configure(text=roll_txt)
                roll_label.grid()

        ### Waitlist Frame ###
        for row in range(MAX_WAIT_SIZE):
            wait_name_label = self.wait_labels[f'WAIT{row+1}']
            wait_name_txt = ''
            wait_phone_label = self.wait_labels[f'W{row+1}PHONE']
            wait_phone_txt = ''
            # If student exists for this row, add their name and phone
            if row < wait_info.shape[0]:
                wait_name_txt += wait_info.iloc[row]['NAME']
                wait_phone_txt += str(wait_info.loc[row,'PHONE'])

            # Update wait labels
            wait_name_label.configure(text=wait_name_txt)
            wait_phone_label.configure(text=wait_phone_txt)


        ### Trial Frame ###
        for row in range(MAX_TRIAL_SIZE):
            trial_name_label = self.trial_labels[f'TRIAL{row+1}']
            trial_name_txt = ''
            trial_phone_label = self.trial_labels[f'T{row+1}PHONE']
            trial_phone_txt = ''
            trial_date_label = self.trial_labels[f'T{row+1}DATE']
            trial_date_txt = ''
            trial_row = trial_info.loc[trial_info['TRIAL_NO'] == row+1].squeeze()
            # If trial exists for this row, add their name, phone, date
            if not trial_row.empty:
                trial_name_txt += trial_row['NAME']
                trial_phone_txt += str(trial_row['PHONE'])
                trial_date_txt += str(trial_row['DATE'])

            # Update wait labels
            trial_name_label.configure(text=trial_name_txt)
            trial_phone_label.configure(text=trial_phone_txt)
            trial_date_label.configure(text=trial_date_txt)

        ### Note Frame ###
        # Up to 4 notes
        for i in range(1,5):
            # If note doesn't exist, make text blank
            if i > note_info.shape[0]:
                note_txt = ''
            # Otherwise, pull note text from database
            else:
                note_txt = note_info.iloc[i-1]['NOTE_TXT']
            # Update text
            self.note_labels[f'NOTE{i}'].configure(text=note_txt)


    # Function to pull up student's record in StudentInfoFrame. This is bound to labels
    # in the class roll frame so that the user can simply click the student's name to
    # tell the program that they want to see that student's information.
    def open_student_record(self, student_id):
        # Get reference to student search results frame
        student_search_frame = self.window.screens['Student Info'].search_results_frame

        # Populate student's first/last name into the search fields and perform search
        student_info = self.database.student.loc[self.database.student['STUDENT_ID'] == student_id].squeeze()
        student_search_frame.entry_boxes['First Name'].cget('textvariable').set(student_info['FNAME'])
        student_search_frame.entry_boxes['Last Name'].cget('textvariable').set(student_info['LNAME'])
        student_search_frame.search_button.invoke()

        # Change view to StudentInfoFrame
        self.window.change_view(new_screen='Student Info')
        
