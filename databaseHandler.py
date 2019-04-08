from pymongo import MongoClient

class databaseHandler():
	"""docstring for ClassName"""
	def __init__(self):
		self.client = MongoClient('localhost', 27017)
		self.db = self.client['cmpe275']
		self.collection = self.db['ProjectData']
		
	def insertData(self,username, filename, data):
		mydict = { "username": username, "filename": filename ,"data" :data }
		x= self.collection.insert_one(mydict)
		print(x)
		
	def getData(self,username, filename):
		myquery = {"filename": filename, "username":username}
		mydoc = self.collection.find(myquery)
		for x in mydoc:
			return (x["username"], x["filename"], x["data"])
	
	def deleteData(self, username, filename):
		myquery = {"filename": filename, "username":username}
		mydoc = self.collection.delete_many(myquery)
		print(mydoc.deleted_count)


if __name__ == '__main__':
	obj = databaseHandler()
	obj.getData("akshay", "ruhi.jpg1")