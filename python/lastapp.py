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

    args = parser.parse_args()

    # Check if any argument is True (meaning it was given)
    if not any(vars(args).values()):
        parser.print_help()
        exit(0)

    if args.init:
        init_environment()
    elif args.data_file:
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
        # Existing code for srcsink goes here
        # ...
        pass

    if args.test:

        df, dfz = init_dataframes('./data/synthload2024.xlsx')
        # Display the first few rows of each dataframe
        kat = 'H0'
        jen = 5500    # jahres energie
        tag = '2024-01-01'
        energysum = lf.compute_total_annual_energy(df, kat)
        print(kat, get_name_from_id(dfz, kat),
              ': Normierte Jahres Energie', energysum, 'kWh')

        actual_kwh, percentage_consumed = lf.day_energy(
            df, tag, kat, yearly_sum=jen)
        print('Tages Energie am', tag, ':', actual_kwh, 'kWh. Das sind',
              percentage_consumed, '% der Jahres Energie von', jen, 'kWh')
