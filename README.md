# UmaClubDailyFilter
Code written with copilot assistants to sort club members who have not done their dailies in Umamusume

>The script check for daily fan gain in the cvs file and return members that has <300 fan gain a day.
>Which I considered not completed their debut run;
>I do not check for the minimum fan gain a day or week it is outside of my scope, however feel free to fork it or contribute to this repo.


UmaClubDailyFilter
Reads a CSV club file exported from chronogenesis.net and prints the names of
club members who have NOT completed their dailies.

Two CSV formats are supported:

  Legacy format:  columns include "Name" and "Daily Fan Gain".
                  A member is inactive when Daily Fan Gain < 300.

  Monthly format: first column is "Trainer"; remaining columns are
                  "Day 1", "Day 2", … containing *cumulative* fan totals.
                  Per-day gain is computed as Day[N] - Day[N-1].
                  A day is skipped (missed) when the gain is < 300.
                  Members are reported with a count of how many days
                  they missed.

Values that are empty or contain only a dash ("-") are treated as missing
and are skipped; a gap in the day sequence resets the running baseline.

Usage:
    python filter_dailies.py [CSV_FILE]

    If CSV_FILE is not provided as a command-line argument the script
    prompts the user for a filename. Pressing Enter without typing a name
    defaults to "sample_club_data.csv".

Setup:
``` sh
git clone https://github.com/Devtorious/UmaClubDailyFilter
cd UmaClubDailyFilter
```

Usage:
``` sh
python filter_dailies.py <your CVS file>
```
If CVS input left empty the script will default to read the sample file

Only tested with (Chronogenesis)[https://chronogenesis.net/club_profile]
