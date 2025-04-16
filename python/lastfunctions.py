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

from pandas.tseries.offsets import YearEnd
import warnings

# Global configuration
DATA_URL = 'https://www.apcs.at/apcs/clearing/lastprofile/synthload2024.zip'
DATA_DIR = './data'
ZIP_FILE = f'{DATA_DIR}/synthload2024.zip'

# Suppress matplotlib warnings
if 'plt' in globals():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        plt.show(block=True)


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
        df, kategorie) # No scaling needed here as percentage is relative
    # Ensure total_annual_energy is not zero to avoid division by zero
    if total_annual_energy == 0:
        percentage_consumed = 0.0
    else:
        # Use the scaled actual_kwh and the unscaled total_annual_energy * scaling_factor for percentage
        percentage_consumed = (actual_kwh / (total_annual_energy * scaling_factor)) * 100

    # Return a dictionary instead of a tuple
    return {
        "date": date_str,
        "kategorie": kategorie,
        "yearly_sum_used": yearly_sum,
        "daily_kwh": round(actual_kwh, 2),
        "daily_percentage_of_year": round(percentage_consumed, 2)
    }


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


def plot_day(df, dfz, date_str, kategorie, yearly_sum=1000, output='text'):
    """
    Plot daily energy distribution or return data for a specific date and category.

    Args:
        df (DataFrame): Main energy data
        dfz (DataFrame): Category metadata
        date_str (str): Date to plot (YYYY-MM-DD format)
        kategorie (str): Energy category to plot
        yearly_sum (float): Annual energy sum for scaling (default: 1000)
        output (str): Output format ('text', 'plot', or 'json')

    Returns:
        dict or None: Data dictionary if output is 'json', None otherwise.
                      Prints text or shows plot for other outputs.
    """
    # Import necessary libraries only if plotting
    if output == 'plot':
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
        except ImportError:
            print(
                "Error: matplotlib is required for plotting. Please install with 'pip install matplotlib'")
            # For JSON output, we don't strictly need matplotlib, so proceed if possible
            # If data calculation fails later, it will be caught.
            pass # Continue if not plotting

    actual_kwh_series, percentage_series, filtered_df = day_vector(
        df, date_str, kategorie, yearly_sum)

    # Get category name
    typtext = get_name_from_id(dfz, kategorie)
    if not typtext:
        # Return None or raise error? For JSON, returning structured error might be better
        if output == 'json':
             return {"error": f"Category '{kategorie}' not found in metadata"}
        else:
             print(f"Error: Category '{kategorie}' not found in metadata")
             return None # Or raise ValueError

    total_energy = round(actual_kwh_series.sum(), 2)
    # Recalculate total percentage based on the scaled total annual energy
    total_annual_energy_scaled = compute_total_annual_energy(df, kategorie) * (yearly_sum / 1000)
    if total_annual_energy_scaled == 0:
        total_percentage = 0.0
    else:
        total_percentage = round((total_energy / total_annual_energy_scaled) * 100, 2)

    # Aggregate quarter-hourly values into hourly sums
    hourly_kwh = [0.0] * 24
    hourly_percent = [0.0] * 24
    timestamps = filtered_df['ts'].dt.strftime('%H:%M:%S').tolist() # Get timestamps for JSON
    quarter_hourly_kwh = actual_kwh_series.round(4).tolist()
    quarter_hourly_percent = percentage_series.round(4).tolist()

    for i, (kwh, percent) in enumerate(zip(actual_kwh_series, percentage_series)):
        hour = i // 4
        if hour < 24: # Ensure index is within bounds
             hourly_kwh[hour] += kwh
             hourly_percent[hour] += percent

    # Round hourly values after summing
    hourly_kwh = [round(val, 2) for val in hourly_kwh]
    hourly_percent = [round(val, 4) for val in hourly_percent]

    if output == 'text':
        print(f"Daily energy consumption for {date_str} ({typtext}): {total_energy} kWh.")
        print(f"Percentage of yearly consumption: {total_percentage} %.")
        print("\nHourly Energy Values:")
        for hour in range(24):
            print(
                f"{hour:02d}:00 - {hourly_kwh[hour]:.2f} kWh ({hourly_percent[hour]:.4f}%)")
        return None # Indicate successful text output

    elif output == 'plot':
        # Visualization (ensure matplotlib was imported)
        try:
            plt.figure(figsize=(10, 6)) # Adjusted size for better readability
            # Plotting power (kW) which is energy per 15min * 4
            plt.plot(filtered_df['ts'], actual_kwh_series * 4, label=f"Power (kW)")
            plt.title(f"Energy Distribution for {date_str} ({typtext})\nTotal: {total_energy} kWh ({total_percentage}% of Year)")
            plt.xlabel("Time")
            plt.ylabel("Power (kW)")

            # Format x-axis
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=3)) # Adjust interval if needed
            plt.xticks(rotation=45)

            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show(block=True)
            return None # Indicate successful plot output
        except NameError: # Handle case where plt or mdates failed import
             print("Plotting failed due to missing matplotlib library.")
             return None

    elif output == 'json':
        # Prepare data for JSON output
        hourly_data = [
            {"hour": f"{h:02d}:00", "kwh": kwh, "percentage": percent}
            for h, (kwh, percent) in enumerate(zip(hourly_kwh, hourly_percent))
        ]
        quarter_hourly_data = [
             {"timestamp": ts, "kwh": kwh, "percentage": percent}
             for ts, kwh, percent in zip(timestamps, quarter_hourly_kwh, quarter_hourly_percent)
        ]

        return {
            "function": "plot_day",
            "parameters": {
                "date": date_str,
                "kategorie": kategorie,
                "yearly_sum": yearly_sum
            },
            "category_name": typtext,
            "summary": {
                "total_energy_kwh": total_energy,
                "total_percentage_of_year": total_percentage
            },
            "hourly_values": hourly_data,
            "quarter_hourly_values": quarter_hourly_data
        }
    else:
         # Should not happen with argparse choices, but good practice
         print(f"Error: Invalid output format '{output}'")
         return None


