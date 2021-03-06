from pathlib import Path
# https://sourcegraph.com/github.com/TheAlePower/TeamFortress2@1b81dded673d49adebf4d0958e52236ecc28a956/-/blob/tf2_src/tier1/KeyValues.cpp?L2388:17

# note, support chained key values? (ChainKeyValue)
# maybe keep track of line numbers so we can sneak new values in better?
WS = " \t\n\r"

from model.util import ResDict


class Buf:
    def __init__(self, st):
        self.st = st

    def is_valid(self):
        while 1:
            if all(c in WS for c in self.st):
                return False

            self.eat_white_space()

            if (not self.eat_cpp_comment()) \
               and (not self.eat_brackets()):
                break

        if len(self.st) == 0:
            return False

        return True

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
        self.eat_one_char()
        return True

    def eat_brackets(self):
        c = self.st[0]
        if c != "[":
            return False

        self.eat_one_char()
        self.eat_until("]")
        assert self.st[0] == "]"
        self.eat_one_char()
        return True

    def eat_until(self, cs):
        # ret does not include the end character
        # but st does
        if self.st == '':
            return ''
        i = 0
        length = len(self.st) - 1 

        while i < length and self.st[i] not in cs:
            i += 1

        cap = self.st[:i]
        self.st = self.st[i:]
        return cap

    def get_deliminited_string(self):
        assert self.st[0] == '"'
        self.st = self.st[1:]

        s = self.eat_until('"')
        assert self.st[0] == '"'
        self.eat_one_char()
        #return '"' + s + '"'
        return s


class Parser:
    def __init__(self, inputstring, path='', parsed=[]):
        self.path = Path(path)  # for base and include
        self.parsed = parsed # for avoiding parsing file twice while following base

        self.items = ResDict()
        self.buf = Buf(inputstring)
        self.visited_filenames = []
        self.parse_file()

    def get_text(self):
        return self.buf.st

    def parse_file(self):

        while self.buf.is_valid():
            token, _ = self.read_token()
            if token == "#include" or token == "#base":
                # include is appended, and base is merged
                # but not sure how those are different so..
                includefile, _ = self.read_token()
                f = (self.path / includefile).resolve()
                if f.is_file() and f not in self.parsed:
                    print('parsing ', f)
                    # {HERE} Fix infinite looping of parsing
                    new_items = parse_file(f.resolve(), parsed=[f, *self.parsed])
                    # TODO make sure that it doesn't override
                    # values, it keeps oldest ones
                    self.items.deep_merge_with(new_items)

            else:
                opn, qtd = self.read_token()


                assert opn == "{", opn
                assert not qtd

                res = ResDict()
                res[token] = self.recursive_parse_file()

                self.items.deep_merge_with(res)


    def recursive_parse_file(self):
        # parse until closing block, returning dict of pairs
        items = ResDict()
        while 1:
            key, qtd = self.read_token()

            if key == "}" and not qtd:
                return items

            if key == "{" and not qtd:
                raise Exception("two { in a row")

            value, qtd = self.read_token()

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

        token = self.buf.eat_until(WS + '}{')
        return token, False
        # TODO handle conditionals []


def parse_file(fname, parsed=[]):
    path = Path(fname).resolve().parent
    with open(fname) as f:
        return Parser(f.read(), path, parsed=parsed).items
