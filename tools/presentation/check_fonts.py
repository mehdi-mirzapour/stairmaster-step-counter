import os
import matplotlib.font_manager as fm

fonts = [f.fname for f in fm.fontManager.ttflist if 'sans' in f.name.lower() or 'dejavu' in f.name.lower()]
print('Available fonts:', fonts[:10])
