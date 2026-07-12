"""Load skipped Gold Coast I/II files after trial-name slot fix."""
from populate_trialresults_fixed import (
    get_connection,
    get_next_ids_from_db,
    process_trial_file,
    run_deferred_trial_normalizations,
)

SKIPPED_FILES = [
    (r"Gold Coast\2011 Gold Coast II.txt", 2011),
    (r"Gold Coast\2012 Gold Coast I.txt", 2012),
    (r"Gold Coast\2012 Gold Coast II.txt", 2012),
]

conn = get_connection()
next_trial_id, next_trialclass_id, next_placement_id = get_next_ids_from_db(conn)
loaded_trial_ids: list[int] = []

for file_path, year in SKIPPED_FILES:
    next_trial_id, next_trialclass_id, next_placement_id = process_trial_file(
        conn,
        file_path,
        year,
        next_trial_id,
        next_trialclass_id,
        next_placement_id,
        defer_normalization=True,
        loaded_trial_ids=loaded_trial_ids,
    )

run_deferred_trial_normalizations(conn, loaded_trial_ids)
conn.close()
