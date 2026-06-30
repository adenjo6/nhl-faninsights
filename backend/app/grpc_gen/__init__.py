"""Generated gRPC stubs for prospects.v1.

Source of truth: proto/prospects/v1/prospects.proto.
Regenerate with `buf generate` from the proto/ directory (emits both the Go
stubs for prospect-service and the Python stubs here).

Import gotcha: the grpc-generated ``prospects_pb2_grpc.py`` resolves its sibling
with an absolute import rooted at the proto package
(``from prospects.v1 import prospects_pb2``). Putting this directory on
``sys.path`` lets that import succeed. Consumers must therefore import the stubs
through the top-level ``prospects.v1`` namespace (NOT ``app.grpc_gen.prospects.v1``)
so the protobuf descriptors are registered exactly once — importing under two
distinct module names double-registers them and raises at import time.
"""
import os
import sys

_GEN_DIR = os.path.dirname(__file__)
if _GEN_DIR not in sys.path:
    sys.path.insert(0, _GEN_DIR)
