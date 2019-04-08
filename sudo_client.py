from concurrent import futures
import time
# from timeit import default_timer as timer
import logging
import threading
import grpc
import sys
sys.path.append('./Gen')
import fileService_pb2
import fileService_pb2_grpc
from timeit import default_timer as timer

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

CHUNK_SIZE= 1024*1024

def get_file_chunks(filename):
	with open(filename, 'rb') as f:
		while True:
			piece = f.read(CHUNK_SIZE)
			if len(piece) == 0:
				return
			yield fileService_pb2.FileData(username='akshay', filename= filename,data=piece)

def save_chunks(chunks, filename):
	i=0
	for chunk in chunks:
		with open(filename+str(i), 'wb') as f:
			if data.get(filename,None)==None:
				data[filename]=[0]*2
			data[filename][0]+=1
			i=i+1
			f.write(chunk.data)
	args= (1, filename, i)
	mycursor.execute("Insert into chunk_data VALUES(%d , '%s',  %d)" %(1, filename, i))
	cnx.commit()
	cnx.close()
	

def save_chunks_to_file(chunks, filename):
	with open(filename, 'wb') as f:
		for chunk in chunks:
			f.write(chunk.data)

def client():
	while True: 
		choice= int(input("What operation: 1. Upload 2. Download 3. File Search 4. File List 5. File Delete : "))
		if choice==1:
			channel = grpc.insecure_channel('169.254.46.132:3000')
			fileName=input("FileName to be uploaded: ")
			# start = timer()
			start_time = time.time()
			chunk_generator= get_file_chunks(fileName)
			# time.sleep(1)
			# end = timer()
			# print(end-start)
			# print("Chunks generated in %s seconds" % (time.time() - start_time))
			print("Chunks generated in %s seconds" % (str((time.time() - start_time))))
			start_time = time.time()
			stub = fileService_pb2_grpc.FileserviceStub(channel)
			response = stub.UploadFile(chunk_generator)
			print("File Uploaded in - %s seconds" % (str(round(time.time() - start_time,10))))
			print(response)
		elif choice==2:
			channel = grpc.insecure_channel('169.254.46.132:3000')
			name= input("Name of file to download")
			start_time = time.time()
			stub = fileService_pb2_grpc.FileserviceStub(channel)
			res = stub.FileSearch(fileService_pb2.FileInfo(username="akshay", filename=name))
			if res.success:
				response = stub.DownloadFile(fileService_pb2.FileInfo(username="akshay", filename=name))
				print("Files downloaded in %s seconds" % (str(round(time.time() - start_time,10))))
				start_time = time.time()
				save_chunks_to_file(response, "downloads/"+name)
				print("Download chunks aggregated in %s seconds" % (str(round(time.time() - start_time,10))))
				print("File downloaded. ")
			else:
				print("File not found")
		elif choice==3:
			channel = grpc.insecure_channel('169.254.46.132:3000')
			name= input("Name of file to Search")
			stub = fileService_pb2_grpc.FileserviceStub(channel)
			response = stub.FileSearch(fileService_pb2.FileInfo(username="akshay", filename=name))
			print(response)
		elif choice==4:
			channel = grpc.insecure_channel('169.254.46.132:3000')
			name= input("Enter username: ")
			stub = fileService_pb2_grpc.FileserviceStub(channel)
			fileList = stub.FileList(fileService_pb2.UserInfo(username=name))
			# response = stub.DownloadFile(fileService_pb2.FileInfo(username="akshay", filename=name))
			print("File List. ", fileList)
		elif choice==5:
		   channel = grpc.insecure_channel('169.254.46.132:3000')
		   name= input("Name of file to Delete: ")
		   stub = fileService_pb2_grpc.FileserviceStub(channel)
		   res = stub.FileSearch(fileService_pb2.FileInfo(username="akshay", filename=name))
		   if res.success:
			   response= stub.FileDelete(fileService_pb2.FileInfo(username="akshay", filename=name))
			   print(response)
		   else:
			   print("file not found")


if __name__ == '__main__':
	t3 = threading.Thread(target=client)
	t3.start()
	t3.join()
