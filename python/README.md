# Energy Profile Analyzer

A Python application for analyzing and visualizing energy consumption data.

## Features

- Calculate daily energy consumption
- Visualize energy data by day, month, or year
- Support for custom data files
- Multiple analysis functions

## Installation

1. Clone this repository
2. Install dependencies:

```
pip install -r requirements.txt
```

## Usage

```
python lastapp.py [options]
```

### Options

- `-i`, `--init`: Initialize environment (download data files)
- `-df`, `--data-file`: Path to custom Excel data file
- `-f`, `--function`: Analysis function to execute (de, pd, pm, pym, pyd)
- `-d`, `--date`: Date in YYYY-MM-DD format
- `-m`, `--month`: Month in YYYY-MM format
- `-y`, `--year`: Year in YYYY format
- `-k`, `--kategorie`: Category (default: H0)
- `-ys`, `--yearly_sum`: Yearly sum (default: 1000)
- `-yr`, `--year_range`: Year range (default: 2024)

### Examples

1. Get daily energy consumption:

```
python lastapp.py -f de -d 2024-01-01
```

2. Plot monthly energy data:

```
python lastapp.py -f pm -m 2024-01
```

3. Plot yearly energy data:

```
python lastapp.py -f pyd -y 2024
```

## License

MIT
