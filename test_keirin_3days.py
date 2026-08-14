import datetime
import json
import sys

import keirin_today

JST = datetime.timezone(datetime.timedelta(hours=9))

def main():
    today = datetime.datetime.now(JST).date()

    print("KEIRIN 3-DAY TEST")
    print("=================")

    result = {}

    for offset in range(3):
        d = today + datetime.timedelta(days=offset)
        date_str = d.strftime("%Y%m%d")

        print()
        print(f"===== {date_str} =====")
        data = keirin_today.build_today(date_str)

        venues = data.get("venues", {})
        result[date_str] = data

        print(f"VENUES: {len(venues)}")

        for venue, info in venues.items():
            races = info.get("races", [])
            first = races[0].get("time", "") if races else ""
            last = races[-1].get("time", "") if races else ""
            print(
                f"{venue}: {len(races)}R "
                f"{first}-{last} "
                f"{info.get('day_emoji','')}{info.get('day_type','')} "
                f"{info.get('grade','')} "
                f"{info.get('event_name','')} "
                f"{info.get('event_day','')}"
            )

    # Keep a test artifact so we can inspect all three dates if needed.
    with open("keirin_3days_test.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print()
    print("=================")
    print("KEIRIN 3-DAY TEST OK")
    print("Output: keirin_3days_test.json")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("TEST FAILED:", repr(e))
        sys.exit(1)
