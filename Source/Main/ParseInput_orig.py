#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 12-12-2022 14.45.07

#===============================================
# progamma che cerca di sfruttare al meglio le caratteristiche di rclone ed rsync
# rclone multitasking, molto più veloce, accesso ai cloud
# rclone capace di copiare i symbolic link
#===============================================

import sys; sys.dont_write_bytecode=True
import os
from pathlib import Path
import argparse



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
    parser.add_argument('--no-prompt', required=False, action='store_true', help='use rsync so sync')
    parser.add_argument('--post-commands', required=False, action='store_true', help='execute remote post commands')

    rclone_rsync=parser.add_mutually_exclusive_group(required=True)
    rclone_rsync.add_argument('--rclone', action='store_true', help='use rclone so sync')
    rclone_rsync.add_argument('--rsync', action='store_true', help='use rsync so sync')


    args = parser.parse_args()


    if args.display_args:
        import json
        json_data = json.dumps(vars(args), indent=4, sort_keys=True)
        print('input arguments: {json_data}'.format(**locals()))
        sys.exit(0)

    return  args

