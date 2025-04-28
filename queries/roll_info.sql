-- Now filter to only student IDs who are paid
SELECT ACTIVE_STUDENTS.STUDENT_ID, FNAME, LNAME, BIRTHDAY, PAY,
       IIF(P.STUDENT_ID IS NULL, 0, 1) AS PAID,
       IIF(B.STUDENT_ID IS NULL, 0, 1) AS BILLED
FROM (
    -- Get all (active) student IDs linked to this class ID
    SELECT CS.CLASS_ID, S.STUDENT_ID, S.FNAME, S.LNAME, S.BIRTHDAY
    FROM class_student AS CS
        INNER JOIN student AS S ON CS.STUDENT_ID = S.STUDENT_ID
    WHERE S.ACTIVE AND CLASS_ID=:class_id
) AS ACTIVE_STUDENTS
    LEFT JOIN payment AS P ON ACTIVE_STUDENTS.STUDENT_ID = P.STUDENT_ID
                              AND P.MONTH=:current_month AND P.YEAR=:current_year
    LEFT JOIN bill AS B ON ACTIVE_STUDENTS.STUDENT_ID = B.STUDENT_ID
                              AND B.MONTH=:current_month AND B.YEAR=:current_year
ORDER BY PAID DESC, BILLED DESC, LNAME ASC

