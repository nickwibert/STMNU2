/**
This query contains the necessary CREATE statements
to create all of the database tables used in this program.
Note that this query simply defines fields and datatypes
for each table, and does not populate them with any data.
**/

/** Create student table **/
CREATE TABLE IF NOT EXISTS student (
    STUDENT_ID  INTEGER PRIMARY KEY     AUTOINCREMENT,
    FAMILY_ID   INTEGER,
    ACTIVE      INTEGER,
    CLASS       TEXT,
    STUDENTNO   INTEGER,
    FNAME       TEXT,
    LNAME       TEXT,
    BIRTHDAY    TEXT,
    ENROLLDATE  TEXT,
    MONTHLYFEE  REAL,
    BALANCE     REAL,
    PHONE       TEXT,
    EMAIL       TEXT,
    ADDRESS     TEXT,
    CITY        TEXT,
    STATE       TEXT,
    ZIP         INTEGER,
    CREA_TMS    TEXT,
    UPDT_TMS    TEXT
);

/** Create guardian table **/
CREATE TABLE IF NOT EXISTS guardian (
    GUARDIAN_ID INTEGER PRIMARY KEY     AUTOINCREMENT,
    FAMILY_ID   INTEGER,
    RELATION    TEXT,
    FNAME       TEXT,
    LNAME       TEXT,
    PHONE       TEXT,
    EMAIL       TEXT,
    CREA_TMS    TEXT,
    UPDT_TMS    TEXT,
    UNIQUE (FAMILY_ID, RELATION)
);

/** Create payment table **/
CREATE TABLE IF NOT EXISTS payment (
    STUDENT_ID  INTEGER,
    MONTH       INTEGER,
    YEAR        INTEGER,
    PAY         REAL,
    DATE        TEXT,
    UNIQUE (STUDENT_ID, MONTH, YEAR)
);

/** Create bill table **/
CREATE TABLE IF NOT EXISTS bill (
    STUDENT_ID  INTEGER,
    MONTH       INTEGER,
    YEAR        INTEGER,
    UNIQUE (STUDENT_ID, MONTH, YEAR)
);

/** Create class_student table **/
CREATE TABLE IF NOT EXISTS class_student (
    CLASS_ID    INTEGER,
    STUDENT_ID  INTEGER,
    UNIQUE (CLASS_ID, STUDENT_ID)
);

/** Create note table **/
CREATE TABLE IF NOT EXISTS note (
    CLASS_ID    INTEGER,
    STUDENT_ID  INTEGER,
    NOTE_TXT    TEXT,
    CREA_TMS    TEXT,
    UPDT_TMS    TEXT,
    UNIQUE (CLASS_ID, STUDENT_ID)
);

/** Create classes table **/
CREATE TABLE IF NOT EXISTS classes (
    CLASS_ID    INTEGER PRIMARY KEY     AUTOINCREMENT,
    SESSION     TEXT,
    TEACH       TEXT,
    TEACH2      TEXT,
    DAYOFWEEK   INTEGER,
    TIMEOFDAY   TEXT,
    CLASSTIME   TEXT,
    SECONDTIME  TEXT,
    CODE        TEXT,
    CLASSNAME   TEXT,
    MAX         INTEGER,
    AVAILABLE   INTEGER,
    CREA_TMS    TEXT,
    UPDT_TMS    TEXT
);

/** Create waitlist table **/
CREATE TABLE IF NOT EXISTS wait (
    CLASS_ID    INTEGER,
    WAIT_NO     INTEGER,
    NAME        TEXT,
    PHONE       TEXT,
    CREA_TMS    TEXT,
    UPDT_TMS    TEXT,
    UNIQUE (CLASS_ID, WAIT_NO)
);

/** Create trial table **/
CREATE TABLE IF NOT EXISTS trial (
    CLASS_ID    INTEGER,
    TRIAL_NO     INTEGER,
    NAME        TEXT,
    PHONE       TEXT,
    DATE        TEXT,
    CREA_TMS    TEXT,
    UPDT_TMS    TEXT,
    UNIQUE (CLASS_ID, TRIAL_NO)
);

/** Create makeup table **/
CREATE TABLE IF NOT EXISTS makeup (
    CLASS_ID    INTEGER,
    MAKEUP_NO   INTEGER,
    NAME        TEXT,
    DATE        TEXT,
    CREA_TMS    TEXT,
    UPDT_TMS    TEXT,
    UNIQUE (CLASS_ID, MAKEUP_NO)
);

