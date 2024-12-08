import customtkinter as ctk

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

        # Configure rows/columns
        self.columnconfigure((0,1,2), weight=1)
        self.rowconfigure((0,1,2), weight=1)

        self.search_results_frame = SearchResultsFrame(self, type='class', max_row=100)
        self.header_frame = ctk.CTkFrame(self)
        self.roll_frame = ctk.CTkFrame(self)
        self.wait_frame = ctk.CTkFrame(self)
        self.trial_frame = ctk.CTkFrame(self)
        self.note_frame = ctk.CTkFrame(self)

        self.search_results_frame.grid(row=0, column=0, rowspan=3, sticky='nsew')
        self.header_frame.grid(row=0, column=1, sticky='nsew')
        self.roll_frame.grid(row=1, column=1, rowspan=2, sticky='nsew')
        self.wait_frame.grid(row=0, column=2, sticky='nsew')
        self.trial_frame.grid(row=1, column=2, sticky='nsew')
        self.note_frame.grid(row=2, column=2, sticky='nsew')

        self.create_labels()

    def create_labels(self):
        ### Class Header Frame ###
        self.header_frame.columnconfigure(0, weight=1)
        self.header_labels = {}
        self.header_labels['TEACH'] = ctk.CTkLabel(self.header_frame, text='', width=300, anchor='w')
        self.header_labels['CLASSTIME'] = ctk.CTkLabel(self.header_frame, text='', width=300, anchor='w')
        self.header_labels['CLASSNAME'] = ctk.CTkLabel(self.header_frame, text='', width=300, anchor='w')
        self.header_labels['SESSION'] = ctk.CTkLabel(self.header_frame, text='', width=300, anchor='w')

        # Put labels in header_frame
        for label in self.header_labels.values():
            label.grid(row=self.header_frame.grid_size()[1], column=0, sticky='nsew')


        ### Class Roll Frame ###
        self.roll_frame.columnconfigure(0, weight=1)
        self.roll_labels = {}

        # Create placeholder labels based on global variable for max class size
        for row in range(1,MAX_CLASS_SIZE+1):
            self.roll_labels[f'STUDENT{row}'] = ctk.CTkLabel(self.roll_frame, width=200,
                                                             text=f'{row}. ', anchor='w',
                                                             fg_color='grey70' if row % 2 == 0 else 'transparent',
                                                             cursor='hand2')
            self.roll_labels[f'STUDENT{row}'].grid(row=self.roll_frame.grid_size()[1], column=0, sticky='nsew')

        
        ### Waitlist Frame ###
        self.wait_frame.columnconfigure(0, weight=1)
        self.wait_labels = {}
        # Create placeholder labels based on global variable for max waitlist size
        for row in range(1,MAX_WAIT_SIZE+1):
            row_frame = ctk.CTkFrame(self.wait_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')
            row_frame.columnconfigure((0,1), weight=1)
            row_frame.grid(row=self.wait_frame.grid_size()[1], column=0, sticky='nsew')

            self.wait_labels[f'WAIT{row}'] = ctk.CTkLabel(row_frame, width=200, text=f'{row}. ', anchor='w')
            self.wait_labels[f'WAIT{row}'].grid(row=0, column=0, sticky='nsew')

            self.wait_labels[f'W{row}PHONE'] = ctk.CTkLabel(row_frame, text='', anchor='e')
            self.wait_labels[f'W{row}PHONE'].grid(row=0, column=1, sticky='nsew')


        ### Trial Frame ###
        self.trial_frame.columnconfigure(0, weight=1)
        self.trial_labels = {}
        # Create placeholder labels based on global variable for max trial size
        for row in range(1,MAX_TRIAL_SIZE+1):
            row_frame = ctk.CTkFrame(self.trial_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')
            row_frame.columnconfigure((0,1), weight=1)
            row_frame.grid(row=self.trial_frame.grid_size()[1], column=0, sticky='nsew')

            self.trial_labels[f'TRIAL{row}'] = ctk.CTkLabel(row_frame, width=200, text=f'{row}. ', anchor='w')
            self.trial_labels[f'TRIAL{row}'].grid(row=0, column=0, sticky='nsew')

            self.trial_labels[f'T{row}PHONE'] = ctk.CTkLabel(row_frame, text='', anchor='e')
            self.trial_labels[f'T{row}PHONE'].grid(row=0, column=1, sticky='nsew')

            self.trial_labels[f'T{row}DATE'] = ctk.CTkLabel(row_frame, text='', anchor='w')
            self.trial_labels[f'T{row}DATE'].grid(row=0, column=1, sticky='nsew')

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
                            ].merge(self.database.student, how='left', on='STUD_ID'
                            ).loc[:,['STUD_ID','FAMILY_ID','STUDENTNO','FNAME','LNAME','BIRTHDAY']]


        ### Class Header Frame ###
        for field in self.header_labels.keys():
            label = self.header_labels[field]
            label.configure(text=header_info[field])

        ### Class Roll Frame ###
        # First, wipe all roll labels and remove from grid
        for label in self.roll_labels.values():
            label.configure(text='')
            label.unbind('<Button-1>')
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

                    # Bind function so that user can click student name in class roll to pull up student record
                    roll_label.bind("<Button-1>", lambda event, student_id=roll_info.loc[row,'STUD_ID']:
                                                    self.open_student_record(student_id))

                # Update and grid roll label
                roll_label.configure(text=roll_txt)
                roll_label.grid()


    # Function to pull up student's record in StudentInfoFrame. This is bound to labels
    # in the class roll frame so that the user can simply click the student's name to
    # tell the program that they want to see that student's information.
    def open_student_record(self, student_id):
        student_search_frame = self.window.screens['Student Info'].search_results_frame

        # Populate student's first/last name into the search fields and perform search
        student_info = self.database.student.loc[self.database.student['STUD_ID'] == student_id].squeeze()
        student_search_frame.entry_boxes['First Name'].cget('textvariable').set(student_info['FNAME'])
        student_search_frame.entry_boxes['Last Name'].cget('textvariable').set(student_info['LNAME'])
        student_search_frame.search_button.invoke()

        # Change view to StudentInfoFrame
        self.window.change_view(new_screen='Student Info')
