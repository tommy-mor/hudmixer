from pathlib import Path
from shutil import copytree, copy, move
import os

import read as r


def translate_string(st, tr):
    for frm, to in tr.items():
        st = st.replace(frm, to)
    return st


def translate_dict(dic, tr):
    keys = list(dic.keys())
    for k in keys:
        newkey = translate_string(k, tr)
        dic[newkey] = dic[k]
        if newkey != k:
            del dic[k]

        val = dic[newkey]
        if type(val) == dict:
            translate_dict(val, tr)
        else:
            dic[newkey] = translate_string(val, tr)


class Feature:
    def __init__(self, hud):
        self.fromhud = hud

        self.font_defs = {}
        self.font_filedefs = []
        self.color_defs = {}
        self.hudlayout_changes = {}
        self.file_copies = {}
        self.raw_copies = {}

    def add_changes(self, dic, new):
        # TODO assert any overlap must be equal
        r.merge_dict(new, dic)

    def collect_file(self, f):
        # copy entire file

        # collect all color definitions
        colors = self.fromhud.collect(f, ["fgColor", "bgColor"])
        print('colors', colors)

        translation_colors = {k: k + "_" + self.fromhud.translation_key for k in colors}

        colordefs = self.fromhud.collect_color_defs(colors)

        translate_dict(colordefs, translation_colors)
        print('colordefs', colordefs)

        # check that colors are colors
        for v in colordefs.values():
            a, b, c, d = v.split(' ')
            int(a), int(b), int(c), int(d)

        fontnames = self.fromhud.collect(f, ["font", "font_minmode"])

        translation_fonts = {k: k + "_" + self.fromhud.translation_key for k in fontnames}

        fontnames = set(list(fontnames))
        fontdefs, fontfiledefs, fontpaths = self.fromhud.collect_font_defs(fontnames)

        translate_dict(fontdefs, translation_fonts)

        fontpath_translate = {}

        for path in fontpaths:
            p = self.fromhud.srcdir / path
            assert p.resolve().is_file()

            topath = Path('mixer/fonts') / p.name
            self.raw_copies[p] = topath
            fontpath_translate[path] = str(topath)

        for fontdef in fontfiledefs:
            translate_dict(fontdef, fontpath_translate)

        fi = r.parse_file(self.fromhud.srcdir / f)

        # TODO maybe make it only translate specific fields...
        translate_dict(fi, translation_fonts)
        translate_dict(fi, translation_colors)

        self.add_changes(self.color_defs, colordefs)
        self.add_changes(self.font_defs, fontdefs)
        self.font_filedefs.extend(fontfiledefs)
        self.add_changes(self.file_copies, {f: fi})

        # TODO rename to avoid collisiog

        # TODO copy font files
        # TODO copy image files

        # get font file index (from basehud and outhud)

    def hudlayout_grab(self, itemname):
        hl = self.fromhud.hudlayout
        assert len(hl) == 1

        for _, hl in hl.items():
            ret = hl[itemname]
        self.hudlayout_changes[itemname] = ret


        # don't splice directly, but return our dicts to outhud for merging



# PROMBLEM: if the imported file does not have a block, it will not override the base one, and it will live on

