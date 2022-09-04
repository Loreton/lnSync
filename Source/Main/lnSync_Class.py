#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 04-09-2022 18.10.55

import sys; sys.dont_write_bytecode=True
import os
# from benedict import benedict
from subprocessRun import run_sh
# from subprocessPopen import runCommand
# from keyboard_prompt import prompt
# from read_ini_file import readIniFile
from fileUtils import writeTextFile
from LnDict import LoretoDict
from ColoredLogger import getColors; C=getColors()

from subprocessPopen import runCommand

from LoadYamlFile_Class_V02 import LoadYamlFile_V02 as LoadYamlFile
from read_ini_file import readIniFile
from keyboard_prompt import keyb_prompt


########################################################
#
########################################################
class lnSync_Class():

    def __init__(self, *, main_config_filename: str, logger, fRCLONE: bool=False, fRSYNC: bool=False):
        self.logger=logger

        main_config             = self.load_profiles(filename=main_config_filename)
        import pdb; pdb.set_trace(); pass # by Loreto
        main_data               = main_config['main']
        self.rclone_config_file = main_data['rclone_config_file']

        self.runtime_dir        = main_data['runtime_dir']
        self.dry_run            = main_data['dry-run']
        self.rclone_conf        = readIniFile(filename=self.rclone_config_file)

        self.profiles           = main_config['profiles']


        self.isRCLONE=fRCLONE
        self.isRSYNC=fRSYNC

        if self.isRCLONE:
            _config=main_config['rclone']
            self.rclone_bin=_config['bin']
            self.pgm_bin=self.rclone_bin

        elif self.isRSYNC:
            _config=main_config['rsync']
            self.rsync_bin=_config['bin']
            self.pgm_bin=self.rsync_bin

        else:
            self.logger.critical('rclone or rsync must be specified.')
            sys.exit(1)

        self.temp_dir = _config['temp_dir']
        if not os.path.exists(self.temp_dir):
                os.mkdir(self.temp_dir)

        self.pgm_options=[]
        self.exclude_files=[]
        self.setOptions(options=_config['options'])
        self.setExcludeFiles(excl=main_config['common_exclude_files'])



    # --------------------------------------
    # ----- reading profiles configuration
    # --------------------------------------
    def load_profiles(self, filename):
        self.logger.info('reading file: %s', filename)

        YamlData=LoadYamlFile(filename=filename, logger=self.logger)
        config=YamlData.config()
        self.runtime_dir=config.get_keypath('main.runtime_dir')
        self.temp_dir=config.get_keypath('main.temp_dir')
        if not os.path.exists(self.temp_dir):
                os.mkdir(self.temp_dir)


        # ---------- save configuration file for debugging
        config.toYamlFile(file_out=f"{self.runtime_dir}/yaml/main_config.yaml", replace=True)
        config.toJsonFile(file_out=f"{self.runtime_dir}/json/main_config.json", replace=True)
        # ---------- save configuration file for debugging
        return config



    # --------------------------------------
    # ----- retrieve profile to be processed
    #
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
    # --------------------------------------
    def load_req_profile(self, profile_name):
        if profile_name in self.profiles.keys():
            profile=LoretoDict(self.profiles[profile_name]) # solo per la scrittura su file
            profile.toJsonFile(file_out=f"{self.runtime_dir}/json/{profile_name}.json", replace=True)
            profile.toYamlFile(file_out=f"{self.runtime_dir}/yaml/{profile_name}.yaml", replace=True)
        else:
            self.logger.error('Profile %s not found', profile_name)
            self.logger.notify('     Please enter one of the following profile name:')
            for profile in self.profiles.keys():
                self.logger.notify('     %s', profile)
            sys.exit(1)

        return profile



    def setExcludeFiles(self, excl: list=[]):
        self.exclude_files.extend(excl)
        self.exclude_files = list(dict.fromkeys(self.exclude_files))

        temp_fname=f'{self.temp_dir}/exclude_files.txt'
        writeTextFile(data=self.exclude_files, file_out=temp_fname, replace=True, logger=self.logger)
        return temp_fname


    def setOptions(self, options: list=[]):
        self.pgm_options.extend(options)
        return ' '.join(self.pgm_options)


    def checkLocalDir(self, path, exit_on_error=False):
        if os.path.exists(path):
            return path

        elif exit_on_error:
            self.logger.critical("Local directory: %s doesn't esists", path)
            sys.exit(1)

        else:
            return None

    def resolveRemoteDir(self, node_name: str, path: str, check_it: bool=False, exit_on_error=False):
        if path is None: path=''
        node=self.rclone_conf.get(node_name, {})
        node_type=node.get('type')


        if node_name=='local': #---- rclone --config ./rclone.conf -L lsd /home/loreto
            remote_path=path
            check_cmd=f"ls -l {remote_path}"

        elif node_type=='sftp': #---- rclone --config=./rclone.conf -L lsd lnpi31:/mnt/Toshiba_1TB_LnDisk/Filu
            ssh_key=node.get('key_file')
            ssh_port=node.get('port')
            ssh_host=node.get('host')
            ssh_user=node.get('user')
            self.ssh_remote_conn=f"ssh -i {ssh_key} -p {ssh_port} {ssh_user}@{ssh_host}"

            if self.isRCLONE:
                remote_path=f"{node_name}:{path}"
                check_cmd=f"{self.rclone_bin} --config={self.rclone_config_file} -L lsd {remote_path}"

            elif self.isRSYNC:
                remote_path=f"{ssh_user}@{ssh_host}:{path}"
                check_cmd=f"{self.ssh_remote_conn} ls -l {path}"
                # check_cmd=f"ssh -i {ssh_key} -p {ssh_port} {ssh_user}@{ssh_host} ls -l {path}"

        elif node_type in ['gmail', 'drive']: #---- rclone --config=./rclone.conf -L lsd nloreto:_@NLORETO

            if self.isRCLONE:
                remote_path=f"{node_name}:_@{node_name.upper()}{path}"
                check_cmd=f"{self.rclone_bin} --config={self.rclone_config_file} -L lsd {remote_path}"
            else:
                remote_path=None

        else:
            self.logger.error('node: %s: [%s] is not supported by rSync!', node_name, node_type )
            remote_path=None


        # check if remote_path exists
        if check_cmd and check_it:
            self.logger.info("[CMD] - %s", check_cmd)
            run_sh(cmd=check_cmd, logger=self.logger, exit_on_error=exit_on_error)

        return remote_path




    #==============================================================
    #- check local directory
    #- get and check remote dir
    #- create eclude_file
    #- build rclone command
    #==============================================================
    def processProfileV2(self, profile_name: str, delete_excluded: bool=False, dry_run='--dry-run', prompt=False, post_commands=False):
        # ---- read profile to be processed
        profile=self.load_req_profile(profile_name=profile_name)

        if isinstance(profile['remote_nodes'], str): profile['remote_nodes']=profile['remote_nodes'].split()
        if isinstance(profile['folders'], str): profile['folders']=profile['folders'].split()

        stdout_file=f'{self.temp_dir}/lnSync_stdout.log'
        stderr_file=f'{self.temp_dir}/lnSync_stderr.log'
        delete_excluded='--deleted-excluded' if delete_excluded else ''

        for node_name in profile['remote_nodes']:
            self.logger.notify("going to update node: %s", node_name)
            self.logger.notify("...the following folders:")
            for folder in profile['folders']:
                self.logger.notify("    - %s", folder)

            check_remote_dir=True # check just first remote folder

            for folder in profile['folders']:
                # ---- check local directory
                root_local_path=profile["root_local_dir"]
                root_remote_path=profile["root_remote_dir"]

                # add project exclude file to exclude base list
                exclude_filename=self.setExcludeFiles(profile.get("exclude_files", []))

                # add project options to common options list
                options=self.setOptions(options=profile.get("options", []))

                # ---- check local path directory
                local_path=self.checkLocalDir(path=f'{root_local_path}/{folder}/', exit_on_error=True)

                # ---- check remote path directory
                remote_path=self.resolveRemoteDir(node_name=node_name, path=root_remote_path, check_it=check_remote_dir, exit_on_error=True)
                dest=f"{remote_path}/{folder}/"

                # -----------------------------
                # ---- prepare command
                # -----------------------------
                configuration_file=f"--config={self.rclone_config_file}" if self.isRCLONE else ''

                baseCMD=[self.pgm_bin,
                            configuration_file,
                            f"--exclude-from {exclude_filename}",
                            f"--log-file {self.temp_dir}/{folder}.log", # se lo metto perdo l'outpus su console
                            delete_excluded,
                            options,
                            dry_run,
                            local_path ,
                            dest,
                        ]
                synchCMD=' '.join(baseCMD)


                # ----------------------------------
                # -  comando colorato per la console
                # ----------------------------------
                colored_data=[
                            C.redH    + dry_run    + C.colorReset,
                            C.greenH  + local_path + C.colorReset,
                            C.yellowH + dest       + C.colorReset,
                        ]

                colored_command=baseCMD[:-3]
                colored_command.extend(colored_data)
                colored_command=' '.join(colored_command)
                self.logger.notify(colored_command)

                # ----------------------------------
                # -  convert command to string
                # ----------------------------------

                if prompt:
                    keyb_prompt(msg='', validKeys='ENTER', exitKeys='x|q', displayValidKeys=False)

                # ----------------------------------
                # -  execute command
                # ----------------------------------
                rcode, stdout, stderr=runCommand(synchCMD, logger=self.logger, console=True, stdout_file=stdout_file, stderr_file=stderr_file)
                self.logger.notify("%s --> %s: [rcode:%s]", local_path, dest, rcode)
                check_remote_dir=False

            for command in profile['post_commands']:
                command=f"{self.ssh_remote_conn} {command}"
                self.logger.notify(command)
                if post_commands:
                    import pdb; pdb.set_trace(); pass # by Loreto
                    run_sh(cmd=command, logger=self.logger, exit_on_error=True)
                else:
                    self.logger.warning("   enter --post-commands to execute the above commands")







        # ---- execute rclone

