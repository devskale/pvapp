import subprocess
import requests
import zipfile
import os
import pandas as pd


# ------------
def init_environment():
    url = 'https://www.apcs.at/apcs/clearing/lastprofile/synthload2024.zip'
    local_file = './data/synthload2024.zip'

    # Create 'data' folder if it doesn't exist
    if not os.path.exists('./data'):
        os.makedirs('./data')

    # Download the file
    response = requests.get(url)
    with open(local_file, 'wb') as f:
        f.write(response.content)

    # Unzip the file
    with zipfile.ZipFile(local_file, 'r') as zip_ref:
        zip_ref.extractall('./data')

    # Delete the zip file
    os.remove(local_file)

    print("Initialization complete.")


# ------------
def init_dataframes(excel_file_path):
    # Load the first row to get column names
    column_names = pd.read_excel(
        excel_file_path, header=None, nrows=1).values[0]

    # Load the data starting from row 3
    df = pd.read_excel(excel_file_path, skiprows=2, header=None)
    dfz = pd.read_excel(excel_file_path, sheet_name=1)

    # Rename columns. The first column is renamed to 'ts', and the others are renamed using values from the first row.
    df.columns = ['ts'] + list(column_names[1:])

    # Convert the 'ts' column to datetime
    df['ts'] = pd.to_datetime(df['ts'])

    # Extract the 'Year' and 'Month' from the 'ts' column
    df['Year'] = df['ts'].dt.year
    df['Month'] = df['ts'].dt.month

    return df, dfz


# ------------
# Your main srcsink function
def srcsink(df, day, src, src_kwh, sink, sink_kwh):
    # Calculate energy for source and sink
    # ...
    # Return values
    return total_used, total_not_used, perc_used, perc_powered
