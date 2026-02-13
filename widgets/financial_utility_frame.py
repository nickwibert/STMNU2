import customtkinter as ctk
from tktooltip import ToolTip
import pandas as pd
import calendar
from datetime import datetime

import functions as fn
from widgets.search_results_frame import StudentSearchResultsFrame

# Global variables
from globals import CURRENT_SESSION, CALENDAR_DICT

class FinancialUtilityFrame(ctk.CTkFrame):
    def __init__(self, window, master, database, default_year=CURRENT_SESSION.year, **kwargs):
        # Create frame
        super().__init__(master, **kwargs)
        # Application window
        self.window = window

        # Instance of student database
        self.database = database

        self.filter_dropdowns = {}

        # Configure rows/columns
        self.columnconfigure((0,1,2), weight=1)
        self.rowconfigure((0,1,2,3,4), weight=10)
        
        # Get all valid session years in database
        self.database.cursor.execute('SELECT DISTINCT YEAR FROM payment')
        year_list = [f'{t[0]}' for t in self.database.cursor.fetchall()]
        self.filter_dropdowns['SESSION_YEAR'] = ctk.CTkOptionMenu(
            self,
            values=year_list,
            font=ctk.CTkFont('Arial',32,'bold'),
            command=lambda choice: self.update_labels()
        )
        
        # Set year to default passed in value
        self.filter_dropdowns['SESSION_YEAR'].set(f'{default_year}')
        self.filter_dropdowns['SESSION_YEAR'].grid(row=0,column=0)

        self.financial_as_of_today_frame = ctk.CTkFrame(self)
        self.financial_as_of_today_frame.columnconfigure(0,weight=1)
        self.financial_as_of_today_frame.rowconfigure(0,weight=1)
        self.financial_as_of_today_frame.rowconfigure(1,weight=3)
        self.financial_as_of_today_frame.grid(row=0,column=1,columnspan=2,sticky='nsew')


        self.month_frames = {}
        for month_idx in range(12):
            month_frame = ctk.CTkFrame(self, border_width=5, border_color='midnightblue')
            month_frame.rowconfigure(0, weight=1)
            month_frame.rowconfigure((1,2), weight=4)
            month_frame.columnconfigure((0,1),weight=1)
            month_frame.grid(row=month_idx // 3 + 1, column=month_idx % 3, sticky='nsew')
            self.month_frames[calendar.month_name[month_idx+1]] = month_frame 



        # Populate frame with labels containing student information
        self.create_labels()
        self.update_labels()


    # Create a label for each bit of student information and place into the frame
    def create_labels(self):

        # Create special label based on pay/billing as of current month/day
        self.today_header_label = ctk.CTkLabel(
            self.financial_as_of_today_frame,
            text = '',
            font=ctk.CTkFont('Arial',28,'bold'),
            wraplength=500
        )
        self.today_header_label.grid(row=0,column=0,sticky='nsew')
        self.today_payment_label = ctk.CTkLabel(
            self.financial_as_of_today_frame,
            text='',
            font=ctk.CTkFont('Arial',20,'bold'),
            text_color='green'
        )
        self.today_payment_label.grid(row=1,column=0,sticky='nsew')

        self.payment_labels = {}
        self.bill_labels = {}

        for month_name, month_frame in self.month_frames.items():
            month_header = ctk.CTkLabel(
                month_frame,
                text=month_name.upper(),
                font=ctk.CTkFont('Arial',20,'bold'),
                bg_color='dodgerblue4',
                text_color='white'
            )
            month_header.grid(row=0,column=0,columnspan=2, sticky='nsew')

            payment_header = ctk.CTkLabel(
                month_frame,
                text='Gross Pay:',
                font=ctk.CTkFont('Arial',16,'bold'),
            )
            payment_header.grid(row=1,column=0,sticky='nsew',padx=5)

            payment_label = ctk.CTkLabel(
                month_frame,
                text='',
                font=ctk.CTkFont('Arial',20,'bold'),
                text_color='green'
            )
            payment_label.grid(row=2,column=0,sticky='new',padx=5)
            self.payment_labels[month_name] = payment_label
 
            bill_header = ctk.CTkLabel(
                month_frame,
                text='Gross Owed:',
                font=ctk.CTkFont('Arial',16,'bold'),
                )
            bill_header.grid(row=1,column=1,sticky='nsew',padx=5)

            bill_label = ctk.CTkLabel(
                month_frame,
                text='',
                font=ctk.CTkFont('Arial',20,'bold'),
                text_color='red'
            )
            bill_label.grid(row=2,column=1,sticky='new',padx=5)
            self.bill_labels[month_name] = bill_label


    def reset_labels(self):
        # Wipe info from labels
        self.today_header_label.configure(text='')
        self.today_payment_label.configure(text='')
        for label in self.payment_labels.values():
            label.configure(text=' \n ')

        for label in self.bill_labels.values():
            label.configure(text=' \n ')


    # Update text in labels
    def update_labels(self):
        # Wipe info from labels
        self.reset_labels()
        
        # Current year for this frame
        selected_year = self.filter_dropdowns['SESSION_YEAR'].get()
        # Get financial as of today for current session
        today_df = self.database.get_financial_as_of_today(year=selected_year)
        today_header_txt = f'Payments for {datetime.now().strftime("%b")} session as of\n {datetime.now().strftime("%b %d")}, {selected_year}:'
        self.today_header_label.configure(text=today_header_txt)
        today_payment_txt =  f'${today_df.gross_paid}\n({int(today_df.paid_student_count)} students)'
        self.today_payment_label.configure(text=today_payment_txt)

        # Get monthly financial summary for this year
        df = self.database.get_financial_summary(year=selected_year)

        for month_num, month_name in enumerate(calendar.month_name):
            # Skip over 0
            if month_num == 0: continue

            # Get row corresponding to this month
            month_df = df.loc[df['month']==month_num]
            if not month_df.empty:
                month_df = month_df.iloc[0]

                payment_txt = f'${month_df.gross_paid:,.2f}\n({int(month_df.paid_student_count)} students)'
                self.payment_labels[month_name].configure(text=payment_txt)

                bill_txt = f'${month_df.gross_owed:,.2f}\n({int(month_df.billed_student_count)} students)'
                self.bill_labels[month_name].configure(text=bill_txt)
            else:
                print(f'month_df empty for month {month_name}')

