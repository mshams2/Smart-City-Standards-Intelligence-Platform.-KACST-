# Smart City Standards Dashboard

A Streamlit dashboard for browsing smart-city standards, comparing projects, reviewing maturity gaps, and inspecting supporting evidence.

## Quick start on Windows

1. Install **Python 3.12** and enable **Add Python to PATH** during installation.
2. Extract the project folder to a normal location such as `Documents` or `Desktop`.
3. Double-click `run_dashboard.bat`.
4. The first run creates `.venv` and installs the packages in `requirements.txt`.
5. Open the local address shown in the terminal, normally:

```text
http://localhost:8501
```

To stop the dashboard, press `Ctrl + C` in the terminal window or close it.

## Run from PowerShell or Command Prompt

From the project folder:

```powershell
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run dash.py
```

When opening a new terminal later, reactivate the environment before running the dashboard:

```powershell
.venv\Scripts\activate
python -m streamlit run dash.py
```

## Project structure

```text
SCDashboard/
├── dash.py                       # Application entry point
├── run_dashboard.bat             # Windows launcher
├── requirements.txt              # Python packages
├── assets/                        # Logo and visual assets
├── data/                          # Excel, CSV, and SQLite data
├── .streamlit/config.toml         # Streamlit theme and server settings
└── src/
    ├── config.py                  # Paths, colors, rubrics, and constants
    ├── data_loader.py             # Data loading and merging
    ├── database.py                # Project Checker SQLite storage
    ├── scoring.py                 # Maturity and priority calculations
    ├── ui.py                      # Shared layout and styling
    └── pages/                     # Dashboard pages
```

## Edit the new card background colors

The light card colors added to **Standards Library**, **Gap Analysis**, and **Evidence Repository** are controlled in:

```text
src/config.py
```

Find this dictionary:

```python
PAGE_CARD_BACKGROUNDS = {
    "library_catalogue_card": "#F8FBFF",
    "library_information_card": "#F7FAFF",
    "library_specification_card": "#FBFAFF",
    "gap_largest_card": "#F8FAFF",
    "gap_missing_card": "#F7FCF9",
    "gap_low_evidence_card": "#FFF9F7",
    "gap_high_impact_card": "#FBF9FF",
    "gap_priority_card": "#FFFDF7",
    "evidence_records_card": "#F8FBFF",
    "evidence_details_card": "#FBFAFF",
}
```

Replace any hexadecimal value with another light color, save the file, and refresh the browser. Examples:

```text
#F8FBFF  very light blue
#F7FCF9  very light green
#FBF9FF  very light purple
#FFF9F7  very light peach
#FFFFFF  white / no visible tint
```

Keep the dictionary keys unchanged because they connect each color to its card.

## Update dashboard data

Keep the existing file names and column layouts when replacing files in `data/`:

- `standards_indicators.xlsx`
- `projects.xlsx`
- `evidence_repository.xlsx`
- `assessment_scores.csv`
- `recommendations.csv`
- `smart_city.db`

Restart the dashboard after changing data files. Evidence links are read directly from the hyperlinks stored in `evidence_repository.xlsx`.

## Troubleshooting

### `py` is not recognized

Use `python` instead:

```powershell
python -m venv .venv
```

### Port 8501 is already in use

Run on another port:

```powershell
python -m streamlit run dash.py --server.port 8502
```

### Packages or environment are corrupted

Delete the `.venv` folder, then run `run_dashboard.bat` again.

### Dashboard data cannot be loaded

Confirm that all required files are still inside the `data` folder and that their file names have not changed.
