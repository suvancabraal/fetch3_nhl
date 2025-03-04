from pathlib import Path
import cProfile
import pstats

try:
    from fetch3.__main__ import (setup_config, spatial_discretization, prepare_met_data,
                                 temporal_discretization, initial_conditions, Picard)
except ImportError:
    import os
    fetch_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    import sys
    sys.path.insert(0, fetch_dir)
    from fetch3.__main__ import (setup_config, spatial_discretization, prepare_met_data,
                                 temporal_discretization, initial_conditions, Picard)

p = (Path(__file__).parent / "output/cProfile_speed2.prof").resolve()
p.parent.mkdir(exist_ok=True, parents=True)


def profile():


    config_file = Path(__file__).resolve().parent.parent / 'config_files' / 'model_config.yml'
    data_dir= Path(__file__).resolve().parent.parent / 'data'
    output_dir = Path(__file__).resolve().parent.parent / 'output'



    with cProfile.Profile() as pr:

        cfg = setup_config(config_file)

        ##########Set up spatial discretization
        zind = spatial_discretization(
        cfg.dz, cfg.Soil_depth, cfg.Root_depth, cfg.Hspec, cfg.sand_d, cfg.clay_d)
        ######prepare met data
        met, tmax, start_time, end_time = prepare_met_data(cfg, data_dir, zind.z_upper)

        t_num, nt = temporal_discretization(cfg, tmax)

        ############## Calculate initial conditions #######################
        H_initial, Head_bottom_H = initial_conditions(cfg, met.q_rain, zind)

        Picard(cfg, H_initial, Head_bottom_H, zind, met, t_num, nt, output_dir, data_dir)



    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats(filename=p)

if __name__ == "__main__":
    profile()