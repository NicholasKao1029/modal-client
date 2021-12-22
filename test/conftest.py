import asyncio
import random
import typing

import grpc
import pytest
from modal import Session
from modal.client import Client
from modal.proto import api_pb2, api_pb2_grpc
from modal.session_singleton import set_session_singleton


class GRPCClientServicer(api_pb2_grpc.ModalClient):
    def __init__(self):
        self.requests = []
        self.done = False
        self.inputs = []
        self.outputs = []
        self.object_ids = {}

    async def ClientCreate(
        self,
        request: api_pb2.ClientCreateRequest,
        context: grpc.aio.ServicerContext,
    ) -> api_pb2.ClientCreateResponse:
        self.requests.append(request)
        client_id = "cl-123"
        return api_pb2.ClientCreateResponse(client_id=client_id)

    async def SessionCreate(
        self,
        request: api_pb2.SessionCreateRequest,
        context: grpc.aio.ServicerContext,
    ) -> api_pb2.SessionCreateResponse:
        self.requests.append(request)
        session_id = "se-123"
        return api_pb2.SessionCreateResponse(session_id=session_id)

    # async def ClientStop(self, request: api_pb2.ByeRequest, context: grpc.aio.ServicerContext) -> api_pb2.Empty:
    #    self.requests.append(request)
    #    self.done = True
    #    return api_pb2.Empty()

    async def ClientHeartbeat(
        self, request: api_pb2.ClientHeartbeatRequest, context: grpc.aio.ServicerContext
    ) -> api_pb2.Empty:
        self.requests.append(request)
        return api_pb2.Empty()

    async def SessionGetLogs(
        self, request: api_pb2.SessionGetLogsRequest, context: grpc.aio.ServicerContext
    ) -> typing.AsyncIterator[api_pb2.TaskLogs]:
        await asyncio.sleep(1.0)
        if self.done:
            yield api_pb2.TaskLogs(done=True)

    async def FunctionGetNextInput(
        self, request: api_pb2.FunctionGetNextInputRequest, context: grpc.aio.ServicerContext
    ) -> api_pb2.BufferReadResponse:
        return self.inputs.pop(0)

    async def FunctionOutput(
        self, request: api_pb2.FunctionOutputRequest, context: grpc.aio.ServicerContext
    ) -> api_pb2.BufferWriteResponse:
        self.outputs.append(request)
        return api_pb2.BufferWriteResponse(status=api_pb2.BufferWriteResponse.BufferWriteStatus.SUCCESS)

    async def SessionGetObjects(
        self, request: api_pb2.SessionGetObjectsRequest, context: grpc.aio.ServicerContext
    ) -> api_pb2.SessionGetObjectsResponse:
        return api_pb2.SessionGetObjectsResponse(object_ids=self.object_ids)


@pytest.fixture(scope="function")
async def servicer():
    servicer = GRPCClientServicer()
    port = random.randint(8000, 8999)
    servicer.remote_addr = "http://localhost:%d" % port
    server = grpc.aio.server()
    api_pb2_grpc.add_ModalClientServicer_to_server(servicer, server)
    server.add_insecure_port("[::]:%d" % port)
    await server.start()
    yield servicer
    await server.stop(0)


@pytest.fixture
def reset_session_singleton():
    yield
    set_session_singleton(None)
