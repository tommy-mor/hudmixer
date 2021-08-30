from collections import UserDict
# dict class that has case insesitive lookups
class ResDict(UserDict):

    def __init__(self, dict={}):
        super().__init__(self)
        self.keymap = {}

        for key, value in dict.items():
            if type(value) == str:
                self[key] = value
            else:
                self[key] = ResDict(dict=value)

    def __setitem__(self, key, value):
        assert type(value) == str or type(value) == ResDict

        newkey = key.lower()

        if newkey in self.keymap:
            key = self.keymap[newkey]
        else:
            self.keymap[newkey] = key

        super().__setitem__(key, value)

    def __getitem__(self, key):
        newkey = key.lower()

        if newkey in self.keymap:
            return super().__getitem__(self.keymap[newkey])
            
        return super().__getitem__(key)

    def __contains__(self, key):
        return key.lower() in self.keymap


    def deep_merge_with(self, new):
        assert new.__class__ == ResDict

        for key, value in new.items():
            if isinstance(value, ResDict):
                node = self.setdefault(key, ResDict())
                node.deep_merge_with(value)
            else:
                if key in self:
                    # don't overwrite strings
                    pass
                else:
                    self[key] = value


a = ResDict()
b = 'blingus' in a
a['Test'] = 'arst'
assert a['test'] == 'arst'
assert 'Test' in a.keys()

import sys
from pathlib import Path

# adapted from
# https://github.com/7x11x13/songs-to-youtube/blob/226026c86b8564db91e1a326a56eabb847c158b5/src/utils.py#L80
def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # it is parent dir because tests are run from inside src 
        base_path = '..'
    return Path(base_path) / relative_path