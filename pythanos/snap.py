from pathlib import Path
import random
import shutil
from typing import List
import re
import urllib.request
import concurrent.futures
import time
from os import path
import socket
import json
import csv


class Snap:

    def __init__(self, inputvar) -> None:
        self.inputvar = inputvar
        self.download_file_name = f"download.xyz"
        self.download_file_type = self.download_file_name.split('.')[-1]
        self.download_complete_path = Path.joinpath(
            Path.cwd(), self.download_file_name)
        self.download_save_path = self.download_complete_path.parent
        self.run_loader = False
        self.split_ratio = (0.8, 0.1, 0.1)
        self.split_fixed = (100, 100)
        self.seed = 69
        self.output = "output"
        self.split_train_idx = None
        self.split_val_idx = None
        self.use_test = False
        self.create_mode = f'copy'

    def input_type(self) -> None:
        try:
            if Path(self.inputvar).is_file():
                print(f"File exist")
            elif Path(self.inputvar).is_dir():
                print(f"Dir exist")
            elif self.isValidURL():
                print(f"URL exist")
            else:
                raise TypeError
        except Exception as e:
            print(f"Input must be a valid Directory, File or a URL")

    def list_dirs(self, directory) -> List:
        return [f for f in Path(directory).iterdir() if f.is_dir()]

    def list_files(self, directory) -> List:
        return [f for f in Path(directory).iterdir()
                if f.is_file() and not f.name.startswith(".")]

    def get_nth_dirs(self, path=None, n=1):
        if path is not None:
            self.output = path
        assert Path(self.output).is_dir(), f"Invalid directory fed."
        return self._get_nth_dirs(self.output, n)

    def _get_nth_dirs(self, path, n=1):
        dirs = []
        for e in Path(path).iterdir():
            if e.is_dir():
                if len(str(Path(e).relative_to(self.output)).split("/")) == 1 and n == 1:
                    dirs.append(e)
                else:
                    for i in self._get_nth_dirs(e, n-1):
                        dirs.append(i)
        return dirs

    def isValidURL(self):
        regex = r"\A(((https?|ftp)://|(www|ftp)\.))?[a-z0-9-]+(\.[a-z0-9-]+)+([/?].*)?\Z"

        p = re.compile(regex)

        if self.inputvar is None:
            return False

        if re.search(p, self.inputvar):
            return True
        else:
            return False

    def get_all_invalid_dirs_w_paths(self, allowed_exts=['.jpg', '.png']):

        allowed_exts = list(set(allowed_exts))
        for i in range(len(allowed_exts)):
            allowed_exts[i] = allowed_exts[i].lower()

        dir_d1_w_files = []
        temp_dir_d1_w_files = []
        empty_dirs_d1 = []
        temp_empty_dirs_d1 = []
        dirs_at_d2 = []
        exts_files = []

        for e in Path(self.inputvar).iterdir():
            temp_dirs_at_d2 = []
            temp_exts_files = []
            if e.is_dir():
                check_empty = True
                for i in Path(e).iterdir():
                    check_empty = False
                    if i.is_dir():
                        temp_dirs_at_d2.append(i)
                    elif i.parent.is_dir():
                        if ''.join(i.suffixes).lower() not in allowed_exts:
                            temp_exts_files.append(i)
                else:
                    if check_empty is True:
                        temp_empty_dirs_d1.append(e)
            else:
                temp_dir_d1_w_files.append(e)
            if temp_dirs_at_d2:
                dirs_at_d2.append([temp_dirs_at_d2, e])
            if temp_exts_files:
                exts_files.append([temp_exts_files, e])

        if temp_dir_d1_w_files:
            dir_d1_w_files.append([temp_dir_d1_w_files, Path(self.output)])

        if temp_empty_dirs_d1:
            empty_dirs_d1.append([temp_empty_dirs_d1, Path(self.output)])

        return (dir_d1_w_files, empty_dirs_d1,
                dirs_at_d2, exts_files)

    def is_valid_dir(self, allowed_exts=['.jpg', '.png'],
                     verbose=1, do_on_err='copy', output='output',
                     err_log_mode='json'):

        assert type(allowed_exts) == list, f"""
        Allowed extensions should be a list"""
        assert len(allowed_exts) > 0, f"""
        Allowed extensions list can't be empty"""
        assert do_on_err in ('copy', 'move', 'delete'), f"""
        Invalid do on err passed. Can only be copy or move"""
        assert verbose in [0, 1], f"Verbose can be 0 (silent) or 1 (normal)"

        self.output = output

        check_root_dir_empty = True

        for e in Path(self.inputvar).iterdir():
            if e.is_dir() or e.is_file():
                check_root_dir_empty = False
                break
        else:
            if check_root_dir_empty:
                print(f"[-] CHECK -> Root directory not empty -> FAILED")
                return None, False

        dir_d1_w_files, empty_dirs_d1, dirs_at_d2, \
            exts_files = self.get_all_invalid_dirs_w_paths(allowed_exts)

        if verbose == 1:
            if dir_d1_w_files:
                print(f"*"*70)
                print(f"[-] CHECK 1 -> Files at depth 1 -> FAILED", "\n")
                print(f"""(1) Root directory "{Path(self.output).name}" """)
                print(f"contains files at depth 1, namely - ")
                for i in dir_d1_w_files[0][0]:
                    print(f"""-> "{i.name}" """)
            else:
                print(f"*"*70)
                print(f"[+] CHECK 1 -> Files at depth 1 -> PASSED")

            if empty_dirs_d1:
                print(f"*"*70)
                print(f"[-] CHECK 2 -> Empty dirs at depth 1 -> FAILED", "\n")
                print(f"""(1) Root directory "{Path(self.output).name}" """)
                print(f"contains empty directories at depth 1, namely - ")
                for i in empty_dirs_d1[0][0]:
                    print(f"""-> "{i.name}" """)
            else:
                print(f"*"*70)
                print(f"[+] CHECK 2 -> Empty dirs at depth 1 -> PASSED")

            if dirs_at_d2:
                print(f"*"*70)
                print(f"[-] CHECK 3 -> Dirs at depth 2 -> FAILED", "\n")
                print(f"These are the list of empty directories at depth 1")
                for i, f in enumerate(dirs_at_d2):
                    print("\n", f"""({i+1}) Directory "{f[1].name}" """)
                    print(f"at depth 1 contains empty directories, namely -")
                    for p in f[0]:
                        print(f"""-> "{p.name}" """)
            else:
                print(f"*"*70)
                print(f"[+] CHECK 3 -> Dirs at depth 2 -> PASSED")

            if exts_files:
                print(f"*"*70)
                print(
                    f"[-] CHECK 4 -> Unwanted file extensions -> FAILED", "\n")
                print(f"These are the list of directories with")
                print(f"unwanted extension files at depth 1")
                for i, f in enumerate(exts_files):
                    print(
                        "\n", f"""({i+1}) Directory "{f[1].name}" at depth""")
                    print(f"1 has files with unwanted extensions, namely")
                    for p in f[0]:
                        print(f"""-> "{p.name}" """)
            else:
                print(f"*"*70)
                print(f"[+] CHECK 4 -> Unwanted file extensions -> PASSED")

        if len(dir_d1_w_files) > 0 or len(empty_dirs_d1) > 0 or len(
                dirs_at_d2) > 0 or len(exts_files) > 0:
            if verbose == 0:
                print(f"[-] Some checks haven't passed.")
        else:
            print(f"[+] All checks passed.")

        if err_log_mode == 'json':
            self.write_to_JSON(dir_d1_w_files, empty_dirs_d1,
                               dirs_at_d2, exts_files)
        elif err_log_mode == 'csv':
            self.write_to_JSON(dir_d1_w_files, empty_dirs_d1,
                               dirs_at_d2, exts_files)
        else:
            self.write_to_text(dir_d1_w_files, empty_dirs_d1,
                               dirs_at_d2, exts_files)

        if do_on_err == 'delete':
            for i in [dir_d1_w_files, exts_files]:
                for x, _ in i:
                    for f in x:
                        Path(f).unlink()
            for i in [empty_dirs_d1, dirs_at_d2]:
                for x, _ in i:
                    for f in x:
                        shutil.rmtree(f)
            print(f"Unwanted files and directories have been deleted.")
            return None, True

        for i in [dir_d1_w_files, empty_dirs_d1, dirs_at_d2, exts_files]:
            for k, _ in enumerate(i):
                i[k][1] = i[k][1].name

        if do_on_err == 'copy':
            for i in [dirs_at_d2, exts_files]:
                if len(i) > 0:
                    self.copy_files(i, None, False)
            for i in [dir_d1_w_files, empty_dirs_d1]:
                if len(i) > 0:
                    self.copy_files(i, None, None)
        else:
            for i in [dir_d1_w_files, dirs_at_d2, exts_files, empty_dirs_d1]:
                if len(i) > 0:
                    self.move_files(i, None, False)

        return self.output, True

    def write_to_JSON(self, *args):
        dir_d1_w_files, empty_dirs_d1, dirs_at_d2, exts_files = args
        dictjson = {}

        dictjson["CHECK 1 -> Files at depth 1"] = str(dir_d1_w_files)
        dictjson["CHECK 2 -> Empty dirs at depth 1"] = str(empty_dirs_d1)
        dictjson["CHECK 3 -> Dirs at depth 2"] = str(dirs_at_d2)
        dictjson["CHECK 4 -> Unwanted file extensions"] = str(exts_files)

        json_object = json.dumps(dictjson, indent=4)
        filename = Path(self.output).parent.joinpath("errorlog.json")

        print(f"creating JSON log file...")

        with open(filename, "w") as outfile:
            outfile.write(json_object)

        print(f"created log file successfully.")

        return filename

    def write_to_text(self, *args):
        dir_d1_w_files, empty_dirs_d1, dirs_at_d2, exts_files = args
        filename = Path(self.output).parent.joinpath("errorlog.txt")
        file = open(filename, "w")

        file.write("CHECK 1 -> Files at depth 1")
        file.write(str(dir_d1_w_files))
        file.write("CHECK 2 -> Empty dirs at depth 1")
        file.write(str(empty_dirs_d1))
        file.write("CHECK 3 -> Dirs at depth 2")
        file.write(str(dirs_at_d2))
        file.write("CHECK 4 -> Unwanted file extensions")
        file.write(str(exts_files))

        file.close()

        return filename

    def write_to_CSV(self, *args):
        dir_d1_w_files, empty_dirs_d1, dirs_at_d2, exts_files = args
        filename = Path(self.output).parent.joinpath("errorlog.csv")

        with open(filename, 'w') as file:
            writer = csv.writer(file)
            writer.writerow(["SN", "Name", "Contribution"])
            writer.writerow(["CHECK 1 -> Files at depth 1"])
            writer.writerow(dir_d1_w_files)
            writer.writerow(["CHECK 2 -> Empty dirs at depth 1"])
            writer.writerow(empty_dirs_d1)
            writer.writerow(["CHECK 3 -> Dirs at depth 2"])
            writer.writerow(dirs_at_d2)
            writer.writerow(["CHECK 4 -> Unwanted file extensions"])
            writer.writerow(exts_files)

        return filename

    def download_from_url(self, save_path=None, filename=None):
        if save_path is not None and filename is not None:
            self.download_complete_path = save_path
            self.download_file_name = filename
        elif save_path is None and filename is not None:
            self.download_file_name = filename
            self.download_complete_path = Path.joinpath(
                self.download_save_path, filename)
        elif save_path is not None and filename is None:
            self.download_save_path = save_path
            self.download_file_type = self.inputvar.split(".")[-1]
            self.download_file_name = "download." + self.download_file_type
            self.download_complete_path = Path(
                self.download_save_path).joinpath(self.download_file_name)
        else:
            self.download_file_type = self.inputvar.split(".")[-1]
            s = str(self.download_complete_path)
            s = s.rstrip("xyz")
            self.download_complete_path = s + self.download_file_type

        with urllib.request.urlopen(self.inputvar) as response, open(
                self.download_complete_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    def _zip(self, base_name='download',
             output_format='zip', root_dir=Path.cwd()):
        shutil.make_archive(base_name=base_name,
                            format=output_format, root_dir=root_dir)
        self.run_loader = False

    def zip(self, base_name='download',
            output_format='zip', root_dir=Path.cwd()):
        start = time.time()
        self.run_loader = True

        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=2) as e:
                e.submit(self.loader, "zipping")
                e.submit(self._zip, base_name, output_format, root_dir)
            print("\n", f"Zipping this took -> ",
                  (time.time())-start, f" seconds")
        except Exception:
            print(f"Looks like you aren't using __name__ in your script")
            print(f"Switching to old method of zipping.")
            print(f"Started zipping...")
            self._zip(base_name, output_format, root_dir)
            print(f"finished zipping successfully!")

    def _unzip(self, filename=None, extract_dir=Path.cwd()):
        shutil.unpack_archive(filename=filename, extract_dir=extract_dir)
        self.run_loader = False

    def unzip(self, filename=None, extract_dir=Path.cwd()):
        start = time.time()
        self.run_loader = True

        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=2) as e:
                e.submit(self.loader, "unzipping")
                e.submit(self._unzip, filename, extract_dir)
            print("\n", f"Unzipping this took -> ",
                  (time.time())-start, f" seconds")
        except Exception as err:
            print(f"Looks like you aren't using __name__ in your script")
            print(f"Switching to old method of zipping.")
            print(f"Started unzipping...")
            self._unzip(filename, extract_dir)
            print(f"finished zipping successfully!")

    def loader(self, message):
        loaderanimation = [f'|', f'/', f'-', '\\']
        i = 0
        while self.run_loader is True:
            print("\r\b", f"{message} : ",
                  loaderanimation[i], end=f'  ', flush=True)
            i += 1
            if i >= 4:
                i = 0
        print("\r\b", f"{message} : ", f"DONE", end=f'  ', flush=True)

    def progbar(self, curr, total, message=""):
        frac = curr/total
        filled_progbar = round(frac*100)
        print('\r\b', f"{message} : ",
              f'#'*filled_progbar + f'-'*(100 - filled_progbar),
              f"""[{frac:>7.2%}] [{curr}/{total}]""", end='', flush=True)

    def ratio(self, output="output", seed=69,
              ratio=(0.8, 0.1, 0.1), create_mode='copy'):

        assert round(sum(ratio), 10) == 1, f"Sum of Ratio must be 1."
        assert len(ratio) in (2, 3), f"Invalid split ratio tuple dimension"
        assert create_mode in ('copy', 'move'), f"Invalid create mode"

        self.split_ratio = ratio
        self.seed = seed
        self.output = output
        self.create_mode = create_mode

        for class_dir in self.list_dirs(self.inputvar):
            self.split_class_dir_ratio(class_dir)

        return self.output

    def fixed(self, output="output", seed=69,
              fixed=(100, 100), create_mode='copy'):

        assert len(fixed) in (1, 2), f"Invalid fixed split tuple dimension"
        assert create_mode in ('copy', 'move'), f"Invalid create mode"

        self.split_fixed = fixed
        self.seed = seed
        self.output = output
        self.create_mode = create_mode

        dirs = self.list_dirs(self.inputvar)
        lens = []
        for class_dir in dirs:
            lens.append(
                self.split_class_dir_fixed(
                    class_dir,
                    self.output,
                    self.split_fixed,
                    self.seed,
                )
            )

        return self.output

    def group_by_exts(self, output="output", exts=['jpg', 'pdf'],
                      seed=69, create_mode='copy'):

        assert isinstance(
            exts, list), f"All extensions must be passed in a list"
        assert create_mode in ('copy', 'move'), f"Invalid create mode"
        assert self.inputvar not in ('', None), f"Invalid input dir."

        self.seed = seed
        self.create_mode = create_mode
        self.output = Path.joinpath(Path(self.inputvar).parent, output)

        exts = list(set(exts))
        len_exts = len(exts)
        list_by_exts = []
        files = self.setup_files(self.inputvar)

        for i, i_exts in enumerate(exts):
            temp = [f for f in files if str(f).split(".")[-1] == i_exts]
            if len(temp) == 0:
                print(f"No match found for {i_exts}")
                continue
            else:
                print(f"Matches found for {i_exts}")
            list_by_exts.append([temp, f"group_by_{i_exts}"])
            self.progbar(i+1, len_exts, f"grouping by {exts}")

        print("\n")

        if len(list_by_exts) == 0:
            print(f"No file matches by all extensions.")
            return None

        if create_mode == 'copy':
            self.copy_files(list_by_exts, None, False)
        else:
            self.move_files(list_by_exts, None, False)

        return self.output

    def rglob(self, regex=r'*', output="output",
              recursive=True, create_mode='copy'):

        assert recursive in (
            True, False), f"recursive can only be True or False"
        assert create_mode in ('copy', 'move'), f"Invalid create mode"

        self.output = Path.joinpath(Path(self.inputvar).parent, output)
        files = []
        if recursive is True:
            files = files.append(
                ["group_by_rglob", list(Path(self.inputvar).rglob(regex))])
        else:
            files = files.append(
                ["group_by_glob", list(Path(self.inputvar).glob(regex))])

        if len(files) == 0:
            print("No file matches found.")
            return None

        if create_mode == 'copy':
            self.copy_files(files, None, False)
        else:
            self.move_files(files, None, False)

        return self.output

    def setup_files(self, class_dir):
        random.seed(self.seed)
        files = self.list_files(class_dir)
        files.sort()
        random.shuffle(files)
        return files

    def split_class_dir_ratio(self, class_dir):
        files = self.setup_files(class_dir, self.seed)

        self.split_train_idx = int(self.ratio[0] * len(files))
        self.split_val_idx = self.split_train_idx + \
            int(self.ratio[1] * len(files))
        self.use_test = len(self.ratio) == 3

        li = self.split_files(files)
        if self.create_mode == 'copy':
            self.copy_files(li, class_dir)
        else:
            self.move_files(li, class_dir)

    def split_class_dir_fixed(self, class_dir):
        files = self.setup_files(class_dir, self.seed)

        assert len(files) < sum(
            self.split_fixed), f"No of files>split fixed passed. Invalid input"

        self.split_train_idx = len(files) - sum(self.split_fixed)
        self.split_val_idx = self.split_train_idx + self.split_fixed[0]
        self.use_test = len(self.split_fixed) == 2

        li = self.split_files(files)
        if self.create_mode == 'copy':
            self.copy_files(li, class_dir)
        else:
            self.move_files(li, class_dir)
        return len(files)

    def split_files(self, files):
        files_train = files[:self.split_train_idx]
        files_val = (files[self.split_train_idx:self.split_val_idx]
                     if self.use_test else files[self.split_train_idx:])

        li = [[files_train, "train"], [files_val, "val"]]

        if self.use_test:
            files_test = files[self.split_val_idx:]
            li.append([files_test, "test"])
        return li

    def copy_files(self, files_type, class_dir=None, create_class_name=True):

        assert len(files_type) > 0, f"No files found to be copied."
        assert create_class_name in (
            True, False, None), f"Create class name can be True, False or None"

        class_name = None
        if create_class_name is True:
            class_name = path.split(class_dir)[1]
        for files, folder_type in files_type:
            full_path = None
            if create_class_name is True:
                full_path = Path(self.output).joinpath(folder_type, class_name)
            elif create_class_name is False:
                full_path = Path(self.output).joinpath(folder_type)
            else:
                full_path = Path(self.output)
            curr_file_len = len(files)
            Path(full_path).mkdir(parents=True, exist_ok=True)
            for i, f in enumerate(files):
                try:
                    if type(f) == list:
                        for x in f:
                            if Path(x).is_file():
                                shutil.copy2(x, full_path)
                            elif Path(x).is_dir():
                                c_path = Path(full_path).joinpath(f.name)
                                shutil.copytree(x, c_path, symlinks=True)
                    else:
                        if Path(f).is_file():
                            shutil.copy2(f, full_path)
                        elif Path(f).is_dir():
                            c_path = Path(full_path).joinpath(f.name)
                            shutil.copytree(f, c_path, symlinks=True)
                except Exception as e:
                    print(e)
                else:
                    self.progbar(i+1, curr_file_len,
                                 f"Copying into {folder_type}")
            print("\n")

    def move_files(self, files_type,  class_dir=None, create_class_name=True):

        assert len(files_type) > 0, f"No files found to be moved."
        assert create_class_name in (
            True, False, None), f"Create class name can be True, False or None"

        class_name = None
        if create_class_name is True:
            class_name = path.split(class_dir)[1]
        for files, folder_type in files_type:
            full_path = None
            if create_class_name is True:
                full_path = Path(self.output).joinpath(folder_type, class_name)
            elif create_class_name is False:
                full_path = Path(self.output).joinpath(folder_type)
            else:
                full_path = Path(self.output)
            curr_file_len = len(files)
            Path(full_path).mkdir(parents=True, exist_ok=True)
            for i, f in enumerate(files):
                try:
                    if type(f) == list:
                        for x in f:
                            shutil.move(x, full_path)
                    else:
                        shutil.move(f, full_path)
                except Exception as e:
                    print(e)
                else:
                    self.progbar(i+1, curr_file_len,
                                 f"Moving into {folder_type}")
            print("\n")

    def send_to_server(self, separator=f"<SEPARATOR>", buffer_size=4096,
                       host=f"192.168.1.109", port=5000, delay=5):

        assert buffer_size > 0, f"buffer size can't be negative."
        assert delay >= 0, f"delay can't be negative."
        assert separator not in ('', None), f"separator can't be None or empty"
        assert Path(self.inputvar).is_file(), f"Input path must be a file"
        assert port >= 0, f"port can't be negative"
        assert re.match(r"([0-9]{1,3}\.){3}[0-9]{1,3}", host), f"""
        host address is invalid.
        It must be of format - xxx.xxx.xxx.xxx where x = digit"""

        for i in range(delay, -1, -1):
            print("\r\b", f"Connecting to server in {i} seconds",
                  end='', flush=True)

        s = socket.socket()
        print(f"[+] Connecting to {host}:{port}")

        try:
            s.connect((host, port))
        except Exception:
            print("Invalid host and port address")
            return False

        print(f"[+] Connected to ", host)
        filesize = round((Path(self.inputvar).stat().st_size)/(1024*1024), 8)
        print(f"Sending {Path(self.inputvar).stem} with size {filesize} MB")
        s.send(f"{Path(self.inputvar).stem}{separator}{filesize}".encode())

        with open(self.inputvar, "rb") as f:
            while True:
                bytes_read = f.read(buffer_size)
                if not bytes_read:
                    break
                s.sendall(bytes_read)
                self.progbar(round(bytes_read/(1024*1024), 8),
                             filesize, "Uploading")
        s.close()

        return True
