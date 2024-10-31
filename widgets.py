import customtkinter as ctk
import functions as fn
from functools import partial

class MyFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

class StudentInfoWindow(ctk.CTkToplevel):
    def __init__(self, students, *args, **kwargs):
        self.students = students
        # Ask user for last name input and search for a match in the students dataframe
        dialog = ctk.CTkInputDialog(text="Last Name:", title="Student Info")        
        lname = dialog.get_input()
        # If no name provided, do nothing
        if lname is None or len(lname) == 0:
            return

        # Otherwise, search for match in students dataframe
        self.student_idx = self.students.search(lname)
        # Initialize empty dict of student info labels
        self.labels = {}

        # Create and configure student info window
        super().__init__(*args, **kwargs)
        self.geometry('600x500')
        self.main_frame = MyFrame(self)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure((0,1,2),weight=1)
        self.main_frame.pack()

        # Buttons to scroll through students
        self.prev_next_frame = MyFrame(self.main_frame)
        self.prev_next_frame.rowconfigure(0,weight=1)
        self.prev_next_frame.columnconfigure((0,1),weight=1)
        self.prev_student_button = ctk.CTkButton(self.prev_next_frame,
                                         text="Previous Student",
                                         command=self.go_prev_student)
        self.next_student_button = ctk.CTkButton(self.prev_next_frame,
                                         text="Next Student",
                                         command=self.go_next_student)
        self.prev_student_button.grid(row=0,column=0,pady=5,padx=5)
        self.next_student_button.grid(row=0,column=1,pady=5,padx=5)
        self.prev_next_frame.grid(row=0,column=0)


        self.student_info_frame = MyFrame(self.main_frame)
        self.student_info_frame.columnconfigure(0, weight=1)
        self.student_info_frame.rowconfigure(0,weight=3)
        self.student_info_frame.grid(row=1, column=0)

        # If no student match was found, display error message and exit function
        if self.student_idx is None:
            self.geometry('200x100')
            ctk.CTkLabel(self.student_info_frame, text="No matches found.").pack()
            return
        
        self.student_info_frame.rowconfigure(tuple(i for i in range(1,10)), weight=1)
        self.create_student_info_labels()

        # Button to edit student info
        self.edit_button = ctk.CTkButton(self.main_frame,
                                         text="Edit Student Info",
                                         command=self.edit_student_info)
        
        self.edit_button.grid(row=2, column=0)

    # Create a "label" for each piece of student information that needs to be displayed,
    # and then place them appropriately in the window
    def create_student_info_labels(self):
        # If student info labels already exist, destroy them
        if len(self.labels) > 0:
            for key in self.labels.keys():
                self.labels[key].destroy()
                #self.labels.pop(key)
            self.labels = {}

        # Create frame for full student name
        self.name_frame = MyFrame(self.student_info_frame)
        self.name_frame.columnconfigure((0,1,2), weight=1)
        self.name_frame.grid(row=0, column=0, sticky='nsew')
        #self.name_frame.columnconfigure(1, weight=1 if len(self.student_info['MIDDLE'].fillna('')) > 0 else 0)

        # Series containing all info for a single student
        # (capitalize all strings for visual appeal)
        self.student_info = self.students.df.iloc[self.student_idx].astype('string').fillna('').str.title()
        
        self.labels['FNAME'] = ctk.CTkLabel(self.name_frame, text=self.student_info['FNAME'], anchor='e')
        self.labels['FNAME'].grid(row=0, column=0, padx=2, sticky='nsew')
        self.labels['MIDDLE'] = ctk.CTkLabel(self.name_frame, text=self.student_info['MIDDLE'])
        self.labels['MIDDLE'].grid(row=0, column=1, sticky='nsew')
        self.labels['LNAME'] = ctk.CTkLabel(self.name_frame, text=self.student_info['LNAME'], anchor='w')
        self.labels['LNAME'].grid(row=0, column=2, padx=2, sticky='nsew')

        # Create frame for full address
        self.address_frame = MyFrame(self.student_info_frame)
        self.address_frame.rowconfigure((0,1), weight=1)
        self.address_frame.columnconfigure((0,1,2), weight=1)
        self.address_frame.grid(row=1,column=0,rowspan=2, sticky='nsew')

        self.labels['ADDRESS'] = ctk.CTkLabel(self.address_frame, text=self.student_info['ADDRESS'])
        self.labels['ADDRESS'].grid(row=0, column=0, columnspan=3, sticky='nsew')
        self.labels['CITY'] = ctk.CTkLabel(self.address_frame, text=self.student_info['CITY'])
        self.labels['CITY'].grid(row=1, column=0, padx=2, sticky='nsew')
        self.labels['STATE'] = ctk.CTkLabel(self.address_frame, text=self.student_info['STATE'].upper())
        self.labels['STATE'].grid(row=1, column=1, padx=2, sticky='nsew')
        self.labels['ZIP'] = ctk.CTkLabel(self.address_frame, text=self.student_info['ZIP'])
        self.labels['ZIP'].grid(row=1, column=2, padx=2, sticky='nsew')

        # Create frame for mother name
        self.mom_frame = MyFrame(self.student_info_frame)
        self.mom_frame.columnconfigure((0,1), weight=1)
        self.mom_frame.grid(row=3,column=0, sticky='nsew')
        self.labels['MOM_HEADER'] = ctk.CTkLabel(self.mom_frame, text='Mom:')
        self.labels['MOM_HEADER'].grid(row=0, column=0, sticky='nse', padx=4)
        self.labels['MOMNAME'] = ctk.CTkLabel(self.mom_frame, text=self.student_info['MOMNAME'], anchor='w')
        self.labels['MOMNAME'].grid(row=0, column=1, sticky='nsew')

        # Create frame for father name
        self.dad_frame = MyFrame(self.student_info_frame)
        self.dad_frame.columnconfigure((0,1), weight=1)
        self.dad_frame.grid(row=4,column=0, sticky='nsew')
        self.labels['DAD_HEADER'] = ctk.CTkLabel(self.dad_frame, text='Dad:')
        self.labels['DAD_HEADER'].grid(row=0,column=0, padx=4, sticky='nse')
        self.labels['DADNAME'] = ctk.CTkLabel(self.dad_frame, text=self.student_info['DADNAME'], anchor='w')
        self.labels['DADNAME'].grid(row=0, column=1, sticky='nsew')

        self.labels['PHONE'] = ctk.CTkLabel(self.student_info_frame, text=self.student_info['PHONE'])
        self.labels['PHONE'].grid(row=5, column=0, sticky='nsew')


        # Create frame for birthday
        self.bday_frame = MyFrame(self.student_info_frame)
        self.bday_frame.columnconfigure((0,1), weight=1)
        self.bday_frame.grid(row=6,column=0, sticky='nsew')
        self.labels['BIRTHDAY_HEADER'] = ctk.CTkLabel(self.bday_frame, text='Birthday:', anchor='w')
        self.labels['BIRTHDAY_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['BIRTHDAY'] = ctk.CTkLabel(self.bday_frame, text=self.student_info['BIRTHDAY'], anchor='e')
        self.labels['BIRTHDAY'].grid(row=0, column=1, sticky='nsew')

        # Create frame for enroll date
        self.bday_frame = MyFrame(self.student_info_frame)
        self.bday_frame.columnconfigure((0,1), weight=1)
        self.bday_frame.grid(row=7,column=0, sticky='nsew')
        self.labels['ENROLLDATE_HEADER'] = ctk.CTkLabel(self.bday_frame, text='Enroll Date:', anchor='w')
        self.labels['ENROLLDATE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['ENROLLDATE'] = ctk.CTkLabel(self.bday_frame, text=self.student_info['ENROLLDATE'], anchor='e')
        self.labels['ENROLLDATE'].grid(row=0, column=1, sticky='nsew')

        self.labels['MONTHLYFEE'] = ctk.CTkLabel(self.student_info_frame, text=self.student_info['MONTHLYFEE'])
        self.labels['MONTHLYFEE'].grid(row=8, column=0, sticky='nsew')
        self.labels['BALANCE'] = ctk.CTkLabel(self.student_info_frame, text=self.student_info['BALANCE'])
        self.labels['BALANCE'].grid(row=9, column=0, sticky='nsew')

    # Edit student information currently displayed in window
    def edit_student_info(self):
        # Disable prev/next student buttons
        self.prev_student_button.configure(state='disabled')
        self.next_student_button.configure(state='disabled')
        # Replace info labels with entry boxes, and populate with the current info
        self.entry_boxes = dict.fromkeys(self.labels)

        for key in self.labels.keys():
            # Ignore certain labels
            if 'HEADER' in key:
                self.entry_boxes.pop(key)
                continue

            default_text = ctk.StringVar()
            default_text.set(self.labels[key].cget('text'))
            self.entry_boxes[key] = ctk.CTkEntry(self.labels[key], textvariable=default_text)
            self.entry_boxes[key].place(x=0, y=0, relheight=1.0, relwidth=1.0)
           
        self.confirm_button = ctk.CTkButton(self.edit_button,
                                            text="Confirm Changes",
                                            command=self.confirm_edit)
        self.confirm_button.place(x=0, y=0, relheight=1.0, relwidth=1.0)

    def confirm_edit(self):
        # Update student dataframe to reflect changes
        self.students.update_student_info(self.student_idx, self.entry_boxes)

        # Update labels (where necessary) and then destroy entry boxes
        for key in self.entry_boxes.keys():
            if self.entry_boxes[key].get() != self.labels[key].cget("text"):
                self.labels[key].configure(text=self.entry_boxes[key].get())
            self.entry_boxes[key].destroy()

        self.confirm_button.destroy()
        # Re-enable prev/next student buttons
        self.prev_student_button.configure(state='normal')
        self.next_student_button.configure(state='normal')

    # Change student info window to the previous student (alphabetically)
    def go_prev_student(self):
        # Since the indices are chronological and not alphabetical, first find 
        # the location of the current student after sorting alphabetically
        student_sorted_idx = self.students.sort_alphabetical().index.get_loc(self.student_idx)
        # If current student is the first student alphabetically, there are no previous students
        if student_sorted_idx == 0:
            return
        else:
            prev_student_idx = self.students.sort_alphabetical().index[student_sorted_idx - 1]
            self.student_idx = prev_student_idx
            self.create_student_info_labels()

    # Change student info window to the next student in dataframe
    def go_next_student(self):
        # Since the indices are chronological and not alphabetical, first find 
        # the location of the current student after sorting alphabetically
        student_sorted_idx = self.students.sort_alphabetical().index.get_loc(self.student_idx)
        # If current student is the last student alphabetically, there are no subsequent students
        if student_sorted_idx == (self.students.df.shape[0]-1):
            return
        else:
            next_student_idx = self.students.sort_alphabetical().index[student_sorted_idx + 1]
            self.student_idx = next_student_idx
            self.create_student_info_labels()




            

    

