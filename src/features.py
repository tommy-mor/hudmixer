from hud import ImportHud, BaseHud
from pathlib import Path
from shutil import copytree


class Feature:
    pass


class Health(Feature):
    def __init__(self, hud):
        assert hud.__class__ == ImportHud

        self.fromhud = hud

        # fname :=> [(from, to)] translations
        self.file_copies = {}
        # fname :=> splice dict
        self.file_changes = {}

    def gather(self, outdir):
        self.collect_file("resource/ui/hudammoweapons.res")
        # TODO hudlayout

    def collect_file(self, f):
        # copy entire file
        # TODO

        # collect all color definitions
        colors = self.fromhud.collect(f, ["fgColor", "bgColor"])
        print('colors', colors)

        colordefs = self.fromhud.collect_color_defs(colors)
        print('colordefs', colordefs)

        # check that colors are colors
        for v in colordefs.values():
            a, b, c, d = v.split(' ')
            int(a), int(b), int(c), int(d)

        fonts = self.fromhud.collect(f, ["font", "font_minmode"])
        fonts = set(list(fonts))
        fontdefs, fontfiledefs, fontpaths = self.fromhud.collect_font_defs(fonts)

        #{HERE}
        # TODO rename to avoid collisions
        # TODO have all these methods return splice dicts



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
            f.gather(outdir)

        for fname, newtext in []:
            newfname = Path(outdir) / fname
            with open(newfname, 'w') as f:
                f.write(newtext)

        return outdir
