import sys; import types; import importlib.util; import importlib.machinery; sys.modules['imp'] = types.ModuleType('imp'); from heroprotocol.versions import latest
