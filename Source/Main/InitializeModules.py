import  sys; sys.dont_write_bytecode = True
import os

from types import SimpleNamespace




def setup_LnUtils(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger

    import LnUtils; LnUtils.setup(gVars=gv)


def setup_LoadYamlFile_Class(*, gVars):
    gv=SimpleNamespace()
    gv.logger=gVars.logger
    gv.envars_dir              = os.path.expandvars("${ln_ENVARS_DIR}")
    gv.mqttmonitor_runtime_dir = os.path.expandvars("${ln_RUNTIME_DIR}/mqtt_monitor")
    gv.brokers_file            = os.path.expandvars("${ln_ENVARS_DIR}/yaml/Mqtt_Brokers.yaml")
    gv.telegram_groups_file    = os.path.expandvars("${ln_ENVARS_DIR}/yaml/telegramGroups.yaml")
    gv.mariadb_file            = os.path.expandvars("${ln_ENVARS_DIR}/yaml/mariadb.yaml")

    import LoadYamlFile_Class; LoadYamlFile_Class.setup(gVars=gv)




def Main(*, gVars):
    setup_LnUtils(gVars=gVars)
    setup_LoadYamlFile_Class(gVars=gVars)
