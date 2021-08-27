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
