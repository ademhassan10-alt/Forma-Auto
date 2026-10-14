# Code

The Python code that does the work lives here.
Each automation (welcome email, win-back, Sheet check, and so on) will get its own file.
GitHub Actions runs these files on a schedule. Nothing in here contains passwords or keys: those come from GitHub secrets when the code runs.

Empty for now except `__init__.py`, which tells Python "this folder is a package of code".

## Files
- `mindbody.py`: reads clients, class visits (last 60 days) and packs from Mindbody. Read-only: the only non-GET request is the staff login.
- `mindbody_report.py`: runs the fetch and prints counts and field names only (never names, emails or phone numbers). Used by the "Mindbody fetch check" workflow.
