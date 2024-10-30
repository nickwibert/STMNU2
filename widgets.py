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
        lname = dialog.get_input().upper()
        self.student_idx = self.students.search(lname)

        # Create and configure student info window
        super().__init__(*args, **kwargs)
        self.geometry('600x500')
        self.main_frame = MyFrame(self)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure((0,1),weight=1)
        self.main_frame.pack()

        self.student_info_frame = MyFrame(self.main_frame)
        self.student_info_frame.columnconfigure(0, weight=1)
        self.student_info_frame.rowconfigure(0,weight=3)

        # If no student match was found, display error message and exit function
        if self.student_idx is None:
            self.geometry('200x100')
            ctk.CTkLabel(self.student_info_frame, text="No matches found.").pack()
            return
        
        # Series containing all info for a single student
        # (capitalize all strings for visual appeal)
        self.student_info = self.students.df.iloc[self.student_idx].astype('string').fillna('').str.title()
        self.student_info_frame.rowconfigure(tuple(i for i in range(1,10)), weight=1)
        
        self.create_student_info_labels()
        self.student_info_frame.grid(row=0, column=0)

        # Button to edit student info
        self.edit_button = ctk.CTkButton(self.main_frame,
                                         text="Edit Student Info",
                                         command=self.edit_student_info)
        
        self.edit_button.grid(row=1, column=0)

    # Create a "label" for each piece of student information that needs to be displayed,
    # and then place them appropriately in the window
    def create_student_info_labels(self):
        self.labels = {}
        # Create frame for full student name
        self.name_frame = MyFrame(self.student_info_frame)
        self.name_frame.columnconfigure((0,1,2), weight=1)
        self.name_frame.grid(row=0, column=0, sticky='nsew')
        #self.name_frame.columnconfigure(1, weight=1 if len(self.student_info['MIDDLE'].fillna('')) > 0 else 0)
        
        self.labels['FNAME'] = ctk.CTkLabel(self.name_frame, text=self.student_info['FNAME'])
        self.labels['FNAME'].grid(row=0, column=0, padx=2, sticky='nsew')
        self.labels['MIDDLE'] = ctk.CTkLabel(self.name_frame, text=self.student_info['MIDDLE'])
        self.labels['MIDDLE'].grid(row=0, column=1, sticky='nsew')
        self.labels['LNAME'] = ctk.CTkLabel(self.name_frame, text=self.student_info['LNAME'])
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
        self.labels['MOM'] = ctk.CTkLabel(self.mom_frame, text='Mom:')
        self.labels['MOM'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['MOMNAME'] = ctk.CTkLabel(self.mom_frame, text=self.student_info['MOMNAME'])
        self.labels['MOMNAME'].grid(row=0, column=1, sticky='nsew')

        # Create frame for father name
        self.dad_frame = MyFrame(self.student_info_frame)
        self.dad_frame.columnconfigure((0,1), weight=1)
        self.dad_frame.grid(row=4,column=0, sticky='nsew')
        self.labels['DAD'] = ctk.CTkLabel(self.dad_frame, text='Dad:')
        self.labels['DAD'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['DADNAME'] = ctk.CTkLabel(self.dad_frame, text=self.student_info['DADNAME'])
        self.labels['DADNAME'].grid(row=0, column=1, sticky='nsew')

        self.labels['PHONE'] = ctk.CTkLabel(self.student_info_frame, text=self.student_info['PHONE'])
        self.labels['PHONE'].grid(row=5, column=0, sticky='nsew')
        self.labels['BIRTHDAY'] = ctk.CTkLabel(self.student_info_frame, text=self.student_info['BIRTHDAY'])
        self.labels['BIRTHDAY'].grid(row=6, column=0, sticky='nsew')
        self.labels['ENROLLDATE'] = ctk.CTkLabel(self.student_info_frame, text=self.student_info['ENROLLDATE'])
        self.labels['ENROLLDATE'].grid(row=7, column=0, sticky='nsew')
        self.labels['MONTHLYFEE'] = ctk.CTkLabel(self.student_info_frame, text=self.student_info['MONTHLYFEE'])
        self.labels['MONTHLYFEE'].grid(row=8, column=0, sticky='nsew')
        self.labels['BALANCE'] = ctk.CTkLabel(self.student_info_frame, text=self.student_info['BALANCE'])
        self.labels['BALANCE'].grid(row=9, column=0, sticky='nsew')

    # Edit student information currently displayed in window
    def edit_student_info(self):
        # Hide student info labels temporarily
        # for label in self.labels.values(): label.grid_forget()
        # Replace info labels with entry boxes, and populate with the current info
        self.entry_boxes = dict.fromkeys(self.labels)
        print(self.entry_boxes)
        for key in self.labels.keys():
            # Ignore certain labels
            if key in ('MOM', 'DAD'):
                self.entry_boxes.pop(key)
                continue

            default_text = ctk.StringVar()
            default_text.set(self.labels[key].cget('text'))
            self.entry_boxes[key] = ctk.CTkEntry(self.labels[key], textvariable=default_text)
            self.entry_boxes[key].place(x=0, y=0, relheight=1.0, relwidth=1.0)
           
        self.confirm_button = ctk.CTkButton(self.edit_button,
                                            text="Confirm Changes",
                                            command=partial(self.students.update_student_info,
                                                            student_idx=self.student_idx,
                                                            entry_boxes=self.entry_boxes))
        self.confirm_button.place(x=0, y=0, relheight=1.0, relwidth=1.0)



            

    

