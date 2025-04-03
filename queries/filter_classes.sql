/** Used in `SearchResultsFrame.update_labels()` to determine
    the number of open spots, waitlist, and trials for 
    each class in the displayed search results **/

-- Finally, get number of trial spots, as well as class info from `classes` table
SELECT COUNTS.CLASS_ID, C.TEACH, C.CLASSTIME,
       CONCAT(SUBSTRING(C.CLASSNAME, 0, 25),'...') AS CLASSNAME,
       C.MAX - COUNTS.CLASS_COUNT AS AVAILABLE,
       COUNTS.TRIAL_COUNT,
       COUNT(W.WAIT_NO) AS WAITLIST_COUNT
FROM (
    -- Get number of waitlist spots
    SELECT CLASS_COUNTS.CLASS_ID, CLASS_COUNTS.CLASS_COUNT,
        COUNT(T.TRIAL_NO) AS TRIAL_COUNT
    FROM (
        -- Get relevant classes based on user filters, along with number of paid/billed students
        SELECT C.CLASS_ID, COUNT(PAID_OR_BILLED.STUDENT_ID) AS CLASS_COUNT
        FROM classes AS C
            LEFT JOIN class_student AS CS ON C.CLASS_ID = CS.CLASS_ID
            LEFT JOIN (
                -- Get all active students who are paid or billed for current session
                SELECT S.STUDENT_ID,
                    IIF(P.STUDENT_ID IS NULL, 0, 1) AS PAID,
                    IIF(B.STUDENT_ID IS NULL, 0, 1) AS BILLED
                FROM student AS S 
                    LEFT JOIN payment AS P ON S.STUDENT_ID = P.STUDENT_ID
                                            AND P.MONTH=:current_month AND P.YEAR=:current_year
                    LEFT JOIN bill AS B ON S.STUDENT_ID = B.STUDENT_ID
                                            AND B.MONTH=:current_month AND B.YEAR=:current_year
                WHERE S.ACTIVE AND (PAID OR BILLED)
            ) AS PAID_OR_BILLED ON CS.STUDENT_ID = PAID_OR_BILLED.STUDENT_ID
        GROUP BY C.CLASS_ID
    ) AS CLASS_COUNTS
        LEFT JOIN trial AS T ON CLASS_COUNTS.CLASS_ID = T.CLASS_ID
    GROUP BY CLASS_COUNTS.CLASS_ID
) AS COUNTS
    LEFT JOIN wait AS W ON COUNTS.CLASS_ID = W.CLASS_ID
    INNER JOIN classes AS C ON COUNTS.CLASS_ID = C.CLASS_ID
WHERE (TEACH LIKE :instructor_filter)
    AND (CLASSNAME LIKE :gender_filter)
    AND (DAYOFWEEK LIKE :day_filter)
    AND (CLASSNAME LIKE :level_filter OR CLASSTIME LIKE :level_filter)
GROUP BY C.CLASS_ID
ORDER BY DAYOFWEEK, TIMEOFDAY
COLLATE NOCASE