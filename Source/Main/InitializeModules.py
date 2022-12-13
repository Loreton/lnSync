# import  sys; sys.dont_write_bytecode = True
# import os

from types import SimpleNamespace


def setup_LoretoDict(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger

    from LoretoDict import setup; setup(gVars=gv)

def setup_Benedict(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger

    import benedictMonkey; benedictMonkey.setup(gVars=gv)



def setup_envarsYamlLoader(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    # gv.envars_dir=gVars.envars_dir
    # gv.mqttmonitor_runtime_dir = gVars.mqttmonitor_runtime_dir

    from envarsYamlLoader import setup; setup(gVars=gv)


def Main(*, gVars):
    setup_LoretoDict(gVars=gVars)
    setup_Benedict(gVars=gVars)
