from model.hud import ImportHud, BaseHud, OutHud
import model.read as read
import model.features as features

import model.feature_list as fl
import glob
import shutil

from itertools import permutations
from pathlib import Path


outdir = Path('../outhud')
def big_test():
    # deli hud is nested..
    huddirs = [dir for dir in glob.glob('../huds/*') if 'Deli' not in dir]
    for h in huddirs:
        h = Path(h)
        basehud = BaseHud(h)

        without = list(set(huddirs) - set([h]))
        orderings = permutations(without, len(fl.classes))

        print('basehud', basehud.srcdir)
        for ordering in orderings:

            if outdir.exists():
                shutil.rmtree(outdir)
            assert not outdir.exists()
            outhud = OutHud(basehud, outdir)
            for feature_cls, huddir in zip(fl.classes, ordering):
                print(feature_cls.__name__, 'from', huddir)
                outhud.add_feature(feature_cls(ImportHud(huddir)))
            outhud.export()


def overwrite_test():
    # this failed at one point because m0rehud hudlayout had multiple hudlayouts,
    # and they were getting merged improperly

    basehud = BaseHud('../huds/rayshud')
    importhud = ImportHud('../huds/m0rehud/')

    shutil.rmtree(outdir, ignore_errors=True)
    outhud = OutHud(basehud, outdir)
    outhud.add_feature(fl.Ammo(importhud))
    outhud.export()

    hl = read.parse_file(outhud.outdir / 'scripts' / 'hudlayout.res')
    ammo = hl['Resource/HudLayout.res']['HudWeaponAmmo']
    #print('ammo', ammo)
    assert ammo['xpos'] == '0'
    assert ammo['xpos_minmode'] == '0'

    test = ImportHud(outdir)
    fonts = test.collect('resource/ui/hudammoweapons.res', features.FONT_STRINGS)
    colors = test.collect('resource/ui/hudammoweapons.res', features.COLOR_STRINGS)
    # make sure all fonts are in clientscheme
    for font in fonts:
        assert 'm0re' in font
        assert font in test.clientscheme['scheme']['fonts']
    for color in colors:
        assert 'm0re' in color
        assert color in test.clientscheme['scheme']['colors']


def caseinsensitive_test():
    # this must work because key lookups should be case insensitive...
    # because one of the fonts in ahud is defined with different cases, this required the ResDict class
    basehud = BaseHud('../huds/rayshud')
    importhud = ImportHud('../huds/ahud/')

    shutil.rmtree(outdir, ignore_errors=True)
    outhud = OutHud(basehud, outdir)
    outhud.add_feature(fl.Scoreboard(importhud))
    outhud.export()

    hl = read.parse_file(outhud.outdir / 'resource' / 'clientscheme.res')
    colors = hl['Scheme']['Colors']
    assert 'Hudblack_ahud' in colors


import model.read as r

def parser_tests():
    a = r.Buf('abcd')
    a.eat_white_space()
    assert a.st == 'abcd'

    a = r.Buf('   abcd')
    a.eat_white_space()
    assert a.st == 'abcd'

    a = r.Buf('   abcd   ')
    a.eat_white_space()
    assert a.st == 'abcd   '


    a = r.Buf('   abcd   ')
    b = a.eat_until('b')
    assert b == '   a'
    assert a.st == 'bcd   '

    a = r.Parser("""//
    //
    // TRACKER SCHEME RESOURCE FILE
    //
    // sections:
    //		colors			- all the colors used by the scheme
    //		basesettings	- contains settings for app to use to draw controls
    //		fonts			- list of all the fonts used by app
    //		borders			- description of all the borders
    //
    //
    Scheme {}""")
    assert len(a.items['Scheme']) == 0


    # can parse the one line things
    a = r.Parser("""Scheme {blah blah}""")
    assert a.items['Scheme']['blah'] == 'blah'

    a = r.Parser("""Scheme {"blah" "blah"}""")
    assert a.items['Scheme']['blah'] == 'blah'

    
    a = r.Parser(""""Scheme"{blah blah}""")
    assert a.items['Scheme']['blah'] == 'blah'

    a = r.Parser("""Scheme{blah blah}""")
    assert a.items['Scheme']['blah'] == 'blah'

    a = r.Parser("""Scheme{"te st tt" [xb360]"blah"}""")
    assert a.items['Scheme']['te st tt'] == 'blah'

overwrite_test()
caseinsensitive_test()
parser_tests()

#shutil.rmtree(outdir)
#big_test()

# TODO test things like idhud