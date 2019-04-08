from concurrent import futures
import time
import logging
from activeNodes import activeNodes
from threading import Thread
import sys
import grpc
from NodePing import Heartbeat
from FileOperations import FileService
sys.path.append('./Gen')
import heartbeat_pb2
import heartbeat_pb2_grpc
import fileservice_pb2_grpc as fileService_pb2_grpc
import fileservice_pb2 as fileService_pb2
from leaderbackground import TestObj
from state import State
_ONE_DAY_IN_SECONDS = 60 * 60 * 24
activeNodeObj= activeNodes()


"""
Thread function to check Leader
"""

state=State(False)
mainLeader = None
superNodeIp = "192.168.0.9:9000"

def threaded_function(a):
    global superNodeIp
    global mainLeader
    print("Argument",a)
    port = ""
    partners = [] #,"168.254.46.132:3000"]
    self_node = '192.168.0.21:2000'
    o = TestObj(self_node, partners)
    n = 0
    old_value = -1
    informSuperNode(self_node)
    while True:
        
        #print('Current Counter value:', old_value)
        print(" is Leader : ",mainLeader)
        time.sleep(0.5)
        if o.getCounter() != old_value:
            old_value = o.getCounter()
            print('Current Counter value:', old_value)
        if o._getLeader() is None:
            mainLeader = self_node
            continue
        
        # if n < 2000:
        if n < 20: 
            if (port == 2000):
                o.addValue(10, n)
        n += 1
        #if n % 20 == 0:
        print("thread function-----"+o._getLeader())
        mainLeader = o._getLeader()
        if state.changeState(mainLeader == self_node) :
            informSuperNode(self_node)
            continue


def informSuperNode(self_node):
    temp = self_node.split(":")[0]
    try:
        channel = grpc.insecure_channel(superNodeIp)
        if isChannelAlive(channel):
            stub = fileService_pb2_grpc.FileserviceStub(channel)
            response = stub.getLeaderInfo(fileService_pb2.ClusterInfo(ip=str(temp), port="3000", clusterName="Saket"))
            print(response.message)
        else:
            raise
    except Exception as e:
        print(e)
            

def isChannelAlive(channel):
		try:
			grpc.channel_ready_future(channel).result(timeout=1)
		except grpc.FutureTimeoutError:
			return False
		return True

def serve():
    global mainLeader
    cmd_host = "192.168.0.21"
    serverAddress= cmd_host+':'+sys.argv[1]
    print("Server started on" +  sys.argv[1])
    thread = Thread(target = threaded_function, args = (sys.argv[1], ))
    print("System args",sys.argv[1])
    thread.start()
    leader=False
    while not mainLeader:
        pass
    else:
        leader=(cmd_host==mainLeader.split(":")[0])
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1000))
    heartbeat_pb2_grpc.add_HearBeatServicer_to_server(Heartbeat(), server)
    # if sys.argv[1] == str(3000):
    #     state.changeState(True)
    # else:
    #     state.changeState(False)

    fileService_pb2_grpc.add_FileserviceServicer_to_server(FileService(state, serverAddress, activeNodeObj), server)
    server.add_insecure_port(cmd_host+":"+sys.argv[1])
    #time.sleep(30)
    print("Current leader is ",mainLeader)
    server.start()
    
    #thread.join()
    try:
        while True:
            
            time.sleep(_ONE_DAY_IN_SECONDS)

            #if mainLeader:
            #    print("Current Main leader is ",mainLeader)
            #else:
            #    print("not up")
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    print("Mian start here")
    serve()
    # print(superNodeIp)
    # channel = grpc.insecure_channel(superNodeIp)
    # stub = fileService_pb2_grpc.FileserviceStub(channel)
    # response = stub.getLeaderInfo(fileService_pb2.ClusterInfo(ip=str("192.168.43.81"), port="3000", clusterName="Saket"))
    # print(response.message)
    # try:
    #     while True:
            
    #         time.sleep(_ONE_DAY_IN_SECONDS)

    #         #if mainLeader:
    #         #    print("Current Main leader is ",mainLeader)
    #         #else:
    #         #    print("not up")
    # except KeyboardInterrupt:
    #     pass        


# from concurrent import futures
# import time
# import logging
# from activeNodes import activeNodes
# import threading
# import sys
# import grpc
# from NodePing import Heartbeat
# from FileOperations import FileService
# sys.path.append('./Gen')
# import heartbeat_pb2
# import heartbeat_pb2_grpc
# import fileService_pb2
# import fileService_pb2_grpc

# _ONE_DAY_IN_SECONDS = 60 * 60 * 24
# activeNodeObj= activeNodes()

# def serve():
#     leader=True
#     server = grpc.server(futures.ThreadPoolExecutor(max_workers=1000))
#     if sys.argv[1] != str(3000):
#         leader=False
#     serverAddress= '127.0.0.1:'+sys.argv[1]
#     print("Server started on" +  sys.argv[1])
#     heartbeat_pb2_grpc.add_HearBeatServicer_to_server(Heartbeat(), server)
#     fileService_pb2_grpc.add_FileserviceServicer_to_server(FileService(leader, serverAddress, activeNodeObj), server)
#     server.add_insecure_port('127.0.0.1:'+sys.argv[1])
#     server.start()
#     try:
#         while True:
#             time.sleep(_ONE_DAY_IN_SECONDS)
#     except KeyboardInterrupt:
#         server.stop(0)


# if __name__ == '__main__':
#     serve()
