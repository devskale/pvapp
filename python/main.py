from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pandas as pd
import lastfunctions as lf
import os
from pathlib import Path

app = FastAPI()

# Determine the base directory of the script
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / 'data'
STATIC_DIR = BASE_DIR / 'static'
EXCEL_FILE_PATH = DATA_DIR / 'synthload2024.xlsx'
CATEGORIES_FILE_PATH = DATA_DIR / 'Kategorien.csv'

# --- Data Loading ---


def load_data():
    """Loads the energy dataframes."""
    if not EXCEL_FILE_PATH.exists():
        # Attempt to initialize if data file is missing
        print(
            f"Data file not found at {EXCEL_FILE_PATH}. Attempting to initialize environment...")
        try:
            # Assuming init_environment downloads to the correct relative path
            lf.init_environment()
            if not EXCEL_FILE_PATH.exists():
                raise HTTPException(
                    status_code=500, detail=f"Data file {EXCEL_FILE_PATH} not found even after initialization.")
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to initialize environment or find data file: {e}")

    try:
        df, dfz = lf.init_dataframes(str(EXCEL_FILE_PATH))
        # Ensure dfz uses the correct path for Kategorien.csv if needed within init_dataframes or later
        # If init_dataframes doesn't load dfz from the CSV, load it here:
        if not isinstance(dfz, pd.DataFrame):
            if CATEGORIES_FILE_PATH.exists():
                dfz = pd.read_csv(CATEGORIES_FILE_PATH, sep=';')
            else:
                # Fallback or raise error if Kategorien.csv is essential and missing
                print(
                    f"Warning: Categories file {CATEGORIES_FILE_PATH} not found. Category names might be unavailable.")
                dfz = None  # Or handle as needed

        return df, dfz
    except ValueError as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading dataframes: {e}")
    except FileNotFoundError:
        raise HTTPException(
            status_code=500, detail=f"Data file not found at {EXCEL_FILE_PATH}. Run initialization if needed.")


df, dfz = load_data()

# --- API Endpoints ---


@app.get("/api/pd")  # plot_day
async def get_plot_day(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    kategorie: str = Query(
        'H0', description="Energy category code (e.g., H0, G1)"),
    yearly_sum: int = Query(1000, description="Yearly sum in kWh for scaling")
):
    """API endpoint for daily energy profile data."""
    try:
        # Validate date format roughly (more robust validation could be added)
        pd.to_datetime(date, format='%Y-%m-%d')
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    try:
        result = lf.plot_day(df, dfz, date, kategorie,
                             yearly_sum, output='json')
        if result and 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Catch unexpected errors during function execution
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e}")


@app.get("/api/pm")  # plot_month
async def get_plot_month(
    date: str = Query(..., description="Month in YYYY-MM format"),
    kategorie: str = Query('H0', description="Energy category code"),
    yearly_sum: int = Query(1000, description="Yearly sum in kWh")
):
    """API endpoint for monthly energy profile data."""
    try:
        # Accept both YYYY-MM and YYYY-MM-DD formats
        date_obj = pd.to_datetime(date)
        month_str = f"{date_obj.year}-{date_obj.month:02d}"
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM or YYYY-MM-DD.")

    try:
        result = lf.plot_month(
            df, dfz, month_str, kategorie, yearly_sum, output='json')
        if result and 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e}")


@app.get("/api/pym")  # plot_yearmonths
async def get_plot_yearmonths(
    date: str = Query(...,
                      description="Year in YYYY or YYYY-MM or YYYY-MM-DD format"),
    kategorie: str = Query('H0', description="Energy category code"),
    yearly_sum: int = Query(1000, description="Yearly sum in kWh")
):
    """API endpoint for yearly energy profile aggregated by month."""
    try:
        # Extract year from date string (accepts YYYY, YYYY-MM, or YYYY-MM-DD)
        date_obj = pd.to_datetime(date)
        year_str = str(date_obj.year)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY, YYYY-MM, or YYYY-MM-DD.")

    try:
        result = lf.plot_yearmonths(
            df, dfz, kategorie, year_str, yearly_sum, output='json')
        if result and 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e}")


@app.get("/api/pyd")  # plot_yeardays
async def get_plot_yeardays(
    date: str = Query(..., description="Year in YYYY format"),
    kategorie: str = Query('H0', description="Energy category code"),
    yearly_sum: int = Query(1000, description="Yearly sum in kWh")
):
    """API endpoint for yearly energy profile aggregated by day."""
    try:
        # Validate date format roughly
        if len(date) != 4:
            raise ValueError("Invalid date format")
        pd.to_datetime(date, format='%Y')
        year_str = date
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY.")

    try:
        result = lf.plot_yeardays(
            df, dfz, kategorie, year_str, yearly_sum, output='json')
        if result and 'error' in result:
            raise HTTPException(status_code=404, detail=result['error'])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {e}")


@app.get("/api/categories")
async def get_categories():
    """API endpoint to get the list of available categories."""
    if dfz is None:
        raise HTTPException(
            status_code=404, detail="Category data (dfz) not loaded or available.")
    try:
        # Assuming dfz has columns 'Typname' and 'Typtext'
        # Adjust column names if they are different in your actual dfz
        categories = dfz[['Typname', 'Typtext']].to_dict(orient='records')
        return categories
    except KeyError as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: Missing expected column in category data: {e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error retrieving categories: {e}")


# --- Static Files & Root ---

# Create static directory if it doesn't exist
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def read_index():
    """Serves the main HTML page."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        # Provide a default message or create a basic index.html if it's missing
        return {"message": "Welcome to the PV App API. Frontend not found."}
    return FileResponse(index_path)

# --- Uvicorn Runner (for local development) ---
if __name__ == "__main__":
    import uvicorn
    # Run directly from script for simple testing
    # Use --reload for development to automatically pick up changes
    uvicorn.run("main:app", host="127.0.0.1", port=8008, reload=True)
