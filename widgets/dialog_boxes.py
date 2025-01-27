# Custom dialog boxes created by slightly modifying source code for 'CTkInputDialog'.
# I needed the text in the entry box to be hidden and could not modify the EntryBox
# within CTkInputDialog object, so needed to create a custom version.

# Packages
import customtkinter as ctk
import calendar
from datetime import datetime

### Pop-Up Window ###
# Parent class with general attributes that will apply to all dialog boxes in the program
class DialogBox(ctk.CTkToplevel):
    def __init__(self, window, title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title = title
        self.title(self._title)

        self.window=window

        self.lift()  # lift window on top
        self.attributes("-topmost", True)  # stay on top

        self.after(10, self._create_widgets)  # create widgets with slight delay, to avoid white flickering of background
        self.resizable(False, False)
        self.grab_set()  # make other windows not clickable        


### Password Dialog Box ###
# This pop-up window is used when the user tries to modify student payment records.
# The user must first enter the correct password in order to make edits.
class PasswordDialog(DialogBox):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = text
        self.protocol("WM_DELETE_WINDOW", self._ok_event)

        # Set location of window relative to the main window
        window_x, window_y = (self.window.winfo_x(), self.window.winfo_y())
        x, y = (window_x + (self.window.winfo_width()*0.66), window_y + (self.window.winfo_height()*0.1))
        self.geometry(f'+{round(x)}+{round(y)}')

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._label = ctk.CTkLabel(master=self,
                               width=230,
                               wraplength=150,
                               fg_color="transparent",
                               text=self._text)
        self._label.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self._entry = ctk.CTkEntry(master=self,
                                   show='*',
                                   width=100)
        self._entry.grid(row=1, column=0, padx=20, pady=(0, 20))

        self._ok_button = ctk.CTkButton(master=self,
                                    width=100,
                                    border_width=0,
                                    text='Enter',
                                    command=self._ok_event)
        self._ok_button.grid(row=2, column=0, padx=(20, 10), pady=(0, 20))

        self.after(150, lambda: self._entry.focus())  # set focus to entry with slight delay, otherwise it won't work
        self._entry.bind("<Return>", self._ok_event)

    def _ok_event(self, event=None):
        self._user_input = self._entry.get()
        self.grab_release()
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self._user_input


### Move Student Dialog ###
# This pop-up window is used when the user attempts to move a student from one class to another.
# (Or, to move a student into a class for the first time, when `new_enrollment`=True)
# The user selects options from various dropdown menus which are populated using only valid values.
# Therefore it is not possible for the user to make an invalid selection in this window.
class MoveStudentDialog(DialogBox):
    def __init__(self, database, current_class_id, student_labels, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database = database
        self.current_class_id = current_class_id
        self.student_labels = student_labels
        self.new_enrollment = True if 'Enroll' in self._title else False

        # Set location of window relative to the main window
        self.geometry('500x250')
        window_x, window_y = (self.window.winfo_x(), self.window.winfo_y())
        x, y = (window_x + ((self.window.winfo_width() - self.winfo_reqwidth())// 2), window_y + ((self.window.winfo_height() - self.winfo_reqheight()) // 2))
        self.geometry(f'+{round(x)}+{round(y)}')

    def _create_widgets(self):
        self.columnconfigure((0,1), weight=1)
        self.rowconfigure(0, weight=1)

        student_label = ctk.CTkLabel(self, text='Which student would you like to move?')
        student_label.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.student_dropdown = ctk.CTkOptionMenu(self, values=[label.cget('text') for label in self.student_labels], width=150)
        self.student_dropdown.grid(row=1, column=0, columnspan=2)

        # If `new_enrollment` == True, we are looking at a specific student's record and attempting to move them into a class.
        # Therefore, lock the `student_dropdown` on this student's name so it cannot be changed.
        if self.new_enrollment:
            self.student_dropdown.configure(state='disabled')

        self.time_dropdown = ctk.CTkOptionMenu(self, command=lambda _: self.update_time_dropdown(-1))
        self.day_dropdown = ctk.CTkOptionMenu(self, command=self.update_time_dropdown)

        instructor_names = self.database.classes['TEACH'].drop_duplicates().sort_values().str.title()
        self.instructor_dropdown = ctk.CTkOptionMenu(self, values=instructor_names, width=150,
                                                command=self.update_day_dropdown)
        instructor_label = ctk.CTkLabel(self, text='Select instructor:')
        instructor_label.grid(row=2, column=0, columnspan=2, sticky='nsew')
        self.instructor_dropdown.grid(row=3, column=0, columnspan=2)
        day_time_label = ctk.CTkLabel(self, wraplength=200,
                                      text="Select day/time from available options for instructor above:")
        day_time_label.grid(row=4, column=0, columnspan=2, sticky='nsew')
        self.day_dropdown.grid(row=5, column=0, sticky='nse')
        self.time_dropdown.grid(row=5, column=1, sticky='nsw')

        # Placeholder label for warning
        self.warning_label = ctk.CTkLabel(self, wraplength=200, text_color='red')
        self.warning_label.grid(row=6, column=0, columnspan=2)

        # Button to confirm selected options
        self.confirm_button = ctk.CTkButton(self, text='Confirm Enroll' if self.new_enrollment else 'Confirm Move',
                                            command=self.validate_move_student)
        self.confirm_button.grid(row=7, column=0, columnspan=2)

        # Populate dropdowns
        self.update_day_dropdown(self.instructor_dropdown.get())
    
    # Update available values in the 'day of week' dropdown menu
    # based on when the given instructor teaches
    def update_day_dropdown(self, instructor):
        # Find all days on which given instructor teaches
        day_indexes = self.database.classes[self.database.classes['TEACH'] == instructor.upper()
                            ].loc[:,'DAYOFWEEK'
                            ].sort_values(
                            ).drop_duplicates()
        
        days = [calendar.day_name[i-1] for i in day_indexes]
        # Update day dropdown values to only include those days when the instructor teaches
        self.day_dropdown.configure(values=days)
        # Select first option
        self.day_dropdown.set(days[0])
        # Update times
        self.update_time_dropdown(days[0])


    # Update available values in the 'time of day' dropdown menu
    # based on the currently selected intructor/day of week combination
    def update_time_dropdown(self, day):
        # Reset warning text and confirm button command
        self.warning_label.configure(text='')
        self.confirm_button.configure(command=self.validate_move_student)

        # If day == -1, don't update the time dropdown options
        if day == -1: return

        # Convert day selection to day index (Monday=1, ..., Saturday=6)
        day_idx = list(calendar.day_name).index(day) + 1
        # Get current value of instructor
        instructor = self.instructor_dropdown.get()
        # Find all possible times for given instructor and day
        times = self.database.classes[((self.database.classes['TEACH'] == instructor.upper())
                                            & (self.database.classes['DAYOFWEEK'] == day_idx))
                            ].sort_values(by='TIMEOFDAY'
                            ).loc[:,'CLASSTIME'
                            ].to_list()            
        # Update time dropdown values to only include those times when the instructor teaches on this day
        self.time_dropdown.configure(values=times)
        # Select first option
        self.time_dropdown.set(times[0])


    # Function run when user confirms their selections. If the selected class is full or over-capacity,
    # ask the user to confirm a second time that they indeed wish to perform this move.
    # (This is to mimic the old program, if Dad wishes to perform different kinds of validation
    # then this function can be modified later)
    def validate_move_student(self):
        # Get user's selected options
        student = self.student_dropdown.get()
        instructor = self.instructor_dropdown.get()
        day = self.day_dropdown.get()
        classtime = self.time_dropdown.get()

        # Convert day selection to day index (Monday=1, ..., Saturday=6)
        day_idx = list(calendar.day_name).index(day) + 1
        # Get selected student's place in the roll by stripping it from the front of the string
        student_roll_num = int(student.split('.')[0])
        # Get corresponding student label by converting roll number to list index,
        # and extract the unique student ID of the student being moved
        student_id = self.student_labels[student_roll_num-1].student_id

        # Get all information associated with the 'new' class
        class_info = self.database.classes[((self.database.classes['TEACH'] == instructor.upper())
                                          & (self.database.classes['DAYOFWEEK'] == day_idx)
                                          & (self.database.classes['CLASSTIME'] == classtime))
                                 ].squeeze()
        
        class_count = class_info['MAX'] - class_info['AVAILABLE']
        
        # If the selected class is at or above MAX_CLASS_SIZE, don't allow the user to move any more students into it
        if class_count >= 16:
            warning_txt = f'WARNING: The currently selected class already has {class_count} ' \
                          f'spots filled. Please choose a different class.'
            self.warning_label.configure(text=warning_txt)
            return
        # If class is full or over-capacity, ask user to confirm one more time
        elif class_info['AVAILABLE'] <= 0:
            warning_txt = f'WARNING: The currently selected class already has {class_count} ' \
                          f'spots filled, and a max enrollment of {class_info['MAX']} students. Are you sure you want to proceed? ' \
                           "(If so, click 'Confirm' again)"
            self.warning_label.configure(text=warning_txt)
            # Change 'confirm' button command to wait for user to click it again
            var = ctk.StringVar()
            self.confirm_button.configure(command = lambda : var.set('continue'))
            # Wait until confirm button is clicked before continuing
            self.confirm_button.wait_variable(var)

        # Call function to move student in parent frame, and destroy MoveStudentDialog window
        self.database.move_student(student_id, self.current_class_id, new_class_id=class_info['CLASS_ID'])
        self.destroy()


### New Student Dialog ###
# This pop-up window is used when the user requests to create a new student
class NewStudentDialog(DialogBox):
    def __init__(self, database, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database = database

        # Set location of window relative to the main window
        self.geometry('900x500')
        window_x, window_y = (self.window.winfo_x(), self.window.winfo_y())
        x, y = (window_x + ((self.window.winfo_width() - self.winfo_reqwidth())// 2), window_y + ((self.window.winfo_height() - self.winfo_reqheight()) // 2))
        self.geometry(f'+{round(x)}+{round(y)}')

    def _create_widgets(self):
        self.columnconfigure((0,1), weight=1)
        self.rowconfigure((0,1,2), weight=1)

        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0,column=0,columnspan=2)
        studentno = self.database.student['STUDENTNO'].max()
        enrolldate = datetime.today().strftime('%m/%d/%Y')
        self.header_label = ctk.CTkLabel(self.header_frame,
                                         text=f"Student Number: {studentno}\nEnroll Date: {enrolldate}")
        self.header_label.grid(row=0,column=0,sticky='nsew')

        ## Personal Information ##
        self.personal_frame = ctk.CTkFrame(self)
        self.personal_frame.grid(row=1,column=0,)

        field_position = {
            'FNAME'    : {'row' : 0, 'column' : 0, 'columnspan' : 1},
            'LNAME'    : {'row' : 0, 'column' : 1, 'columnspan' : 2},
            'ADDRESS'  : {'row' : 1, 'column' : 0, 'columnspan' : 3},
            'CITY'     : {'row' : 2, 'column' : 0, 'columnspan' : 1},
            'STATE'    : {'row' : 2, 'column' : 1, 'columnspan' : 1},
            'ZIP'      : {'row' : 2, 'column' : 2, 'columnspan' : 1},
            'MOMNAME'  : {'row' : 3, 'column' : 0, 'columnspan' : 3},
            'DADNAME'  : {'row' : 4, 'column' : 0, 'columnspan' : 3},
            'EMAIL'    : {'row' : 5, 'column' : 0, 'columnspan' : 3},
            'PHONE'    : {'row' : 6, 'column' : 0, 'columnspan' : 3},
            'BIRTHDAY' : {'row' : 7, 'column' : 0, 'columnspan' : 3},
        }

        self.entry_boxes = {}
        for field, kwargs in field_position.items():
            entry = ctk.CTkEntry(master=self.personal_frame, placeholder_text=field)
            entry.grid(sticky='nsew', **kwargs)
            self.entry_boxes[field] = entry


        self.class_frame = ctk.CTkFrame(self)
        self.class_frame.grid(row=2,column=0,)

        field_position = {
            'CODE'       : {'row' : 0, 'column' : 0,},
            'INSTRUCTOR' : {'row' : 1, 'column' : 0,},
            'DAYTIME'    : {'row' : 1, 'column' : 1,},
            'INST2'      : {'row' : 2, 'column' : 0,},
            'DAYTIME2'   : {'row' : 2, 'column' : 1,},
            'INST3'      : {'row' : 3, 'column' : 0,},
            'DAYTIME3'   : {'row' : 3, 'column' : 1,}
        }

        for field, kwargs in field_position.items():
            entry = ctk.CTkEntry(master=self.class_frame, placeholder_text=field)
            entry.grid(sticky='nsew', **kwargs)
            self.entry_boxes[field] = entry


        self.payment_frame = ctk.CTkFrame(self)
        self.payment_frame.grid(row=1, column=1, rowspan=2)

        

        # Values that will populate month column
        month_column = list(calendar.month_name)[1:] + ['Reg. Fee']
        # Prefixes/suffixes to store labels and also access data from STUD00.dbf (JANPAY, JANDATE, etc.)
        prefix = [month.upper() for month in calendar.month_abbr[1:]] + ['REG']
        suffix = [['HEADER','PAY','DATE'] for _ in range(13)]
        # Special row of suffixes for REGFEE (because column with pay is simply 'REGFEE' rather than 'REGFEEPAY', and 'REGBILL')
        suffix.append(['FEEHEADER', 'FEE', 'FEEDATE'])
        payment_font = ctk.CTkFont('Britannica',16,'bold')

        # 13 rows (12 months + registration fee row)
        for row in range(13):
            # Create a frame for this row
            month_frame = ctk.CTkFrame(self.payment_frame, fg_color='grey70' if row % 2 == 0 else 'transparent')
            month_frame.columnconfigure((0,1,2), weight=1)
            # Create labels for this row
            header_label = ctk.CTkLabel(month_frame, text=month_column[row],
                                        font=payment_font,
                                        anchor='w', width=75)
            pay_entry = ctk.CTkEntry(month_frame, placeholder_text='0.00', font=payment_font, width=50)
            date_entry = ctk.CTkEntry(month_frame, placeholder_text='MM/DD/YYYY', font=payment_font, width=125)
            # Put labels into grid
            header_label.grid(row=0,column=0,padx=10,sticky='nsew')
            pay_entry.grid(row=0,column=1,padx=10,sticky='nsew')
            date_entry.grid(row=0,column=2,padx=10,sticky='nsew')
            # Grid and store month frame
            month_frame.grid(row=row+2, column=0, sticky='nsew')

            self.entry_boxes[prefix[row] + suffix[row][1]] = pay_entry
            self.entry_boxes[prefix[row] + suffix[row][2]] = date_entry
