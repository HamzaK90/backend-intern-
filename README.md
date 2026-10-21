# Expense Tracker

A terminal app for keeping track of your personal expenses. Record what you
spend, list and filter it, fix or delete mistakes, see a monthly breakdown by
category, and export everything to a spreadsheet. Your data is saved after
every change and is still there the next time you start the app.

Pure Python 3.10+, no third-party packages needed to run it.

---

## Installation

You need **Python 3.10 or newer** (`python --version`).

```bash
git clone https://github.com/HamzaK90/backend-intern-.git
cd backend-intern-
python -m venv .venv

# Activate the environment
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

pip install -e .                # one step: installs the app and the expense-tracker command
```

## Running

```bash
expense-tracker                 # after installing
python -m expense_tracker       # works from the project folder, even without installing
```

By default your data is stored in `~/.expense_tracker/expenses.json`
(on Windows: `C:\Users\<you>\.expense_tracker\expenses.json`), so you see the
same expenses no matter which folder you start the app from.
To use a different file:

```bash
expense-tracker --file path/to/my_expenses.json
expense-tracker --help
```

---

## Usage

The app shows a menu. Type a number and press Enter.

```
  1. Add expense
  2. List / filter expenses
  3. Edit expense
  4. Delete expense
  5. Monthly summary
  6. Export to CSV
  0. Exit
```

**General rules**

- Dates are typed as `DD-MM-YYYY`. `/`, `.` or spaces also work: `05/10/2026`.
- Amounts are positive numbers with up to 2 decimals: `12.5`, `3`, `1200.99`.
- A value in `[brackets]` is the default. Press Enter to accept it.
- If you type something invalid, the app explains why and asks again.
- Press `Ctrl+C` to cancel the current action and go back to the menu.

### 1. Add expense

Each expense has a **name**, **category**, **amount**, **date** (defaults to
today) and an optional **note**. Categories are not case-sensitive:
`Food`, `food` and `FOOD` are the same category.

```
Name: Lunch
Category: Food
Amount: abc
  ! 'abc' is not a number. Use digits like 12.50.
Amount: 12.5
Date (DD-MM-YYYY) [18-10-2026]: 05-10-2026
Note (optional): with Ali
  Added: #1  05-10-2026  Lunch  (food)  12.50  - with Ali
```

Every expense gets a unique **id** (`#1`). You use it to edit or delete.

### 2. List / filter expenses

Answer `y` to see everything, or `n` to filter. Every filter is optional
(press Enter to skip it), and you can combine them:

| Filter | Example | Shows |
|---|---|---|
| Category | `food` | only that category |
| From / To date | `01-10-2026` / `31-10-2026` | expenses in that date range |
| Search | `ali` | name or note contains the text (not case-sensitive) |
| Min / Max amount | `20` / `100` | amounts in that range |

```
ID  Date        Category  Amount  Name    Note
--  ----------  --------  ------  ------  --------
 2  01-10-2026  housing   500.00  Rent
 1  05-10-2026  food       12.50  Lunch   with Ali
2 expenses, total 512.50
```

Expenses are listed oldest first, so the newest is right above the prompt.

### 3. Edit expense

Enter the id, then press Enter to keep each value or type a new one.
Type `-` at the note prompt to clear the note.

### 4. Delete expense

Enter the id. The app shows the expense and asks `Delete this expense? [y/N]`.
Anything other than `y` cancels. Deleting an id that doesn't exist shows
`No expense with id 99.`

### 5. Monthly summary

Answers "How much did I spend this month, and on what?". Enter a month as
`MM-YYYY` (defaults to the current month):

```
October 2026: total 512.50 (2 expenses)

Category  Count   Total     %
--------  -----  ------  ----  --------------------
housing       1  500.00  97.6  ####################
food          1   12.50   2.4  #
```

### 6. Export to CSV

Exports all expenses, or a filtered selection (same filters as listing), to a
`.csv` file that opens in Excel, LibreOffice Calc or Google Sheets. The default
file name is `expenses-<today>.csv` in the current folder. If the file already
exists, the app asks before overwriting it.

---

## How it handles things going wrong

The app never shows a Python traceback. Every expected problem is a custom
exception (`ExpenseTrackerError`), caught by the menu and shown as a one-line
message.

