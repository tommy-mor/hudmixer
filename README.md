# hudmixer
mix tf2 huds together

## installation

On windows, download and extract ``hudmixer-windows-latest.zip`` from the releases tab to the right.

On linux, clone directory and run ``python3 -m pip install -r requirements.txt`` then ``python3 src/run.py``

If you want a collection of huds to start with, also download ``hud-collection.zip`` and extract that.

## usage

  1. double click ``run.exe`` from the downloaded/extracted folder
  2. click the row that says "Base/Foundation" and choose a hud directory. Any of the huds from hud-collection will work well.
  3. for each feature you want replaced in basehud, click that row and select a directory to source it from
  4. click export, and choose a directory. the output hud will be created under that directory as ``MIXER_EXPORTED_HUD``.
  5. drag this folder into ``tf/custom`` as you would any other hud.
