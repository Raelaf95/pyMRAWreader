from pyMRAWreader import pyMRAWreader
import matplotlib.pyplot as plt

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    Reader = pyMRAWreader(r'X:\SpyroFolder\CIHandMRAWfolderName')
    plt.figure()
    ax = plt.subplot()
    #plt.ion()
    for i in range(Reader.TotalFrames):
        ax.imshow(Reader.get_Image(Number=i), cmap='gray')
        plt.draw()
        plt.pause(1/60)

        #plt.ioff() # due to infinite loop, this gets never called.