# nhlib: A New Hazard Library
# Copyright (C) 2012 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`nhlib.calc.hazard_curve` implements :func:`hazard_curves`.
"""
import numpy

from nhlib.tom import PoissonTOM


def hazard_curves_poissonian(sources, sites, imts, time_span,
                             gsims, truncation_level):
    """
    Compute hazard curves on a list of sites, given a set of seismic sources
    and a set of ground shaking intensity models (one per tectonic region type
    considered in the seismic sources).

    The calculator assumes :class:`Poissonian <nhlib.tom.PoissonianTOM>`
    temporal occurrence model.

    The calculator computes probability of ground motion exceedance according
    to the equation as described in pag. 419 of "OpenSHA: A Developing
    Community-modeling Environment for Seismic Hazard Analysis, Edward
    H. Field, Thomas H. Jordan and C. Allin Cornell. Seismological Research
    Letters July/August 2003 v. 74 no. 4 p. 406-419".

    :param sources:
        An iterator of seismic sources objects (instances of subclasses
        of :class:`~nhlib.source.base.SeismicSource`).
    :param sites:
        Instance of :class:`~nhlib.site.SiteCollection` object, representing
        sites of interest.
    :param imts:
        Dictionary mapping intensity measure type objects (see
        :mod:`nhlib.imt`) to lists of intensity measure levels.
    :param time_span:
        An investigation period for Poissonian temporal occurrence model,
        floating point number in years.
    :param gsims:
        Dictionary mapping tectonic region types (members
        of :class:`nhlib.const.TRT`) to :class:`~nhlib.gsim.base.GMPE`
        or :class:`~nhlib.gsim.base.IPE` objects.
    :param trunctation_level:
        Float, number of standard deviations for truncation of the intensity
        distribution.

    :returns:
        Dictionary mapping intensity measure type objects (same keys
        as in parameter ``imts``) to 2d numpy arrays of float, where
        first dimension differentiates sites (the order and length
        are the same as in ``sites`` parameter) and the second one
        differentiates IMLs (the order and length are the same as
        corresponding value in ``imts`` dict).
    """
    curves = dict((imt, numpy.ones([len(sites), len(imts[imt])]))
                  for imt in imts)
    tom = PoissonTOM(time_span)

    for source in sources:
        for rupture in source.iter_ruptures(tom):
            prob = rupture.get_probability()
            gsim = gsims[rupture.tectonic_region_type]
            sctx, rctx, dctx = gsim.make_contexts(sites, rupture)
            for imt in imts:
                poes = gsim.get_poes(sctx, rctx, dctx, imt, imts[imt],
                                     truncation_level)
                curves[imt] *= (1 - prob) ** poes

    for imt in imts:
        curves[imt] = 1 - curves[imt]
    return curves
