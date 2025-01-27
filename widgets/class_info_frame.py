import customtkinter as ctk
import calendar
from datetime import datetime
import functions as fn

from widgets.search_results_frame import SearchResultsFrame
from widgets.dialog_boxes import MoveStudentDialog

# Global values
from globals import CURRENT_SESSION, MAX_CLASS_SIZE, MAX_WAIT_SIZE, MAX_TRIAL_SIZE

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
        self.roll_frame = ctk.CTkFrame(self, border_width=5, border_color='midnightblue')
        self.wait_frame = ctk.CTkFrame(self, border_width=5, border_color='red4')
        self.trial_frame = ctk.CTkFrame(self, border_width=5, border_color='darkolivegreen')
        self.note_frame = ctk.CTkFrame(self, border_width=5, border_color='goldenrod')
        # Create labels for frames created above
        self.create_labels()
        # Blink text
        self.blink_text()
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

        ### BUTTONS ###
        # Invisible buttons to scroll through classes. These will not actually be displayed to the user.
        # We create these so that we can easily disable the scrolling function along with all other buttons
        # when 'Edit' mode is activated
        self.buttons['PREV_CLASS'] = ctk.CTkButton(self, command=self.search_results_frame.prev_result)
        self.buttons['NEXT_CLASS'] = ctk.CTkButton(self, command=self.search_results_frame.next_result)
        # Button to move students to a different class
        self.buttons['MOVE_STUDENT'] = ctk.CTkButton(self.roll_frame,
                                                     text='Move Student',
                                                     command = self.create_move_student_dialog)
        self.buttons['MOVE_STUDENT'].grid(row=MAX_CLASS_SIZE+1, column=0, pady=10)
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
        title_font = ctk.CTkFont('Segoe UI Light', 18, 'bold')
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
        self.roll_frame.columnconfigure(0,weight=1)
        self.roll_labels = {}
        roll_title = ctk.CTkLabel(self.roll_frame, fg_color=self.roll_frame.cget('border_color'),
                                   text='Class Roll', font=title_font, text_color='white')
        roll_title.grid(row=self.roll_frame.grid_size()[1], column=0, sticky='nsew')
        # Create placeholder labels based on global variable for max class size
        for row in range(1,MAX_CLASS_SIZE+1):
            # Student name
            name_label = ctk.CTkLabel(self.roll_frame, width=300, anchor='w',
                                      bg_color='gray70' if row % 2 == 0 else 'gray80',
                                      cursor='hand2')
            name_label.grid(row=self.roll_frame.grid_size()[1], column=0, sticky='nsew', padx=5)
            # Placeholder attribute for student ID and blinking
            name_label.student_id = -1
            name_label.blink = False
            # Store labels using field names from DBF
            self.roll_labels[f'STUDENT{row}'] = name_label

        
        ### Waitlist Frame ###
        self.wait_frame.columnconfigure(0, weight=1)
        self.wait_labels = {}
        wait_title = ctk.CTkLabel(self.wait_frame, fg_color=self.wait_frame.cget('border_color'),
                                   text='Waitlist', font=title_font, text_color='white')
        wait_title.grid(row=self.wait_frame.grid_size()[1], column=0, sticky='nsew')
        # Create placeholder labels based on global variable for max waitlist size
        for row in range(1,MAX_WAIT_SIZE+1):
            row_frame = ctk.CTkFrame(self.wait_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')
            row_frame.columnconfigure((0,1), weight=1)
            row_frame.grid(row=self.wait_frame.grid_size()[1], column=0, padx=10, sticky='nsew')
            # Waitlist name
            name_label = ctk.CTkLabel(row_frame, width=300, text=f'{row}. ', anchor='w')
            name_label.grid(row=0, column=0, pady=(5,0), sticky='nsew')
            # Waitlist phone number
            phone_label = ctk.CTkLabel(row_frame, width=100, text='', anchor='e')
            phone_label.grid(row=0, column=1, sticky='nsew')
            # Store labels using field names from DBF 
            self.wait_labels[f'WAIT{row}'] = name_label
            self.wait_labels[f'W{row}PHONE'] = phone_label


        ### Trial Frame ###
        self.trial_frame.columnconfigure(0, weight=1)
        self.trial_labels = {}
        trial_title = ctk.CTkLabel(self.trial_frame, fg_color=self.trial_frame.cget('border_color'),
                                   text='Trials', font=title_font, text_color='white')
        trial_title.grid(row=self.trial_frame.grid_size()[1], column=0, sticky='nsew')
        # Create placeholder labels based on global variable for max trial size
        for row in range(1,MAX_TRIAL_SIZE+1):
            row_frame = ctk.CTkFrame(self.trial_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')
            row_frame.columnconfigure((0,1), weight=1)
            row_frame.grid(row=self.trial_frame.grid_size()[1], column=0, padx=10, sticky='nsew')
            # Trial name
            name_label = ctk.CTkLabel(row_frame, width=250, text=f'{row}. ', anchor='w')
            name_label.grid(row=0, column=0, pady=(5,0), sticky='nsew')
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
        self.note_frame.columnconfigure(0, weight=1)
        self.note_labels = {}
        note_title = ctk.CTkLabel(self.note_frame, fg_color=self.note_frame.cget('border_color'),
                                   text='Notes', font=title_font, text_color='white')
        note_title.grid(row=self.note_frame.grid_size()[1], column=0, sticky='nsew')
        note_font = ctk.CTkFont('Britannic',18)
        # Up to 4 notes
        for row in range(1,5):
            label = ctk.CTkLabel(self.note_frame, text='', font=note_font, anchor='w', width=200)
            label.grid(row=self.note_frame.grid_size()[1], column=0, sticky='nsew')
            self.note_labels[f'NOTE{row}'] = label


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

        roll_info = self.database.class_student[(self.database.class_student['CLASS_ID'] == class_id)
                            ].merge(self.database.student[self.database.student['ACTIVE']],
                                    how='inner',
                                    on='STUDENT_ID'
                            ).merge(self.database.payment[((self.database.payment['MONTH'] == CURRENT_SESSION.month)
                                                          & (self.database.payment['YEAR'] == CURRENT_SESSION.year))],
                                    how='left',
                                    on='STUDENT_ID'
                            ).loc[:,['PAY','STUDENT_ID','FAMILY_ID','FNAME','LNAME','BIRTHDAY']]
        # Create 'PAID' which is true if student has a non-zero payment for the current month/year
        roll_info['PAID'] = roll_info['PAY'] > 0
        # Create 'BILLED' which is true if student has been billed for the current month/year
        # (since they have a bill record, someone has confirmed that the student
        # is attending and plans to pay; therefore they will take up a spot in the class)
        roll_info['BILLED'] = roll_info['STUDENT_ID'].isin(self.database.bill.loc[((self.database.bill['MONTH'] == CURRENT_SESSION.month)
                                                                             & (self.database.bill['YEAR'] == CURRENT_SESSION.year)),'STUDENT_ID'].values)
        
        # Create 'BILL_COUNT' which is the number of payments owed by each student in `roll_info`
        # (this is simply determined by the number of records that student currently has in the `bill` table)
        roll_info = roll_info.merge(self.database.bill.groupby('STUDENT_ID').size().reset_index(name='BILL_COUNT'),
                                    how='left',
                                    on='STUDENT_ID'
                            ).fillna(0)
        roll_info = roll_info.sort_values(by=['PAID','BILLED','LNAME'], ascending=[False,False,True]
                            ).reset_index(drop=True)
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
            label.configure(text='', text_color='black')
            label.student_id = -1
            for binding in ['<Button-1>', '<Enter>', '<Leave>']:
                label.unbind(binding)
            # Reset blinking
            label.blink = False
            # Hide entire row from view
            label.lower()

        # Get max class size from `classes`
        max_class_size = header_info['MAX']
        # Get current class size as the number of students who have paid/been billed for the current month
        actual_class_size = roll_info.loc[(roll_info['PAID'] | roll_info['BILLED'])].shape[0]
        # Get 'potential' class size as the number of students who are listed as part of this class, regardless of payment
        potential_class_size = roll_info.shape[0]

        # Populate roll labels
        for row in range(1,MAX_CLASS_SIZE+1):
            label = self.roll_labels[f'STUDENT{row}']
            # Update roll label if we have not reached potential_class_size or max_class_size
            # (whichever is larger)
            if row <= max(potential_class_size, max_class_size):
                # Lift row back into view
                label.lift()
                # Create variable to store student name (if exists)
                roll_txt = f"{row}. "
                # If student exists for this row, add their name
                if row <= potential_class_size:
                    # Student name
                    roll_txt += f"{roll_info.loc[row-1,'FNAME']} {roll_info.loc[row-1,'LNAME']}"
                    # Store student ID as attribute as well (this will be necessary for moving students between classes)
                    label.student_id = roll_info.loc[row-1, 'STUDENT_ID']

                    # Highlight label when mouse hovers over it
                    label.bind("<Enter>",    lambda event, c=label.master, r=label.grid_info().get('row'):
                                                     fn.highlight_label(c,r))
                    label.bind("<Leave>",    lambda event, c=label.master, r=label.grid_info().get('row'):
                                                     fn.unhighlight_label(c,r))
                    # Click student name in class roll to pull up student record
                    label.bind("<Button-1>", lambda event, student_id=roll_info.loc[row-1,'STUDENT_ID']:
                                                     self.open_student_record(student_id))
                    
                    # If this is a 'potential' student, their name should be blinking
                    # (all rows up to `actual_class_size` are students who are paid for current month)
                    label.blink = row > actual_class_size

                    # Add dollar signs ($) after the student's name if they owe for previous months
                    # (i.e. if a student has 3 asterisks under 'BILL', 3 dollar signs should display here)
                    bill_count = int(roll_info.loc[row-1, 'BILL_COUNT'])
                    if bill_count > 0:
                        roll_txt += ' ' + '$'*bill_count

                # Update text in label
                label.configure(text=roll_txt,)

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

    # Blinking texts on labels which require it
    def blink_text(self):
        for label in self.roll_labels.values():
            if label.blink:
                text_color = label.cget('bg_color') if label.cget('text_color') == 'black' else 'black'
                label.configure(text_color=text_color)
        
        self.after(250, self.blink_text)

    # Function to pull up student's record in StudentInfoFrame. This is bound to labels
    # in the class roll frame so that the user can simply click the student's name to
    # tell the program that they want to see that student's information.
    def open_student_record(self, student_id):
        # Get reference to student search results frame
        student_search_frame = self.window.screens['Students'].search_results_frame

        # Populate student's first/last name into the search fields and perform search
        student_info = self.database.student.loc[self.database.student['STUDENT_ID'] == student_id].squeeze()
        student_search_frame.entry_boxes['First Name'].cget('textvariable').set(student_info['FNAME'])
        student_search_frame.entry_boxes['Last Name'].cget('textvariable').set(student_info['LNAME'])
        student_search_frame.search_button.invoke()

        # Change view to StudentInfoFrame
        self.window.change_view(new_screen='Students')

    # Create pop-up window for moving student from currently selected class to another.
    # In this window the user will select the student they wish to move, and which class to move them to.
    def create_move_student_dialog(self):
        # Populate list of 'student_labels' by going through every spot in the roll
        # and only adding the labels which contain a student name
        student_labels = []
        for label in self.roll_labels.values():
            text = label.cget('text')
            # If label is completely blank, continue
            if len(text) == 0:
                continue
            # Otherwise, check if there is a name in this label
            elif text.split('.')[1].strip():
                student_labels.append(label)

        move_window = MoveStudentDialog(self.window,
                                        title='Move Student',
                                        database=self.database,
                                        current_class_id=self.id,
                                        student_labels=student_labels)
        # Wait for the move student dialog window to be closed
        self.wait_window(move_window)
        # Update search results to reflect new class availability
        self.search_results_frame.update_labels(select_first_result=False)
        # Update currently selected StudentInfoFrame (if a student is active)
        student_id = self.window.screens['Students'].id
        if student_id is not None:
            self.window.screens['Students'].update_labels(student_id)
        # Update the displayed class roll
        self.update_labels(self.id)
    
 
