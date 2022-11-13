import pkgutil
from pathlib import Path
from argparse import Namespace
import sys
import pyimg4

from . import logger
from . import utils
from .logger import colors


class IMG4:
    def __init__(self, args: Namespace, in_package: bool, shsh: Path, data_dir: Path, tmp: Path) -> None:
        self.in_package = in_package
        self.args = args
        
        self.shsh = shsh
        
        # Directories
        self.data_dir = data_dir
        self.tmp = tmp
        
    def im4p_to_img4(self, input: Path, output: Path, tag: str) -> None:
        print(f"Creating {output.split('/')[-1]} from {input.split('/')[-1]}")
        with open(self.shsh, 'rb') as f:
            shsh = plistlib.load(f)
        im4m = pyimg4.IM4M(shsh['ApImg4Ticket'])
        
        with open(input, 'rb') as f:
            im4p = pyimg4.IM4P(f.read())
        
        new_im4p = pyimg4.IM4P(payload=im4p, fourcc=tag)
        img4 = pyimg4.IMG4(im4p=new_im4p, im4m=im4m)
        
        with open(self.output, 'wb') as f:
            f.write(img4.payload.output().data)
    
    def im4p_to_raw(self, input: Path, output: Path) -> None:
        print(f"Creating {output.split('/')[-1]} from {input.split('/')[-1]}")
        with open(input, 'rb') as f:
            im4p = pyimg4.IM4P(f.read())
        
        with open(self.output, 'wb') as f:
            f.write(im4p.payload.output().data)
