import argparse
from lastfunctions import srcsink, init_environment, init_dataframes
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Energy profile analysis")
    # Add arguments and their help text
    parser.add_argument('-init', '-i', action='store_true', 
                    help="Initialize the environment by downloading and unpacking necessary data files.")
    parser.add_argument('-df', '--data-file', type=str, help="Path to the Excel file containing data.")

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
        zuordnung = dfz[['Typnummer', 'Typname', 'Typtext']].to_dict(orient='records')

    else:
        # Existing code for srcsink goes here
        # ...
        pass
