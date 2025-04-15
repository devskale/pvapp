import argparse
from lastfunctions import init_environment, init_dataframes, get_name_from_id
import lastfunctions as lf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


class EnergyProfileAnalyzer:
    """
    A class to analyze and visualize energy profile data.
    """

    @staticmethod
    def parse_arguments():
        """Parse command line arguments."""
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
        return args

    def __init__(self, args):
        """Initialize the analyzer with command line arguments."""
        self.args = args

    def run(self):
        """Execute the analysis based on provided arguments."""
        # Check if any argument is True (meaning it was given)
        if not any(vars(self.args).values()):
            self.args.parser.print_help()
            exit(0)

        if self.args.init:
            init_environment()
            exit(0)

        if self.args.data_file:
            self.df, self.dfz = init_dataframes(self.args.data_file)
            # Display the first few rows of each dataframe
            print("DataFrame df:")
            print(self.df.head())

            print("DataFrame dfz:")
            print(self.dfz.head())

            # Create a dictionary for 'zuordnung'
            self.zuordnung = self.dfz[['Typnummer', 'Typname', 'Typtext']
                                      ].to_dict(orient='records')
        else:
            self.df, self.dfz = init_dataframes('./data/synthload2024.xlsx')

        if self.args.function == 'de':
            if self.args.date:
                daily_kwh, daily_percentage = lf.day_energy(
                    self.df, self.args.date, self.args.kategorie, self.args.yearly_sum)
                print(
                    f"Daily energy consumption for {self.args.date}: {daily_kwh} kWh.")
                print(
                    f"Percentage of yearly consumption: {daily_percentage} %.")
            else:
                print("Date is required for day_energy.")

        elif self.args.function == 'pd':
            if self.args.date:
                lf.plot_day(self.df, self.dfz, self.args.date,
                            self.args.kategorie, self.args.yearly_sum)
                # Wait for the user to hit space
                input("Hit return to continue...")
            else:
                print("Date is required for plot_day.")

        elif self.args.function == 'pm':
            if self.args.month:
                lf.plot_month(self.df, self.dfz, self.args.month,
                              self.args.kategorie, self.args.yearly_sum)
                input("Hit return to continue...")
            else:
                print("Month is required for plot_month.")

        elif self.args.function == 'pym':
            if self.args.year_range:
                lf.plot_yearmonths(self.df, self.dfz, self.args.kategorie,
                                   self.args.year_range, self.args.yearly_sum)
                input("Hit return to continue...")
            else:
                print("Year range is required for plot_yearmonths.")

        elif self.args.function == 'pyd':
            if self.args.year:
                lf.plot_yeardays(self.df, self.dfz, self.args.kategorie,
                                 self.args.year, self.args.yearly_sum)
                input("Hit return to continue...")
            else:
                print("Year is required for plot_yeardays.")

        elif self.args.test:
            self.df, self.dfz = init_dataframes('./data/synthload2024.xlsx')
            # Display the first few rows of each dataframe
            kat = 'H0'
            jen = 5500    # jahres energie
            tag = '2024-01-01'
            energysum = lf.compute_total_annual_energy(self.df, kat)
            print(kat, get_name_from_id(self.dfz, kat),
                  ': Normierte Jahres Energie', energysum, 'kWh')

            yeardaysum = lf.plot_yeardays(self.df, self.dfz,
                                          kategorie=kat, year_str=2024, yearly_sum=jen)
            print('Jahres Energie', yeardaysum, 'kWh')

            input("Hit space to continue...")  # Wait for the user to hit space


if __name__ == "__main__":
    args = EnergyProfileAnalyzer.parse_arguments()
    analyzer = EnergyProfileAnalyzer(args)
    analyzer.run()
