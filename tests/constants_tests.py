#!/usr/bin/env python3

import unittest

import kirjava


class TestConstantReading(unittest.TestCase):
    """
    Tests that constants are read correctly.
    """

    ...  # TODO


class TestConstantArithmetic(unittest.TestCase):
    """
    Tests that arithmetic with constants produces the correct results.
    """

    def test_python_conversions(self) -> None:
        """
        Tests that integers and longs can be created from Python int types.
        """

        self.assertEqual(2147483647, kirjava.constants.Integer(2147483647).value)
        self.assertEqual(-2147483648, kirjava.constants.Integer(-2147483648).value)

        self.assertRaises(OverflowError, kirjava.constants.Integer, 2147483648)
        self.assertRaises(OverflowError, kirjava.constants.Integer, -2147483649)
        self.assertRaises(OverflowError, kirjava.constants.Integer, 1258912582925125125)
        self.assertRaises(OverflowError, kirjava.constants.Integer, -124892861284248945)

        self.assertEqual(9223372036854775807, kirjava.constants.Long(9223372036854775807).value)
        self.assertEqual(-9223372036854775808, kirjava.constants.Long(-9223372036854775808).value)

        self.assertRaises(OverflowError, kirjava.constants.Long, 9223372036854775808)
        self.assertRaises(OverflowError, kirjava.constants.Long, -9223372036854775809)
        self.assertRaises(OverflowError, kirjava.constants.Long, 274512745812758412758971285)
        self.assertRaises(OverflowError, kirjava.constants.Long, -248127589217589406342958291)

    def test_integer_arithmetic(self) -> None:
        """
        Tests that 32-bit integers behave in the way they should.
        """

        self.assertEqual(
            kirjava.constants.Integer(-2147483648),
            kirjava.constants.Integer(2147483647) + kirjava.constants.Integer(1),
        )
        self.assertEqual(
            kirjava.constants.Integer(2147483647),
            kirjava.constants.Integer(-2147483648) - kirjava.constants.Integer(1),
        )

        self.assertEqual(
            kirjava.constants.Integer(469325057),
            kirjava.constants.Integer(999999999) * kirjava.constants.Integer(99999999),
        )
        self.assertEqual(
            kirjava.constants.Integer(-469325057),
            kirjava.constants.Integer(999999999) * kirjava.constants.Integer(-99999999),
        )

        self.assertEqual(
            kirjava.constants.Integer(249),
            kirjava.constants.Integer(1249) / kirjava.constants.Integer(5),
        )
        self.assertEqual(
            kirjava.constants.Integer(250),
            kirjava.constants.Integer(1250) / kirjava.constants.Integer(5),
        )
        self.assertEqual(
            kirjava.constants.Integer(250),
            kirjava.constants.Integer(1251) / kirjava.constants.Integer(5),
        )

        self.assertRaises(ZeroDivisionError, lambda: kirjava.constants.Integer(5) / kirjava.constants.Integer(0))
        self.assertRaises(ZeroDivisionError, lambda: kirjava.constants.Integer(5) % kirjava.constants.Integer(0))

        self.assertEqual(kirjava.constants.Integer(10), kirjava.constants.Integer(5) << kirjava.constants.Integer(1))
        self.assertEqual(
            kirjava.constants.Integer(-2147483648), kirjava.constants.Integer(5) << kirjava.constants.Integer(31),
        )
        self.assertEqual(kirjava.constants.Integer(5), kirjava.constants.Integer(5) << kirjava.constants.Integer(32))
        self.assertEqual(kirjava.constants.Integer(10), kirjava.constants.Integer(5) << kirjava.constants.Integer(33))
        self.assertEqual(
            kirjava.constants.Integer(1073741824), kirjava.constants.Integer(5) << kirjava.constants.Integer(-2),
        )
        self.assertEqual(kirjava.constants.Integer(10), kirjava.constants.Integer(5) << kirjava.constants.Integer(-31))

        self.assertEqual(
            kirjava.constants.Integer(-1), kirjava.constants.Integer(-2147483648) >> kirjava.constants.Integer(31),
        )
        # TODO: More right shift tests
        # TODO: And, or, xor tests

    def test_long_arithmetic(self) -> None:
        """
        Tests that 64-bit integers (longs) behave in the way they should.
        """

        ...  # TODO

    ...  # TODO: Float and double arithmetic
