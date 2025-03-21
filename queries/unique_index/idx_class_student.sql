/**
idx_class_student.sql - Creates unique index for `class_student` table

Description:
    Every (CLASS_ID, STUDENT_ID) pair should be unique so that the same
    student does not appear twice in the same class.
**/

CREATE UNIQUE INDEX IF NOT EXISTS idx_class_student
ON class_student(CLASS_ID, STUDENT_ID)