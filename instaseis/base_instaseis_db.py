#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Abstract base class for all Instaseis database classes.

:copyright:
    Lion Krischer (krischer@geophysik.uni-muenchen.de), 2014
    Martin van Driel (Martin@vanDriel.de), 2014
:license:
    GNU Lesser General Public License, Version 3 [non-commercial/academic use]
    (http://www.gnu.org/copyleft/lgpl.html)
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from future.utils import with_metaclass

from abc import ABCMeta, abstractmethod
import numpy as np
from obspy.core import AttribDict, Stream, Trace, UTCDateTime
import warnings
from scipy.integrate import cumtrapz

from . import lanczos
from .source import Source, ForceSource, Receiver
from .helpers import get_band_code


DEFAULT_MU = 32e9


class BaseInstaseisDB(with_metaclass(ABCMeta)):
    """
    Base class for all Instaseis database classes defining the user interface.
    """
    def get_seismograms(self, source, receiver, components=("Z", "N", "E"),
                        kind='displacement', remove_source_shift=True,
                        reconvolve_stf=False, return_obspy_stream=True,
                        dt=None, a_lanczos=5):
        """
        Extract seismograms from the Green's function database.

        :param source: The source definition.
        :type source: :class:`instaseis.source.Source` or
            :class:`instaseis.source.ForceSource`
        :param receiver: The seismic receiver.
        :type receiver: :class:`instaseis.source.Receiver`
        :type components: tuple of str, optional
        :param components: Which components to calculate. Must be a tuple
            containing any combination of ``"Z"``, ``"N"``, ``"E"``,
            ``"R"``, and ``"T"``.
        :type kind: str, optional
        :param kind: The desired units of the seismogram:
            ``"displacement"``, ``"velocity"``, or ``"acceleration"``.
        :type remove_source_shift: bool, optional
        :param remove_source_shift: Move the start time of the seismogram to
            the peak of the sliprate from the source time function used to
            generate the database. This has the effect that the first sample
            is at the time of the origin time in the seismogram if available.
        :type reconvolve_stf: bool, optional
        :param reconvolve_stf: Deconvolve the source time function used in
            the AxiSEM run and convolve with the STF attached to the source.
            For this to be stable, the new STF needs to bandlimited.
        :type return_obspy_stream: bool, optional
        :param return_obspy_stream: Return format is either an
            :class:`obspy.core.stream.Stream` object or a dictionary
            containing the raw NumPy arrays.
        :type dt: float, optional
        :param dt: Desired sampling rate of the seismograms. Resampling is done
            using a Lanczos kernel.
        :type a_lanczos: int, optional
        :param a_lanczos: The width of the kernel used in the resampling.

        :returns: Multi component seismograms.
        :rtype: A :class:`obspy.core.stream.Stream` object or a dictionary
            with NumPy arrays as values.
        """
        source, receiver = self._get_seismograms_sanity_checks(
            source=source, receiver=receiver, components=components, kind=kind)

        # Call the _get_seismograms() method of the respective implementation.
        data = self._get_seismograms(source=source, receiver=receiver,
                                     components=components)

        if dt is None:
            dt_out = self.info.dt
        else:
            dt_out = dt

        kind_map = {
            'displacement': 0,
            'velocity': 1,
            'acceleration': 2}

        stf_map = {
            'errorf': 0,
            'quheavi': 0,
            'dirac_0': 1,
            'gauss_0': 1,
            'gauss_1': 2,
            'gauss_2': 3}

        stf_deconv_map = {
            0: self.info.sliprate,
            1: self.info.slip}

        n_derivative = kind_map[kind] - stf_map[self.info.stf]

        # not 100% sure why, but this way we get correct seismograms for
        # impacts when using ForceSource:
        if isinstance(source, ForceSource):
            n_derivative += 2

        if reconvolve_stf and remove_source_shift:
            raise ValueError("'remove_source_shift' argument not "
                             "compatible with 'reconvolve_stf'.")

        for comp in components:
            if reconvolve_stf:
                if source.dt is None or source.sliprate is None:
                    raise ValueError("source has no source time function")

                if stf_map[self.info.stf] not in [0, 1]:
                    raise NotImplementedError(
                        'deconvolution not implemented for stf %s'
                        % (self.info.stf))

                stf_deconv_f = np.fft.rfft(
                    stf_deconv_map[stf_map[self.info.stf]],
                    n=self.info.nfft)

                if abs((source.dt - self.info.dt) / self.info.dt) > 1e-7:
                    raise ValueError("dt of the source not compatible")

                stf_conv_f = np.fft.rfft(source.sliprate,
                                         n=self.info.nfft)

                if source.time_shift is not None:
                    stf_conv_f *= \
                        np.exp(- 1j * np.fft.rfftfreq(self.info.nfft) *
                               2. * np.pi * source.time_shift / self.info.dt)

                # XXX: double check whether a taper is needed at the end of the
                # trace
                dataf = np.fft.rfft(data[comp], n=self.info.nfft)

                data[comp] = np.fft.irfft(
                    dataf * stf_conv_f / stf_deconv_f)[:self.info.npts]

            if dt is not None:
                # This is a bit tricky. We want to resample but we also want
                # to make sure that that the peak of the source time
                # function is exactly hit by a sample point.

                # Number of sample intervals before the origin time in term
                # of the new dt.
                shift = round(self.info.src_shift % dt, 8)
                duration = (len(data[comp]) - 1) * self.info.dt - shift
                new_npts = int(round(duration / dt, 6)) + 1

                data[comp] = lanczos.lanczos_interpolation(
                    data=data[comp], old_start=0, old_dt=self.info.dt,
                    new_start=shift, new_dt=dt, new_npts=new_npts,
                    a=a_lanczos, window="blackman")
                time_shift = self.info.src_shift - shift
            else:
                time_shift = self.info.src_shift

            # Integrate/differentiate before removing the source shift in
            # order to reduce boundary effects at the start of the signal.
            for _ in np.arange(n_derivative):
                data[comp] = np.gradient(data[comp], [dt_out])

            for _ in np.arange(-n_derivative):
                # adding a zero at the beginning to avoid phase shift
                data[comp] = cumtrapz(data[comp], dx=dt_out, initial=0.0)

            # Remove the source shift at the very end to have as little
            # boundary effects as possible.
            if remove_source_shift:
                if dt is not None:
                    data[comp] = data[comp][round(int(time_shift / dt), 8):]
                else:
                    # If no resampling happens, removing the source shift is
                    # simple.
                    data[comp] = data[comp][self.info.src_shift_samples:]
                time_shift = 0
            elif reconvolve_stf:
                time_shift = 0

        if return_obspy_stream:
            return self._convert_to_stream(source=source, receiver=receiver,
                                           components=components,
                                           data=data, dt_out=dt_out,
                                           time_shift=time_shift)
        else:
            return data

    @staticmethod
    def _convert_to_stream(source, receiver, components, data, dt_out,
                           time_shift):
        if hasattr(source, "origin_time"):
            origin_time = source.origin_time
        else:
            origin_time = UTCDateTime(0)
        origin_time -= time_shift

        # Convert to an ObsPy Stream object.
        st = Stream()
        band_code = get_band_code(dt_out)
        instaseis_header = AttribDict(mu=data["mu"])
        for comp in components:
            tr = Trace(data=data[comp],
                       header={"delta": dt_out,
                               "starttime": origin_time,
                               "station": receiver.station,
                               "network": receiver.network,
                               "channel": "%sX%s" % (band_code, comp),
                               "instaseis": instaseis_header})
            st += tr
        return st

    @abstractmethod
    def _get_seismograms(self, source, receiver, components=("Z", "N", "E")):
        pass

    @abstractmethod
    def _get_info(self):
        """
        Must return a dictionary with the following keys:

        ``"is_reciprocal"``, ``"components"``, ``"source_depth"``,
        ``"velocity_model"``, ``"attenuation"``, ``"period"``,
        ``"dump_type"``, ``"excitation_type"``, ``"dt"``,
        ``"sampling_rate"``, ``"npts"``, ``"nnft"``, ``"length"``, ``"stf"``,
        ``"slip"``, ``"sliprate"``, ``"src_shift"``, ``"src_shift_samples"``,
        ``"spatial_order"``, ``"min_radius"``, ``"max_radius"``,
        ``"planet_radius"``, ``"min_d"``, ``"max_d"``, ``"time_scheme"``,
        ``"directory"``, ``"filesize"``, ``"compiler"``, ``"user"``,
        ``"format_version"``, ``"axisem_version"``, ``"datetime"``
        """
        pass

    def get_seismograms_finite_source(self, sources, receiver,
                                      components=("Z", "N", "E"),
                                      kind='displacement', dt=None,
                                      a_lanczos=5, correct_mu=False,
                                      progress_callback=None):
        """
        Extract seismograms for a finite source from an Instaseis database.

        :param sources: A collection of point sources.
        :type sources: :class:`~instaseis.source.FiniteSource` or list of
            :class:`~instaseis.source.Source` objects.
        :param receiver: The seismic receiver.
        :type receiver: :class:`instaseis.source.Receiver`
        :type components: tuple of str, optional
        :param components: Which components to calculate. Must be a tuple
            containing any combination of ``"Z"``, ``"N"``, ``"E"``,
            ``"R"``, and ``"T"``.
        :type kind: str, optional
        :param kind: The desired units of the seismogram:
            ``"displacement"``, ``"velocity"``, or ``"acceleration"``.
        :type dt: float, optional
        :param dt: Desired sampling rate of the seismograms. Resampling is done
            using a Lanczos kernel.
        :type a_lanczos: int, optional
        :param a_lanczos: The width of the kernel used in the resampling.
        :type correct_mu: bool, optional
        :param correct_mu: Correct the source magnitude for the actual shear
            modulus from the model.
        :type progress_callback: function, optional
        :param progress_callback: Optional callback function that will be
            called with current source number and the number of total
            sources for each calculated source. Useful for integration into
            user interfaces to provide some kind of progress information. If
            the callback returns ``True``, the calculation will be cancelled.

        :returns: Multi component finite source seismogram.
        :rtype: :class:`obspy.core.stream.Stream`
        """
        if not self.info.is_reciprocal:
            raise NotImplementedError

        data_summed = {}
        count = len(sources)
        for _i, source in enumerate(sources):
            data = self.get_seismograms(
                source, receiver, components, reconvolve_stf=True,
                return_obspy_stream=False, remove_source_shift=False)

            if correct_mu:
                corr_fac = data["mu"] / DEFAULT_MU,
            else:
                corr_fac = 1

            for comp in components:
                if comp in data_summed:
                    data_summed[comp] += data[comp] * corr_fac
                else:
                    data_summed[comp] = data[comp] * corr_fac
            if progress_callback:
                cancel = progress_callback(_i + 1, count)
                if cancel:
                    return None

        if dt is not None:
            for comp in components:
                # This is a bit tricky. We want to resample but we also want
                # to make sure that that the peak of the source time
                # function is exactly hit by a sample point.
                starttime = round(self.info.src_shift - (
                    int(round(self.info.src_shift / dt, 5)) * dt), 5)
                duration = (len(data[comp]) - 1) * self.info.dt - starttime
                new_npts = int(round(duration / dt, 5)) + 1
                data_summed[comp] = lanczos.lanczos_interpolation(
                    data=data[comp], old_start=0, old_dt=self.info.dt,
                    new_start=starttime, new_dt=dt, new_npts=new_npts,
                    a=a_lanczos, window="blackman")

        # Convert to an ObsPy Stream object.
        st = Stream()
        if dt is None:
            dt = self.info.dt
        band_code = get_band_code(dt)
        for comp in components:
            tr = Trace(data=data_summed[comp],
                       header={"delta": dt,
                               "station": receiver.station,
                               "network": receiver.network,
                               "channel": "%sX%s" % (band_code, comp)})
            st += tr
        return st

    def _get_seismograms_sanity_checks(self, source, receiver, components,
                                       kind):
        """
        Common sanity checks for the get_seismograms method. Also parses
        source and receiver objects if necessary.

        :param source: instaseis.Source or instaseis.ForceSource object
        :type source: :class:`instaseis.source.Source` or
            :class:`instaseis.source.ForceSource`
        :param receiver: instaseis.Receiver object
        :type receiver: :class:`instaseis.source.Receiver`
        :param components: a tuple containing any combination of the
            strings ``"Z"``, ``"N"``, ``"E"``, ``"R"``, and ``"T"``
        :param kind: 'displacement', 'velocity' or 'acceleration'
        """
        # Attempt to parse them if the types are not correct.
        if not isinstance(source, Source) and \
                not isinstance(source, ForceSource):
            source = Source.parse(source)
        if not isinstance(receiver, Receiver):
            # This only works in the special case of one station, otherwise
            # it has to be called more then once.
            rec = Receiver.parse(receiver)
            if len(rec) != 1:
                raise ValueError("Receiver object/file contains multiple "
                                 "stations. Please parse outside the "
                                 "get_seismograms() function and call in a "
                                 "loop.")
            receiver = rec[0]

        if kind not in ['displacement', 'velocity', 'acceleration']:
            raise ValueError('unknown kind %s' % (kind,))

        for comp in components:
            if comp not in ["N", "E", "Z", "R", "T"]:
                raise ValueError("Invalid component: %s" % comp)

        if self.info.is_reciprocal:
            if receiver.depth_in_m is not None:
                warnings.warn('Receiver depth cannot be changed when reading '
                              'from reciprocal DB. Using depth from the DB.')

            if any(comp in components for comp in ['N', 'E', 'R', 'T']) and \
                    "horizontal" not in self.info.components:
                raise ValueError("vertical component only DB")

            if 'Z' in components and "vertical" not in self.info.components:
                raise ValueError("horizontal component only DB")

        else:
            if source.depth_in_m is not None:
                warnings.warn('Source depth cannot be changed when reading '
                              'from forward DB. Using depth from the DB.')

        return source, receiver

    @property
    def info(self):
        try:
            return self.__cached_info
        except:
            pass
        self.__cached_info = AttribDict(self._get_info())
        return self.__cached_info

    def __str__(self):
        info = self.info

        return_str = (
            "{db} {reciprocal} Green's function Database (v{"
            "format_version}) "
            "generated with these parameters:\n"
            "\tcomponents           : {components}\n"
            "{source_depth}"
            "\tvelocity model       : {velocity_model}\n"
            "\tattenuation          : {attenuation}\n"
            "\tdominant period      : {period:.3f} s\n"
            "\tdump type            : {dump_type}\n"
            "\texcitation type      : {excitation_type}\n"
            "\ttime step            : {dt:.3f} s\n"
            "\tsampling rate        : {sampling_rate:.3f} Hz\n"
            "\tnumber of samples    : {npts}\n"
            "\tseismogram length    : {length:.1f} s\n"
            "\tsource time function : {stf}\n"
            "\tsource shift         : {src_shift:.3f} s\n"
            "\tspatial order        : {spatial_order}\n"
            "\tmin/max radius       : {min_radius:.1f} - {max_radius:.1f} km\n"
            "\tPlanet radius        : {planet_radius:.1f} km\n"
            "\tmin/max distance     : {min_d:.1f} - {max_d:.1f} deg\n"
            "\ttime stepping scheme : {time_scheme}\n"
            "\tcompiler/user        : {compiler} by {user}\n"
            "\tdirectory/url        : {directory}\n"
            "\tsize of netCDF files : {filesize}\n"
            "\tgenerated by AxiSEM version {axisem_version} at {datetime}\n"
        ).format(
            db=self.__class__.__name__,
            reciprocal="reciprocal" if info.is_reciprocal else "forward",
            components=info.components,
            source_depth=(
                "\tsource depth         : %.2f km\n" %
                info.source_depth) if info.source_depth is not None else "",
            velocity_model=info.velocity_model,
            attenuation=info.attenuation,
            period=info.period,
            dump_type=info.dump_type,
            excitation_type=info.excitation_type,
            dt=info.dt,
            sampling_rate=info.sampling_rate,
            npts=info.npts,
            length=info.length,
            stf=info.stf,
            src_shift=info.src_shift,
            spatial_order=info.spatial_order,
            min_radius=info.min_radius,
            max_radius=info.max_radius,
            planet_radius=info.planet_radius / 1.0E3,
            min_d=info.min_d,
            max_d=info.max_d,
            time_scheme=info.time_scheme,
            directory=info.directory,
            filesize=sizeof_fmt(info.filesize),
            compiler=info.compiler,
            user=info.user,
            format_version=info.format_version,
            axisem_version=info.axisem_version,
            datetime=info.datetime
        )
        return return_str


def sizeof_fmt(num):
    """
    Handy formatting for human readable filesizes.

    From http://stackoverflow.com/a/1094933/1657047
    """
    for x in ["bytes", "KB", "MB", "GB"]:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return "%3.1f %s" % (num, "TB")
