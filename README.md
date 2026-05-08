# TAIPAN codebase


## Changes to codebase

### Description of Structural Changes

TAIPAN has been restructured to improve modularity, maintainability, and separation of concerns. Each top level directory of `taipan` now contains a distinct functional responsibility. 

- `constants/` - contains all constants (train stations, stabling locations, colours), shared by all scripts. 
- `core/` - contains all common functionality (parsing RSX file, utility functions, processing excel and styling)
- `converters/` - contains all format converters (HASTUS, ITOPS)
- `first_last/` - contains all first last outputs and logic. 
- `gui/` - contains everything relating to UI (standard functions for popup boxes, specialised gui for slicer etc)
- `plans/` - NGR daily plan etc
- `reports/` - QA reports, tripcount, error checker
- `rsx/` - functions that modify, extract or return specific parts of an RSX file (sectoriseRSX, slicer).
- `run_renamer/` - all run renaming functionality 
- `stabling/` - all outputs relating to stabling (stabling count/balance).
- `timetables/` - all outputs relating to timetabling (public and working timetable).


### Developer Docs


**`gui/launch.py`**
- The excel macros file has been replaced with a unified frontend, implemented in PyQT6. PyQT6 is an incredibly flexible UI library, so get creative here `:)`
- This launcher file is referenced in launch_TAIPAN.bat and is the entry point for TAIPAN. The .bat file should not need to be modified.
- To add a new button, a new function must be defined in the `TaipanLauncher` class. To link this function to a button, add the function to the `SCRIPTS` dictionary in `gui/names.py` in the `groups` variable in the appropriate category. The ordering is `("BUTTON_TEXT",   "FUNCTION_NAME",   "TOOLTIP_TEXT")`. Please note the FUNCTION_NAME is the name of the function you added in the `TaipanLauncher` class, so please import it as well. You can also rearrange this dictionary and play around with the formatting...
- You can also modify the styling and colouring of the UI in `gui/stylesheet` - which just uses standard CSS. 
- If a code file has no clear return or exit point (e.g RuntimeDashboard since it uses dash), it must be run as a subprocess. This is so it does not occupy the thread that the actual UI is operating on and freeze it. To see an example, see `_run_runtime` in `launch.py`. 
- The user interface is multi-threaded. This is so multiple scripts can be running simultaneously and so the main UI doesn't crash during processing. The main UI stays on the main thread, and the functions run on Worker threads.  
- Managing the thread state is **incredibly important** - if you don't, the application will crash or hang because of cross thread memory access. See below on how to do this...


```
THREAD SAFETY TIPS
───────────────────────────────────────────────────────────────────────

All tool functions (TTS_TC, TTS_PTT, etc.) run on a QThread worker, keeping the main thread/event loop free and the UI responsive.

Any Qt UI calls (dialogs, popups) from within a tool MUST use the *_safe wrappers defined in taipan/gui/base.py:

For example, in base.py we currently have...
   show_info_safe()
   show_error_safe()
   show_info_scroll_safe()
   select_option_safe()
   select_checkboxes_safe()

These use call_on_main_thread() which works as follows:

   Worker thread                        Main thread
   ─────────────────────────────────    ─────────────────────────────
   tool function running...             UI responsive, event loop
                                        spinning
   hits *_safe() call
   │
   └─ BlockingQueuedConnection ───────► _invoke_slot() fires
      WORKER BLOCKS AND WAITS!          dialog shown to user
                                        user interacts
   result returned ◄─────────────────   slot returns
   worker unblocks, continues
   ─────────────────────────────────    ─────────────────────────────

DO NOT call QDialog, QMessageBox, or any other Qt widget directly from a tool function — always use the *_safe wrappers. To add a new function, add a wrapper using call_on_main_thread in gui/base.py
select_file() and select_multi_rsx_files() are exempt - since they are always called before run_task() on the main thread.
```
- If you see `QObject: Cannot create children for a parent that is in a different thread`, you likely called a Qt widget directly from a worker thread.
- If you see functions/buttons that use COM/win32 freezing or crashing, add pythoncom.CoInitialize() at the top of your tool function and pythoncom.CoUninitialize() in a finally block. COM objects have thread affinity and must be initialised on the thread that uses them.


**`requirements.txt`**
- This file MUST be updated when a new library is used or installed via pip. It manages the install on new users computers
- Versions should also be pinned as supported functionality may vary across different library releases. 
- An easy way to update requirements if you're not keeping track of libraries is to run `.\venv\Scripts\python.exe -m pip freeze > requirements.txt`. However because of the manual pywin32 .whl installation there will be 2 lines with no pinned versions (e.g `==version`). so delete those. If pip freezes any pywin32 libraries, delete those lines as well. 




