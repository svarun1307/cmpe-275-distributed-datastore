from concurrent import futures
import time
import logging
import threading
import grpc
import sys
sys.path.append('./Gen')
import fileService_pb2
import fileService_pb2_grpc
_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def client():
    while True: 
        choice= int(input("What operation: 1. Upload 2. Download 3. Search 4. List File : "))
        if choice==1:
            channel = grpc.insecure_channel('192.168.43.74:9000')
            stub = fileService_pb2_grpc.FileserviceStub(channel)
            response = stub.getLeaderInfo(fileService_pb2.ClusterInfo(ip="192.168.43.2", port="9000", clusterName="akshay"))
            print(response.message)
        


if __name__ == '__main__':
    t3 = threading.Thread(target=client)
    t3.start()
    t3.join()
