# UNC Course Scraper

Python scrapers for collecting UNC course and section data. The default,
`auth_scraper.py`, uses an authenticated ConnectCarolina session. The older
`public_scraper.py` uses the public
[UNC Class Search](https://reports.unc.edu/class-search/) website and is kept
only as a fallback if the authenticated scraper is not working.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
playwright install chromium
```

## Usage

### Authenticated scraper (default)

Run:

```bash
python auth_scraper.py
```

On the first run, a browser window opens at ConnectCarolina. Log in, return to
the terminal, and press Enter. The scraper saves the browser session to
`auth.json` and reuses it on later runs.

If ConnectCarolina returns a non-JSON response, the saved session has probably
expired. Remove `auth.json` and run the scraper again to log in and create a
new session.

```python
from auth_scraper import get_session_credentials, get_json

get_session_credentials()
courses = get_json("COMP", term="2269")
```

`get_json` returns the course data from ConnectCarolina as a list of
JSON-compatible dictionaries.

### Public scraper (fallback)

The public scraper should not normally be needed. Use it only if the
authenticated scraper is unavailable or not working:

```bash
python public_scraper.py
```

It fetches `COMP` courses for Fall 2026 and writes them to
`COMP_courses.json`. Change the subject and term values in
`public_scraper.py` to scrape a different search.

The public scraper's JSON has this structure:

```json
"subject": "COMP",
"catalog_number": "89",
"same_as": "",
"section": "144",
"crn": "18801",
"description": "Fys: Special Topics",
"term": "2026 Fall",
"credit_hours": "3.0",
"meeting_dates": {
    "start": "2026-08-17",
    "end": "2026-12-11"
},
"instruction_type": "In Person On Campus Learners",
"available_seats": "0",
"meeting_days": "TTH",
"start_time": "12:30 PM",
"end_time": "01:45 PM"
```

## License

[MIT License](LICENSE).
