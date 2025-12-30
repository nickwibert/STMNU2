import gui
from database import StudentDatabase

def main():
   # Load student info
   database = StudentDatabase()
   # Initialize instance of program
   root = gui.STMNU(database)

   # Start program maximized
   root.state('zoomed')
   # Start program loop
   root.mainloop()

if __name__ == "__main__":
   main()
