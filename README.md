# Gymtek Student Menu V2

Gymtek Gymnastic Center is a small business which has relied on a dBASE program (written by the owner) since the late 1980s to function as a student database. The project hosted here is a simple Tkinter/CustomTkinter GUI that I built as a full remake of the original program, custom-made to mimic the functionality with which its users are familiar while offering a more streamlined way for the user to interact with the program.

This project also uses [Ethan Furman's DBF package](https://github.com/ethanfurman/dbf) for reading/writing DBF files that function with the original dBASE program. Much of the work for this project came from the need to ensure that any and all changes made in the new program will be reflected in the old program as well (at the request of the owner), and I relied exclusively on this package for dealing with the maintenance of DBF files.

Note: the project is published here with consent of Gymtek's owner to serve as part of my portfolio. All of the company's sensitive data and information is excluded from this project, and indeed the project cannot be run on any other machine besides mine and the business's due to essential files (mainly the above-mentioned DBF files) being excluded from this repository. The project is hosted here purely to serve as part of my coding portfolio. Please refer to the information below, as well as comments within the code itself, for explanations on what the program does.

## Database Structure
The original dBASE program relies primarily on four different tables (`.dbf` files):
  1. Current-year students
  2. Previous-year students
  3. Current-month classes
  4. Previous-month classes

Tables 1 and 2 above contain each gymnastic student's personal information, their parents' information, and all of the payments made for that student in the given year (represented as fields like `JANPAY`, `FEBPAY`, etc.). Tables 3 and 4 have a similar structure, with information for a given class as well as all of the students enrolled in said class (represented as fields like `STUDENT1`, `STUDENT2`, etc.).

For the new program, I decided to represent the data using a relational database structure. For the relatively small amount of data involved in this program, I don't think this new structure will make much difference in terms of efficiency, but it was much more efficient for me to write Python code when the data was represented this way. The new database structure contains the following tables:
  1. `student`
     * Contains the student's personal information, along with a primary key and relevant foreign keys (i.e. `FAMILY_ID`)
  2. `guardian`
     * Contains information for guardians, which can be linked back to students via `FAMILY_ID`
  3. `payment`
     * Contains payment information for a given student and session (month/year) such that each record corresponds to a single payment
  4. `bill`
     * Contains bill information for a given student and session (month/year) such that each record corresponds to a single bill
  5. `classes`
     * Contains basic information for a class like instructor, classtime, etc. along with a primary key
  6. `class_student`
     * Simply contains two fields representing primary keys from `student` and `classes` to link each student with the class in which they are enrolled
  7. `waitlist`
     * Children on a waitlist to enter a given class
  8. `trial`
     * Children who are doing a trial for a given class
  9. `makeup`
     * Each record corresponds to a student performing a makeup for a missed class
  10. `note`\
     * Each record corresponds to a note created by the user, which may correspond to either a class (`CLASS_ID` is not null) or a student (`STUDENT_ID` is not null)

The biggest challenge in the new program was to make changes to these new RDB style tables during runtime while making sure to update the DBF tables as well. The file `database.py` functions mostly as an interface between these two database representations, and throughout it you will see that most of the functions are split into two chunks to first make a necessary change in the RDB representation, and then apply that same change to the DBF files.

At the moment, I maintain the RDB style tables as `.csv` files. My experience is focused on database reporting and data analytics, so while I am familiar with writing queries this was my first time taking a crack at designing a database. Due to the small amount of data, and my limited experience, using `.csv` files was a quicker solution to get the software up and running as soon as possible in the business. I am currently reworking the code to utilize SQLite instead for real-time database functionality (see the `sqlite` branch). In the meantime, the `.csv` files are reconstructed every time the program is run by reading in data from the `.dbf` files, and those same `.dbf` files are modified in real-time by this program, so there is no opportunity for data loss. 

## Graphical User Interface (GUI)
Using Tkinter and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), I created a simple GUI that mimics the layout of the original program. The biggest change in my GUI is to replace function-key operations with simple and intuitive buttons which the user can click. The new program still supports many of the function-key operations present in the original program so that when a seasoned user hits keys due to muscle-memory, the program will still respond as expected.

### Searching for Students/Classes
