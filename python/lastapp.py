import argparse
from lastfunctions import init_environment, init_dataframes, get_name_from_id
import lastfunctions as lf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Energy profile analysis")
    # Add arguments and their help text
    parser.add_argument('-init', '-i', action='store_true',
                        help="Initialize the environment by downloading and unpacking necessary data files.")
    parser.add_argument('-df', '--data-file', type=str,
                        help="Path to the Excel file containing data.")
    parser.add_argument('-test', action='store_true',
                        help="Test function to execute.")
    parser.add_argument('-f', '--function', type=str, required=False, default='de',
                        choices=['de', 'pd', 'pm', 'pym', 'pyd'],
                        help='Function to execute. Options: de (day_energy), pd (plot_day), pm (plot_month), pym (plot_yearmonths), pyd (plot_yeardays)')

    parser.add_argument('-d', '--date', type=str,
                        help='Date in YYYY-MM-DD format. Required for: de, pd.')
    parser.add_argument('-m', '--month', type=str,
                        help='Month in YYYY-MM format. Required for: pm.')
    parser.add_argument('-y', '--year', type=str,
                        help='Year in YYYY format. Required for: pyd.')
    parser.add_argument('-k', '--kategorie', type=str, required=False, default='H0',
                        help='Category. Required for all functions.')
    parser.add_argument('-ys', '--yearly_sum', type=int, default=1000,
                        help='Yearly sum. Optional for all functions.')
    parser.add_argument('-yr', '--year_range', type=int,
                        default=2024, help='Year range. Required for: pym.')

    args = parser.parse_args()

    # Check if any argument is True (meaning it was given)
    if not any(vars(args).values()):
        parser.print_help()
        exit(0)

    if args.init:
        init_environment()
        exit(0)

    if args.data_file:
        df, dfz = init_dataframes(args.data_file)
        # Display the first few rows of each dataframe
        print("DataFrame df:")
        print(df.head())

        print("DataFrame dfz:")
        print(dfz.head())

        # Create a dictionary for 'zuordnung'
        zuordnung = dfz[['Typnummer', 'Typname', 'Typtext']
                        ].to_dict(orient='records')
    else:
        df, dfz = init_dataframes('./data/synthload2024.xlsx')

    if args.function == 'de':
        if args.date:
            daily_kwh, daily_percentage = lf.day_energy(
                df, args.date, args.kategorie, args.yearly_sum)
            print(
                f"Daily energy consumption for {args.date}: {daily_kwh} kWh.")
            print(f"Percentage of yearly consumption: {daily_percentage} %.")
        else:
            print("Date is required for day_energy.")

    elif args.function == 'pd':
        if args.date:
            lf.plot_day(df, dfz, args.date, args.kategorie, args.yearly_sum)
            # Wait for the user to hit space
            input("Hit return to continue...")
        else:
            print("Date is required for plot_day.")

    elif args.function == 'pm':
        if args.month:
            lf.plot_month(df, dfz, args.month, args.kategorie, args.yearly_sum)
            input("Hit return to continue...")
        else:
            print("Month is required for plot_month.")

    elif args.function == 'pym':
        if args.year_range:
            lf.plot_yearmonths(df, dfz, args.kategorie,
                               args.year_range, args.yearly_sum)
            input("Hit return to continue...")
        else:
            print("Year range is required for plot_yearmonths.")

    elif args.function == 'pyd':
        if args.year:
            lf.plot_yeardays(df, dfz, args.kategorie,
                             args.year, args.yearly_sum)
            input("Hit return to continue...")
        else:
            print("Year is required for plot_yeardays.")

    elif args.test:

        df, dfz = init_dataframes('./data/synthload2024.xlsx')
        # Display the first few rows of each dataframe
        kat = 'H0'
        jen = 5500    # jahres energie
        tag = '2024-01-01'
        energysum = lf.compute_total_annual_energy(df, kat)
        print(kat, get_name_from_id(dfz, kat),
              ': Normierte Jahres Energie', energysum, 'kWh')

        # actual_kwh, percentage_consumed = lf.day_energy(
        #    df, tag, kat, yearly_sum=jen)
        # print('Tages Energie am', tag, ':', actual_kwh, 'kWh. Das sind',
        #      percentage_consumed, '% der Jahres Energie von', jen, 'kWh')

        # tag_energie, tag_prozent = lf.plot_day(
        #    df, dfz, tag, kat, yearly_sum=jen)
        # print('tag energie', tag_energie, 'kWh',
        #      'tag prozent', tag_prozent, '%')
        # input("Hit space to continue...")  # Wait for the user to hit space

        # Call the function
        # total_kWh, total_percentage = lf.plot_month(
        #    df, dfz, month_str='2024-07', kategorie=kat, yearly_sum=jen)
        # print('Monats Energie', total_kWh, 'kWh',
        #      'Monats prozent', total_percentage, '%')

#        lf.plot_yearmonths(df, dfz, kategorie=kat, year=2024, yearly_sum=jen)
        yeardaysum = lf.plot_yeardays(df, dfz,
                                      kategorie=kat, year_str=2024, yearly_sum=jen)
        print('Jahres Energie', yeardaysum, 'kWh')

        input("Hit space to continue...")  # Wait for the user to hit space
