-- Run this snippet to view all unique indices that currently exist in database
SELECT TYPE, NAME, TBL_NAME, SQL
FROM sqlite_master
WHERE TYPE='index'