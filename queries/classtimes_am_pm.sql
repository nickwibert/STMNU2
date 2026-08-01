alter table classes add column AM_PM varchar(2);

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

extracted_hours as (

    select
        et.*,
        substring(extracted_time_full, 0, instr(extracted_time_full, ':')) as extracted_hour
    from extracted_times et

),

am_pm_final as (
    select
        class_id,
        classtime,
        dayofweek,
        timeofday,
        extracted_time_full,
        case
            when cast(extracted_hour as integer) between 8 and 11
            then 'AM'
            else 'PM'
        end as am_pm
    from extracted_hours eh
    order by DAYOFWEEK, TIMEOFDAY
)

update classes 
set AM_PM = (
    select AM_PM 
    from am_pm_final 
    where class_id = classes.class_id
)
;
