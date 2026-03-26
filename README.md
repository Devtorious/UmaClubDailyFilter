# UmaClubDailyFilter
A vibe coded filter to sort club members who have not done their dailies in Umamusume

>The script check for daily fan gain in the cvs file and return members that has <300 fan gain a day.
>Which I considered not completed their debut run;
>I do not check for the minimum fan gain a day or week it is outside of my scope, however feel free to fork it or contribute to this repo.

Usage:
``` sh
python filter_dailies.py <your CVS file>
```
If CVS input left empty the script will default to read the sample file

Only tested with (Chronogenesis)[https://chronogenesis.net/club_profile]
