# Script to convert a Gymtek .dbf file into a .csv file
import pandas as pd
import os
from dbfread import DBF

# Fixed file paths for old and new programs
main_path = 'C:\\STMNU2'
dbase_path = 'C:\\dbase'
gymtek_path = dbase_path + '\\gymtek'

# Name of the dbf file you wish to convert
dbf_name = 'STUD2022'
# Path where you wish to save the resulting .csv file
save_to_path = main_path + '\\Data'

try:
    # Ensure that both the current directory and the 'dbase' directory
    # are located on the topmost level of C: drive
    if not os.path.isdir(main_path): raise Exception('STMNU2')
    if not os.path.isdir(dbase_path): raise Exception('dbase')
    if not os.path.isdir(gymtek_path): raise Exception('dbase\\gymtek')
    
    # Collect records from .dbf file and then convert to dataframe
    records = DBF(gymtek_path + f'\\{dbf_name}.dbf')
    data = [record for record in records]
    df = pd.DataFrame(data)
    # Save out dataframe as .csv file
    df.to_csv(f'{save_to_path}\\{dbf_name}.csv', index=False)

except Exception as err:
    print(f'File path C:\\{err.args[0]} does not exist')