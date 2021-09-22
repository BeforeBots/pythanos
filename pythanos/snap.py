from pathlib import Path
import random
import shutil
from typing import List
import re
import urllib.request
import concurrent.futures
import time
from os import path


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
        self.output = f"output"
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(self.loader, "zipping")
            executor.submit(self._zip, base_name, output_format, root_dir)
        print("\n", f"Zipping this took -> ", (time.time())-start, f" seconds")

    def _unzip(self, filename=None, extract_dir=Path.cwd()):
        shutil.unpack_archive(filename=filename, extract_dir=extract_dir)
        self.run_loader = False

    def unzip(self, filename=None, extract_dir=Path.cwd()):
        start = time.time()
        self.run_loader = True
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            executor.submit(self.loader, "unzipping")
            executor.submit(self._zip, filename, extract_dir)
        print("\n", f"Unzipping this took -> ",
              (time.time())-start, f" seconds")

    def loader(self, message):
        loaderanimation = [f'|', f'/', f'-', '\\']
        i = 0
        while self.run_loader is True:
            print("\r", f"{message} : ",
                  loaderanimation[i], end=f'  ', flush=True)
            i += 1
            if i >= 4:
                i = 0
        print("\r", f"{message} : ", f"DONE", end=f'  ', flush=True)

    def progbar(self, curr, total, message=""):
        frac = curr/total
        filled_progbar = round(frac*100)
        print('\r', f"{message} : ",
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
            list_by_exts.append([temp, f"group_by_{i_exts}"])
            self.progbar(i+1, len_exts, f"grouping by {exts}")
        print("\n")
        if create_mode == 'copy':
            self.copy_files(list_by_exts, None, False)
        else:
            self.move_files(list_by_exts, None, False)

        return self.output

    def rglob(self, regex=r'*', output="output",
              recursive=True, create_mode='copy'):
        self.output = Path.joinpath(Path(self.inputvar).parent, output)
        files = []
        if recursive is True:
            files = files.append(
                ["group_by_rglob", list(Path(self.inputvar).rglob(regex))])
        else:
            files = files.append(
                ["group_by_glob", list(Path(self.inputvar).glob(regex))])

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
        class_name = None
        if create_class_name is True:
            class_name = path.split(class_dir)[1]
        for files, folder_type in files_type:
            full_path = None
            if create_class_name is True:
                full_path = path.join(self.output, folder_type, class_name)
            else:
                full_path = path.join(self.output, folder_type)
            curr_file_len = len(files)
            Path(full_path).mkdir(parents=True, exist_ok=True)
            for i, f in enumerate(files):
                self.progbar(i+1, curr_file_len, f"Copying into {folder_type}")
                if type(f) == list:
                    for x in f:
                        shutil.copy2(x, full_path)
                else:
                    shutil.copy2(f, full_path)
            print("\n")

    def move_files(self, files_type,  class_dir=None, create_class_name=True):
        class_name = None
        if create_class_name is True:
            class_name = path.split(class_dir)[1]
        for files, folder_type in files_type:
            full_path = None
            if create_class_name is True:
                full_path = path.join(self.output, folder_type, class_name)
            else:
                full_path = path.join(self.output, folder_type)
            curr_file_len = len(files)
            Path(full_path).mkdir(parents=True, exist_ok=True)
            for i, f in enumerate(files):
                self.progbar(i+1, curr_file_len, f"Moving into {folder_type}")
                if type(f) == list:
                    for x in f:
                        shutil.move(x, full_path)
                else:
                    shutil.move(f, full_path)
            print("\n")
