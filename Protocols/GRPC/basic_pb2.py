# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: basic.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0b\x62\x61sic.proto\x12\x05greet\".\n\x0cHelloRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x10\n\x08greeting\x18\x02 \x01(\t\"\x1d\n\nHelloReply\x12\x0f\n\x07message\x18\x01 \x01(\t\"E\n\x0c\x44\x65layedReply\x12\x0f\n\x07message\x18\x01 \x01(\t\x12$\n\x07request\x18\x02 \x03(\x0b\x32\x13.greet.HelloRequest\"\x1f\n\x0e\x41verageRequest\x12\r\n\x05table\x18\x01 \x03(\x02\"\x1b\n\x0c\x41verageReply\x12\x0b\n\x03\x61vg\x18\x01 \x01(\x02\x32\xc0\x02\n\x07Greeter\x12\x32\n\x08SayHello\x12\x13.greet.HelloRequest\x1a\x11.greet.HelloReply\x12;\n\x0fParrotSaysHello\x12\x13.greet.HelloRequest\x1a\x11.greet.HelloReply0\x01\x12\x43\n\x15\x43hattyClientSaysHello\x12\x13.greet.HelloRequest\x1a\x13.greet.DelayedReply(\x01\x12>\n\x10InteractingHello\x12\x13.greet.HelloRequest\x1a\x11.greet.HelloReply(\x01\x30\x01\x12?\n\rAverageStream\x12\x15.greet.AverageRequest\x1a\x13.greet.AverageReply(\x01\x30\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'basic_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_HELLOREQUEST']._serialized_start=22
  _globals['_HELLOREQUEST']._serialized_end=68
  _globals['_HELLOREPLY']._serialized_start=70
  _globals['_HELLOREPLY']._serialized_end=99
  _globals['_DELAYEDREPLY']._serialized_start=101
  _globals['_DELAYEDREPLY']._serialized_end=170
  _globals['_AVERAGEREQUEST']._serialized_start=172
  _globals['_AVERAGEREQUEST']._serialized_end=203
  _globals['_AVERAGEREPLY']._serialized_start=205
  _globals['_AVERAGEREPLY']._serialized_end=232
  _globals['_GREETER']._serialized_start=235
  _globals['_GREETER']._serialized_end=555
# @@protoc_insertion_point(module_scope)
