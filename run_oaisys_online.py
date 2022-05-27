import argparse
import os
import tarfile
from os.path import join
import subprocess
import shutil
import signal
import sys
from sys import platform, version_info

if version_info.major == 3:
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve
    import contextlib

import uuid


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('args', metavar='arguments', nargs='*', help='Additional arguments which are used to replace placeholders inside the configuration. <args:i> is hereby replaced by the i-th argument.')
parser.add_argument('--blender-install-path', dest='blender_install_path', default=None, help="Set path where blender should be installed. If None is given, /home_local/<env:USER>/blender/ is used per default. This argument is ignored if it is specified in the given YAML config.")
parser.add_argument('--reinstall-blender', dest='reinstall_blender', action='store_true', help='If given, the blender installation is deleted and reinstalled. Is ignored, if a "custom_blender_path" is configured in the configuration file.')
parser.add_argument('--config-file', dest='config_file',  default=None, help='config file path.')
parser.add_argument('-h', '--help', dest='help', action='store_true', help='Show this help message and exit.')
args = parser.parse_args()
blender_install_path = args.blender_install_path
config_file = args.config_file

if blender_install_path is None:
    blender_install_path = os.path.join("/home_local", os.getenv("USERNAME") if platform == "win32" else os.getenv("USER"), "blender")

blender_install_path = os.path.expanduser(blender_install_path)
if blender_install_path.startswith("/home_local") and not os.path.exists("/home_local"):
    user_name = os.getenv("USERNAME") if platform == "win32" else os.getenv("USER")
    home_path = os.getenv("USERPROFILE") if platform == "win32" else os.getenv("HOME")
    print("Warning: Changed install path from {}... to {}..., there is no /home_local/ "
            "on this machine.".format(join("/home_local", user_name), home_path))
            # Replace the seperator from '/' to the os-specific one
            # Since all example config files use '/' as seperator
    blender_install_path = blender_install_path.replace('/'.join(["/home_local", user_name]), home_path, 1)
    blender_install_path = blender_install_path.replace('/', os.path.sep)


# Determine configured version
# right now only support blender-2.93
major_version = "2.93"
minor_version = "0"
blender_version = "blender-{}.{}".format(major_version, minor_version)
if platform == "linux" or platform == "linux2":
    blender_version += "-linux-x64"
    blender_path = os.path.join(blender_install_path, blender_version)
elif platform == "darwin":
    blender_version += "-macos-x64"
    blender_install_path = os.path.join(blender_install_path, blender_version)
    blender_path = os.path.join(blender_install_path, "Blender.app")
elif platform == "win32":
    blender_version += "-windows-x64"
    blender_install_path = os.path.join(blender_install_path, blender_version)
    blender_path = blender_install_path
else:
    raise Exception("This system is not supported yet: {}".format(platform))

 # If forced reinstall is demanded, remove existing files
if os.path.exists(blender_path) and args.reinstall_blender:
    print("Blender installation already exit!")
    shutil.rmtree(blender_path)

# Download blender if it not already exists
if not os.path.exists(blender_path):
    if version_info.major != 3:
        try:
            import lzma
        except ImportError as e:
            print("For decompressing \".xz\" files in python 2.x is it necessary to use lzma")
            raise e  # from import lzma -> pip install --user pyliblzma
    used_url = "https://download.blender.org/release/Blender" + major_version + "/" + blender_version
    if platform == "linux" or platform == "linux2":
        url = used_url + ".tar.xz"
    elif platform == "darwin":
        url = used_url + ".dmg"
    elif platform == "win32":
        url = used_url + ".zip"
    else:
        raise Exception("This system is not supported yet: {}".format(platform))
    try:
        import progressbar
        class DownloadProgressBar(object):
            def __init__(self):
                self.pbar = None
            def __call__(self, block_num, block_size, total_size):
                if not self.pbar:
                    self.pbar = progressbar.ProgressBar(maxval=total_size)
                    self.pbar.start()
                downloaded = block_num * block_size
                if downloaded < total_size:
                    self.pbar.update(downloaded)
                else:
                    self.pbar.finish()

        print("Downloading blender from " + url)
        file_tmp = urlretrieve(url, None, DownloadProgressBar())[0]
    except ImportError:
        print("Progressbar for downloading, can only be shown, "
              "when the python package \"progressbar\" is installed")
        file_tmp = urlretrieve(url, None)[0]


    if platform == "linux" or platform == "linux2":
        if version_info.major == 3:
            SetupUtility.extract_file(blender_install_path, file_tmp, "TAR")
        else:
            with contextlib.closing(lzma.LZMAFile(file_tmp)) as xz:
                with tarfile.open(fileobj=xz) as f:
                    f.extractall(blender_install_path)
    elif platform == "darwin":
        if not os.path.exists(blender_install_path):
            os.makedirs(blender_install_path)
        os.rename(file_tmp, os.path.join(blender_install_path, blender_version + ".dmg"))
        # installing the blender app by mounting it and extracting the information
        subprocess.Popen(["hdiutil attach {}".format(os.path.join(blender_install_path, blender_version + ".dmg"))],
                         shell=True).wait()
        subprocess.Popen(
            ["cp -r {} {}".format(os.path.join("/", "Volumes", "Blender", "Blender.app"), blender_install_path)],
            shell=True).wait()
        subprocess.Popen(["diskutil unmount {}".format(os.path.join("/", "Volumes", "Blender"))], shell=True)
        # removing the downloaded image again
        subprocess.Popen(["rm {}".format(os.path.join(blender_install_path, blender_version + ".dmg"))], shell=True).wait()
        # add Blender.app path to it
    elif platform == "win32":
        SetupUtility.extract_file(blender_install_path, file_tmp)
    # rename the blender folder to better fit our existing scheme
    for folder in os.listdir(blender_install_path):
        if os.path.isdir(os.path.join(blender_install_path, folder)) and folder.startswith("blender-" + major_version):
            os.rename(os.path.join(blender_install_path, folder), os.path.join(blender_install_path, blender_version))


print("Using blender in " + blender_path)

# Run script
if platform == "linux" or platform == "linux2":
    blender_run_path = os.path.join(blender_path, "blender")
elif platform == "darwin":
    blender_run_path = os.path.join(blender_path, "Contents", "MacOS", "Blender")
elif platform == "win32":
    blender_run_path = os.path.join(blender_install_path, "blender-windows64", "blender")
else:
    raise Exception("This system is not supported yet: {}".format(platform))


repo_root_directory = os.path.dirname(os.path.realpath(__file__))
path_src_run = os.path.join(repo_root_directory, "GRPCWrapper.py")

if config_file is None:
    print("WARNING: no config file provided! Will use default cfg file!")
    config_file = os.path.join(repo_root_directory,"cfgExamples/OAISYS_default_cfg.json")

p = subprocess.Popen([blender_run_path, "--background", "--python-use-system-env", "--python-exit-code", "2", "--python", path_src_run, "--", "-c", config_file],
                             env=dict(os.environ, PYTHONPATH=os.getcwd(), PYTHONNOUSERSITE="1"), cwd=repo_root_directory)

def handle_sigterm(signum, frame):
    clean_temp_dir()
    p.terminate()
signal.signal(signal.SIGTERM, handle_sigterm)

try:
    p.wait()
except KeyboardInterrupt:
    try:
        p.terminate()
    except OSError:
        pass
    p.wait()

exit(p.returncode)