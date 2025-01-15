import customtkinter as ctk
import calendar

# Custom dialog box created by slightly modifying source code for 'CTkInputDialog'.
# I needed the text in the entry box to be hidden and could not modify the EntryBox
# within CTkInputDialog object, so needed to create a custom version.
class MoveStudentDialog(ctk.CTkToplevel):
    def __init__(self, window, title, database, current_class_id, student_labels, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title = title
        self.title(self._title)
        self.database = database
        self.current_class_id = current_class_id
        self.student_labels = student_labels

        self.lift()  # lift window on top
        self.attributes("-topmost", True)  # stay on top
        self.after(10, self._create_widgets)  # create widgets with slight delay, to avoid white flickering of background
        self.resizable(False, False)
        self.grab_set()  # make other windows not clickable

        # Set location of window relative to the main window
        self.geometry('500x250')
        window_x, window_y = (window.winfo_x(), window.winfo_y())
        x, y = (window_x + ((window.winfo_width() - self.winfo_reqwidth())// 2), window_y + ((window.winfo_height() - self.winfo_reqheight()) // 2))
        self.geometry(f'+{round(x)}+{round(y)}')

    def _create_widgets(self):
        self.columnconfigure((0,1), weight=1)
        self.rowconfigure(0, weight=1)

        student_label = ctk.CTkLabel(self, text='Which student would you like to move?')
        student_label.grid(row=0, column=0, columnspan=2, sticky='nsew')

        self.student_dropdown = ctk.CTkOptionMenu(self, values=[label.cget('text') for label in self.student_labels], width=150)
        self.student_dropdown.grid(row=1, column=0, columnspan=2)

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
        self.confirm_button = ctk.CTkButton(self, text='Confirm Move', command=self.validate_move_student)
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
                           "(If so, click 'Confirm Move' again)"
            self.warning_label.configure(text=warning_txt)
            # Change 'confirm' button command to wait for user to click it again
            var = ctk.StringVar()
            self.confirm_button.configure(command = lambda : var.set('continue'))
            # Wait until confirm button is clicked before continuing
            self.confirm_button.wait_variable(var)

        # Call function to move student in parent frame, and destroy MoveStudentDialog window
        self.database.move_student(student_id, self.current_class_id, new_class_id=class_info['CLASS_ID'])
        self.destroy()

