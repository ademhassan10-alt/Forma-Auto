# Google Sheet template

One CSV file per tab of the Google Sheet control panel. Each has the column headers and one example row.
To build the real Sheet: create a Google Sheet with tabs named exactly `Campaigns`, `WhatsApp`, `Log`, `Settings`,
then import each CSV into its matching tab (File > Import > Upload > "Replace current sheet").

- `Campaigns.csv`: one-off emails (announcements, discount codes). Sent only when `status` is `Approved`.
- `WhatsApp.csv`: WhatsApp drafts (drink launch, polls, run club). Emailed to hello@formapilates.co.uk only when `status` is `Approved`.
- `Log.csv`: the code writes one row per run and per email sent (or that would have been sent in DRY_RUN). Do not edit by hand.
- `Settings.csv`: switches and thresholds. `DRY_RUN` must stay `TRUE` until go-live is signed off.

Delete the example rows in the real Sheet (keep the Settings rows).
