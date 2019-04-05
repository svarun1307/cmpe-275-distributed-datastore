from concurrent import futures
import time
import logging
from activeNodes import activeNodes
import threading
import sys
import grpc
from NodePing import Heartbeat
from FileOperations import FileService
sys.path.append('./Gen')
import heartbeat_pb2
import heartbeat_pb2_grpc
import fileService_pb2
import fileService_pb2_grpc

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
activeNodeObj= activeNodes()

def serve():
    leader=True
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    if sys.argv[1] != str(3000):
        leader=False
    serverAddress= '127.0.0.1:'+sys.argv[1]
    print("Server started on" +  sys.argv[1])
    heartbeat_pb2_grpc.add_HearBeatServicer_to_server(Heartbeat(), server)
    print(leader)
    fileService_pb2_grpc.add_FileserviceServicer_to_server(FileService(leader, serverAddress, activeNodeObj), server)
    server.add_insecure_port('127.0.0.1:'+sys.argv[1])
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
