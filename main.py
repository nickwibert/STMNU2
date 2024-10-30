import gui
from student_df import StudentDataFrame

def main():
   # Load student info
   students = StudentDataFrame('C:\\STMNU2\\Data\\STUD2022.csv')
   stmnu = gui.STMNU(students)
   stmnu.mainloop()

if __name__ == "__main__":
   main()