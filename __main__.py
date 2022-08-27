#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 27-08-2022 12.17.09

#===============================================
# progamma che cerca di sfruttare al meglio le caratteristiche di rclone ed rsync
# rclone multitasking, molto più veloce, accesso ai cloud
# rclone capace di copiare i symbolic link
#===============================================

import sys; sys.dont_write_bytecode=True
import os
from pathlib import Path



import Source
from   ColoredLogger import setColors, testLogger
# import lnSync
# import lnSync_v2
# import lnSync_v3_using_Class
from lnSync_Class import lnSync_Class
from LnDict import LoretoDict





##############################################################
# - Parse Input
##############################################################
def ParseInput():
    # -----------------------------
    def check_dir(path):
        p = Path(path).resolve()
        if p.is_dir():
            return str(p)
        else:
            p.mkdir(parents=True, exist_ok=True)
            return str(p)


    import argparse
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    parser = argparse.ArgumentParser(description='rclone + rsync')

    parser.add_argument('--profile', help='specify profile to be processed', required=True, default=None)
    parser.add_argument('--go', help='specify if command must be executed. (dry-run is default)', action='store_true')
    parser.add_argument('--verbose', help='Display all messages', action='store_true')


        # logging and debug options
    parser.add_argument('--display-args', help='Display input paramenters', action='store_true')
    parser.add_argument('--logger-console-level', required=False,
            choices=['critical', 'info', 'function', 'warning', 'error', 'debug', 'trace'], default='info',
            help='console logger level - default: error')

    parser.add_argument('--delete-excluded', help='detele excluded files', action='store_true')
    parser.add_argument('--runtime-dir', required=False, type=check_dir, default=None, help='etc directory')
    parser.add_argument('--rclone', required=False, action='store_true', help='use rclone so sync')
    parser.add_argument('--rsync', required=False, action='store_true', help='use rsync so sync')
    parser.add_argument('--no-prompt', required=False, action='store_true', help='use rsync so sync')


    args = parser.parse_args()


    if args.display_args:
        import json
        json_data = json.dumps(vars(args), indent=4, sort_keys=True)
        print('input arguments: {json_data}'.format(**locals()))
        sys.exit(0)

    return  args




#######################################################
#
#######################################################
if __name__ == '__main__':
    # ---- parsing input
    args=ParseInput()


    # ---- Loggging
    logger_level=args.logger_console_level.upper()
    logger=setColors(logger_level, logger_name='lnSync', test=False)
    args.logger=logger

    os.environ['lnSync_RUNTIME_DIR']=os.environ['ln_RUNTIME_DIR'] + '/lnSync'
    os.environ['lnSync_DRY_RUN']='' if args.go else '--dry-run'


    logger.info('------- Starting -----------')

    LoretoDict.setLogger(mylogger=logger)

    # read all configuration data
    lnSync=lnSync_Class(main_config_filename='conf/main_config.yaml', logger=logger)

    # rprocess profile
    dry_run='' if args.go else '--dry-run'

    lnSync.processProfile(profile_name=args.profile, delete_excluded=args.delete_excluded, dry_run=dry_run, prompt=(not args.no_prompt), fRCLONE=args.rclone, fRSYNC=args.rsync)


