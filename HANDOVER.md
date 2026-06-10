# Updating TAIPAN - A Practical Guide
This guide covers the most common maintenance tasks you’ll need to do on TAIPAN. It assumes you know basic Python but are **not** familiar with the TAIPAN codebase yet.
> **Before you start:** Make sure TAIPAN is set up on your machine. If not, follow the Installation Instructions in the main developer docs first.
-----
## Table of Contents
1. [Project Structure - Where is Everything?](#1-project-structure--where-is-everything)
1. [Adding a New Station or Location](#2-adding-a-new-station-or-location)
1. [Adding a New Script or Feature](#4-adding-a-new-script-or-feature)
1. [Adding a New Button to the Launcher](#3-adding-a-new-button-to-the-launcher)
1. [Adding a New Python Library](#5-adding-a-new-python-library)
1. [Running the Test Suite](#6-running-the-test-suite)
1. [Common Errors and Fixes](#7-common-errors-and-fixes)
-----
## 1. TAIPAN Structure — Where is Everything?

![Diagram](taipan-diagram.drawio.svg)


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


## 3. Adding a New Script or Feature
**Where to put it:**

Put new code in the folder that matches its purpose (see the project structure table above). For example, a new stabling report goes in `stabling/`, a new timetable output goes in `timetables/`.

**Tips:**
- If your script needs to parse an RSX file, use the existing `xml_parser.py` in `core/` - don’t write your own parser. The `TrainInfo` object it returns has all the common train attributes already normalised. Further in this section will be an example of how to use this functionality.
- If you need a popup or file input dialog, use the standard functions in `gui/base` rather than writing your own. This keeps the UI consistent.
- If your GUI is specific to one script, add a new file in `gui/` rather than modifying `gui/base`.

**After adding a new script:**
- Add a button for it (see Section 4 below)
- Add unit tests for it if required (see Section 6 below)
- If it uses new libraries, update `requirements.txt` (see Section 5 below)


### 1.  How to use `parse_rsx` and `TrainInfo`
This is the starting point for almost every script in TAIPAN. These functions go through the RSX file and return what is requested in a readable, compact format. 
Here’s a minimal example that parses the RSX and returns lists of useful info:

```python
from taipan.core.xml_parser import parse_rsx

root, trains, d_list, u_list, run_dict, _ = parse_rsx(
   path, # must specify yourself 
   want_trains=True,
   want_days=True,
   want_units=True,
   want_runs=True
)

for train in trains:
    # for every train in the RSX it prints the their (weekday, train type, destination). 
    # You can get more attributes using `Traininfo` attribute cheat sheet further down
   print(train.weekday, train.train_type, train.is_empty)
```

**Return values:**
|Variable    |What it is                                                     |
|------------|---------------------------------------------------------------|
|`root`      |Raw XML root element of the RSX file                           |
|`trains`    |List of `TrainInfo` objects - one per train                    |
|`d_list`    |List of day codes found in the RSX (e.g. `['120', '64', '32']`)|
|`u_list`    |List of unit types found in the RSX (e.g. `['NGR', 'QMU']`)    |
|`run_dict`  |Dictionary of runs keyed by `(run, weekday)`                   |
|`duplicates`|List of duplicate train numbers detected                       |

**`want_` flags:**
|Flag                  |What it does                                                          |
|----------------------|----------------------------------------------------------------------|
|`want_trains=True`    |Parses all trains into `TrainInfo` objects — required for most scripts|
|`want_days=True`      |Builds `d_list`                                                       |
|`want_units=True`     |Builds `u_list`                                                       |
|`want_runs=True`      |Builds `run_dict`                                                     |
|`want_duplicates=True`|Checks for duplicate train numbers                                    |


**`TrainInfo` attribute cheat sheet:**
|Attribute                  |What it gives you                                                          |
|---------------------------|---------------------------------------------------------------------------|
|`train.weekday`            |Day code (e.g. `'120'` for Mon–Thu)                                        |
|`train.unit`               |Train type (e.g. `NGR`, `QMU`, `IMU`)                                      |
|`train.train_type`         |Full normalised type string (e.g. `6-NGR`, `Empty_3-QMU`)                  |
|`train.is_empty_train`     |`True` if the train is running empty                                       |
|`train.cars`               |Number of cars (`3` or `6`)                                                |
|`train.stations`           |List of station IDs in order                                               |
|`train.origin`             |First entry attributes (station, departure time etc.)                      |
|`train.destin`             |Last entry attributes                                                      |
|`train.odep` / `train.ddep`|Origin and destination departure times                                     |
|`train.sector`             |Sector number as an integer                                                |
|`self.start_id` / `self.end_id `| station ID of origin/dest                                            |
|`train.run`                |Run ID                                                                     |
|`train.lineID`             |Full line ID from RSX                                                      |
|`train.number`             |Train number                                                               |
|`train.direction`          |`'Up'` or `'Down'`                                                         |
|`train.connection`         |Connection element if present, else `None`                                 |
|`train.vyst_is_yard`       |`True` if VYST is treated as a yard for this run (temporary - see  main dev docs)|

You can add more to this! See core/xml_parser.py `TrainInfo` class.


### 2. Get it ready to integrate with new buttons!

Let's say you need to create a new script that:
1. Takes an input RSX, from the user
1. Prints all the origin and destinations station IDs for each trainID
1. Pops up a message box of (trainID, origin, and destination)

From the previous section we can come up with something like this - but with a few important additions.

```python
from taipan.core.xml_parser import parse_rsx
from taipan.gui.base import select_file, show_info_scroll_safe # import existing UI elements
from PyQt6.QtWidgets import QApplication
import sys

def get_od_of_trains(path, mypath = None):

    root, trains, d_list, u_list, run_dict, _ = parse_rsx(
    path,
    want_trains=True,
    want_days=True,
    want_units=True,
    want_runs=True
    )

    train_list = []


    for train in trains:
        train_list.append(f"{train.number}, {train.start_id}, {train.end_id}")
        print(train.number, train.start_id, train.end_id)

    train_msg = "\n".join(train_list)
    
    
    show_info_scroll_safe("Trains, origin and destination: ", train_msg) # must use *safe versions to ensure it works with the UI 

if __name__ == "__main__":
	app = QApplication.instance() or QApplication(sys.argv) # this ensures we can still run this function standalone - without using the full UI 
	path = select_file(caption='Select RSX file',directory='',filter_str='RSX Files (*.rsx);;All Files (*.*)') 
	if path:
		get_od_of_trains(path)
```


-----

## 4. Adding a New Button to the Launcher
In this example, we will create a new button that runs the code from #2 in the previous section.
The launcher UI is in `gui/launch.py` and the button configuration lives in `gui/ui_constants/names.py`.

**Step 1 — Load your function (lazily) at the top of launch.py**

```python
# find this section in launch.py
TTS_ERR         = _lazy("taipan.reports.ErrorChecker",           "TTS_ERR")
TTS_PTT         = _lazy("taipan.timetables.PublicTimetable",     "TTS_PTT")
... 
TTS_OD          = _lazy("taipan.test", "get_od_of_trains") # add new import
```

**Step 2 — Add the function to the `TaipanLauncher` class in `launch.py`**
In `gui/launch.py`, add a new method to the `TaipanLauncher` class. This function is what gets called when the button is clicked. 
Going off our previous example:

```python
class TaipanLauncher(QMainWindow):
    ...
    ...

    def _run_qa(self, button=None):
        path = self.get_file(filter_str="RSX Files (*.rsx)")

        if not path:
            return

        self.run_task(lambda: TTS_ERR(path),"● RUNNING — QA / ERROR CHECKER...","● DONE — QA / ERROR CHECKER")


    def _run_OD(self, button = None):
        path = self.get_file(filter_str="RSX Files (*.rsx)") # you can also add force_new = True if you want it to force a new selection each time rather than using saved file

        if not path:
            return

        self.run_task(lambda: TTS_OD(path),"● RUNNING — OD...","● DONE — O/D LIST")
```

**Step 3 — Register the button**

Open `gui/ui_constants/names.py` and find the `groups` dictionary. Add your button to the appropriate category using this format:

```python
("Get Origin/Dest", "_run_OD", "Gets origin and destination of each train in the RSX.")
```
The three values are: button label, function name (must match what you defined in the class, in our example it was `_run_OD`), tooltip text.


> **Important:** If your script has no clear exit point (e.g. it opens a dashboard that stays open), run it as a subprocess instead. See the `_run_runtime` function in `launch.py` for an example of how to do this.

> **Threading note:** The UI is multi-threaded. Never call a Qt widget directly from inside your function — this will crash the app. If you see `QObject: Cannot create children for a parent that is in a different thread`, this is why.

> **COM/win32 note:** If your function uses COM or win32 and it freezes or crashes, add `pythoncom.CoInitialize()` at the top of your function and `pythoncom.CoUninitialize()` in a `finally` block.


**Step 4 — Test it**

Launch TAIPAN (`launch_TAIPAN.bat`) and confirm your button appears and works. Styling of the buttons and UI more generally can be modified via `gui/ui_constants/stylesheet.py` (uses CSS).

-----


## 5. Adding a New Python Library
Whenever you install a new library via pip, you **must** update `requirements.txt` so it installs correctly for everyone else.

**Steps:**
1. Install your library normally: `.\venv\Scripts\python.exe pip -m install <library-name>`
1. Run the following to regenerate `requirements.txt`:

  ```
  .\venv\Scripts\python.exe -m pip freeze > requirements.txt
  ```
3. Open `requirements.txt` and **DELETE any lines** related to `pywin32` that don’t have a pinned version number (lines that look like `pywin32==` with nothing after the `==`, or lines without `==` at all). See below - this is how it might look...
```
-e c:\python_ttsummary
pywin32 @ file:///C:/Users/r919150/Downloads/pywin32-311-cp312-cp312-win_amd64.whl#sha256=b8c095edad5c211ff31c05223658e71bf7116daa0ecf3ad85f3201ea3190d067
```
4. Commit the updated `requirements.txt`

> Others on the team will pick up the new dependency automatically when they run `update_TAIPAN.bat`.
-----
## 6. Running the Test Suite
Always run the tests after making changes to make sure you haven’t broken anything.
**To run all tests, paste this into your terminal from the TAIPAN root folder:**
```
.\venv\Scripts\python.exe -m pytest
```
You should see all tests passing. Currently there are 66 tests.

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