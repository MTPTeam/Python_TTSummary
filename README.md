# TAIPAN codebase


## Changes to codebase

- `SectoriseRSX.py` 
- `StablingCountStepGraph.py` 
- `constants/`
- `xml_parser.py`
- `xml_processor.py`
- `utils.py`


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

- Now tell Python this code is a 'package':

    `.\venv\Scripts\python.exe -m pip install -e .`

### 5. Setup complete
- At this point, TAIPAN and all its dependencies should be installed and ready to use. To verify, run the following (in the same place you ran the previous commands) and if no errors pop up the installation succeeded. 

    `.\venv\Scripts\python.exe -c "import taipan"`

    If an error popped up, ask for help. Otherwise, you’re good to go 🚀



