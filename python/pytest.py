import pandas as pd
import argparse
import matplotlib.pyplot as plt

plt.plot([1, 2, 3, 4])
plt.ylabel('some numbers')
plt.show()


# (Assuming you've imported or defined your functions like day_energy, plot_day, etc.)


# Your function definitions like day_energy, plot_day, etc. should go here.


def main():
    parser = argparse.ArgumentParser(description='Energy plotting utilities.')

    parser.add_argument('-f', '--function', type=str, required=True,
                        choices=['de', 'pd', 'pm', 'pym', 'pyd'],
                        help='Function to execute. Options: de (day_energy), pd (plot_day), pm (plot_month), pym (plot_yearmonths), pyd (plot_yeardays)')

    parser.add_argument('-d', '--date', type=str,
                        help='Date in YYYY-MM-DD format. Required for: de, pd.')
    parser.add_argument('-m', '--month', type=str,
                        help='Month in YYYY-MM format. Required for: pm.')
    parser.add_argument('-y', '--year', type=str,
                        help='Year in YYYY format. Required for: pyd.')
    parser.add_argument('-k', '--kategorie', type=str, required=True,
                        help='Category. Required for all functions.')
    parser.add_argument('-ys', '--yearly_sum', type=int, default=1000,
                        help='Yearly sum. Optional for all functions.')
    parser.add_argument('-yr', '--year_range', type=int,
                        default=2024, help='Year range. Required for: pym.')

    args = parser.parse_args()

    # Assuming df and dfz are loaded within the script
    # df = pd.read_csv('your_dataframe.csv')
    # dfz = pd.read_csv('your_dataframe_z.csv')

    if args.function == 'de':
        if args.date:
            print(lf.day_energy(df, args.date, args.kategorie, args.yearly_sum))
        else:
            print("Date is required for day_energy.")

    elif args.function == 'pd':
        if args.date:
            plot_day(df, dfz, args.date, args.kategorie, args.yearly_sum)
        else:
            print("Date is required for plot_day.")

    elif args.function == 'pm':
        if args.month:
            plot_month(df, dfz, args.month, args.kategorie, args.yearly_sum)
        else:
            print("Month is required for plot_month.")

    elif args.function == 'pym':
        if args.year_range:
            plot_yearmonths(df, dfz, args.kategorie,
                            args.year_range, args.yearly_sum)
        else:
            print("Year range is required for plot_yearmonths.")

    elif args.function == 'pyd':
        if args.year:
            plot_yeardays(df, dfz, args.kategorie, args.year, args.yearly_sum)
        else:
            print("Year is required for plot_yeardays.")


if __name__ == '__main__':
    main()
