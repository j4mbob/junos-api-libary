#!/usr/bin/env python3
# Juniper API module

try:

	import argparse
	import json
	import sys
	import logging
	from lxml import etree
	from jnpr.junos import exception as EzErrors
	from jnpr.junos import Device
	from jnpr.junos.utils.config import Config
	
except ImportError as err:
	print('error importing modules: ' + str(err) )
	exit(1)

class Junos():

	def __init__(self,junos_platform,debug):
		self.junos_platform = junos_platform
		self.debug = debug
		self.logger = logging.getLogger('juniper_junos')
		
		if self.debug:
			self.logger.setLevel(logging.DEBUG)
		
		ch = logging.StreamHandler()
		ch.setLevel(logging.DEBUG)
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		ch.setFormatter(formatter)
		self.logger.addHandler(ch)

		self.junos_factory()

	def junos_factory(self):
		self.logger.debug('platform: ' + self.junos_platform) 

		try:
			self.junos_json =  'api-' + self.junos_platform + '.json'
			with open(self.junos_json, 'r') as f:
				self.logger.debug('loading ' + self.junos_json + 'as target api json schema')
				api = json.load(f)
		except Exception as err:
			print(err)
			sys.exit(1)

		self.host = api['hostname']
		self.port = api['port']
		self.username = api['username']
		self.ssh_key = api['sshkey']

		self.logger.debug(api)

		device_factory = Device(host=self.host, port=self.port,user=self.username,ssh_private_key_file=self.ssh_key)

		try:
			device_factory.open()
		except Exception.ConnectError as err:
			print("Cannot connect to device: {0}".format(err))
			sys.exit(1)
		except Exception as err:
			print(err)
			sys.exit(1)

		self.jfactory = device_factory
		self.logger.debug(self.jfactory.facts)
		return self.jfactory

	def get_junos_config(self,xml_filter,output_format):
	
		rpc_output = self.jfactory.rpc.get_config(filter_xml=xml_filter,options={'format': output_format})
		
		self.jfactory.close()

		return rpc_output

	def call_junos_rpc(self,command):

		rpc_output = self.jfactory.display_xml_rpc(command,format='text')
		print(rpc_output)
		
		self.jfactory.close()

		return rpc_output

	def set_junos_config(self,payload):

		jfactory_config = Config(self.jfactory)

		try:
			load_output = etree.tostring(jfactory_config.load(payload), encoding='unicode')
			self.logger.debug(load_output)
			commit_output = jfactory_config.commit()
			self.jfactory.close()

			return load_output

		except EzErrors.RpcError as err:
			print(err)
			sys.exit(1)
		except EzErrors.ConfigLoadError as err:
			print(err)
			sys.exit(1)
		except Exception as err:
			print(err)
			sys.exit(1)
