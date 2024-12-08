import customtkinter as ctk
import functions as fn

# Widgets
from widgets.student_info_frame import StudentInfoFrame
from widgets.class_info_frame import ClassInfoFrame

class STMNU(ctk.CTk):
    def __init__(self, database):
        super().__init__()
        # Display startup screen
        self.title("Gymtek Student Menu")

        # StudentDatabase instance
        self.database = database

        # Loading screen
        self.geometry("400x300")
        self.load_screen = ctk.CTkFrame(self)
        self.load_screen.rowconfigure((0,1), weight=1)
        self.load_screen.grid(row=0, column=0)
        title_label = ctk.CTkLabel(self.load_screen, text='Gymtek Student Menu',
                                   font = ctk.CTkFont('Britannic', 28, 'bold'))
        loading_label = ctk.CTkLabel(self.load_screen, text='Loading...')
        title_label.grid(row=0, column=0, sticky='nsew')
        loading_label.grid(row=1, column=0, sticky='nsew')

        # Force loading screen to display
        self.update()
        # Load data and create widgets while loading screen is displayed
        self.create_main_window()

    def create_main_window(self):
        # Load data
        self.database.load_data()

        # Destroy loading screen
        self.load_screen.destroy()

        # Set-up main window
        self.geometry("1200x800")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=10)

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.columnconfigure(0,weight=1)
        self.main_frame.rowconfigure(0,weight=1)
        self.main_frame.grid(row=1,column=0, sticky='nsew')

        self.screens = {}
        # StudentInfoFrame
        self.screens['Student Info'] = StudentInfoFrame(window=self,
                                                          master=self.main_frame,
                                                          database=self.database)
        self.screens['Student Info'].grid(row=0,column=0, sticky='nsew')

        # Class Menu
        self.screens['Class Info'] = ClassInfoFrame(window=self,
                                                      master=self.main_frame,
                                                      database=self.database)
        self.screens['Class Info'].grid(row=0, column=0, sticky='nsew')

        self.tabs = ctk.CTkSegmentedButton(self, values=list(self.screens.keys()),
                                      command=self.change_view)
        self.tabs.grid(row=0,column=0)

        # Start on the student info screen
        self.active_screen = 'Student Info'
        self.tabs.set(self.active_screen)
        self.screens['Class Info'].lower()
        self.change_view(self.active_screen)

    def change_view(self, new_screen):
        # Lower active screen
        self.screens[self.active_screen].lower()
        # Set active_screen to new screen, and lift
        self.active_screen = new_screen
        self.screens[self.active_screen].lift()
        # Ensure that the menu button reflects this change
        self.tabs.set(self.active_screen)

        self.main_frame.update_idletasks()

        # Update key bindings
        self.set_binds(new_screen)

    def set_binds(self, new_screen):
        keys = ['<Return>', '<F2>', '<Prior>', '<Next>', '<Up>', '<Down>']
        for key in keys:
            self.unbind(key)

        frame = self.screens[new_screen]

        if new_screen == 'Student Info':
            self.bind('<Prior>',  lambda event: frame.buttons['PREV_STUDENT'].invoke())
            self.bind('<Up>',     lambda event: frame.buttons['PREV_STUDENT'].invoke())
            self.bind('<Next>',   lambda event: frame.buttons['NEXT_STUDENT'].invoke())
            self.bind('<Down>',   lambda event: frame.buttons['NEXT_STUDENT'].invoke())
            self.bind('<F1>',     lambda event: frame.buttons['EDIT_STUDENT'].invoke())
            self.bind('<F2>',     lambda event: frame.payment_switch.toggle())
            self.bind('<F4>',     lambda event: frame.buttons['EDIT_PAYMENT'].invoke() if frame.payment_switch.get() == 'show' else False)
            self.bind('<Return>', lambda event: frame.search_results_frame.search_button.invoke())
        elif new_screen == 'Class Info':
            self.bind('<Prior>',  lambda event: frame.search_results_frame.prev_result())
            self.bind('<Up>',     lambda event: frame.search_results_frame.prev_result())
            self.bind('<Next>',   lambda event: frame.search_results_frame.next_result())
            self.bind('<Down>',   lambda event: frame.search_results_frame.next_result())




        



