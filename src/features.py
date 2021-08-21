from hud import ImportHud, BaseHud
from pathlib import Path
from shutil import copytree


class Feature:
    pass


class Health(Feature):
    def __init__(self, hud):
        assert hud.__class__ == ImportHud

        self.fromhud = hud

    def gather(self):
        self.collect_file("resource/ui/hudammoweapons.res")

    def collect_file(self, f):
        # copy entire file
        # TODO

        # collect all color definitions
        colors = self.fromhud.collect_colors(f)
        print('colors', colors)

        colordefs = self.fromhud.collect_color_defs(colors)
        print('colordefs', colordefs)

        # collect all font definitions
        pass


class OutHud:
    def __init__(self, base, outdir):
        assert base.__class__ == BaseHud
        self.srcdir = base.srcdir

        self.features = []
        # can this be parameter to export method?
        self.outdir = outdir

    def add_feature(self, f):
        assert isinstance(f, Feature)

        self.features.append(f)

    def export(self):
        outdir = self.outdir
        outdir_ = copytree(self.srcdir, outdir)

        assert outdir == outdir_
        outdir = Path(outdir)

        # TODO go through features, and apply them
        for f in self.features:
            f.gather()

        for fname, newtext in []:
            newfname = Path(outdir) / fname
            with open(newfname, 'w') as f:
                f.write(newtext)

        return outdir
