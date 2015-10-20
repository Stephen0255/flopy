import os
import numpy as np
from flopy.utils import util_2d, util_3d, transient_2d,mflist

from . import NetCdf


NC_UNITS_FORMAT = {"hk":"{0}/{1}","sy":"","ss":"1/{0}","rech":"{0}/{1}","strt":"{0}",
                   "wel_flux":"{0}^3/{1}","top":"{0}","botm":"{0}","thickness":"{0}",
                   "ghb_cond":"{0}/{1}^2","ghb_bhead":"{0}","transmissivity":"{0}^2/{1}",
                   "vertical_conductance":"{0}/{1}^2","primary_storage_coefficient":"1/{1}",
                   "horizontal_hydraulic_conductivity":"{0}/{1}","riv_cond":"1/{1}",
                   "riv_stage":"{0}"}
NC_PRECISION_TYPE = {np.float32:"f4",np.int:"i4"}


def datafile_helper(f,df):
    raise NotImplementedError()


def mflist_helper(f,mfl):
    assert isinstance(mfl,mflist)\
                      ,"mflist_helper only helps mflist instances"

    if isinstance(f,str) and f.lower().endswith(".nc"):
        f = NetCdf(f,mfl.model)

    if isinstance(f,NetCdf):
        base_name = mfl.package.name[0].lower()
        f.log("getting 4D masked arrays for {0}".format(base_name))
        m4d = mfl.masked_4D_arrays
        f.log("getting 4D masked arrays for {0}".format(base_name))

        for name,array in m4d.items():
            var_name = base_name + '_' + name
            units = None
            if var_name in NC_UNITS_FORMAT:
                units = NC_UNITS_FORMAT[var_name].format(f.grid_units,f.time_units)
            precision_str = NC_PRECISION_TYPE[mfl.dtype[name].type]
            attribs = {"long_name":"flopy.mflist instance of {0}".format(var_name)}
            if units is not None:
                attribs["units"] = units
            try:
                var = f.create_variable(var_name,attribs,precision_str=precision_str,
                                        dimensions=("time","layer","y","x"))
            except Exception as e:
                estr = "error creating variable {0}:\n{1}".format(var_name,str(e))
                f.logger.warn(estr)
                raise Exception(estr)
            try:
                var[:] = array
            except Exception as e:
                estr = "error setting array to variable {0}:\n{1}".format(var_name,str(e))
                f.logger.warn(estr)
                raise Exception(estr)
        return f
    else:
        raise NotImplementedError("transient2d_helper only for netcdf (*.nc) ")


def transient2d_helper(f,t2d,min_valid=-1.0e+9, max_valid=1.0e+9):
    assert isinstance(t2d,transient_2d)\
                      ,"transient2d_helper only helps transient_2d instances"

    if isinstance(f,str) and f.lower().endswith(".nc"):
        f = NetCdf(f,t2d.model)

    if isinstance(f,NetCdf):
        # mask the array - assume layer 1 ibound is a good mask
        f.log("getting 4D array for {0}".format(t2d.name_base))
        array = t2d.array
        f.log("getting 4D array for {0}".format(t2d.name_base))

        if t2d.model.bas6 is not None:
            array[:,t2d.model.bas6.ibound.array[0] == 0] = f.fillvalue
        array[array<=min_valid] = f.fillvalue
        array[array>=max_valid] = f.fillvalue

        units = None
        var_name = t2d.name_base.replace('_','')
        if var_name in NC_UNITS_FORMAT:
            units = NC_UNITS_FORMAT[var_name].format(f.grid_units,f.time_units)
        precision_str = NC_PRECISION_TYPE[t2d.dtype]
        attribs = {"long_name":"flopy.transient_2d instance of {0}".format(var_name)}
        if units is not None:
            attribs["units"] = units
        try:
            var = f.create_variable(var_name,attribs,precision_str=precision_str,
                                    dimensions=("time","layer","y","x"))
        except Exception as e:
                estr = "error creating variable {0}:\n{1}".format(var_name,str(e))
                f.logger.warn(estr)
                raise Exception(estr)
        try:
            var[:] = array
        except Exception as e:
            estr = "error setting array to variable {0}:\n{1}".format(var_name,str(e))
            f.logger.warn(estr)
            raise Exception(estr)
        return f

    else:
        raise NotImplementedError("transient2d_helper only for netcdf (*.nc) ")


