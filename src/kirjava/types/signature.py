# FIXME: All of this

# #!/usr/bin/env python3

# """
# Generic signature parsing.
# """

# from typing import Union

# from .descriptor import _find_enclosing, next_argument as next_argument_
# from .. import types
# from ..types import (
#     ArrayType, ClassOrInterfaceType,
#     BaseType, InvalidType,
#     TypeArgument, TypeArgumentList, TypeParameter, TypeVariable, VoidType, Wildcard,
# )

# _FORWARD_BASE_TYPES = {
#     "B": types.byte_t,
#     "S": types.short_t,
#     "I": types.int_t,
#     "J": types.long_t,
#     "C": types.char_t,
#     "F": types.float_t,
#     "D": types.double_t,
#     "Z": types.bool_t,
#     "V": types.void_t,
# }
# _BACKWARD_BASE_TYPES = {
#     types.byte_t: "B",
#     types.short_t: "S",
#     types.int_t: "I",
#     types.long_t: "J",
#     types.char_t: "C",
#     types.float_t: "F",
#     types.double_t: "D",
#     types.bool_t: "Z",
#     types.void_t: "V",
# }


# # FIXME
# # def to_signature(*values: Union[tuple["BaseType", ...], "BaseType"], dont_throw: bool = False) -> str:
# #     """
# #     Serializes the provided types into a signature.

# #     :param values: The types to serialize.
# #     :param dont_throw: Don't throw an exception if an invalid type is passed.
# #     :return: The serialized signature.
# #     """

# #     signature = ""
# #     for value in values:
# #         if value in _BACKWARD_BASE_TYPES:
# #             signature += _BACKWARD_BASE_TYPES[value]
# #         elif isinstance(value, ClassTypeArgument):
# #             signature += "L%s<%s>;" % (value.class_, to_signature(*value.type_arguments, dont_throw=dont_throw))
# #         elif isinstance(value, ClassOrInterfaceType):
# #             signature += "L%s;" % value.class_
# #         elif isinstance(value, ArrayType):
# #             signature += "%s%s" % ("[" * value.dimension, to_signature(value.element_type, dont_throw=dont_throw))
# #         elif isinstance(value, tuple):
# #             signature += "(%s)" % to_signature(*value, dont_throw=dont_throw)
# #         elif isinstance(value, VariableTypeArgument):
# #             signature += "T%s;" % value.name_
# #         elif isinstance(value, WildcardTypeArgument):
# #             signature += "*"
# #         elif isinstance(value, ExtendedTypeArgument):
# #             signature += "+%s" % to_signature(value.bound, dont_throw=dont_throw)
# #         elif isinstance(value, SuperTypeArgument):
# #             signature += "-%s" % to_signature(value.bound, dont_throw=dont_throw)
# #         elif isinstance(value, VariableTypeSignature):
# #             signature += "<%s:%s>" % (value.variable.name_, to_signature(value.bound, dont_throw=dont_throw))
# #         elif isinstance(value, ThrowsTypeSignature):
# #             signature += "^%s" % to_signature(value.signature, dont_throw=dont_throw)
# #         elif isinstance(value, TypeSignature):
# #             signature += "<%s>" % to_signature(*value.type_arguments, dont_throw=dont_throw)
# #         elif not dont_throw:
# #             raise TypeError("Invalid type for signature: %r." % value)

# #     return signature


# def next_argument(signature: str, force_read: bool = False) -> tuple[Union[TypeArgumentList, TypeArgument, BaseType], str]:
#     """
#     Gets the next type argument from a signature.

#     :param signature: The signature.
#     :param force_read: Force read the next argument, even if an error has occurred?
#     :return: The next argument and the remaining signature.
#     """

#     if not signature:
#         return InvalidType(signature), ""

#     # if signature.startswith("<") and signature.endswith(">"):
#     #     signature = signature[1:-1]

#     char = signature[0]

#     if char in _FORWARD_BASE_TYPES:
#         return next_argument_(signature)  # Regular type argument

#     elif char == "L":
#         inner_name = None
#         inner_arguments_signature = ""

#         if "<" in signature[:signature.find(";")]:
#             name, arguments_signature, remaining = _find_enclosing(signature, "<", ">")

