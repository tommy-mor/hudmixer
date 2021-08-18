import read as r


a = r.Buf('abcd')
a.eat_white_space()
assert a.st == 'abcd'

a = r.Buf('   abcd')
a.eat_white_space()
assert a.st == 'abcd'


a = r.Buf('   abcd   ')
a.eat_white_space()
assert a.st == 'abcd   '


a = r.Buf('   abcd   ')
b = a.eat_until('d')

with open('../huds/idhud/resource/ui/disguisestatuspanel.res') as f:
    p = r.Parser(f.read())
    print(p.items)
