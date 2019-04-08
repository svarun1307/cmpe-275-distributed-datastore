from concurrent import futures
import sys
import psutil
import threading
import grpc
import time
import random
from activeNodes import activeNodes
sys.path.append('./Gen')
import heartbeat_pb2
import heartbeat_pb2_grpc
_ONE_DAY_IN_SECONDS = 60 * 60 * 24

activeNodeObj = activeNodes()
class nodeSelect():
	def __init__(self):
		self.dummy= []
		activeNodeObj.channelRefresh()
		self.activeIpList = activeNodeObj.getActiveIpsDict()
		print(self.activeIpList)
		
	def leastUtilizedNode(self):
		min= float("-inf")
		self.dummy= []
		for ip, channel in self.activeIpList.items():
			stub = heartbeat_pb2_grpc.HearBeatStub(channel)
			response = stub.isAlive(heartbeat_pb2.NodeInfo())
			self.dummy.append((response.disk_space, response.used_mem, response.cpu_usage, ip))
			
		if len(self.dummy)==0:
			return 9999

		a=sorted(self.dummy,key=lambda x: (x[0], x[1]))
		#self.dummy.sort(key=lambda x: (x[0], x[1]))
		return a[random.randint(0,len(a)-1)][3]

	def getAvg(self):
		count,cpu_usage,disk_space,used_mem= 0,0,0,0
		for ip, channel in self.activeIpList.items():
			stub = heartbeat_pb2_grpc.HearBeatStub(channel)
			response = stub.isAlive(heartbeat_pb2.NodeInfo())
			disk_space += float(response.disk_space)
			used_mem += float(response.used_mem)
			cpu_usage += float(response.cpu_usage)
			count+=1
		if count == 0:
			return (0,0,0)
		return (disk_space/count, used_mem/count, cpu_usage/count)

if __name__ == '__main__':
	n= nodeSelect()
