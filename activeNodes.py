import os
import sys
import glob
import psutil
import threading
import grpc
import time
import pickledb
sys.path.append('./Gen')
import heartbeat_pb2
import heartbeat_pb2_grpc


class activeNodes():

	def __init__(self):
		self.ip_list=[]
		self.channel_ip_map={}
		self.reverse_map={}

	def returnIPList(self):
		with open("valid_ip.txt","r") as ins:
			for line in ins:
				self.ip_list.append(line.strip())

	def isChannelAlive(self, channel):
		# try:
		# 	grpc.channel_ready_future(channel).result(timeout=1)
		# except grpc.FutureTimeoutError:
		# 	return False
		return True

	def createChannels(self):
		for ip in self.ip_list:
		# 	if(self.channel_ip_map.get(ip,None) != None):
		# 		if(self.isChannelAlive(self.channel_ip_map[ip])):
		# 			print("alive for "+ip)
		# 			continue
		# 		else:
		# 			self.ip_list.remove(ip)
		# 			del self.channel_ip_map[ip]
		# 	else:
			channel= grpc.insecure_channel(''+ip)
			if self.isChannelAlive(channel):
				self.channel_ip_map[ip]=channel
				self.reverse_map[channel]=ip
			else:
				continue


	def channelRefresh(self):
		#while True:
		self.ip_list=[]
		self.channel_ip_map={}
		self.returnIPList()
		self.createChannels()
		#time.sleep(3)

	

	def getActiveIpsDict(self):
		self.channelRefresh()
		return self.channel_ip_map
	
    
if __name__ == '__main__':
	a= activeNodes()
	a.channelRefresh()