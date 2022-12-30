#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 29-12-2022 08.33.31

#===============================================
# progamma che cerca di sfruttare al meglio le caratteristiche di rclone ed rsync
# rclone multitasking, molto più veloce, accesso ai cloud
# rclone capace di copiare i symbolic link
#===============================================

import sys; sys.dont_write_bytecode=True
import os
from pathlib import Path
from types import SimpleNamespace


import Source
from ColoredLogger import setColoredLogger, testLogger
from lnSync_Class import lnSync_Class
from LoadYamlFile_Class import LoadYamlFile_Class
from ParseInput import ParseInput


__ln_version__="lnSync V2022-12-29_083331"


#######################################################
#
#######################################################
if __name__ == '__main__':
    args=ParseInput(version=__ln_version__)
    prj_name='lnSync'
    logger=setColoredLogger(logger_name=prj_name,
                            console_logger_level=args.console_logger_level,
                            file_logger_level=args.file_logger_level,
                            logging_dir=args.logging_dir,  # logging file--> logging_dir + logger_name
                            threads=False,
                            create_logging_dir=True)

    testLogger(logger)

    os.environ['lnSync_RUNTIME_DIR']=os.environ['ln_RUNTIME_DIR'] + '/lnSync'
    os.environ['lnSync_DRY_RUN']='' if args.go else '--dry-run'



    logger.info('------- Starting -----------')

    gVars=SimpleNamespace()
    gVars.logger          = logger
    gVars.runtime_dir     = f'{os.environ["ln_RUNTIME_DIR"]}/lnSync'
    gVars.dry_run         = '' if args.go else '--dry-run'
    gVars.profile_name    = args.profile
    gVars.delete_excluded = args.delete_excluded
    gVars.mirror          = args.mirror
    gVars.prompt          = (not args.no_prompt)
    gVars.fPostcommands   = args.post_commands


    import InitializeModules; InitializeModules.Main(gVars=gVars)

    # read all configuration data
    # myYaml=LoadYamlFile_Class(filename='main_config.yaml', search_paths=['conf'], resolve_include=True, resolve_vars=True)
    myYaml=LoadYamlFile_Class(filename=args.config_file, search_paths=[], resolve_include=True, resolve_vars=True)
    my_config=myYaml.get_dict() # converte anche il dict in benedict

    my_config.to_yaml(filepath='/tmp/prova.yaml', indent=4, sort_keys=False)

    lnSync=lnSync_Class(main_config=my_config, fRCLONE=args.rclone, fRSYNC=args.rsync, logger=logger)

    lnSync.processProfile(gVars=gVars)
    if not args.go:
        print()
        logger.notify('Process run in --dry-run mode. enter: --run to execute!')
        logger.notify('Process run in --dry-run mode. enter: --run to execute!')
        logger.notify('Process run in --dry-run mode. enter: --run to execute!')
        logger.notify('Process run in --dry-run mode. enter: --run to execute!')

    print()