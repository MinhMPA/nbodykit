from runtests.mpi import MPITest
from nbodykit.io.binary import BinaryFile
import os
import numpy
import tempfile
import pickle

@MPITest([1])
def test_data(comm):

    with tempfile.NamedTemporaryFile() as ff:    
        
        # generate data
        pos = numpy.random.random(size=(1024, 3))
        vel = numpy.random.random(size=(1024, 3))
        pos.tofile(ff); vel.tofile(ff); ff.seek(0)
        
        # read
        f = BinaryFile(ff.name, [('Position', ('f8', 3)), ('Velocity', ('f8', 3))], size=1024)
        
        assert f.size == len(f[:]), "mismatch between 'size' and length of data read"
        assert f.size == 1024, "wrong data size"
        
        numpy.testing.assert_almost_equal(pos, f['Position'][:])
        numpy.testing.assert_almost_equal(vel, f['Velocity'][:])

@MPITest([1])
def test_offsets(comm):

    with tempfile.NamedTemporaryFile() as ff:    
        
        # generate data
        pos = numpy.random.random(size=(1024, 3))
        vel = numpy.random.random(size=(1024, 3))
        pos.tofile(ff); vel.tofile(ff); ff.seek(0)
        
        # pass an offsets dictionary
        dtype = [('Position', ('f8', 3)), ('Velocity', ('f8', 3))]
        f = BinaryFile(ff.name, dtype, size=1024, offsets={'Position':0, 'Velocity':pos.nbytes})
        
        assert f.size == len(f[:]), "mismatch between 'size' and length of data read"
        assert f.size == 1024, "wrong data size"
        
        numpy.testing.assert_almost_equal(pos, f['Position'][:])
        numpy.testing.assert_almost_equal(vel, f['Velocity'][:])
        
        # wrong offsets dict
        try: f = BinaryFile(ff.name, dtype, size=1024, offsets={'Position':0})
        except: pass
        
        # must be a dict
        try: f = BinaryFile(ff.name, dtype, size=1024, offsets=[('Position',0)])
        except: pass

@MPITest([1])
def test_header(comm):

    with tempfile.NamedTemporaryFile() as ff:    
        
        # generate data
        pos = numpy.random.random(size=(1024, 3))
        vel = numpy.random.random(size=(1024, 3))
        hdr = numpy.arange(10); hdr.tofile(ff)
        pos.tofile(ff); vel.tofile(ff); ff.seek(0)
        
        # read
        dtype = [('Position', ('f8', 3)), ('Velocity', ('f8', 3))]
        f = BinaryFile(ff.name, dtype, size=1024, header_size=hdr.nbytes)
        
        assert f.size == len(f[:]), "error when header is non-zero"
        assert f.size == 1024,"error when header is non-zero"
        
        # test wrong header size
        try: f = BinaryFile(ff.name, dtype, header_size=hdr.nbytes-1)
        except ValueError: pass
        
@MPITest([1])
def test_infer_size(comm):

    with tempfile.NamedTemporaryFile() as ff:    
        
        # generate data
        pos = numpy.random.random(size=(1024, 3))
        vel = numpy.random.random(size=(1024, 3))
        hdr = numpy.arange(10); hdr.tofile(ff)
        pos.tofile(ff); vel.tofile(ff); ff.seek(0)
        
        # read
        dtype = [('Position', ('f8', 3)), ('Velocity', ('f8', 3))]
        f = BinaryFile(ff.name, dtype, header_size=hdr.nbytes)
        
        assert f.size == len(f[:]), "error when trying to infer size"
        assert f.size == 1024, "error when trying to infer size"

@MPITest([1])
def test_wrong_size(comm):

    with tempfile.NamedTemporaryFile() as ff:    
        
        # generate data
        pos = numpy.random.random(size=(1024, 3))
        vel = numpy.random.random(size=(1024, 3))
        hdr = numpy.arange(10); hdr.tofile(ff)
        pos.tofile(ff); vel.tofile(ff); ff.seek(0)
        
        # size must be an int
        dtype = [('Position', ('f8', 3)), ('Velocity', ('f8', 3))]
        try: f = BinaryFile(ff.name, dtype, header_size=hdr.nbytes, size=1024.0)
        except: pass

        
@MPITest([1])
def test_pickle(comm):

    with tempfile.NamedTemporaryFile() as ff:    
        
        # generate data
        pos = numpy.random.random(size=(1024, 3))
        vel = numpy.random.random(size=(1024, 3))
        pos.tofile(ff); vel.tofile(ff); ff.seek(0)
        
        # read
        f = BinaryFile(ff.name, [('Position', ('f8', 3)), ('Velocity', ('f8', 3))], size=1024)
        
        s = pickle.dumps(f)
        f2 = pickle.loads(s)
        
        numpy.testing.assert_almost_equal(f['Position'][:], f2['Position'][:])