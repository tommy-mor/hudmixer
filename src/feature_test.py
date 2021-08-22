from hud import ImportHud, BaseHud
import features
import shutil
from test_util import deep_compare


class hud_test:
    def __init__(self, fname):
        self.fname = fname

    def __enter__(self):
        hud = BaseHud(self.fname)

        self.outname = "../huds/outhud"

        # ignore if dir not there
        shutil.rmtree(self.outname, ignore_errors=True)

        self.out = features.OutHud(hud, self.outname)

        return self.out

    def __exit__(self, type, value, traceback):
        self.out.export()

        deep_compare(self.fname, self.outname)

try:
    with hud_test("../huds/TF2-Default-Hud") as out:
        improved = ImportHud("../huds/rayshud/")
        
        out.add_feature(features.Health(improved))
except Exception as e:
    print(e)

# TODO improved deault hud tests, where some files are completely unchanged. in that case, fill in required values from default tf2 hud.