def plot_month(df, dfz, month_str, kategorie, yearly_sum=1000, output='text'):
    """
    Plot monthly energy distribution or return data for a specific month and category.

    Args:
        df (DataFrame): Main energy data
        dfz (DataFrame): Category metadata
        month_str (str): Month to plot (YYYY-MM format)
        kategorie (str): Energy category to plot
        yearly_sum (float): Annual energy sum for scaling (default: 1000)
        output (str): Output format ('text', 'plot', or 'json')

    Returns:
        dict or None: Data dictionary if output is 'json', None otherwise.
                      Prints text or shows plot for other outputs.
    """
    if output == 'plot':
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print(
                "Error: matplotlib is required for plotting. Please install with 'pip install matplotlib'")
            # Allow proceeding if output is not 'plot'
            pass

    try:
        period = pd.Period(month_str)
        days_in_month = pd.date_range(
            start=period.start_time, end=period.end_time, freq='D')

        category_name = get_name_from_id(dfz, kategorie)
        if not category_name:
            if output == 'json':
                return {"error": f"Category '{kategorie}' not found in metadata"}
            else:
                print(f"Error: Category '{kategorie}' not found in metadata")
                return None

        # Collect daily data
        daily_results = []
        for day in days_in_month:
            day_data = day_energy( # Use the modified day_energy
                df, day.strftime('%Y-%m-%d'), kategorie, yearly_sum)
            daily_results.append(day_data)

        # Extract kwh and percentage for calculations and potential plotting/text output
        kwh_series = [res['daily_kwh'] for res in daily_results]
        percentage_series = [res['daily_percentage_of_year'] for res in daily_results]
        day_strs = [day.strftime('%Y-%m-%d') for day in days_in_month]

        total_energy = round(sum(kwh_series), 2)
        # Recalculate total percentage based on the scaled total annual energy
        total_annual_energy_scaled = compute_total_annual_energy(df, kategorie) * (yearly_sum / 1000)
        if total_annual_energy_scaled == 0:
             total_percentage = 0.0
        else:
             total_percentage = round((total_energy / total_annual_energy_scaled) * 100, 2)

        if output == 'text':
            print(
                f"Monthly energy consumption for {month_str} ({category_name}): {total_energy} kWh.")
            print(f"Percentage of yearly consumption: {total_percentage} %.")
            print(
                f"\nDaily values for {period.strftime('%B %Y')} - {category_name}:")
            print("Date       kWh     Percentage")
            print("---------- ------- ----------")
            for i, day_str_full in enumerate(day_strs):
                day_num = day_str_full.split('-')[2] # Extract day number
                print(
                    f"{day_str_full} {kwh_series[i]:<7.2f} {percentage_series[i]:<10.2f}%")
            return None

        elif output == 'plot':
            try:
                # Create plot
                fig, ax1 = plt.subplots(figsize=(12, 6))
                ax2 = ax1.twinx()

                ax1.set_title(f"Monthly Energy Distribution for {period.strftime('%B %Y')} - {category_name}\nTotal: {total_energy} kWh ({total_percentage}% of Year)")
                ax1.bar(days_in_month, kwh_series, alpha=0.6, label='Daily kWh')
                ax2.plot(days_in_month, percentage_series,
                         color='r', marker='o', linestyle='-', label='Daily Percentage (%)')

                ax1.set_xlabel('Day of Month')
                ax1.set_ylabel('Energy (kWh)', color='b')
                ax2.set_ylabel('Percentage of Yearly Consumption (%)', color='r')
                ax1.tick_params(axis='y', labelcolor='b')
                ax2.tick_params(axis='y', labelcolor='r')

                # Format x-axis
                ax1.set_xticks(days_in_month)
                ax1.set_xticklabels([day.strftime('%d')
                                    for day in days_in_month], rotation=45, ha="right")
                ax1.xaxis.set_major_locator(plt.MaxNLocator(integer=True)) # Ensure integer ticks

                fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
                fig.tight_layout()
                plt.show(block=True)
                return None
            except NameError:
                 print("Plotting failed due to missing matplotlib library.")
                 return None

        elif output == 'json':
            # Prepare daily data for JSON
            daily_data_json = [
                {
                    "date": res["date"],
                    "kwh": res["daily_kwh"],
                    "percentage_of_year": res["daily_percentage_of_year"]
                }
                for res in daily_results
            ]
            return {
                "function": "plot_month",
                "parameters": {
                    "month": month_str,
                    "kategorie": kategorie,
                    "yearly_sum": yearly_sum
                },
                "category_name": category_name,
                "summary": {
                    "total_energy_kwh": total_energy,
                    "total_percentage_of_year": total_percentage
                },
                "daily_values": daily_data_json
            }
        else:
            print(f"Error: Invalid output format '{output}'")
            return None

    except Exception as e:
        # General error handling
        if output == 'json':
            return {"error": f"Failed to process month {month_str}: {str(e)}"}
        else:
            print(f"Error: Failed to process month {month_str}: {str(e)}")
            return None # Or raise


