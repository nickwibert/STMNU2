import customtkinter as ctk
import pandas as pd
from tktooltip import ToolTip
import calendar
from datetime import datetime
import functions as fn
from widgets.search_results_frame import SearchResultsFrame
from widgets.dialog_boxes import MoveStudentDialog

# Global values
from globals import CURRENT_SESSION, MAX_CLASS_SIZE, MAX_WAIT_SIZE, MAX_TRIAL_SIZE, MAX_MAKEUP_SIZE

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
        # Dictionary for switches
        self.switches = {}
        # List of tooltips (messages that display on hover)
        self.tooltips = []
        # List of scrollable frames (excluding search results)
        self.scroll_frames = []

        # Configure rows/columns
        self.columnconfigure((0,1,2), weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure((1,2,3), weight=3)

        # Containers for various information
        self.header_frame = ctk.CTkFrame(self)
        self.roll_frame = ctk.CTkFrame(self, border_width=5, border_color='midnightblue')
        self.wait_frame = ctk.CTkFrame(self, border_width=5, border_color='red4')
        self.wait_frame.columnconfigure(0,weight=1)
        self.wait_scroll = ctk.CTkScrollableFrame(self.wait_frame,height=100)
        self.trial_frame = ctk.CTkFrame(self, border_width=5, border_color='darkolivegreen')
        self.trial_frame.columnconfigure(0,weight=1)
        self.trial_scroll = ctk.CTkScrollableFrame(self.trial_frame,height=100)
        self.makeup_frame = ctk.CTkFrame(self, border_width=5, border_color='purple')
        self.makeup_frame.columnconfigure(0,weight=1)
        self.makeup_scroll = ctk.CTkScrollableFrame(self.makeup_frame,height=100)
        self.note_frame = ctk.CTkFrame(self, border_width=5, border_color='goldenrod')
        
        # Handle bug in customtkinter: manually override scrollbar height of CTkScrollableFrame
        self.scroll_frames.append(self.wait_scroll)
        self.scroll_frames.append(self.trial_scroll)
        self.scroll_frames.append(self.makeup_scroll)
        for scroll_frame in self.scroll_frames:
            scroll_frame._scrollbar.configure(height=0)

        ### SWITCHES ###
        age_switch = ctk.CTkSwitch(self.roll_frame,
                                    text='Show/Hide Age',
                                    command=lambda : self.update_labels(self.id),
                                    variable=ctk.StringVar(value='hide'),
                                    onvalue='show',offvalue='hide')
        self.switches['AGE'] = age_switch

        # Create labels for frames created above
        self.create_labels()
        # Blink text
        self.blink_text()
        # Add frames to grid, leaving first column (column 0) open for search results
        self.header_frame.grid(row=0, column=1, rowspan=1, sticky='nsew')

        self.roll_frame.grid_propagate(False)
        self.roll_frame.grid(row=1, column=1, rowspan=3, sticky='nsew')

        self.wait_frame.grid(row=0, column=2, sticky='nsew')
        self.wait_scroll.grid(row=self.wait_frame.grid_size()[1], column=0, sticky='nsew', padx=5)
        self.wait_frame.rowconfigure(self.wait_scroll.grid_info().get('row'), weight=3)

        self.trial_frame.grid(row=1, column=2, sticky='nsew')
        self.trial_scroll.grid(row=self.trial_frame.grid_size()[1], column=0, sticky='nsew', padx=5)
        self.trial_frame.rowconfigure(self.trial_scroll.grid_info().get('row'), weight=3)

        self.makeup_frame.grid(row=2, column=2, sticky='nsew')
        self.makeup_scroll.grid(row=self.makeup_frame.grid_size()[1], column=0, sticky='nsew', padx=5)
        self.makeup_frame.rowconfigure(self.makeup_scroll.grid_info().get('row'), weight=3)

        self.note_frame.grid(row=3, column=2, sticky='nsew')

        # Create and add search results frame to grid
        self.search_results_frame = SearchResultsFrame(self, type='class', max_row=100)
        self.search_results_frame.grid(row=0, column=0, rowspan=4, sticky='nsew')

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
        self.buttons['MOVE_STUDENT'].grid(row=MAX_CLASS_SIZE+1, column=0, padx=(5,0), pady=(0,5))
        age_switch.grid(row=MAX_CLASS_SIZE+1, column=1, columnspan=2, pady=(0,5), padx=(0,5))

        # Frame to hold waitlist buttons
        wait_buttons_frame = ctk.CTkFrame(self.wait_frame, fg_color=self.wait_frame.cget('border_color'), corner_radius=0)
        wait_buttons_frame.columnconfigure((0,1,2), weight=1)
        wait_buttons_frame.grid(row=self.wait_frame.grid_size()[1], column=0, sticky='nsew', )
        self.wait_frame.rowconfigure(wait_buttons_frame.grid_info().get('row'), weight=1)
        # Button to edit waitlist
        self.buttons['EDIT_CLASS_WAIT'] = ctk.CTkButton(wait_buttons_frame,
                                                  width=100,
                                                  text="Edit",
                                                  command = lambda frame=self.wait_frame, labels=self.wait_labels, type='CLASS_WAIT':
                                                               fn.edit_info(frame, labels, type))
        self.buttons['EDIT_CLASS_WAIT'].grid(row=0, column=0, pady=10)

        self.buttons['ADD_WAIT'] = ctk.CTkButton(wait_buttons_frame,
                                                  width=100,
                                                  text='Create',
                                                  command=self.add_wait)
        self.buttons['ADD_WAIT'].grid(row=0,column=1)

        self.buttons['CLASS_REMOVE_WAIT'] = ctk.CTkButton(wait_buttons_frame,
                                                  text='Remove',
                                                  width=100,
                                                  command = lambda frame=self.wait_frame, labels=self.wait_labels, type='CLASS_REMOVE_WAIT':
                                                      fn.edit_info(frame, labels, type))
        self.buttons['CLASS_REMOVE_WAIT'].grid(row=0,column=2)

        # Frame/buttons to add/remove trials
        trial_buttons_frame = ctk.CTkFrame(self.trial_frame, fg_color=self.trial_frame.cget('border_color'), corner_radius=0)
        trial_buttons_frame.columnconfigure((0,1,2), weight=1)
        trial_buttons_frame.grid(row=self.trial_frame.grid_size()[1], column=0, sticky='nsew',)
        self.trial_frame.rowconfigure(trial_buttons_frame.grid_info().get('row'), weight=1)
        # Button to edit trials
        self.buttons['EDIT_CLASS_TRIAL'] = ctk.CTkButton(trial_buttons_frame,
                                                  width=100,
                                                  text="Edit",
                                                  command = lambda frame=self.trial_frame, labels=self.trial_labels, type='CLASS_TRIAL':
                                                               fn.edit_info(frame, labels, type))
        self.buttons['EDIT_CLASS_TRIAL'].grid(row=0, column=0, pady=10)

        self.buttons['CLASS_ADD_TRIAL'] = ctk.CTkButton(trial_buttons_frame,
                                                  width=100,
                                                  text='Create',
                                                  command=self.add_trial)
        self.buttons['CLASS_ADD_TRIAL'].grid(row=0,column=1)

        self.buttons['CLASS_REMOVE_TRIAL'] = ctk.CTkButton(trial_buttons_frame,
                                                  text='Remove',
                                                  width=100,
                                                  command = lambda frame=self.trial_frame, labels=self.trial_labels, type='CLASS_REMOVE_TRIAL':
                                                      fn.edit_info(frame, labels, type))
        self.buttons['CLASS_REMOVE_TRIAL'].grid(row=0,column=2)

        # Frame to hold makeup buttons
        makeup_buttons_frame = ctk.CTkFrame(self.makeup_frame, fg_color=self.makeup_frame.cget('border_color'), corner_radius=0)
        makeup_buttons_frame.columnconfigure((0,1,2), weight=1)
        makeup_buttons_frame.grid(row=self.makeup_frame.grid_size()[1], column=0, sticky='nsew',)
        self.makeup_frame.rowconfigure(makeup_buttons_frame.grid_info().get('row'), weight=1)
        # Button to edit makeups
        self.buttons['EDIT_CLASS_MAKEUP'] = ctk.CTkButton(makeup_buttons_frame,
                                                  width=100,
                                                  text="Edit",
                                                  command = lambda frame=self.makeup_frame, labels=self.makeup_labels, type='CLASS_MAKEUP':
                                                               fn.edit_info(frame, labels, type))
        self.buttons['EDIT_CLASS_MAKEUP'].grid(row=0, column=0, pady=10)

        self.buttons['CLASS_ADD_MAKEUP'] = ctk.CTkButton(makeup_buttons_frame,
                                                  width=100,
                                                  text='Create',
                                                  command=self.add_makeup)
        self.buttons['CLASS_ADD_MAKEUP'].grid(row=0,column=1)

        self.buttons['CLASS_REMOVE_MAKEUP'] = ctk.CTkButton(makeup_buttons_frame,
                                                  width=100,
                                                  text='Remove',
                                                  command = lambda frame=self.makeup_frame, labels=self.makeup_labels, type='CLASS_REMOVE_MAKEUP':
                                                      fn.edit_info(frame, labels, type))
        self.buttons['CLASS_REMOVE_MAKEUP'].grid(row=0,column=2)


        # Button to edit notes
        self.buttons['EDIT_CLASS_NOTE'] = ctk.CTkButton(self.note_frame,
                                                  text="Edit Notes",
                                                  command = lambda frame=self.note_frame, labels=self.note_textbox, type='CLASS_NOTE':
                                                               fn.edit_info(frame, labels, type))
        self.buttons['EDIT_CLASS_NOTE'].grid(row=self.note_frame.grid_size()[1], column=0, pady=10)

        # Final update of the labels using the first class selected on startup
        self.update_labels(self.id)


    def create_labels(self):
        title_font = ctk.CTkFont('Segoe UI', 20, 'bold')
        instructor_font = ctk.CTkFont('Segoe UI', 28, 'bold')
        ### Class Header Frame ###
        self.header_frame.columnconfigure(0, weight=1)
        # Current session only needs to be created once when the program starts up; store separately
        session_label = ctk.CTkLabel(self.header_frame, width=300, wraplength=300, font=title_font, fg_color='black', text_color='white',
                                          text=f'Current Session: {calendar.month_name[CURRENT_SESSION.month]} {CURRENT_SESSION.year}')
        session_label.grid(row=self.header_frame.grid_size()[1], column=0, sticky='nsew', pady=(0,5))
        # # 'Selected Class' header
        # class_header = ctk.CTkLabel(self.header_frame, width=300, wraplength=300, anchor='w', justify='left', font=title_font,
        #                             text='Selected Class:')
        # class_header.grid(row=self.header_frame.grid_size()[1], column=0, sticky='nsew')

        self.header_labels = {}
        for header in ['TEACH', 'CLASSTIME', 'CLASSNAME']:
            # Create label and add to grid
            label = ctk.CTkLabel(self.header_frame, text='', width=300,
                                 font=instructor_font if header=='TEACH' else title_font,
                                 wraplength=400, anchor='w', justify='left')
            label.grid(row=self.header_frame.grid_size()[1], column=0, sticky='nsew')
            # Store header label
            self.header_labels[header] = label



        ### Class Roll Frame ###
        self.roll_frame.columnconfigure((0,1),weight=1)
        self.roll_labels = {}
        self.bill_labels = {}
        self.age_labels = {}
        roll_title = ctk.CTkLabel(self.roll_frame, fg_color=self.roll_frame.cget('border_color'),
                                   text='Class Roll', font=title_font, text_color='white')
        roll_title.grid(row=self.roll_frame.grid_size()[1], column=0, columnspan=3, sticky='nsew')
        # Create placeholder labels based on global variable for max class size
        for row in range(1,MAX_CLASS_SIZE+1):
            # Student name
            name_label = ctk.CTkLabel(self.roll_frame, width=250, anchor='w',
                                      font=ctk.CTkFont('Arial',18,'normal'),
                                      bg_color='gray70' if row % 2 == 0 else 'gray80',
                                      cursor='hand2')
            name_label.grid(row=self.roll_frame.grid_size()[1], column=0, sticky='nsew', padx=(5,0))
            # Placeholder attribute for student ID and blinking
            name_label.student_id = -1
            name_label.blink = False
            # Store labels using field names from DBF
            self.roll_labels[f'STUDENT{row}'] = name_label

            # Label that will contain the student's age
            age_label = ctk.CTkLabel(self.roll_frame, width=50, justify='right',
                                      font=ctk.CTkFont('Arial',16,'normal'),
                                      bg_color='gray70' if row % 2 == 0 else 'gray80',
                                      cursor='hand2')
            age_label.grid(row=name_label.grid_info().get('row'), column=1, sticky='nsew', ipadx=5)
            self.age_labels[f'STUDENT{row}'] = age_label

            # Label that will contain $ symbols to indicate # of payments owed
            bill_label = ctk.CTkLabel(self.roll_frame, width=100, anchor='w',
                                      font=ctk.CTkFont('Arial',18,'bold'),
                                      text_color='red',
                                      bg_color='gray70' if row % 2 == 0 else 'gray80',
                                      cursor='hand2')
            bill_label.grid(row=name_label.grid_info().get('row'), column=2, sticky='nsew', padx=(0,5))
            self.bill_labels[f'STUDENT{row}'] = bill_label

        
        ### Waitlist Frame ###
        self.wait_scroll.columnconfigure(0, weight=1)
        self.wait_labels = {}
        wait_title = ctk.CTkLabel(self.wait_frame, fg_color=self.wait_frame.cget('border_color'),
                                   text='Waitlist', font=title_font, text_color='white')
        wait_title.grid(row=self.wait_frame.grid_size()[1], column=0, sticky='nsew')
        # Create placeholder labels based on global variable for max waitlist size
        for row in range(1,MAX_WAIT_SIZE+1):
            row_frame = ctk.CTkFrame(self.wait_scroll,)
            row_frame.columnconfigure((0,1), weight=1)
            row_frame.grid(row=self.wait_scroll.grid_size()[1], column=0, sticky='nsew')
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
        self.trial_scroll.columnconfigure(0,weight=1)
        self.trial_labels = {}
        trial_title = ctk.CTkLabel(self.trial_frame, fg_color=self.trial_frame.cget('border_color'),
                                   text='Trials', font=title_font, text_color='white')
        trial_title.grid(row=self.trial_frame.grid_size()[1], column=0, sticky='nsew')
        # Create placeholder labels based on global variable for max trial size
        for row in range(1,MAX_TRIAL_SIZE+1):
            row_frame = ctk.CTkFrame(self.trial_scroll,)
            row_frame.columnconfigure((0,1), weight=1)
            row_frame.grid(row=self.trial_scroll.grid_size()[1], column=0, sticky='nsew')
            # Trial name
            name_label = ctk.CTkLabel(row_frame, width=250, wraplength=250, text=f'{row}. ', anchor='w')
            name_label.grid(row=0, column=0, pady=(5,0), sticky='nsew')
            # Trial phone number
            phone_label = ctk.CTkLabel(row_frame, width=100, wraplength=100, text='', anchor='w')
            phone_label.grid(row=0, column=1, sticky='nsew')
            # Trial date
            date_label = ctk.CTkLabel(row_frame, width=100, wraplength=100, text='', anchor='w')
            date_label.grid(row=0, column=2, sticky='nsew')
            # Store labels using field names from DBF
            self.trial_labels[f'TRIAL{row}']  = name_label
            self.trial_labels[f'T{row}PHONE'] = phone_label
            self.trial_labels[f'T{row}DATE']  = date_label


        ### Makeup Frame ###
        self.makeup_scroll.columnconfigure(0,weight=1)
        self.makeup_labels = {}
        makeup_title = ctk.CTkLabel(self.makeup_frame, fg_color=self.makeup_frame.cget('border_color'),
                                   text='Makeups', font=title_font, text_color='white')
        makeup_title.grid(row=self.makeup_frame.grid_size()[1], column=0, columnspan=1, sticky='nsew')
        # Create placeholder labels based on global variable for max makeup size
        for row in range(1,MAX_MAKEUP_SIZE+1):
            row_frame = ctk.CTkFrame(self.makeup_scroll,)
            row_frame.columnconfigure((0,1), weight=1)
            row_frame.grid(row=self.makeup_scroll.grid_size()[1], column=0, sticky='nsew')
            # Makeup name
            name_label = ctk.CTkLabel(row_frame, width=300, text='', anchor='w')
            name_label.grid(row=0, column=0, pady=(5,0), sticky='nsew')
            # Makeup date
            date_label = ctk.CTkLabel(row_frame, width=100, wraplength=100, text='', anchor='w')
            date_label.grid(row=0, column=1, sticky='nsew')
            # Store labels using field names from DBF 
            self.makeup_labels[f'MAKEUP{row}'] = name_label
            self.makeup_labels[f'M{row}DATE'] = date_label

        ### Notes Frame ###
        # This is handled differently than the other frames, as there is one note field per class.
        # This has no limit on length, so we want a scrollable textbox rather than a label.
        self.note_frame.columnconfigure(0, weight=1)
        note_title = ctk.CTkLabel(self.note_frame, fg_color=self.note_frame.cget('border_color'),
                                   text='Notes', font=title_font, text_color='white')
        note_title.grid(row=self.note_frame.grid_size()[1], column=0, sticky='nsew')

        self.note_textbox = ctk.CTkTextbox(self.note_frame, height=200, width=400, wrap='word',
                                           font=ctk.CTkFont('Britannic',24), fg_color=self.note_frame.cget('fg_color'))
        self.note_textbox.grid(row=self.note_frame.grid_size()[1],column=0,sticky='nsew',padx=10)
        # Set to 'disabled' so the displayed text cannot be edited
        self.note_textbox.configure(state='disabled')


    def reset_labels(self):
        for label in self.header_labels.values():
            label.configure(text='')

        # Wipe all roll labels and remove from grid
        for label in self.roll_labels.values():
            label.configure(text='', text_color='black')
            label.student_id = -1
            for binding in ['<Button-1>', '<Enter>', '<Leave>']:
                label.unbind(binding)
            # Reset blinking
            label.blink = False
            # Hide entire row from view
            label.lower()
            
        for label in self.bill_labels.values():
            for binding in ['<Button-1>', '<Enter>', '<Leave>']:
                label.unbind(binding)
            label.configure(text='')
            label.lower()

        for label in self.age_labels.values():
            for binding in ['<Button-1>', '<Enter>', '<Leave>']:
                label.unbind(binding)
            label.configure(text='')
            label.lower()

        for tooltip in self.tooltips:
            tooltip.destroy()

        # Remove wait/trial labels from grid but keep widget in memory (along with its location)
        for label in (self.wait_labels | self.trial_labels | self.makeup_labels).values():
            label.configure(text='', fg_color='transparent')
            label.master.grid_remove()

        # Delete text displayed in note textbox
        self.note_textbox.configure(state='normal')
        self.note_textbox.delete('1.0', ctk.END)
        self.note_textbox.configure(state='disabled')


    def update_labels(self, class_id):
        # Wipe labels
        self.reset_labels()
        # SPECIAL CASE: If student_id == -1, exit function
        if class_id == -1:
            # Exit function
            return

        # Currently selected class
        self.id = class_id

        # header_info = self.database.classes[self.database.classes['CLASS_ID'] == class_id].squeeze()
        header_info = pd.read_sql(f"SELECT * FROM classes WHERE CLASS_ID={class_id}", self.database.conn
                       ).squeeze()

        # roll_info = self.database.class_student[(self.database.class_student['CLASS_ID'] == class_id)
        #                     ].merge(self.database.student[self.database.student['ACTIVE']],
        #                             how='inner',
        #                             on='STUDENT_ID'
        #                     ).merge(self.database.payment[((self.database.payment['MONTH'] == CURRENT_SESSION.month)
        #                                                   & (self.database.payment['YEAR'] == CURRENT_SESSION.year))],
        #                             how='left',
        #                             on='STUDENT_ID'
        #                     ).loc[:,['PAY','STUDENT_ID','FAMILY_ID','FNAME','LNAME','BIRTHDAY']]
        # # Create 'PAID' which is true if student has a non-zero payment for the current month/year
        # roll_info['PAID'] = roll_info['PAY'] > 0

        roll_info = pd.read_sql(f"""-- Keep only the active students who are either paid or billed
                                    SELECT ACTIVE_STUDENTS.STUDENT_ID, FNAME, LNAME, BIRTHDAY,
                                        IIF(P.STUDENT_ID IS NULL, 0, 1) AS PAID,
                                        IIF(B.STUDENT_ID IS NULL, 0, 1) AS BILLED
                                    FROM (
                                        -- Get all (active) student IDs linked to this class ID
                                        SELECT CS.CLASS_ID, S.STUDENT_ID, S.FNAME, S.LNAME, S.BIRTHDAY
                                        FROM class_student AS CS
                                            INNER JOIN student AS S ON CS.STUDENT_ID = S.STUDENT_ID
                                        WHERE S.ACTIVE AND CLASS_ID = {class_id}
                                    ) AS ACTIVE_STUDENTS
                                        LEFT JOIN payment AS P ON ACTIVE_STUDENTS.STUDENT_ID = P.STUDENT_ID
                                                                AND P.MONTH=3 AND P.YEAR=2025
                                        LEFT JOIN bill AS B ON ACTIVE_STUDENTS.STUDENT_ID = B.STUDENT_ID
                                                                AND B.MONTH=3 AND B.YEAR=2025
                                    WHERE PAID OR BILLED
                                    ORDER BY PAID DESC, LNAME ASC""",
                                self.database.conn)
        
        # Get `bill_info` as all the bill records for students in `roll_info`
        # bill_info = self.database.bill.merge(roll_info, how='inner', on='STUDENT_ID'
        #                              ).loc[:,['STUDENT_ID','MONTH','YEAR']]
        bill_info = pd.read_sql(f"""SELECT STUDENT_ID, MONTH, YEAR
                                    FROM bill
                                    WHERE STUDENT_ID IN ({','.join(str(id) for id in roll_info['STUDENT_ID'])})""",
                                self.database.conn)
        
        # wait_info = self.database.wait[self.database.wait['CLASS_ID'] == class_id
        #                     ].reset_index(drop=True
        #                     ).fillna('')
        wait_info = pd.read_sql(f"""SELECT WAIT_ID, CLASS_ID, WAIT_NO, NAME, PHONE
                                    FROM wait
                                    WHERE CLASS_ID={class_id}""",
                                self.database.conn)
        
        # trial_info = self.database.trial[self.database.trial['CLASS_ID'] == class_id
        #                     ].reset_index(drop=True
        #                     ).fillna('')
        trial_info = pd.read_sql(f"""SELECT TRIAL_ID, CLASS_ID, TRIAL_NO, NAME, PHONE, DATE
                                     FROM trial
                                     WHERE CLASS_ID={class_id}""",
                                self.database.conn)
        
        makeup_info = self.database.makeup[self.database.makeup['CLASS_ID'] == class_id
                            ].reset_index(drop=True
                            ).fillna('')
        
        # This will either be empty, or contain exactly one note
        # note_info = self.database.note[self.database.note['CLASS_ID'] == class_id].squeeze()
        note_info = pd.read_sql(f"""SELECT NOTE_ID, CLASS_ID, NOTE_TXT
                                    FROM note
                                    WHERE CLASS_ID = {class_id}""",
                                self.database.conn
                     ).squeeze()

        # Before populating labels, enable/disable certain buttons based on spots available
        for button_name, button in self.buttons.items():
            if 'WAIT' in button_name:
                info = wait_info
                max_size = MAX_WAIT_SIZE
            elif 'TRIAL' in button_name:
                info = trial_info
                max_size = MAX_TRIAL_SIZE
            elif 'MAKEUP' in button_name:
                info = makeup_info
                max_size = MAX_MAKEUP_SIZE
            # Leave button alone if it doesn't deal with waitlist, trials, or makeups
            else:
                continue
            # If record list is empty, only enable 'add' button
            if info.empty:
                if 'ADD' in button_name:
                    button.configure(state='normal', fg_color='steelblue3')
                else:
                    button.configure(state='disabled', fg_color='grey')
            # If record list is full, disable 'add' button
            elif info.shape[0] == max_size:
                if 'ADD' in button_name:
                    button.configure(state='disabled', fg_color='grey')
                else:
                    button.configure(state='normal', fg_color='steelblue3')
            # Otherwise, all buttons enabled
            else:
                button.configure(state='normal', fg_color='steelblue3')

        ### Class Header Frame ###
        for field in self.header_labels.keys():
            label = self.header_labels[field]
            label.configure(text=header_info[field])

        ### Class Roll Frame ###
        # Get max class size from `classes`
        max_class_size = header_info['MAX']
        # Get current class size as the number of students who have paid/been billed for the current month
        actual_class_size = roll_info.loc[(roll_info['PAID'] | roll_info['BILLED'])].shape[0]
        # Get 'potential' class size as the number of students who are listed as part of this class, regardless of payment
        potential_class_size = roll_info.shape[0]

        # Populate roll labels
        for row in range(1,MAX_CLASS_SIZE+1):
            label = self.roll_labels[f'STUDENT{row}']
            age_label = self.age_labels[f'STUDENT{row}']
            bill_label = self.bill_labels[f'STUDENT{row}']
            # Update roll label if we have not reached potential_class_size or max_class_size
            # (whichever is larger)
            if row <= max(potential_class_size, max_class_size):
                # Lift row back into view
                label.lift()
                age_label.lift()
                bill_label.lift()
                # Create variable to store student name (if exists)
                roll_txt = f"{row}. "
                bill_txt = ''
                age_txt = ''
                # If student exists for this row, add their name
                if row <= potential_class_size:
                    # Student name
                    roll_txt += f"{roll_info.loc[row-1,'FNAME'].title()} {roll_info.loc[row-1,'LNAME'].title()}"
                    # Store student ID as attribute as well (this will be necessary for moving students between classes)
                    label.student_id = roll_info.loc[row-1, 'STUDENT_ID']
                    # If this is a 'potential' student, their name should be blinking
                    # (all rows up to `actual_class_size` are students who are paid for current month)
                    label.blink = row > actual_class_size

                    # Determine age of student and add to label
                    if self.switches['AGE'].get() == 'show':
                        birthday = roll_info.loc[row-1,'BIRTHDAY']
                        if pd.isna(birthday) or len(birthday)==0:
                            age_txt += 'N/A'
                        else:
                            today = datetime.today()
                            birthday = datetime.strptime(birthday, "%m/%d/%Y")
                            age_txt += str(today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day)))
                            age_txt += ' yrs'

                    # Add dollar signs ($) after the student's bill label if they owe for previous months
                    # (i.e. if a student has 3 asterisks under 'BILL', 3 dollar signs should display here)
                    if label.student_id in bill_info['STUDENT_ID'].values:
                        student_bills = bill_info.loc[bill_info['STUDENT_ID']==label.student_id]
                        bill_count = student_bills.loc[student_bills['MONTH']!=13].shape[0]
                        regfee_count = student_bills.loc[student_bills['MONTH']==13].shape[0]
                        bill_txt += '$'*bill_count + 'R'*regfee_count
                        tooltip_txt = 'Payments owed:'
                        # Create tooltip showing which payments are owed
                        for bill_idx in range(student_bills.shape[0]):
                            bill = student_bills.iloc[bill_idx].squeeze()
                            month = 'Reg Fee' if bill['MONTH']==13 else calendar.month_abbr[bill['MONTH']]
                            tooltip_txt += f'\n{month} {bill['YEAR']}'

                        self.tooltips.append(ToolTip(bill_label, msg=tooltip_txt, font=ctk.CTkFont('Segoe UI',16)))

                    # Bind functions to both label and bill label
                    for lab in [label, bill_label, age_label]:
                        # Highlight label when mouse hovers over it
                        lab.bind("<Enter>",    lambda event, c=lab.master, r=lab.grid_info().get('row'):
                                                        fn.highlight_label(c,r))
                        lab.bind("<Leave>",    lambda event, c=lab.master, r=lab.grid_info().get('row'):
                                                        fn.unhighlight_label(c,r))
                        # Click student name in class roll to pull up student record
                        lab.bind("<Button-1>", lambda event, student_id=label.student_id:
                                                self.open_student_record(student_id))


                # Update text in label
                label.configure(text=roll_txt)
                age_label.configure(text=age_txt)
                bill_label.configure(text=bill_txt)

        ### Waitlist Frame ###
        row_color = 'grey75'
        for row in range(MAX_WAIT_SIZE):
            wait_name_label = self.wait_labels[f'WAIT{row+1}']
            wait_name_txt=''
            wait_phone_label = self.wait_labels[f'W{row+1}PHONE']
            wait_phone_txt=''
            wait_record = wait_info.loc[wait_info['WAIT_NO']==row+1].squeeze()
            row_frame = wait_name_label.master

            if not wait_record.empty:
                row_frame.configure(fg_color=row_color)
                row_frame.grid()
                row_color = 'grey65' if row_color=='grey75' else 'grey75'
                wait_name_txt += wait_record['NAME']
                wait_phone_txt += str(wait_record['PHONE'])

            # Update wait labels
            wait_name_label.configure(text=wait_name_txt)
            wait_phone_label.configure(text=wait_phone_txt)


        ### Trial Frame ###
        row_color = 'grey75'
        for row in range(MAX_TRIAL_SIZE):
            trial_name_label = self.trial_labels[f'TRIAL{row+1}']
            trial_name_txt = ''
            trial_phone_label = self.trial_labels[f'T{row+1}PHONE']
            trial_phone_txt = ''
            trial_date_label = self.trial_labels[f'T{row+1}DATE']
            trial_date_txt = ''
            trial_date_label.cget('font').configure(weight='normal')
            trial_date_label.configure(text_color='black')
            trial_record = trial_info.loc[trial_info['TRIAL_NO'] == row+1].squeeze()
            row_frame = trial_name_label.master

            if not trial_record.empty:
                row_frame.configure(fg_color=row_color)
                row_frame.grid()
                row_color = 'grey65' if row_color=='grey75' else 'grey75'
                trial_name_label.master.grid()

                trial_name_txt += trial_record['NAME']
                trial_phone_txt += str(trial_record['PHONE'])
                trial_date_txt += str(trial_record['DATE'])
                # Flag date with red bg if date is either blank or in the past
                if pd.isna(pd.to_datetime(trial_date_txt)) or (pd.to_datetime(trial_date_txt).date() < datetime.today().date()):
                    trial_date_label.cget('font').configure(weight='bold')
                    trial_date_label.configure(text_color='red')

            # Update wait labels
            trial_name_label.configure(text=trial_name_txt)
            trial_phone_label.configure(text=trial_phone_txt)
            trial_date_label.configure(text=trial_date_txt)


        ### Makeup Frame ###
        row_color = 'grey75'
        for row in range(MAX_MAKEUP_SIZE):
            makeup_name_label = self.makeup_labels[f'MAKEUP{row+1}']
            makeup_name_txt=''
            makeup_date_label = self.makeup_labels[f'M{row+1}DATE']
            makeup_date_txt=''
            makeup_record = makeup_info.loc[makeup_info['MAKEUP_NO']==row+1].squeeze()
            row_frame = makeup_name_label.master

            if not makeup_record.empty:
                row_frame.configure(fg_color=row_color)
                row_frame.grid()
                row_color = 'grey65' if row_color=='grey75' else 'grey75'
                makeup_name_txt += makeup_record['NAME']
                makeup_date_txt += str(makeup_record['DATE'])

            # Update wait labels
            makeup_name_label.configure(text=makeup_name_txt)
            makeup_date_label.configure(text=makeup_date_txt)


        ### Note Frame ###
        if not note_info.empty:
            self.note_textbox.configure(state='normal')   
            self.note_textbox.insert('1.0', note_info['NOTE_TXT'])
            self.note_textbox.configure(state='disabled')   


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

        move_window = MoveStudentDialog(window=self.window,
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

            
    # Add a name to the waitlist of currently selected class
    def add_wait(self):
        # Find the first blank waitlist spot
        for row in range(1,MAX_WAIT_SIZE+1):
            wait_name_label = self.wait_labels[f'WAIT{row}']
            row_frame = wait_name_label.master
            if not row_frame.winfo_ismapped():
                self.after(100, lambda : self.wait_scroll._parent_canvas.yview_moveto(1))
                row_frame.grid()
                edit_labels = {key:label for key,label in self.wait_labels.items() if f'{row}' in key}
                fn.edit_info(edit_frame=self.wait_frame, labels=edit_labels, edit_type='CLASS_WAIT')
                self.wait_scroll._parent_canvas.yview_moveto(1)
                return

        print('Waitlist FULL')


    # Add a trial to the currently selected class
    def add_trial(self):
        # Find the first blank trial spot
        for row in range(1,MAX_TRIAL_SIZE+1):
            trial_name_label = self.trial_labels[f'TRIAL{row}']
            row_frame = trial_name_label.master
            if not row_frame.winfo_ismapped():
                self.after(100, lambda : self.trial_scroll._parent_canvas.yview_moveto(1))
                row_frame.grid()
                edit_labels = {key:label for key,label in self.trial_labels.items() if f'{row}' in key}
                fn.edit_info(edit_frame=self.trial_frame, labels=edit_labels, edit_type='CLASS_TRIAL')
                self.trial_scroll._parent_canvas.yview_moveto(1)
                return
            
        print('Trials FULL')


    # Add a makeup to the currently selected class
    def add_makeup(self):
        # Find the first blank makeup spot
        for row in range(1,MAX_MAKEUP_SIZE+1):
            name_label = self.makeup_labels[f'MAKEUP{row}']
            row_frame = name_label.master
            if not row_frame.winfo_ismapped():
                self.after(100, lambda : self.makeup_scroll._parent_canvas.yview_moveto(1))
                row_frame.grid()
                edit_labels = {key:label for key,label in self.makeup_labels.items() if f'{row}' in key}
                fn.edit_info(edit_frame=self.makeup_frame, labels=edit_labels, edit_type='CLASS_MAKEUP')
                self.makeup_scroll._parent_canvas.yview_moveto(1)
                return
            
        print('Makeups FULL')

 
    def reset_scroll_frames(self):
        for scroll_frame in self.scroll_frames:
            scroll_frame._parent_canvas.yview_moveto(0)