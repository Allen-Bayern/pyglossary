import unittest
import random
from typing import Optional, Tuple, List, Any

from pyglossary.option import *


class TestOptionValidateIntBool(unittest.TestCase):
	def caseOK(self, cls, raw: str, value: Optional[bool]):
		opt = cls()
		valueActual, ok = opt.evaluate(raw)
		self.assertTrue(ok, "evaluate failed")
		self.assertEqual(valueActual, value)
		ok2 = opt.validate(valueActual)
		self.assertEqual(ok2, True, "validate failed")

	def caseFailed(self, cls, raw: str, value: Optional[bool]):
		opt = cls()
		valueActual, ok = opt.evaluate(raw)
		self.assertFalse(ok)
		self.assertEqual(valueActual, value)

	def test_bool_ok(self):
		self.caseOK(BoolOption, "True", True)
		self.caseOK(BoolOption, "False", False)

		self.caseOK(BoolOption, "true", True)
		self.caseOK(BoolOption, "false", False)

		self.caseOK(BoolOption, "TRUE", True)
		self.caseOK(BoolOption, "FALSE", False)

		self.caseOK(BoolOption, "1", True)
		self.caseOK(BoolOption, "0", False)

		self.caseOK(BoolOption, "yes", True)
		self.caseOK(BoolOption, "no", False)

		self.caseOK(BoolOption, "YES", True)
		self.caseOK(BoolOption, "NO", False)

	def test_bool_failed(self):
		self.caseFailed(BoolOption, "Y", None)
		self.caseFailed(BoolOption, "N", None)
		self.caseFailed(BoolOption, "YESS", None)
		self.caseFailed(BoolOption, "NOO", None)
		self.caseFailed(BoolOption, "123", None)
		self.caseFailed(BoolOption, "a", None)

	def test_int_ok(self):
		self.caseOK(IntOption, "0", 0)
		self.caseOK(IntOption, "1", 1)
		self.caseOK(IntOption, "-1", -1)
		self.caseOK(IntOption, "1234", 1234)

	def test_int_failed(self):
		self.caseFailed(IntOption, "abc", None)
		self.caseFailed(IntOption, "12f", None)
		self.caseFailed(IntOption, "fff", None)


class TestOptionValidateStr(unittest.TestCase):
	def newTester(self, customValue: bool, values: List[str]):
		def test(raw: str, valid: bool):
			opt = StrOption(customValue=customValue, values=values)
			valueActual, evalOkActual = opt.evaluate(raw)
			self.assertEqual(evalOkActual, True, "evaluate failed")
			self.assertEqual(valueActual, raw)
			validActual = opt.validate(valueActual)
			self.assertEqual(validActual, valid, "validate failed")
		return test

	def test_1(self):
		test = self.newTester(False, ["a", "b", "c"])
		test("a", True)
		test("b", True)
		test("c", True)
		test("d", False)
		test("123", False)

	def test_2(self):
		test = self.newTester(True, ["a", "b", "3"])
		test("a", True)
		test("b", True)
		test("c", True)
		test("d", True)
		test("123", True)


class TestOptionValidateDict(unittest.TestCase):
	def caseOK(self, raw: str, value: Optional[Dict]):
		opt = DictOption()
		valueActual, ok = opt.evaluate(raw)
		self.assertTrue(ok, "evaluate failed")
		self.assertEqual(valueActual, value)
		ok2 = opt.validate(valueActual)
		self.assertEqual(ok2, True, "validate failed")

	def caseEvalFail(self, raw: str):
		opt = DictOption()
		valueActual, ok = opt.evaluate(raw)
		self.assertFalse(ok)
		self.assertEqual(valueActual, None)

	def test_dict_ok(self):
		self.caseOK("", None)
		self.caseOK("{}", {})
		self.caseOK('{"a": 1}', {"a": 1})
		self.caseOK('{"a": "b", "123":456}', {"a": "b", "123": 456})

	def test_dict_syntaxErr(self):
		self.caseEvalFail("123abc")
		self.caseEvalFail('{')
		self.caseEvalFail("(")
		self.caseEvalFail('{"a": 1')
		self.caseEvalFail('{"a": 1]')
		self.caseEvalFail('][')

	def test_dict_notDict(self):
		self.caseEvalFail("123")
		self.caseEvalFail("[]")
		self.caseEvalFail("[1, 2, 3]")
		self.caseEvalFail('["a", 2, 3.5]')
		self.caseEvalFail('{10, 20, 30}')


if __name__ == "__main__":
	unittest.main()
