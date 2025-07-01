#! /usr/bin/python
import suds
import logging

clie = suds.client.Client('https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantes?wsdl')
clie.set_options(port='BasicHttpBinding_IMyService')
print(clie)
logging.basicConfig(level=logging.DEBUG, filename="suds.log")
logging.getLogger('suds.client').setLevel(logging.DEBUG)
logging.getLogger('suds.transport').setLevel(logging.DEBUG)
logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

print(dir(clie.service.autorizacionComprobante))
print(dir(clie.service.autorizacionComprobante('0210201701099218002100120050030000343801234567819')))