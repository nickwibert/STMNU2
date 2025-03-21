/**
idx_payment.sql - Creates unique index for `payment` table

Description:
    Unique payments are keyed by 3 columns: student ID, month, and year.
    The unique index will ensure there are never duplicate payment records.
**/

CREATE UNIQUE INDEX IF NOT EXISTS idx_payment
ON payment(STUDENT_ID, MONTH, YEAR)