from math import dist
import os
import os.path as osp
import sys
import argparse
import subprocess
import shutil
from pathlib import Path
from zipfile import ZipFile

def src_dir():
    return Path(__file__).parent

def parse_args():
    parser = argparse.ArgumentParser();
    parser.add_argument('--pkg-dir', default='pkg', type=Path)
    parser.add_argument('--dist-dir', default='dist', type=Path)
    return vars(parser.parse_args())

def build():
    # build debug
    if sys.platform == 'win32':
        envs = os.environ
        envs['CFLAGS'] = '/MTd'
    shutil.rmtree('target', ignore_errors=True)
    # override CFLAGS to build debug build, details see https://github.com/dtolnay/cxx/issues/880
    subprocess.check_call(['cargo', 'build'], env=envs)
    # build release
    subprocess.check_call(['cargo', 'build', '--release'])

def _ensure_empty_dir(dir: Path):
    if dir.exists():
        shutil.rmtree(dir, ignore_errors=True)
    dir.mkdir(parents=True)

def prepare_package(pkg_dir: Path):
    # copy header files
    shutil.copytree(src_dir()/'target'/'cxxbridge'/'rust', pkg_dir/'include'/'rust')
    shutil.copytree(src_dir()/'target'/'cxxbridge'/'tokenizers-cpp'/'tokenizers-cpp', pkg_dir/'include'/'tokenizers-cpp')
    shutil.copytree(src_dir()/'thirdparty'/'nonstd', pkg_dir/'include'/'nonstd')

    headers = [
        'common.h',
        'normalizers.h',
        'pre_tokenizers.h',
        'models.h',
        'processors.h',
        'decoders.h',
        'tokenizer.h',
        'tokens.h',
        'input_sequence.h',
    ] 
    for header in headers:
        shutil.copyfile(src_dir()/'tokenizers-cpp'/ header, pkg_dir/'include'/'tokenizers-cpp'/ header)
   
    # copy build files
    shutil.copytree(src_dir()/'build', pkg_dir/'build')

    # copy debug lib
    (pkg_dir/'lib'/'debug').mkdir(parents=True)
    shutil.copyfile(src_dir()/'target'/'debug'/'tokenizers.lib', pkg_dir/'lib'/'debug'/'tokenizers.lib')
    
    # copy release lib
    (pkg_dir/'lib'/'release').mkdir(parents=True)
    shutil.copyfile(src_dir()/'target'/'release'/'tokenizers.lib', pkg_dir/'lib'/'release'/'tokenizers.lib')

def infer_version():
    output = subprocess.check_output(['git', 'describe', '--tags'], encoding='utf-8')
    # python-v0.9.4-116-g7c76158
    return output.split('-')[1]

def package_filename():
    targetOS = {'win32':'win', 'darwin':'osx'}
    return f'tokenizers_{targetOS[sys.platform]}_{infer_version()}.zip'

def make_archive(pkg_dir, archive_filepath):
    with ZipFile(archive_filepath, 'w') as zipObj:
        for folderName, subfolders, filenames in os.walk(pkg_dir):
            for filename in filenames:
                # create complete filepath of file in directory
                filePath = os.path.join(folderName, filename)
                zipObj.write(filePath, osp.relpath(filePath, pkg_dir))

def main(pkg_dir, dist_dir):
    build()

    _ensure_empty_dir(pkg_dir)
    prepare_package(pkg_dir)

    # create dist dir
    _ensure_empty_dir(dist_dir)
    make_archive(pkg_dir, dist_dir/package_filename() )

    # upload?

if __name__ == '__main__':
    main(**parse_args())
