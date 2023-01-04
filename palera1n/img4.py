import plistlib
import pyimg4

from argparse import Namespace
from pathlib import Path


class IMG4:
    def __init__(self, args: Namespace, in_package: bool, shsh: Path, data_dir: Path, tmp: Path) -> None:
        self.in_package = in_package
        self.args = args
        
        self.shsh = shsh
        
        # Directories
        self.data_dir = data_dir
        self.tmp = tmp
        
    def im4p_to_img4(self, input_file: Path, output_file: Path, tag: str, compression: pyimg4.Compression = None) -> None:
        print(f"Creating {output_file.name.split('/')[-1]} from {input_file.name.split('/')[-1]}")
        with open(self.shsh, 'rb') as f:
            try:
                shsh = plistlib.load(f)
                im4m = pyimg4.IM4M(shsh['ApImg4Ticket'])
            except plistlib.InvalidFileException:
                im4m = pyimg4.IM4M(f.read())
        
        im4p = pyimg4.IM4P(payload=input_file.read_bytes(), fourcc=tag)
        if compression is not None:
            im4p.payload.compress(compression)
        
        img4 = pyimg4.IMG4(im4p=im4p, im4m=im4m)
        
        output_file.write_bytes(img4.output())
    
    def im4p_to_raw(self, input_file: Path, output_file: Path, compressed: bool = False) -> None:
        print(f"Creating {output_file.name.split('/')[-1]} from {input_file.name.split('/')[-1]}")
        
        payload = pyimg4.IM4P(input_file.read_bytes()).payload
        if compressed:
            payload.decompress()
        
        output_file.write_bytes(payload.output().data)
