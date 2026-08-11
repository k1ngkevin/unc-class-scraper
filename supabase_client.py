import time
import os
from dotenv import load_dotenv
from supabase import Client, create_client
from auth_scraper import (
    get_json,
    get_session_credentials,
    normalize_class
)

load_dotenv()

API_URL = os.getenv("SUPABASE_URL")
API_KEY = os.getenv("SUPABASE_KEY")

if not API_URL or not API_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are not set in .env")

supabase: Client = create_client(API_URL, API_KEY)


def save_course(cls):
    course_data = {
        "unc_course_id": cls["course_id"],
        "subject": cls["subject"],
        "course_number": cls["course_number"],
        "title": cls["title"],
        "min_credits": cls["min_credits"],
        "max_credits": cls["max_credits"],
        "term": cls["term"],
    }

    result = (
        supabase.table("courses").upsert(
            course_data,
            on_conflict="term,unc_course_id",
        )
        .select("id")
        .execute()
    )

    data = result.data

    if not data:
        raise RuntimeError("Failed to get course id after upsert")

    row = data[0]
    if not isinstance(row, dict):
        raise RuntimeError(f"unexpected supabase response: {row}")

    return row["id"]


def save_section(cls, course_id):
    section_data = {
        "class_number": cls["class_number"],
        "course_id": course_id,
        "section": cls["section"],
        "component": cls["component"],
        "section_type": cls["section_type"],
        "instruction_mode": cls["instruction_mode"],
        "status": cls["status"],
        "capacity": cls["capacity"],
        "enrolled": cls["enrolled"],
        "available_seats": cls["available_seats"],
        "waitlist_capacity": cls["waitlist_capacity"],
        "waitlist_total": cls["waitlist_total"],
        "attributes": cls["attributes"],
        "attributes_values": cls["attribute_values"],
        "term": cls["term"],
    }

    result = (
        supabase.table("sections").upsert(
            section_data,
            on_conflict="term,class_number",
        )
        .select("id")
        .execute()
    )

    data = result.data

    if not data:
        raise RuntimeError("Failed to get section id after upsert")

    row = data[0]
    if not isinstance(row, dict):
        raise RuntimeError(f"unexpected supabase response: {row}")

    return row["id"]


def save_meeting(meetings, section_id):
    supabase.table("meetings").delete().eq("section_id", section_id).execute()

    if not meetings:
        return
    meeting_data = [{
        "section_id": section_id,
        "start_time": meeting["start_time"],
        "days": meeting["days"],
        "end_time": meeting["end_time"],
        "building_code": meeting["building_code"],
        "building": meeting["building"],
        "room": meeting["room"],
        "facility_id": meeting["facility_id"],
    }
        for meeting in meetings]

    supabase.table("meetings").insert(meeting_data).execute()


def save_reserve_capacities(capacities, section_id):
    supabase.table("reserved_capacities").delete().eq(
        "section_id", section_id).execute()

    if not capacities:
        return

    reserve_capacity_data = [{
        "section_id": section_id,
        "number": reserved["number"],
        "description": reserved["description"],
        "start": reserved["start"],
        "capacity": reserved["capacity"],
        "enrolled": reserved["enrolled"],
    }
        for reserved in capacities
    ]

    supabase.table("reserved_capacities").insert(
        reserve_capacity_data).execute()


def save_instructors(instructors, section_id):

    supabase.table("section_instructors").delete().eq(
        "section_id", section_id).execute()

    if not instructors:
        return

    instructor_links = []

    for instructor in instructors:
        instructor_data = {
            "name": instructor["name"],
            "email": instructor["email"],
        }

        result = (
            supabase.table("instructors").upsert(
                instructor_data,
                on_conflict="name",
            )
            .select("id")
            .execute())

        data = result.data

        if not data:
            raise RuntimeError("failed to save instructor")

        row = data[0]

        if not isinstance(row, dict):
            raise RuntimeError(f"Unexpected Supabase response: {row}")

        instructor_id = row["id"]

        instructor_links.append(
            {
                "section_id": section_id,
                "instructor_id": instructor_id,
            }
        )

    supabase.table("section_instructors").insert(instructor_links).execute()


def save_class(cls):
    course_id = save_course(cls)

    section_id = save_section(cls, course_id)

    save_meeting(cls["meetings"], section_id)
    save_reserve_capacities(cls["reserved_capacities"], section_id)
    save_instructors(cls["instructors"], section_id)


if __name__ == "__main__":

    # SUBJECTS = [
    #    "AAAD", "AMST", "ANTH", "APPL", "ASTR", "BCB", "BIOC", "BIOL", "BIOS",
    #    "BMME", "BUSI", "CHEM", "CLAR", "CMPL", "COMM", "COMP", "DATA", "DRAM",
    #    "ECON", "EDUC", "EMES", "ENEC", "ENGL", "ENVR", "EPID", "EXSS", "GEOG",
    #    "HBEH", "INLS", "LING", "MATH", "MEJO", "NSCI", "PHIL", "PHYS", "PLAN",
    #    "PLCY", "POLI", "PSYC", "SOCI", "STOR", "WGST",
    # ]

    start = time.time()
    get_session_credentials()
    subjects = ["COMP", "AAAD", "AMST", "ANTH", "APPL"]
    for subject in subjects:
        raw_classes = get_json(subject)
        classes = [normalize_class(cls) for cls in raw_classes]

        for cls in classes:
            save_class(cls)
    end = time.time()
    print(f"time took {end-start} seconds")
