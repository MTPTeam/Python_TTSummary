
import xlsxwriter
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet

from MTP_constants import (FAMILY_BG, ALERT, GREY, UNBALANCED_YELLOW, WHITE, STYLE_VARIANTS, GENERIC_STYLES, BORDER_STYLES, SEMANTIC_STYLES)


def writecell_unbalanced(Summary, r,c,value,unbalancedfont,balancedfont):
    """ If cell does not equal zero, assign a cell format to highlight inbalance """
    
    if value != 0:
        Summary.write(r,c,value,unbalancedfont)
    else:
        Summary.write(r,c,value,balancedfont)


def write_unit_totals(sheet, sum_of_units, n_units, r, c, font):
    """ 
    Used in write_day function, writes the last column in both in and out blocks,
    If only one entry of a unit type, will skip the merge-range step as this will error
    """
    if n_units == 1:
        sheet.write(r, c, sum_of_units, font)
    else:
        sheet.merge_range(r, c, r+n_units-1, c, sum_of_units, font)    



def build_excel_formats(workbook):
    """
    Build all Excel formats.

    Returns:
        dict[family][variant] -> xlsxwriter Format
    """

    formats = {}

    for family, bg_colour in FAMILY_BG.items():
        base = {
            "align": "center",
            "bg_color": bg_colour,
        }

        formats[family] = {}

        for variant, overrides in STYLE_VARIANTS.items():
            
            fmt = dict(base)
            fmt.update(overrides)

            formats[family][variant] = workbook.add_format(fmt)

    return formats



def build_generic_formats(workbook):
    """
    Builds non-unit Excel formats:
    titles, headers, borders, semantic flags.
    """
    formats = {}

    for name, style in GENERIC_STYLES.items():
        formats[name] = workbook.add_format(style)

    for name, style in BORDER_STYLES.items():
        formats[name] = workbook.add_format(style)

    for name, style in SEMANTIC_STYLES.items():
        formats[name] = workbook.add_format(style)

    return formats
