from nbodykit.io.stack import FileStack
from nbodykit.base.particlemesh import ParticleMeshSource
from nbodykit.utils import cosmology_to_dict
from nbodykit import CurrentMPIComm

import numpy

class ZeldovichParticles(ParticleMeshSource):
    """
    A source of particles Poisson-sampled from density fields in the Zel'dovich approximation
    """
    @CurrentMPIComm.enable
    def __init__(self, cosmo, nbar, redshift, BoxSize, Nmesh, bias=2., rsd=None, seed=None, comm=None):
        """
        Parameters
        ----------
        cosmo : subclass of astropy.cosmology.FLRW
           the cosmology used to generate the linear power spectrum (using CLASS) 
        nbar : float
            the number density of the particles in the box, assumed constant across the box; 
            this is used when Poisson sampling the density field
        redshift : float
            the redshift of the linear power spectrum to generate
        BoxSize : float, 3-vector of floats
            the size of the box to generate the grid on
        Nmesh : int
            the mesh size to use when generating the density and displacement fields, which
            are Poisson-sampled to particles
        bias : float, optional
            the desired bias of the particles; applied while applying a log-normal transformation
            to the density field
        rsd : array_like, optional
            apply redshift space-distortions in this direction; if None, no rsd is applied.
        seed : int, optional
            the global random seed, used to set the seeds across all ranks
        comm : MPI communicator
            the MPI communicator
        """
        # communicator and cosmology
        self.comm    = comm
        self.cosmo   = cosmo

        if rsd is None:
            rsd = [0, 0, 0.]

        self.attrs.update(cosmology_to_dict(cosmo))

        # save the meta-data
        self.attrs['nbar']     = nbar
        self.attrs['redshift'] = redshift
        self.attrs['bias']     = bias
        self.attrs['rsd']      = rsd
        self.attrs['seed']     = seed

        ParticleMeshSource.__init__(self, BoxSize=BoxSize, Nmesh=Nmesh, dtype='f4', comm=comm)

        self._source = self._makesource()

        # recompute _csize to the real size
        self.update_csize()

    def get_column(self, col):
        """
        Return a column from the underlying file source
        
        Columns are returned as dask arrays
        """
        import dask.array as da
        return da.from_array(self._source[col], chunks=100000)

    @property
    def size(self):
        if not hasattr(self, "_source"):
            return NotImplemented
        return len(self._source)

    @property
    def hcolumns(self):
        """
        The union of the columns in the file and any transformed columns
        """
        return list(self._source.dtype.names)

    def _makesource(self):
        # classylss is required to call CLASS and create a power spectrum
        try: import classylss
        except: raise ImportError("`classylss` is required to use %s" %self.__class__.__name__)
    
        # the other imports
        from nbodykit import mockmaker
        from pmesh.pm import ParticleMesh
        from nbodykit.utils import MPINumpyRNGContext
    
        # initialize the CLASS parameters 
        pars = classylss.ClassParams.from_astropy(self.cosmo)

        try:
            cosmo = classylss.Cosmology(pars)
        except Exception as e:
            raise ValueError("error running CLASS for the specified cosmology: %s" %str(e))
    
        # initialize the linear power spectrum object
        Plin = classylss.power.LinearPS(cosmo, z=self.attrs['redshift'])
    
        # the particle mesh for gridding purposes
        pm = self.pm
    
        # generate initialize fields and Poisson sample with fixed local seed
        with MPINumpyRNGContext(self.attrs['seed'], self.comm):
    
            # compute the linear overdensity and displacement fields
            delta, disp = mockmaker.gaussian_real_fields(pm, Plin, compute_displacement=True)
    
            # sample to Poisson points
            f = cosmo.f_z(self.attrs['redshift']) # growth rate to do RSD in the Zel'dovich approx
            kws = {'f':f, 'bias':self.attrs['bias']}
            pos, vel = mockmaker.poisson_sample_to_points(delta, disp, pm, self.attrs['nbar'], **kws)
        
        pos += vel * self.attrs['rsd']

        dtype = numpy.dtype([
                ('Position', ('f4', 3)),
                ('Velocity', ('f4', 3)),
        ])

        source = numpy.empty(len(pos), dtype)
        source['Position'][:] = pos[:]
        source['Velocity'][:] = vel[:]
        return source
