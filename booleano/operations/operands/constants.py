# -*- coding: utf-8 -*-
#
# Copyright (c) 2009 by Gustavo Narea <http://gustavonarea.net/>.
#
# This file is part of Booleano <http://code.gustavonarea.net/booleano/>.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, distribute with
# modifications, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# ABOVE COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright
# holders shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written authorization.
"""
Constant operands.

"""
from booleano.exc import InvalidOperationError
from booleano.operations.operands import Operand

__all__ = ["String", "Number", "Arithmetic", "Set"]


class Constant(Operand):
	"""
	Base class for constant operands.

	The only operation that is common to all the constants is equality (see
	:meth:`equals`).

	Constants don't rely on the context -- they are constant!

	.. warning::
		This class is available as the base for the built-in :class:`String`,
		:class:`Number` and :class:`Set` classes. User-defined constants aren't
		supported, but you can assign a name to a constant (see
		:term:`binding`).

	"""

	operations = {'equality'}

	def __init__(self, constant_value):
		"""

		:param constant_value: The Python value represented by the Booleano
			constant.
		:type constant_value: :class:`object`

		"""
		self.constant_value = constant_value

	def to_python(self, context):
		"""
		Return the value represented by this constant.

		"""
		return self.constant_value

	def equals(self, value, context):
		"""
		Check if this constant equals ``value``.

		"""
		return self.constant_value == value

	def check_equivalence(self, node):
		"""
		Make sure constant ``node`` and this constant are equivalent.

		:param node: The other constant which may be equivalent to this one.
		:type node: Constant
		:raises AssertionError: If the constants are of different types or
			represent different values.

		"""
		super(Constant, self).check_equivalence(node)
		assert node.constant_value == self.constant_value, \
			u'Constants %s and %s represent different values' % (self,
			                                                     node)


class String(Constant):
	u"""
	Constant string.

	These constants only support equality operations.

	.. note:: **Membership operations aren't supported**

		Although both sets and strings are item collections, the former is
		unordered and the later is ordered. If they were supported, there would
		some ambiguities to sort out, because users would expect the following
		operation results:

		- ``"ao" ⊂ "hola"`` is false: If strings were also sets, then the
		  resulting operation would be ``{"a", "o"} ⊂ {"h", "o", "l", "a"}``,
		  which is true.
		- ``"la" ∈ "hola"`` is true: If strings were also sets, then the
		  resulting operation would be ``{"l", "a"} ∈ {"h", "o", "l", "a"}``,
		  which would be an *invalid operation* because the first operand must
		  be an item, not a set. But if we make an exception and take the first
		  operand as an item, the resulting operation would be
		  ``"la" ∈ {"h", "o", "l", "a"}``, which is not true.

		The solution to the problems above would involve some magic which
		contradicts the definition of a set: Take the second operand as an
		*ordered collection*. But it'd just cause more trouble, because both
		operations would be equivalent!

		Also, there would be other issues to take into account (or not), like
		case-sensitivity.

		Therefore, if this functionality is needed, developers should create
		functions to handle it.

	"""

	def __init__(self, string):
		"""

		:param string: The Python string to be represented by this Booleano
			string.
		:type string: :class:`basestring`

		``string`` will be converted to :class:`unicode`, so it doesn't
		have to be a :class:`basestring` initially.

		"""
		import sys
		if sys.version_info >= (3, 0):
			string = str(string)
		else:
			string = unicode(string)
		super(String, self).__init__(string)

	def equals(self, value, context):
		"""Turn ``value`` into a string if it isn't a string yet"""
		value = str(value)
		return super(String, self).equals(value, context)

	def __unicode__(self):
		"""Return the Unicode representation of this constant string."""
		return u'"%s"' % self.constant_value

	def __hash__(self):
		return id(self)

	def __repr__(self):
		"""Return the representation for this constant string."""
		return '<String "%s">' % self.constant_value.encode("utf-8")


