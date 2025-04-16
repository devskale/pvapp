"""
Energy Profile Analysis Module

This module provides functions to download, process, and visualize energy consumption data
from APCS (Austrian Power Clearing and Settlement).
"""
import requests
import zipfile
import os
import pandas as pd

# Global configuration
DATA_URL = 'https://www.apcs.at/apcs/clearing/lastprofile/synthload2024.zip'
DATA_DIR = './data'
ZIP_FILE = f'{DATA_DIR}/synthload2024.zip'


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
        df, kategorie)  # No scaling needed here as percentage is relative
    # Ensure total_annual_energy is not zero to avoid division by zero
    if total_annual_energy == 0:
        percentage_consumed = 0.0
    else:
        # Use the scaled actual_kwh and the unscaled total_annual_energy * scaling_factor for percentage
        percentage_consumed = (
            actual_kwh / (total_annual_energy * scaling_factor)) * 100

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
    plt = None
    mdates = None
    if output == 'plot':
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
        except ImportError:
            print(
                "Error: matplotlib is required for plotting. Please install with 'pip install matplotlib'")
            return None  # Cannot plot

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
            return None  # Or raise ValueError

    total_energy = round(actual_kwh_series.sum(), 2)
    # Recalculate total percentage based on the scaled total annual energy
    total_annual_energy_scaled = compute_total_annual_energy(
        df, kategorie) * (yearly_sum / 1000)
    if total_annual_energy_scaled == 0:
        total_percentage = 0.0
    else:
        total_percentage = round(
            (total_energy / total_annual_energy_scaled) * 100, 2)

    # Aggregate quarter-hourly values into hourly sums
    hourly_kwh = [0.0] * 24
    hourly_percent = [0.0] * 24
    timestamps = filtered_df['ts'].dt.strftime(
        '%H:%M:%S').tolist()  # Get timestamps for JSON
    quarter_hourly_kwh = actual_kwh_series.round(4).tolist()
    quarter_hourly_percent = percentage_series.round(4).tolist()

    for i, (kwh, percent) in enumerate(zip(actual_kwh_series, percentage_series)):
        hour = i // 4
        if hour < 24:  # Ensure index is within bounds
            hourly_kwh[hour] += kwh
            hourly_percent[hour] += percent

    # Round hourly values after summing
    hourly_kwh = [round(val, 2) for val in hourly_kwh]
    hourly_percent = [round(val, 4) for val in hourly_percent]

    if output == 'text':
        print(
            f"Daily energy consumption for {date_str} ({typtext}): {total_energy} kWh.")
        print(f"Percentage of yearly consumption: {total_percentage} %.")
        print("\nHourly Energy Values:")
        for hour in range(24):
            print(
                f"{hour:02d}:00 - {hourly_kwh[hour]:.2f} kWh ({hourly_percent[hour]:.4f}%)")
        return None  # Indicate successful text output

    elif output == 'plot':
        # Visualization (ensure matplotlib was imported)
        if plt is None or mdates is None:
            # This case should be handled by the import check already, but as a safeguard:
            print("Plotting skipped due to missing matplotlib library or import error.")
            return None
        try:
            fig, ax = plt.subplots(figsize=(10, 6))  # Use fig, ax pattern
            # Plotting power (kW) which is energy per 15min * 4
            ax.plot(filtered_df['ts'], actual_kwh_series *
                    4, label=f"Power (kW)")
            ax.set_title(
                f"Energy Distribution for {date_str} ({typtext})\nTotal: {total_energy} kWh ({total_percentage}% of Year)")
            ax.set_xlabel("Time")
            ax.set_ylabel("Power (kW)")

            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
            plt.setp(ax.get_xticklabels(), rotation=45,
                     ha="right")  # Use plt.setp

            ax.legend()
            ax.grid(True)
            fig.tight_layout()
            plt.show(block=True)
            return None  # Indicate successful plot output
        except Exception as e:  # Catch potential plotting errors
            print(f"Plotting failed: {e}")
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
    plt = None
    if output == 'plot':
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print(
                "Error: matplotlib is required for plotting. Please install with 'pip install matplotlib'")
            return None  # Cannot plot

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
            day_data = day_energy(  # Use the modified day_energy
                df, day.strftime('%Y-%m-%d'), kategorie, yearly_sum)
            daily_results.append(day_data)

        # Extract kwh and percentage for calculations and potential plotting/text output
        kwh_series = [res['daily_kwh'] for res in daily_results]
        percentage_series = [res['daily_percentage_of_year']
                             for res in daily_results]
        day_strs = [day.strftime('%Y-%m-%d') for day in days_in_month]

        total_energy = round(sum(kwh_series), 2)
        # Recalculate total percentage based on the scaled total annual energy
        total_annual_energy_scaled = compute_total_annual_energy(
            df, kategorie) * (yearly_sum / 1000)
        if total_annual_energy_scaled == 0:
            total_percentage = 0.0
        else:
            total_percentage = round(
                (total_energy / total_annual_energy_scaled) * 100, 2)

        if output == 'text':
            print(
                f"Monthly energy consumption for {month_str} ({category_name}): {total_energy} kWh.")
            print(f"Percentage of yearly consumption: {total_percentage} %.")
            print(
                f"\nDaily values for {period.strftime('%B %Y')} - {category_name}:")
            print("Date       kWh     Percentage")
            print("---------- ------- ----------")
            for i, day_str_full in enumerate(day_strs):
                day_num = day_str_full.split('-')[2]  # Extract day number
                print(
                    f"{day_str_full} {kwh_series[i]:<7.2f} {percentage_series[i]:<10.2f}%")
            return None

        elif output == 'plot':
            if plt is None:
                print(
                    "Plotting skipped due to missing matplotlib library or import error.")
                return None
            try:
                # Create plot
                fig, ax1 = plt.subplots(figsize=(12, 6))
                ax2 = ax1.twinx()

                ax1.set_title(
                    f"Monthly Energy Distribution for {period.strftime('%B %Y')} - {category_name}\nTotal: {total_energy} kWh ({total_percentage}% of Year)")
                ax1.bar(days_in_month, kwh_series,
                        alpha=0.6, label='Daily kWh')
                ax2.plot(days_in_month, percentage_series,
                         color='r', marker='o', linestyle='-', label='Daily Percentage (%)')

                ax1.set_xlabel('Day of Month')
                ax1.set_ylabel('Energy (kWh)', color='b')
                ax2.set_ylabel(
                    'Percentage of Yearly Consumption (%)', color='r')
                ax1.tick_params(axis='y', labelcolor='b')
                ax2.tick_params(axis='y', labelcolor='r')

                # Format x-axis
                ax1.set_xticks(days_in_month)
                ax1.set_xticklabels([day.strftime('%d')
                                    for day in days_in_month], rotation=45, ha="right")
                ax1.xaxis.set_major_locator(plt.MaxNLocator(
                    integer=True))  # Ensure integer ticks

                # Combine legends
                lines, labels = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax2.legend(lines + lines2, labels + labels2,
                           loc='upper right')  # Use combined legend

                # fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax1.transAxes) # Remove separate legend call
                fig.tight_layout()
                plt.show(block=True)
                return None
            except Exception as e:
                print(f"Plotting failed: {e}")
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
            return None  # Or raise


