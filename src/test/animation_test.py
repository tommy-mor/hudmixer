from animation import AnimationParser

with open('../huds/rayshud/scripts/hudanimations_custom.txt') as f:
    p = AnimationParser(f.read())

print(p.items)
