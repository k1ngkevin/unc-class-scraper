import json
import requests
import re
from datetime import datetime
from typing import Any
from bs4 import BeautifulSoup

BASE_URL = "https://reports.unc.edu/class-search/"

headers = [
    "subject",
    "catalog_number",
    "same_as",
    "section",
    "crn",
    "description",
    "term",
    "credit_hours",
    "meeting_dates",
    "schedule",
    "instruction_type",
    "available_seats",
]


def fetch_subject_html(subject):
    url = BASE_URL + f"?subject={subject}&term=2026+Fall"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def parse_subject(subject, html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="results-table")
    if (not table):
        return []

    current_catalog = ""

    class_data = []
    for tr in table.find_all("tr"):
        rowspan_cells = tr.find_all("td", rowspan=True)

        if rowspan_cells:
            catalog_cell = rowspan_cells[-1]
            current_catalog = catalog_cell.text.strip()

        cells = tr.find_all("td", rowspan=False)

        if cells:
            row_vals = [cell.text.strip() for cell in cells]
            if row_vals[0] != subject:
                row_vals.insert(0, subject)

            row_vals.insert(1, current_catalog)
            if len(headers) == len(row_vals):
                course_dict: dict[str, Any] = dict(zip(headers, row_vals))

                date_range = course_dict["meeting_dates"]
                try:
                    start_date, end_date = re.split(
                        r"\s*-\s*", date_range, maxsplit=1)

                    course_dict["meeting_dates"] = {
                        "start": datetime.strptime(start_date, "%m/%d/%Y").date().isoformat(),
                        "end": datetime.strptime(end_date, "%m/%d/%Y").date().isoformat(),
                    }
                except ValueError:
                    course_dict["meeting_dates"] = {
                        "start": "",
                        "end": "",
                    }

                schedule = course_dict["schedule"]

                try:
                    days, time_range = schedule.split(maxsplit=1)
                    start_time, end_time = re.split(
                        r"\s*-\s*",
                        time_range,
                        maxsplit=1,
                    )

                    course_dict["meeting_days"] = days
                    course_dict["start_time"] = start_time
                    course_dict["end_time"] = end_time
                except ValueError:
                    course_dict["meeting_days"] = None
                    course_dict["start_time"] = None
                    course_dict["end_time"] = None

                del course_dict["schedule"]

            class_data.append(course_dict)

    return class_data


def save_course(course_name, json_data):
    with open(f"{course_name}_courses.json", "w") as file:
        json.dump(json_data, file, indent=4)


if __name__ == "__main__":
    subject = "COMP"
    subject_html = fetch_subject_html(subject)
    subject_data = parse_subject(subject, subject_html)
    save_course(subject, subject_data)
