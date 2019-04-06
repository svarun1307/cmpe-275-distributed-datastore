from concurrent import futures
import sys
import psutil
import threading
import grpc
import time
sys.path.append('./Gen')
import heartbeat_pb2
import heartbeat_pb2_grpc
_ONE_DAY_IN_SECONDS = 60 * 60 * 24



class Heartbeat(heartbeat_pb2_grpc.HearBeatServicer):
    def _init_(self):
         self.status=200

    def isAlive(self, request, context):
         cpu_usage = str(psutil.cpu_percent())
         disk_space = str(psutil.virtual_memory()[2])
         used_mem = str(psutil.disk_usage('/')[3])
         info = heartbeat_pb2.Stats(cpu_usage = cpu_usage, disk_space = disk_space, used_mem = used_mem)
         return info

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    heartbeat_pb2_grpc.add_HearBeatServicer_to_server(Heartbeat(), server)
    server.add_insecure_port('[::]:'+sys.argv[1])
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)

def client():
	with grpc.insecure_channel('localhost:3000') as channel:
		stub = heartbeat_pb2_grpc.HearBeatStub(channel)
		response = stub.isAlive(heartbeat_pb2.NodeInfo())
		print("Greeter client received: " + response.used_mem)
        

if __name__ == '__main__':
    t1 = threading.Thread(target=serve)
    #t2 = threading.Thread(target=client)
    t1.start()
    #time.sleep(2)
    #t2.start()
    t1.join()
    #t2.join()
