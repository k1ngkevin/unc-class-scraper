import time
import os
from dotenv import load_dotenv
from supabase import Client, create_client
from auth_scraper import (
    get_json,
    get_session_credentials,
    normalize_class
)
from subjects import load_subjects

load_dotenv()

API_URL = os.getenv("SUPABASE_URL")
API_KEY = os.getenv("SUPABASE_KEY")

if not API_URL or not API_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are not set in .env")

supabase: Client = create_client(API_URL, API_KEY)


def save_courses_batch(classes):
    if not classes:
        return {}

    unique_courses = {}

    for cls in classes:
        key = (cls["term"], cls["course_id"])
        unique_courses[key] = {
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
            list(unique_courses.values()),
            on_conflict="term,unc_course_id",
        )
        .select("id,term,unc_course_id")
        .execute()
    )

    course_ids = {}

    if not result.data:
        raise RuntimeError("Failed to save course data")

    for row in result.data:
        if not isinstance(row, dict):
            continue

        key = (row["term"], row["unc_course_id"])
        course_ids[key] = row["id"]

    return course_ids


def save_sections_batch(classes, course_ids):
    if not classes or not course_ids:
        return {}

    sections_data = []

    for cls in classes:
        course_key = (cls["term"], cls["course_id"])

        sections_data.append({
            "class_number": cls["class_number"],
            "course_id": course_ids[course_key],
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
        })

    result = (
        supabase.table("sections").upsert(
            sections_data,
            on_conflict="term,class_number",
        )
        .select("id,term,class_number")
        .execute()
    )

    section_ids = {}

    if not result.data:
        raise RuntimeError("failed to save sections")

    for row in result.data:
        if not isinstance(row, dict):
            continue

        key = (row["term"], row["class_number"])
        section_ids[key] = row["id"]

    return section_ids


def save_meetings_batch(classes, section_ids):
    if not classes or not section_ids:
        return

    supabase.table("meetings").delete().in_(
        "section_id", list(section_ids.values())).execute()

    meeting_data = []

    for cls in classes:
        section_key = (cls["term"], cls["class_number"])

        for meeting in cls["meetings"]:
            meeting_data.append({
                "section_id": section_ids[section_key],
                "start_time": meeting["start_time"],
                "days": meeting["days"],
                "end_time": meeting["end_time"],
                "building_code": meeting["building_code"],
                "building": meeting["building"],
                "room": meeting["room"],
                "facility_id": meeting["facility_id"],
            })
    if meeting_data:
        supabase.table("meetings").insert(meeting_data).execute()


def save_reserve_capacities_batch(classes, section_ids):
    if not classes or not section_ids:
        return

    supabase.table("reserved_capacities").delete().in_(
        "section_id", list(section_ids.values())).execute()

    reserve_capacity_data = []

    for cls in classes:
        section_key = (cls["term"], cls["class_number"])
        for reserved in cls["reserved_capacities"]:

            reserve_capacity_data.append({
                "section_id": section_ids[section_key],
                "number": reserved["number"],
                "description": reserved["description"],
                "start": reserved["start"],
                "capacity": reserved["capacity"],
                "enrolled": reserved["enrolled"],
            })

    if reserve_capacity_data:
        supabase.table("reserved_capacities").insert(
            reserve_capacity_data).execute()


def save_instructors_batch(classes):
    if not classes:
        return {}

    unique_instructors = {}

    for cls in classes:
        for instructor in cls["instructors"]:
            instructor_key = instructor["name"]

            unique_instructors[instructor_key] = {
                "name": instructor["name"],
                "email": instructor["email"],
            }

    if not unique_instructors:
        return {}

    result = (
        supabase.table("instructors").upsert(
            list(unique_instructors.values()),
            on_conflict="name",
        )
        .select("id,name")
        .execute())

    instructor_ids = {}

    if not result.data:
        raise RuntimeError("failed to save instructors")

    for row in result.data:
        if not isinstance(row, dict):
            continue

        key = row["name"]
        instructor_ids[key] = row["id"]

    return instructor_ids


def save_instructor_links_batch(classes, section_ids, instructor_ids):
    if not classes or not section_ids:
        return

    supabase.table("section_instructors").delete().in_(
        "section_id", list(section_ids.values())).execute()

    unique_links = {}

    for cls in classes:
        section_key = (cls["term"], cls["class_number"])
        for instructor in cls["instructors"]:
            instructor_key = instructor["name"]
            section_id = section_ids[section_key]
            instructor_id = instructor_ids[instructor_key]

            instructor_link_key = (section_id, instructor_id)

            unique_links[instructor_link_key] = {
                "section_id": section_id,
                "instructor_id": instructor_id,
            }

    if unique_links:
        supabase.table("section_instructors").insert(
            list(unique_links.values())).execute()


def save_classes_batch(classes):
    if not classes:
        return

    course_ids = save_courses_batch(classes)

    section_ids = save_sections_batch(classes, course_ids)

    save_meetings_batch(classes, section_ids)
    save_reserve_capacities_batch(classes, section_ids)

    instructor_ids = save_instructors_batch(classes)
    save_instructor_links_batch(classes, section_ids, instructor_ids)


if __name__ == "__main__":
    subjects = load_subjects()

    total_start = time.perf_counter()

    get_session_credentials()
    for subject in subjects:
        subject_start = time.perf_counter()
        start = time.perf_counter()
        raw_classes = get_json(subject)

        classes = [normalize_class(cls) for cls in raw_classes]
        save_classes_batch(classes)

        print(f" {subject} took {(time.perf_counter()-subject_start):.2f} seconds")

    total_elapsed = time.perf_counter() - total_start
    print(f"Total time: {total_elapsed:.2f} seconds")
