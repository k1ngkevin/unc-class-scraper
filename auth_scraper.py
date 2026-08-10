from playwright.sync_api import sync_playwright, expect
import os


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
            all_results.append(data["classes"])

        browser.close()

    return all_results


if __name__ == "__main__":
    get_session_credentials()
    get_json("COMP")
