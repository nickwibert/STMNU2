import customtkinter as ctk
import functions as fn
import widgets as w

class STMNU(ctk.CTk):
    def __init__(self, students):
        super().__init__()
        self.geometry("300x350")
        self.title("Gymtek Student Menu")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # StudentDataFrame instance
        self.students = students

        self.main_frame = w.MyFrame(self)
        self.main_frame.grid(row=0,column=0)

        # Add widgets
        self.stud_info_button = ctk.CTkButton(
                                    self.main_frame,
                                    text="Student Info",
                                    command=self.display_student_info)
        self.bind('<F1>', lambda event: self.display_student_info())
        self.new_stud_button= ctk.CTkButton(
                                    self.main_frame,
                                    text="New Student",
                                    command=fn.button_click)
        self.class_menu_button = ctk.CTkButton(
                                    self.main_frame,
                                    text="Class Menu",
                                    command=fn.button_click)
        
        # Place in grid
        self.stud_info_button.grid(row=0, column=0, padx=20, pady=10)
        self.new_stud_button.grid(row=1, column=0, padx=20, pady=10)
        self.class_menu_button.grid(row=2, column=0, padx=20, pady=10)


    # Display student info in a pop-up window (if match found)
    def display_student_info(self):
        # Create window
        self.student_info_window = w.StudentInfoWindow(self, self.students, height=500, width=600)
        # Focus window
        self.student_info_window.after(10, self.student_info_window.lift)
        self.student_info_window.after(10, self.student_info_window.focus)


        



