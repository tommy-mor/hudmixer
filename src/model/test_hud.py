from model.hud import ImportHud
import os

for h in os.glob('../../*'):
    ImportHud(h)
