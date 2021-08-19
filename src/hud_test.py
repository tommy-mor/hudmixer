import hud
import filecmp
import shutil


def deep_compare(a, b):
    diffs = []

    def rec(dcmp):
        diffs.extend(dcmp.diff_files)
        for subdcmp in dcmp.subdirs.values():
            rec(subdcmp)

    print("comparing", a, b)
    dcmp = filecmp.dircmp(a, b)
    rec(dcmp)
    print("diff files", diffs)


class hud_test:
    def __init__(self, fname):
        self.fname = fname

    def __enter__(self):
        self.hud = hud.BaseHud(self.fname)
        return self.hud

    def __exit__(self, type, value, traceback):
        outname = "../huds/outhud"
        shutil.rmtree(outname)
        self.hud.export(outname)

        deep_compare(self.hud.srcdir, outname)


with hud_test("../huds/idhud") as h:
    new = h.splice(
        "resource/clientscheme_small.res",
        {"Scheme": {"Colors": {'"TommyColor"': '"0 0 0 0"'}}},
    )
    print(new)


st = "blah blah blah Source"
a = hud.find_ignoring(st, "Source")
assert st[a:].startswith("Source")

st = "blah blah blah Source Source"
a = hud.find_ignoring(st, "Source")
assert st[a:] == "Source Source"

st = """
#include blah Source blah

Source {}
"""
a = hud.find_ignoring(st, "Source")
assert st[a:] == "Source {}\n"

assert hud.string_splice("abcd", "HAH", 2) == "abHAHcd"

st = """
#base "../arsotieanrstoiaernst"

Source {}
"""
a = hud.find_ignoring(st, "Source")
assert st[a:] == "Source {}\n"

# TODO test inserting multiple kv pairs, or assert just supporting only one
# TODO make it actually modify file, then start working on feature extraction
# code.