**`core/xml_parser.py`**
- Contains foundational functionality relied upon across the entire TAIPAN codebase.
- Defines the core RSX data model, where each RSX `<train>` element is parsed and represented as a structured Python object (`TrainInfo`).
- The `TrainInfo` object acts as the canonical representation of a train, exposing normalised and commonly used attributes such as weekday, lineID, origin/destination, station sequence, train type, empty/revenue status, sector, and connection information. More variables can be added to  `__init__` if new information from the RSX is needed, however, if any current variables are updated the changes will propagate across the codebase. 

**`constants/`**
- Updating one of these constants, such as adding a new train station to `STATIONS_MASTER` in `locations.py`, will propagate the change over the entire codebase. 
- If a station/yard or location is missing from an output, check `locations.py`.

**`rsx/SectoriseRSX.py`** 
- Sectorises an RSX file by assigning a sector based pattern using origin and destination station codes. Outputs a modified RSX file which can be loaded into Railsys with a folder structure separating trains by sector.
- Only applicable to CRR files; execution will fail if `RS` is present without a corresponding `RTL`
- There may be some trains which are unable to be sectorised. They will be marked as **Unassigned** where a sector cannot be reliably determined due to conflicting or ambiguous sector mapping and will be required to be manually resolved in Railsys. 

**`first_last/first_last_graph.py`**
- Produces an interactive Excel report of first and last revenue departures by station, day, and direction.
- Processes one or more RSX files and determines inbound/outbound direction based on core station logic.
- For comparing multiple timetables select them when inputting the RSX files. 
- Outputs a workbook with charts, pivot tables, and slicers for filtering and comparison across timetables.


**`stabling/StablingCountStepGraph.py`**
- The step graph provides minute level resolution for each yard, with yard capacity overlaid to identify periods where stabling exceeds capacity.
- Produces an Excel workbook containing one worksheet per yard with time‑series stabling graphs.
- Overlays total stabled units, unit type breakdowns, and yard capacity to identify periods where capacity is exceeded.
- Intended as a visual validation and analysis tool for stabling demand across the operating day.
- Styling is done via changing `chart.ChartStyle = 240`, however there is no list of available styles. An easy way to find out what number  a chartstyle corresponds to is to record a macro -> change the chartstyle -> stop recording -> view macros -> select the macro and click edit -> see what number `ActiveChart.ChartStyle` and set the chartstyle in the code to that number. 
- **Its important to note that many Excel chart formatting properties accessed via pywin32 / win32com (such as ChartStyle and ChartColor) are version dependent and may render differently across Excel releases. In some cases, styles that are unsupported in a given Excel version may raise COM runtime errors when applied. COM‑fragile properties are annotated in the code (search for COM‑fragile)**
- New feature: a summary table identifying yards where incompatible rollingstock is stabled (e.g. NGR units stabled in QR only yards, and vice versa). Additional summary table where yards with capacity violations are recorded, along with peak stabled + time of first capacity breach.

**`stabling/StablingCount.py`**
- In summary, yard name will highlight dark red when the yard has imbalances.
- When capacity is red, this indicates a stabling issue: 
> - incorrect train type stabled at yard (NGR at QR only fleet or vice versa). At the moment QTMP/QMU/REP are caught as QR fleet in this check since capacity is unknown - intended to be an FYI.
> - stabling capacity has been exceeded for a period/day 
- If Sat/Sun uses more trains than weekdays, unit cells text colour will be red.


**All files in `stabling/`**
- `REP` has been changed to `QMU` to align with newer rollingstock naming convention. However the input RSX can contain both `REP` and `QMU` and they will be processed the same - the output file will just change it to `QMU`.
- Logic has been changed -> for all trains, 6 cars always count as 1 unit, and 3 cars count as 0.5. All calculations are done relative to 6 car sets. To get 3 car equivalent = 6 car equivalent * 2. This change means we can now directly compare stabling totals to the yard capacity. 
- All stabling files now check for capacity/wrong traintype violations

