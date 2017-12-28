"""
OpenEnsembles is a resource for performing and analyzing ensemble clustering

Copyright (C) 2017 Naegle Lab

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import os.path
import time
import unittest
import random
import pandas as pd

import openensembles as oe

class TestFunctions(unittest.TestCase):

    def setUp(self):
        fileName = 'data_test.csv'
        df = pd.DataFrame.from_csv(fileName)
        x = [0, 5, 30]
        self.data = oe.data(df, x)

    def test_correct_setup(self):
        self.assertEqual((3,3), self.data.D['parent'].shape)
        self.assertEqual(3, len(self.data.x['parent']))

    def test_incorrect_setup(self):
        fileName = 'data_test.csv'
        df = pd.DataFrame.from_csv(fileName)
        x = [0, 5, 10, 30]
        self.assertRaises(ValueError, lambda: oe.data(df,x)) 

    def test_setup_stringX(self):
        fileName = 'data_test.csv'
        df = pd.DataFrame.from_csv(fileName)
        x = ['something', 5, 30]
        self.data = oe.data(df,x)
        self.assertListEqual([0,1,2], self.data.x['parent'])

    def test_setup_floats(self):
        fileName = 'data_test.csv'
        df = pd.DataFrame.from_csv(fileName)
        x = [0.0, 5.0, 30.0]
        self.data = oe.data(df,x)
        self.assertListEqual(x, self.data.x['parent'])

    def test_transform_error_noSource(self):
        #self.assertEqual(-1, self.data.transform('parentZ', 'zscore', 'zscore_parentZ'))
        self.assertRaises(ValueError, lambda: self.data.transform('parentZ', 'zscore', 'zscore_parentZ'))

    def test_transform_NoNaNs(self):
        """
        Behavior in oe.data.transform when Keep_NaN=0 is to prevent the addition of a transformation that produced 
        NaNs. Keep_NaN default is True and must be set to prevent addition. NaNs produced will always produce a warning.
        """
        self.data.transform('parent', 'zscore', 'zscore', axis=1, Keep_NaN=False)
        self.assertEqual(1, len(self.data.D))

    def test_transform_NoInf(self):
        self.data.transform('parent', 'log', 'log10', base=10, Keep_Inf=False)
        self.assertEqual(1, len(self.data.D))

    def test_transform_error_noTxfm(self):
        self.assertRaises(ValueError, lambda: self.data.transform('parent', 'zscoreGobblyGook', 'zscore'))

    def test_internal_normalization(self):
        self.assertRaises(ValueError, lambda: self.data.transform('parent', 'internal_normalization', 'internal_normalization'))
        self.assertRaises(ValueError, lambda: self.data.transform('parent', 'internal_normalization', 'internal_normalization', x_val=40))
        self.assertRaises(ValueError, lambda: self.data.transform('parent', 'internal_normalization', 'internal_normalization', col_index=5))
        
        self.data.transform('parent', 'internal_normalization', 'internal_norm_to_5min_byIndex', col_index=1)
        self.assertEqual(2, len(self.data.D))

        self.data.transform('parent', 'internal_normalization', 'internal_norm_to_5min', x_val=5)
        self.assertEqual(3, len(self.data.D))

    def test_zscore_axis(self):
        self.data.transform('parent', 'zscore', 'zscore_axis0', axis=0)
        self.assertEqual(2, len(self.data.D))

        self.data.transform('parent', 'zscore', 'zscore_axis1', axis=1)
        self.assertEqual(3, len(self.data.D))

        self.data.transform('parent', 'zscore', 'zscore_axis_both', axis='both')
        self.assertEqual(4, len(self.data.D))

        self.assertRaises(ValueError, lambda: self.data.transform('parent', 'zscore', 'zscore', axis=3))



    def test_all_transform(self):
        #check to see that a new entry in D, x and params are added for every
        #transform available that has a default behavior
        TXFM_FCN_DICT = self.data.transforms_available()
        special_transforms = ['internal_normalization']
        for txfm in special_transforms:
            if txfm in TXFM_FCN_DICT:
                del TXFM_FCN_DICT[txfm]
        #take internal_normalization out 
        len_expected = 2
        for transform in TXFM_FCN_DICT:
            self.data.transform('parent', transform, transform)
            self.assertEqual(len_expected, len(self.data.D))
            self.assertEqual(len_expected, len(self.data.x))
            self.assertEqual(len_expected, len(self.data.params))
            len_expected += 1

    def test_all_algorithms(self):
        """
        Test all algorithms with default parameters
        """
        c = oe.cluster(self.data)
        ALG_FCN_DICT = c.algorithms_available()
        num = 0
        for algorithm in ALG_FCN_DICT:
            name = algorithm + 'parent'
            c.cluster('parent', algorithm, name, K=2)
            num += 1
        self.assertEqual(num, len(c.labels))

    def test_clustering_setup(self):
        c = oe.cluster(self.data)
        self.assertEqual(1, len(c.dataObj.D))

    def test_clustering_NoSource(self):
        c = oe.cluster(self.data)
        self.assertRaises(ValueError, lambda: c.cluster('parentZ', 'kmeans', 'bad'))

    def test_clustering_NoAlgorithm(self):
        c = oe.cluster(self.data)
        self.assertRaises(ValueError, lambda: c.cluster('parent', 'gobblygook', 'bad'))

    def test_clustering_namingTestRequireUnique(self):
        c = oe.cluster(self.data)
        c.cluster('parent', 'kmeans', 'kmeans', K=2)
        self.assertEqual(1, len(c.labels))

        c.cluster('parent', 'kmeans', 'kmeans', Require_Unique=1, K=2)
        self.assertEqual(1, len(c.labels))


    def test_clustering_namingTestRequireNotUnique(self):
        c = oe.cluster(self.data)
        c.cluster('parent', 'kmeans', 'kmeans', K=2)
        c.cluster('parent', 'kmeans', 'kmeans', Require_Unique=0, K=2)
        self.assertEqual(2, len(c.labels))

    def test_validation_badSourceAndCluster(self):
        c = oe.cluster(self.data)
        c.cluster('parent', 'kmeans', 'kmeans', K=2)
        v = oe.validation(self.data, c)
        self.assertRaises(ValueError, lambda: v.calculate('Ball_Hall', 'kmeans', 'gobblygook'))
        self.assertRaises(ValueError, lambda: v.calculate('Ball_Hall', 'gobblygook', 'parent'))
        self.assertRaises(ValueError, lambda: v.calculate('GobblyGook', 'kmeans', 'parent'))

    def test_ReplicateValidation(self):
        c = oe.cluster(self.data)
        c.cluster('parent', 'kmeans', 'kmeans', K=2)
        v = oe.validation(self.data, c)
        len_expected = 0
        self.assertEqual(len_expected, len(v.validation))
        v.calculate('Ball_Hall', 'kmeans', 'parent')
        len_expected = 1
        self.assertEqual(len_expected, len(v.validation))
        v.calculate('Ball_Hall', 'kmeans', 'parent')
        self.assertEqual(len_expected, len(v.validation))



    def test_allValidationMetrics(self):
        c = oe.cluster(self.data)
        c.cluster('parent', 'kmeans', 'kmeans', K=2)
        v = oe.validation(self.data, c)
        FCN_DICT = v.validation_metrics_available()
        len_expected = 1
        for validation_name in FCN_DICT:
            v.calculate(validation_name, 'kmeans', 'parent')
            self.assertEqual(len_expected, len(v.validation))
            self.assertEqual(len_expected, len(v.description))
            self.assertEqual(len_expected, len(v.source_name))
            self.assertEqual(len_expected, len(v.cluster_name))
            len_expected += 1





