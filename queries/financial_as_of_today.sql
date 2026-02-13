/* Payment summary for current session / year selection as of today's date */
with payment_summary as (
    select
        year,
        month,
        count(distinct student_id) as paid_student_count,
        sum(pay) as gross_paid
    from payment
    where
        year = :session_year
        and month = strftime('%m', current_date)
        and (DATE(SUBSTR(date, 7, 4) || '-' || SUBSTR(date, 1, 2) || '-' || SUBSTR(date, 4, 2)) <= DATE(:session_year || '-' || strftime('%m',current_date) || '-' || strftime('%d',current_date)))
    group by
        year,
        month
)

select
    ps.year,
    ps.month,
    coalesce(ps.paid_student_count, 0) as paid_student_count,
    coalesce(ps.gross_paid, 0) as gross_paid
from payment_summary as ps
