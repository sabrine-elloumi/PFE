#!/usr/bin/env python

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    # Afficher la version de pandas pour debug
    print(f"Pandas version: {pd.__version__}")
    print()
    main()