/* Payment/billing summary for given session(s) */
with payment_summary as (
    select
        year,
        month,
        count(distinct student_id) as paid_student_count,
        sum(pay) as gross_paid
    from payment
    where
        year = :session_year
        -- ignore reg. fee
        and month != 13
    group by
        year,
        month
),

bill_summary as (
    select
        b.year,
        b.month,
        count(distinct b.student_id) as billed_student_count,
        sum(s.MONTHLYFEE) as gross_owed
    from bill as b
    left join student as s 
        on  b.STUDENT_ID = s.STUDENT_ID 
    where
        year = :session_year
        -- ignore reg. fee
        and month != 13
    group by
        year,
        month
)

select
    ps.year,
    ps.month,
    coalesce(ps.paid_student_count, 0) as paid_student_count,
    coalesce(ps.gross_paid, 0) as gross_paid,
    coalesce(bs.billed_student_count, 0) as billed_student_count,
    coalesce(bs.gross_owed, 0) as gross_owed
from payment_summary as ps
left join bill_summary as bs
    on  ps.year  = bs.year 
    and ps.month = bs.month