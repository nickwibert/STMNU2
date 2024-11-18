import customtkinter as ctk
import dbf
import functions as fn
from functools import partial
from datetime import datetime

class MyFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

# Scrollable frame to display the results from a search 
class SearchResultsFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, results, max_row, **kwargs):
        super().__init__(master, **kwargs)
        # Results from user's search (dataframe)
        self.results = results
        # Maximum number of rows to return
        self.max_row = max_row

        # Populate results into labels
        for row in range(min(max_row, self.results.shape[0])+1):
            # Configure row
            self.rowconfigure(row, weight=1)
            for col in range(self.results.shape[1]):
                # Create headers
                if row == 0:
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
                                                master.create_student_info_window(idx))

                label.grid(row=row, column=col, sticky='nsew')
    
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

# Reusable class for the student information window. User searches for a student,
# and then picks an individual student from the resulting matches.
# Multiple windows can be open at once.
class StudentInfoWindow(ctk.CTkToplevel):
    def __init__(self, master, students, *args, **kwargs):
        self.students = students
        # # Ask user for last name input and search for a match in the students dataframe
        # dialog = ctk.CTkInputDialog(text="Last Name:", title="Student Info")
        # lname = dialog.get_input()
        # # If no name provided, do nothing
        # if lname is None or len(lname) == 0:
        #     return
        # # Otherwise, search for matches in students dataframe
        # matches = self.students.search(lname)

        # Create and configure window 
        super().__init__(*args, **kwargs)
        self.geometry('400x300')
        # Main frame to hold widgets
        self.main_frame = MyFrame(self)
        self.main_frame.grid(row=0,column=0,sticky='nsew')
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0,weight=1)
        self.main_frame.pack()
        # Dictionary of entry boxes to stay organized. The keys will act as the labels
        # next to each entry box, and the values will hold the actual EntryBox objects
        self.entry_boxes = dict.fromkeys(['Student Number', 'First Name', 'Middle Name', 'Last Name'])
        # Create and grid each entry box in a loop
        for row, key in list(zip(range(len(self.entry_boxes.keys())), self.entry_boxes.keys())):
            # Label to identify entry box
            label = ctk.CTkLabel(self.main_frame, text=key + ':')
            label.grid(row=row, column=0)
            # If field is numeric, enable data validation
            if row == 0:
                vcmd = (self.register(fn.validate_float), '%d', '%P', '%s', '%S')
                self.entry_boxes[key] = (ctk.CTkEntry(self.main_frame, validate='key', validatecommand=vcmd))
            else:
                self.entry_boxes[key] = (ctk.CTkEntry(self.main_frame))
            
            self.entry_boxes[key].grid(row=row, column=1)
        
        # Button to perform search when clicked (see function create_search_results_window())
        self.search_button = ctk.CTkButton(self.main_frame, text='Search', command=self.create_search_results_window)
        self.search_button.grid(row=len(self.entry_boxes)+1, column=0, columnspan=2)

        # Also bind Enter key to the "Search" button
        self.bind('<Return>', lambda event: self.search_button.invoke())

    def create_search_results_window(self):
        # Get user input
        query = dict.fromkeys(self.entry_boxes.keys())
        for key in query.keys():
            query[key] = self.entry_boxes[key].get().strip()

        # If user provided no input whatsoever, do nothing
        if set(query.values()) == {''}: return

        # Destroy existing widgets
        self.main_frame.destroy()
        # Search for matches
        matches = self.students.search(query)
        self.geometry(f'{100*matches.shape[1]}x400')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # If no match found, create window and display error
        if matches.empty:
            self.create_student_info_window(None)
        else:
            self.matches_frame = SearchResultsFrame(self, matches, max_row=100)
            self.matches_frame.grid(row=0,column=0,sticky='nsew')

    def create_student_info_window(self, student_idx):
        # Selected student
        self.student_idx = student_idx
        # If no student match was found, display error message and exit function
        if self.student_idx is None:
            self.geometry('200x100')
            ctk.CTkLabel(self, text="No matches found.").pack()
            return
        
        # Hide search results for now
        self.matches_frame.grid_forget()

        # Initialize empty dict of student info labels
        self.labels = {}
        self.main_frame = MyFrame(self)
        self.main_frame.grid(row=0,column=0,sticky='nsew')
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure((0,1,2,3),weight=1)

        # Button to return to search results
        self.return_to_matches_button = ctk.CTkButton(self.main_frame,
                                               text="Return to Search Results",
                                               command=self.return_to_matches)
        self.return_to_matches_button.grid(row=0,column=0)
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
        self.prev_next_frame.grid(row=1,column=0)


        self.student_info_frame = MyFrame(self.main_frame)
        self.student_info_frame.columnconfigure(0, weight=1)
        self.student_info_frame.rowconfigure(0,weight=3)
        self.student_info_frame.grid(row=2, column=0)
        
        self.student_info_frame.rowconfigure(tuple(i for i in range(1,10)), weight=1)
        self.create_student_info_labels()

        # Button to edit student info
        self.edit_button = ctk.CTkButton(self.main_frame,
                                         text="Edit Student Info",
                                         command=self.edit_student_info)
        
        self.edit_button.grid(row=3, column=0)

        # Empty list for error labels (created when necessary)
        self.error_labels = []

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

        # Series containing all info for a single student (capitalize all strings for visual appeal)
        self.student_info = self.students.df.iloc[self.student_idx].astype('string').fillna('').str.title()
        name_font = ctk.CTkFont('Britannic', 18)
        
        self.labels['FNAME'] = ctk.CTkLabel(self.name_frame, text=self.student_info['FNAME'], font=name_font, anchor='e')
        self.labels['FNAME'].grid(row=0, column=0, padx=2, sticky='nsew')
        self.labels['MIDDLE'] = ctk.CTkLabel(self.name_frame, text=self.student_info['MIDDLE'], font=name_font)
        self.labels['MIDDLE'].grid(row=0, column=1, sticky='nsew')
        self.labels['LNAME'] = ctk.CTkLabel(self.name_frame, text=self.student_info['LNAME'], font=name_font, anchor='w')
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
        self.enrolldate_frame = MyFrame(self.student_info_frame)
        self.enrolldate_frame.columnconfigure((0,1), weight=1)
        self.enrolldate_frame.grid(row=7,column=0, sticky='nsew')
        self.labels['ENROLLDATE_HEADER'] = ctk.CTkLabel(self.enrolldate_frame, text='Enroll Date:', anchor='w')
        self.labels['ENROLLDATE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['ENROLLDATE'] = ctk.CTkLabel(self.enrolldate_frame, text=self.student_info['ENROLLDATE'], anchor='e')
        self.labels['ENROLLDATE'].grid(row=0, column=1, sticky='nsew')

        # Create frame for monthly fee
        self.monthlyfee_frame = MyFrame(self.student_info_frame)
        self.monthlyfee_frame.columnconfigure((0,1), weight=1)
        self.monthlyfee_frame.grid(row=8,column=0, sticky='nsew')
        self.labels['MONTHLYFEE_HEADER'] = ctk.CTkLabel(self.monthlyfee_frame, text='Monthly Fee:', anchor='w')
        self.labels['MONTHLYFEE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['MONTHLYFEE'] = ctk.CTkLabel(self.monthlyfee_frame, text=f'{float(self.student_info['MONTHLYFEE']):.2f}', anchor='e')
        self.labels['MONTHLYFEE'].grid(row=0, column=1, sticky='nsew')

        # Create frame for balance
        self.balance_frame = MyFrame(self.student_info_frame)
        self.balance_frame.columnconfigure((0,1), weight=1)
        self.balance_frame.grid(row=9,column=0, sticky='nsew')
        self.labels['BALANCE_HEADER'] = ctk.CTkLabel(self.balance_frame, text='Balance:', anchor='w')
        self.labels['BALANCE_HEADER'].grid(row=0,column=0,padx=2, sticky='nsew')
        self.labels['BALANCE'] = ctk.CTkLabel(self.balance_frame, text=f'{float(self.student_info['BALANCE']):.2f}', anchor='e')
        self.labels['BALANCE'].grid(row=0, column=1, sticky='nsew')

    # Edit student information currently displayed in window
    def edit_student_info(self):
        # Disable prev/next student buttons
        self.prev_student_button.configure(state='disabled')
        self.next_student_button.configure(state='disabled')
        self.return_to_matches_button.configure(state='disabled')
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


        
    def confirm_edit(self):
        # Get rid of any error labels, if they exist
        if len(self.error_labels) > 0:
            self.geometry(f'{self.winfo_width()}x{self.winfo_height() - 50*len(self.error_labels)}')
            for _ in range(len(self.error_labels)):
                label = self.error_labels.pop()
                label.destroy()
            self.update()

        
        # Update labels (where necessary) and then destroy entry boxes
        for field in self.entry_boxes.keys():
            field_info = self.students.dbf_table.field_info(field)
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

                self.error_labels.append(ctk.CTkLabel(self.main_frame,
                                                    text=error_txt,
                                                    text_color='red'))
                self.error_labels[-1].grid(row=self.main_frame.grid_size()[1], column=0)



        # If any errors so far, exit function so user can fix entry
        if len(self.error_labels) > 0:
            # Adjust window size to accomodate
            self.geometry(f'{self.winfo_width()}x{self.winfo_height() + 50*len(self.error_labels)}')
            self.update()
            return
        else:
            # Update student dataframe and dbf file to reflect changes
            self.students.update_student_info(self.student_idx, self.entry_boxes)
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
            self.return_to_matches_button.configure(state='normal')

    # Go back to search results window
    def return_to_matches(self):
        # Destroy student info frame and contents
        self.main_frame.destroy()
        # Re-enable search results
        self.matches_frame.grid(row=0,column=0,sticky='nsew')

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




            

    