#             if "." in name:  # It's found the inner class's signature, not the outer's
#                 name = name[:name.find(".")]
#                 arguments_signature = None
#                 remaining = remaining[remaining.find("."):]  # This won't mess up as there's no signature on the outer

#             if remaining is not None and remaining.startswith("."):
#                 inner_signature = remaining
#             elif "." in signature[:signature.find(";")]:  # Check for any inner classes
#                 # We can do this as we've already checked, and the outer class has no generic signature
#                 inner_signature = signature[signature.find("."):]
#             else:
#                 inner_signature = None

#             if inner_signature is not None:  # Find the inner class signature if there is one
#                 if "<" in inner_signature[:inner_signature.find(";")]:  # Inner class is generic
#                     inner_name, inner_arguments_signature, remaining = _find_enclosing(inner_signature, "<", ">")
#                 else:
#                     inner_name = inner_signature[:inner_signature.find(";")]
#                     remaining = inner_signature[inner_signature.find(";"):]

#                 inner_name = inner_name[1:]

#             # Excusable if there's an inner name as the outer may not be generic
#             if (arguments_signature is None and not inner_name) or not remaining.startswith(";"):
#                 return InvalidType(signature), ""

#             name = name[1:]

#         else:
#             return next_argument_(signature)

#         type_arguments = []
#         while arguments_signature:
#             type_, arguments_signature = next_argument(arguments_signature, force_read)
#             if isinstance(type_, InvalidType) and not force_read:
#                 return InvalidType(signature), ""

#             type_arguments.append(type_)

#         inner_type_arguments = []
#         while inner_arguments_signature:
#             type_, inner_arguments_signature = next_argument(inner_arguments_signature, force_read)
#             if isinstance(type_, InvalidType) and not force_read:
#                 return InvalidType(signature), ""

#             inner_type_arguments.append(type_)

#         return ClassOrInterfaceType(name, type_arguments, inner_name, inner_type_arguments), remaining[1:]

#     elif char == "[":
#         element_type, signature = next_argument(signature[1:], force_read)
#         if isinstance(element_type, ArrayType):
#             element_type.dimension += 1
#             array_type = element_type
#         else:
#             array_type = ArrayType(element_type)

#         return array_type, signature

#     elif char == "<":
#         _, middle, end = _find_enclosing(signature, "<", ">")
#         if not middle:
#             return InvalidType(end), ""
#         type_variables = []  # The type variables that we've found

#         while middle:
#             identifier, *remaining = middle.split(":")
#             upper_bound = None
#             additional_bounds = []
            
#             if not remaining:  # Can't just have an identifier on its own, this is probably invalid
#                 if not force_read:
#                     return InvalidType(signature), ""

#                 type_variables.append(next_argument(identifier, force_read)[0])
#                 break

#             while remaining:
#                 part_full = remaining.pop(0)  # For reference if it's invalid
#                 if not part_full:  # T::Ljava/util/List<Ljava/lang/String;>; <- thanks Java <3
#                     continue
#                 bound, part = next_argument(part_full, force_read)
#                 valid = isinstance(bound, ClassOrInterfaceType) or isinstance(bound, TypeVariable)
                
#                 if valid and upper_bound is None:
#                     upper_bound = bound
#                 elif valid:
#                     additional_bounds.append(bound)
                        
#                 if part or not remaining:  # Add this here, in case there is an invalid type, to preserve order
#                     type_variables.append(TypeParameter(identifier, upper_bound, additional_bounds))
#                     middle = ":".join([part] + remaining)
                        
#                 if not valid:
#                     if not force_read:
#                         return InvalidType(signature), ""

#                     type_variables.append(bound)  # InvalidType(part_full)
                        
#                 if part or not remaining:
#                     break

#         return TypeArgumentList(type_variables), end

#     elif char == "^":
#         argument, signature_ = next_argument(signature[1:], force_read)
#         if not isinstance(argument, ClassOrInterfaceType) and not isinstance(argument, TypeVariable):
#             return InvalidType(signature), ""
#         return argument, signature_

#     elif char == "T":
#         end_index = signature.find(";")
#         # I mean, this is a type variable right?
#         return TypeVariable(signature[1: end_index]), signature[end_index + 1:]

#     elif char == "*":
#         return Wildcard(), signature[1:]

#     elif char in ("+", "-"):
#         argument, signature = next_argument(signature[1:], force_read)
#         return Wildcard(**{("upper_bound" if char == "+" else "lower_bound"): argument}), signature

