#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 05-09-2022 15.12.36

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
    # sotto VsCode lanciare il seguente comando...
    # /home/loreto/.ln/init/Loretorc_Variables
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

        # ---- finally
        # self._dict=self.resolve_vars(self._dict)
        self._dict=self.resolve_parent(self._dict)


    def config(self):
        return self._dict


    def read_file(self, filename):
        # it's on filesystem
        self.logger.debug('reding file: %s', filename)
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
        my_dict=self.resolve_vars(my_dict) # risolve le variabili interne del nuovo file
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
            flat_dict=d.flattenT1a(key_str="include_files", explode_list=False)
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

        pfx_generic='${'
        pfx_get='${get:'
        pfx_get_dict='${get_dict:'
        pfx_get_list='${get_list:'
        pfx_env='${env:'

        ln_dict=LoretoDict(d)
        flat_dict=ln_dict.flattenT1a(value_str=pfx_generic, explode_list=False)

        for keypath, value in flat_dict.items():
            if isinstance(value, str):
                if pfx_generic in value:
                    self.resolve_envars(prefix=pfx_env, d=ln_dict, keypath=keypath, value=value)
                    self.resolve_get(prefix=pfx_get, d=ln_dict, keypath=keypath, value=value)
                    self.resolve_get_dict(prefix=pfx_get_dict, d=ln_dict, keypath=keypath, value=value)


        return ln_dict




    # ------------------------------
    def split_var(self, value, prefix, suffix):
        left_data, rest = value.split(prefix, 1)
        var_name, rest = rest.split(suffix, 1)
        return left_data, var_name, rest
    # ------------------------------

    # ------------------------------
    # folders=/tmp/${env:main.MyData}/file.txt
    # ------------------------------
    def resolve_envars(self, prefix, d, keypath, value):
        value=os.path.expandvars(value)
        while prefix in value:
            left_data, var_name, rest=self.split_var(value=value, prefix=prefix, suffix="}")
            env_value=os.environ[var_name]
            value=left_data+env_value+rest # importante impostarlo per poter usire dal loop
            value=d.set_keypath(keypath, value)


    # ------------------------------
    # folders=${get_dict:main.MyData}
    # folders._!_remove_this_key=${get_dict:main.MyData}  remove_this_key will be removed
    # folders=/tmp/${get:main.MyData}
    # folders=/tmp/${get:main.MyData}/file.txt
    # ------------------------------
    def resolve_get_dict(self, prefix, d, keypath, value):
        while prefix in value:
            left_data, var_name, rest=self.split_var(value=value, prefix=prefix, suffix="}")
            value=d.get_keypath(var_name)

            if keypath.endswith('remove_this_key'):
                parent, last_key = keypath.rsplit('.', 1)
                ptr=d.get_keypath(parent) # ptr to parent
                del ptr[last_key]                  # remove xxxx_dummy_key entry
                value=d.merge(keypath=parent, d2=value, override=False) # update current

            else:
                value=d.merge(keypath=keypath, d2=value, override=False)




    # ------------------------------
    # folders=${get:main.MyData}
    # folders=/tmp/${get:main.MyData}
    # folders=/tmp/${get:main.MyData}/file.txt
    # ------------------------------
    def resolve_get(self, prefix, d, keypath, value):
        while prefix in value:
            left_data, var_name, rest=self.split_var(value=value, prefix=prefix, suffix="}")
            value=d.get_keypath(var_name)
            d.set_keypath(keypath, value)


    # ------------------------------
    # folders=/tmp/${get_parent:-2.MyData}/file.txt
    # ------------------------------
    def resolve_parent(self, d: dict) -> dict:
        prefix='${get_parent:'

        ln_dict=LoretoDict(d)
        flat_dict=ln_dict.flattenT1a(value_str=prefix, explode_list=True)
        for keypath, value in flat_dict.items():
            if isinstance(value, str):
                value=os.path.expandvars(value) # resolve env variables
                while prefix in value:
                    left_data, var_name, rest=self.split_var(value=value, prefix=prefix, suffix="}")

                    """get parent level... (first qualifier, negative number)
                    """
                    parent, *rel_path=var_name.split('.')
                    token=keypath.split('.')
                    full_keypath=token[:int(parent)] + rel_path
                    ptr_value=d.get_keypath(full_keypath)
                    value=left_data + ptr_value + rest
                    d.set_keypath(keypath, value)
        return ln_dict
