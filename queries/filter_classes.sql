/** Used in `SearchResultsFrame.update_labels()` to determine
    the number of open spots, waitlist, and trials for 
    each class in the displayed search results **/
with 

time_start_index as (
    select 
        class_id,
        DAYOFWEEK,
        TIMEOFDAY,
        CLASSTIME,
        CLASSNAME,
        MIN(
            CASE WHEN instr(classtime, '0') > 0 THEN instr(classtime, '0') ELSE 999 END,                
            CASE WHEN instr(classtime, '1') > 0 THEN instr(classtime, '1') ELSE 999 END,                
            CASE WHEN instr(classtime, '2') > 0 THEN instr(classtime, '2') ELSE 999 END,                
            CASE WHEN instr(classtime, '3') > 0 THEN instr(classtime, '3') ELSE 999 END,                
            CASE WHEN instr(classtime, '4') > 0 THEN instr(classtime, '4') ELSE 999 END,                
            CASE WHEN instr(classtime, '5') > 0 THEN instr(classtime, '5') ELSE 999 END,                
            CASE WHEN instr(classtime, '6') > 0 THEN instr(classtime, '6') ELSE 999 END,                
            CASE WHEN instr(classtime, '7') > 0 THEN instr(classtime, '7') ELSE 999 END,                
            CASE WHEN instr(classtime, '8') > 0 THEN instr(classtime, '8') ELSE 999 END,                
            CASE WHEN instr(classtime, '9') > 0 THEN instr(classtime, '9') ELSE 999 END
        ) as first_digit_index,
        instr(classtime,':') as colon_index
    FROM classes
    GROUP BY 
        class_id, DAYOFWEEK, TIMEOFDAY, CLASSTIME, CLASSNAME
),

extracted_times as (

    select
        time_start_index.*,
        substring(classtime, first_digit_index) as extracted_time_full
    from time_start_index

),

extracted_hour_minute as (

    select
        et.*,
        cast(substring(extracted_time_full, 0, instr(extracted_time_full, ':')) as INTEGER) as extracted_hour,
        cast(substring(extracted_time_full, instr(extracted_time_full, ':')+1, 999) as INTEGER) as extracted_minute
    from extracted_times et

)

-- Finally, get number of trial spots, as well as class info from `classes` table
SELECT
    COUNTS.CLASS_ID,
    C.TEACH,
    C.CLASSTIME,
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
    LEFT JOIN extracted_hour_minute as EHM ON C.CLASS_ID = EHM.CLASS_ID
WHERE (C.TEACH LIKE :instructor_filter)
    AND (C.CLASSNAME LIKE :gender_filter)
    AND (C.DAYOFWEEK LIKE :day_filter)
    AND (C.CLASSNAME LIKE :level_filter OR C.CLASSTIME LIKE :level_filter)
GROUP BY C.CLASS_ID
-- sort using extracted times from CLASSTIME field
ORDER BY
    C.DAYOFWEEK,
    CASE AM_PM 
        WHEN 'AM' THEN 
            CASE WHEN EHM.extracted_hour = 12 THEN 0 ELSE EHM.extracted_hour END
        WHEN 'PM' THEN 
            CASE WHEN EHM.extracted_hour = 12 THEN 12 ELSE EHM.extracted_hour + 12 END
    END ASC,
    EHM.extracted_minute,
    C.CLASSNAME
COLLATE NOCASE