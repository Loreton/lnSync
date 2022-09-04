#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 04-09-2022 12.43.34

import sys; sys.dont_write_bytecode=True
import os
import yaml
from collections import OrderedDict
from pathlib import Path
from LnDict import LoretoDict
import zipfile, io

##########################################
#
##########################################
class nullLogger():
    def dummy(title, *args, **kwargs):
        pass
    critical=trace=error=notify=function=warning=info=debug=dummy



############################################
# Supporta anche l'esecuzione come zip
############################################
class LoadYamlFile_V02(object):

    def __init__(self, filename, paths=['conf', 'common_includes', 'templates'], logger=nullLogger):
        self.logger=logger
        script_path=Path(sys.argv[0]).resolve()

        """ check it its a zip file """
        if zipfile.is_zipfile(script_path):
            self.zipFile=script_path
            self.zFile=zipfile.ZipFile(self.zipFile, "r")
            self.zFileNamelist=self.zFile.namelist()

        else:
            self.zFile=None
            self.zFileNamelist=[]


        self._dict=LoretoDict(self.read_file(filename))
        self.resolve_include(d=self._dict)
        self._dict=self.resolve_vars(self._dict)


    def config(self):
        return self._dict


    def read_file_prev(self, filename):
        if not os.path.exists(filename):
            self.logger.error('File: %s not found', filename)
            sys.exit(1)

        with open(filename, 'r') as f:
            content=f.read() # single string

        if isinstance(content, dict):
            my_dict=content
        else:
            my_dict=yaml.load(content, Loader=yaml.SafeLoader)

        ''' l'include Non va bene perché il secondo file va in override al primo '''
        my_dict=self.resolve_vars(my_dict) # risolve le variabili interne al file
        return my_dict

    def read_file(self, filename):
        # it's on filesystem
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                content=f.read() # single string

        # it's inside zipfile
        elif filename in self.zFileNamelist:
            content=io.BytesIO(self.zFile.read(filename))

        else:
            self.logger.error('File: %s not found', filename)
            sys.exit(1)


        if isinstance(content, dict):
            my_dict=content
        else:
            my_dict=yaml.load(content, Loader=yaml.SafeLoader)

        ''' l'include Non va bene perché il secondo file va in override al primo '''
        my_dict=self.resolve_vars(my_dict) # risolve le variabili interne al file
        return my_dict


    #============================================
    #- _!include: conf/lnprofile.yaml
    #- il nuovo file andrà nella root del dict
    #- tested: OK
    #============================================
    def resolve_include(self, d):
        sep='.'

        fFOUND=True
        while fFOUND:
            fFOUND=False
            flat_dict=d.flatten()
            for keypath, value in flat_dict.items():
                if keypath.endswith("include_files"): # ex: _!include: conf/lnprofile.yaml
                    fFOUND=True
                    if not sep in keypath:
                        keypath=sep+keypath
                    parent, last_key = keypath.rsplit('.', 1)

                    ptr=d.get_keypath(parent)     # ptr to parent
                    del ptr[last_key]                  # remove include_files entry
                    for filename in value:
                        _dict=self.read_file(filename)
                        value=d.merge(keypath=parent, d2=_dict, override=True) # update current




    # ----------------------------------------------
    # - process all keys for:
    #      include#section_name
    #       The section_name will be included in the replacing the option include#
    #
    # - and all values for:
    #      @@_get.key1.key2...
    # ----------------------------------------------
    def resolve_vars(self, d: dict) -> dict:
        ln_dict=LoretoDict(d)
        flat_dict=ln_dict.flattenT1()
        for keypath, value in flat_dict.items():
            if isinstance(value, list) and 'post_commands' in keypath:
                self.resolve_in_string(ln_dict, keypath, value)

            elif isinstance(value, str):
                # value=os.path.expandvars(value)
                self.resolve_in_string(ln_dict, keypath, value)

        return ln_dict


    def resolve_in_string(self, ln_dict, keypath, value):
        # ------------------------------
        def split_var(value, prefix, suffix):
            left_data, rest = value.split(prefix, 1)
            var_name, rest = rest.split(suffix, 1)
            return left_data, var_name, rest
        # ------------------------------

        pfx_get_dict='${get_dict:'
        pfx_get_list='${get_list:'
        pfx_get='${get:'
        pfx_env='${env:'

        if isinstance(value, str):
            value=os.path.expandvars(value)
            # ------------------------------
            # folders=/tmp/${env:main.MyData}/file.txt
            # ------------------------------
            while pfx_env in value:
                left_data, var_name, rest=split_var(value=value, prefix=pfx_env, suffix="}")
                env_value=os.environ[var_name]
                value=left_data+env_value+rest # importante impostarlo per poter usire dal loop


                value=ln_dict.set_keypath(keypath, value)

            # ------------------------------
            # folders=${get_dict:main.MyData}
            # folders._!_remove_this_key=${get_dict:main.MyData}  remove_this_key will be removed
            # folders=/tmp/${get:main.MyData}
            # folders=/tmp/${get:main.MyData}/file.txt
            # ------------------------------
            while pfx_get_dict in value:
                left_data, var_name, rest=split_var(value=value, prefix=pfx_get_dict, suffix="}")
                value=ln_dict.get_keypath(var_name)

                if keypath.endswith('remove_this_key'):
                    parent, last_key = keypath.rsplit('.', 1)
                    ptr=ln_dict.get_keypath(parent) # ptr to parent
                    del ptr[last_key]                  # remove xxxx_dummy_key entry
                    value=ln_dict.merge(keypath=parent, d2=value, override=False) # update current

                else:
                    value=ln_dict.merge(keypath=keypath, d2=value, override=False)

            # ------------------------------
            # folders=${get:main.MyData}
            # folders=/tmp/${get:main.MyData}
            # folders=/tmp/${get:main.MyData}/file.txt
            # ------------------------------
            while pfx_get in value:
                left_data, var_name, rest=split_var(value=value, prefix=pfx_get, suffix="}")
                value=ln_dict.get_keypath(var_name)
                ln_dict.set_keypath(keypath, value)
