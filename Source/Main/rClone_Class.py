#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 26-08-2022 14.04.46

import sys; sys.dont_write_bytecode=True
import os
from benedict import benedict
from subprocessRun import run_sh
from subprocessPopen import runCommand
from keyboard_prompt import keyb_prompt
from read_ini_file import readIniFile
from fileUtils import writeTextFile


########################################################
#
########################################################
class rClone_Class():
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
        self.rclone_config_file = config['config_file'] # ini configuration file di rclone
        self.rclone_bin         = config['bin']
        self.rclone_options     = config['options']
        self.exclude_files      = config['exclude_files']
        self.rclone_ini         = readIniFile(filename=self.rclone_config_file)
        self.temp_dir       =config['tmp_dir']
        if not os.path.exists(self.temp_dir):
                os.mkdir(self.temp_dir)





    # def getRcloneConf(self, filename):
    #     if self.rclone_ini is None:
    #         rclone_conf=readIniFile(filename=filename)
    #     return rclone_conf


    def checkLocalDir(self, path, exit_on_not_found=False):
        if os.path.exists(path):
            return path

        elif exit_on_not_found:
            self.logger.critical("Local directory: %s doesn't esists", path)
            sys.exit(1)

        else:
            return None


    def resolveRemoteDir(self, node_name: str, path: str, exit_on_not_found=False):
        if path is None: path=''
        node=self.rclone_ini.get(node_name, {})
        node_type=node.get('type')

        if node_name=='local': #---- rclone --config ./rclone.conf -L lsd /home/loreto
            remote_path=path

        elif node_type in ['gmail', 'drive']: #---- rclone --config=./rclone.conf -L lsd nloreto:_@NLORETO
            remote_path=f"{node_name}:_@{node_name.upper()}{path}"

        elif node_type=='sftp': #---- rclone --config=./rclone.conf -L lsd lnpi31:/mnt/Toshiba_1TB_LnDisk/Filu
            remote_path=f"{node_name}:{path}"

        else:
            remote_path=None
            if exit_on_not_found:
                self.logger.critical('node: %s or node_type: %s is unmanaged!', node_name, node_type )
                sys.exit(1)
            else:
                self.logger.error('node: %s or node_type: %s is unmanaged!', node_name, node_type )

        return remote_path


    def checkRemoteDir(self, path, exit_on_not_found=False):
        check_cmd=f"{self.rclone_bin} --config={self.rclone_config_file} -L lsd {path}"
        self.logger.info("[CMD] - %s", check_cmd)
        rcode, stdout, stderr=run_sh(cmd=check_cmd, logger=self.logger, exit_on_error=True)

        if rcode:
            if exit_on_not_found:
                self.logger.critical("remote directory: %s not found", path)
                sys.exit(1)
            else:
                self.logger.error("remote directory: %s not found", path)



    def setExcludeFiles(self, excl: list=[]):
        if not self.exclude_files:
            self.exclude_files=[]
        self.exclude_files.extend(excl)
        temp_fname=f'{self.temp_dir}/exclude_files.txt'
        writeTextFile(data=self.exclude_files, file_out=temp_fname, replace=True, logger=self.logger)
        return temp_fname


    def setOptions(self, options: list=[]):
        if not self.rclone_options:
            self.rclone_options=[]
        self.rclone_options.extend(options)
        return ' '.join(self.rclone_options)





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

        stdout_file=f'{self.temp_dir}/rclone_stdout.log'
        stderr_file=f'{self.temp_dir}/rclone_stderr.log'
        # stdout_total=f'{self.temp_dir}/rclone_stdout_total.log'
        # stderr_total=f'{self.temp_dir}/rclone_stderr_total.log'


        # ---- check remote path directory 
        for node_name in profile['remote_nodes']:
            remote_path=self.resolveRemoteDir(node_name=node_name, path=root_remote_path, exit_on_not_found=True)
            if remote_path:
                self.checkRemoteDir(path=remote_path, exit_on_not_found=True)

                # add project exclude file to list
                exclude_filename=self.setExcludeFiles(profile.get("exclude_files", []))

                # add project options to list
                options=self.setOptions(options=profile.get("options", []))

                for folder in profile['folders']:
                    local_path=self.checkLocalDir(path=f'{root_local_path}/{folder}', exit_on_not_found=True)
                    remote_path=f'{root_remote_path}/{folder}' # controlliamo solo il root_remote_path

                    # ---- prepare command
                    rcloneCMD=f"""{self.rclone_bin} \
                                    {dry_run} \
                                    --config={self.rclone_config_file}  \
                                    --exclude-from {exclude_filename} \
                                    --delete-excluded={delete_excluded} \
                                    {options} \
                                    {local_path}\
                                    {remote_path}"""


                    # - remove extra blanks from command
                    rcloneCMD=" ".join(rcloneCMD.split())
                    self.logger.notify(rcloneCMD)

                    prompt(msg='', validKeys='ENTER', exitKeys='x|q', displayValidKeys=False)
                    # os.system(rcloneCMD)
                    # rcode, stdout, stderr=run_sh(f'cat {stdout_file} >>{stdout_total}')
                    # rcode, stdout, stderr=run_sh(f'cat {stderr_file} >>{stderr_total}')

                    rcode, stdout, stderr=runCommand(rcloneCMD, logger=self.logger, console=True, stdout_file=stdout_file, stderr_file=stderr_file)
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
    def processFolder(self, node_name: str, folder: str, profile: dict, delete_excluded: bool=False, prompt: bool=True, dry_run='--dry-run'):
        redH='\033[1;31m'
        yellowH='\033[1;33m'
        colorReset='\033[0m'
        # ---- check local directory
        root_local_path=profile.get("base_local_root_dir")
        root_remote_path=profile.get("base_remote_root_dir", '')

        stdout_file=f'{self.temp_dir}/rclone_stdout.log'
        stderr_file=f'{self.temp_dir}/rclone_stderr.log'
        # stdout_total=f'{self.temp_dir}/rclone_stdout_total.log'
        # stderr_total=f'{self.temp_dir}/rclone_stderr_total.log'


        # ---- check remote path directory
        remote_path=self.resolveRemoteDir(node_name=node_name, path=root_remote_path, exit_on_not_found=True)
        if remote_path:
            self.checkRemoteDir(path=remote_path, exit_on_not_found=True)

            # add project exclude file to list
            exclude_filename=self.setExcludeFiles(profile.get("exclude_files", []))

            # add project options to list
            options=self.setOptions(options=profile.get("options", []))


            # ---- process folder
            local_path=self.checkLocalDir(path=f'{root_local_path}/{folder}', exit_on_not_found=True)
            remote_path=f'{root_remote_path}/{folder}' # controlliamo solo il root_remote_path

            # ---- prepare command
            rcloneCMD=f"""{self.rclone_bin} \
                            {dry_run} \
                            --config={self.rclone_config_file}  \
                            --exclude-from {exclude_filename} \
                            --delete-excluded={delete_excluded} \
                            {options} \
                            {local_path} \
                            {remote_path}"""


            # - remove extra blanks from command
            rcloneCMD=" ".join(rcloneCMD.split())
            # self.logger.notify(rcloneCMD)
            # self.logger.notify(rcloneCMD.replace(folder, yellowH+folder+colorReset)).replace(dry_run, redH+dry_run+colorReset)
            self.logger.notify(rcloneCMD.replace(folder, yellowH+folder+colorReset))

            if prompt:
                keyb_prompt(msg='', validKeys='ENTER', exitKeys='x|q', displayValidKeys=False)

            rcode, stdout, stderr=runCommand(rcloneCMD, logger=self.logger, console=True, stdout_file=stdout_file, stderr_file=stderr_file)
            self.logger.notify("%s --> %s: [rcode:%s]", local_path, remote_path, rcode)

