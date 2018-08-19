import os
from os.path import join as pjoin
import directory_info.fileInfo as fileInfo
import ntpath
import json
import shutil

class ModBuild(object):

    def __init__(self, mod_name, target_dir, files_to_copy=[]):
        self.mod_name = mod_name
        self.active = True
        self.files = files_to_copy
        self.config_file = None
        self.config = {}
        self.target_root = target_dir
        self.source_root = ''
        self.exclude_files = []

    def load_config(self, config_file):
        """
        Loads json config file an example of a simple config file is:

        {
          "RAGEHook": {
            "files_to_copy": [
              "*"
            ],
            "mkdirs": [
              "Plugins"
            ],
            "exclude_dir": [
              "Licenses",
              "SDK"
            ],
            "exclude_files": [
              "Readme.txt"
            ],
            "source_root": "D:\\\\LSDPFR\\\\RAGEHook\\\\RAGEPluginHook_0_63_1224_15140_ALPHA"
          }
        }

        :param config_file:
        :return:
        """
        self.config_file = config_file
        with open(self.config_file, 'r') as fd:
            j = json.load(fd)
            self.config = j.get(self.mod_name, None)
            if self.config is None:
                return
            self.files = self.config.get('files_to_copy', [])
            self.exclude_files = self.config.get('exclude_files', [])
            self.files = list(
                filter(lambda x: normalize_ntpath(x) not in [normalize_ntpath(p) for p in self.exclude_files],
                       self.files))
            self.source_root = self.config.get('source_root', '')

    def process_wildcards(self):
        """
        If a path has a astrisk (*) in it that is indicating import all files recursivily under that path. You are able
        to explicitly exclude files or directories with:
        'exlcude_dir' and 'exclude_files' in the config

        :return:
        """
        wild_cards = [_dir for _dir in self.files if ntpath.basename(_dir) == '*']
        for wc in wild_cards:
            self.files = list(filter(lambda x: x != wc, self.files))
            self.files += [fn.replace(self.source_root, '') for fn in
                           fileInfo.get_file_list(pjoin(self.source_root, ntpath.dirname(wc)))]  # This is a hack
            self.files = list(
                filter(lambda x: normalize_ntpath(x) not in [normalize_ntpath(p) for p in self.exclude_files],
                       self.files))

    def copy_to_target(self):
        """
        Copies the files identified to the target identified
        :return:
        """
        if not ntpath.exists(self.target_root):
            os.makedirs(self.target_root)

        for fname in self.files:
            if not ntpath.exists(pjoin(self.target_root, ntpath.dirname(fname.strip('\\')))):
                os.makedirs(pjoin(self.target_root, ntpath.dirname(fname.strip('\\'))))
            shutil.copy2(pjoin(self.source_root, fname.strip('\\')), pjoin(self.target_root, fname.strip('\\')))

    def exclude_directory(self):
        """
        Uses self.config['exclude_dir'] to identify and remove files found in specific directories that are excluded in
        the configuration.

        :return:
        """
        for exclude in self.config.get('exclude_dir', []):
            self.exclude_files += [fn.replace(self.source_root, '') for fn in
                                   fileInfo.get_file_list(pjoin(self.source_root, exclude))]

    def mkdirs(self):
        for _dir in self.config['mkdirs']:
            if not ntpath.exists(pjoin(self.target_root, _dir)):
                os.makedirs(pjoin(self.target_root, _dir))


def normalize_ntpath(pname):
    """
    I got really annoyed with doing string minimpulation on Windows Paths. This basically ensures that I am not dealling
    with `\\\\` and `\\` and `/`. Probably a better way of doing this - but for now this is working.

    :param pname:
    :return:
    """
    return pjoin(ntpath.dirname(pname), ntpath.basename(pname))
