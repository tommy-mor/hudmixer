import hud
import read
import filecmp
import difflib
import shutil
import os
from test_util import deep_compare



class hud_test:
    def __init__(self, fname):
        self.fname = fname

    def __enter__(self):
        self.hud = hud.BaseHud(self.fname)
        return self.hud

    def __exit__(self, type, value, traceback):
        outname = "../huds/outhud"
        # shutil.rmtree(outname)
        # self.hud.export(outname)

        #deep_compare(self.hud.srcdir, outname)


with hud_test("../huds/idhud") as h:
    new = h.splice(
        "resource/clientscheme_small.res",
        {"Scheme": {"Colors": {'TommyColor': '0 0 0 0'}}},
    )
    new = h.splice(
        "resource/clientscheme.res",
        {"Scheme": {"Fonts":
                    {'Crosshairs24': {"1": {'meme': 'stuff'}}}}}
    )
    new = h.splice(
        "resource/clientscheme_small.res",
        {"Scheme": {"NewColors": {'TommyColor': '0 0 0 0'}}},
    )
    try:
        parsed = read.Parser(new).items
        assert parsed['Scheme']['NewColors']['TommyColor'] == '0 0 0 0'
    except Exception as e:
        print(e)
        import pdb
        pdb.post_mortem()
    #print(new)


st = "blah blah blah Source"
a = hud.find_ignoring(st, "Source")
assert st[a:].startswith("Source")

st = "blah blah blah Source Source"
a = hud.find_ignoring(st, "Source")
assert st[a:] == "Source Source"

st = """
#include blah Source blah

Source {}
"""
a = hud.find_ignoring(st, "Source")
assert st[a:] == "Source {}\n"

assert hud.string_splice("abcd", "HAH", 2) == "abHAHcd"

st = """
#base "../arsotieanrstoiaernst"

Source {}
"""
a = hud.find_ignoring(st, "Source")
assert st[a:] == "Source {}\n"

# TODO make it actually modify file, then start working on feature extraction
# code.
# TODO figure out weird syntax on idhud/resource/clientscheme.res:767

with hud_test("../huds/TF2-Default-Hud") as h:
    new = h.splice(
        "resource/clientscheme.res",
        {"Scheme": {"Fonts":
                    {'Crosshairs24': {"1": {'meme': 'stuff'}}}}}
    )
    parsed = read.Parser(new).items
    parsed['Scheme']['Fonts']['Crosshairs24']['1']['meme'] == 'stuff'
    #print(new)


# multiple splices

with hud_test("../huds/TF2-Default-Hud") as h:
    parsed = h.file_items('resource/clientscheme.res')

    oldfonts = parsed['Scheme']['Fonts'].keys()
    oldfont = parsed['Scheme']['Fonts']['HudFontSmall']

    assert '2' not in oldfont

    new = h.splice(
        "resource/clientscheme.res",
        {"Scheme": {"Fonts":
                    {'Crosshairs24': {"1": {'meme': 'stuff'}},
                     'HudFontSmall': {"2": {'xd': 'test'}}}}}
    )

    parsed = read.Parser(new).items
    newfonts = set(parsed['Scheme']['Fonts'].keys()) - set(oldfonts)

    assert parsed['Scheme']['Fonts']['Crosshairs24']['1']['meme'] == 'stuff'

    oldfont = parsed['Scheme']['Fonts']['HudFontSmall']
    assert oldfont['2'] == {'xd': 'test'}


# multiple splices
