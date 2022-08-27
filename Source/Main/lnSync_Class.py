#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 27-08-2022 12.19.16

import sys; sys.dont_write_bytecode=True
import os
from benedict import benedict
from subprocessRun import run_sh
# from subprocessPopen import runCommand
# from keyboard_prompt import prompt
# from read_ini_file import readIniFile
from fileUtils import writeTextFile
from LnDict import LoretoDict
from ColoredLogger import getColors; C=getColors()


from LoadYamlFile_Class import LoadYamlFile
from read_ini_file import readIniFile, readIniFile_preset
from rClone_Class import rClone_Class
from rSync_Class import rSync_Class


########################################################
#
########################################################
class lnSync_Class():

    def __init__(self, *, main_config_filename: str, logger):
        self.logger=logger

        self.config=self.load_profiles(filename=main_config_filename)
        self.profiles=self.config['profiles']

        self.rclone=rClone_Class(config=self.config['rclone'], logger=self.logger)
        self.rsync=rSync_Class(config=self.config['rsync'], logger=self.logger)
        # self.rclone_ini=self.rclone.getRcloneConf() # Utilizzo il file di configurazione di rclone per capire il tipo di nodo di destinazione





    # --------------------------------------
    # ----- reading profiles configuration
    # --------------------------------------
    def load_profiles(self, filename):
        self.logger.info('reading file: %s', filename)

        YamlData=LoadYamlFile(filename=filename, logger=self.logger)
        config=YamlData.config()
        self.runtime_dir=config.get_keypath('main.runtime_dir')
        self.temp_dir=config.get_keypath('main.tmp_dir')
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
            profile=LoretoDict(self.config.get_keypath(['profiles', profile_name]))
            profile.toJsonFile(file_out=f"{self.runtime_dir}/json/{profile_name}.json", replace=True)
            profile.toYamlFile(file_out=f"{self.runtime_dir}/yaml/{profile_name}.yaml", replace=True)
        else:
            self.logger.error('Profile %s not found', profile_name)
            self.logger.notify('     Please enter one of the following profile name:')
            for profile in self.profiles.keys():
                self.logger.notify('     %s', profile)
            sys.exit(1)

        return profile

    #==============================================================
    #- check local directory
    #- get and check remote dir
    #- create eclude_file
    #- build rclone command
    #==============================================================
    def processProfile(self, profile_name: str, delete_excluded: bool=False, dry_run='--dry-run', prompt=False, fRCLONE=False, fRSYNC=False):

        # ---- read profile to be processed
        profile=self.load_req_profile(profile_name=profile_name)

        if isinstance(profile['remote_nodes'], str): profile['remote_nodes']=profile['remote_nodes'].split()
        if isinstance(profile['folders'], str): profile['folders']=profile['folders'].split()
        dry_run=os.environ['lnSync_DRY_RUN']

        # if fRCLONE:
        #     self.rclone.processProfile(profile=profile, delete_excluded=delete_excluded, dry_run=dry_run)
        # if fRSYNC:
        #     self.rsync.processProfile(profile=profile, delete_excluded=delete_excluded, dry_run=dry_run)


        for node_name in profile['remote_nodes']:
            self.logger.notify("going to update node: %s", node_name)
            self.logger.notify("...the following folders:")
            for folder in profile['folders']:
                self.logger.notify("    - %s", folder)

            check_remote_dir=True # check just first remote folder
            for folder in profile['folders']:
                data={
                    "node_name":        node_name,
                    # "node":             self.rclone.rclone_conf.get(node_name, {}),
                    "folder":           folder,
                    "profile":          profile,
                    "delete_excluded":  delete_excluded,
                    "dry_run":          dry_run,
                    "prompt":           prompt,
                    "check_remote_dir": check_remote_dir,
                }
                if fRCLONE:
                    # self.rclone.processFolder(node_name=node_name, folder=folder, profile=profile, delete_excluded=delete_excluded, dry_run=dry_run)
                    self.rclone.processFolder(**data)
                if fRSYNC:
                    # self.rsync.processFolder(node_name=node_name, folder=folder, profile=profile, delete_excluded=delete_excluded, dry_run=dry_run)
                    self.rsync.processFolder(**data)

                check_remote_dir=False

        # ---- execute rclone

