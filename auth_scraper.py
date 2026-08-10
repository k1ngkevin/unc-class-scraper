from playwright.sync_api import sync_playwright
import json
import os
import re


def get_session_credentials():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        if not os.path.isfile("auth.json"):
            context = browser.new_context()
            page = context.new_page()

            page.goto("https://connectcarolina.unc.edu/")
            input("login to connect carolina then press enter...")

            path = "auth.json"

            context.storage_state(path=path)
            print(f"made file {path}")

        browser.close()


def get_json(subject, term="2269"):
    if not os.path.isfile("auth.json"):
        raise FileNotFoundError("could not find auth.json file")

    all_results = []

    API_URL = "https://cs.cc.unc.edu/psc/campus/EMPLOYEE/SA/s/" \
        "WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearch"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="auth.json")

        def fetch_page(page):
            response = context.request.get(
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
                    f"Received {content_type} instead of JSON."
                )
            return response.json()

        first_page = fetch_page(1)
        all_results.extend(first_page["classes"])
        page_count = first_page["pageCount"]

        for page in range(2, page_count + 1):
            data = fetch_page(page)
            all_results.extend(data["classes"])

        browser.close()

    return all_results


def normalize_class_time(value):
    if not value:
        return None

    parts = value.split(".")
    return f"{parts[0]}:{parts[1]}"


def split_day(value):
    if not value:
        return None

    parts = re.findall(r"[A-Z][^A-Z]*", value)
    return parts


def normalize_class(data):
    return {
        "class_number": data["class_nbr"],
        "course_id": data["crse_id"],

        "term": data["strm"],

        "subject": data["subject"],
        "course_number": data["catalog_nbr"],
        "section": data["class_section"],

        "title": data["descr"],
        "credits": float(data["units"]),

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
                "building": meeting.get("facility_descr"),
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
                "start": reserve.get("start_dt"),
                "capacity": reserve["enrl_cap"],
                "enrolled": reserve["enrl_tot"],
            }
            for reserve in data.get("reserve_caps", [])
        ]
    }


if __name__ == "__main__":
    subject = "COMP"

    get_session_credentials()
    raw_classes = get_json(subject)
    classes = [
        normalize_class(cls)
        for cls in raw_classes
    ]

    file_path = f"{subject}_data.json"
    output_directory = "scraped_data"
    os.makedirs(output_directory, exist_ok=True)
    path = os.path.join(output_directory, file_path)

    with open(path, "w") as file:
        json.dump(classes, file, indent=2)
