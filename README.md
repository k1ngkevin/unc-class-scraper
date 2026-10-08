# UNC Course Scraper

Python scrapers for collecting UNC course and section data. The default,
`auth_scraper.py`, uses an authenticated ConnectCarolina session. The older
`public_scraper.py` uses the public
[UNC Class Search](https://reports.unc.edu/class-search/) website and is kept
only as a fallback if the authenticated scraper is not working.

`subjects.py` fetches all the courses from [UNC Catalog](https://catalog.unc.edu/courses/)
and saves the subjects into `subjects.json`

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

The default run fetches classes for all subjects returned by `load_subjects()`,
using `TERM` in `auth_scraper.py`, and normalizes the ConnectCarolina response.
It uploads JSON directly to `scraped_data/{TERM}.json` in the Supabase
`course-data` storage bucket without creating a local course-data file.
Repeated runs replace the stored file for that term. Change `TERM` to scrape
another semester.

If ConnectCarolina returns a non-JSON response, the saved session has probably
expired. Remove `auth.json` and run the scraper again to log in and create a
new session.

```python
from auth_scraper import get_json, get_session_credentials, normalize_class

get_session_credentials()

with sync_playwright() as p:
  request_context = p.request.new_context(storage_state="auth.json")
  raw_classes = get_json(request_context=request_context, subject="COMP")

classes = [normalize_class(cls) for cls in raw_classes]
```

The authenticated scraper's output has this general structure:

```json
{
  "class_number": "12345",
  "course_id": "012345",
  "term": "2269",
  "subject": "COMP",
  "course_number": "110",
  "section": "001",
  "title": "Introduction to Programming",
  "credits": 3.0,
  "component": "LEC",
  "section_type": "Class Section",
  "instruction_mode": "In Person",
  "status": "open",
  "capacity": 24,
  "enrolled": 20,
  "available_seats": 4,
  "waitlist_capacity": 5,
  "waitlist_total": 0,
  "instructors": [
    {
      "name": "Instructor Name",
      "email": "instructor@unc.edu"
    }
  ],
  "meetings": [
    {
      "days": ["Mo", "We", "Fr"],
      "start_time": "10:10",
      "end_time": "11:00",
      "building_code": "FB",
      "building": "Example Building",
      "room": "101",
      "facility_id": "FB-0101"
    }
  ],
  "attributes": [],
  "attribute_values": [],
  "reserved_capacities": []
}
```

### Database

`supabase_client.py` handles saving scraped course data to the Supabase database.

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
{
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
}
```

## License

[MIT License](LICENSE).
