import filecmp
import os


def deep_compare(a, b):
    diffs = []

    def rec(dcmp):
        for subdcmp in dcmp.subdirs.values():
            rec(subdcmp)

        diffs.extend(dcmp.diff_files)
        for diff_file in dcmp.diff_files:
            with open(os.path.join(dcmp.left, diff_file)) as f1:
                with open(os.path.join(dcmp.right, diff_file)) as f2:
                    pass
                    #print(''.join(difflib.unified_diff(f1.readlines(), f2.readlines())))
    print("comparing", a, b)
    dcmp = filecmp.dircmp(a, b)
    rec(dcmp)
    print("diff files", diffs)
