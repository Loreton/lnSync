import  sys; sys.dont_write_bytecode = True
import os
import logging; logger=logging.getLogger(__name__)


from pathlib import Path
import argparse


# -----------------------------
def check_dir(path):
    p = Path(path).resolve()
    if p.is_dir():
        return str(p)
    else:
        p.mkdir(parents=True, exist_ok=True)
        return str(p)


def check_file(path):
    p = Path(path)
    if p.is_file():
        return str(p.resolve())
    else:
        print(f'    ParseInput ERROR: file: {p} NOT found.')
        sys.exit(1)
# -----------------------------


##############################################################
# - Parse Input
##############################################################
def ParseInput(version):

    # =============================================
    # = Common Options
    # =============================================

    # --------------------------------------------------
    # -- add common options to all subparsers
    # --------------------------------------------------
    def subparser_common_options(subparsers):
        for name, subp in subparsers.choices.items():
            ### --- mi serve per avere la entry negli args e creare poi la entry "product"
            subp.add_argument('--{0}'.format(name), action='store_true', default=True)
            single_parser_common_options(subp)
    # --------------------------------------------------

    # --------------------------------------------------
    # -- add common options to single subparsers or parser
    # --------------------------------------------------
    def single_parser_common_options(_parser):
        logger_levels=['trace', 'debug', 'notify', 'info', 'function', 'warning', 'error', 'critical']

        # _parser.add_argument('--go', help='specify if command must be executed. (dry-run is default)', action='store_true')
        _parser.add_argument('--display-args', action='store_true', help='''Display arguments\n\n''' )
        _parser.add_argument('--systemd', action='store_true', help='''It's a systemd process\n\n''' )
        _parser.add_argument('--pid-file', type=str, required=False, default='/tmp/mqttmonitor/mqttmonitor.pid', help='''pid file\n\n''' )

        _parser.add_argument('--go', help='specify if command must be executed. (--dry-run is default)', action='store_true')
        _parser.add_argument('--verbose', help='Display all messages', action='store_true')

        _parser.add_argument( "--console-logger-level",
                                metavar='<optional>',
                                type=str.lower,
                                required=False,
                                default='critical',
                                choices=logger_levels,
                                nargs="?", # just one entry
                                help=f"""set console logger level:
                                        {logger_levels}
                                        \n\n""".replace('  ', '')
                            )


        _parser.add_argument( "--file-logger-level",   ##  MI DA ERRORE
                                metavar='<file_logger>',
                                type=str.lower,
                                required=False,
                                default='warning',
                                choices=logger_levels,
                                nargs="?", # just one entry
                                help=f"""set file logger level:
                                        {logger_levels}
                                        \n\n""".replace('  ', '')
                            )



        _parser.add_argument( "--logging-dir",
                                metavar='<logger_dir>',
                                type=check_dir,
                                required=True,
                                default=None,
                                help=f"""full path of logger directory. It will be created dinamically. \n\n""".replace('  ', '')
                            )






    # =============================================
    # = Main
    # =============================================

    if len(sys.argv) == 1:
        sys.argv.append('-h')

    parser=argparse.ArgumentParser(description=f'{version}', formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--profile', help='specify profile to be processed', required=True, default=None)

    parser.add_argument('--delete-excluded', help='deteles excluded files', action='store_true')
    parser.add_argument('--mirror', help='deletes any files that exist in your target directories but that do not exist in the source directory', action='store_true')
    parser.add_argument('--runtime-dir', required=False, type=check_dir, default=None, help='etc directory')
    parser.add_argument('--no-prompt', required=False, action='store_true', help='use rsync so sync')
    parser.add_argument('--post-commands', required=False, action='store_true', help='execute remote post commands')

    rclone_rsync=parser.add_mutually_exclusive_group(required=True)
    rclone_rsync.add_argument('--rclone', action='store_true', help='use rclone so sync')
    rclone_rsync.add_argument('--rsync', action='store_true', help='use rsync so sync')


    single_parser_common_options(parser)

    args = parser.parse_args()

    if args.display_args:
        import json
        json_data = json.dumps(vars(args), indent=4, sort_keys=True)
        print('input arguments: {json_data}'.format(**locals()))
        sys.exit(0)


    return  args

