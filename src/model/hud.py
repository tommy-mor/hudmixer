import os
import model.read as read
from pathlib import Path
from shutil import copytree, copy, move
from model.features import Feature
from model.util import ResDict

from model.animation import AnimationParser, ManifestParser, format_manifest, format_events

# for backups when files are missing in custom huds
DEFAULT_HUD = Path('../huds/TF2-Default-Hud')

# TODO use this more
def gen_name(desired, existing_names):
    if desired in existing_names:
        root, end = desired.split('.')
        desired = root + '_' + '.' + end
        return gen_name(desired, existing_names)
    else:
        return desired


class HudException(Exception):
    pass


def ensure_is_hud(fname):
    path = Path(fname)

    clientscheme = path / "resource" / "clientscheme.res"
    if not (clientscheme.exists() and not clientscheme.is_dir()):
        raise HudException('this directory is not a hud')

    hudlayout = path / "scripts" / "hudlayout.res"
    if not (hudlayout.exists() and not hudlayout.is_dir()):
        raise HudException('this directory is not a hud')


def collect_values_from_keys(dic, keys):
    ret = []
    def search_rec(dic):
        for key, value in dic.items():
            if key in keys:
                ret.append(value)
            else:
                if type(value) == ResDict:
                    search_rec(value)

    search_rec(dic)
    return ret


class BaseHud:
    # hud that we are importing properties into.
    # will have to be able to export into final hud, splicing in important info

    def __init__(self, fname):
        self.srcdir = Path(fname)
        self.translation_key = self.srcdir.name

        # relativefname :=> new file contents
        ensure_is_hud(fname)


class ImportHud:
    # TODO make super class for huds with hud.pars_file(fname)

    # hud that we are going to gather features from.
    # need to extract entire files, and everything referenced in them.

    def __init__(self, fname):
        self.srcdir = Path(fname)
        ensure_is_hud(fname)
        self.translation_key = self.srcdir.name

        # precompute frequently referenced files
        self.clientscheme = read.parse_file(
            self.srcdir / "resource/clientscheme.res"
        )

        self.hudlayout = read.parse_file(
            self.srcdir / "scripts/hudlayout.res"
        )

        self.read_animation_manifest()

    def read_animation_manifest(self):
        self.events = {}

        manifest = self.srcdir / 'scripts' / 'hudanimations_manifest.txt'
        if manifest.resolve().exists():
            with open(manifest) as f:
                files = ManifestParser(f.read()).animation_files
                
            for path in files:
                # problem: these should be in order, they are not.
                newpath = self.srcdir / path
                if newpath.resolve().exists():
                    with open(newpath) as f:
                        # shallow merge
                        self.events.update(AnimationParser(f.read()).events)
        else:
            hudanimations = self.srcdir / 'scripts' / 'hudanimations.txt'
            with open(hudanimations) as f:
                self.events.update(AnimationParser(f.read()).events)

    def collect(self, f, qry):

        if (self.srcdir / f).exists():
            items = read.parse_file(self.srcdir / f)
        else:
            # fallthrough for missing files
            items = read.parse_file(DEFAULT_HUD / f)
        return collect_values_from_keys(items, qry)

    def collect_clientscheme(self, path, keys):
        missing = []

        def rec(dic, path, keys):
            if len(path) == 0:
                for key in keys:
                    if key not in dic:
                        print('could not find', key)
                        missing.append(key)
                ret = ResDict()
                for key in keys:
                    if key in dic:
                        ret[key] = dic[key]
                return ret
            else:
                key = path[0]
                return rec(dic[key], path[1:], keys)

        found = rec(self.clientscheme, path, keys)
        defaultclientscheme = DEFAULT_HUD / 'resource/clientscheme.res'
        founddefault = rec(read.parse_file(defaultclientscheme), path, [*missing])

        found.deep_merge_with(founddefault)

        return found

    def parse_file(self, f):
        d = self.srcdir / f
        if not d.exists():
            print('cound not find', f, 'using default')
            d = DEFAULT_HUD / f

        return read.parse_file(d)

    def find_font_defs(self, fontnames):

        fonts = []
        fontfiles = []

        for key, val in self.clientscheme['Scheme']['CustomFontFiles'].items():
            if type(val) == ResDict:
                assert 'name' in val
                assert 'font' in val

                if val['name'] in fontnames:
                    fonts.append(val)
                    fontfiles.append(val['font'])

        return fonts, fontfiles

    def collect_color_defs(self, colors):

        return self.collect_clientscheme(['Scheme', 'Colors'], colors)

    def collect_font_defs(self, fonts):
        fonts = self.collect_clientscheme(['Scheme', 'Fonts'], fonts)
        font_names = collect_values_from_keys(fonts, ["name"])

        font_names = list(set(font_names))

        # TODO there can be fontfiles at BitmapFontFiles, ?others?,
        # not just CustomFontFiles
        font_definitions, font_paths = self.find_font_defs(font_names)
        return fonts, font_definitions, font_paths


