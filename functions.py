import pandas as pd
import os
import customtkinter as ctk
from dbfread import DBF

# Function to convert a given .dbf file to .csv
def dbf_to_csv(filename, save_to_path='C:\\STMNU2\\Data'):
    # Fixed file paths for old and new programs
    main_path = 'C:\\STMNU2'
    dbase_path = 'C:\\dbase'
    gymtek_path = dbase_path + '\\gymtek'

    try:
        # Ensure that both the current directory and the 'dbase' directory
        # are located on the topmost level of C: drive
        if not os.path.isdir(main_path): raise NameError('STMNU2')
        if not os.path.isdir(dbase_path): raise NameError('dbase')
        if not os.path.isdir(gymtek_path): raise NameError('dbase\\gymtek')
        
        # Collect records from .dbf file and then convert to dataframe
        records = DBF(gymtek_path + f'\\{filename}')
        data = [record for record in records]
        df = pd.DataFrame(data)
        # Save out dataframe as .csv file
        filename_trunc = os.path.splitext(filename)[0]
        df.to_csv(f'{save_to_path}\\{filename_trunc}.csv', index=False)

    except NameError as err:
        print(f'File path C:\\{err.args[0]} does not exist')

    except UnicodeDecodeError:
        print(f'Could not convert {filename}')

def button_click():
    print("button clicked")