**`gui/`**
- All user interface code been changed from Tkinter to PyQT6.
- `base` contains all the standard functionality (e.g error boxes, warning boxes, inputting RSX files). Any other files in this directory contain specialised GUI functionality for specific functions. This structure should be maintained - if you expect to use a GUI across multiple files (in other words, if it's generic), it should be in base, or if it is specialised to one function, add a new file. 

**`tests/`** 
- A test suite containing unit tests for new and old functionality. 
- When new functionality is added, this test suite should be run to ensure no breaking changes were introduced. 
- To add new tests, add a new file in the folder with unit tests, and it will automatically be discovered by pytest (see Testing). 
- So far contains tests for `xml_parser.py`, `TrainInfo`, `SectoriseRSX.py`, needs extending. 

**`run_renamers/run_renamer_new.py`**
- Run renamer and block creator buttons (and their variants) in TAIPAN's excel file have been replaced with a single unified button/code file (button: Assign LineIDs -> `run_renamer_new.py`). Original code files have been retained and are available in the `run_renamers` folder 
- new renamer automatically assigns and normalises LineIDs to trains in an RSX file based on (unit type, operating day, yard departure order, connecting trains).
- Broadly the scripts steps are:
> - parse all trains from rsx and filter to supported unit types (see LineID range table)
> - build connection blocks - train chains via `<connection>`
> - sort blocks by earliest yard departure. Fallback: use first timetabled departure 
> - cross day matching -> match block between paired days (weekdays & weekend) using first stop signature. Where cross day matches exist force LineiDs to be reused. 
> - rewrite RSX file 


- **LineID range table** - these will need to be updated once new ranges are known. These ranges are a modified version of the RMC electric workings document. 


| Unit Type | LineID / Run Code Range                     |
|-----------|---------------------------------------------|
| EMU       | AA–EZ, IA–JZ, OA–PZ                         |
| IMU       | FA–GZ, KA–KZ, QA–QZ                         |
| NGR       | 01–499                                      |
| REP       | 500–999                                     |

> - Note that we share IDs across days to account for the lack of IDs to assign to new trains. NGRs and REP have had their ranges expanded to account for the amount of trains. 


**`publictimetable/PublicTimetable.py`**
- Logic has been updated to make it independent of O/D pairs - only uses O or D to determine line. This was done so PTT works properly with future states.
- For writing station-times, there is additional logic introduced for new timetables:

> - If RS exists:
>> - AND origin station is Southern lines then Bowen Hills is last revenue station
>> - AND origin station is Northern lines then Roma Street is last revenue station
> - If RTL exists:
>> - AND origin station is Southern lines then Exhibition is the last revenue station
>> - AND origin station is Northern Lines Boggo road is the last revenue station 

- There is a new 'shuttle' sheet which has trains with no RS or RTL stations in their `entries` but contain revenue stations. There will be a separate sheet for each day in the RSX if 'shuttles' are detected. 
- All the data structures have been removed and refactored (vrt, unique stations, stablingmaster, stationsmaster etc) and will only rely on a single source to receive station and line metadata (`STATIONS_MASTER` in `constants/locations.py`). If you find a missing station / and or line in the output, `STATION_MASTER` would be the place to update. 
- Station ordering is no longer hardcoded - this is inferred dynamically from each train. The script looks at all trains that have stations belonging to a line and builds the order using that.
- Now has Roma Street Arrive and Roma Street Depart rows - for sheets with both RS and RTL. Also has Central Arrive and Central Depart.
- Inner city sheet has been separated by RS and RTL. RS inbound, outbound and RTL inbound, outbound
- User can specify what day's timetables they want generated (generated list from all possible days in input rsx)


## Testing
 - Run all tests; copy into cmd

    `.\venv\Scripts\python.exe -m pytest`


 - **Current state (29/04) - 24 PASSED, 0 FAILING**

## Installation Instructions 


### 1. Download Python 

- Go to [this link](https://www.python.org/downloads/release/python-3129/), scroll down, find the 64 bit windows installer. Click the version (displayed) below to install

    ![Python installer](/images/python_install.png "Page")

- When the installer is finished, run it from your downloads folder. Leave everything as default and click skip/next.

### 2. Clone the repository OR Download the repository 


#### Cloning 
- Cloning is recommended so you can keep updated with files instantaneously rather than having to manually update the code files every time an update is pushed.
- For this method - you need to do two additional steps before you can proceed with Step 4.
> - Create a Github account (use QR email to sign up) 
> -  Download Github Desktop (from here https://desktop.github.com/download/)
- Clone the repository anywhere in a local drive (e.g any path starting with C:/). DO NOT install TAIPAN into any network drives, this will slow down the code runtime significantly. 


#### Non cloning way (manual)

- To download: Code -> download zip
- Unzip the repository in a local drive (e.g any path starting with C:/). DO NOT install TAIPAN into any network drives, this will slow down the code runtime significantly. 


### 3. Downloading / Setup of IDE (skip if not developing)
- Install VSCode if needed

### 4. Setup 

This step sets up the virtual environment and installs all dependencies. 
- Double click setup_TAIPAN (.bat file)
- Script works on both home and corp computers. The path to Python can also be specified manually.

### 5. Run 🚀
This launches TAIPAN
- Double click launch_TAIPAN (.bat file)