import unittest
import requests, io, pathlib, shutil, logging
import bfio
import numpy as np

TEST_IMAGES = {
    '1884807.ome.zarr': 'https://s3.embassy.ebi.ac.uk/idr/zarr/v0.1/1884807.zarr/',
    'Plate1-Blue-A-12-Scene-3-P3-F2-03.czi': 'https://downloads.openmicroscopy.org/images/Zeiss-CZI/idr0011/Plate1-Blue-A_TS-Stinger/Plate1-Blue-A-12-Scene-3-P3-F2-03.czi',
    '0.tif': 'https://osf.io/j6aer/download',
    'img_r001_c001.ome.tif': 'https://github.com/usnistgov/WIPP/raw/master/data/PyramidBuilding/inputCollection/img_r001_c001.ome.tif'
}
    
TEST_DIR = pathlib.Path(__file__).with_name('data')

def setUpModule():
    """ Download images for testing """
    TEST_DIR.mkdir(exist_ok=True)
    
    for file,url in TEST_IMAGES.items():
        print(f'setup - Downloading: {file}')
        
        if not file.endswith('.ome.zarr'):
            r = requests.get(url)
            
            with open(TEST_DIR.joinpath(file),'wb') as fw:
                
                fw.write(r.content)
        else:
            
            base_path = TEST_DIR.joinpath(file)
            base_path.mkdir()
            base_path.joinpath('0').mkdir()
            
            units = [
                '.zattrs',
                '.zgroup',
                '0/.zarray',
                '0/0.0.0.0.0',
                '0/0.1.0.0.0',
                '0/0.2.0.0.0',
            ]
            
            for u in units:
                
                with open(base_path.joinpath(u),'wb') as fw:
                    
                    fw.write(requests.get(url+u).content)
            
def tearDownModule():
    """ Remove test images """
    
    print('teardown - Removing test images...')
    shutil.rmtree(TEST_DIR)

class TestSimpleRead(unittest.TestCase):
    
    @classmethod
    def tearDownClass(self):
        """ Load the czi image, and save as a npy file for further testing. """
        
        with bfio.BioReader(TEST_DIR.joinpath('Plate1-Blue-A-12-Scene-3-P3-F2-03.czi')) as br:
            
            np.save(TEST_DIR.joinpath('4d_array.npy'),br[:])
        
    def test_java(self):
        """test_java - Fails if Java/JPype improperly configured """
        
        bfio.start()
                
    def test_read_czi(self):
        """test_read_czi
        
        This test will fail if JPype and Java are not installed or improperly
        configured.
        
        """
        
        with bfio.BioReader(TEST_DIR.joinpath('Plate1-Blue-A-12-Scene-3-P3-F2-03.czi')) as br:
            
            self.assertEqual(br._backend_name, 'java')
            
            I = br[:]
            
            np.save(TEST_DIR.joinpath('4d_array.npy'),br[:])
            
            self.assertEqual(I.shape[0],512)
            self.assertEqual(I.shape[1],672)
            self.assertEqual(I.shape[2],21)
            self.assertEqual(I.shape[3],3)
            self.assertEqual(I.shape[4],1)
            self.assertEqual(I.dtype,np.uint16)
            
    def test_read_tif_strip_auto(self):
        """test_read_tif_strip_auto - Read tiff saved in strips, should load java backend """
        with bfio.BioReader(TEST_DIR.joinpath('0.tif')) as br:
            
            self.assertEqual(br._backend_name, 'java')
            
            I = br[:]
            
    def test_read_zarr_auto(self):
        """test_read_zarr_auto - Read ome zarr, should load zarr backend """
        with bfio.BioReader(TEST_DIR.joinpath('1884807.ome.zarr')) as br:
            
            self.assertEqual(br._backend_name, 'zarr')
            
            I = br[:]
            
            print(I.shape)
            
    @unittest.expectedFailure
    def test_read_ome_tif_strip_auto(self):
        """test_read_ome_tif_strip_auto - Expected failure, should load python backend """
        with bfio.BioReader(TEST_DIR.joinpath('img_r001_c001.ome.tif')) as br:
            
            I = br[:]
            
    def test_read_tif_strip_java(self):
        """test_read_tif_strip_java - Read tiff using Java backend """
        with bfio.BioReader(TEST_DIR.joinpath('img_r001_c001.ome.tif'),backend='java') as br:
            
            self.assertEqual(br._backend_name,'java')
            
            I = br[:]
            
    @unittest.expectedFailure
    def test_read_tif_strip_python(self):
        """test_read_tif_strip_python - Expected failure, read tiff saved in strips """
        with bfio.BioReader(TEST_DIR.joinpath('img_r001_c001.ome.tif'),backend='python') as br:
            
            I = br[:]
            
