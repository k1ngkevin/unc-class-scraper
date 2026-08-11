from bs4 import BeautifulSoup
import json
import requests
import re
import os

SUBJECTS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "subjects.json"
)


def fetch_subjects_html():
    url = "https://catalog.unc.edu/courses/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def fetch_subject_codes(html):
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", id="atozindex")
    if container:
        courses = [
            li.get_text(strip=True) for li in container.find_all("li")
        ]

        course_tags = []
        for course in courses:
            match = re.search(r'\(([^)]+)', course)
            if match:
                course_tags.append(match.group(1))

        return course_tags

    else:
        print("no text container found")


def load_subjects():
    try:
        html = fetch_subjects_html()
        subjects = fetch_subject_codes(html)

        if not subjects:
            raise ValueError("No subject code found")

        with open(SUBJECTS_FILE, "w") as file:
            json.dump(subjects, file, indent=2)

        return subjects

    except Exception as e:
        print(f"couldn't find subjects; using cache: {e}")

        with open(SUBJECTS_FILE, "r") as file:
            return json.load(file)


if __name__ == "__main__":
    load_subjects()
