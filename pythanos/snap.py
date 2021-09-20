from pathlib import Path
import random
import shutil
from typing import List
import re
import urllib.request


class Snap:

    def __init__(self, inputvar) -> None:
        self.inputvar = inputvar
        self.download_file_name = "download.xyz"
        self.download_file_type = self.download_file_name.split('.')[-1]
        self.download_complete_path = Path.joinpath(
            Path.cwd(), self.download_file_name)
        self.download_save_path = self.download_complete_path.parent

    def input_type(self) -> None:
        try:
            if Path(self.inputvar).is_file():
                print("File exist")
            elif Path(self.inputvar).is_dir():
                print("Dir exist")
            elif self.isValidURL():
                print("URL exist")
            else:
                raise TypeError
        except Exception as e:
            print("Input must be a valid Directory, File or a URL")

    def list_dirs(self, directory) -> List:
        return [f for f in Path(directory).iterdir() if f.is_dir()]

    def list_files(self, directory) -> List:
        return [
            f
            for f in Path(directory).iterdir()
            if f.is_file() and not f.name.startswith(".")
        ]

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

    def progbar(self, curr, total):
        frac = curr/total
        filled_progbar = round(frac*100)
        print('\r', '#'*filled_progbar + '-'*(100 - filled_progbar),
              f"""[{frac:>7.2%}]""", end='', flush=True)


# abcd = r"""http://i3.ytimg.com/vi/J---aiyznGQ/mqdefault.jpg"""
# Snap(abcd).download_from_url(
#     filename=r"abcd.jpg")

# x = Snap(abcd)

# for i in range(1066+1):
#     x.progbar(i, 1066)
# print()
