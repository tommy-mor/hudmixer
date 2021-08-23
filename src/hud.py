import os
import read
from pathlib import Path
from shutil import copytree, copy, move
from features import Feature


def ensure_is_hud(fname):
    path = Path(fname)

    clientscheme = path / "resource" / "clientscheme.res"
    assert clientscheme.exists() and not clientscheme.is_dir()

    hudlayout = path / "scripts" / "hudlayout.res"
    assert hudlayout.exists() and not hudlayout.is_dir()


class BaseHud:
    # hud that we are importing properties into.
    # will have to be able to export into final hud, splicing in important info

    def __init__(self, fname):
        self.srcdir = Path(fname)

        # relativefname :=> new file contents
        self.changedFiles = {}
        ensure_is_hud(fname)


def permute(strings):
    r = []
    for s in strings:
        r.append(s)
        r.append('"' + s + '"')
        r.append(s.lower())
        r.append('"' + s.lower() + '"')
    return list(set(r))


def collect_values_from_keys(dic, keys):
    ret = []

    COLOR_KEYS = keys

    def search_rec(dic):
        for key, value in dic.items():
            if key in COLOR_KEYS:
                ret.append(value)
            else:
                if type(value) == dict:
                    search_rec(value)

    search_rec(dic)
    return ret


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

    def collect(self, f, qry):
        COLOR_KEYS = permute(qry)

        items = read.parse_file(self.srcdir / f)
        return collect_values_from_keys(items, COLOR_KEYS)

    def collect_at(self, dic, path, keys, wrap=False):

        def rec(dic):
            if len(path) == 0:
                return {key: dic[key] for key in keys}
            else:
                key = path.pop()
                #return {key: rec(dic[key])}
                return rec(dic[key])

        path.reverse()
        return rec(dic)

    def find_font_defs(self, fontnames):

        fonts = []
        fontfiles = []

        for key, val in self.clientscheme['Scheme']['CustomFontFiles'].items():
            if type(val) == dict:
                assert 'name' in val
                assert 'font' in val

                if val['name'] in fontnames:
                    fonts.append(val)
                    fontfiles.append(val['font'])

        return fonts, fontfiles

    def collect_color_defs(self, colors):

        return self.collect_at(self.clientscheme, ['Scheme', 'Colors'], colors)

    def collect_font_defs(self, fonts):
        fonts = self.collect_at(self.clientscheme, ['Scheme', 'Fonts'], fonts)
        font_names = collect_values_from_keys(fonts, permute(["name"]))

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
                  {'Colors': {k: v for k, v in f.color_defs.items() for f in self.features}}}

        self.splice('resource/clientscheme.res', colors)
        # todo check no font overlap
        fonts = {'Scheme':
                 {'Fonts':
                  {k: v for k, v in f.font_defs.items()
                   for f in self.features}}}
        self.splice('resource/clientscheme.res', fonts)

        # get max index of existing custom font definitions
        customfonts = read.parse_file(self.outdir / 'resource/clientscheme.res')['Scheme']['CustomFontFiles']
        maxkey = max(int(k) for k in customfonts.keys()) + 1

        filedefs = set((d['name'], d['font']) for d in f.font_filedefs for f in self.features)

        # splice in new custom font definitions
        i = maxkey
        for filedef in filedefs:
            ins = {'name': filedef[0], 'font': filedef[1]}
            self.splice('resource/clientscheme.res',
                        {'Scheme': {'CustomFontFiles':
                                    {str(i): ins}}})
            i += 1

        topkey, _ = read.parse_file(self.outdir / 'scripts/hudlayout.res').popitem()

        hudlayout = {topkey: {k: v for k, v in f.hudlayout_changes.items() for f in self.features}}
        self.splice('scripts/hudlayout.res', hudlayout)

        for f in self.features:
            for fname, splice_dict in f.file_copies.items():
                self.replace(fname, splice_dict, f.fromhud.translation_key)

        fontpath = (self.outdir / 'mixer' / 'fonts')
        fontpath.mkdir()

        for f in self.features:
            for frompath, topath in f.raw_copies.items():
                copy(frompath, self.outdir / topath)
        # todo copy files (using splice?)
        # todo copy raw font files
        # copy raw images

        return outdir

    def replace(self, fname, dic, tk):
        fname = self.outdir / fname

        with open(fname, 'w') as f:
            f.write(format_dict(0, dic))
            f.write('\n// file imported by mixer from %s' % tk)

    def splice(self, fname, splice_dict, tk = None):

        def prepend_file(fname, new_line):
            with open(fname) as f: data = f.read()
            with open(fname, 'w') as f: f.write(new_line + '\n' + data)

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
            read.merge_dict(items, splice_dict)
        else:
            move(fname, old_file_new_name)
            with open(fname, 'w') as f:
                f.write('"#base" "%s"\n' % included_file_name)
                f.write('"#base" "%s"\n' % old_file_new_name_nice)

        with open(included_file, 'w') as f:
            f.write(format_dict(0, splice_dict))



def ident(n):
    return "\t" * n


def wrap(string):
    if len(string) == 0:
        return '""'
    elif not string[0] != '"' and string[-1] != '"':
        raise ('bad', string)
    else:
        return '"' + string + '"'


def format_dict(i, dic, skip = True):
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