| Situation | What happens |
|---|---|
| Data file doesn't exist | Normal first run: start empty; the file is created on the first save. |
| Data file was edited by hand and is broken (invalid JSON, a bad amount, duplicate ids, ...) | The app says exactly what is wrong (e.g. `entry #2: Amount must be greater than zero`) and asks whether to move the broken file aside (`expenses.corrupt-<time>.json`) and start fresh. Answering no exits without touching the file, so you can fix it by hand. The data is never silently deleted. |
| One bad row among good ones | The whole file is treated as broken. Skipping the row would silently delete it on the next save. |
| `next_id` in the file is missing or wrong | Repaired automatically. It can be recalculated without losing anything. |
| Program killed or disk error while saving | Saves go to a temporary file first and are then swapped in atomically (`os.replace`), so the data file is never half-written. If saving fails, the change is not applied in memory either. |
| File can't be read/written (permissions, locked by another program) | A clear message instead of a crash. |
| Invalid amount | Rejected: not a number, zero or negative, more than 2 decimals, `NaN`/`Infinity`, over 1,000,000,000. |
| Invalid date | Rejected: wrong format, impossible dates (`31-02-2026`), dates in the future. Two-digit years are rejected on purpose (`26` could mean 1926 or 2026). |
| Delete/edit an id that doesn't exist | `No expense with id N.`, then back to the menu. |
| `Ctrl+C` during an action | The action is cancelled; back to the menu. At the menu it exits. |
| Input closed (`Ctrl+Z` on Windows, `Ctrl+D` on macOS/Linux) | Clean exit. |
| Text starting with `=`, `+`, `-`, `@` in an export | Prefixed with `'` so spreadsheet apps don't run it as a formula (CSV injection). |

---

## Design decisions

### Project structure

The code is split by responsibility: each module has one reason to change.

```
expense_tracker/
├── models.py     What an expense is and what counts as valid (Expense, parsing rules)
├── storage.py    Reading/writing the JSON data file (JsonStorage)
├── tracker.py    The operations: add, edit, delete, list, filter (ExpenseTracker, ExpenseFilter)
├── reports.py    Monthly summary by category
├── exporter.py   CSV export
├── display.py    Turning expenses and summaries into text tables
├── cli.py        The interactive menu, prompts, and error handling
├── exceptions.py Exception types shared by all modules
└── __main__.py   Entry point for `python -m expense_tracker`
```

Each layer only calls the layer below it: `cli` → `tracker` → `storage`.
Only `cli.py` reads input or prints; nothing else knows a terminal exists. So
the menu could be replaced by a web page, or JSON by SQLite, without touching
the other modules.

### Main choices

- **JSON for storage.** It keeps the structure, can hold metadata next to the
  rows (`next_id`, a format `version`), is readable/editable by hand, and needs
  no extra packages. CSV is used only for export because it has no types and no
  place for metadata.
- **The whole file is loaded into memory.** One person's expenses are small
  (even 10,000 entries are a few MB). For much larger data, a database such as
  SQLite would be the next step.
- **`Decimal` for money, never `float`.** `0.1 + 0.2` is not `0.3` with floats.
  Amounts are stored in JSON as strings (`"12.50"`) so no precision is lost.
- **Ids are never reused.** A `next_id` counter is stored in the file. Deleting
  #3 and adding a new expense gives #4, not #3, so an id always means the same
  expense.
- **Dates: two formats.** The user types and sees `DD-MM-YYYY`. The file and the
  CSV use ISO `YYYY-MM-DD`, which is unambiguous, sorts correctly as text, and is
  read correctly by every spreadsheet app.
- **Validation lives in `Expense.__post_init__`.** An `Expense` object can't exist
  in an invalid state, whether it was typed by the user or loaded from the file.
- **Categories are free text, normalized to lowercase,** so the user can create
  their own without "Food" and "food" ending up as two groups.

### Example data file

```json
{
  "version": 1,
  "next_id": 4,
  "expenses": [
    {
      "id": 1,
      "name": "Lunch",
      "category": "food",
      "amount": "12.50",
      "date": "2026-10-05",
      "note": "with Ali"
    }
  ]
}
```

---

## Going further: what I added and why

- **Edit an expense.** The task says users should be able to *correct
  mistakes*. Deleting and re-adding loses the id and is tedious.
- **Rich filtering.** Filter by category, date range, text search and amount
  range, combined. "What did I spend on food last month?" is a real question.
- **Safe handling of a broken data file.** The user decides whether to back it
  up and start fresh; data is never silently lost.
- **Atomic saves.** A crash or power cut during a save can't corrupt the data.
- **Excel-friendly CSV.** UTF-8 with BOM so non-English text (e.g. Arabic) shows
  correctly in Excel, ISO dates, and formula escaping against CSV injection.
- **`--file` option.** Keep separate files (e.g. personal / business) or try
  the app on test data.
