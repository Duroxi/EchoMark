import os
from datetime import datetime
from db import execute_sql

LAST_UPDATE_FILE = os.getenv("LAST_UPDATE_FILE", "/opt/echomark/last_update")

def read_last_update() -> datetime:
    """Read last update timestamp from file."""
    try:
        with open(LAST_UPDATE_FILE, "r") as f:
            content = f.read().strip()
            if content:
                return datetime.fromisoformat(content)
    except (FileNotFoundError, ValueError):
        pass
    return datetime(1970, 1, 1)

def write_last_update(dt: datetime):
    """Write current timestamp to file."""
    os.makedirs(os.path.dirname(LAST_UPDATE_FILE), exist_ok=True)
    with open(LAST_UPDATE_FILE, "w") as f:
        f.write(dt.isoformat())

def nightly_update():
    """Update tool_stats with new ratings since last run."""
    last_update = read_last_update()
    now = datetime.now()

    new_ratings = execute_sql(
        """SELECT tool_name, accuracy, efficiency, usability, stability, overall
           FROM ratings WHERE timestamp > %s AND tool_name != '__agent__'""",
        (last_update,),
        fetch_all=True
    )

    if not new_ratings:
        write_last_update(now)
        return

    tools = {}
    for r in new_ratings:
        tool = r['tool_name']
        if tool not in tools:
            tools[tool] = []
        tools[tool].append(r)

    for tool_name, ratings in tools.items():
        existing = execute_sql(
            "SELECT * FROM tool_stats WHERE tool_name = %s",
            (tool_name,),
            fetch_one=True
        )

        if existing is not None:
            old_total = existing['total_ratings']
            new_count = len(ratings)
            new_total = old_total + new_count

            new_acc = sum(r['accuracy'] for r in ratings) / new_count
            new_eff = sum(r['efficiency'] for r in ratings) / new_count
            new_usa = sum(r['usability'] for r in ratings) / new_count
            new_sta = sum(r['stability'] for r in ratings) / new_count
            new_ovl = sum(r['overall'] for r in ratings) / new_count

            avg_accuracy = round((existing['avg_accuracy'] * old_total + new_acc * new_count) / new_total, 1)
            avg_efficiency = round((existing['avg_efficiency'] * old_total + new_eff * new_count) / new_total, 1)
            avg_usability = round((existing['avg_usability'] * old_total + new_usa * new_count) / new_total, 1)
            avg_stability = round((existing['avg_stability'] * old_total + new_sta * new_count) / new_total, 1)
            avg_overall = round((existing['avg_overall'] * old_total + new_ovl * new_count) / new_total, 1)

            execute_sql(
                """UPDATE tool_stats SET
                   total_ratings = %s, avg_accuracy = %s, avg_efficiency = %s,
                   avg_usability = %s, avg_stability = %s, avg_overall = %s, last_updated = %s
                   WHERE tool_name = %s""",
                (new_total, avg_accuracy, avg_efficiency, avg_usability, avg_stability, avg_overall, now, tool_name)
            )
        else:
            count = len(ratings)
            avg_accuracy = round(sum(r['accuracy'] for r in ratings) / count, 1)
            avg_efficiency = round(sum(r['efficiency'] for r in ratings) / count, 1)
            avg_usability = round(sum(r['usability'] for r in ratings) / count, 1)
            avg_stability = round(sum(r['stability'] for r in ratings) / count, 1)
            avg_overall = round(sum(r['overall'] for r in ratings) / count, 1)

            execute_sql(
                """INSERT INTO tool_stats (tool_name, total_ratings, avg_accuracy, avg_efficiency,
                   avg_usability, avg_stability, avg_overall, last_updated)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (tool_name, count, avg_accuracy, avg_efficiency, avg_usability, avg_stability, avg_overall, now)
            )

    write_last_update(now)
    print(f"Nightly update complete: processed {len(new_ratings)} ratings for {len(tools)} tools")