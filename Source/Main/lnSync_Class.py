#!/usr/bin/python
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 11-01-2023 09.38.09

import sys; sys.dont_write_bytecode=True
import os
import glob
from types import SimpleNamespace
from subprocessRun import run_sh
import LnUtils

from ColoredLogger import getColors; C=getColors()


from subprocessPopen import runCommand
# from LoadYamlFile_Class import LoadYamlFile_Class
from read_ini_file import readIniFile
# from keyboard_prompt import keyb_prompt
# from envarsYamlLoader import loadYamlFile


########################################################
#
########################################################
class lnSync_Class():

    def __init__(self, *, main_config: dict, profile_name: str, logger, fRCLONE: bool=False, fRSYNC: bool=False):
        self.logger=logger


        main_data               = main_config['main']
        self.rclone_config_file = main_data['rclone_config_file']

        self.runtime_dir        = main_data['runtime_dir']
        # self.dry_run            = main_data['dry-run']
        self.rclone_conf        = readIniFile(filename=self.rclone_config_file)

        self.profiles           = main_config['profiles']

        ### ---- read profile to be processed
        self.profile=self.load_req_profile(profile_name=profile_name)

        self.isRCLONE=fRCLONE
        self.isRSYNC=fRSYNC

        if self.isRCLONE:
            # _config=main_config['rclone']
            # self.main_options=main_config['rclone.options']
            # self.rclone_bin=_config['bin']
            # self.pgm_bin=self.rclone_bin
            self.profile.update(main_config['rclone'])

        elif self.isRSYNC:
            # _config=main_config['rsync']
            # self.main_options=main_config['rsync.options']
            # self.rsync_bin=_config['bin']
            # self.pgm_bin=self.rsync_bin

            self.profile.update(main_config['rsync'])

        else:
            self.logger.critical('rclone or rsync must be specified.')
            sys.exit(1)


        ### add remote nodes data
        if isinstance(self.profile['remote_nodes'], str): self.profile['remote_nodes']=self.profile['remote_nodes'].split()
        self.profile['nodes']={}
        for node_name in self.profile['remote_nodes']:
            node=self.rclone_conf.get(node_name, {})
            self.profile['nodes'][node_name]=node

        # self.pgm_options=[]
        self.exclude_files=[]

        if 'folders' in self.profile.keys():
            if isinstance(self.profile['folders'], str):
                self.profile['folders']=self.profile['folders'].split()
        else:
            self.profile['folders']=[]



        # self.setOptions(options=_config['options'])
        # self.setExcludeFiles(excl=main_config['common_exclude_files'])
        self.profile.to_json(filepath=f"{self.runtime_dir}/json/{profile_name}.json")
        self.profile.to_yaml(filepath=f"{self.runtime_dir}/yaml/{profile_name}.yaml")

        self.temp_dir = self.profile['temp_dir']
        if not os.path.exists(self.temp_dir):
                os.mkdir(self.temp_dir)






    ### --------------------------------------
    ### ----- retrieve profile to be processed
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
    ### --------------------------------------
    def load_req_profile(self, profile_name):
        ### formato benedict
        if profile_name in self.profiles.keys():
            profile=self.profiles[profile_name] # scrittura su file
            profile.to_json(filepath=f"{self.runtime_dir}/json/{profile_name}.json")
            profile.to_yaml(filepath=f"{self.runtime_dir}/yaml/{profile_name}.yaml")
        else:
            self.logger.error('Profile %s not found', profile_name)
            self.logger.notify('     Please enter one of the following profile name:')
            colored_profile_name=C.redH + profile_name + C.greenH + C.colorReset
            for profile in self.profiles.keys():
                if profile.startswith('_') or profile in ['main', 'local_vars']: continue
                self.logger.info('     %s', profile.replace(profile_name, colored_profile_name))
            sys.exit(1)

        return profile



    def setExcludeFiles(self, excl: list=[]):
        self.exclude_files.extend(excl)
        self.exclude_files = list(dict.fromkeys(self.exclude_files))

        temp_fname=f'{self.temp_dir}/exclude_files.txt'
        LnUtils.writeTextFile(data=self.exclude_files, filename=temp_fname, replace=True)
        return temp_fname


    def setOptions_XXXX(self, options: list=[]):
        if isinstance(options, list):
            self.pgm_options.extend(options)
        else:
            self.pgm_options.append(options)
        # print(self.pgm_options)
        return ' '.join(self.pgm_options)


    def checkLocalDir(self, path, exit_on_error=False):
        if os.path.exists(path):
            return path

        elif exit_on_error:
            self.logger.critical("Local directory: %s doesn't esists", path)
            sys.exit(1)

        else:
            return None

    # def resolveRemoteDir(self, node_name: str, path: str, check_it: bool=False, exit_on_error=False):
    def resolveRemoteDir(self, node_name: str, check_it: bool=False, exit_on_error=False):
        path=self.profile["remote_root_dir"]
        if path is None: path=''

        node=self.profile.get(f'nodes.{node_name}', {})
        node_type=node.get('type')
        check_cmd=None

        if node_name=='local': #---- rclone --config ./rclone.conf -L lsd /home/loreto
            remote_path=path
            check_cmd=f"ls -l {remote_path}"

        elif node_type=='sftp': #---- rclone --config=./rclone.conf -L lsd lnpi31:/mnt/Toshiba_1TB_LnDisk/Filu
            ssh_key=node['key_file']
            ssh_port=node['port']
            ssh_host=node['host']
            ssh_user=node['user']
            self.ssh_base=f"-i {ssh_key} -p {ssh_port} {ssh_user}@{ssh_host}"

            if self.isRCLONE:
                remote_path=f"{node_name}:{path}"
                check_cmd=f"{self.profile['bin']} --config={self.rclone_config_file} -L lsd {remote_path}"

            elif self.isRSYNC:
                remote_path=f"{ssh_user}@{ssh_host}:{path}"
                check_cmd=f"ssh {self.ssh_base} ls -l {path}/"
                self.profile["sync_options"].append(f"-e 'ssh -i {ssh_key} -p {ssh_port}'")

        elif node_type in ['gmail', 'drive']: #---- rclone --config=./rclone.conf -L lsd nloreto:_@NLORETO

            if self.isRCLONE:
                remote_path=f"{node_name}:_@{node_name.upper()}{path}"
                check_cmd=f"{self.profile['bin']} --config={self.rclone_config_file} -L lsd {remote_path}"
            else:
                remote_path=None
                self.logger.error('node: %s: [%s] is not supported by rSync!', node_name, node_type )

        else:
            self.logger.error('node: %s: [%s] is not supported by rSync!', node_name, node_type )
            remote_path=None


        # check if remote_path exists
        if check_cmd and check_it:
            self.logger.info("[CMD] - %s", check_cmd)
            run_sh(cmd=check_cmd, logger=self.logger, exit_on_error=exit_on_error, stacklevel=2)

        return remote_path




    #==============================================================
    #- check local directory
    #- get and check remote dir
    #- create eclude_file
    #- build rclone command
    #==============================================================
    def processFolder(self, folder_name, local_path, dest_path):
        # v=prfVars

        ### add project exclude file to exclude base list
        exclude_filename=self.setExcludeFiles(self.profile.get("exclude_files", []))



        stdout_file=f'{self.temp_dir}/lnSync_stdout.log'
        stderr_file=f'{self.temp_dir}/lnSync_stderr.log'
        delete_excluded='--delete-excluded' if gv.delete_excluded else ''
        dq='"'
        ### -----------------------------
        ### ---- prepare command
        ### -----------------------------
        configuration_file=f"--config={self.rclone_config_file}" if self.isRCLONE else ''

        log_filename=f"{self.temp_dir}/{folder_name}.log"
        if os.path.exists(log_filename):
            os.remove(log_filename)


        quoted_local_path=f"{dq}{local_path}/{dq}"
        quoted_dest_path=f"{dq}{dest_path}/{dq}"
        options=' '.join(self.profile['sync_options'])
        baseCMD=[self.profile['bin'],
                    configuration_file,
                    f"--exclude-from {exclude_filename}",
                    f"--log-file {log_filename}", # se lo metto perdo l'output su console
                    delete_excluded,
                    options,
                    gv.dry_run,
                    quoted_local_path,
                    quoted_dest_path,
                ]
        synchCMD=' '.join(baseCMD)



        ### ----------------------------------
        # -  comando colorato per la console
        ### ----------------------------------
        colored_data=[
                    C.redH    + gv.dry_run + C.colorReset,
                    C.greenH  + quoted_local_path + C.colorReset,
                    C.yellowH + quoted_dest_path  + C.colorReset,
                ]

        colored_command=baseCMD[:-3]
        colored_command.extend(colored_data)
        colored_command=' '.join(colored_command)
        self.logger.info(colored_command)


        ### ----------------------------------
        # -  convert command to string
        ### ----------------------------------
        if gv.prompt:
            keyb_msg='[R]un [any]Skip'
            choice=LnUtils.keyb_prompt(msg=keyb_msg, validKeys='ENTER', exitKeys='x|q', displayValidKeys=False)
            if not choice=='r': return

        ### ----------------------------------
        # -  execute command
        ### ----------------------------------
        rcode, stdout, stderr=runCommand(synchCMD, logger=self.logger, console=self.profile["log_to_console"], stdout_file=stdout_file, stderr_file=stderr_file)

        ### print log file
        with open(log_filename, 'r', encoding='utf-8') as f:
            for line in f:
                print(line[28:].strip('\n'))
        if self.isRSYNC:
            print('''
                for file status legenda see: https://stackoverflow.com/questions/4493525/what-does-f-mean-in-rsync-logs
            ''')



        self.logger.info("%s --> %s: [rcode:%s]", quoted_local_path, quoted_dest_path, rcode)

        # if ' ' in local_path:
        #     import pdb; pdb.set_trace(); pass # by Loreto




    #==============================================================
    #- check local directory
    #- get and check remote dir
    #- create eclude_file
    #- build rclone command
    #==============================================================
    def processProfile(self, gVars):
        global gv
        gv=gVars

        ### add project options to common options list
        if gv.mirror:
            options.extend(['--delete-after'])

        # if self.isRSYNC and self.profile.get('big_files'):
        #     self.profile['sync_options'].extend(self.profile['big_files_or_remote_options'])

        if self.isRSYNC and self.profile.get('rsync_extra_options'):
            self.profile['sync_options'].extend(self.profile['rsync_extra_options'])


        for node_name in self.profile['nodes'].keys():
            self.logger.notify("going to update node: %s", node_name)
            self.logger.notify("...the following folders:")
            for folder in self.profile['folders']:
                self.logger.notify("    - %s", folder)

            local_root_path=self.profile["local_root_dir"]

            ### ---- check remote path directory
            remote_path=self.resolveRemoteDir(node_name=node_name, check_it=True, exit_on_error=True)
            if not remote_path:
                return



            for folder_name in self.profile['folders']:
                if folder_name.endswith('.sub'):
                    folder_name=folder_name.split('.sub')[0]
                    fSubFolder=True
                else:
                    fSubFolder=False

                ### ---- check local path directory
                local_path=self.checkLocalDir(path=f'{local_root_path}/{folder_name}', exit_on_error=True)

                if fSubFolder:
                    sub_folders=os.listdir(f'{local_root_path}/{folder_name}')

                    for sub_folder in sub_folders:
                        _local_path=f'{local_path}/{sub_folder}'
                        if not os.path.isdir(_local_path):
                            self.logger.notify('file: %s will be skipped', _local_path)
                            # LnUtils.keyb_prompt(msg=f'file: {_local_path} will be skipped', validKeys='ENTER', exitKeys='x|q', displayValidKeys=False)
                            continue
                        _dest_path=f"{remote_path}/{folder_name}/{sub_folder}"
                        self.processFolder(folder_name=folder_name, local_path=_local_path, dest_path=_dest_path)

                else:
                    dest_path=f"{remote_path}/{folder_name}"
                    self.processFolder(folder_name=folder_name, local_path=local_path, dest_path=dest_path)






            post_commands=self.profile.get('post_commands', [])
            if post_commands and not gv.fPostcommands:
                self.logger.warning("   enter --post-commands to execute the following commands")

            for command in post_commands:
                fPOST_COMMANDS=False
                token=command.split()
                if token[0] == 'alias':
                    """ https://www.cyberciti.biz/faq/use-bash-aliases-ssh-based-session/ """
                    command=command=f"ssh -t {self.ssh_base} /bin/bash -ic {' '.join(token[1:])}"
                else:
                    command=f"ssh {self.ssh_base} {command}"

                self.logger.notify(command)
                if gv.fPostcommands:
                    run_sh(cmd=command, logger=self.logger, exit_on_error=True)
                    fPOST_COMMANDS=True







        ### ---- execute rclone

