from model.hud import ImportHud, BaseHud, OutHud
import model.read as read

import model.feature_list as fl
import glob
import shutil

from itertools import permutations


outdir = '../outhud'
def big_test():
    huddirs = glob.glob('../huds/*')
    for h in huddirs:
        basehud = BaseHud(h)

        without = list(set(huddirs) - set([h]))
        orderings = permutations(without, len(fl.classes))

        print('basehud', basehud.srcdir)
        for ordering in orderings:

            shutil.rmtree(outdir, ignore_errors=True)
            outhud = OutHud(basehud, outdir)
            for feature_cls, huddir in zip(fl.classes, ordering):
                print(feature_cls.__name__, 'from', huddir)
                outhud.add_feature(feature_cls(ImportHud(huddir)))
                outhud.export()


def overwrite_test():
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


def caseinsensitive_test():
    # this must work because key lookups should be case insensitive...
    basehud = BaseHud('../huds/rayshud')
    importhud = ImportHud('../huds/ahud/')

    shutil.rmtree(outdir, ignore_errors=True)
    outhud = OutHud(basehud, outdir)
    outhud.add_feature(fl.Scoreboard(importhud))
    outhud.export()

    hl = read.parse_file(outhud.outdir / 'resource' / 'clientscheme.res')
    colors = hl['Scheme']['Colors']
    assert 'Hudblack_ahud' in colors


overwrite_test()
caseinsensitive_test()
shutil.rmtree(outdir)