def plot_yearmonths(df, dfz, kategorie, year=2024, yearly_sum=1000, output='text'):
    """
    Plot monthly energy distribution for a specific year or return data.

    Args:
        df (DataFrame): Main energy data
        dfz (DataFrame): Category metadata
        kategorie (str): Energy category to plot
        year (int): Year to plot
        yearly_sum (float): Annual energy sum for scaling (default: 1000)
        output (str): Output format ('text', 'plot', or 'json')

    Returns:
        dict or None: Data dictionary if output is 'json', None otherwise.
                      Prints text or shows plot for other outputs.
    """
    if output == 'plot':
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print(
                "Error: matplotlib is required for plotting. Please install with 'pip install matplotlib'")
            pass # Allow proceeding if not plotting

    try:
        # Ensure 'Year' and 'Month' columns exist or create them safely
        if 'Year' not in df.columns or 'Month' not in df.columns:
             # Avoid modifying original df if called multiple times
             df_copy = df.copy()
             df_copy['ts'] = pd.to_datetime(df_copy['ts'])
             df_copy['Year'] = df_copy['ts'].dt.year
             df_copy['Month'] = df_copy['ts'].dt.month
             df_to_use = df_copy
        else:
             df_to_use = df

        # Filter data for the specific year and then group by month
        monthly_energy = df_to_use[df_to_use['Year'] == year].groupby('Month')[kategorie].sum()

        # Scale the energy values
        scaling_factor = yearly_sum / 1000
        monthly_energy_scaled = monthly_energy * scaling_factor

        # Get the Typtext for the kategorie
        typtext = get_name_from_id(dfz, kategorie)
        if not typtext:
            if output == 'json':
                return {"error": f"Category '{kategorie}' not found in metadata"}
            else:
                print(f"Error: Category '{kategorie}' not found in metadata")
                return None

        summed_energy = round(monthly_energy_scaled.sum(), 2)

        # Prepare month names and data for output
        month_map = {i: name for i, name in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
        monthly_data_list = []
        for month_num, energy in monthly_energy_scaled.items():
            monthly_data_list.append({
                "month_num": month_num,
                "month_name": month_map.get(month_num, "Unknown"),
                "kwh": round(energy, 2)
            })

        # Sort by month number for consistent output
        monthly_data_list.sort(key=lambda x: x['month_num'])

        if output == 'text':
            print(
                f"Monthly energy distribution for {year} ({typtext}), Scaled Total: {summed_energy:.2f} kWh (Target: {yearly_sum} kWh)")
            print("Month    kWh")
            print("-----    ------")
            for item in monthly_data_list:
                print(f"{item['month_name']:<5}    {item['kwh']:.2f}")
            print(f"\nSum of scaled monthly kWh's: {summed_energy:.2f} kWh")
            # Optional: Add assertion check for text output as well?
            # tolerance = 0.01 * yearly_sum
            # if not (yearly_sum - tolerance <= summed_energy <= yearly_sum + tolerance):
            #     print(f"Warning: Sum {summed_energy:.2f} deviates by more than 1% from target {yearly_sum:.2f} kWh.")
            return None

        elif output == 'plot':
            try:
                plt.figure(figsize=(10, 6))
                # Use the sorted data for plotting
                month_names_sorted = [item['month_name'] for item in monthly_data_list]
                kwh_values_sorted = [item['kwh'] for item in monthly_data_list]

                plt.bar(month_names_sorted, kwh_values_sorted, color='skyblue')

                plt.title(
                    f"Monthly Energy Distribution for {year} ({typtext})\nScaled Total: {summed_energy:.2f} kWh (Target: {yearly_sum} kWh)")
                plt.xlabel("Month")
                plt.xticks(rotation=45)
                plt.ylabel("Energy (kWh)")
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                plt.tight_layout()
                plt.show(block=True)
                return None
            except NameError:
                 print("Plotting failed due to missing matplotlib library.")
                 return None

        elif output == 'json':
            return {
                "function": "plot_yearmonths",
                "parameters": {
                    "year": year,
                    "kategorie": kategorie,
                    "yearly_sum": yearly_sum
                },
                "category_name": typtext,
                "summary": {
                    "total_energy_kwh": summed_energy
                },
                "monthly_values": monthly_data_list
            }
        else:
            print(f"Error: Invalid output format '{output}'")
            return None

    except Exception as e:
        if output == 'json':
            return {"error": f"Failed to process year {year} months: {str(e)}"}
        else:
            print(f"Error: Failed to process year {year} months: {str(e)}")
            return None

    # Assertion should ideally be outside the try-except or handled carefully
    # If placed here, it might not run if an exception occurred earlier.
    # Consider placing it within the 'text' and 'json' blocks if needed.
    # tolerance = 0.01 * yearly_sum
    # assert yearly_sum - tolerance <= summed_energy <= yearly_sum + tolerance, \
    #     f"Sum of monthly kWh's ({summed_energy:.2f}) does not fall within the ±1% tolerance of the provided yearly sum ({yearly_sum:.2f})."


def plot_yeardays(df, dfz, kategorie, year_str, yearly_sum=1000, output='text'):
    """
    Plot daily energy distribution for a specific year or return data.

    Args:
        df (DataFrame): Main energy data
        dfz (DataFrame): Category metadata
        kategorie (str): Energy category to plot
        year_str (str): Year to plot (YYYY format)
        yearly_sum (float): Annual energy sum for scaling (default: 1000)
        output (str): Output format ('text', 'plot', or 'json')

    Returns:
        dict or None: Data dictionary if output is 'json', None otherwise.
                      Prints text or shows plot for other outputs.
    """
    if output == 'plot':
        try:
            import matplotlib.pyplot as plt
            from pandas.tseries.offsets import YearEnd # Ensure YearEnd is available
            import matplotlib.dates as mdates # Ensure mdates is available
        except ImportError:
            print(
                "Error: matplotlib is required for plotting. Please install with 'pip install matplotlib'")
            pass # Allow proceeding if not plotting

    try:
        year = int(year_str) # Convert year_str to int for date range
        start_date = pd.Timestamp(f"{year}-01-01")
        # Ensure end_date calculation is robust
        try:
             end_date = pd.Timestamp(f"{year}-12-31")
        except ValueError: # Handle leap year if necessary, though YearEnd should work
             end_date = pd.Timestamp(f"{year}-01-01") + pd.offsets.YearEnd()

        days_in_year = pd.date_range(start_date, end_date, freq='D')

        category_name = get_name_from_id(dfz, kategorie)
        if not category_name:
            if output == 'json':
                return {"error": f"Category '{kategorie}' not found in metadata"}
            else:
                print(f"Error: Category '{kategorie}' not found in metadata")
                return None

        # Collect daily data using the modified day_energy function
        daily_results = []
        for day in days_in_year:
            day_data = day_energy(
                df, day.strftime('%Y-%m-%d'), kategorie, yearly_sum)
            daily_results.append(day_data)

        # Extract kwh and percentage for calculations and potential plotting/text output
        kwh_series = [res['daily_kwh'] for res in daily_results]
        percentage_series = [res['daily_percentage_of_year'] for res in daily_results]
        day_strs = [day.strftime('%Y-%m-%d') for day in days_in_year]

        total_yearly_kwh = round(sum(kwh_series), 2)
        # Recalculate total percentage based on the scaled total annual energy
        total_annual_energy_scaled = compute_total_annual_energy(df, kategorie) * (yearly_sum / 1000)
        if total_annual_energy_scaled == 0:
             total_yearly_percentage = 0.0
        else:
             # Summing daily percentages might not be accurate, recalculate from total kwh
             total_yearly_percentage = round((total_yearly_kwh / total_annual_energy_scaled) * 100, 2)

        if output == 'text':
            print(
                f"Yearly energy distribution for {year_str} ({category_name}), Scaled Total: {total_yearly_kwh:.2f} kWh (Target: {yearly_sum} kWh)")
            print("\nDaily Energy Values:")
            print("Date       kWh     PercentageOfYear")
            print("---------- ------- ----------------")
            for i, day_str_full in enumerate(day_strs):
                print(
                    f"{day_str_full} {kwh_series[i]:<7.2f} {percentage_series[i]:<16.2f}%")
            print(f"\nSum of scaled daily kWh's: {total_yearly_kwh:.2f} kWh")
            # Optional: Add assertion check for text output
            # tolerance = 0.01 * yearly_sum
            # if not (yearly_sum - tolerance <= total_yearly_kwh <= yearly_sum + tolerance):
            #     print(f"Warning: Sum {total_yearly_kwh:.2f} deviates by more than 1% from target {yearly_sum:.2f} kWh.")
            return None

        elif output == 'plot':
            try:
                # Data for plotting
                fig, ax1 = plt.subplots(figsize=(15, 7))
                ax2 = ax1.twinx()

                ax1.set_title(f"Daily Energy Distribution for {year_str} - {category_name}\nScaled Total: {total_yearly_kwh:.2f} kWh (Target: {yearly_sum} kWh)")
                ax1.plot(days_in_year, kwh_series, alpha=0.7, label='Daily kWh', color='blue')
                ax2.plot(days_in_year, percentage_series, alpha=0.7, label='Daily Percentage of Year (%)', color='red')

                ax1.set_xlabel('Date')
                ax1.set_ylabel('Energy (kWh)', color='blue')
                ax2.set_ylabel('Percentage of Yearly Consumption (%)', color='red')
                ax1.tick_params(axis='y', labelcolor='blue')
                ax2.tick_params(axis='y', labelcolor='red')

                # Formatting the x-axis to show months
                ax1.xaxis.set_major_locator(mdates.MonthLocator())
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                plt.xticks(rotation=45, ha="right")

                # Set Y limits dynamically
                max_kwh = max(kwh_series) if kwh_series else 1
                max_percent = max(percentage_series) if percentage_series else 1
                upper_kwh = ((max_kwh // 5) + 1) * 5 if max_kwh > 0 else 5
                upper_percent = ((max_percent // 0.1) + 1) * 0.1 if max_percent > 0 else 0.5 # Adjust scale for percentage
                ax1.set_ylim(bottom=0, top=max(upper_kwh, 1)) # Ensure limit is at least 1
                ax2.set_ylim(bottom=0, top=max(upper_percent, 0.1)) # Ensure limit is at least 0.1

                fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes)
                fig.tight_layout()
                plt.grid(True)
                plt.show(block=True)
                return None
            except NameError:
                 print("Plotting failed due to missing matplotlib library.")
                 return None

        elif output == 'json':
            # Prepare daily data for JSON
            daily_data_json = [
                {
                    "date": res["date"],
                    "kwh": res["daily_kwh"],
                    "percentage_of_year": res["daily_percentage_of_year"]
                }
                for res in daily_results
            ]
            return {
                "function": "plot_yeardays",
                "parameters": {
                    "year": year_str,
                    "kategorie": kategorie,
                    "yearly_sum": yearly_sum
                },
                "category_name": category_name,
                "summary": {
                    "total_energy_kwh": total_yearly_kwh,
                    # Add total percentage if meaningful
                    # "total_percentage_of_year": total_yearly_percentage
                },
                "daily_values": daily_data_json
            }
        else:
            print(f"Error: Invalid output format '{output}'")
            return None

    except Exception as e:
        if output == 'json':
            return {"error": f"Failed to process year {year_str} days: {str(e)}"}
        else:
            print(f"Error: Failed to process year {year_str} days: {str(e)}")
            return None

# You can call this function like so:
# result = plot_yeardays(df, dfz, 'H0', '2024', 1000, output='json')
# if result:
#     import json
#     print(json.dumps(result, indent=4))
