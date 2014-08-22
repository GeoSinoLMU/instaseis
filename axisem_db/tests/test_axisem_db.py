#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic integration tests for the AxiSEM database Python interface.

XXX: Right now the path to the database is hardcoded! It is too big to commit
it with the repository so something needs to be figured out. Best way is likely
to just generate a smaller database.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2014
:license:
    GNU General Public License, Version 3
    (http://www.gnu.org/copyleft/gpl.html)
"""
from __future__ import absolute_import

import numpy as np

from ..axisem_db import AxiSEMDB
from ..source import Source, Receiver


def test_basic_output():
    """
    Test against output directly from the axisem DB reader.
    """
    axisem_db = \
        AxiSEMDB("/Users/lion/workspace/code/axisem/SOLVER/prem50s_forces")
    receiver = Receiver(latitude=42.6390, longitude=74.4940)
    source = Source(
        latitude=89.91, longitude=0.0, depth_in_m=12000,
        m_rr=4.710000e+24 / 1E7,
        m_tt=3.810000e+22 / 1E7,
        m_pp=-4.740000e+24 / 1E7,
        m_rt=3.990000e+23 / 1E7,
        m_rp=-8.050000e+23 / 1E7,
        m_tp=-1.230000e+24 / 1E7)
    st = axisem_db.get_seismograms(source=source, receiver=receiver)

    n_data = np.array([
        -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0,
        -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -0.0, -7.183695E-44,
        6.201348E-42, 1.478579E-40, -6.104198E-39, -2.939338E-37,
        -4.945937E-37, 1.072107E-34, -3.041621E-34, -7.652161E-33,
        2.214094E-31, 5.601806E-31, 4.240771E-30, 1.006155E-28, -5.399007E-28,
        5.790040E-27, -3.010067E-26, -1.175898E-24, 5.809355E-24, 5.223013E-23,
        -1.453331E-21, -6.294746E-20, -7.540908E-17, -1.381345E-13,
        -3.265489E-11, -1.351891E-09, -3.024001E-09, 6.848123E-08,
        1.205207E-07, 4.819264E-08, 5.518334E-08, 6.583487E-08, 8.150570E-08,
        1.012352E-07, 1.055464E-07, 7.414001E-08, 1.679650E-07, 2.784896E-07,
        2.206829E-07, 1.936204E-07, 2.340856E-07, 1.803208E-07, 1.385476E-07,
        6.785513E-08, 2.899254E-08, 6.294315E-09, -4.599663E-09, -1.743001E-08,
        -2.595952E-08, -1.071743E-09, 4.191247E-08, 1.014835E-07, 1.581918E-07,
        1.939492E-07, 2.346080E-07, 2.382118E-07, 2.137073E-07, 1.263431E-07,
        -4.892889E-08, -4.451496E-07, -1.068539E-06, -5.157217E-07,
        1.545875E-06, 3.819888E-07, -3.938210E-07, 4.684740E-07, -8.194233E-08,
        2.149664E-07, 1.476712E-07, 3.730389E-08, 1.029422E-07, 1.638113E-07,
        1.232860E-07, 1.012607E-07, 4.174790E-08, 1.696431E-07, 6.332481E-08,
        3.907343E-08, -5.263358E-08, -1.933687E-07, -1.378726E-07,
        -1.598703E-07, -1.032468E-07, -1.117853E-07, -5.307041E-08,
        2.657340E-08, 4.544845E-08, -7.143105E-09, -4.218048E-08, 3.107075E-08,
        3.689852E-07, 7.780862E-07, -7.324227E-08, -2.608334E-06,
        -2.285997E-06, 2.627911E-06, 3.922536E-06, 1.285143E-06, 6.946971E-07,
        -3.389947E-07, -8.403630E-07, -8.852953E-07, -8.801109E-07,
        -6.610466E-07, -4.615913E-07, -2.545142E-07, -6.651063E-08,
        6.130591E-08, 1.723345E-07, 2.304882E-07, 2.374456E-07, 2.497180E-07,
        2.150196E-07, 1.797127E-07, 1.443892E-07, 9.477943E-08, 6.186546E-08,
        3.795263E-08, 3.080387E-09, -4.054393E-09, -7.624076E-09,
        -1.720859E-08, -1.281327E-08, -4.164188E-09])

    e_data = np.array([
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.293891E-47, -7.960512E-45,
        -2.565086E-43, 5.601668E-42, 4.295549E-40, 3.502265E-39, -1.165257E-37,
        7.360848E-37, 1.241967E-35, -3.867647E-34, -1.550451E-33,
        -1.101189E-32, -1.882064E-31, 5.724249E-31, -1.218819E-29,
        5.558247E-29, 2.215278E-27, -6.491563E-27, -7.265685E-26, 2.184427E-24,
        1.527340E-22, 1.292851E-19, 1.455002E-16, 1.573808E-14, -1.300657E-12,
        -6.491115E-11, -3.772020E-10, -2.314962E-10, 2.227033E-10,
        2.729536E-10, 3.371808E-10, 3.996143E-10, 4.723826E-10, 6.916227E-10,
        9.849159E-10, 7.909180E-10, 8.594033E-10, 1.449194E-09, 1.847096E-09,
        2.049652E-09, 2.548173E-09, 2.904327E-09, 3.285237E-09, 3.505557E-09,
        3.670030E-09, 3.784588E-09, 3.883007E-09, 3.954069E-09, 3.943480E-09,
        3.918640E-09, 3.905141E-09, 3.931181E-09, 3.941734E-09, 4.235156E-09,
        4.833539E-09, 5.249609E-09, 5.786588E-09, 7.008452E-09, 1.999126E-08,
        4.289288E-08, -3.948626E-08, -5.175802E-08, -6.303021E-09,
        -1.004425E-08, -1.086826E-08, -1.038698E-08, -1.236826E-08,
        -8.436007E-09, -9.135319E-09, -1.084253E-08, -1.371805E-08,
        -1.195116E-08, -6.421059E-09, 9.170287E-09, -4.782648E-09,
        -5.250811E-08, -7.165548E-08, -1.461580E-07, -6.605157E-09,
        4.166291E-08, 3.245431E-08, 2.099061E-08, 4.955582E-08, 2.117060E-07,
        2.456609E-07, 8.827656E-09, -2.283070E-07, -1.620225E-07, 1.429597E-07,
        9.832815E-08, -1.826465E-07, -2.503563E-08, 1.496816E-07,
        -1.141966E-07, -4.081054E-08, 1.044424E-07, -1.162238E-07,
        5.149226E-08, 2.711128E-08, -7.267841E-08, 9.276406E-08, -7.804038E-08,
        5.968422E-08, -3.444183E-08, 1.650617E-08, -4.767296E-09,
        -2.464382E-09, 2.897646E-09, -2.099779E-09, -3.040235E-09,
        6.521682E-09, -1.415001E-08, 1.690170E-08, -1.852017E-08, 1.421904E-08,
        -7.248936E-09, -1.370118E-09, 6.983255E-09, -6.786952E-09,
        1.663439E-09, 3.303061E-09, -2.143398E-09, -3.396735E-09])

    z_data = np.array([
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.701327E-43, 7.018565E-42,
        -1.867007E-41, -7.496780E-39, -1.377076E-37, 1.248486E-36,
        -2.883759E-35, 6.205079E-34, 1.978852E-32, -2.129065E-31,
        -5.367113E-31, 5.068524E-29, 2.159288E-29, -2.489202E-27, 3.563001E-26,
        8.907326E-27, -4.002944E-24, 2.437259E-23, 1.753412E-22, 9.076995E-22,
        -8.023611E-20, 1.481801E-16, 2.532032E-13, 5.664692E-11, 2.153508E-09,
        2.896353E-09, -9.692703E-08, -1.375223E-07, -4.452593E-08,
        -3.441410E-08, -3.240885E-08, -3.463395E-08, -3.048284E-08,
        -1.552783E-08, -2.143912E-09, -7.789044E-08, -1.225611E-07,
        -5.344417E-08, -1.552656E-08, -2.867482E-08, 3.098022E-08,
        6.903256E-08, 1.195810E-07, 1.325962E-07, 1.415300E-07, 1.397247E-07,
        1.458709E-07, 1.449791E-07, 1.400782E-07, 1.341358E-07, 1.263151E-07,
        1.192269E-07, 1.172090E-07, 1.234361E-07, 1.361837E-07, 1.781511E-07,
        2.061400E-07, 2.244271E-07, 1.255551E-07, -4.275674E-07, -1.012863E-06,
        -3.042036E-07, 6.211357E-07, 7.464105E-08, -1.699995E-08, 1.443275E-07,
        -6.581097E-08, 1.110329E-07, -8.471594E-08, -1.064905E-07,
        -7.198731E-08, 1.159495E-09, -6.098020E-08, -1.425050E-07,
        -1.512389E-07, -1.228428E-07, 8.630727E-09, 1.387881E-07,
        -3.145172E-07, -1.750447E-08, 3.632108E-08, -9.520157E-09,
        -4.721631E-08, 7.031441E-08, 1.651969E-07, 1.638390E-07, 1.815276E-07,
        2.245849E-07, 3.434750E-07, 3.638966E-07, -3.096832E-07, -1.614924E-06,
        -5.423943E-07, 3.997288E-06, 4.538764E-06, -6.278966E-07,
        -2.309359E-06, -2.144571E-06, -2.399276E-06, -1.322421E-06,
        -8.823042E-07, -1.236961E-07, 1.941729E-07, 5.294808E-07, 6.115453E-07,
        6.486833E-07, 5.787853E-07, 4.620343E-07, 3.511557E-07, 2.134995E-07,
        8.973106E-08, 2.319181E-09, -8.625759E-08, -1.262903E-07,
        -1.496944E-07, -1.672665E-07, -1.470819E-07, -1.256458E-07,
        -1.115759E-07, -6.885732E-08, -3.837220E-08, -2.082509E-08,
        6.581382E-09])

    np.testing.assert_allclose(st.select(component="Z")[0].data,
                               z_data, rtol=1E-4, atol=1E-15)
    np.testing.assert_allclose(st.select(component="N")[0].data,
                               n_data, rtol=1E-4, atol=1E-15)
    np.testing.assert_allclose(st.select(component="E")[0].data,
                               e_data, rtol=1E-4, atol=1E-15)