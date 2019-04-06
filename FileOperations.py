from concurrent import futures
import sys
import psutil
import threading
import grpc
import io
import time
import pickledb 
sys.path.append('./Gen')
import fileService_pb2
import fileService_pb2_grpc
import heartbeat_pb2_grpc
import heartbeat_pb2
import yaml
import threading
import hashlib
from activeNodes import activeNodes
from nodeSelect import nodeSelect
from databaseHandler import databaseHandler
from pickledbMetadata import pickledbMetadata
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

chunk_id=0

class FileService(fileService_pb2_grpc.FileserviceServicer):
    def __init__(self, leader, serverAddress,activeNodeObj):
        self.leader= leader
        self.serverAddress= serverAddress
        self.nodeSelect= nodeSelect()
        self.activeNodeObj=activeNodes()
        self.databaseHandlerObj= databaseHandler()
        self.pickledbMetadataobj=pickledbMetadata(serverAddress)

    
    def UploadFile(self, request_iterator, context):
        global chunk_id
        print(self.leader)
        activeIpList = self.activeNodeObj.getActiveIpsDict()
        if self.leader:
            print("I am the leader")
            chunk_id=0
            for chunk in request_iterator:
                print("chunk"+chunk.username)
                username= chunk.username
                filename = chunk.filename
                destination= self.nodeSelect.leastUtilizedNode()
                if destination==9999:
                    return fileService_pb2.ack(success=False, message="No active nodes!")
                if str(destination)==str(self.serverAddress):
                    print("data stored on primary")
                    chunk_id+=1
                    print("Active IP List:")
                    ##metadata broadcast
                    self.databaseHandlerObj.insertData(chunk.username, chunk.filename+str(chunk_id), chunk.data)
                    self.broadcastMetadata(chunk.username, chunk.filename, str(chunk_id), str(destination))

                else:
                    chunk_id+=1
                    print(chunk_id)
                    self.sendDataToDestination(chunk, destination, chunk_id)
                    print("Active IP List:")
                    for ip in activeIpList:
                        print(ip)
                        #pickledbMetadataobj.insertData(username,)


            return fileService_pb2.ack(success=True, message="Saved data!")

        else:
            for request in request_iterator:
                print("data stored on"+request.username)
                self.databaseHandlerObj.insertData(request.username, request.filename+str(request.chunk_id), request.data)
                self.broadcastMetadata(request.username, request.filename, str(request.chunk_id), str(self.serverAddress))
                return fileService_pb2.ack(success=True, message="Data has been saved!")

    def DownloadFile(self, request_iterator , context):
        activeIpList=self.activeNodeObj.getActiveIpsDict()
        username=request_iterator.username
        filename=request_iterator.filename
        if(self.leader):
            print("I am the leader")
            metadata= self.pickledbMetadataobj.getData(username,filename)
            print(metadata)
            for item in metadata:
                if item[1]==self.serverAddress:
                    print("heloo")
                else:
                    data= self.getDataFromNode(username, filename, item[0], item [1])
                    for d in data:
                        yield d
                    
        else:
            result= self.databaseHandlerObj.getData(username,filename)
            chunk_id= request_iterator.sequence_no
            yield fileService_pb2.FileData(username=result[0], filename= result[1][:-len(chunk_id)], data=result[2], chunk_id=int(chunk_id))

    def getDataFromNode(self, username, filename, chunk_id, destination):
        channel = grpc.insecure_channel(destination)
        channel2= self.activeNodeObj.getActiveIpsDict()[destination]
        stub = fileService_pb2_grpc.FileserviceStub(channel2)
        response= stub.DownloadFile(fileService_pb2.FileInfo(username=username, filename=str(filename+chunk_id), sequence_no=str(chunk_id)))
        print(response)
        return response
        #for r in response:
        #    yield r


    def sendDataToDestination(self, chunk, node, chunk_id):
        channel= self.activeNodeObj.getActiveIpsDict()[node]
        stub = fileService_pb2_grpc.FileserviceStub(channel)
        chunk_generator= self.getChunksinStream(chunk, chunk_id)
        response = stub.UploadFile(chunk_generator)

    def getChunksinStream(self,chunk, chunk_id):
        end= sys.getsizeof(chunk.data)
        start =0
        while True:
            data= chunk.data[start:end]
            if end>sys.getsizeof(chunk.data):
                break
            start=end
            end=end+sys.getsizeof(chunk.data)
            yield fileService_pb2.FileData(username=chunk.username, filename= chunk.filename,data=data, chunk_id=chunk_id)

    def broadcastMetadata(self, username, filename, chunk_id, destination):
        activeIpList = self.activeNodeObj.getActiveIpsDict()
        for ip,channel in activeIpList.items():
            stub= fileService_pb2_grpc.FileserviceStub(channel)
            response= stub.metadataUpdate(fileService_pb2.metadataInfo(username=username, filename=filename, chunk_id=chunk_id, destination=destination))
            print(response)

    def metadataUpdate(self, request, context):
        self.pickledbMetadataobj.insertData(request.username, request.filename, request.chunk_id, request.destination)
        return fileService_pb2.ack(success=True, message="MetaData has been saved!")

    def isChannelAlive(self, channel):
        try:
            grpc.channel_ready_future(channel).result(timeout=1)
        except grpc.FutureTimeoutError:
            #print("Connection timeout. Unable to connect to port ")
            return False
        return True