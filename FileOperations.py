
from pickledbMetadata import pickledbMetadata
from databaseHandler import databaseHandler
from nodeSelect import nodeSelect
from activeNodes import activeNodes
import sys
sys.path.append('./Gen')
import hashlib
import heartbeat_pb2
import heartbeat_pb2_grpc

import fileservice_pb2_grpc as fileService_pb2_grpc
import fileservice_pb2 as fileService_pb2
from concurrent import futures

import psutil
import threading
import grpc
import io
import time
import pickledb

_ONE_DAY_IN_SECONDS = 60 * 60 * 24


class FileService(fileService_pb2_grpc.FileserviceServicer):
	def __init__(self, leader, serverAddress, activeNodeObj):
		self.leader = leader
		self.serverAddress = serverAddress
		self.nodeSelect = nodeSelect()
		self.activeNodeObj = activeNodes()
		self.databaseHandlerObj = databaseHandler()
		self.pickledbMetadataobj = pickledbMetadata(serverAddress)

	def UploadFile(self, request_iterator, context):
		print("--------")
		activeIpList = self.activeNodeObj.getActiveIpsDict()
		if self.leader.isLeader():
			print("here-----")
			chunk_id = 0
			for chunk in request_iterator:
				print("In iterator")
				username = chunk.username
				filename = chunk.filename
				metadata = self.pickledbMetadataobj.getFileData(username)
				if metadata and chunk_id == 0:
					if filename in metadata:
						return fileService_pb2.ack(success=True, message="File Already Present!")
				destination = self.nodeSelect.leastUtilizedNode()
				if destination == 9999:
					return fileService_pb2.ack(success=False, message="No active nodes!")
				if str(destination) == str(self.serverAddress):
					chunk_id += 1
					self.databaseHandlerObj.insertData(
						chunk.username, chunk.filename+str(chunk_id), chunk.data)
					self.broadcastMetadata(
						chunk.username, chunk.filename, str(chunk_id), str(destination))

				else:
					chunk_id += 1
					self.sendDataToDestination(chunk, destination, chunk_id)
			return fileService_pb2.ack(success=True, message="Saved data!")

		else:
			for request in request_iterator:
				self.databaseHandlerObj.insertData(
					request.username, request.filename+str(request.chunk_id), request.data)
				self.broadcastMetadata(request.username, request.filename, str(
					request.chunk_id), str(self.serverAddress))
				return fileService_pb2.ack(success=True, message="Data has been saved!")

	def DownloadFile(self, request_iterator, context):
		activeIpList = self.activeNodeObj.getActiveIpsDict()
		username = request_iterator.username
		filename = request_iterator.filename
		if(self.leader.isLeader()):
			metadata = self.pickledbMetadataobj.getData(username, filename)
			for item in metadata:
				if item[1] == self.serverAddress:
					fname = filename+str(item[0])
					result = self.databaseHandlerObj.getData(username, fname)
					yield fileService_pb2.FileData(username=result[0], filename=filename, data=result[2], chunk_id=int(item[0]))

				else:
					data = self.getDataFromNode(
						username, filename, item[0], item[1])
					for d in data:
						yield d

		else:
			result = self.databaseHandlerObj.getData(username, filename)
			chunk_id = request_iterator.sequence_no
			yield fileService_pb2.FileData(username=result[0], filename=result[1][:-len(chunk_id)], data=result[2], chunk_id=int(chunk_id))

	def getDataFromNode(self, username, filename, chunk_id, destination):
		channel = grpc.insecure_channel(destination)
		channel2 = self.activeNodeObj.getActiveIpsDict()[destination]
		stub = fileService_pb2_grpc.FileserviceStub(channel2)
		response = stub.DownloadFile(fileService_pb2.FileInfo(
			username=username, filename=str(filename+chunk_id), sequence_no=str(chunk_id)))
		return response
		# for r in response:
		#    yield r

	def sendDataToDestination(self, chunk, node, chunk_id):
		channel = self.activeNodeObj.getActiveIpsDict()[node]
		stub = fileService_pb2_grpc.FileserviceStub(channel)
		chunk_generator = self.getChunksinStream(chunk, chunk_id)
		response = stub.UploadFile(chunk_generator)

	def getChunksinStream(self, chunk, chunk_id):
		end = sys.getsizeof(chunk.data)
		start = 0
		while True:
			data = chunk.data[start:end]
			if end > sys.getsizeof(chunk.data):
				break
			start = end
			end = end+sys.getsizeof(chunk.data)
			yield fileService_pb2.FileData(username=chunk.username, filename=chunk.filename, data=data, chunk_id=chunk_id)

	def broadcastMetadata(self, username, filename, chunk_id, destination):
		activeIpList = self.activeNodeObj.getActiveIpsDict()
		for ip, channel in activeIpList.items():
			stub = fileService_pb2_grpc.FileserviceStub(channel)
			response = stub.metadataUpdate(fileService_pb2.metadataInfo(
				username=username, filename=filename, chunk_id=chunk_id, destination=destination))

	def metadataUpdate(self, request, context):
		self.pickledbMetadataobj.insertData(
			request.username, request.filename, request.chunk_id, request.destination)
		return fileService_pb2.ack(success=True, message="MetaData has been saved!")

	def getClusterStats(self, request, context):
		c, d, u = self.nodeSelect.getAvg()
		return fileService_pb2.ClusterStats(cpu_usage=str(c), disk_space=str(d), used_mem=str(u))

	def FileSearch(self, request, context):
		username = request.username
		filename = request.filename
		metadata = self.pickledbMetadataobj.getFileData(username)
		if metadata:
			if filename in metadata:
				return fileService_pb2.ack(success=True, message="File Found!")
		return fileService_pb2.ack(success=False, message="File not found")
	
	def FileList(self, request, context):
		username = request.username
		if not username:
			return fileService_pb2.FileListResponse(Filenames="")
		fileList = self.pickledbMetadataobj.getFileList(username)
		return fileService_pb2.FileListResponse(Filenames=fileList)

	def FileDelete(self, request, context):
	   username= request.username
	   filename= request.filename
	   if self.leader:
		   metadata= self.pickledbMetadataobj.getData(username,filename)
		   for item in metadata:
			   if item[1]==self.serverAddress:
				   fname= filename+str(item[0])
				#    self.databaseHandlerObj.deleteData(username,fname)

			   else:
				   self.deleteDataFromNode(username, filename, item[0], item [1])
		   self.pickledbMetadataobj.deleteData(username,filename)
		   return fileService_pb2.ack(success=True, message="Data deleted!")
	   else:
		#    self.databaseHandlerObj.deleteData(username,filename)
		   self.pickledbMetadataobj.deleteData(str(username),filename[:-len(request.sequence_no)])
		   return fileService_pb2.ack(success=True, message="Data deleted!")

	def deleteDataFromNode(self, username, filename, chunk_id, destination):
	   channel = grpc.insecure_channel(destination)
	   channel2= self.activeNodeObj.getActiveIpsDict()[destination]
	   stub = fileService_pb2_grpc.FileserviceStub(channel2)
	   response= stub.FileDelete(fileService_pb2.FileInfo(username=username, filename=str(filename+chunk_id),sequence_no=chunk_id))
	   return response