import gui
from database import StudentDatabase

def main():
   # Load student info
   students = StudentDatabase('C:\\STMNU2\\data\\dbf_format\\STUD00.csv')
   # Initialize instance of program
   stmnu = gui.STMNU(students)
   # Start program loop
   stmnu.mainloop()

if __name__ == "__main__":
   main()
   