# Solar Installation Calculator

## Description
This simple web application allows users to estimate the parameters of a solar module installation. It takes the peak kW as input and provides the required square meters, installation cost, number of panels, and projected energy production per year. The application also displays a graph comparing the average daily energy production to the average daily consumption for a single-person household and a family in Central Europe.

## Installation and Usage

1. Clone the repository
    ```bash
    git clone https://github.com/your-username/your-repository-name.git
    ```

2. Navigate to the project directory
    ```bash
    cd your-repository-name
    ```

3. Open `index.html` in your web browser

## Features

- Input for peak kW of solar installation
- Calculation of:
  - Required m²
  - Cost of installation
  - Number of panels
  - kWh production per year
- Graphical representation:
  - Daily average kWh production per month
  - Daily average kWh consumption in Central Europe for a single-person household and a family

## Tech Stack
- HTML
- CSS
- JavaScript
- Chart.js

## Future Enhancements
- Include installation type as a parameter for more accurate estimations
- Add more geographical regions for energy consumption data

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
MIT License

---

## User Journey

Web UI  
User enters data as follows:

---

## UI Sketch: Leistungsverbrauchs UI

```
+-------------------------------------------------------------+
|                 Leistungsverbrauchs UI                      |
+-------------------------------------------------------------+
| Verbrauchsmodell:                                           |
+-------------------------------------------------------------+
| Sub-Einheits-Jahresverbrauch [_____] kWh                    |
| Sub-Einheiten:           [_____] (1-100)                    |
| Allgemeinteil:           [_____] % (default: 20%)           |
+-------------------------------------------------------------+
| Verbraucher hinzufügen:                                     |
| [Wärmepumpe] [Warmwasser] [Klimaanlage] [Allgemein] [+ Add] |
| (Each with Einheitsanteil input)                            |
+-------------------------------------------------------------+
| Erzeuger:                                                   |
| PV-Anlage Leistung: [_____] kWp                             |
+-------------------------------------------------------------+
| Energiespeicher:                                            |
| Kapazität: [_____] kWh                                      |
| Leistung: [_____] kW                                        |
+-------------------------------------------------------------+
| [Berechnen]                                                 |
+-------------------------------------------------------------+
| Dimensionierungs-Kommentar                                  |
| - PV-Kommentar (gut: >1,5 kWp pro 1000 kWh Jahresverbrauch) |
| - E-Speicher-Kommentar (gut: >1,5 kWh pro 1000 kWh Jahresverbrauch) |
| - E-Speicher-Kommentar (gut: >1,5 kWh pro 1 kWp Nennleistung)      |
+-------------------------------------------------------------+
| Ergebnis:                                                   |
| - Gesamtverbrauch: ____ kWh                                 |
| - PV-Anlage Deckung: ____ %                                 |
| - Energiespeicher: ____ %                                   |
+-------------------------------------------------------------+
| [Graph: Verbrauch vs. Erzeugung Lastprofil]                 |
+-------------------------------------------------------------+
```

**Notes:**
- Inputs for annual consumption, number of units, and general overhead.
- Add/remove consumers with specific shares.
- PV system input for generation.
- Results and graph shown after calculation.
- Profiles are stored in a JSON file.

Example profile:
```json
{
  "Wärmepumpenlastprofil": {
    "January": 12,
    "February": 10,
    "March": 8,
    "April": 6,
    "May": 5,
    "June": 4,
    "July": 4,
    "August": 4,
    "September": 6,
    "October": 8,
    "November": 10,
    "December": 13
  }
}
```

Wärmepumpe Verteilung:

---
````
