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

try:
    a = r.Parser("""//
//
// TRACKER SCHEME RESOURCE FILE
//
// sections:
//		colors			- all the colors used by the scheme
//		basesettings	- contains settings for app to use to draw controls
//		fonts			- list of all the fonts used by app
//		borders			- description of all the borders
//
//
Scheme {}""")
except:
    import pdb
    pdb.post_mortem()
print(a.items)
