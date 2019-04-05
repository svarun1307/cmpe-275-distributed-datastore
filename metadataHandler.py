import json

class metadataHandler():
	def __init__(self, serverAddress):
		self.file= serverAddress[-4]+'.json'

	def insertData(self, data):
		readfile = open(self.file, "r")
		data_read = json.load(readfile)
		if "user_1" in data_read:
			files= data_read["user_1"]
			if "files" in data_read:
				#tmp =d["pagar"]
				#data_read["pagar"]= "ruhi"
				writefile = open(self.file, "w")
				files["user_1"]= "ruhi"
				json.dump(data_read,writefile)
		else: 
			appendfile = open(self.file, "w")
			data_read["akshay"]= "ruhi"
			json.dump(data_read,appendfile)
		
if __name__ == '__main__':
	obj= metadataHandler('metadata')
	obj.insertData("Pagar")
