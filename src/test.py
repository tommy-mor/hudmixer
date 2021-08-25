from model.hud import ImportHud, BaseHud, OutHud
import model.feature_list as fl
import glob
import shutil

from itertools import permutations

huddirs = glob.glob('../huds/*')
for h in huddirs:
    basehud = BaseHud(h)

    without = list(set(huddirs) - set([h]))
    orderings = permutations(without, len(fl.classes))

    print('basehud', basehud.srcdir)
    for ordering in orderings:

        shutil.rmtree('../outhud')
        outhud = OutHud(basehud, '../outhud')
        for feature_cls, huddir in zip(fl.classes, ordering):
            print(feature_cls.__name__, 'from', huddir)
            outhud.add_feature(feature_cls(ImportHud(huddir)))
        outhud.export()
