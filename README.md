# UNC Course Scraper

Simple Python scraper that collects UNC course and section data from the
[UNC Class Search](https://reports.unc.edu/class-search/) website and saves it
as JSON.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage

Run the scraper with:

```bash
python public_scraper.py
```

The current script fetches `COMP` courses for Fall 2026 and writes them to
`COMP_courses.json`. Change the subject and term values in
`public_scraper.py` to scrape a different search.

currently the JSON has this structure

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
