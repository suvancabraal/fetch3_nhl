"""
Functions for calculating sap storage and sap flux from the model outputs
"""

import numpy as np
import xarray as xr
from fetch3.scaling import integrate_trans2d

def format_inputs(nc_out, crown_area):
    H = nc_out["ds_all"].H

    #trans_2d [ m3H2O m-2crown_projection s-1 m-1stem]
    # 10**3 to convert m to kg
    # multiply by crown area to get transpiration in [m3 s-1 m-1stem]
    trans_2d_tree = nc_out["ds_canopy"].trans_2d * crown_area

    #Get aboveground z indexes to slice the H dataset
    zind_canopy = np.arange(len(nc_out['ds_all'].z) - len(nc_out['ds_canopy'].z),len(nc_out['ds_all'].z))

    H_above = H.isel(z=zind_canopy)

    return H_above, trans_2d_tree

def calc_sap_storage(H, cfg):
    """
    _summary_

    Parameters
    ----------
    H : xarray.dataarray
        Water potential [Pa]
    cfg : dataclass
        Model configuration parameters

    Returns
    -------
    storage: xarray.dataarray
        Sap storage [m3]
    """
    sapwood_area = cfg.sapwood_area # m2
    dz = cfg.dz
    Phi0x = cfg.Phi_0
    p = cfg.p

    #cfg.sat_xylem is in [m3 h2o/m3xylem]
    thetasat = cfg.sat_xylem
    taper_top = cfg.taper_top

    nz = len(H.z)

    taper = np.linspace(1, taper_top,nz)

    sapwood_area_z = sapwood_area * taper

    theta = thetasat * ((Phi0x / (Phi0x - H)) ** p) * sapwood_area_z

    storage = (theta.rolling(z=2).mean() * dz).sum(dim='z', skipna=True) # m3

    return storage

def calc_sapflux(H, trans_2d, cfg):
    """
    Calculates sapflux and total aboveground water storage of the tree.

    Parameters
    ----------
    H : _type_
        Water potential [Pa]
    trans_2d : datarray
        transpiration [m3 s-1 m-1stem]
    params : _type_
        _description_

    Returns
    -------
    sapflux : array-like
        Tree-level sap flux [m3 s-1]
    storage : array-like
        Total aboveground water storage [m3]

    """
    dt = cfg.dt
    dz = cfg.dz

    storage = calc_sap_storage(H, cfg)
    storage.name = 'storage'

    trans_tot = integrate_trans2d(trans_2d, dz)  #[m3 s-1]

    # Change in storage
    delta_S = storage.pad(time=(1,0)).diff(dim='time') / dt
    delta_S.name = 'delta_S'

    sapflux = trans_tot + delta_S
    sapflux.name = 'sapflux'

    ds_sapflux = xr.merge([sapflux, storage, delta_S])

    return ds_sapflux