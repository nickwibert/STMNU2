
with classes_base as (
    select distinct CLASS_ID, CLASSNAME
    from classes
),

classes_std as (
    select
        class_id, 
        classname,
        case 
            when CLASSNAME like '%BOY%BEG%'
                then 'BOY''S BEGINNER GYMNASTICS (6&UP)'
            when CLASSNAME like '%BOY%ADV%'
                then 'BOY''S ADVANCED GYMNASTICS (6&UP)'
            when CLASSNAME like '%FUNTASTIK%3%4%'
                then 'FUNTASTIKS (3-4YRS)'
            when CLASSNAME like '%FUNTASTIK%4%5%'
                then 'FUNTASTIKS (4-5YRS)'
            when CLASSNAME like '%FUNTASTIK%4%6%'
                then 'FUNTASTIKS (4-6YRS)'
            when CLASSNAME like '%GIRL%BEG%ADV%'
                then 'GIRL''S BEG-ADV TUMBLING (8&UP)'
            when CLASSNAME like '%GIRL%BEG%'
                then 'GIRL''S BEGINNER GYMNASTICS (6&UP)'
            when CLASSNAME like '%GIRL%INT%ADV%'
                then 'GIRL''S INT-ADV GYMNASTICS (6&UP)'
            when CLASSNAME like '%GIRL%INT%'
                then 'GIRL''S INTERMEDIATE GYMNASTICS (6&UP)'
            when CLASSNAME like '%GIRL%ADV%'
                then 'GIRL''S ADVANCED GYMNASTICS (6&UP)'
            WHEN CLASSNAME LIKE '%HOME%'
                THEN 'HOMESCHOOL (6&UP)'
            WHEN CLASSNAME LIKE '%PARENT%18%'
                THEN 'PARENT & TOT (18MO-2YRS)'
            WHEN CLASSNAME LIKE '%PARENT%2%3%'
                THEN 'PARENT & TOT (2-3YRS)'
            ELSE CLASSNAME
        end as classname_std
    from classes_base 
    order by classname
)

update classes 
set CLASSNAME = (
    select CLASSNAME_STD 
    from classes_std
    where class_id = classes.class_id
)
;


select * from classes;