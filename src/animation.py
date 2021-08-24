from read import Parser

COMMAND_ARITIES = {'Animate': 6,
                   'RunEvent': 2,
                   'StopEvent': 2,
                   'StopAnimation': 3,
                   'StopPanelAnimations': 2,
                   'SetFont': 4,
                   'SetTexture': 4,
                   'SetString': 4,
                   'SetVisible': 3
                   }

class ManifestParser(Parser):

    def parse_file(self):
        start, _ = self.read_token()
        assert start == 'hudanimations_manifest'

        opn, _ = self.read_token()
        assert opn == "{"

        self.animation_files = []

        while self.buf.is_valid():
            tok, _ = self.read_token()
            if tok == "}":
                break
            else:
                assert tok == "file"
                filename, _ = self.read_token()
                self.animation_files.append(filename)


class AnimationParser(Parser):

    def parse_file(self):
        while self.buf.is_valid():
            self.parse_event()

    def read_n_tokens(self, n):
        r = []
        for _ in range(n):
            tk, _ = self.read_token()
            r.append(tk)
        return r

    def parse_event(self):
        tok, _ = self.read_token()
        assert tok == "event"

        name, _ = self.read_token()
        prn, q = self.read_token()

        assert not q
        assert prn == "{"

        commands = []

        while self.buf.is_valid():
            cmd, q = self.read_token()
            if cmd == "}":
                break

            if cmd == "Animate":
                starttokens = self.read_n_tokens(3)
                interpolator = self.read_n_tokens(1)[0]
                if interpolator.lower() in ['pulse', 'flicker', 'gain', 'bias']:
                    resttokens = self.read_n_tokens(3)
                else:
                    assert interpolator.lower() in ['linear', 'accel', 'deaccel', 'spline']
                    resttokens = self.read_n_tokens(2)

                commands.append([cmd, *starttokens, interpolator, *resttokens])
            else:
                
                assert cmd in COMMAND_ARITIES, cmd
                commands.append([cmd, *self.read_n_tokens(COMMAND_ARITIES[cmd])])
        self.items[name] = commands


def collect_list(li: "[Commands]", keys):
    ret = []
    for cmd in li:
        if cmd[0] == "Animate":
            if cmd[2] in keys:
                ret.append(cmd[3])
    return ret


# TODO move this into utils file
def translate_string(st, tr):
    for frm, to in tr.items():
        st = st.replace(frm, to)
    return st


def translate_clist_colors(li: "[Commands]", tr, at):
    def translate_cmd(cmd):
        if cmd[0] == "Animate":
            if cmd[2] in at:
                ret = [*cmd]
                ret[3] = translate_string(ret[3], tr)
                return ret

        return cmd

    return [translate_cmd(x) for x in li]
# TODO change everywhere so that it uses keys.lower() instead of permute
# TODO see if setfont does anything


def format_events(events):
    def wrap_if_spaces(st):
        if ' ' in st:
            return '"' + st + '"'
        else:
            return st

    st = '// exported by mixer\n'
    for title, cmdlist in events.items():
        st += 'event %s\n{\n' % title
        for cmd in cmdlist:
            st += '\t' + '\t'.join(wrap_if_spaces(param) for param in cmd)
            st += '\n'
        st += '}\n'
    return st


def format_manifest(files):
    st = 'hudanimations_manifest\n{'
    for fname in files:
        st += '\t "file"\t"%s"\n' % fname
    st += '}\n'
    return st
