from playwright.sync_api import sync_playwright
from datetime import datetime
from tqdm import tqdm
import os
import re
from subjects import load_subjects
from datetime import datetime, timezone

AUTH_FILE = "auth.json"
API_URL = "https://cs.cc.unc.edu/psc/campus/EMPLOYEE/SA/s/" \
    "WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"

"""
format for the term
2 + two-digit year + semester digit
spring = 2, summer 1 = 3, summer 2 = 4, fall = 9
ex.
fall 2026 = 2269
spring 2027 = 2272
"""

TERM = "2272"


def get_session_credentials():
    if os.path.isfile(AUTH_FILE):
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context()
        page = context.new_page()

        page.goto("https://connectcarolina.unc.edu/")
        input("login to connect carolina then press enter...")

        context.storage_state(path=AUTH_FILE)
        print(f"made file {AUTH_FILE}")

        browser.close()


def get_json(request_context, subject, term=TERM):
    if not os.path.isfile(AUTH_FILE):
        raise FileNotFoundError(f"could not find {AUTH_FILE} file")

    all_results = []

    def fetch_page(page):
        response = request_context.get(
            API_URL,
            params={
                "institution": "UNCCH",
                "term": term,
                "subject": subject,
                "x_acad_career": "UGRD",
                "enrl_stat": "",
                "crse_attr": "",
                "crse_attr_value": "",
                "page": page,
            }
        )

        content_type = response.headers.get("content-type", "")

        if "application/json" not in content_type:
            raise RuntimeError(
                "ConnectCarolina session is probably expired. "
                "Try deleting the auth.json file. "
                f"Received {content_type} instead of JSON."
            )

        return response.json()

    first_page = fetch_page(1)
    all_results.extend(first_page["classes"])
    page_count = first_page["pageCount"]

    for page in range(2, page_count + 1):
        data = fetch_page(page)
        all_results.extend(data["classes"])

    return all_results


def normalize_class_time(value):
    if not value:
        return None

    parts = value.split(".")
    return f"{parts[0]}:{parts[1]}"


def normalize_class_date(value):
    if not value:
        return None
    date = datetime.strptime(value, "%m/%d/%Y")
    formatted_date = date.strftime("%Y-%m-%d")
    return formatted_date


def split_day(value):
    if not value:
        return None

    parts = re.findall(r"[A-Z][^A-Z]*", value)
    return parts

def normalize_building_name(value, room=None):
    if not value:
        return None

    value = value.strip()

    if value == "TBA":
        return value

    if room:
        room_suffix = f"-Rm {room}"
        if value.endswith(room_suffix):
            value = value[:-len(room_suffix)].strip()

    if value.endswith("-Rm"):
        value = value.removesuffix("-Rm").strip()

    building, separator, _ = value.rpartition("-Rm ")
    if separator:
        value = building.strip()

    if " " not in value:
        return value

    suffix = None
    parts = value.rsplit(" ", 1)

    match parts[-1].lower():
        case "bui":
            suffix ="Building"
        case "cen":
            suffix = "Center"
        case "re":
            suffix = "Research Center"
        case "ha":
            suffix = "Hall"
        case "a":
            suffix = "Art"
        case "biomolecula":
            suffix = "Biomolecular Research Bldg"

    if suffix:
        value = parts[0] + " " + suffix

    value = value.split("(", 1)[0].rstrip()
        
    return value


def get_min_credits(value):
    if not value:
        return None

    min_credits = value.strip().split("-")[0]
    return min_credits


def get_max_credits(value):
    if not value:
        return None

    max_credits = value.strip().split("-")
    if len(max_credits) > 1:
        return max_credits[1]

    return max_credits[0]


def normalize_class(data):
    return {
        "class_number": data["class_nbr"],
        "course_id": data["crse_id"],

        "term": data["strm"],

        "subject": data["subject"],
        "course_number": data["catalog_nbr"],
        "section": data["class_section"],

        "title": data["descr"],
        "min_credits": get_min_credits(data["units"]),
        "max_credits": get_max_credits(data["units"]),

        "component": data["component"],
        "section_type": data["section_type"],

        "instruction_mode": data["instruction_mode_descr"],

        "status": data["enrl_stat_descr"].lower(),

        "capacity": data["class_capacity"],
        "enrolled": data["enrollment_total"],
        "available_seats": data["enrollment_available"],

        "waitlist_capacity": data["wait_cap"],
        "waitlist_total": data["wait_tot"],

        "instructors": [
            {
                "name": instructor["name"],
                "email": instructor.get("email") or None,
            }
            for instructor in data.get("instructors", [])
        ],

        "meetings": [
            {
                "days": split_day(meeting.get("days")),
                "start_time": normalize_class_time(
                    meeting.get("start_time")
                ),
                "end_time": normalize_class_time(
                    meeting.get("end_time")
                ),

                "building_code": meeting.get("bldg_cd"),
                "building": normalize_building_name(meeting.get("facility_descr"), meeting.get("room")),
                "room": meeting.get("room"),
                "facility_id": meeting.get("facility_id"),
            }
            for meeting in data.get("meetings", [])
        ],

        "attributes": [
            x for
            x in data.get("crse_attr", "").split(",")
            if x
        ],

        "attribute_values": [
            x for
            x in data.get("crse_attr_value", "").split(",")
            if x
        ],

        "reserved_capacities": [
            {
                "number": reserve["rsrv_cap_nbr"],
                "description": reserve["descr"],
                "start": normalize_class_date(reserve.get("start_dt")),
                "capacity": reserve["enrl_cap"],
                "enrolled": reserve["enrl_tot"],
            }
            for reserve in data.get("reserve_caps", [])
        ]
    }



if __name__ == "__main__":
    from supabase_client import save_json_to_storage
    subjects = load_subjects()
    raw_classes = []

    get_session_credentials()

    with sync_playwright() as p:
        request_context = p.request.new_context(storage_state=AUTH_FILE)

        try:
            print("Fetching class data.\n")
            for subject in tqdm(subjects):
                raw_classes.extend(get_json(request_context, subject))
        finally:
            request_context.dispose()

    classes = [
        normalize_class(cls)
        for cls in raw_classes
    ]

    data = {
        "scraped_date": datetime.now(timezone.utc).isoformat(),
        "classes" : classes,
    }

    save_json_to_storage(data, f"scraped_data/{TERM}.json")
