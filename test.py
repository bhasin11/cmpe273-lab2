import requests, re, urllib
import ast
import operator
from spyne import Application, rpc, ServiceBase, Integer, Unicode

from spyne import Iterable
from spyne.protocol.http import HttpRpc
from spyne.protocol.json import JsonDocument
from spyne.decorator import srpc
from spyne.server.wsgi import WsgiApplication


class findCrime(ServiceBase):
	@srpc(Unicode, Unicode, Unicode, _returns=Iterable(Unicode))
	def checkcrime(lat, lon, radius):
		site = "https://api.spotcrime.com/crimes.json?lat="+lat+"&lon="+lon+"&radius="+radius+"&key=."
		u = urllib.urlopen(site)
		text = u.read()
		#u = requests.get(site)
		#text = u.json()
		i=0
		lines = text.split('{')
		totalLength=len(lines)

		typeDictionary={}
		addressDictionary={}
		timeDictionary={}

		for line in lines:
			if(i>=2):
				line = '{'+line
				stringLength = len(line)-1
				if(i==totalLength-1):
					stringLength=stringLength-1
				line=line[:stringLength]

				user= ast.literal_eval(line)
				crime=user['type']
				address=user['address']
				pp = address.split('BLOCK BLOCK ')
				if(len(pp)>1):
					address=pp[1]
				else:
					pp = address.split('BLOCK ')
					if(len(pp)>1):
						address=pp[1]

				time=user['date']
				time = time[9:]

				if(typeDictionary.has_key(crime)):
					value = typeDictionary[crime]
					typeDictionary[crime]=value+1
					#print value
				else:
					typeDictionary[crime]=1;

				if(addressDictionary.has_key(address)):
					value = addressDictionary[address]
					addressDictionary[address]=value+1
					#print value
				else:
					parts = address.split('OF')

					if(len(parts)>1):
						parts[1]=parts[1].strip();
						if(addressDictionary.has_key(parts[1])):
							value = addressDictionary[parts[1]]
							addressDictionary[parts[1]]=value+1
							#print value
						else:
							addressDictionary[parts[1]]=1

					else:
						parts = address.split('&')
						if(len(parts)>1):
							parts[0]=parts[0].strip()

							if(addressDictionary.has_key(parts[0])):
								value = addressDictionary[parts[0]]
								addressDictionary[parts[0]]=value+1
								#print value
							else:
								addressDictionary[parts[0]]=1

							parts[1]= parts[1].strip()

							if(addressDictionary.has_key(parts[1])):
								value = addressDictionary[parts[1]]
								addressDictionary[parts[1]]=value+1
								#print value
							else:
								addressDictionary[parts[1]]=1
						else:
							addressDictionary[address]=1

				if(timeDictionary.has_key(time)):
					value = timeDictionary[time]
					timeDictionary[time]=value+1
					#print time
				else:
					timeDictionary[time]=1;

			i=i+1

		totalCrimes=totalLength-2

		#print typeDictionary
		#print addressDictionary

		threeAddresses = sorted(addressDictionary.items(), key=operator.itemgetter(1),reverse=True)
		threeAddresses= threeAddresses[:3]

		xx = []
		for k, v in threeAddresses:
			xx.append(k)

		#print threeAddresses
		print xx
		#print timeDictionary

		outputTime={
				"12:01am-3am" : 0,
				"3:01am-6am" : 0,
				"6:01am-9am" : 0,
				"9:01am-12noon" : 0,
				"12:01pm-3pm" : 0,
				"3:01pm-6pm" : 0,
				"6:01pm-9pm" : 0,
				"9:01pm-12midnight" : 0
		}

		for item in timeDictionary:
			hrs = item.split(':')
			zone = item.split()
			mins = zone[0].split(':')
			hours= int (hrs[0])
			minutes = int (mins[1])

			if (hours>=12 and minutes>10) or (hours<3 and minutes>0) or (hours==3 and minutes==0) :
				if zone[1] == 'AM':
					#print '1'
					value = outputTime['12:01am-3am']
					outputTime['12:01am-3am'] =value+1
				else:
					#print '2'
					value = outputTime['12:01pm-3pm']
					outputTime['12:01pm-3pm'] =value+1

			elif( (hours>=3 and minutes>0) or (hours<6 and minutes>0) or (hours==6 and minutes==0)):
				if(zone[1] == 'AM'):
					#print '3'
					value = outputTime['3:01am-6am']
					outputTime['3:01am-6am'] =value+1
				else:
					#print '4'
					value = outputTime['3:01pm-6pm']
					outputTime['3:01pm-6pm'] =value+1

			elif( (hours>=6 and minutes>0) or (hours<9 and minutes>0) or (hours==9 and minutes==0)):
				if(zone[1] == 'AM'):
					#print '5'
					value = outputTime['6:01am-9am']
					outputTime['6:01am-9am'] =value+1
				else:
					#print '6'
					value = outputTime['6:01pm-9pm']
					outputTime['6:01pm-9pm'] =value+1

			elif( (hours>=9 and minutes>0) or (hours<12 and minutes>0) ):
				if(zone[1] == 'AM'):
					#print '7'
					value = outputTime['9:01pm-12midnight']
					outputTime['9:01am-12noon'] =value+1
				else:
					#print '8'
					value = outputTime['9:01pm-12midnight']
					outputTime['9:01pm-12midnight'] =value+1

			else:
				if(zone[1]=='AM'):
					#print '9'
					value = outputTime['9:01pm-12midnight']
					outputTime['9:01pm-12midnight'] = value + 1
				else:
					#print '10'
					value = outputTime['9:01am-12noon']
					outputTime['9:01am-12noon'] = value + 1

		yield ({'total_crimes': totalCrimes, 'the_most_dangerous_streets': xx, 'crime_type_count':typeDictionary, 'event_type_count' : outputTime})


application = Application([findCrime],
	tns='spyne.determinecrime',
	in_protocol=HttpRpc(validator='soft'),
	out_protocol=JsonDocument()
)

if __name__ == '__main__':
	from wsgiref.simple_server import make_server

	wsgi_app = WsgiApplication(application)
	server = make_server('0.0.0.0', 8000, wsgi_app)
	server.serve_forever()