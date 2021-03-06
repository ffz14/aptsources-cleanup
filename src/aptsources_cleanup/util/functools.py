# -*- coding: utf-8
"""Utilities for and around functional programming"""
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = (
	'comp', 'cmp_to_key', 'total_ordering', 'reduce', 'update_wrapper', 'wraps',
	'partial', 'LazyInstance'
)

from ._3to2 import *
from functools import *
from .operator import rapply, identity, methodcaller


def comp(*funcs):
	"""Returns a function object that concatenates the passed functions from left
	to right.
	"""

	assert all(map(callable, funcs))
	if len(funcs) <= 1:
		return funcs[0] if funcs else identity
	return partial(reduce, rapply, funcs)


class LazyInstance(object):
	"""Instantiate objects lazily on first access

	Instances of this class provide transparent attribute access to the wrapped
	instance which is created on demand during the first access or on first call
	for methods present in the type of the wrapped object (if known).
	"""

	__slots__ = ('_li_instance', '_li_factory', '_li_type_hint', '_li_strict')


	def __init__(self, factory, type_hint=None, strict=False):
		"""Creates a new lazy instance object

		'factory' must be a nullary function that returns the underlying object as
		needed and is called at most once.

		'type_hint' is a hint to the type of the return value of 'factory'. If
		unset or None and if 'factory' is itself a type it defaults to 'factory'.
		A type hint is necessary for implicit lazy instantion on method call.

		If 'strict' is true and a type hint is available (see above) raise
		AttributeError when trying to access attributes that exist neither on
		LazyInstance nor on the type of the (future) wrapped object.
		"""

		self._li_instance = None
		self._li_factory = factory
		self._li_strict = strict

		if type_hint is None:
			if isinstance(factory, TypesType):
				type_hint = factory
		elif not isinstance(type_hint, TypesType):
			raise TypeError(
				'type_hint must be None or a type, not ' + str(type(type_hint)))
		self._li_type_hint = type_hint


	@property
	def _instance(self):
		"""Accesses the wrapped instance

		and create it using the factory method provided earlier if necessary.
		"""

		if self._li_factory is not None:
			self._li_instance = self._li_factory()
			assert (self._li_type_hint is None or
				isinstance(self._li_instance, self._li_type_hint))
			self._li_factory = None
			self._li_type_hint = None

		return self._li_instance


	def __getattr__(self, name):
		if self._li_type_hint is not None:
			if self._li_strict:
				value = getattr(self._li_type_hint, name)
			else:
				value = getattr(self._li_type_hint, name, None)
			if callable(value):
				return self._li_bind_method_impl(name)

		return getattr(self._instance, name)


	def _bind_method(self, *methods_or_names):
		"""Wrap a lazy method call

		Returns a function based on an attribute of the (future) wrapped object but
		don't instantiate the wrapped object until execution.  You can provide both
		attribute names or an arbitrary getter method for attribute access.

		If you specify multible accessors this returns a sequence of functions as
		described above.
		"""

		if len(methods_or_names) == 1:
			return self._li_bind_method_impl(methods_or_names)
		return map(self._li_bind_method_impl, methods_or_names)


	def _li_bind_method_impl(self, method_or_name):
		if not callable(method_or_name):
			method_or_name = methodcaller(getattr, method_or_name)

		if self._li_factory is None:
			return method_or_name(self._li_instance)

		return lambda *args: method_or_name(self._instance)(*args)
