import customtkinter as ctk
import pandas as pd
from datetime import datetime
import calendar

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
        self.rowconfigure(1, weight=4)

        self.create_query_frame()

        # Frame which contains results from search
        self.results_frame = ctk.CTkFrame(self)

        # Create headers for search results
        if self.type == 'student':
            self.headers = ['First Name', 'Last Name']
            self.column_widths = [150, 150]
        elif self.type == 'class':
            self.headers = ['Instructor', 'Time', 'Name', 'Max', 'Available']
            self.column_widths = [75, 75, 150, 50, 50]
        for i in range(len(self.headers)):
            ctk.CTkLabel(self.results_frame,
                         text=self.headers[i],
                         width=self.column_widths[i],
                         anchor='w'
                        ).grid(row=0, column=i, sticky='nsew')
        
        # Configure results_frame and place in SearchResultsFrame
        self.results_frame.rowconfigure(1, weight=1)
        self.results_frame.columnconfigure(tuple(range(len(self.headers))), weight=1)
        self.results_frame.grid(row=1,column=0,sticky='nsew')

        # Scrollable list of search results
        self.results_list = ctk.CTkScrollableFrame(self.results_frame)
        self.results_list.grid(row=1,column=0,columnspan=len(self.headers),sticky='nsew')

        # Create "max_row" placeholder labels for search results
        self.create_labels()
        #self.update_labels()

    def create_query_frame(self):
        # Container holding search boxes where user will enter their query
        self.query_frame = ctk.CTkFrame(self)
        self.query_frame.columnconfigure(0,weight=1)
        self.query_frame.rowconfigure((0,1,2,3),weight=1)
        self.query_frame.grid(row=0,column=0)

        if self.type == 'student':
            # Dictionary of entry boxes to stay organized. The keys will act as the labels
            # next to each entry box, and the values will hold the actual EntryBox objects
            self.entry_boxes = dict.fromkeys(['First Name', 'Last Name'])

            # Create and grid each entry box in a loop
            for row, key in list(zip(range(len(self.entry_boxes.keys())), self.entry_boxes.keys())):
                # Label to identify entry box
                label = ctk.CTkLabel(self.query_frame, text=key + ':', anchor='w')
                label.grid(row=row, column=0, sticky='nsew', pady=5, padx=5)
                self.entry_boxes[key] = (ctk.CTkEntry(self.query_frame, textvariable=ctk.StringVar()))
                self.entry_boxes[key].grid(row=row, column=1, sticky='ew')

                # Button to perform search when clicked 
                self.search_button = ctk.CTkButton(self.query_frame, text='Search', command=self.update_labels)
                self.search_button.grid(row=len(self.entry_boxes)+1, column=0, columnspan=2)

        elif self.type == 'class':
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
                        'Level 5'        : 'L5',
                        'Level 6'        : 'L6',
                        'Level 8'        : 'L8',
                        'Funtastiks'     : 'FUN',
                        'Parent & Tot'   : 'TOT'
                    },
            }
            self.filter_dropdowns = {}
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
                checkbox.select()

                # Grid checkbox + option menu
                checkbox.grid(row=0, column=0)
                filter_dropdown.grid(row=0, column=1)
                filter_frame.grid(row=self.query_frame.grid_size()[1], column=0, sticky='nsew')

                # Store option menu
                self.filter_dropdowns[filter_type] = filter_dropdown

            # Set default starting filters
            self.filter_dropdowns['GENDER'].set("Girl's")
            current_day = datetime.now().weekday()
            self.filter_dropdowns['DAY'].set(calendar.day_name[current_day] if current_day < 6 else "Monday")
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
                # Create blank label
                label = ctk.CTkLabel(self.results_list,
                                     text='', anchor='w',
                                     width=self.column_widths[col],
                                     cursor='hand2')
                # Place label in grid and store
                label.grid(row=row, column=col, sticky='nsew')
                row_labels.append(label)

            # Store row
            self.result_rows.append(row_labels)

    def update_labels(self):
        if self.type == 'student':
            # Get user input
            query = dict.fromkeys(self.entry_boxes.keys())
            for key in query.keys():
                query[key] = self.entry_boxes[key].get().strip()

            # If user provided no input whatsoever, do nothing
            if set(query.values()) == {''}: return

            # Search for matches
            self.df = self.database.search_student(query)

        elif self.type == 'class':
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
            class_counts = self.df.merge(self.database.class_student, how='right'
                                         ).groupby('CLASS_ID'
                                         ).size(
                                         ).rename('COUNT'
                                         ).reset_index()
            self.df = self.df.merge(class_counts, how='left', on='CLASS_ID')
            # Make sure empty classes have count entered as 0
            self.df['COUNT'] = self.df['COUNT'].fillna(0).astype('int')
            # Calculate number of spots available and drop 'count' column
            self.df['AVAILABLE'] = self.df['MAX'] - self.df['COUNT']
            self.df.drop(columns='COUNT', inplace=True)
            # Truncate class name
            self.df['CLASSNAME'] = self.df['CLASSNAME'].str[:25]

        # Update matches in search results frame
        self.display_search_results()

    def display_search_results(self):
        # Move scrollbar back to top
        self.results_list._parent_canvas.yview_moveto(0)
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

        # Boolean variable which is True when the number of matches
        # is greater than `max_row`, indicating that we need to truncate the results
        truncate_results = True if self.df.shape[0] > self.max_row else False
        # Number of rows in SearchResultsList including potential 'truncated results' message
        # and column headers
        row_count = min(self.max_row, self.df.shape[0])

        # Populate results into labels
        for row in range(row_count):
            # Get relevant ID column (i.e. student ID, class ID)
            id = self.df.filter(like='_ID').iloc[row].values[0]
            for col in range(len(self.headers)):
                # Get text from search results and place in label
                # (Note: we use `col+1` because the first column of `matches` is an ID column)
                label_txt = self.df.iloc[row,col+1]
                label = self.result_rows[row][col]
                label.configure(text=label_txt, bg_color='transparent')
                # Bind functions to highlight row when mouse hovers over it
                label.bind("<Enter>", lambda event, row=row:
                                            self.highlight_label(row))
                label.bind("<Leave>", lambda event, row=row:
                                            self.unhighlight_label(row))
                # When user clicks this row, update all of the information in 
                # student_info_frame to display this student's records
                label.bind("<Button-1>", lambda event, id=id:
                                            self.select_result(id))

                # Place label back into grid
                label.grid()

        # If search results are empty, wipe the parent frame so no info is displayed
        if self.df.empty:
            self.master.update_labels(-1)
        # Otherwise, refresh parent frame to display info for student at top of search results
        else:
            self.selection_idx = 0
            self.select_result(self.df.filter(like='_ID').iloc[0].values[0])

    # Highlight student row when mouse hovers over it
    def highlight_label(self, row):
        for label in self.results_list.grid_slaves(row=row):
                label.configure(fg_color='white smoke')

    # Undo highlight when mouse moves off
    def unhighlight_label(self, row):
        for label in self.results_list.grid_slaves(row=row):
                label.configure(fg_color='transparent')

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

    # Change student info window to the previous student (alphabetically)
    def prev_result(self):
        # If currently selected student is first student in results, do nothing
        if self.selection_idx == 0:
            return
        # Otherwise, get index for previous row in search results and set as current selection
        else:
            prev_student_idx = self.df.index[self.selection_idx - 1]
            prev_student_id = self.df.filter(like='_ID').iloc[prev_student_idx].values[0]
            self.select_result(prev_student_id)

    # Change student info window to the next student in dataframe
    def next_result(self):
        # If currently selected student is last student in results, do nothing
        if self.selection_idx == (self.df.shape[0] - 1):
            return
        else:
            next_student_idx = self.df.index[self.selection_idx + 1]
            next_student_id = self.df.filter(like='_ID').iloc[next_student_idx].values[0]
            self.select_result(next_student_id)

    # Enable/disable filter dropdown (class search results only)
    def toggle_filter(self, filter_dropdown):
        if filter_dropdown.cget('state') == 'disabled':
            filter_dropdown.configure(state='normal')
        else:
            filter_dropdown.configure(state='disabled')

        # Apply filters
        self.update_labels()