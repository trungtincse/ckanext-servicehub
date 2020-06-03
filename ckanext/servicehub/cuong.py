from __future__ import print_function

import json

cprint = print
ccprint = lambda x: cprint(json.dumps(x, indent=4, ensure_ascii=False))
