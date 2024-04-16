import streamlit as st
import pandas as pd
from datetime import datetime
import os
import lastfunctions as lf  # Assuming your functions are in a file named lastfunctions.py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import altair as alt

# Initialization
def setup_data():
    # Initialize environment if the data folder doesn't exist
    if not os.path.exists('./data'):
        lf.init_environment()
    # Assuming the data file path after extraction
    excel_file_path = './data/synthload2024.xlsx'
    return lf.init_dataframes(excel_file_path)



def plot_yearmonths(df, dfz, kategorie, year=2024, yearly_sum=1000):
    # Ensure 'ts' is a datetime column
    df['ts'] = pd.to_datetime(df['ts'])

    # Filter data for the specific year and then group by month
    df['Year'] = df['ts'].dt.year
    df['Month'] = df['ts'].dt.month
    filtered_df = df[df['Year'] == year]
    
    if filtered_df.empty:
        print(f"No data available for year {year}.")
        return

    monthly_energy = filtered_df.groupby('Month')[kategorie].sum()

    if monthly_energy.sum() == 0:
        print("Sum of energy data across all months is zero. Please check the data quality and category specifications.")
        return

    # Scale the energy values
    scaling_factor = yearly_sum / 1000
    monthly_energy *= scaling_factor

    # Create DataFrame for Altair
    chart_df = pd.DataFrame({
        'Month': monthly_energy.index,
        'Energy (kWh)': monthly_energy.values
    })

    # Define interactive brush
    brush = alt.selection_interval(encodings=['x'])

    # Create bar chart
    bars = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X('Month:O', axis=alt.Axis(title='Month', labelAngle=-45)),
        y=alt.Y('Energy (kWh):Q', axis=alt.Axis(title='Energy (kWh)')),
        opacity=alt.condition(brush, alt.value(1), alt.value(0.7)),
    ).add_selection(
        brush
    )

    # Create rule to show average energy use when brushed
    line = alt.Chart(chart_df).mark_rule(color='firebrick').encode(
        y='mean(Energy (kWh)):Q',
        size=alt.value(3)
    ).transform_filter(
        brush
    )

    # Combine bar and rule charts
    chart = alt.layer(bars, line).properties(
        title=f"Monthly Energy Distribution for {year}, Total: {yearly_sum} kWh",
        width=800,
        height=400
    )

    # Display the Altair chart in Streamlit
    st.altair_chart(chart, use_container_width=True)



def plot_day_streamlit(df, dfz, date_str, kategorie, yearly_sum=1000):
    # Adapted plot_day function for Streamlit with Altair
    actual_kwh_series, percentage_series, filtered_df = lf.day_vector(
        df, date_str, kategorie, yearly_sum)

    typtext = lf.get_name_from_id(dfz, kategorie)

    # Create a new DataFrame for plotting
    plot_df = pd.DataFrame({
        'Time': filtered_df['ts'],
        'Actual kWh': actual_kwh_series * 4
    })

    # Create an Altair chart object
    chart = alt.Chart(plot_df).mark_line().encode(
        x=alt.X('Time', axis=alt.Axis(title='Time', format='%H:%M', labelAngle=-45)),
        y=alt.Y('Actual kWh', axis=alt.Axis(title='Energy (kWh)')),
        tooltip=['Time', 'Actual kWh']
    ).properties(
        title=f"Energy Distribution for {date_str} ({typtext})",
        width=800,
        height=400
    )

    # Display the Altair chart in Streamlit
    st.altair_chart(chart, use_container_width=True)

# App definition
def app():
    st.set_page_config(page_title='Austria Energy Consumption Dashboard')

    # Load data
    df, dfz = setup_data()

    # Sidebar for user input
    st.sidebar.title("Settings")
    # Checking if 'E1' is among the unique categories available
    default_category = "E1" if "E1" in dfz['Typname'].unique() else dfz['Typname'].unique()[0]

#    kategorie = st.sidebar.selectbox('Select Category', dfz['Typname'].unique())
    kategorie = st.sidebar.selectbox(
        'Select Category',
        options=dfz['Typname'].unique(),
        index=list(dfz['Typname'].unique()).index(default_category)
        )
    # anlage can be 5kWp, 10kWp or 15kWp
    # Define the options for the solar installation capacities
    AnalgenOptions = [5, 10, 15]  # Capacities in kWp

    Anlage = st.sidebar.selectbox('Select Solar Installation Capacity (kWp)', AnalgenOptions)
    
    SpezifischerErtrag = 1000
    yearly_sum = Anlage * SpezifischerErtrag
    st.sidebar.write(f"Yearly Sum (kWh): {yearly_sum}")
    #yearly_sum = st.sidebar.number_input('Set Yearly Sum (kWh)', value=500)

    # Display app title
    st.title('Energy Consumption Dashboard')

    # Calculate and display current day's energy
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_energy, today_percentage = lf.day_energy(df, today_str, kategorie, yearly_sum)
    st.header(f"Energy Consumption for Today: {today_str}")
    st.subheader(f"Total kWh: {today_energy} kWh")
    st.write(f"Percentage of Yearly Consumption: {today_percentage:.2f}%")
    
    # Plot the day's energy distribution
    plot_day_streamlit(df, dfz, today_str, kategorie, yearly_sum)
    # Calculate and display current month's energy

    plot_yearmonths(df, dfz, kategorie, 2024, yearly_sum)

    current_month_str = datetime.now().strftime('%Y-%m')
    month_energy, month_percentage = lf.plot_month(df, dfz, current_month_str, kategorie, yearly_sum)
    st.header(f"Energy Consumption for Current Month: {current_month_str}")
    st.subheader(f"Total kWh: {month_energy} kWh")
    st.write(f"Percentage of Yearly Consumption: {month_percentage:.2f}%")

if __name__ == '__main__':
    app()
