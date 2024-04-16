import requests
import zipfile
import os
import pandas as pd



def init_environment():
    #    print(
    #        f"The current function name is {inspect.currentframe().f_code.co_name}")

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
    #    print(
    #        f"The current function name is {inspect.currentframe().f_code.co_name}")

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


def compute_total_annual_energy(df, kategorie):
    energy_sum = df[kategorie].sum()

    if 990 <= energy_sum <= 1010:
        return round(energy_sum, 2)
    else:
        raise ValueError(
            f"The annual energy for {kategorie} deviates by more than 1% from 1000 kWh. Computed sum: {energy_sum} kWh")


def get_name_from_id(dfz, id_value):
    filtered_df = dfz[dfz['Typname'] == id_value]

    if len(filtered_df) == 0:
        return None  # or some default value
    else:
        return filtered_df.iloc[0]['Typtext']


def day_energy(df, date_str, kategorie, yearly_sum=1000):
    scaling_factor = yearly_sum / 1000
    specific_date = pd.to_datetime(date_str)
    filtered_df = df[df['ts'].dt.date == specific_date.date()]

    actual_kwh = filtered_df[kategorie].sum() * scaling_factor

    total_annual_energy = compute_total_annual_energy(
        df, kategorie) * scaling_factor
    percentage_consumed = (
        actual_kwh / total_annual_energy) * 100

    return round(actual_kwh, 2), round(percentage_consumed, 2)


def day_vector(df, date_str, kategorie, yearly_sum=1000):
    specific_date = pd.to_datetime(date_str)
    filtered_df = df[df['ts'].dt.date == specific_date.date()]

    scaling_factor = yearly_sum / 1000
    actual_kwh_series = filtered_df[kategorie] * \
        scaling_factor  # Include scaling here
    total_annual_energy = compute_total_annual_energy(df, kategorie)
    total_annual_energy *= scaling_factor  # Adjust the total annual energy
    percentage_series = (actual_kwh_series / total_annual_energy) * 100
#    print(f"Length of actual_kwh_series: {len(actual_kwh_series)}")

    return actual_kwh_series, percentage_series, filtered_df


def plot_month(df, dfz, month_str, kategorie, yearly_sum=1000):
    # Prepare to collect data
    days_in_month = pd.date_range(
        month_str, periods=pd.Period(month_str).days_in_month, freq='D')
    kwh_series = []
    percentage_series = []
    category_name = get_name_from_id(dfz, kategorie)

    # Loop through each day in the month
    for day in days_in_month:
        date_str = day.strftime('%Y-%m-%d')
        daily_kwh, daily_percentage = day_energy(
            df, date_str, kategorie, yearly_sum)
        kwh_series.append(daily_kwh)
        percentage_series.append(daily_percentage)

    return round(sum(kwh_series), 2), round(sum(percentage_series), 2)