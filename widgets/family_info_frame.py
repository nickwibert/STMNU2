import customtkinter as ctk
import pandas as pd
import calendar
from datetime import datetime

import functions as fn
from widgets.search_results_frame import SearchResultsFrame


class FamilyInfoFrame(ctk.CTkFrame):
    def __init__(self, window, master, database, **kwargs):
        # Create frame
        super().__init__(master, **kwargs)
        # Application window
        self.window = window

        # Instance of student database
        self.database = database
        self.id = None

        self.buttons = {}

        # Configure rows/columns
        self.columnconfigure((0,1,2), weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure((1,2), weight=5)

        # Frame which will contain search boxes / results to perform student search
        self.search_results_frame = SearchResultsFrame(self, type='family', max_row=100)
        # Frame at top of window which lists the name of the selected family
        self.surname_frame = ctk.CTkFrame(self)
        # Frame which will list guardians
        self.guardian_frame = ctk.CTkFrame(self)
        # Frame which will list children
        self.child_frame = ctk.CTkFrame(self)

        self.surname_frame.grid(row=0,column=1,sticky='nsew')
        self.guardian_frame.grid(row=1,column=1,sticky='nsew')
        self.child_frame.grid(row=2,column=1,sticky='nsew')
        self.search_results_frame.grid(row=0,column=0,rowspan=3, sticky='nsew')

        self.create_labels()

    def create_labels(self):
        ### Surname Frame ###
        self.surname_frame.columnconfigure(0,weight=1)
        self.surname_label = ctk.CTkLabel(self.surname_frame, text='')
        self.surname_label.grid(row=0,column=0,sticky='nsew')


    def update_labels(self, family_id):
        # Currently selected family
        self.id = family_id

        surname = self.database.student[self.database.student['FAMILY_ID'] == family_id
                                        ].loc[:,'LNAME'
                                        ].squeeze()

        ### Surname Frame ###
        self.surname_label.configure(text=f'{surname.title()} Family')
