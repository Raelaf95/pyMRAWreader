import numpy as np
import os


class pyMRAWreader:
    '''
    REQUIREMENTS
    https://numpy.org/ import numpy as np

    OBJ = pyMRAWreader(str:FOLDERNAME, bool,optional:BoolcheckBitOrder) constructs
    a multimedia reader object, OBJ, that can read in video data from a binary
    PHOTORN mraw file. FILENAME is a string specifying the name of the folder
    containing the mraw and cih/cihx files.
    If BoolcheckBitOrder = True constructor will run OBJ.__check_bitOrder__()


    pyMRAWreader methods:
    OBJ = pyMRAW_reader(r'X:\SpyroFolder\Filename_without_extension,  BoolcheckBitOrder:bool = False )

    pyMRAWreader methods:
    Image = OBJ.get_Image(Number) - Read a single image, number <<Number>>, from the video file.
                                    Returns a numpy 2D-array[OBJ.Height, OBJ.Width] with
                                    datatype int{OBJ.BitSize}
    OBJ.__check_bitOrder__()      - Assert bit order from CIH. Update if not consistent.


    pyMRAWreader public properties:
    OBJ.CIH_Dict    - Dict: with all readed info form CIH file
    OBJ.Height      - int: with Height readed form CIH file
    OBJ.Width       - int: with Width readed form CIH file
    OBJ.TotalFrames - int: with total number of images readed form CIH or CIHX file
    OBJ.FrameRate   - int: frames per second read from CIH file
    OBJ.BitSize     - int: Data type int-size of the MRAW file and the numpy OBJ.get_Image(Number)
    OBJ.BitOrder    - int: with bit order used to read MRAW file
    OBJ.bitShift    - int: bits shifted to read MRAW file. i.e. saved as 12 bit in  16 bit
    '''

    ####################################### CLASS CONSTRUCTOR #######################################
    def __init__(self, FolderName: str, BoolcheckBitOrder: bool = False):

        for filename in os.listdir(FolderName):
            ############################################################ find .chi
            if filename.lower().endswith('.cih'):
                self.cih_path = os.path.join(FolderName, filename)

                with open(self.cih_path, mode='rb') as file:  # b is important -> binary
                    CIH_fileContent = file.read()

                self.CIH_Dict = {}  ## Create a dict with all CHI info
                for line in CIH_fileContent.splitlines():
                    text = line.decode('utf-8').strip()
                    if ':' in text:
                        key, value = map(str.strip, text.split(':', 1))  # split only once
                        self.CIH_Dict[key] = value

                self.Height = int(self.CIH_Dict['Image Height'])
                self.Width = int(self.CIH_Dict['Image Width'])
                self.TotalFrames = int(self.CIH_Dict['Total Frame'])
                self.FrameRate = int(self.CIH_Dict['Record Rate(fps)'])

                self.BitOrder = self.CIH_Dict['EffectiveBit Side']
                self.BitSize = int(self.CIH_Dict['Color Bit'])
                self.bitShift = self.BitSize - int(self.CIH_Dict['EffectiveBit Depth'])

            ############################################################ find .chix
            elif filename.lower().endswith('.cihx'):
                self.cihx_path = os.path.join(FolderName, filename)

                with open(self.cihx_path, mode='rb') as file:  # b is important -> binary
                    CHIX_fileContent = file.read()

                start = CHIX_fileContent.find(b'cih')
                end = CHIX_fileContent.rfind(b'</cih>')
                CHIX_fileContent = CHIX_fileContent[start - 1:end + len(b'</cih>')].decode("utf-8", errors="ignore")

                self.CIHX_Dict = {}
                for line in CHIX_fileContent.splitlines():
                    text = line.strip()
                    key = text.split('<')[1].split('>')[0]
                    value = text.split('>')[1].split('<')[0]
                    self.CIHX_Dict[key] = value

                self.Height = int(self.CIHX_Dict['height'])
                self.Width = int(self.CIHX_Dict['width'])
                self.TotalFrames = int(self.CIHX_Dict['totalFrame'])
                self.FrameRate = int(self.CIHX_Dict['recordRate'])

                self.BitOrder = self.CIHX_Dict['side']
                self.BitSize = int(self.CIHX_Dict['bit'])
                self.bitShift = self.BitSize - int(self.CIHX_Dict['depth'])

            ############################################################ find .mraw
            elif filename.lower().endswith('.mraw'):
                self.mraw_path = os.path.join(FolderName, filename)

        if BoolcheckBitOrder:
            self.__check_bitOrder__()

    ########################################## CLASS METHODS ##########################################
    def __check_bitOrder__(self):
        Image = self.load_frame(Number=0)
        all_divisible_and_positive = np.all(Image % self.BitSize == 0) and Image.min() >= 0
        self.BitOrder = (
            'Higher' if self.BitOrder == 'Lower' else 'Lower') if all_divisible_and_positive else self.BitOrder

    def get_Image(self, Number=0):

        if self.BitSize % 8 == 0:
            Frame = np.zeros(self.Width * self.Height, np.dtype('uint' + str(self.BitSize)))

            with open(self.mraw_path, mode='rb') as file:  # b is important -> binary
                file.seek(Number * (self.BitSize // 8) * self.Width * self.Height)
                for i in range(self.Width * self.Height):
                    byte = file.read(self.BitSize // 8)

                    if self.BitOrder == 'Higher':
                        Frame[i] = int.from_bytes(byte, byteorder='big', signed=False) << self.bitShift
                    elif self.BitOrder == 'Lower':
                        Frame[i] = int.from_bytes(byte, byteorder='little', signed=False) << self.bitShift
                    else:
                        self.BitOrder = 'Higher'
                        self.__check_bitOrder__()
                        print(f'Settign Bit Order automatically to {self.BitOrder}')

        elif self.BitSize == 12:  ### if I need to split 3 8bits bytes into 2 12 bit bytes
            Frame = np.zeros(self.Width * self.Height, np.dtype('uint16'))

            with open(self.mraw_path, mode='rb') as file:  # b is important -> binary
                file.seek(Number * self.Width * self.Height * 3 // 2)

                for i in range(0, self.Width * self.Height - 2, 2):

                    veinticuatrobits = file.read(3)
                    b0 = veinticuatrobits[0]
                    b1 = veinticuatrobits[1]
                    b2 = veinticuatrobits[2]

                    if self.BitOrder == 'Higher':
                        # Extract two 12-bit values (bigg-endian)
                        first = b0 | ((b1 & 0x0F) << 8)
                        second = ((b1 >> 4) | (b2 << 4))
                    elif self.BitOrder == 'Lower':
                        # Extract two 12-bit values (littel-endian)
                        first = (b0 << 4) | (b1 >> 4)  # First 12 bits
                        second = ((b1 & 0x0F) << 8) | b2  # Second 12 bits
                    else:
                        self.BitOrder = 'Higher'
                        self.__check_bitOrder__()
                        print(f'Settign Bit Order automatically to {self.BitOrder}')

                    Frame[i] = first  # int.from_bytes(first, byteorder='little', signed=False)
                    Frame[i + 1] = second  # int.from_bytes(second, byteorder='little', signed=False)
        else:
            return -1

        return Frame.reshape((self.Height, self.Width))