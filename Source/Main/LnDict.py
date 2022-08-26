#!/usr/bin/python3
# -*- coding: utf-8 -*-
# -*- coding: iso-8859-1 -*-

# updated by ...: Loreto Notarantonio
# Date .........: 25-08-2022 13.50.17

import sys; sys.dont_write_bytecode=True
import os
import yaml, json
from collections import OrderedDict
from collections.abc import MutableMapping
from pathlib import Path

class nullLogger():
    def dummy(self,  title, *args, **kwargs): pass
    critical=trace=error=warning=info=notify=debug=dummy

logger=nullLogger()

class LoretoDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        super(LoretoDict, self).__init__(*args, **kwargs)

    @staticmethod
    def setLogger(mylogger):
        global logger
        logger=mylogger

    #------------------------------------------
    #-
    #------------------------------------------
    # def __missing__(self, key):
    #     result = self[key] = self.default_factory()
    #     return result

    #------------------------------------------
    #- Non cambia nulla se ci sono o meno
    #------------------------------------------
    # def __getattr__(self, key):
    #     OrderedDict.__getattr__(self, key)
    # def __setattr__(self, key):
    #     OrderedDict.__setattr__(self, key)

    # def __getattr__(self, key):
    #     try:
    #         return self[key]
    #     except KeyError:
    #         return super(LoretoDict(), self).__getattr__(key)




    #==========================================================
    # keypath: "key1.key2.key3...." or ["key1", "key2", "key3"]
    #==========================================================
    def get_keypath(self, keypath: (str, list), sep: str='.', default={}, exit_on_not_found=True) -> dict:
        if keypath=='':
            return self
        if isinstance(keypath, str):
            keypath=keypath.split(sep)

        try:
            ptr=self
            for key in keypath:
                ptr=ptr[key]
            return ptr

        except (KeyError) as error: # https://stackoverflow.com/questions/2052390/manually-raising-throwing-an-exception-in-python
            logger.error(error)
            logger.error(f"key: {key} part of keypath: {keypath} NOT found")
            if exit_on_not_found:
                raise

            if default is None:
                default={}
            return default

    getkp=get_keypath


    #==========================================================
    # keypath: "key1.key2.key3...." or ["key1", "key2", "key3"]
    #==========================================================
    # def update_keypath(self, keypath: (str, list), value, sep: str='.', create=False) -> dict:
    #     ptr=self.get_keypath(keypath)

    #     if isinstance(keypath, str):
    #         keypath=keypath.split(sep)

    #     curr_value=ptr[last_key]

    #     if isinstance(curr_value, list):
    #         if isinstance(value, list)
    #             ptr[last_key].extend(value)

    #     elif isinstance(curr_value, dict):
    #         if isinstance(value, dict):
    #             ptr[last_key].update(value)


    #     return ptr

    #==========================================================
    # keypath: "key1.key2.key3...." or ["key1", "key2", "key3"]
    #==========================================================
    def set_keypath(self, keypath: (str, list), value, sep: str='.', create=False) -> dict:
        # if not keypath: return
        if isinstance(keypath, str):
            keypath=keypath.split(sep)

        ptr=self
        last_key=keypath[-1]
        for key in keypath[:-1]:
            if key in ptr:
                ptr=ptr[key]
            else:
                if create:
                    ptr[key]=OrderedDict()
                    ptr=ptr[key]
                else:
                    logger.error(error)
                    logger.error("key: %s part of keypath: %s NOT found", key, keypath)
                    raise

        curr_value=ptr[last_key]
        ptr[last_key]=value
        return ptr

    setkp=set_keypath


    #==========================================================
    # return d1 updated
    #==========================================================
    def merge(self, keypath: (str, list), d2: dict, override=False) -> dict:
        d1=self.get_keypath(keypath)
        return merge(d1=d1, d2=d2, override=override)





    def pjson(self,  **kwargs):
        print(self.to_json(**kwargs))
    print_Json=pjson

    def pyaml(self,  **kwargs):
        print(self.to_yaml(**kwargs))
    print_Yaml=pyaml



    #==========================================================
    # esplode anche le list
    #==========================================================
    def flattenT1(self, dictionary: dict=OrderedDict(), parent_key=False, separator='.'):
        if not dictionary: dictionary=self
        items = []
        for key, value in dictionary.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            if isinstance(value, MutableMapping):
                items.extend(self.flattenT1(value, new_key, separator).items())
            elif isinstance(value, list):
                for k, v in enumerate(value):
                    items.extend(self.flattenT1({str(k): v}, new_key).items())
            else:
                items.append((new_key, value))
        return dict(items)



    #==========================================================
    # NON esplode le list
    # https://www.freecodecamp.org/news/how-to-flatten-a-dictionary-in-python-in-4-different-ways/
    #==========================================================
    def flatten(self, d=OrderedDict(),  parent_key: str = '', sep: str = '.'):
        if not d: d=self
        return LoretoDict(self._flatten_dict_gen(d, parent_key, sep))
        # return dict(self._flatten_dict_gen(d, parent_key, sep))

    def _flatten_dict_gen(self, d, parent_key, sep):
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, MutableMapping):
                yield from self.flatten(v, new_key, sep=sep).items()
            else:
                yield new_key, v




    def to_json(self, title=None, indent=4, sort_keys=True):
        return json.dumps(self, indent=indent, sort_keys=sort_keys, separators=(',', ': '), default=str)

    def to_yaml(self, title=None, indent=4, sort_keys=True):
        # tutto il giro per evitare che compaiano dei rifetimenti strani di benedict nel'output
        _dict={title: self} if title else self # add title
        _json_str=json.dumps(_dict) # convert benedict to json_str
        _json_dict=json.loads(_json_str) # convert json_str to dict
        return yaml.dump(_json_dict, indent=indent, sort_keys=sort_keys, default_flow_style=False)


    def toYamlFile(self, file_out, title=None, indent=4, sort_keys=False, replace=False):
        yaml_data=self.to_yaml(title=title, indent=indent, sort_keys=sort_keys)
        return writeTextFile(data=yaml_data, file_out=file_out, replace=replace)


    def toJsonFile(self, file_out, title=None, indent=4, sort_keys=False, replace=False):
        json_data=self.to_json(title=title, indent=indent, sort_keys=sort_keys)
        return writeTextFile(data=json_data, file_out=file_out, replace=replace)



