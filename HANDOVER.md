# Updating TAIPAN - A Practical Guide
This guide covers the most common maintenance tasks you’ll need to do on TAIPAN. It assumes you know basic Python but are **not** familiar with the TAIPAN codebase yet.
> **Before you start:** Make sure TAIPAN is set up on your machine. If not, follow the Installation Instructions in the main developer docs first.
-----
## Table of Contents
1. [Project Structure - Where is Everything?](#1-project-structure--where-is-everything)
1. [Adding a New Station or Location](#2-adding-a-new-station-or-location)
1. [Adding a New Button to the Launcher](#3-adding-a-new-button-to-the-launcher)
1. [Adding a New Script or Feature](#4-adding-a-new-script-or-feature)
1. [Adding a New Python Library](#5-adding-a-new-python-library)
1. [Running the Test Suite](#6-running-the-test-suite)
1. [Common Errors and Fixes](#7-common-errors-and-fixes)
-----
## 1. TAIPAN Structure — Where is Everything?
Here’s a quick map of the codebase so you know where to look:
|Folder       |What’s in it                                              |
|-------------|----------------------------------------------------------|
|`constants/` |Station names, yard locations, colours - shared everywhere|
|`core/`      |Common utilities used across majority of the scripts             |
|`converters/`|Format converters (HASTUS, ITOPS)                         |
|`first_last/`|First/last departure outputs                              |
|`gui/`       |All UI code — launcher, popups, etc.                      |
|`plans/`     |NGR daily plan and similar                                |
|`reports/`   |QA reports, trip counts, error checker                    |
|`rsx/`       |Functions that modify RSX files                      |
|`stabling/`  |Stabling count and balance outputs                        |
|`timetables/`|Public and working timetable outputs                      |
|`tests/`     |Unit tests                                                |

**Rule of thumb:** if something’s broken or missing, start in `constants/` — a lot of issues trace back there.

-----
## 2. Adding a New Station or Location
This is the most common maintenance task. All station data lives in one place.

**File to edit:** `constants/locations.py`

**What to do:**
1. Open `constants/locations.py`
1. Find the `STATIONS_MASTER` dictionary
1. Add your new station following the same format as existing entries
1. Save the file — the change will automatically flow through to all scripts that use station data

> **Note:** If a station or yard is missing from any output (e.g. stabling count, public timetable), this is almost always the fix. **For yards specifically**, also check the `YARDS` constant in the same file. If it’s a new yard, add it there too with its capacity and train type (use `None` if unknown). If its not a station or yard, add it to `MISC_STATIONS` instead. 
-----
## 3. Adding a New Button to the Launcher
The launcher UI is in `gui/launch.py` and the button configuration lives in `gui/ui_constants/names.py`.

**Step 1 — Write your function**

In `gui/launch.py`, add a new method to the `TaipanLauncher` class. This function is what gets called when the button is clicked. Example:

```python
def my_new_tool(self):
   # your code here
   pass
```

> **Important:** If your script has no clear exit point (e.g. it opens a dashboard that stays open), run it as a subprocess instead. See the `_run_runtime` function in `launch.py` for an example of how to do this.

> **Threading note:** The UI is multi-threaded. Never call a Qt widget directly from inside your function — this will crash the app. If you see `QObject: Cannot create children for a parent that is in a different thread`, this is why.

> **COM/win32 note:** If your function uses COM or win32 and it freezes or crashes, add `pythoncom.CoInitialize()` at the top of your function and `pythoncom.CoUninitialize()` in a `finally` block.

**Step 2 — Register the button**

Open `gui/ui_constants/names.py` and find the `groups` dictionary. Add your button to the appropriate category using this format:

```python
("BUTTON TEXT", "my_new_tool", "Tooltip text shown on hover")
```
The three values are: button label, function name (must match what you defined in Step 1), tooltip text.

**Step 3 — Test it**

Launch TAIPAN (`launch_TAIPAN.bat`) and confirm your button appears and works.

-----

## 4. Adding a New Script or Feature
**Where to put it:**

Put new code in the folder that matches its purpose (see the project structure table above). For example, a new stabling report goes in `stabling/`, a new timetable output goes in `timetables/`.

**Tips:**
- If your script needs to parse an RSX file, use the existing `xml_parser.py` in `core/` - don’t write your own parser. The `TrainInfo` object it returns has all the common train attributes already normalised.
- If you need a popup or file input dialog, use the standard functions in `gui/base` rather than writing your own. This keeps the UI consistent.
- If your GUI is specific to one script, add a new file in `gui/` rather than modifying `gui/base`.

**After adding a new script:**
- Add a button for it (see Section 3 above)
- Add unit tests for it (see Section 6 below)
- If it uses new libraries, update `requirements.txt` (see Section 5 below)
-----

## 5. Adding a New Python Library
Whenever you install a new library via pip, you **must** update `requirements.txt` so it installs correctly for everyone else.

**Steps:**
1. Install your library normally: `.\venv\Scripts\python.exe pip -m install <library-name>`
1. Run the following to regenerate `requirements.txt`:

  ```
  .\venv\Scripts\python.exe -m pip freeze > requirements.txt
  ```

1. Open `requirements.txt` and **delete any lines** related to `pywin32` that don’t have a pinned version number (lines that look like `pywin32==` with nothing after the `==`, or lines without `==` at all)
1. Commit the updated `requirements.txt`

> Others on the team will pick up the new dependency automatically when they run `update_TAIPAN.bat`.
-----
## 6. Running the Test Suite
Always run the tests after making changes to make sure you haven’t broken anything.
**To run all tests, paste this into your terminal from the TAIPAN root folder:**
```
.\venv\Scripts\python.exe -m pytest
```
You should see all tests passing. As of April 2025 there are 24 tests.

**To add new tests:**
1. Create a new file in the `tests/` folder
1. pytest will automatically discover and run it - no extra configuration needed
1. Write tests for any new functionality you add
-----
## 7. Common Errors and Fixes
|Error                                                                       |What it means                                 |Fix                                                                                                            |
|----------------------------------------------------------------------------|----------------------------------------------|---------------------------------------------------------------------------------------------------------------|
|Station/yard missing from output                                            |Station not in `STATIONS_MASTER`              |Add it to `constants/locations.py`                                                                             |
|`QObject: Cannot create children for a parent that is in a different thread`|Qt widget called directly from worker thread  |Don’t call UI elements from inside your tool function                                                          |
|COM/win32 function freezing or crashing                                     |COM object not initialised on the right thread|Add `pythoncom.CoInitialize()` at the top of the function and `pythoncom.CoUninitialize()` in a `finally` block|
|New library not found on someone else’s machine                             |`requirements.txt` not updated                |Run `pip freeze > requirements.txt`, remove unversioned pywin32 lines, commit                                  |                                                          |

-----


*For deeper technical detail on any of the above, refer to the main developer docs on the main Git page.*