#     else:
#         # TODO: Keep searching until valid signature is found?
#         return InvalidType(signature), ""


# def parse_field_signature(
#         signature: str,
#         *,
#         force_read: bool = False,
#         do_raise: bool = True,
# ) -> BaseType:
#     """
#     Parses a field's signature.

#     :param signature: The signature to parse.
#     :param force_read: Force the already parsed field signature to be returned, even if there is an error.
#     :param do_raise: Raises an exception if an error occurs while parsing. Otherwise, an InvalidType is returned.
#     :return: The parsed signature.
#     """

#     if not force_read and not signature:
#         if do_raise:
#             raise ValueError("Signature is empty.")
#         return InvalidType(signature)

#     type_, remaining = next_argument(signature, force_read)
#     if not force_read:
#         # Check for trailing data
#         if remaining:
#             if do_raise:
#                 raise ValueError("Trailing data %r in signature." % remaining)
#             return InvalidType(signature)

#         # Check type is valid
#         if isinstance(type_, VoidType) or isinstance(type_, InvalidType) or isinstance(type_, TypeArgumentList):
#             if do_raise:
#                 raise TypeError("Invalid type argument %r found." % type_)
#             return InvalidType(signature)

#     return type_


# def parse_method_signature(
#         signature: str,
#         *,
#         force_read: bool = False,
#         do_raise: bool = True,
# ) -> Union[tuple[TypeArgumentList, tuple[BaseType, ...], BaseType, tuple[ClassOrInterfaceType, ...]], InvalidType]:
#     """
#     Parses a method signature.

#     :param signature: The signature to parse.
#     :param force_read: Force the already parsed method signature to be returned, even if there is an error.
#     :param do_raise: Raises an exception if an error occurs. Otherwise, returns an InvalidType.
#     :return: The parsed signature (type parameters, argument types, the return type and exception types).
#     """

#     if not force_read and not signature:
#         if do_raise:
#             raise ValueError("Signature is empty.")
#         return InvalidType(signature)

#     preceding, arguments_signature, remaining = _find_enclosing(signature, "(", ")")
    
#     # Find the type parameters, if necessary
#     if preceding:
#         type_parameters, preceding = next_argument(preceding, force_read)
#     else:
#         type_parameters = TypeArgumentList(())

#     # Find the argument types
#     argument_types = []
#     while arguments_signature:
#         type_, arguments_signature = next_argument(arguments_signature, force_read)
#         argument_types.append(type_)
#     argument_types = tuple(argument_types)
    
#     # Find the return type
#     return_type, remaining = next_argument(remaining, force_read)
    
#     # Find the exception types
#     if remaining:
#         exception_types = []
#         while remaining.startswith("^"):
#             type_, remaining = next_argument(remaining, force_read)
#             exception_types.append(type_)
#         exception_types = tuple(exception_types)
#     else:
#         exception_types = ()
    
#     # Verify everything is correct
#     if not force_read:
#         # Checking for leading / trailing data
#         if preceding:
#             if do_raise:
#                 raise ValueError("Leading data %r in signature." % preceding)
#             return InvalidType(signature)

#         if remaining:
#             if do_raise:
#                 raise ValueError("Trailing data %r in signature." % remaining)
#             return InvalidType(signature)

#         # Check we have a list for the type parameters
#         if not isinstance(type_parameters, TypeArgumentList):
#             if do_raise:
#                 raise TypeError("Expected %r for type parameters, found %r." % (TypeArgumentList, type_parameters))
#             return InvalidType(signature)

#         # Check the type parameters are actually type parameters
#         for type_parameter in type_parameters:
#             if not isinstance(type_parameter, TypeParameter):
#                 if do_raise:
#                     raise TypeError("Expected %r in type parameters, found %r." % (TypeParameter, type_parameter))
#                 return InvalidType(signature)
                
#         if arguments_signature is None:
#             if do_raise:
#                 raise ValueError("No argument types found.")
#             return InvalidType(signature)
            
#         for argument_type in argument_types:
#             if (
#                 isinstance(argument_type, VoidType) or 
#                 isinstance(argument_type, InvalidType) or 
#                 isinstance(argument_type, TypeParameter) or 
#                 isinstance(argument_type, TypeArgumentList)
#             ):
#                 if do_raise:
#                     raise TypeError("Invalid argument type %r found." % argument_type)
#                 return InvalidType(signature)
                
