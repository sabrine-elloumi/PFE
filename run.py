#!/usr/bin/env python
# Script d'execution du projet ETL

import os
import sys

# Ajouter le repertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()