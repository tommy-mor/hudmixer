from hud import ImportHud, BaseHud, OutHud
import features
import shutil
from test_util import deep_compare

import feature_list as fl


class hud_test:
    def __init__(self, fname):
        self.fname = fname

    def __enter__(self):
        hud = BaseHud(self.fname)

        self.outname = "/home/tommy/.steam/steam/steamapps/common/Team Fortress 2/tf/custom/outhud"

        # ignore if dir not there
        shutil.rmtree(self.outname, ignore_errors=True)

        self.out = OutHud(hud, self.outname)

        return self.out

    def __exit__(self, type, value, traceback):
        self.out.export()

        deep_compare(self.fname, self.outname)


with hud_test("../huds/flawhud") as out:
    improved = ImportHud("../huds/rayshud/")

    out.add_feature(fl.Health(improved))

# TODO improved deault hud tests, where some files are completely unchanged. in that case, fill in required values from default tf2 hud.
