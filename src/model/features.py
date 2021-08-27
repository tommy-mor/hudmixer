from pathlib import Path

import model.read as r
import model.animation as animation

from model.util import ResDict


def translate_string(st, tr):
    for frm, to in tr.items():
        st = st.replace(frm, to)
    return st


def translate_dict(dic, tr, at):
    # only translate when keys is one of 'at'
    assert type(dic) == ResDict

    new = ResDict()
    for k, v in dic.items():
        newkey = translate_string(k, tr)
        if type(v) == str:
            if k in at:
                new[newkey] = translate_string(v, tr)
            else:
                new[newkey] = v
        else:
            new[newkey] = translate_dict(v, tr, at)
    return new


def is_color(st):
    sp = st.split()
    return len(sp) == 4 and all(c.isnumeric() for c in sp)


def permute(strings):
    r = []
    for s in strings:
        r.append(s)
        r.append(s.lower())
    return list(set(r))

COLOR_STRINGS = permute(["fgColor", "bgColor", "fgColor_Override", "bgColor_Override", "color_outline"])
FONT_STRINGS = permute(["font", "font_minmode"])
COLOR_ANIM_STRINGS = permute(["FgColor", "BgColor", "Text2Color", "Ammo2Color"])

class Feature:
    def __init__(self, hud):
        self.fromhud = hud

        self.font_defs = ResDict()
        self.font_filedefs = []
        self.color_defs = ResDict()
        self.hudlayout_changes = ResDict()
        self.file_copies = ResDict()
        self.raw_copies = {} # fname to path
        self.event_copies = {} # event name to [cmds]

    def add_changes(self, dic, new):
        # TODO assert any overlap must be equal
        if type(new) != ResDict:
            import pdb
            pdb.set_trace()
        dic.deep_merge_with(new)

    def add_colors(self, colors):
        colors = list(set([c for c in colors if not is_color(c)]))

        translation_colors = ResDict({k: k + "_" + self.fromhud.translation_key for k in colors})

        colordefs = self.fromhud.collect_color_defs(colors)

        colordefs = translate_dict(colordefs, translation_colors, COLOR_STRINGS)

        # check that colors are colors
        for v in colordefs.values():
            a, b, c, d = v.split(' ')
            int(a), int(b), int(c), int(d)

        self.add_changes(self.color_defs, colordefs)
        return translation_colors

    def collect_file(self, f):

        # collect all color definitions
        translation_colors = self.add_colors(self.fromhud.collect(f, COLOR_STRINGS))

        fontnames = self.fromhud.collect(f, FONT_STRINGS)

        translation_fonts = ResDict({k: k + "_" + self.fromhud.translation_key for k in fontnames})

        fontnames = set(list(fontnames))

        fontdefs, fontfiledefs, fontpaths = self.fromhud.collect_font_defs(fontnames)

        fontdefs = translate_dict(fontdefs, translation_fonts, FONT_STRINGS)

        fontpath_translate = {}

        for path in fontpaths:
            p = self.fromhud.srcdir / path

            if p.resolve().is_file():
                topath = Path('mixer/fonts') / p.name
                self.raw_copies[p] = topath
                fontpath_translate[path] = str(topath)
            else:
                print('not importing default font', p)

        fontfiledefs = [translate_dict(fontdef, fontpath_translate, FONT_STRINGS) for fontdef in fontfiledefs]

        fi = self.fromhud.parse_file(f)

        # TODO maybe make it only translate specific fields...
        fi = translate_dict(fi, translation_fonts, FONT_STRINGS)
        fi = translate_dict(fi, translation_colors, COLOR_STRINGS)

        self.add_changes(self.font_defs, fontdefs)
        self.font_filedefs.extend(fontfiledefs)
        self.file_copies[f] = fi

        # TODO copy image files

    def hudlayout_grab(self, itemname):
        hl = self.fromhud.hudlayout
        assert len(hl) == 1

        for _, hl in hl.items():
            ret = hl[itemname]
        self.hudlayout_changes[itemname] = ret

    def animation_grab(self, eventname):
        if eventname in self.event_copies:
            return

        # TODO close over events that are referenced by RunEvent and StopEvent
        if eventname in self.fromhud.events:
            event = self.fromhud.events[eventname]

            colors = animation.collect_list(event, COLOR_ANIM_STRINGS)

            translation_colors = self.add_colors(colors)

            event = animation.translate_clist_colors(event, translation_colors, COLOR_ANIM_STRINGS)
            self.event_copies[eventname] = event

            # look for referenced events
            for cmd in event:
                if cmd[0] in ["RunEvent"]:
                    otherevent = cmd[1]
                    self.animation_grab(otherevent)
