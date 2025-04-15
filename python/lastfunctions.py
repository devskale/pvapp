"""
Energy Profile Analysis Module

This module provides functions to download, process, and visualize energy consumption data
from APCS (Austrian Power Clearing and Settlement).
"""
import requests
import zipfile
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.tseries.offsets import YearEnd
import warnings

# Global configuration
DATA_URL = 'https://www.apcs.at/apcs/clearing/lastprofile/synthload2024.zip'
DATA_DIR = './data'
ZIP_FILE = f'{DATA_DIR}/synthload2024.zip'

# Suppress matplotlib warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    plt.show(block=False)


def init_environment():
    """
    Initialize the data environment by downloading and extracting the energy profile data.

    Downloads the zip file from APCS, extracts it to the data directory,
    and cleans up the zip file afterward.
    """
    # Create data directory if it doesn't exist
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Download the file
    response = requests.get(DATA_URL)
    with open(ZIP_FILE, 'wb') as f:
        f.write(response.content)

    # Unzip the file
    with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
        zip_ref.extractall(DATA_DIR)

    # Clean up
    os.remove(ZIP_FILE)
    print("Initialization complete.")


# ------------
def init_dataframes(excel_file_path):
    """
    Initialize and process the energy profile data from Excel files.

    Args:
        excel_file_path (str): Path to the Excel file containing energy data

    Returns:
        tuple: (df, dfz) where df is the main data DataFrame and dfz contains category metadata
    """
    try:
        # Load column names from first row
        column_names = pd.read_excel(
            excel_file_path, header=None, nrows=1).values[0]

        # Load main data starting from row 3
        df = pd.read_excel(excel_file_path, skiprows=2, header=None)
        dfz = pd.read_excel(excel_file_path, sheet_name=1)

        # Rename columns
        df.columns = ['ts'] + list(column_names[1:])

        # Convert and extract datetime features
        df['ts'] = pd.to_datetime(df['ts'])
        df['Year'] = df['ts'].dt.year
        df['Month'] = df['ts'].dt.month

        return df, dfz

    except Exception as e:
        raise ValueError(f"Failed to initialize dataframes: {str(e)}")


def compute_total_annual_energy(df, kategorie):
    """
    Compute and validate the total annual energy for a given category.

    Args:
        df (DataFrame): The energy data
        kategorie (str): The category column to analyze

    Returns:
        float: The rounded annual energy sum

    Raises:
        ValueError: If energy sum deviates by more than 1% from 1000 kWh
    """
    if kategorie not in df.columns:
        raise ValueError(f"Category '{kategorie}' not found in data")

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
    """
    Plot daily energy distribution for a specific date and category.

    Args:
        df (DataFrame): Main energy data
        dfz (DataFrame): Category metadata
        date_str (str): Date to plot (YYYY-MM-DD format)
        kategorie (str): Energy category to plot
        yearly_sum (float): Annual energy sum for scaling (default: 1000)

    Returns:
        tuple: (total_energy, total_percentage) for the day
    """
    actual_kwh_series, percentage_series, filtered_df = day_vector(
        df, date_str, kategorie, yearly_sum)

    # Get category name
    typtext = get_name_from_id(dfz, kategorie)
    if not typtext:
        raise ValueError(f"Category '{kategorie}' not found in metadata")

    # Visualization
    plt.figure(figsize=(5, 3))
    plt.plot(filtered_df['ts'], actual_kwh_series * 4, label=f"Actual kWh")
    plt.title(f"Energy Distribution for {date_str} ({typtext})")
    plt.xlabel("Time")
    plt.ylabel("Energy (kWh)")

    # Format x-axis
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)

    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show(block=True)
    return round(actual_kwh_series.sum(), 2), round(percentage_series.sum(), 2)


def plot_month(df, dfz, month_str, kategorie, yearly_sum=1000):
    """
    Plot monthly energy distribution for a specific month and category.

    Args:
        df (DataFrame): Main energy data
        dfz (DataFrame): Category metadata
        month_str (str): Month to plot (YYYY-MM format)
        kategorie (str): Energy category to plot
        yearly_sum (float): Annual energy sum for scaling (default: 1000)

    Returns:
        tuple: (total_energy, total_percentage) for the month
    """
    try:
        period = pd.Period(month_str)
        days_in_month = pd.date_range(
            month_str, periods=period.days_in_month, freq='D')

        category_name = get_name_from_id(dfz, kategorie)
        if not category_name:
            raise ValueError(f"Category '{kategorie}' not found in metadata")

        # Collect daily data
        kwh_series = []
        percentage_series = []
        for day in days_in_month:
            daily_kwh, daily_percentage = day_energy(
                df, day.strftime('%Y-%m-%d'), kategorie, yearly_sum)
            kwh_series.append(daily_kwh)
            percentage_series.append(daily_percentage)

        # Create plot
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()

        ax1.set_title(f"{period.strftime('%B %Y')} - {category_name}")
        ax1.bar(days_in_month, kwh_series, alpha=0.6, label='Daily kWh')
        ax2.plot(days_in_month, percentage_series,
                 color='r', label='Percentage (%)')

        ax1.set_xlabel('Day')
        ax1.set_ylabel('Energy (kWh)')
        ax2.set_ylabel('Percentage (%)')

        # Format x-axis
        ax1.set_xticks(days_in_month)
        ax1.set_xticklabels([day.strftime('%d')
                            for day in days_in_month], rotation=75)

        fig.tight_layout()
        fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
        plt.show(block=True)

        return round(sum(kwh_series), 2), round(sum(percentage_series), 2)

    except Exception as e:
        raise ValueError(f"Failed to plot month {month_str}: {str(e)}")

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
    plt.show(block=True)

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
    # Round up to next multiple of 5

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
    max_kwh = max(kwh_series)
    max_percent = max(percentage_series)
    upper_kwh = ((max_kwh // 5) + 1) * 5
    upper_percent = ((max_percent // 1) + 1) * 1
    ax1.set_ylim(bottom=0, top=upper_kwh)
    ax2.set_ylim(bottom=0, top=upper_percent)

    fig.tight_layout()
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))

    plt.show(block=False)

    total_yearly_kwh = round(sum(kwh_series), 2)
    return total_yearly_kwh

# You can call this function like so:
# total_yearly_kwh = plot_year(df, dfz, '2023', 'some_kategorie', 1000)
