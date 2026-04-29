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


### Description of New Functionality

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
- All user interface code been changed from Tkinter to PyQT5.
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
- Clone the repository into your C drive



#### Non cloning way (manual)

- To download: Code -> download zip
- Create a new folder in your C drive called "Python_TTSummary" (MUST be exactly this capitalisation/spelling/etc)
> - C-drive is `C:\` in the path bar
- Place the contents of the zip you downloaded into Python_TTSummary. Full path should look like `"C:\Python_TTSummary"` with src, tests, etc in the folder.


### 3. Downloading / Setup of IDE (skip if not developing)

- Install VSCode if needed

### 4. Setup the Python Virtual Environment
- **Important**: For all commands, replace the `<username>` part with your own username (e.g r123456)

- Open a powershell terminal inside the `Python_TTSummary` folder (the repository you just cloned/downloaded). 
> - To do this, right click inside the folder -> select open in Terminal. This is the 'root' directory. In the terminal run the following commands.

- Create a virtual environment:

    `C:\Users\<username>\AppData\Local\Programs\Python\Python312\python.exe -m venv venv`

- Activate the virtual environment

    `.\venv\Scripts\activate`

    After running the previous two steps, you see something that looks like the below image, note the green (venv) to the left of the folder structure. 

    ![venv](/images/activating_venv.png "venv")

    If you don't see the green (venv)  **🚨 DO NOT CONTINUE WITH THE REST OF THE STEPS! 🚨**. Doing so may break your Python environment. 

- Install TAIPAN's Python packages to virtual environment:

    `.\venv\Scripts\python.exe -m pip install -r requirements.txt`

    Should see something that looks like this when it's finished; if you get that red error just ignore it and continue.

    ![package installer](/images/installing_packages.png "packages")

- Install pywin32 (requires .whl file, installing manually)
    `.\venv\Scripts\python.exe -m pip install "C:\Python_TTSummary\pywin32-311-cp312-cp312-win_amd64.whl"`

- Now tell Python this code is a 'package':

    `.\venv\Scripts\python.exe -m pip install -e .`

### 5. Setup complete
- At this point, TAIPAN and all its dependencies should be installed and ready to use. To verify, run the following (in the same place you ran the previous commands) and if no errors pop up the installation succeeded. 

    `.\venv\Scripts\python.exe -c "import taipan"`

    If an error popped up, ask for help. Otherwise, you’re good to go 🚀


