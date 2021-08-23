from hud import ImportHud, BaseHud
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
        assert hud.__class__ == ImportHud
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


class Health(Feature):
    def __init__(self, hud):
        super().__init__(hud)

    def gather(self):
        self.collect_file("resource/ui/hudammoweapons.res")
        self.hudlayout_grab('HudWeaponAmmo')
        # don't splice directly, but return our dicts to outhud for merging


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
        customfonts = r.parse_file(self.outdir / 'resource/clientscheme.res')['Scheme']['CustomFontFiles']
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

        topkey, _ = r.parse_file(self.outdir / 'scripts/hudlayout.res').popitem()

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
            items = r.parse_file(included_file)
            r.merge_dict(items, splice_dict)
        else:
            move(fname, old_file_new_name)
            with open(fname, 'w') as f:
                f.write('"#base" "%s"\n' % included_file_name)
                f.write('"#base" "%s"\n' % old_file_new_name_nice)

        with open(included_file, 'w') as f:
            f.write(format_dict(0, splice_dict))


        


    def splice_old(self, fname, splice_dict):

        fname = self.outdir / fname
        assert fname.exists() and fname.suffix == ".res"

        self.text = ""

        with open(fname) as f:
            self.text = f.read()

        assert self.text != ""

        def splice_rec(i, splice_dict, addr):
            # i is where to start.

            for key, value in splice_dict.items():
                path.append(key)
                # todo if it doesnt find it
                ki = find_ignoring(self.text[i:], key)

                if ki is not None:
                    i += ki

                    assert self.text[i:].startswith(key)

                    i += len(key)

                    if type(value) == str:
                        raise Exception("cant overwrite existing value %s for key %s" % (value, key))
                    elif type(value) == dict:
                        # must absorb until openbracket
                        a = find_ignoring(self.text[i:], "{") + 1
                        splice_rec(a + i, value, path)
                    else:
                        raise Exception("malformed splice dict")
                else:
                    print("inserting value", value)
                    # key not found, insert it
                    end_bracket_loc = count_until_matches_bracket(self.text, i)
                    self.text = string_splice(
                        self.text, key + "\t" + format_dict(0, value), end_bracket_loc - 1
                    )
                break  # only do one

        def delete_rec(dic, path):
            if len(path) == 1:
                # end of path
                key = path.pop()
                del dic[key]

            elif len(path) > 1:
                key = path.pop()
                delete_rec(dic[key], path)

                # get rid of empty
                if len(dic[key]) == 0:
                    del dic[key]

            else:
                assert not 'impossible'

        while len(splice_dict) > 0:
            # keep splicing until splice dict is empty
            # keep track of current angle
            path = []
            splice_rec(0, splice_dict, path)

            # delete path in splice_dict
            path.reverse()
            delete_rec(splice_dict, path)

        s = self.text
        with open(fname, 'w') as f:
            f.write(self.text)

        delattr(self, "text")
        return s


def find_ignoring(text, search):
    if type(search) != list:
        search = [search]

    def count_until_nl(i):
        while text[i] != "\n":
            i += 1
        return i

    i = 0
    end = len(text)

    while 1:
        if end <= i:
            return None

        for s in search:
            if text[i:].startswith(s):
                return i

        if text[i:].startswith("//"):
            i = count_until_nl(i)
        elif text[i:].startswith("{"):
            i = count_until_matches_bracket(text, i + 1)
            assert text[i] == "}"
            i += 1
        elif text[i:].startswith("}"):
            # not found
            return None
        elif text[i:].startswith("#base") or text[i:].startswith("#include"):
            i = count_until_nl(i)
        else:
            i += 1


def count_until_matches_bracket(text, i):
    # assert text[i-1] == "{"

    depth = 1
    i += 1

    while 1:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth += -1

        if depth == 0:
            return i

        if depth < 0:
            # TODO NO! this lets us exit early with no find.
            raise Exception("too many closing brackets")

        i += 1


def string_splice(base, inst, index):
    basea, baseb = base[:index], base[index:]
    return basea + inst + baseb


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

# PROMBLEM: if the imported file does not have a block, it will not override the base one, and it will live on

