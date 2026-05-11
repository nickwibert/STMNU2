/* given a date parameter, return all students + emails that have been enrolled since then */
select distinct 
    s.fname, 
    s.lname,
    s.email,
    c.classtime,
    s.enrolldate
from student as s
left join class_student as cs 
    on  s.student_id = cs.student_id
left join classes as c 
    on  cs.class_id = c.class_id 
where
    -- Date mut be in YYYY-MM-DD for SQLITE "DATE" function to work
    DATE(SUBSTR(s.ENROLLDATE, 7, 4) || '-' || SUBSTR(s.ENROLLDATE, 1, 2) || '-' || SUBSTR(s.ENROLLDATE, 4, 2)) >= DATE(SUBSTR(:enrolldate_lower_bound, 7, 4) || '-' || SUBSTR(:enrolldate_lower_bound, 1, 2) || '-' || SUBSTR(:enrolldate_lower_bound, 4, 2))
;
