import requests
import zipfile
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.tseries.offsets import YearEnd
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    plt.show(block=False)
# ------------


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


def plot_day(df, dfz, date_str, kategorie, yearly_sum=1000):
    actual_kwh_series, percentage_series, filtered_df = day_vector(
        df, date_str, kategorie, yearly_sum)

    # Get the Typtext for the kategorie
    typtext = get_name_from_id(dfz, kategorie)

    # Visualization
    plt.figure(figsize=(5, 3))

    plt.plot(filtered_df['ts'], actual_kwh_series * 4, label=f"Actual kWh")

    # This adjustment is necessary to correctly represent the energy values
    # in kilowatt-hours (kWh) per 15-minute interval.
    plt.title(f"Energy Distribution for {date_str} ({typtext})")
    plt.xlabel("Time")
    plt.ylabel("Energy (kWh)")

    # Format x-ticks to show only the hours
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)

    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show(block=False)

    total_energy = round(actual_kwh_series.sum(), 2)
    total_percentage = round(percentage_series.sum(), 2)

    return total_energy, total_percentage


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

    # Data for plotting
    fig, ax1 = plt.subplots()

    ax2 = ax1.twinx()
    ax1.set_title(
        f"{pd.Period(month_str).strftime('%B %Y')} - {category_name}")
    ax1.bar(days_in_month, kwh_series, alpha=0.6, label='Daily kWh')
    ax2.plot(days_in_month, percentage_series,
             color='r', label='Percentage (%)')

    ax1.set_xlabel('Day')
    ax1.set_ylabel('Energy (kWh)')
    ax2.set_ylabel('Percentage (%)')

    # Only display the day on the x-axis
# Display month and day on the x-axis
    ax1.set_xticks(days_in_month)  # set ticks at the specific days
    ax1.set_xticklabels(
        [day.strftime('%d') for day in days_in_month], rotation=75)

    fig.tight_layout()
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    plt.show(block=False)

    return round(sum(kwh_series), 2), round(sum(percentage_series), 2)

# Replace with your actual DataFrame and parameters
# df = your_actual_dataframe
# month_str = '2022-10'
# kategorie = some_category_variable
# yearly_sum = 1000
# plot_month(df, month_str, kategorie, yearly_sum)


def plot_yearmonths(df, dfz, kategorie, year=2024, yearly_sum=1000):
    # Filter data for the specific year and then group by month
    df['Year'] = pd.DatetimeIndex(df['ts']).year
    df['Month'] = pd.DatetimeIndex(df['ts']).month
    monthly_energy = df[df['Year'] == year].groupby('Month')[kategorie].sum()

    # Scale the energy values
    scaling_factor = yearly_sum / 1000
    monthly_energy *= scaling_factor

    # Get the Typtext for the kategorie
    typtext = get_name_from_id(dfz, kategorie)

    plt.figure(figsize=(10, 6))
    monthly_energy.plot(kind='bar', color='skyblue')

    plt.title(
        f"Monthly Energy Distribution for {year} ({typtext}), Total: {yearly_sum} kWh")
    plt.xlabel("Month")
    plt.xticks(ticks=range(12), labels=[
               'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], rotation=45)
    plt.ylabel("Energy (kWh)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show(block=False)

    # Sum of all monthly kWh values and compare to yearly_sum
    summed_energy = monthly_energy.sum()
    print(f"Sum of all monthly kWh's: {summed_energy:.2f} kWh")

    tolerance = 0.01 * yearly_sum
    assert yearly_sum - tolerance <= summed_energy <= yearly_sum + \
        tolerance, "Sum of monthly kWh's does not fall within the ±1% tolerance of the provided yearly sum."

# Assume get_name_from_id is defined, df is your DataFrame, and 'kategorie' column exists.
# plot_monthly_energy_distribution(df, 'kategorie', year=2024, yearly_sum=1000)


def plot_yeardays(df, dfz, kategorie, year_str, yearly_sum=1000):
    # Prepare to collect data
    start_date = pd.Timestamp(f"{year_str}-01-01")
    end_date = pd.Timestamp(f"{year_str}") + YearEnd()
    days_in_year = pd.date_range(start_date, end_date, freq='D')

    kwh_series = []
    percentage_series = []
    category_name = get_name_from_id(dfz, kategorie)

    # Loop through each day in the year
    for day in days_in_year:
        date_str = day.strftime('%Y-%m-%d')
        daily_kwh, daily_percentage = day_energy(
            df, date_str, kategorie, yearly_sum)
        kwh_series.append(daily_kwh)
        percentage_series.append(daily_percentage)

    # Data for plotting
    fig, ax1 = plt.subplots()

    ax2 = ax1.twinx()
    ax1.set_title(f"{year_str} - {category_name}")
    ax1.plot(days_in_year, kwh_series, alpha=0.6, label='Daily kWh')
    ax2.plot(days_in_year, percentage_series,
             color='r', label='Percentage (%)')

    ax1.set_xlabel('Day of Year')
    ax1.set_ylabel('Energy (kWh)')
    ax2.set_ylabel('Percentage (%)')

    fig.tight_layout()
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))

    plt.show(block=False)

    total_yearly_kwh = round(sum(kwh_series), 2)
    return total_yearly_kwh

# You can call this function like so:
# total_yearly_kwh = plot_year(df, dfz, '2023', 'some_kategorie', 1000)
