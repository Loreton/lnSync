#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 26-08-2022 17.58.36

import sys; sys.dont_write_bytecode=True
import os
from benedict import benedict
from subprocessRun import run_sh
from subprocessPopen import runCommand
from keyboard_prompt import keyb_prompt
from read_ini_file import readIniFile
from fileUtils import writeTextFile
from ColoredLogger import getColors; C=getColors()



########################################################
#
########################################################
class rSync_Class():
    ''' rclone_conf sample node
    [lnpi22]
        host = 192.168.1.22
        user = pi
        port = 22
        type = sftp
        key_file = ~/.ssh/tunnel_ed25519
        md5sum_command = md5sum
        sha1sum_command = sha1sum
    '''

    def __init__(self, *, config: dict, logger):
        self.logger=logger


        # ---- read rclone_conf to acces destination nodes
        self.rclone_conf   = readIniFile(filename=config['rclone_config_file'])
        self.rclone_node   = None
        self.rsync_bin     = config['bin']
        self.rsync_options = config['options']
        self.exclude_files = config['exclude_files']
        self.temp_dir       =config['tmp_dir']
        if not os.path.exists(self.temp_dir):
                os.mkdir(self.temp_dir)


    def setOptions(self, options: list=[]):
        if not self.rsync_options:
            self.rsync_options=[]
        self.rsync_options.extend(options)
        return ' '.join(self.rsync_options)



    def resolveRemoteDir(self, node_name: str, path: str, check_it: bool=False, exit_on_not_found=False):
        if path is None: path=''
        node=self.rclone_conf.get(node_name, {})
        node_type=node.get('type')

        check_cmd=None

        if node_name=='local': #---- rclone --config ./rclone.conf -L lsd /home/loreto
            remote_path=path
            check_cmd=f"ls -l {remote_path}"

        elif node_type=='sftp': #---- rclone --config=./rclone.conf -L lsd lnpi31:/mnt/Toshiba_1TB_LnDisk/Filu
            ssh_key=node.get('key_file')
            ssh_port=node.get('port')
            ssh_host=node.get('host')
            ssh_user=node.get('user')
            remote_path=f"{ssh_user}@{ssh_host}:{path}"
            check_cmd=f"ssh -i {ssh_key} -p {ssh_port} {ssh_user}@{ssh_host} ls -l {path}"

        else:
            self.logger.error('node: %s: [%s] is not supported by rSync!', node_name, node_type )
            remote_path=None


        # check if remote_path exists
        if check_cmd and check_it:
            self.logger.info("[CMD] - %s", check_cmd)
            run_sh(cmd=check_cmd, logger=self.logger, exit_on_error=True)

        return remote_path


    def checkLocalDir(self, path, exit_on_not_found=False):
        if os.path.exists(path):
            return path

        elif exit_on_not_found:
            self.logger.critical("Local directory: %s doesn't esists", path)
            sys.exit(1)

        else:
            return None


    def setExcludeFiles(self, excl: list=[]):
        if not self.exclude_files:
            self.exclude_files=[]
        self.exclude_files.extend(excl)
        self.exclude_files = list(dict.fromkeys(self.exclude_files))

        temp_fname=f'{self.temp_dir}/exclude_files.txt'
        writeTextFile(data=self.exclude_files, file_out=temp_fname, replace=True, logger=self.logger)
        return temp_fname


    #==============================================================
    #- check local directory
    #- get and check remote dir
    #- create eclude_file
    #- build rclone command
    #  sample profile:
    #        base_local_root_dir: /home/loreto/.ln
    #        base_remote_root_dir: /media/loreto/LnDataDisk/Filu/LnDisk/.ln
    #        remote_nodes:
    #           - local
    #        options:
    #           - --skip-links
    #           - --one-file-system
    #        folders:
    #           - config
    #           - envars
    #           - init
    #           - LnDoc
    #           - scripts
    #           - systemd
    #        exclude_files:
    #           - ''
    #
    #==============================================================
    # def processFolder(self, node_name: str, folder: str, profile: dict, delete_excluded: bool=False, prompt: bool=True, dry_run='--dry-run'):
    def processFolder(self, **kwargs):
        node_name       = kwargs["node_name"]
        # rclone_node     = kwargs["node"]
        folder          = kwargs["folder"]
        profile         = kwargs["profile"]
        delete_excluded = kwargs["delete_excluded"]
        dry_run         = kwargs["dry_run"]
        prompt          = kwargs["prompt"]
        check_remote_dir= kwargs["check_remote_dir"]

        # ---- check local directory
        root_local_path=profile.get("base_local_root_dir")
        root_remote_path=profile.get("base_remote_root_dir", '')

        stdout_file=f'{self.temp_dir}/rsync_stdout.log'
        stderr_file=f'{self.temp_dir}/rsync_stderr.log'

        # add project exclude file to exclude base list
        exclude_filename=self.setExcludeFiles(profile.get("exclude_files", []))

        # add project options to common options list
        options=self.setOptions(options=profile.get("options", []))

        # ---- check local path directory
        local_path=self.checkLocalDir(path=f'{root_local_path}/{folder}/', exit_on_not_found=True)

        # ---- check remote path directory
        remote_path=self.resolveRemoteDir(node_name=node_name, path=root_remote_path, check_it=check_remote_dir, exit_on_not_found=True)
        dest=f"{remote_path}/{folder}/"

        if remote_path:
            # ---- prepare command
            rsyncCMD=f"""{self.rsync_bin} \
                            {dry_run} \
                            --exclude-from {exclude_filename} \
                            --delete-excluded={delete_excluded} \
                            {options} \
                            {local_path} \
                            {dest}"""
                            # {remote_path}/{folder}/"""

            colored_command=f"""{self.rsync_bin} \
                            {C.redH}{dry_run}{C.colorReset} \
                            --exclude-from {exclude_filename} \
                            --delete-excluded={delete_excluded} \
                            {options} \
                            {C.greenH}{local_path} \
                            {C.yellowH}{dest}{C.colorReset}"""
                            # {remote_path}/{folder}/"""


            # - remove extra blanks from command

            rsyncCMD=" ".join(rsyncCMD.split())
            colored_command=" ".join(colored_command.split())
            # colored_command=rsyncCMD
            # colored_command=colored_command.replace(folder, C.yellowH+local_path+C.colorReset)
            # print(dest)
            # colored_command=colored_command.replace(dest, C.yellowH+dest+C.colorReset)
            # colored_command=colored_command.replace(dry_run, C.redH+dry_run+C.colorReset)
            self.logger.notify(colored_command)
            # self.logger.notify(rsyncCMD)


            if prompt:
                keyb_prompt(msg='', validKeys='ENTER', exitKeys='x|q', displayValidKeys=False)

            # rcode, stdout, stderr=run_sh(f'cat {stdout_file} >>{stdout_total}')
            # rcode, stdout, stderr=run_sh(f'cat {stderr_file} >>{stderr_total}')

            rcode, stdout, stderr=runCommand(rsyncCMD, logger=self.logger, console=True, stdout_file=stdout_file, stderr_file=stderr_file)
            self.logger.notify("%s --> %s: [rcode:%s]", local_path, remote_path, rcode)





    #==============================================================
    #- check local directory
    #- get and check remote dir
    #- create eclude_file
    #- build rclone command
    #  sample profile:
    #        base_local_root_dir: /home/loreto/.ln
    #        base_remote_root_dir: /media/loreto/LnDataDisk/Filu/LnDisk/.ln
    #        remote_nodes:
    #           - local
    #        options:
    #           - --skip-links
    #           - --one-file-system
    #        folders:
    #           - config
    #           - envars
    #           - init
    #           - LnDoc
    #           - scripts
    #           - systemd
    #        exclude_files:
    #           - ''
    #
    #==============================================================
    def processProfile(self, profile: dict, delete_excluded: bool=False, dry_run='--dry-run'):

        # ---- check local directory
        root_local_path=profile.get("base_local_root_dir")
        root_remote_path=profile.get("base_remote_root_dir", '')

        stdout_file=f'{self.temp_dir}/rsync_stdout.log'
        stderr_file=f'{self.temp_dir}/rsync_stderr.log'
        # stdout_total=f'{self.temp_dir}/rsync_stdout_total.log'
        # stderr_total=f'{self.temp_dir}/rsync_stderr_total.log'

        # ---- check remote path directory
        for node_name in profile['remote_nodes']:
            remote_path=self.resolveRemoteDir(node_name=node_name, path=root_remote_path, exit_on_not_found=True)
            if remote_path:
                # self.checkRemoteDir(path=remote_path, exit_on_not_found=True)

                # add project exclude file to list
                exclude_filename=self.setExcludeFiles(profile.get("exclude_files", []))

                # add project options to list
                options=self.setOptions(options=profile.get("options", []))

                for folder in profile['folders']:
                    local_path=self.checkLocalDir(path=f'{root_local_path}/{folder}', exit_on_not_found=True)
                    remote_path=f'{root_remote_path}/{folder}' # controlliamo solo il root_remote_path

                    # ---- prepare command
                    rsyncCMD=f"""{self.rsync_bin} \
                                    {dry_run} \
                                    --exclude-from {exclude_filename} \
                                    --delete-excluded={delete_excluded} \
                                    {options} \
                                    {local_path}\
                                    {remote_path}"""


                    # - remove extra blanks from command
                    rsyncCMD=" ".join(rsyncCMD.split())
                    self.logger.notify(rsyncCMD)

                    prompt(msg='', validKeys='ENTER', exitKeys='x|q', displayValidKeys=False)

                    # rcode, stdout, stderr=run_sh(f'cat {stdout_file} >>{stdout_total}')
                    # rcode, stdout, stderr=run_sh(f'cat {stderr_file} >>{stderr_total}')

                    rcode, stdout, stderr=runCommand(rsyncCMD, logger=self.logger, console=True, stdout_file=stdout_file, stderr_file=stderr_file)
                    self.logger.notify("%s --> %s: [rcode:%s]", local_path, remote_path, rcode)



