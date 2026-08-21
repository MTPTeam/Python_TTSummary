## Freight timetabling code 

This folder contains code for generating RSX files containing freight trains and processing them into train movement tables. 

- `RSX_to_TM` - processes RSX files (containing freight + SEQ) into train movement tables (raw format). 

- `locations.py` - ported from MTP code, required for train movements code to run

- `build_rsx_{timetable type}.py` - this is the code that builds freight RSX files that gets uploaded into railsys and will be modelled into Soft Open and the Wave timetables. The code processes the freight trains from `Regional Path Summary.xlsx` sheet and outputs a separate RSX file by stage (Stage 1 expand, stage 2, stage 3 and stage 4 tabs in the excel sheet). Includes repositioning freight movements. 

- `04 train graphs_freight.ipynb` - notebook for generating train graphs from raw train movement file outputs that include freight, with new corresponding `train_graph_stns_mtp.json`. 


### `build_rsx_freight.py`

- The script gets the train from the regional path summary sheets, however it gets the timings from the reformatted timetables sheet. This is so runtimes can be derived by Railsys automatically  

- Since the timings are derived from the reformatted timetables, you may need to add to the `DEPARTURE_TIMES_XLSX` variable depending on what stage trains you are generating. For example, stage 1 requires the timings to be derived from the reformatted NCL timetable but stage 4 requires the west moreton reformatted timetables. Some of the stage sheets are not exclusive to one freight line, so this variable can search through multiple timetables by train ID to find all the train times. To set the stage sheet, just change `STAGE` variable at the top of the code.


#### Making changes to `build_rsx_freight_{timetable}.py`
- There are separate timetable generator files for SOTT and Wave. 
- If in the output RSX, the `stationName` element is Unknown, it means the location name isnt is `locations.py`. To resolve this, modify `EXTRA_STATION_NAMES` with actual names. It has to match what railsys geo has for it's internal name. 
- Excluding a station from output RSX: modify `DELETE_STATIONS`
- Sometimes Vizi has slightly different station naming conventions to Railsys. Rename using `STATION_RENAMES` variable - map all instances of x to y (new name). 
- Some stations need their trackIds to be set as timing points in Railsys to be recognised correctly. Modify `TIMING_POINTS_OVERRIDES`. You can also change the `T` to what letter you like in case that is needed.
- Some stations need platform changes with new geo state - modify `PLATFORM_OVERRIDES` to change platform numbers
- In some cases, all instances of platform 1 should be changed to 2 . Modify `FLIP_PLATFORMS` to add stations where platforms should be flipped.
- Sometimes stations need a fixed departure flag - add it to `FIXED_DWELL_STATIONS`. 
- Direction is not fully known for each path, to override direction for a train or route modify `REPOS_DIRECTION_OVERRIDES`. See the first element for an example of how a direction override is applied to a train number
- `LIVESTOCK_CDS` / `LIVESTOCK_PRIORITY_STATIONS` - should not need to be modified. These are used to remap ICE trains into empty/full livestock trains.
- `TRAIN_TYPE_ID` is the dictionary mapping of Vizi train types -> Railsys train types. This is required since railsys doesn't have all the train types specified, however should not need to be modified. 
- For the Wave timetables, some trackIDs will need to be completely updated. See `TRACK_ID_OVERRIDES` in build_rsx_wave.py.