######################################################
# -
######################################################
def writeTextFile(*, data, file_out: (str, os.PathLike) , replace=False):
    logger.debug('writing file: %s', file_out)
    fileError=True
    file_out=Path(file_out)

    if file_out.exists() and replace is False:
        fWRITE=False
    else:
        fWRITE=True

    if isinstance(data, list):
        data='\n'.join(data)

    if fWRITE:
        os.makedirs(file_out.parent,  exist_ok=True)
        with open(file_out, "w") as f:
            f.write(f'{data}\n')
        fileError=False
    else:
        logger.warning('ERROR: file %s already exists.', file_out )

    return fileError




#==========================================================
# return d1 updated
#==========================================================
def merge(d1: dict, d2: dict, override=False) -> dict:
    if override:
        d1.update(d2)
    else:
        dx=OrderedDict() # create new dict
        dx.update(d2)   # copy d2
        dx.update(d1)   # merge d1
        d1.update(dx)   # move result to d1

    return LoretoDict(d1)



#######################################################
#
#######################################################
if __name__ == '__main__':
    # ---- Loggging
    # logger=setColors('DEBUG', test=False)

    myDict=LoretoDict({'name': 'Jack', 'age': 26})

    myDict['Loreto']=LoretoDict()
    myDict['Loreto']['level2']=LoretoDict()
    myDict['Loreto']['level2']['level3']='level3'

    # myDict['Loreto']['level3']=LoretoDict()
    ptr=myDict['Loreto']['level2']
    ptr['level3']=LoretoDict()
    ptr=ptr['level3']
    ptr['ohhh']='ciao'

    xx=myDict.keypath('Loreto.level2.level3',exit_on_not_found=True)
    # xx=myDict.keypath('Loreto1.level2.level3', default='ciao', exit_on_not_found=True)
    myDict.set_keypath('Loreto.level2.level31.level4', value='ciao', create=True)
    myDict.set_keypath('Loreto1', value='ciao', create=True)
    myDict.set_keypath('', value='empty', create=True)

    xx=myDict.get('Loreto')
    xx=myDict.get('Loreto.level2.level31.level4')

    # flatmyDict=myDict.flattenT2()
    flatmyDict=LoretoDict(myDict.flattenT2())
    flatmyDict.pyaml()
    print(type(flatmyDict))