""" Metadata tests to run on each backend """
def get_dims(reader):
    """ Get all dimension attributes """
    for dim in 'xyzct':
        print('image.{} = {}'.format(dim,getattr(reader,dim)))
    for dim in 'xyzct'.upper():
        print('image.{} = {}'.format(dim,getattr(reader,dim)))
    print('image.shape = {}'.format(reader.shape))
    
def get_pixel_size(reader):
    """ Get all pixel size attributes """
    for dim in 'xyz':
        attribute = 'physical_size_{}'.format(dim)
        print('image.physical_size_{} = {}'.format(dim,
                                                   getattr(reader,attribute)))
    for dim in 'xyz':
        attribute = 'ps_{}'.format(dim)
        print('image.ps_{} = {}'.format(dim,
                                        getattr(reader,attribute)))
        
def get_pixel_info(reader):
    """ Get pixel information (type, samples per pixel, etc) """
    print('image.samples_per_pixel={}'.format(reader.samples_per_pixel))
    print('image.spp={}'.format(reader.spp))
    print('image.bytes_per_pixel={}'.format(reader.bytes_per_pixel))
    print('image.bpp={}'.format(reader.bpp))
    print('image.dtype={}'.format(reader.dtype))
    
def get_channel_names(reader):
    """ Get channel names attribute """
    print('image.channel_names={}'.format(reader.channel_names))
    print('image.cnames={}'.format(reader.cnames))

""" Test classes (where the testing actually happens) """
class TestVersion(unittest.TestCase):
    
    def test_bfio_version(self):
        """ Ensure bfio version is properly loaded """
        print('__version__ = {}'.format(bfio.__version__))
        assert bfio.__version__ != '0.0.0'
        
    def test_jar_version(self):
        """ Load loci-tools.jar and get version """
        print('JAR_VERSION = {}'.format(bfio.JAR_VERSION))
        assert bfio.__version__ != None
        
class TestJavaReader(unittest.TestCase):
    
    def test_get_dims(self):
        """ Testing metadata dimension attributes """
        with bfio.BioReader(TEST_DIR.joinpath('0.tif')) as br:
            get_dims(br)
        
    def test_get_pixel_size(self):
        """ Testing metadata pixel sizes """
        with bfio.BioReader(TEST_DIR.joinpath('0.tif')) as br:
            get_pixel_size(br)
        
    def test_get_pixel_info(self):
        """ Testing metadata pixel information """
        with bfio.BioReader(TEST_DIR.joinpath('0.tif')) as br:
            get_pixel_info(br)
        
    def test_get_channel_names(self):
        """ Testing metadata channel names """
        with bfio.BioReader(TEST_DIR.joinpath('0.tif')) as br:
            get_channel_names(br)

class TestZarrReader(unittest.TestCase):
    
    def test_get_dims(self):
        """ Testing metadata dimension attributes """
        with bfio.BioReader(TEST_DIR.joinpath('1884807.ome.zarr')) as br:
            get_dims(br)
        
    def test_get_pixel_size(self):
        """ Testing metadata pixel sizes """
        with bfio.BioReader(TEST_DIR.joinpath('1884807.ome.zarr')) as br:
            get_pixel_size(br)
        
    def test_get_pixel_info(self):
        """ Testing metadata pixel information """
        with bfio.BioReader(TEST_DIR.joinpath('1884807.ome.zarr')) as br:
            get_pixel_info(br)
        
    def test_get_channel_names(self):
        """ Testing metadata channel names """
        with bfio.BioReader(TEST_DIR.joinpath('1884807.ome.zarr')) as br:
            get_channel_names(br)