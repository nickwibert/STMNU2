import gui
from database import StudentDatabase

def main():
   # Load student info
   database = StudentDatabase(student_dbf_path='C:\\dbase\\gymtek\\STUD00.dbf',
                              student_prev_year_dbf_path='C:\\dbase\\gymtek\\STUD99.dbf',
                              clsbymon_dbf_path='C:\\dbase\\gymtek\\clsbymon.dbf',
                              update_active=False)
   # Initialize instance of program
   root = gui.STMNU(database)

   # Start program loop
   root.mainloop()

if __name__ == "__main__":
   main()