def plot_yearmonths(df, dfz, kategorie, year_str, yearly_sum=1000, output='text'):
    """
    Plot yearly energy distribution by month or return data for a specific year and category.

    Args:
        df (DataFrame): Main energy data
        dfz (DataFrame): Category metadata
        kategorie (str): Energy category to plot
        year_str (str): Year to analyze (YYYY format)
        yearly_sum (float): Annual energy sum for scaling (default: 1000)
        output (str): Output format ('text', 'plot', or 'json')

    Returns:
        dict or None: Data dictionary if output is 'json', None otherwise.
                      Prints text or shows plot for other outputs.
    """
    plt = None
    if output == 'plot':
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print(
                "Error: matplotlib is required for plotting. Please install with 'pip install matplotlib'")
            return None  # Cannot plot

    try:
        year = int(year_str)  # Convert year string to integer for filtering
        # Filter data for the specified year
        # Use .copy() to avoid SettingWithCopyWarning
        df_year = df[df['ts'].dt.year == year].copy()

        category_name = get_name_from_id(dfz, kategorie)
        if not category_name:
            if output == 'json':
                return {"error": f"Category '{kategorie}' not found in metadata"}
            else:
                print(f"Error: Category '{kategorie}' not found in metadata")
                return None

        # Calculate total annual energy (scaled)
        total_annual_energy_scaled = compute_total_annual_energy(
            df, kategorie) * (yearly_sum / 1000)

        # Group by month and sum the energy
        scaling_factor = yearly_sum / 1000
        # Apply scaling factor before summing
        df_year[kategorie] = df_year[kategorie] * scaling_factor
        monthly_energy = df_year.groupby(df_year['ts'].dt.month)[
            kategorie].sum()

        # Ensure all 12 months are present, filling missing ones with 0
        monthly_energy = monthly_energy.reindex(range(1, 13), fill_value=0)

        # Calculate total energy for the year from monthly sums
        total_energy_year = round(monthly_energy.sum(), 2)

        # Calculate monthly percentages
        monthly_percentages = {}  # Store percentages
        if total_annual_energy_scaled > 0:
            monthly_percentages = (
                monthly_energy / total_annual_energy_scaled * 100).round(2)
        else:
            monthly_percentages = pd.Series([0.0] * 12, index=range(1, 13))

        # Get month names
        month_names = [pd.Timestamp(
            f'{year}-{month}-01').strftime('%b') for month in range(1, 13)]

        if output == 'text':
            print(f"Yearly energy distribution for {year} ({category_name})")
            print(f"Total Energy: {total_energy_year} kWh")
            print("\nMonth      kWh     % of Year")
            print("--------- ------- ----------")
            for month_num in range(1, 13):
                print(
                    f"{month_names[month_num-1]:<9} {monthly_energy[month_num]:<7.2f} {monthly_percentages[month_num]:<10.2f}%")
            return None

        elif output == 'plot':
            if plt is None:
                print(
                    "Plotting skipped due to missing matplotlib library or import error.")
                return None
            try:
                fig, ax1 = plt.subplots(figsize=(12, 6))
                ax2 = ax1.twinx()

                ax1.set_title(
                    f"Monthly Energy Distribution for {year} - {category_name}\nTotal: {total_energy_year} kWh")
                ax1.bar(month_names, monthly_energy,
                        alpha=0.6, label='Monthly kWh')
                ax2.plot(month_names, monthly_percentages, color='r',
                         marker='o', linestyle='-', label='Monthly Percentage (%)')

                ax1.set_xlabel('Month')
                ax1.set_ylabel('Energy (kWh)', color='b')
                ax2.set_ylabel(
                    'Percentage of Yearly Consumption (%)', color='r')
                ax1.tick_params(axis='y', labelcolor='b')
                ax2.tick_params(axis='y', labelcolor='r')
                ax1.grid(axis='y', linestyle='--')

                # Combine legends
                lines, labels = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax2.legend(lines + lines2, labels + labels2, loc='upper right')

                fig.tight_layout()
                plt.show(block=True)
                return None
            except Exception as e:
                print(f"Plotting failed: {e}")
                return None

        elif output == 'json':
            monthly_values_json = [
                {
                    "month_num": month_num,
                    "month_name": month_names[month_num-1],
                    "kwh": round(monthly_energy[month_num], 2),
                    # Add percentage here
                    "percent_of_year": round(monthly_percentages[month_num], 2)
                }
                for month_num in range(1, 13)
            ]

            return {
                "function": "plot_yearmonths",
                "parameters": {
                    "year": year,  # Use the integer year here
                    "kategorie": kategorie,
                    "yearly_sum": yearly_sum
                },
                "category_name": category_name,
                "summary": {
                    "total_energy_kwh": total_energy_year
                    # Add total percentage if needed, calculated from total_energy_year / total_annual_energy_scaled
                },
                "monthly_values": monthly_values_json
            }

    except ValueError:
        # Handle case where year_str is not a valid integer
        error_msg = f"Invalid year format provided: '{year_str}'. Please use YYYY format."
        if output == 'json':
            return {"error": error_msg}
        else:
            print(f"Error: {error_msg}")
            return None
    except Exception as e:
        error_msg = f"An error occurred during yearly analysis: {str(e)}"
        if output == 'json':
            return {"error": error_msg}
        else:
            print(f"Error: {error_msg}")
            return None


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
    plt = None
    mdates = None
    YearEnd = None  # Initialize YearEnd as None
    if output == 'plot':
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            # Import YearEnd specifically here as it's from pandas
            from pandas.tseries.offsets import YearEnd
        except ImportError:
            print(
                "Error: matplotlib and/or pandas is required for plotting. Please install with 'pip install matplotlib pandas'")
            return None  # Cannot plot

    try:
        year = int(year_str)  # Convert year_str to int for date range
        start_date = pd.Timestamp(f"{year}-01-01")
        # Ensure end_date calculation is robust
        try:
            end_date = pd.Timestamp(f"{year}-12-31")
        except ValueError:  # Handle leap year if necessary, though YearEnd should work
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
        percentage_series = [res['daily_percentage_of_year']
                             for res in daily_results]
        day_strs = [day.strftime('%Y-%m-%d') for day in days_in_year]

        total_yearly_kwh = round(sum(kwh_series), 2)
        # Recalculate total percentage based on the scaled total annual energy
        total_annual_energy_scaled = compute_total_annual_energy(
            df, kategorie) * (yearly_sum / 1000)
        if total_annual_energy_scaled == 0:
            total_yearly_percentage = 0.0
        else:
            # Summing daily percentages might not be accurate, recalculate from total kwh
            total_yearly_percentage = round(
                (total_yearly_kwh / total_annual_energy_scaled) * 100, 2)

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
            # Ensure matplotlib and pandas were imported successfully
            if plt is None or mdates is None or YearEnd is None:
                print("Plotting skipped due to missing libraries or import error.")
                return None

            try:
                # Create plot
                fig, ax1 = plt.subplots(figsize=(15, 7))
                ax2 = ax1.twinx()

                ax1.set_title(
                    f"Daily Energy Distribution for {year} - {category_name}\nTotal: {total_yearly_kwh:.2f} kWh ({total_yearly_percentage:.2f}% of Year)")
                ax1.plot(days_in_year, kwh_series,
                         label='Daily kWh', color='blue', alpha=0.7)
                ax2.plot(days_in_year, percentage_series, label='Daily Percentage (%)',
                         color='red', linestyle='--', alpha=0.7)

                ax1.set_xlabel('Date')
                ax1.set_ylabel('Energy (kWh)', color='blue')
                ax2.set_ylabel(
                    'Percentage of Yearly Consumption (%)', color='red')
                ax1.tick_params(axis='y', labelcolor='blue')
                ax2.tick_params(axis='y', labelcolor='red')

                # Format x-axis to show month abbreviations
                ax1.xaxis.set_major_locator(mdates.MonthLocator())
                ax1.xaxis.set_major_formatter(
                    mdates.DateFormatter('%b'))  # Use %b for month abbr
                # Optional: minor ticks for weeks
                ax1.xaxis.set_minor_locator(mdates.DayLocator(interval=7))
                plt.setp(ax1.get_xticklabels(), rotation=45, ha="right")

                # Set x-axis limits to the year range
                ax1.set_xlim(start_date, end_date)

                # Combine legends
                lines, labels = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax2.legend(lines + lines2, labels + labels2, loc='upper right')

                ax1.grid(True, which='major', axis='x',
                         linestyle='--')  # Grid lines for months
                fig.tight_layout()
                plt.show(block=True)
                return None
            except Exception as e:
                print(f"Plotting failed: {e}")
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
# result = plot_yeardays(df, dfz, 'H0', '2025', 1000, output='json')
# if result:
#     import json
#     print(json.dumps(result, indent=4))
