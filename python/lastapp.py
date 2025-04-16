import argparse
from lastfunctions import init_environment, init_dataframes, get_name_from_id
import lastfunctions as lf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import json


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
                            help='Date in YYYY-MM-DD, YYYY-MM, or YYYY format. Required for: de, pd (YYYY-MM-DD); pm (YYYY-MM); pyd (YYYY).')
        parser.add_argument('-k', '--kategorie', type=str, required=False, default='H0',
                            help='Category. Required for all functions.')
        parser.add_argument('-o', '--output', type=str, default='text',
                            choices=['text', 'plot', 'json'], help='Output format: text, plot, or json')
        parser.add_argument('-ys', '--yearly_sum', type=int, default=1000,
                            help='Yearly sum. Optional for all functions.')

        args = parser.parse_args()
        return args

    def __init__(self, args):
        """Initialize the analyzer with command line arguments."""
        self.args = args
        # Add a reference to the parser for printing help

    def run(self):
        """Execute the analysis based on provided arguments."""
        # Check if any argument is True (meaning it was given)
        # A simple check like this might not be robust if default values change
        # Consider a more specific check if needed
        # if not any(vars(self.args).values()):
        #     self.parser.print_help()
        #     exit(0)

        if self.args.init:
            init_environment()
            exit(0)

        if self.args.data_file:
            self.df, self.dfz = init_dataframes(self.args.data_file)
            if self.args.output != 'json': # Avoid printing dataframes in json mode
                print("DataFrame df loaded.")
                # print(self.df.head())
                print("DataFrame dfz loaded.")
                # print(self.dfz.head())
        else:
            self.df, self.dfz = init_dataframes('./data/synthload2024.xlsx')

        result_data = None

        if self.args.function == 'de':
            if self.args.date:
                # Assuming lf.day_energy will be modified to return a dict for json
                result_data = lf.day_energy(
                    self.df, self.args.date, self.args.kategorie, self.args.yearly_sum)
                if self.args.output != 'json':
                    daily_kwh, daily_percentage = result_data # Unpack if not json
                    print(
                        f"Daily energy consumption for {self.args.date}: {daily_kwh} kWh.")
                    print(
                        f"Percentage of yearly consumption: {daily_percentage} %.")
            elif self.args.output != 'json':
                print("Date is required for day_energy.")

        elif self.args.function == 'pd':
            if self.args.date:
                # Assuming lf.plot_day will be modified to return a dict for json
                result_data = lf.plot_day(self.df, self.dfz, self.args.date,
                                        self.args.kategorie, self.args.yearly_sum, self.args.output)
            elif self.args.output != 'json':
                print("Date is required for plot_day.")

        elif self.args.function == 'pm':
            if self.args.date:
                # Assuming lf.plot_month will be modified to return a dict for json
                # Extract YYYY-MM from date
                month_str = self.args.date[:7] if len(self.args.date) >= 7 else None
                if month_str:
                    result_data = lf.plot_month(self.df, self.dfz, month_str,
                                              self.args.kategorie, self.args.yearly_sum, self.args.output)
                elif self.args.output != 'json':
                    print("Valid date in YYYY-MM format is required for plot_month.")
            elif self.args.output != 'json':
                print("Date is required for plot_month.")

        elif self.args.function == 'pym':
            if self.args.date:
                # Extract YYYY from date
                year_str = self.args.date[:4] if len(self.args.date) >= 4 else None
                if year_str:
                    # Assuming lf.plot_yearmonths will be modified to return a dict for json
                    result_data = lf.plot_yearmonths(self.df, self.dfz, self.args.kategorie,
                                                   year_str, self.args.yearly_sum, self.args.output)
                elif self.args.output != 'json':
                    print("Valid date in YYYY format is required for plot_yearmonths.")
            elif self.args.output != 'json':
                print("Date is required for plot_yearmonths.")

        elif self.args.function == 'pyd':
            if self.args.date:
                # Assuming lf.plot_yeardays will be modified to return a dict for json
                # Extract YYYY from date
                year_str = self.args.date[:4] if len(self.args.date) >= 4 else None
                if year_str:
                    result_data = lf.plot_yeardays(self.df, self.dfz, self.args.kategorie,
                                                 year_str, self.args.yearly_sum, self.args.output)
                elif self.args.output != 'json':
                    print("Valid date in YYYY format is required for plot_yeardays.")
            elif self.args.output != 'json':
                print("Date is required for plot_yeardays.")

        elif self.args.test:
            # Test function remains unchanged for now, might need adjustment
            # if lf functions change significantly
            self.df, self.dfz = init_dataframes('./data/synthload2024.xlsx')
            kat = 'H0'
            jen = 5500
            tag = '2024-01-01'
            energysum = lf.compute_total_annual_energy(self.df, kat)
            print(kat, get_name_from_id(self.dfz, kat),
                  ': Normierte Jahres Energie', energysum, 'kWh')
            yeardaysum = lf.plot_yeardays(self.df, self.dfz,
                                          kategorie=kat, year_str='2024', yearly_sum=jen, output='plot') # Keep plot for test, uses year_str directly
            print('Jahres Energie', yeardaysum, 'kWh')
            pass # End of test block

        # Output JSON if requested and data is available
        if self.args.output == 'json' and result_data is not None:
            # Ensure pandas Series/DataFrames are converted to basic types
            def default_serializer(obj):
                if isinstance(obj, (pd.Series, pd.DataFrame)):
                    return obj.to_dict(orient='records') # Or other suitable format
                if isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

            print(json.dumps(result_data, indent=4, default=default_serializer))

if __name__ == "__main__":
    args = EnergyProfileAnalyzer.parse_arguments()
    analyzer = EnergyProfileAnalyzer(args)
    analyzer.run()
