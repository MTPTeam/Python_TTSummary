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
- New feature: a summary table identifying yards where incompatible rollingstock is stabled (e.g. NGR units stabled in QR only yards, and vice versa).


**All files in `stabling/`**
- `REP` has been changed to `QMU` to align with newer rollingstock naming convention. However the input RSX can contain both `REP` and `QMU` and they will be processed the same - the output file will just change it to `QMU`.


**`gui/`**
- All user interface code been changed from Tkinter to PyQT5.
- `base` contains all the standard functionality (e.g error boxes, warning boxes, inputting RSX files). Any other files in this directory contain specialised GUI functionality for specific functions. This structure should be maintained - if you expect to use a GUI across multiple files (in other words, if it's generic), it should be in base, or if it is specialised to one function, add a new file. 

**`tests/`** 
- A test suite containing unit tests for new and old functionality. 
- When new functionality is added, this test suite should be run to ensure no breaking changes were introduced. 
- To add new tests, add a new file in the folder with unit tests, and it will automatically be discovered by pytest (see Testing). 
- So far contains tests for `xml_parser.py`, `TrainInfo`, `SectoriseRSX.py`, needs extending. 


## Testing
 - Run all tests; copy into cmd

    `.\venv\Scripts\python.exe -m pytest`


## Installation Instructions 


### 1. Download Python 

- Go to [this link](https://www.python.org/downloads/release/python-3129/), scroll down, find the 64 bit windows installer. Click the version (displayed) below to install

    ![Python installer](/images/python_install.png "Page")

- When the installer is finished, run it from your downloads folder. Leave everything as default and click skip/next.

### 2. Clone the repository 

- Add instructions here (todo)

### 3. Downloading / Setup of IDE (skip if not developing)

- Add instructions here (todo)

### 4. Run the following commands in a Python Terminal located in the root directory. 
- For all commands, replace the `<username>` part with your own username (e.g r123456)

- Open a Python terminal inside the `Python_TTSummary` folder (the repository you just cloned/downloaded). This is the 'root' directory. In the Python terminal run the following commands.

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

- Install pywin32 (requires .whl file, cannot be downloaded manually)

    `.\venv\Scripts\python.exe -m pip install C:\Users\<username>\Downloads\pywin32-311-cp312-cp312-win_amd64.whl`

- Now tell Python this code is a 'package':

    `.\venv\Scripts\python.exe -m pip install -e .`

### 5. Setup complete
- At this point, TAIPAN and all its dependencies should be installed and ready to use. To verify, run the following (in the same place you ran the previous commands) and if no errors pop up the installation succeeded. 

    `.\venv\Scripts\python.exe -c "import taipan"`

    If an error popped up, ask for help. Otherwise, you’re good to go 🚀



