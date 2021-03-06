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
import unittest

import numpy

from nhlib import const
from nhlib import imt
from nhlib.geo import Point
from nhlib.tom import PoissonTOM
from nhlib.calc.hazard_curve import hazard_curves_poissonian


class HazardCurvesTestCase(unittest.TestCase):
    class FakeRupture(object):
        def __init__(self, probability, tectonic_region_type):
            self.probability = probability
            self.tectonic_region_type = tectonic_region_type
        def get_probability(self):
            return self.probability

    class FakeSource(object):
        def __init__(self, ruptures, time_span):
            self.time_span = time_span
            self.ruptures = ruptures
        def iter_ruptures(self, tom):
            assert tom.time_span is self.time_span
            assert isinstance(tom, PoissonTOM)
            return iter(self.ruptures)

    class FakeGSIM(object):
        def __init__(self, truncation_level, imts, poes):
            self.truncation_level = truncation_level
            self.imts = imts
            self.poes = poes
            self.dists = object()
        def make_contexts(self, sites, rupture):
            return (sites, rupture, self.dists)
        def get_poes(self, sctx, rctx, dctx, imt, imls, truncation_level):
            assert truncation_level is self.truncation_level
            assert dctx is self.dists
            return numpy.array([self.poes[(site, rctx, imt)]
                                for site in sctx])

    class FakeSite(object):
        def __init__(self, location):
            self.location = location

    def test1(self):
        truncation_level = 3.4
        imts = {imt.PGA(): [1, 2, 3], imt.PGD(): [2, 4]}
        time_span = 49.2

        rup11 = self.FakeRupture(0.23, const.TRT.ACTIVE_SHALLOW_CRUST)
        rup12 = self.FakeRupture(0.15, const.TRT.ACTIVE_SHALLOW_CRUST)
        rup21 = self.FakeRupture(0.04, const.TRT.VOLCANIC)
        source1 = self.FakeSource([rup11, rup12], time_span=time_span)
        source2 = self.FakeSource([rup21], time_span=time_span)
        sources = iter([source1, source2])
        site1 = self.FakeSite(Point(10, 20))
        site2 = self.FakeSite(Point(20, 30))
        sites = [site1, site2]

        gsim1 = self.FakeGSIM(truncation_level, imts, poes={
            (site1, rup11, imt.PGA()): [0.1, 0.05, 0.03],
            (site2, rup11, imt.PGA()): [0.11, 0.051, 0.034],
            (site1, rup12, imt.PGA()): [0.12, 0.052, 0.035],
            (site2, rup12, imt.PGA()): [0.13, 0.053, 0.036],

            (site1, rup11, imt.PGD()): [0.4, 0.33],
            (site2, rup11, imt.PGD()): [0.39, 0.331],
            (site1, rup12, imt.PGD()): [0.38, 0.332],
            (site2, rup12, imt.PGD()): [0.37, 0.333],
        })
        gsim2 = self.FakeGSIM(truncation_level, imts, poes={
            (site1, rup21, imt.PGA()): [0.5, 0.3, 0.2],
            (site2, rup21, imt.PGA()): [0.4, 0.2, 0.1],

            (site1, rup21, imt.PGD()): [0.24, 0.08],
            (site2, rup21, imt.PGD()): [0.14, 0.09],
        })
        gsims = {const.TRT.ACTIVE_SHALLOW_CRUST: gsim1,
                 const.TRT.VOLCANIC: gsim2}

        site1_pga_poe_expected = [0.0639157, 0.03320212, 0.02145989]
        site2_pga_poe_expected = [0.06406232, 0.02965879, 0.01864331]
        site1_pgd_poe_expected = [0.16146619, 0.1336553]
        site2_pgd_poe_expected = [0.15445961, 0.13437589]

        curves = hazard_curves_poissonian(sources, sites, imts, time_span,
                                          gsims, truncation_level)
        self.assertIsInstance(curves, dict)
        self.assertEqual(set(curves.keys()), set([imt.PGA(), imt.PGD()]))

        pga_curves = curves[imt.PGA()]
        self.assertIsInstance(pga_curves, numpy.ndarray)
        self.assertEqual(pga_curves.shape, (2, 3))  # two sites, three IMLs
        site1_pga_poe, site2_pga_poe = pga_curves
        self.assertTrue(numpy.allclose(site1_pga_poe, site1_pga_poe_expected),
                        str(site1_pga_poe))
        self.assertTrue(numpy.allclose(site2_pga_poe, site2_pga_poe_expected),
                        str(site2_pga_poe))

        pgd_curves = curves[imt.PGD()]
        self.assertIsInstance(pgd_curves, numpy.ndarray)
        self.assertEqual(pgd_curves.shape, (2, 2))  # two sites, two IMLs
        site1_pgd_poe, site2_pgd_poe = pgd_curves
        self.assertTrue(numpy.allclose(site1_pgd_poe, site1_pgd_poe_expected),
                        str(site1_pgd_poe))
        self.assertTrue(numpy.allclose(site2_pgd_poe, site2_pgd_poe_expected),
                        str(site2_pgd_poe))
