#!/bin/bash

sourcelibDIR="${ln_GIT_REPO_DIR}/Python/LnPyLib"
destlibDIR="Source/LnLib"

function load_mod() {
    modules="
        "$sourcelibDIR/Logger/ColoredLogger.py"     =
        "$sourcelibDIR/Utils/convertionsUtils.py"   =
        "$sourcelibDIR/Utils/fileUtils.py"          =
        "$sourcelibDIR/Utils/keyboard_prompt.py"    =
        "$sourcelibDIR/Dictionary/read_ini_file.py" =
        "$sourcelibDIR/System/subprocessPopen.py"   =
        "$sourcelibDIR/System/subprocessRun.py"     =
    "
    echo $modules
}


