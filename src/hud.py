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


def string_splice(base, inst, index):
    basea, baseb = base[:index], base[index:]
    return basea + inst + baseb


def ident(n):
    return "\n" * n


def wrap(string):
    assert string[0] != '"' and string[-1] != '"'
    return '"' + string + '"'


def format_dict(i, dic):
    if type(dic) == str:
        return wrap(dic)

    st = ident(i) + "{\n"
    for k, v in dic.items():
        assert type(k) == str
        st += ident(i + 1) + k
        st += "\t" + format_dict(i + 1, v)
    st += ident(i) + "}\n"
    return st


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

    def splice(self, fname, splice_dict):
        # NOTE: can only insert one value at a time without breaking

        f = self.srcdir / fname
        assert f.exists() and f.suffix == ".res"

        self.text = ""

        with open(f) as f:
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
                        raise Exception("cant overwrite existing value")
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
        delattr(self, "text")
        self.changedFiles[fname] = s
        return s


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
    # hud that we are going to gather features from.
    # need to extract entire files, and everything referenced in them.

    def __init__(self, fname):
        self.srcdir = Path(fname)
        ensure_is_hud(fname)

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

    def collect_at(self, dic, path, keys):
        search = dic

        for loc in path:
            search = search[loc]

        ret = {}
        for key in keys:
            ret[key] = search[key]

        return ret

    def collect_color_defs(self, colors):

        return self.collect_at(self.clientscheme, ['Scheme', 'Colors'], colors)

    def collect_font_defs(self, fonts):
        fonts = self.collect_at(self.clientscheme, ['Scheme', 'Fonts'], fonts)
        font_names = collect_values_from_keys(fonts, permute(["name"]))
        # TODO there can be fontfiles at BitmapFontFiles, ?others?,
        # not just CustomFontFiles
        font_definitions = self.collect_at(self.clientscheme, ['Scheme', 'CustomFontFiles'], font_names)
        font_paths = collect_values_from_keys(font_definitions, permute(["font"]))
        return fonts, font_definitions, font_paths
