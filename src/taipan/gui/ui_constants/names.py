SCRIPTS = {

    "Timetable Information": {

        "style": "normal",

        "groups": {

            "": [
                ("Timetable Summary",  "_run_tt_summary",        "Generate multiple reports"),
                ("Working Timetable",  "_run_wtt",               "Generate the working timetable from RSX"),
                ("Public Timetable",   "_run_ptt",               "Generate public timetable workbooks from RSX"),
                ("RunInfo",            "_run_runinfo",           "Generate run information report from RSX"),
                ("Train Movements",    "_run_movements",         "Generate train movements report from RSX"),
                ("TripCount",          "_run_tripcount",         "Count trips by line and period from RSX"),
                ("Runtime Dashboard",  "_run_runtime",           "Generate runtime dashboard from RSX"),
                ("KM Calculation",     "_run_km",                "Calculate kilometres by service from Excel export of RSX"),

            ],

            "First Last": [
                ("First Last",         "_run_first_last",        "Generate detailed first and last service report from RSX"),
                ("Simple First Last",  "_run_simple_first_last", "Simplified first and last service report from RSX"),
                ("First Last Graph",   "_run_first_last_graph",  "Graph first and last services from single or multiple RSX files"),

            ],
        }
    },

    "Timetable Development": {

        "style": "normal",

        "groups": {

            "": [
                ("QA",     "_run_qa",     "Run quality assurance checks on RSX"),
                ("Slicer", "_run_slicer", "Slice timetable data"),

            ],

            "Stabling": [
                ("Stabling Balance", "_run_stabling_balance", "Check stabling balance across yards"),
                ("Stabling Count",   "_run_stabling_count",   "Count stabling movements"),
                ("Stabling Graph",   "_run_stabling_graph",   "Graph stabling over time"),

            ],

            "Renamers": [
                ("Assign LineIDs",  "_run_assign_lineids", "Assign line IDs to services"),
                ("Train Renamer",   "_run_train_renamer",  "Rename trains in RSX in bulk"),
                ("Sectorise RSX",   "_run_sectorise",      "Sectorise RSX file"),

            ],

        }

    },

    "ITOPS": {

        "style": "normal",
        "note": "⚠ Do not override current rsl files.\nCopy all rsl files in geo/dat to a separate folder first.",
        "groups": {

            "": [
                ("ITOPS TT Conversion",  "_run_itops_tt",  "Convert timetable to ITOPS format"),
                ("ITOPS Geo Conversion", "_run_itops_geo", "Convert geo data to ITOPS format"),

            ],

        },

    },

    "HASTUS": {
        "style": "normal",
        "groups": {
            "": [
                ("HASTUS",            "_run_hastus",          "Export RSX to HASTUS format"),
                ("HASTUS (ttrefnum)", "_run_hastus_ttrefnum", "Export RSX to HASTUS (ttrefnum)"),

            ],

        }

    },

    "Deployment Plan": {

        "style": "normal",
        "note": "Requires an RSX and excel\n\"train characteristics\" export.",
        "groups": {

            "": [
                ("NGR Weekly Plan", "_run_ngr_weekly", "Generate NGR weekly deployment plan"),
                ("NGR Daily Plan",  "_run_ngr_daily",  "Generate NGR daily deployment plan"),

            ],

        },

    },

    "Others": {

        "style": "normal",
        "groups": {

            "": [

                ("VAS Extractor",      "_run_vas",      "Extract VAS data from RSX"),
                ("Closure Impacts",    "_run_closure",  "Assess closure impacts on services"),
                ("Timetable Archiver", "_run_archiver", "Archive timetable files"),

            ],

        }

    },

    "TDS": {

        "style": "normal",

        "groups": {

            "": [

                ("TDS + Journey Planner", "_run_tds_jp",  "Export TDS with Journey Planner data"),
                ("TDS → WorkingTT",       "_run_tds_wtt", "Convert TDS to Working Timetable"),
                ("TDS → PublicTT",        "_run_tds_ptt", "Convert TDS to Public Timetable"),

            ],

        }

    },

}

COLUMN_ORDER = [

    ["Timetable Information"],
    ["Timetable Development"],
    ["ITOPS", "Deployment Plan"],
    ["HASTUS", "Others", "TDS"],

]
