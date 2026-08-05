"""自动将项目packages目录加入sys.path"""
import sys
import os

_packages_dir = os.path.join(os.path.dirname(__file__), "packages")
if _packages_dir not in sys.path:
    sys.path.insert(0, _packages_dir)
