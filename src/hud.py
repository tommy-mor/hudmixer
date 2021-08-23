import os
import read
from pathlib import Path
from shutil import copytree


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

    def file_items(self, fname):
        return read.parse_file(self.srcdir / fname)


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
