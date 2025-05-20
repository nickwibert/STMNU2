import customtkinter as ctk
import functions as fn

# Widgets
from widgets.class_info_frame import ClassInfoFrame
from widgets.student_info_frame import StudentInfoFrame
from widgets.family_info_frame import FamilyInfoFrame
from widgets.dialog_boxes import BackupDialog

class STMNU(ctk.CTk):
    def __init__(self, database):
        super().__init__()
        # Display startup screen
        self.title("Gymtek Student Menu")

        # StudentDatabase instance
        self.database = database

        window_width = 400
        window_height = 300
        # Calculate center coordinates
        x = int((self.winfo_screenwidth()/2) - (window_width/2))
        y = int((self.winfo_screenheight()/2) - (window_height/2))
        # Set window geometry
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)

        # Loading screen
        self.load_screen = ctk.CTkFrame(self)
        self.load_screen.columnconfigure(0,weight=1)
        self.load_screen.rowconfigure((0,1),weight=1)
        self.load_screen.grid(row=0, column=0, sticky='nsew')
        title_label = ctk.CTkLabel(self.load_screen, text='Gymtek Student Menu',
                                   font = ctk.CTkFont('Britannic', 28, 'bold'))
        loading_label = ctk.CTkLabel(self.load_screen, text='Loading...')
        title_label.grid(row=0, column=0, sticky='s')
        loading_label.grid(row=1, column=0, sticky='n')

        # Force loading screen to render
        self.update()
        # Load data and create widgets while loading screen is displayed
        self.create_main_window()

        # Exit protocol
        self.protocol("WM_DELETE_WINDOW", self.exit_program)

    def create_main_window(self):
        # Load data from dBASE program
        self.database.load_data_from_dbase()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=10)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.columnconfigure(0,weight=1)
        self.main_frame.rowconfigure(0,weight=1)

        # Create screens
        self.create_screens() 

    # Create the different screens that the user will navigate amongst
    def create_screens(self):
        self.screens = {}
        # Class Info (like the class menu from dBASE program)
        self.screens['Classes'] = ClassInfoFrame(window=self,
                                                 master=self.main_frame,
                                                 database=self.database)
        self.screens['Classes'].grid(row=0,column=0, sticky='nsew')
        # Student Info (like the screen you see in dBASE after searching for a student)
        self.screens['Students'] = StudentInfoFrame(window=self,
                                                    master=self.main_frame,
                                                    database=self.database)
        self.screens['Students'].grid(row=0,column=0, sticky='nsew')
        # # Family Info (disabled for now)
        # self.screens['Families'] = FamilyInfoFrame(window=self,
        #                                             master=self.main_frame,
        #                                             database=self.database)
        # self.screens['Families'].grid(row=0,column=0, sticky='nsew')

        # Button "menu" which user clicks to change screens
        self.tabs = ctk.CTkSegmentedButton(self,
                                           font=ctk.CTkFont('Segoe UI Light', 24),
                                           height=50,
                                           values=list(self.screens.keys()),
                                           command=self.change_view)

        # Start on the student info screen
        self.active_screen = 'Students'
        self.tabs.set(self.active_screen)
        for screen_name, screen in self.screens.items():
            if screen_name != self.active_screen:
                screen.lower()
        self.change_view(self.active_screen)

        # Bind left/right keys to flipping through screens
        self.bind('<Left>',  lambda event: self.prev_screen())
        self.bind('<Right>', lambda event: self.next_screen())

        # Destroy loading screen
        self.load_screen.destroy()
        window_width = 1300
        window_height = 900
        # Calculate center coordinates
        x = int((self.winfo_screenwidth()/2) - (window_width/2))
        y = int((self.winfo_screenheight()/2) - (window_height/2))
        # Set window geometry
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        # Place menu button and main container into grid
        self.tabs.grid(row=0,column=0,sticky='nsew')
        self.main_frame.grid(row=1,column=0, sticky='nsew')

    # Change the current view to `new_screen`
    def change_view(self, new_screen):
        # Change active screen and lift into view
        self.active_screen = new_screen
        self.screens[self.active_screen].lift()
        # Ensure that the menu button reflects this change
        self.tabs.set(self.active_screen)

        # Update key bindings
        self.set_binds(new_screen)

    def set_binds(self, new_screen):
        keys = ['<Return>', '<F1>', '<F2>', '<F3>', '<F4>', '<F5>', '<F6>', '<F7>',
                '<Prior>', '<Next>', '<Up>', '<Down>', '<Control-Home>']
        for key in keys:
            self.unbind(key)

        frame = self.screens[new_screen]

        if new_screen == 'Students':
            self.bind('<Prior>',        lambda event: frame.buttons['PREV_STUDENT'].invoke())
            self.bind('<Up>',           lambda event: frame.buttons['PREV_STUDENT'].invoke())
            self.bind('<Next>',         lambda event: frame.buttons['NEXT_STUDENT'].invoke())
            self.bind('<Down>',         lambda event: frame.buttons['NEXT_STUDENT'].invoke())
            self.bind('<F1>',           lambda event: frame.buttons['EDIT_STUDENT'].invoke())
            self.bind('<F2>',           lambda event: frame.switches['PAYMENT'].toggle())
            self.bind('<F4>',           lambda event: frame.buttons['EDIT_STUDENT_PAYMENT'].invoke() if frame.switches['PAYMENT'].get() == 'show' else False)
            self.bind('<Return>',       lambda event: frame.search_results_frame.search_button.invoke())
            self.bind('<Control-Home>', lambda event: frame.buttons['PAYMENT_YEAR'].invoke())
        elif new_screen == 'Classes':
            self.bind('<Prior>',  lambda event: frame.buttons['PREV_CLASS'].invoke())
            self.bind('<Up>',     lambda event: frame.buttons['PREV_CLASS'].invoke())
            self.bind('<Next>',   lambda event: frame.buttons['NEXT_CLASS'].invoke())
            self.bind('<Down>',   lambda event: frame.buttons['NEXT_CLASS'].invoke())
            self.bind('<F1>',     lambda event: frame.buttons['EDIT_CLASS_TRIAL'].invoke())
            self.bind('<F2>',     lambda event: frame.buttons['EDIT_CLASS_WAIT'].invoke())
            self.bind('<F3>',     lambda event: frame.buttons['EDIT_CLASS_NOTE'].invoke())
            self.bind('<F5>',     lambda event: frame.switches['AGE'].toggle())
            self.bind('<F6>',     lambda event: frame.buttons['MOVE_STUDENT'].invoke())
            self.bind('<F7>',     lambda event: frame.switches['PAYMENT'].toggle())



    def prev_screen(self):
        if self.tabs._state == 'disabled':
            return
        # Get 'index' of currently active screen (0 is leftmost screen, 1 is second screen, etc.)
        active_screen_index = list(self.screens.keys()).index(self.active_screen)
        # If we are at the first screen, jump to the last screen
        if active_screen_index == 0:
            new_screen = list(self.screens.keys())[-1]
        else:
            new_screen = list(self.screens.keys())[active_screen_index - 1]
        
        self.change_view(new_screen)

    def next_screen(self):
        if self.tabs._state == 'disabled':
            return
        # Get 'index' of currently active screen (0 is leftmost screen, 1 is second screen, etc.)
        active_screen_index = list(self.screens.keys()).index(self.active_screen)
        # If we are at the last screen, jump to first screen
        if active_screen_index == (len(self.screens.keys()) - 1):
            new_screen = list(self.screens.keys())[0]
        else:
            new_screen = list(self.screens.keys())[active_screen_index + 1]
        
        self.change_view(new_screen)


    # Function called when the user closes the main program window
    def exit_program(self):
        # Ask user if they want to backup files
        wait_var = ctk.StringVar()
        backup_dialog = BackupDialog(window=self, title='Backup Data?', wait_var=wait_var)
        self.wait_variable(wait_var)
        backup_dialog.update()

        # If user requests, backup SQLite database to CSV files in `backup_dir`
        if wait_var.get() == 'backup':
            self.database.backup_sqlite_to_csv()

        # Disconnect from SQLite database
        self.database.conn.close()

        # Destroy window/program
        self.destroy()
            




        