#         if isinstance(return_type, InvalidType) or isinstance(return_type, TypeParameter) or isinstance(return_type, TypeArgumentList):
#             if do_raise:
#                 raise TypeError("Invalid return type %r found." % return_type)
#             return InvalidType(signature)
                
#         for exception_type in exception_types:
#             if not isinstance(exception_type, ClassOrInterfaceType) and not isinstance(exception_type, TypeVariable):
#                 if do_raise:
#                     raise TypeError("Expected %r in exception types, found %r." % (ClassOrInterfaceType, exception_type))
#                 return InvalidType(signature)

#     return type_parameters, argument_types, return_type, exception_types


# def parse_class_signature(
#         signature: str,
#         *,
#         force_read: bool = True,
#         do_raise: bool = True,
# ) -> Union[tuple[TypeArgumentList, ClassOrInterfaceType, tuple[ClassOrInterfaceType, ...]], InvalidType]:
#     """
#     Parses a class signature.

#     :param signature: The signature to parse.
#     :param force_read: Force the already parsed method signature to be returned, even if there is an error.
#     :param do_raise: Raises an exception if an error occurs. Otherwise, returns an InvalidType.
#     :return: The parsed signature.
#     """

#     if not signature:
#         if do_raise:
#             raise ValueError("Signature is empty.")
#         return InvalidType(signature)

#     type_parameters, remaining = next_argument(signature)
#     if not isinstance(type_parameters, TypeArgumentList):
#         super_class_type = type_parameters
#         type_parameters = TypeArgumentList(())
#     else:
#         super_class_type, remaining = next_argument(remaining)

#     interface_types = []
#     while remaining:
#         type_, remaining = next_argument(remaining)
#         interface_types.append(type_)
#     interface_types = tuple(interface_types)

#     if not force_read:
#         # Check for trailing data
#         if remaining:
#             if do_raise:
#                 raise ValueError("Trailing data %r in signature." % remaining)
#             return InvalidType(signature)

#         # Check the type parameters are valid
#         for type_parameter in type_parameters:
#             if not isinstance(type_parameter, TypeParameter):
#                 if do_raise:
#                     raise TypeError("Expected %r in type parameters, found %r." % (TypeParameter, type_parameter))
#                 return InvalidType(signature)

#         # Check super class type is valid
#         if not isinstance(super_class_type, ClassOrInterfaceType):
#             if do_raise:
#                 raise TypeError("Expected %r in exception types, found %r." % (ClassOrInterfaceType, super_class_type))
#             return InvalidType(signature)

#         # Check interface types are valid
#         for interface_type in interface_types:
#             if not isinstance(interface_type, ClassOrInterfaceType):
#                 if do_raise:
#                     raise TypeError("Expected %r in interface types, found %r." % (ClassOrInterfaceType, interface_type))
#                 return InvalidType(signature)

#     return type_parameters, super_class_type, interface_types


# # def parse_any_signature(signature: str, dont_throw: bool = False, force_tuple: bool = False,
# #                         force_read: bool = True) -> Union[tuple["BaseType", ...], "BaseType"]:
# #     """
# #     Parses any signature.
# # 
# #     :param signature: The signature to parse.
# #     :param dont_throw: Don't throw an exception if an error occurs.
# #     :param force_tuple: Force the returned result to be a tuple, even if it is only one type.
# #     :param force_read: Return all already read type arguments if an error occurs.
# #     :return: The parsed signature.
# #     """
# # 
# #     original_signature = signature
# #     argument_types = []
# # 
# #     prev_signature = signature
# #     while signature:
# #         type_, signature = next_argument(signature)
# #         if isinstance(type_, InvalidType) or signature == prev_signature:
# #             if force_read:
# #                 argument_types.append(type_)
# #                 break
# #             if dont_throw:
# #                 if force_tuple:  # Lol
# #                     return InvalidType(original_signature),
# #                 return InvalidType(original_signature)
# #             raise ValueError("Invalid signature %r." % signature)
# # 
# #         prev_signature = signature
# #         argument_types.append(type_)
# # 
# #     if len(argument_types) == 1 and not force_tuple:
# #         return argument_types[0]
# #     return tuple(argument_types)