class ArithmeticVariable(object):
	def __init__(self, number, namespace, namespace_separator=":"):
		self.namespace_separator = namespace_separator
		self.parsed_results = number
		self._namespace = namespace
		self.variables = {}
		self.__define_variables()
		number = self.flatten(self.parsed_results)
		self.__full_expression = "".join(number)

	def __str__(self):
		number = self.flatten(self.parsed_results)
		return "".join(number)

	def __define_variables(self):
		number = self.parsed_results
		temp = []
		for n in number:
			t = self.__get_variable_names(n)
			if isinstance(t, list):
				temp.extend(t)
			else:
				temp.append(t)
		self.required_variables = temp
		temp = {}
		for v in self.required_variables:
			for k, val in v.items():
				temp[k] = val
		self.required_variables = temp

	def __get_variable_names(self, number):
		from pyparsing import ParseResults
		import re
		temp = []
		if isinstance(number, ParseResults):
			for n in number:
				t = self.__get_variable_names(n)
				if isinstance(t, list):
					temp.extend(t)
				else:
					temp.append(t)
			return temp
		elif len(re.findall("[a-zA-Z" + self.namespace_separator + "]+", number)) > 0:
			var = str(number).split(self.namespace_separator)
			variable_namespaces = var[0:-1]
			variable_name = var[-1]
			return {str(number): self._namespace.get_object(variable_name, variable_namespaces)}
		return temp

	@classmethod
	def flatten(cls, s):
		from pyparsing import ParseResults
		if s == []:
			return s
		if isinstance(s[0], ParseResults):
			return cls.flatten(s[0]) + cls.flatten(s[1:])
		return s[:1] + cls.flatten(s[1:])

	def replace(self, num, context, namespace=True):
		for k, v in self.required_variables.items():
			if namespace and self.namespace_separator not in k:
				continue
			num = num.replace(k, str(v.to_python(context)))
		return num

	def evaluate(self, context):
		number = self.__full_expression
		# Replace all variables with numbers
		# First replace variables with namespaces defined to avoid clobbering
		number = self.replace(number, context)
		# Then replace variables with no namespace
		number = self.replace(number, context, False)
		number = number.replace("^", "**")
		from booleano import SafeEval
		answer = SafeEval.eval_expr(number)
		return answer


class Arithmetic(Constant):
	"""
	Numeric constant.

	These constants support inequality operations; see :meth:`greater_than`
	and :meth:`less_than`.

	"""

	operations = Constant.operations | {'inequality'}

	def __init__(self, number, namespace, namespace_separator=":"):
		"""

		:param number: The number to be represented, as a Python object.
		:type number: :class:`object`

		``number`` is converted into a :class:`float` internally, so it can
		be an :class:`string <basestring>` initially.

		"""
		self.namespace_sparator = namespace_separator
		super(Arithmetic, self).__init__(ArithmeticVariable(number, namespace, namespace_separator))

	def equals(self, value, context):
		"""
		Check if this numeric constant equals ``value``.

		:raises InvalidOperationError: If ``value`` can't be turned into a
			float.

		``value`` will be turned into a float prior to the comparison, to
		support strings.

		"""
		print("Constant equals")
		return super(Arithmetic, self).equals(self._to_number(value), context)

	def greater_than(self, value, context):
		"""
		Check if this numeric constant is greater than ``value``.

		:raises InvalidOperationError: If ``value`` can't be turned into a
			float.

		``value`` will be turned into a float prior to the comparison, to
		support strings.

		"""
		print("Constant gt")
		return self.constant_value > self._to_number(value)

	def less_than(self, value, context):
		"""
		Check if this numeric constant is less than ``value``.

		:raises InvalidOperationError: If ``value`` can't be turned into a
			float.

		``value`` will be turned into a float prior to the comparison, to
		support strings.

		"""
		print("Constant lt")
		return self.constant_value < self._to_number(value)

	def to_python(self, context):
		return self.constant_value.evaluate(context)

	def _to_number(self, value):
		"""
		Convert ``value`` to a Python float and return the new value.

		:param value: The value to be converted into float.
		:return: The value as a float.
		:rtype: float
		:raises InvalidOperationError: If ``value`` can't be converted.

		"""
		print("Constant to_num")
		try:
			return float(value)
		except ValueError:
			raise InvalidOperationError('"%s" is not a number' % value)

	def __unicode__(self):
		"""Return the Unicode representation of this constant number."""
		print("constant unicode")
		return str(self.constant_value)

	def __repr__(self):
		"""Return the representation for this constant number."""
		return '<Arithmetic %s>' % self.constant_value


