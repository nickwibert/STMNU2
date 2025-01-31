import customtkinter as ctk
import pandas as pd
from datetime import datetime
import calendar
import functions as fn

# Global variables
from globals import CURRENT_SESSION

# Scrollable frame to display the results from a search 
class SearchResultsFrame(ctk.CTkFrame):
    def __init__(self, master, type, max_row, **kwargs):
        super().__init__(master, **kwargs)
        # Maximum number of rows to return
        self.max_row = max_row
        # Type of SearchResultsFrame (i.e. student, class)
        self.type = type
        # Get database instance from parent frame
        self.database = self.master.database
        # Dataframe where currently displayed search results are stored
        self.df = pd.DataFrame()
        # Index of currently active result
        self.selection_idx = None

        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=10)

        # Frame which contains results from search
        self.results_frame = ctk.CTkFrame(self)

        # Create headers for search results
        if self.type == 'student':
            self.headers = ['First Name', 'Last Name']
            self.column_widths = [150, 150]
        elif self.type == 'class':
            self.headers = ['Instructor', 'Time', 'Name', 'Available', 'Max']
            self.column_widths = [75, 75, 125, 75, 75]
        elif self.type == 'family':
            self.headers = ['Last Name', 'Number of Children']
            self.column_widths = [150, 150]
        for i in range(len(self.headers)):
            ctk.CTkLabel(self.results_frame,
                         text=self.headers[i],
                         width=self.column_widths[i],
                         anchor='w'
                        ).grid(row=0, column=i, sticky='nsew')
            
        self.create_query_frame()
        
        # Configure results_frame and place in SearchResultsFrame
        self.results_frame.rowconfigure(1, weight=1)
        self.results_frame.columnconfigure(tuple(range(len(self.headers))), weight=1)
        self.results_frame.grid(row=1,column=0,sticky='nsew')

        # Scrollable list of search results
        self.results_list = ctk.CTkScrollableFrame(self.results_frame)
        self.results_list.grid(row=1,column=0,columnspan=len(self.headers),sticky='nsew')

        # Create "max_row" placeholder labels for search results
        self.create_labels()
        self.update_labels()

    def create_query_frame(self):
        # Container holding search boxes where user will enter their query
        self.query_frame = ctk.CTkFrame(self)
        self.query_frame.columnconfigure((0,1),weight=1)
        self.query_frame.rowconfigure(0,weight=1)
        self.query_frame.grid(row=0,column=0,)

        if self.type == 'student':
            # Button to create new student
            self.new_student_button = ctk.CTkButton(self.query_frame,
                                                    text='Create New Student',
                                                    command=self.master.create_student)
            self.new_student_button.grid(row=0,column=0, columnspan=2)

            ctk.CTkLabel(self.query_frame, text='STUDENT SEARCH', font=ctk.CTkFont('Britannic',18,'bold')
                         ).grid(row=1,column=0,columnspan=2,sticky='nsew',padx=10)
            search_help_text = 'Search for students by first name, last name, or both. '\
                               'Search results are sorted by last name then first name.'
            ctk.CTkLabel(self.query_frame, text=search_help_text, wraplength=self.query_frame.winfo_reqwidth()
                         ).grid(row=2,column=0,columnspan=2,sticky='nsew',)

            # Dictionary of entry boxes to stay organized. The keys will act as the labels
            # next to each entry box, and the values will hold the actual EntryBox objects
            self.entry_boxes = dict.fromkeys([hdr for hdr in self.headers if 'Name' in hdr])

            # Create and grid each entry box in a loop
            for row, key in list(zip(range(self.query_frame.grid_size()[1],len(self.entry_boxes.keys())+self.query_frame.grid_size()[1]), self.entry_boxes.keys())):
                # Label to identify entry box
                label = ctk.CTkLabel(self.query_frame, text=key + ':', anchor='w')
                label.grid(row=row, column=0,sticky='e',pady=2)
                self.entry_boxes[key] = (ctk.CTkEntry(self.query_frame, textvariable=ctk.StringVar()))
                self.entry_boxes[key].grid(row=row, column=1, sticky='w',pady=2)

            active_help_text = 'Only "active" students are shown by default.\nClick "Show Inactive" to search entire database.'
            ctk.CTkLabel(self.query_frame, text=active_help_text, wraplength=self.query_frame.winfo_reqwidth()
                        ).grid(row=self.query_frame.grid_size()[1],column=0,columnspan=2,sticky='ew',pady=2)
            # Checkbox to show active students
            self.active_checkbox = ctk.CTkCheckBox(self.query_frame, text='Show Inactive Students', command=self.update_labels)
            self.active_checkbox.grid(row=self.query_frame.grid_size()[1], column=0, columnspan=2,)
            # Button to perform search when clicked 
            self.search_button = ctk.CTkButton(self.query_frame, text='Search', command=self.update_labels)
            self.search_button.grid(row=self.query_frame.grid_size()[1], column=0, columnspan=2)

        elif self.type == 'class':
            ctk.CTkLabel(self.query_frame, text='CLASS SEARCH', font=ctk.CTkFont('Britannic',18,'bold')
                         ).grid(row=1,column=0,columnspan=2,sticky='nsew',padx=10)
            search_help_text = 'Click a checkbox to enable a filter, then choose a value.'
            ctk.CTkLabel(self.query_frame, text=search_help_text, wraplength=self.query_frame.winfo_reqwidth()
                         ).grid(row=2,column=0,columnspan=2,sticky='nsew',)
            # Dictionaries of values for different option menus.
            # The dictionary keys is what the user will see, and
            # the corresponding values will be the patterns used to 
            # search the database.
            self.filter_dicts = {
                'INSTRUCTOR' :
                    {k:v for (k,v) in zip(self.database.classes['TEACH'].sort_values().str.title(),
                                          self.database.classes['TEACH'].sort_values())},
                'GENDER' :
                    {
                        "Girl's" : "GIRL",
                        "Boy's"  : "BOY"
                    },
                'DAY' :
                    {
                        'Monday'    : 1,
                        'Tuesday'   : 2,
                        'Wednesday' : 3,
                        'Thursday'  : 4,
                        'Friday'    : 5,
                        'Saturday'  : 6
                    },
                'LEVEL' :
                    {
                        'Beginner'       : 'BEG',
                        'Intermediate'   : 'INT',
                        'Advanced'       : 'ADV',
                        'Level 5/6/8'    : 'LEVEL',
                        'Gymtrainers'    : 'GYMTRAIN',
                        'Tumbling'       : 'TUMBL',
                        'Funtastiks'     : 'FUN',
                        'Parent & Tot'   : 'TOT'
                    },
            }
            self.filter_dropdowns = {}
            self.checkboxes = {}
            for filter_type, filter_dict in self.filter_dicts.items():
                # Frame for option menu
                filter_frame = ctk.CTkFrame(self.query_frame)
                # Option menu
                filter_dropdown = ctk.CTkOptionMenu(filter_frame,
                                                    values=list(filter_dict.keys()),
                                                    command=lambda choice: self.update_labels())

                # Checkbox to enable/disable corresponding option menu
                checkbox = ctk.CTkCheckBox(filter_frame,
                                           text=f'{filter_type.title()}:',
                                           command = lambda f=filter_dropdown: self.toggle_filter(f))
                # Disable instructor filter at outset
                if filter_type == 'INSTRUCTOR':
                    filter_dropdown.configure(state='disabled')
                # Otherwise leave filter active and ensure checkbox is turned on
                else:
                    checkbox.select()

                # Grid checkbox + option menu
                checkbox.grid(row=0, column=0)
                filter_dropdown.grid(row=0, column=1)
                filter_frame.grid(row=self.query_frame.grid_size()[1], column=0, sticky='nsew')

                # Store checkbox and option menu
                self.checkboxes[filter_type] = checkbox
                self.filter_dropdowns[filter_type] = filter_dropdown

            # Set default starting filters:
            # Gender = Girl
            self.filter_dropdowns['GENDER'].set("Girl's")
            # Day = Current Weekday (unless today is Sunday, then set to Monday)
            current_day = datetime.now().weekday()
            self.filter_dropdowns['DAY'].set(calendar.day_name[current_day] if current_day < 6 else "Monday")
            # Level = Beginner
            self.filter_dropdowns['LEVEL'].set("Beginner")

    def create_labels(self):
        # 2D list to store each row in search results
        self.result_rows = []

        self.results_list.columnconfigure(tuple(range(len(self.headers))), weight=1)
        
        # Create placeholder labels, up to 'max_row'
        for row in range(self.max_row):
            # Configure row
            self.results_list.rowconfigure(row, weight=1)
            # List to store labels for this row
            row_labels = []
            for col in range(len(self.headers)):
                # If the data displayed is a number, center; otherwise left-align
                anchor = 'center' if self.headers[col] in ('Available', 'Max') else 'w'
                # Create blank label
                label = ctk.CTkLabel(self.results_list,
                                     text='', anchor=anchor,
                                     width=self.column_widths[col],
                                     cursor='hand2')
                # Placeholder for ID 
                label.id = None
                # Place label in grid and store
                row_labels.append(label)
                row_labels[-1].grid(row=row, column=col, sticky='nsew')

            # Store row
            self.result_rows.append(row_labels)

    def update_labels(self, select_first_result=True):
        if self.type in ['student', 'family']:
            # Get user input
            query = dict.fromkeys(self.entry_boxes.keys())
            for key in query.keys():
                query[key] = self.entry_boxes[key].get().strip()

            # If user provided no input whatsoever, do nothing
            if set(query.values()) == {''}: return

            # Search for matches
            if self.type == 'student':
                self.df = self.database.search_student(query, show_inactive=self.active_checkbox.get())
            elif self.type == 'family':
                self.df = self.database.search_family(query)

        elif self.type == 'class':
            # SPECIAL CASES: If Funtastiks, Parent & Tot, or Level 5/6/8 chosen,
            # disable certain filters before updating search results
            if self.filter_dropdowns['LEVEL'].get() in ['Funtastiks', 'Parent & Tot', 'Level 5/6/8', 'Gymtrainers']:
                for filter_type in ['GENDER', 'INSTRUCTOR', 'DAY']:
                    # Only disable instructor / day of week for high-level classes
                    if filter_type != 'GENDER' and self.filter_dropdowns['LEVEL'].get() not in ['Level 5/6/8', 'Gymtrainers']:
                        continue
                    # Disable filter if necessary
                    if self.checkboxes[filter_type].get():
                        self.checkboxes[filter_type].toggle()

            # Get user input
            filters = dict.fromkeys(self.filter_dicts.keys())
            # Loop through each option menu
            for filter_type in filters.keys():
                filter_dict = self.filter_dicts[filter_type]
                filter_dropdown = self.filter_dropdowns[filter_type]
                # If this option menu is disabled, ignore value inside
                if filter_dropdown.cget('state') == 'disabled':
                    filter = ''
                # Otherwise, get selected filter
                else:
                    filter = filter_dict[filter_dropdown.get()]
                # Store selected filter
                filters[filter_type] = filter

            # Search for matches
            self.df = self.database.filter_classes(filters)

            ## Add column for available spots in each class ##
            # Get student count for each class and add to results dataframe
            # (spots are taken by both PAID and BILLED students)
            payment_info = self.database.payment.loc[(self.database.payment['MONTH'] == CURRENT_SESSION.month)
                                                    & (self.database.payment['YEAR'] == CURRENT_SESSION.year)
                                            ].loc[:, ['STUDENT_ID', 'PAY']]
            bill_info = self.database.bill.loc[(self.database.bill['MONTH'] == CURRENT_SESSION.month)
                                             & (self.database.bill['YEAR'] == CURRENT_SESSION.year)
                                            ].assign(BILLED=True)
            class_counts = self.df.merge(self.database.class_student, how='right'
                                 ).merge(payment_info, how='left'
                                 ).merge(bill_info, how='left'
                                 ).dropna(subset=['PAY','BILLED'], how='all'
                                 ).groupby('CLASS_ID'
                                 ).size(
                                 ).rename('COUNT'
                                 ).reset_index()
            self.df = self.df.merge(class_counts, how='left', on='CLASS_ID')
            # Make sure empty classes have count entered as 0
            self.df['COUNT'] = self.df['COUNT'].fillna(0).astype('int')
            # Calculate number of spots available and drop 'count' column
            available = self.df['MAX'] - self.df['COUNT']
            self.df.insert(self.df.shape[1]-2, 'AVAILABLE', available)
            self.df.drop(columns='COUNT', inplace=True)
            # Truncate class name
            self.df['CLASSNAME'] = self.df['CLASSNAME'].str[:16] + '...'

        # Update matches in search results frame
        self.display_search_results(select_first_result)

    def display_search_results(self, select_first_result=True):
        # Loop through search result labels
        for row in self.result_rows:
            for label in row:
                # Reset label text and unbind highlight functions
                label.configure(text='')
                label.unbind("<Enter>")
                label.unbind("<Leave>")
                label.unbind("<Button-1>")
                # Remove from grid but keep widget in memory (along with its location)
                label.grid_remove()

        # If search results are empty, print message stating no results found,
        # wipe labels in parent frame, and exit function
        if self.df.empty:
            first_label = self.result_rows[0][0]
            first_label.configure(text='No matches found.', bg_color='transparent', cursor='arrow')
            first_label.grid()
            self.master.update_labels(-1)
            return

        # Display all rows unless it exceeds max_row
        row_count = min(self.max_row, self.df.shape[0])

        # Populate search results into labels
        for row in range(row_count):
            # Get relevant ID column (i.e. student ID, class ID)
            id = self.df.filter(like='_ID').iloc[row].values[0]

            for col in range(len(self.headers)):
                # Get text from search results and place in label
                # (Note: we use `col+1` because the first column of `matches` is an ID column)
                label_txt = self.df.iloc[row,col+1]
                label = self.result_rows[row][col]
                # Store relevant ID column as attribute in label
                label.id = id
                label.configure(text=label_txt, bg_color='transparent')
                # Bind functions to highlight row when mouse hovers over it
                label.bind("<Enter>", lambda event, c=label.master, r=row:
                                            fn.highlight_label(c,r))
                label.bind("<Leave>", lambda event, c=label.master, r=row:
                                            fn.unhighlight_label(c,r))
                # When user clicks this row, update all of the information in 
                # student_info_frame to display this student's records
                label.bind("<Button-1>", lambda event, id=label.id:
                                            self.select_result(id))
                # Place label back into grid
                label.grid()

        # Scroll to back to top and select first search result
        if select_first_result:
            self.results_list._parent_canvas.yview_moveto(0)
            self.selection_idx = 0
            self.select_result(self.df.filter(like='_ID').iloc[0].values[0])
        # Otherwise, stay on the currently selected result
        else:
            self.select_result(self.master.id)

    # Select a row from the search results
    def select_result(self, id):
        id_column = self.df.filter(like='_ID').squeeze()
        # If id_column is just one value, convert back to series
        if not isinstance(id_column, pd.Series):
            id_column = pd.Series(id_column)

        # ID of previously selected result
        prev_id = self.master.id

        # If a result was previously selected before this, and the search results have not changed,
        # 'de-activate' the previous search result row by turning color back to default
        if prev_id is not None and prev_id in id_column.values:
            prev_selection_idx = self.df.loc[id_column == prev_id].index[0]
            for label in self.results_list.grid_slaves(row=prev_selection_idx):
                label.configure(bg_color='transparent')

        # Update index to current selection
        self.selection_idx = self.df.loc[id_column == id].index[0]
        # Change color of search result containing selected student to indicate that they are the current selection
        for label in self.results_list.grid_slaves(row=self.selection_idx):
            label.configure(bg_color='royalblue')

        # Finally, update the relevant info frame based on `id`
        self.master.update_labels(id)

    # Select previous result (row ABOVE current selection in search results)
    def prev_result(self):
        # If currently selected result is first row in results, do nothing
        if self.selection_idx == 0:
            return
        # Otherwise, get index for previous row in search results and set as current selection
        else:
            prev_result_idx = self.df.index[self.selection_idx - 1]
            prev_id = self.df.filter(like='_ID').iloc[prev_result_idx].values[0]
            self.select_result(prev_id)

    # Select next result (row BELOW current selection in search results)
    def next_result(self):
        # If currently selected result is last row in results, do nothing
        if self.selection_idx == (self.df.shape[0] - 1):
            return
        # Otherwise, get index for next row in search results and set as current selection
        else:
            next_result_idx = self.df.index[self.selection_idx + 1]
            next_id = self.df.filter(like='_ID').iloc[next_result_idx].values[0]
            self.select_result(next_id)

    # Enable/disable filter dropdown (class search results only)
    def toggle_filter(self, filter_dropdown):
        if filter_dropdown.cget('state') == 'disabled':
            filter_dropdown.configure(state='normal')
        else:
            filter_dropdown.configure(state='disabled')

        # Apply filters
        self.update_labels()