

-- Now filter to only student IDs who are paid
SELECT P.STUDENT_ID, FNAME, LNAME, BIRTHDAY, PAY, (PAY > 0) AS PAID
FROM (
    -- Get all (active) student IDs linked to this class ID
    SELECT CS.CLASS_ID, S.STUDENT_ID, S.FNAME, S.LNAME, S.BIRTHDAY
    FROM class_student AS CS
        INNER JOIN student AS S ON CS.STUDENT_ID = S.STUDENT_ID
    WHERE S.ACTIVE AND CLASS_ID = 38
) AS ACTIVE_STUDENTS
    LEFT JOIN payment AS P ON ACTIVE_STUDENTS.STUDENT_ID = P.STUDENT_ID
    LEFT JOIN bill AS B ON ACTIVE_STUDENTS.STUDENT_ID = B.STUDENT_ID
                           AND P.MONTH = B.MONTH
                           AND P.YEAR = B.YEAR
WHERE (P.MONTH = 3 AND P.YEAR = 2025) OR (B.MONTH=3 AND B.YEAR=2025)


/**
roll_info = self.database.class_student[(self.database.class_student['CLASS_ID'] == class_id)
                    ].merge(self.database.student[self.database.student['ACTIVE']],
                            how='inner',
                            on='STUDENT_ID'
                    ).merge(self.database.payment[((self.database.payment['MONTH'] == CURRENT_SESSION.month)
                                                    & (self.database.payment['YEAR'] == CURRENT_SESSION.year))],
                            how='left',
                            on='STUDENT_ID'
                    ).loc[:,['PAY','STUDENT_ID','FAMILY_ID','FNAME','LNAME','BIRTHDAY']]
# Create 'PAID' which is true if student has a non-zero payment for the current month/year
roll_info['PAID'] = roll_info['PAY'] > 0
# Get `bill_info` as all the bill records for students in `roll_info`
bill_info = self.database.bill.merge(roll_info, how='inner', on='STUDENT_ID'
                                ).loc[:,['STUDENT_ID','MONTH','YEAR']]
# Create 'BILLED' which is true if student has been billed for the current month/year
# (since they have a bill record, someone has confirmed that the student
# is attending and plans to pay; therefore they will take up a spot in the class)
roll_info['BILLED'] = roll_info['STUDENT_ID'].isin(bill_info.loc[((bill_info['MONTH']==CURRENT_SESSION.month)
                                                                    &(bill_info['YEAR']==CURRENT_SESSION.year)),'STUDENT_ID'].values)
roll_info = roll_info.sort_values(by=['PAID','BILLED','LNAME'], ascending=[False,False,True]
                    ).reset_index(drop=True)
**/
