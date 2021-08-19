import os
import read
from pathlib import Path
from shutil import copytree


def ensure_is_hud(fname):
    path = Path(fname)

    clientscheme = path / 'resource' / 'clientscheme.res'
    assert clientscheme.exists() and not clientscheme.is_dir()

    hudlayout = path / 'scripts' / 'hudlayout.res'
    assert hudlayout.exists() and not hudlayout.is_dir()

def count_until_matches_bracket(text, i):
    #assert text[i-1] == "{"

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
            raise Exception('too many closing brackets')


        i += 1


def find_ignoring(text, search):
    if type(search) != list:
        search = [search]

    def count_until_nl(i):
        while text[i] != '\n':
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

        if text[i:].startswith('//'):
            i = count_until_nl(i)
        elif text[i:].startswith('{'):
            i = count_until_matches_bracket(text, i + 1)
            assert text[i] == "}"

        elif text[i:].startswith("#base") or text[i:].startswith("#include"):
            i = count_until_nl(i)
        else:
            i += 1


def string_splice(base, inst, index):
    basea, baseb = base[:index], base[index:]
    return basea + inst + baseb

class BaseHud:
    # hud that we are importing properties into.
    # will have to be able to export into final hud, splicing in important info

    def __init__(self, fname):
        self.srcdir = Path(fname)
        ensure_is_hud(fname)

    def splice(self, fname, splice_dict):
        # TODO should only copy from copied hud, then update file in place
        f = self.srcdir / fname
        assert f.exists() and f.suffix == '.res'

        self.text = ''

        with open(f) as f:
            self.text = f.read()

        assert self.text != ''

        def splice_rec(i, splice_dict):
            # i is where to start.

            for key, value in splice_dict.items():
                # todo if it doesnt find it
                ki = find_ignoring(self.text[i:], key)

                if ki is not None:
                    i = ki + i

                    assert self.text[i:].startswith(key)

                    i += len(key)

                    if type(value) == str:
                        raise Exception('cant overwrite existing value')
                    elif type(value) == dict:
                        # must absorb until openbracket
                        a = find_ignoring(self.text[i:], '{') + 1
                        splice_rec(a + i, value)
                    else:
                        raise Exception('malformed splice dict')
                else:
                    print('inserting value', value)
                    # key not found, insert it
                    end_bracket_loc = count_until_matches_bracket(self.text, i)
                    self.text = string_splice(self.text, key + "\t" + value,
                                              end_bracket_loc - 1)

        splice_rec(0, splice_dict)

        s = self.text
        delattr(self, 'text')
        return s


    def export(self, outdir):
        outdir_ = copytree(self.srcdir, outdir)
        assert outdir == outdir_
        return outdir


class ImportHud:
    # hud that we are going to gather features from.
    # need to extract entire files, and everything referenced in them.

    def __init__(self, fname):
        self.srcdir = fname
        ensure_is_hud(fname)