def util3d_helper(f,u3d,min_valid=-1.0e+9, max_valid=1.0e+9):
    assert isinstance(u3d,util_3d),"util3d_helper only helps util_3d instances"
    assert len(u3d.shape) == 3,"util3d_helper only supports 3D arrays"

    if isinstance(f,str) and f.lower().endswith(".nc"):
        f = NetCdf(f,u3d.model)

    if isinstance(f,NetCdf):
        var_name = u3d.name[0].replace(' ','_').lower()
        f.log("getting 3D array for {0}".format(var_name))
        array = u3d.array
        # this is for the crappy vcont in bcf6
        if array.shape != f.shape:
            f.log("broadcasting 3D array for {0}".format(var_name))
            full_array = np.empty(f.shape)
            full_array[:] = np.NaN
            full_array[:array.shape[0]] = array
            array = full_array
            f.log("broadcasting 3D array for {0}".format(var_name))
        f.log("getting 3D array for {0}".format(var_name))

        if u3d.model.bas6 is not None:
            array[u3d.model.bas6.ibound.array == 0] = f.fillvalue
        array[array<=min_valid] = f.fillvalue
        array[array>=max_valid] = f.fillvalue

        units = None

        if var_name in NC_UNITS_FORMAT:
            units = NC_UNITS_FORMAT[var_name].format(f.grid_units,f.time_units)

        precision_str = NC_PRECISION_TYPE[u3d.dtype]

        attribs = {"long_name":"flopy.util_3d instance of {0}".format(var_name)}
        if units is not None:
            attribs["units"] = units
        try:
            var = f.create_variable(var_name,attribs,precision_str=precision_str,
                                    dimensions=("layer","y","x"))
        except Exception as e:
            estr = "error creating variable {0}:\n{1}".format(var_name,str(e))
            f.logger.warn(estr)
            raise Exception(estr)
        try:
            var[:] = array
        except Exception as e:
            estr = "error setting array to variable {0}:\n{1}".format(var_name,str(e))
            f.logger.warn(estr)
            raise Exception(estr)
        return f

    else:
        raise NotImplementedError("util3d_helper only for netcdf (*.nc) ")


def util2d_helper(f,u2d,min_valid=-1.0e+9, max_valid=1.0e+9):

    assert isinstance(u2d,util_2d),"util2d_helper only helps util_2d instances"

    assert len(u2d.shape) == 2,"util2d_helper only supports 2D arrays"

    if isinstance(f,str) and f.lower().endswith(".nc"):
        f = NetCdf(f,u2d.model)

    if isinstance(f,NetCdf):


        # try to mask the array - assume layer 1 ibound is a good mask
        f.log("getting 2D array for {0}".format(u2d.name))
        array = u2d.array
        f.log("getting 2D array for {0}".format(u2d.name))

        if u2d.model.bas6 is not None:
            array[u2d.model.bas6.ibound.array[0,:,:] == 0] = f.fillvalue
        array[array<=min_valid] = f.fillvalue
        array[array>=max_valid] = f.fillvalue

        units = None
        var_name = u2d.name

        if var_name in NC_UNITS_FORMAT:
            units = NC_UNITS_FORMAT[var_name].format(f.grid_units,f.time_units)

        precision_str = NC_PRECISION_TYPE[u2d.dtype]

        attribs = {"long_name":"flopy.util_2d instance of {0}".format(var_name)}
        if units is not None:
            attribs["units"] = units
        try:
            var = f.create_variable(var_name,attribs,precision_str=precision_str,
                                    dimensions=("y","x"))
        except Exception as e:
            estr = "error creating variable {0}:\n{1}".format(var_name,str(e))
            f.logger.warn(estr)
            raise Exception(estr)
        try:
            var[:] = array
        except Exception as e:
            estr = "error setting array to variable {0}:\n{1}".format(var_name,str(e))
            f.logger.warn(estr)
            raise Exception(estr)
        return f

    else:
        raise NotImplementedError("util2d_helper only for netcdf (*.nc) ")