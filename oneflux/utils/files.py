'''
oneflux.utils.files

For license information:
see LICENSE file or headers in oneflux.__init__.py 

File manipulation utilities

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import os
import sys
import logging
import subprocess
import zipfile
import hashlib
import fnmatch

from datetime import datetime

from oneflux import ONEFluxError

MD5_BLOCK_SIZE = 2 ** 16  # 65536 bytes (64KiB) seems to be ideal block size (depends on storage buffer size?)

HOME = os.path.expanduser("~")

_log = logging.getLogger(__name__)


def block_md5(filename, block_size=MD5_BLOCK_SIZE):
    """
    Computes md5sum in chunks to reduce memory use

    :param filename: path to file
    :type filename: str
    :param block_size: block size to be used in computing each md5 iteration
    :type block_size: int
    """
    md5sum = hashlib.md5()
    with open(filename, 'rb') as f:
        block = f.read(block_size)
        while block:
            md5sum.update(block)
            block = f.read(block_size)
    return md5sum.hexdigest()


def replace_file(filename, pattern='_', timestamped=False):
    """
    Renames file to new by adding numeric counter as:
    pattern# if not timestamped or
    pattern#_YYYYmmddHHMMSS if timestamped

    :param filename: file to be renamed
    :type filename: str
    :param pattern: pattern to be added to indicate renaming
    :type pattern: str
    :param timestamped: adds timestamp if True
    :type timestamped: boolean
    :rtype: str
    """
    filename_noext, ext = os.path.splitext(filename)
    count = 1
    timestamp = (datetime.now().strftime("_%Y%m%d%H%M%S") if timestamped else '')
    new_filename = filename_noext + pattern + str(count) + timestamp + ext
    while os.path.isfile(new_filename):
        count += 1
        new_filename = filename_noext + pattern + str(count) + timestamp + ext
    os.rename(filename, new_filename)
    _log.info("Renamed file '{f1}' to '{f2}'".format(f1=filename, f2=new_filename))
    return new_filename


def create_replace_file(filename, timestamped=False):
    """
    If file exists, renames it and creates new empty file

    :param filename: file to be created
    :type filename: str
    :rtype: None
    """
    if os.path.isfile(filename):
        replace_file(filename, pattern='_v', timestamped=timestamped)
    else:
        base_directory = os.path.dirname(filename)
        if not os.path.exists(base_directory):
            os.makedirs(base_directory)
    open(filename, 'a').close()
    return


def check_create_directory(directory):
    """
    Checks if directory exists and creates if not

    :param directory: path to be tested/created
    :type directory: str
    """
    if not os.path.isdir(directory):
        if os.path.exists(directory):
            msg = "Directory check: not a directory '{p}'".format(p=directory)
            _log.critical(msg)
            raise ONEFluxError(msg)
        else:
            os.makedirs(directory)
            _log.info("Created directory '{p}'".format(p=directory))
    return

def list_files_pattern(tdir, tpattern):
    """
    Looks for files matching pattern exist in directory,
    if not logs error and raises exception

    :param tdir: path to directory to be searched and tested
    :type tdir: str
    :param tpattern: file name pattern to be tested
    :type tpattern: str
    """
    if not os.path.isdir(tdir):
        msg = "Directory {d} not found".format(d=tdir)
        _log.warning(msg)
        return []

    matches = fnmatch.filter(os.listdir(tdir), tpattern)

    if matches:
        _log.debug("Found {n} matches in '{d}'for pattern '{p}'".format(n=len(matches), d=tdir, p=tpattern))
        return matches
    else:
        _log.debug("Found NO matches in '{d}'for pattern '{p}'".format(d=tdir, p=tpattern))
        return []


def is_executable(filename):
    """
    Returns True if file exists and is executable, False otherwise

    :param filename: file path to be tested
    :type filename: str
    :rtype: boolean
    """
    return os.path.isfile(filename) and os.access(filename, os.X_OK)


def get_abspath(path):
    """
    If not an absolute path, converts to absolute path using cwd

    :param path: path to be converted into absolute path
    :type path: str
    :rtype: str
    """
    if os.path.isabs(path):
        return path
    else:
        return os.path.abspath(path)


def find_command(command):
    """
    Finds full path of executable

    :param command: executable name
    :type command: str
    :rtype: str or None
    """
    basepath, _ = os.path.split(command)
    if basepath:
        if is_executable(command):
            return command
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            filename = os.path.join(path, command)
            if is_executable(filename):
                return filename
    return


def compress_file(filename):
    """
    Compresses file with gzip

    :param filename: path to file to be compressed
    :type filename: str
    :rtype: str or None
    """
    if not os.path.isfile(filename):
        msg = "File not found or cannot be accessed: '{f}'".format(f=filename)
        _log.critical(msg)
        raise ONEFluxError(msg)
    try:
        r = subprocess.call(['gzip', '-f', filename])
        _log.debug("Compressing file '{d}'. Result: {o}".format(d=filename, o=('success' if r == 0 else "fail ({r})".format(r=r))))
    except subprocess.CalledProcessError as e:
        msg = "Problems compressing file '{d}'. Error: '{e}'".format(d=filename, e=str(e))
        _log.critical(msg)
        raise ONEFluxError(msg)
    return filename + '.gz'


def run_command(cmd):
    """
    Run command as subprocess

    :param cmd: command to be run
    :type cmd: list (of str)
    :rtype: str or None
    """
    _log.debug('External command execution: {c}'.format(c=cmd))
    try:
        sproc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = sproc.communicate()
        exitcode = sproc.returncode
        if exitcode == 0:
            _log.debug("Execution succeeded: {o}".format(o=stdout.replace('\r', '  ').replace('\n', '  ')))
            if stderr:
                _log.warning("Execution STDERR: {o}".format(o=stderr.replace('\r', '  ').replace('\n', '  ')))
        else:
            msg = 'Execution failed! EXITCODE: {c}  STDOUT: {o}  STDERR: {e}'.format(c=exitcode, o=stdout.replace('\r', '  ').replace('\n', '  '), e=stderr.replace('\r', '  ').replace('\n', '  '))
            _log.critical(msg)
            raise ONEFluxError(msg)
    except subprocess.CalledProcessError as e:
        msg = "Execution raised error: '{e}'".format(e=str(e))
        _log.critical(msg)
        raise ONEFluxError(msg)
    return stdout


def last_line(filename):
    """
    Returns last nonempty line

    :param filename: name of data file
    :type filename: str
    :rtype: str
    """

    statinfo = os.stat(filename)
    filesize = statinfo.st_size
    if filesize == 0:
        msg = "File '{f}' empty".format(f=filename)
        _log.critical(msg)
        raise Exception(msg)

    last_line = ''
    with open(filename, 'rU') as f:
        f.seek(-1, 2)  # moves 1 back from end (2)
        ch = f.read(1)
        while ch != '\n' or last_line.strip() == '':
            last_line = ch + last_line
            f.seek(-2, 1)  # moves 2 back from current (1)
            ch = f.read(1)  # reads, moves 1 forward

    return last_line


def zip_file(filename, zipfilename=None, zip_option='w'):
    """
    Creates zip file compressing file (name from filename
    if not given, replacing extension with .zip and removing
    base path). If zip file exists, can append to existing
    zip file using zip_option 'a'.

    Returns zip file name

    :param filename: path to file to be compressed
    :type filename: str
    :param zipfilename: filename for resulting zip file
    :type zipfilename: str
    :param zip_option: eithe 'w' for (over)write, or 'a' for append
    :type zip_option: str
    :rtype: str
    """
    if not zipfilename:
        name, _ = os.path.splitext(filename)
        zipfilename = name + ".zip"

    try:
        with zipfile.ZipFile(zipfilename, zip_option, zipfile.ZIP_DEFLATED) as z:
            _log.debug("Compressing '{f}' into '{z}' using zip option {o}".format(f=filename, z=zipfilename, o=zip_option))
            z.write(filename, os.path.basename(filename))
    except Exception as e:
        _log.error("Error in zip_file: {e}".format(e=e))
    return zipfilename

def zip_file_list(filename_list, zipfilename, zip_option='w'):
    """
    Creates zip file compressing all files in list.
    If zip file exists, can append to existing zip file using
    zip_option 'a'.

    Returns zip file name

    :param filename_list: list of paths to files to be compressed
    :type filename_list: list
    :param zipfilename: filename for resulting zip file
    :type zipfilename: str
    :param zip_option: eithe 'w' for (over)write, or 'a' for append
    :type zip_option: str
    :rtype: str
    """

    try:
        with zipfile.ZipFile(zipfilename, zip_option, zipfile.ZIP_DEFLATED) as z:
            _log.debug("Compressing files into '{z}' using zip option {o}".format(z=zipfilename, o=zip_option))
            for filename in filename_list:
                _log.debug("Adding '{f}'".format(f=filename))
                z.write(filename, os.path.basename(filename))
    except Exception as e:
        _log.error("Error in zip_file: {e}".format(e=e))
    return zipfilename


def file_stat(filename):
    """
    Returns information on file

    :param filename: path to file to be checked
    :type filename: str
    :rtype: typle
    """

    size = os.stat(filename).st_size
    md5sum = block_md5(filename=filename)
    timestamp_change = datetime.fromtimestamp(os.stat(filename).st_mtime)

    return (size, md5sum, timestamp_change)


def join_paths(a, *p):
    """
    Similar to os.path.join, but always includes preceding paths,
    even if subsequent paths begin with '/'

    :param path_list: list of paths to be joined
    :type path_list: list
    :rtype: str
    """
    path = a
    for b in p:
        if path == '':
            path = b
        elif b.startswith('/'):
            if path.endswith('/'):
                path += b[1:]
            else:
                path += '/' + b[1:]
        else:
            if path.endswith('/'):
                path += b
            else:
                path += '/' + b
    return path


def file_exists_not_empty(filename,):
    """
    Tests if file exists and is not empty
    
    :param filename: full path of file to be checked
    :type filename: str
    """
    if os.path.isfile(filename):
        if os.stat(filename).st_size == 0:
                return False
    else:
        return False
    return True


if __name__ == '__main__':
    raise ONEFluxError('Not executable')
