# https://sourcegraph.com/github.com/TheAlePower/TeamFortress2@1b81dded673d49adebf4d0958e52236ecc28a956/-/blob/tf2_src/tier1/KeyValues.cpp?L2388:17

# note, support chained key values? (ChainKeyValue)
# maybe keep track of line numbers so we can sneak new values in better?
WS = " \t\n\r"


class Buf:
    def __init__(self, st):
        self.st = st

    def is_valid(self):
        return any(c not in WS for c in self.st)

    def peek(self):
        return self.st[0]

    def eat_one_char(self):
        self.st = self.st[1:]

    def eat_white_space(self):
        i = 0
        while self.st[i] in WS:
            i += 1

        self.st = self.st[i:]

    def eat_cpp_comment(self):
        if len(self.st) < 2:
            return False

        c1, c2 = self.st[0], self.st[1]
        if c1 != "/" or c2 != "/":
            return False

        self.eat_until("\n")
        return True

    def eat_brackets(self):
        c = self.st[0]
        if c != "[":
            return False

        self.eat_one_char()
        self.eat_until("]")
        assert self.st[0] != "]"
        return True

    def eat_until(self, cs):
        # does not include the end character
        i = 0
        while self.st[i] not in cs:
            i += 1

        cap = self.st[:i]
        self.st = self.st[i + 1 :]
        return cap

    def get_deliminited_string(self):
        assert self.st[0] == '"'
        self.st = self.st[1:]

        s = self.eat_until('"')

        return '"' + s + '"'


class Parser:
    def __init__(self, inputstring):
        self.items = {}
        self.buf = Buf(inputstring)
        self.parse_file()

    def get_text(self):
        return self.buf.st

    def parse_file(self):
        while self.buf.is_valid():
            token, _ = self.read_token()
            if token == "#include":
                includefile, _ = self.read_token()
                # TODO parse includes now, or do it later
                # self.includes.append(includefile)
                continue

            elif token == "#base":
                basefile, _ = self.read_token()
                # self.includes.append(basefile)
                continue
                # TODO do base files
            # TODO check for conditionals
            opn, qtd = self.read_token()

            assert opn == "{"
            assert not qtd

            self.items[token] = self.recursive_parse_file()

    def recursive_parse_file(self):
        # parse until closing block, returning dict of pairs
        items = {}
        while 1:
            key, qtd = self.read_token()

            if key == "}" and not qtd:
                return items

            if key == "{" and not qtd:
                raise Exception("two { in a row")

            if key == "GameUIButtonsSmall":
                import pdb

                pdb.set_trace()

            value, qtd = self.read_token()

            print("kv", key, value)
            if value == "{" and not qtd:
                items[key] = self.recursive_parse_file()
            else:
                items[key] = value

    def read_token(self):
        # eat whitespace/comments
        while 1:
            self.buf.eat_white_space()

            if (not self.buf.eat_cpp_comment()) \
               and (not self.buf.eat_brackets()):
                break

        c = self.buf.peek()
        if c == '"':
            token = self.buf.get_deliminited_string()
            return token, True
        elif c == "{" or c == "}":
            self.buf.eat_one_char()
            return c, False

        token = self.buf.eat_until(WS)
        return token, False
        # TODO handle conditionals []
