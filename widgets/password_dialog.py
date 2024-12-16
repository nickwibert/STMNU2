import customtkinter as ctk

# Custom dialog box created by slightly modifying source code for 'CTkInputDialog'.
# I needed the text in the entry box to be hidden and could not modify the EntryBox
# within CTkInputDialog object, so needed to create a custom version.
class PasswordDialog(ctk.CTkToplevel):
    def __init__(self, window, title, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title = title
        self._text = text

        self.title(self._title)
        self.lift()  # lift window on top
        self.attributes("-topmost", True)  # stay on top
        self.protocol("WM_DELETE_WINDOW", self._ok_event)
        self.after(10, self._create_widgets)  # create widgets with slight delay, to avoid white flickering of background
        self.resizable(False, False)
        self.grab_set()  # make other windows not clickable

        # Set location of window relative to the main window
        window_x, window_y = (window.winfo_x(), window.winfo_y())
        x, y = (window_x + (window.winfo_width()*0.66), window_y + (window.winfo_height()*0.1))
        self.geometry(f'+{round(x)}+{round(y)}')

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._label = ctk.CTkLabel(master=self,
                               width=230,
                               wraplength=150,
                               fg_color="transparent",
                               text=self._text)
        self._label.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self._entry = ctk.CTkEntry(master=self,
                                   show='*',
                                   width=100)
        self._entry.grid(row=1, column=0, padx=20, pady=(0, 20))

        self._ok_button = ctk.CTkButton(master=self,
                                    width=100,
                                    border_width=0,
                                    text='Enter',
                                    command=self._ok_event)
        self._ok_button.grid(row=2, column=0, padx=(20, 10), pady=(0, 20))

        self.after(150, lambda: self._entry.focus())  # set focus to entry with slight delay, otherwise it won't work
        self._entry.bind("<Return>", self._ok_event)

    def _ok_event(self, event=None):
        self._user_input = self._entry.get()
        self.grab_release()
        self.destroy()

    def get_input(self):
        self.master.wait_window(self)
        return self._user_input