class Number(Constant):
	"""
	Numeric constant.

	These constants support inequality operations; see :meth:`greater_than`
	and :meth:`less_than`.

	"""

	operations = Constant.operations | {'inequality'}

	def __init__(self, number):
		"""

		:param number: The number to be represented, as a Python object.
		:type number: :class:`object`

		``number`` is converted into a :class:`float` internally, so it can
		be an :class:`string <basestring>` initially.

		"""
		number = float(number)
		super(Number, self).__init__(number)

	def equals(self, value, context):
		"""
		Check if this numeric constant equals ``value``.

		:raises InvalidOperationError: If ``value`` can't be turned into a
			float.

		``value`` will be turned into a float prior to the comparison, to
		support strings.

		"""
		return super(Number, self).equals(self._to_number(value), context)

	def greater_than(self, value, context):
		"""
		Check if this numeric constant is greater than ``value``.

		:raises InvalidOperationError: If ``value`` can't be turned into a
			float.

		``value`` will be turned into a float prior to the comparison, to
		support strings.

		"""
		return self.constant_value > self._to_number(value)

	def less_than(self, value, context):
		"""
		Check if this numeric constant is less than ``value``.

		:raises InvalidOperationError: If ``value`` can't be turned into a
			float.

		``value`` will be turned into a float prior to the comparison, to
		support strings.

		"""
		return self.constant_value < self._to_number(value)

	def _to_number(self, value):
		"""
		Convert ``value`` to a Python float and return the new value.

		:param value: The value to be converted into float.
		:return: The value as a float.
		:rtype: float
		:raises InvalidOperationError: If ``value`` can't be converted.

		"""
		try:
			return float(value)
		except ValueError:
			raise InvalidOperationError('"%s" is not a number' % value)

	def __unicode__(self):
		"""Return the Unicode representation of this constant number."""
		return str(self.constant_value)

	def __repr__(self):
		"""Return the representation for this constant number."""
		return '<Number %s>' % self.constant_value


class Set(Constant):
	"""
	Constant sets.

	These constants support membership operations; see :meth:`contains` and
	:meth:`is_subset`.

	"""

	operations = Constant.operations | {"inequality", "membership"}

	def __init__(self, *items):
		"""

		:raises booleano.exc.InvalidOperationError: If at least one of the
			``items`` is not an operand.

		"""
		for item in items:
			if not isinstance(item, Operand):
				raise InvalidOperationError('Item "%s" is not an operand, so '
				                            'it cannot be a member of a set' %
				                            item)
		super(Set, self).__init__(set(items))

	def to_python(self, context):
		"""
		Return a set made up of the Python representation of the operands
		contained in this set.

		"""
		items = set(item.to_python(context) for item in self.constant_value)
		return items

	def equals(self, value, context):
		"""Check if all the items in ``value`` are the same of this set."""
		value = set(value)
		return value == self.to_python(context)

	def less_than(self, value, context):
		"""
		Check if this set has less items than the number represented in
		``value``.

		:raises InvalidOperationError: If ``value`` is not an integer.

		"""
		value = self._to_int(value)
		return len(self.constant_value) < value

	def greater_than(self, value, context):
		"""
		Check if this set has more items than the number represented in
		``value``.

		:raises InvalidOperationError: If ``value`` is not an integer.

		"""
		value = self._to_int(value)
		return len(self.constant_value) > value

	def belongs_to(self, value, context):
		"""
		Check that this constant set contains the ``value`` item.

		"""
		for item in self.constant_value:
			try:
				if item.equals(value, context):
					return True
			except InvalidOperationError:
				continue
		return False

	def is_subset(self, value, context):
		"""
		Check that the ``value`` set is a subset of this constant set.

		"""
		for item in value:
			if not self.belongs_to(item, context):
				return False
		return True

	def check_equivalence(self, node):
		"""
		Make sure set ``node`` and this set are equivalent.

		:param node: The other set which may be equivalent to this one.
		:type node: Set
		:raises AssertionError: If ``node`` is not a set or it's a set
			with different elements.

		"""
		Operand.check_equivalence(self, node)

		unmatched_elements = list(self.constant_value)
		assert len(unmatched_elements) == len(node.constant_value), \
			u'Sets %s and %s do not have the same cardinality' % \
			(unmatched_elements, node)

		# Checking that each element is represented by a mock operand:
		for element in node.constant_value:
			for key in range(len(unmatched_elements)):
				if unmatched_elements[key] == element:
					del unmatched_elements[key]
					break

		assert 0 == len(unmatched_elements), \
			u'No match for the following elements: %s' % unmatched_elements

	def __unicode__(self):
		"""Return the Unicode representation of this constant set."""
		elements = [str(element) for element in self.constant_value]
		elements = u", ".join(elements)
		return "{%s}" % elements

	def __repr__(self):
		"""Return the representation for this constant set."""
		elements = [repr(element) for element in self.constant_value]
		elements = ", ".join(elements)
		if elements:
			elements = " " + elements
		return '<Set%s>' % elements

	@classmethod
	def _to_int(cls, value):
		"""
		Convert ``value`` is to integer if possible.

		:param value: The value to be verified.
		:return: ``value`` as integer.
		:rtype: int
		:raises InvalidOperationError: If ``value`` is not an integer.

		This is a workaround for Python < 2.6, where floats didn't have the
		``.is_integer()`` method.

		"""
		try:
			value_as_int = int(value)
			is_int = value_as_int == float(value)
		except (ValueError, TypeError):
			is_int = False
		if not is_int:
			raise InvalidOperationError("To compare the amount of items in a "
			                            "set, the operand %s has to be an "
			                            "integer" % repr(value))
		return value_as_int