class OutHud:
    def __init__(self, base, outdir):
        assert base.__class__ == BaseHud
        self.srcdir = base.srcdir

        self.features = []
        # can this be parameter to export method?
        self.outdir = Path(outdir)

    def add_feature(self, f):
        assert isinstance(f, Feature)

        self.features.append(f)

    def export(self):
        outdir = self.outdir
        outdir_ = copytree(self.srcdir, outdir)

        assert outdir == outdir_

        for f in self.features:
            # this modifies many fields on f
            f.gather()

        # todo translations/renaming

        colors = {'Scheme':
                  {'Colors': {k: v for f in self.features for k, v in f.color_defs.items()}}}

        self.splice('resource/clientscheme.res', colors)
        # todo check no font overlap
        fonts = {'Scheme':
                 {'Fonts':
                  {k: v
                   for f in self.features
                   for k, v in f.font_defs.items()}}}

        self.splice('resource/clientscheme.res', fonts)

        # get max index of existing custom font definitions
        customfonts = read.parse_file(self.outdir / 'resource/clientscheme.res')['Scheme']['CustomFontFiles']
        maxkey = max(int(k) for k in customfonts.keys()) + 1

        filedefs = set((d['name'], d['font']) for f in self.features for d in f.font_filedefs)

        # splice in new custom font definitions
        i = maxkey
        for filedef in filedefs:
            ins = {'name': filedef[0], 'font': filedef[1]}
            self.splice('resource/clientscheme.res',
                        {'Scheme': {'CustomFontFiles':
                                    {str(i): ins}}})
            i += 1

        topkey, _ = read.parse_file(self.outdir / 'scripts/hudlayout.res').popitem()

        hudlayout = {topkey: {k: v for f in self.features for k, v in f.hudlayout_changes.items()}}
        self.splice('scripts/hudlayout.res', hudlayout)

        for f in self.features:
            for fname, splice_dict in f.file_copies.items():
                self.replace(fname, splice_dict, f.fromhud.translation_key)

        fontpath = (self.outdir / 'mixer' / 'fonts')
        fontpath.mkdir()

        for f in self.features:
            for frompath, topath in f.raw_copies.items():
                copy(frompath, self.outdir / topath)
        # TODO copy raw images

        new_events = {event: cmds for f in self.features for event, cmds in f.event_copies.items()}
        self.write_events(new_events)

        return outdir

    def replace(self, fname, dic, tk):
        fname = self.outdir / fname

        with open(fname, 'w') as f:
            f.write(format_dict(0, dic))
            f.write('\n// file imported by mixer from %s' % tk)

    def splice(self, fname, splice_dict, tk = None):
        print('splicing', fname, list(splice_dict.keys()))

        if type(splice_dict) == dict:
            splice_dict = ResDict(dict=splice_dict)

        fname = self.outdir / fname
        assert fname.exists() and fname.suffix == ".res"

        old_file_new_name = fname.with_name(fname.stem + '_mixer_base.res')

        #included_file = fname.with_name(fname.stem + '_mixer_' + tk + '.res')
        (self.outdir / 'mixer').mkdir(exist_ok=True)
        included_file = self.outdir / 'mixer' / (fname.stem + '_mixer' + ('_' + tk if tk else '') + '.res')

        included_file_name = os.path.relpath(included_file, fname.parent)
        old_file_new_name_nice = os.path.relpath(old_file_new_name, fname.parent)

        if old_file_new_name.resolve().exists():
            # we have already modified things.
            items = read.parse_file(included_file)
            splice_dict.deep_merge_with(items)
        else:
            move(fname, old_file_new_name)
            with open(fname, 'w') as f:
                f.write('"#base" "%s"\n' % included_file_name)
                f.write('"#base" "%s"\n' % old_file_new_name_nice)

        with open(included_file, 'w') as f:
            f.write(format_dict(0, splice_dict))

    def write_events(self, events):
        manifest = self.outdir / 'scripts' / 'hudanimations_manifest.txt'
        if manifest.resolve().exists():
            with open(manifest) as f:
                files = ManifestParser(f.read()).animation_files
                new_name = gen_name('scripts/hudanimations_mixer.txt', files)
                files.insert(0, new_name)
        else:
            files = ['scripts/hudanimations_mixer.txt',
                     'scripts/hudanimations.txt',
                     'scripts/hudanimations_tf.txt']
            new_name = files[0]

        with open(manifest, 'w') as f:
            f.write(format_manifest(files))

        with open(self.outdir / new_name, 'w') as f:
            f.write(format_events(events))


def ident(n):
    return "\t" * n


def wrap(string):
    if len(string) == 0:
        return '""'
    elif not string[0] != '"' and string[-1] != '"':
        raise ('bad', string)
    else:
        return '"' + string + '"'


def format_dict(i, dic, skip=True):
    if type(dic) == str:
        return wrap(dic)

    if not skip:
        st = ident(i) + "{\n"
    else:
        i -= 1
        st = ""
    for k, v in dic.items():
        assert type(k) == str
        st += ident(i + 1) + wrap(k)
        st += "  " + format_dict(i + 1, v, skip=False)
        st += "\n"
    if not skip:
        st += ident(i) + "}"
    return st
