from datetime import timedelta


def find_contiguous_slot(start_date, skill_sequence, calendar, max_search_days=365):

    day = start_date
    searched = 0

    explain = {
        "searched_days": 0,
        "rejections": [],
        "chosen_start": None
    }

    while searched < max_search_days:

        valid = True
        timeline = []

        for i, skill in enumerate(skill_sequence):

            check_day = day + timedelta(days=i)

            # normalize skill name
            skill_name = skill.value if hasattr(skill, "value") else str(skill)

            if calendar.is_skill_full(skill_name, check_day):
                valid = False

                explain["rejections"].append(
                    f"{check_day.isoformat()} {skill_name} full"
                )

                break

            timeline.append({
                "skill": skill_name,
                "start": check_day,
                "end": check_day
            })

        if valid:
            explain["searched_days"] = searched + 1
            explain["chosen_start"] = day.isoformat()

            return {
                "timeline": timeline,
                "explain": explain
            }

        day += timedelta(days=1)
        searched += 1

    explain["searched_days"] = searched

    return {
        "timeline": None,
        "explain": explain
    }