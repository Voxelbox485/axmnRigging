from pymel.core import *
import utils
import buildRig
class chain(buildRig.rig):
	'''Options:
	parent

	'''
	# def __init__(self):
	# 	pass

	# 	self.joints = self.fitNode.joints.get()
	# 	assert len(self.joints) == 3, 'Wrong amount of input joints: %s (3 required)'  % len(self.joints)
	# 	self.start, self.mid, self.end = self.joints

	# 	# ####

	# @gShowProgress(end=100)
	def __init__(self, fitNode=None, rigNode=None):

		if fitNode is None and rigNode is None:
			raise Exception('No data specified.')

		elif fitNode is None:
			self.rigNode = rigNode
			# Put any attributes needed for initialized rigs here

		else:

			# Initialize rigNode
			# Error Check:
			
			# Convert string input to PyNode if neccessary
			if isinstance(fitNode, str):
				fitNode = ls(fitNode)[0]

			if fitNode.rigType.get() != 'chain':
				raise Exception('Incorrect rig type: %s' % fitNode.rigType.get())

			self.offsetCtrls = []
			self.crvs = []

			buildRig.rig.__init__(self, fitNode)


			# fitNode attributes

			jointsList = 		self.fitNode.jointsList.get()
			fkShapes = 			self.fitNode.fkShapes.get()
			ikShapes = 			self.fitNode.ikShapes.get()
			useIK = 			self.fitNode.offsets.get()
			multiChain = 0
			if hasAttr(self.fitNode, 'multiChain'):
				multiChain = 		self.fitNode.multiChain.get()

			# Move rigGroup
			xform(self.rigGroup, ws=1, m=xform(jointsList[0], q=1, ws=1, m=1))


			# Mirroring
			if self.fitNode.side.get() == 2:
				mirror=True
			else:
				mirror=False

			if hasAttr(self.fitNode, 'bind'):
				doBind = self.fitNode.bind.get()
			else:
				doBind = True


			# partition into groups based on input joints and attach rignode attribute to all
			partitions = []
			if multiChain:
				# Find each top joint
				roots = []
				for jnt in jointsList:
					if jnt.getParent() not in jointsList:
						if jnt not in roots:
							roots.append(jnt)
				print '\nROOTS:'
				print roots
				# add rest in order
				for root in roots:
					partition = [root]

					# print '\DESCENDANTS:'
					# print listRelatives(root, allDescendents=True)[::-1]

					for child in listRelatives(root, allDescendents=True)[::-1]:
						if child not in roots:
							if child in jointsList:
								partition.append(child)

					print '\nPARTITION:'
					print partition
					partitions.append(partition)

			# raise Exception('end test.')
			# Naming
			self.globalName = self.fitNode.globalName.get()
			self.subNames = []
			subAttrs = listAttr(self.fitNode, st='subName*')
			for subAttr in subAttrs:
				self.subNames.append(self.fitNode.attr(subAttr).get())
			# print 'subnames:'
			# print self.subNames

			self.naming()
			self.names = utils.constructNames(self.namesDict)
			# ========================= RigNode Attributes =========================
			self.rigNode.rigType.set('chain', l=1)

			utils.cbSep(self.rigNode)
			addAttr(self.rigNode, ct='publish', ln='fkVis', nn='FK Vis', at='short', min=0, max=1, dv=1)
			setAttr(self.rigNode.fkVis, keyable=False, channelBox=True)
			if useIK:
				addAttr(self.rigNode, ct='publish', ln='ikVis', nn='IK Vis', at='short', min=0, max=1, dv=1)
				setAttr(self.rigNode.ikVis, keyable=False, channelBox=True)
		

			# ========================= Vis Mults =========================
			# allVis Mults
			fkVisMult = createNode('multDoubleLinear', n=self.names.get('fkVisMult', 'rnm_fkVisMult'))
			self.rigNode.allVis >> fkVisMult.i1
			self.rigNode.fkVis >> fkVisMult.i2
			self.step(fkVisMult, 'fkVisMult')

			if useIK:
				ikVisMult = createNode('multDoubleLinear', n=self.names.get('ikVisMult', 'rnm_ikVisMult'))
				self.rigNode.allVis >> ikVisMult.i1
				self.rigNode.ikVis >> ikVisMult.i2
				self.ikVis = ikVisMult.o
				self.step(ikVisMult, 'ikVisMult')

			debugVisMult = createNode('multDoubleLinear', n=self.names.get('debugVisMult', 'rnm_debugVisMult'))
			self.debugVis = debugVisMult.o
			self.rigNode.allVis >> debugVisMult.i1
			self.rigNode.debugVis >> debugVisMult.i2
			self.step(debugVisMult, 'debugVisMult')

			# ========================= World Group =========================
			# worldGroup = createNode('transform', n=self.names.get('worldGroup', 'rnm_worldGroup'), p=self.rigGroup)
			# self.worldGroup = worldGroup
			# self.step(worldGroup, 'worldGroup')
			# worldGroup.inheritsTransform.set(0)
			# xform(worldGroup, rp=[0,0,0], ro=[0,0,0], ws=1)

			#=========================== FK Setup =================================
			if multiChain and partitions:
				print '\nJointsList:'
				print jointsList
				for partition in partitions:

					strt = jointsList.index(partition[0])
					end = (jointsList.index(partition[-1])+1)
					print '\n[%s:%s]' % (strt, end)
					print jointsList[strt:end]
					
					fkGroup = self.buildFkSetup(shapes=fkShapes[strt:end], transforms=jointsList[strt:end], mirror=mirror, startInt=strt)
					fkVisMult.o.connect(fkGroup.v)

				if useIK:
					for fkCtrl in self.fkCtrls:
						self.socket(fkCtrl).message.connect(self.rigNode.socketList, na=1)

				# raise Exception('endTest')
			else:
				fkGroup = self.buildFkSetup(shapes=fkShapes, transforms=jointsList, mirror=mirror)
				fkVisMult.o.connect(fkGroup.v)
				if not useIK:
					for fkCtrl in self.fkCtrls:
						self.socket(fkCtrl).message.connect(self.rigNode.socketList, na=1)

			#=========================== Offset Setup =================================

			if useIK:
				for i, fkCtrl in enumerate(self.fkCtrls):
					self.naming(i=i)
					self.names = utils.constructNames(self.namesDict)

					offsetCtrl = self.createControlHeirarchy(selectionPriority=0, mirror=mirror, name=self.names.get('offsetCtrl', 'rnm_offsetCtrl'), shape=ikShapes[i], par=fkCtrl, ctrlParent=fkCtrl, jntBuf=False, outlinerColor=(0,0,0))
					self.offsetCtrls.append(offsetCtrl)
					self.ctrlsList.append(offsetCtrl)

					self.ikVis.connect(offsetCtrl.buf.get().v)

					try:
						self.ikCtrls.append(offsetCtrl)
					except AttributeError:
						self.ikCtrls = []
						self.ikCtrls.append(offsetCtrl)

					self.socket(offsetCtrl).message.connect(self.rigNode.socketList, na=1)

			if doBind:
				for i, ctrl in enumerate(self.ikCtrls if useIK else self.fkCtrls):
					self.naming(i=i)
					self.names = utils.constructNames(self.namesDict)
					
					if mirror:
						ctrl = self.socket(ctrl)
					# 	ctrl.rotateY.set(-180)
					# 	ctrl.scaleX.set(-1)
					
					bind = createNode('joint', n=self.names.get('bind', 'rnm_bind'), p=ctrl)
					self.bindList.append(bind)
					self.step(bind, 'bind')
					bind.hide()


			#=========================== Finalize =================================

			try:
				self.setController(fkRigGroup, self.rigGroup)
			except:
				pass

			try:
				self.constructSelectionList(selectionName='fkCtrls', selectionList=self.fkCtrls)
				if useIK:
					self.constructSelectionList(selectionName='offsetCtrls', selectionList=self.offsetCtrls)
				self.constructSelectionList(selectionName='frozenNodes', selectionList=self.freezeList)
			except:
				pass

			self.finalize()

	def naming(self, i=0, n=0, *args, **kwargs):
		
		try:
			globalName = self.globalName
		except:
			globalName = ''

		try:
			subName = self.subNames[i]
		except:
			subName = globalName

		self.namesDict={			
			'asset':					{'desc': globalName, 'side': self.fitNode.side.get(),	'warble': 'asset'},
			'rigGroup':					{'desc': globalName, 'side': self.fitNode.side.get(),	'warble': 'rigGroup'},
			'fkControlsGroup':			{'desc': globalName, 'side': self.fitNode.side.get(),	'warble': 'grp',		'other': ['fk', 'controls']							},
			'fkIkAutoMult':           	{'desc': globalName, 'side': self.fitNode.side.get(),	'warble': 'mult',		'other': ['fkIkAuto', 'vis']							},
			'fkVisMult':              	{'desc': globalName, 'side': self.fitNode.side.get(),	'warble': 'mult',		'other': ['fk', 'vis']									},
			'ikVisMult':              	{'desc': globalName, 'side': self.fitNode.side.get(),	'warble': 'mult',		'other': ['ik', 'vis']									},
			'debugVisMult':             {'desc': globalName, 'side': self.fitNode.side.get(),	'warble': 'mult',		'other': ['ik', 'vis']									},
			'fkCtrl':          			{'desc': subName, 	 'side': self.fitNode.side.get(),	'warble': None,			'other': ['fk']											},
			'offsetCtrl':          		{'desc': subName, 	 'side': self.fitNode.side.get(),	'warble': None,			'other': ['offset']											},
			'bind':          			{'desc': subName, 	 'side': self.fitNode.side.get(),	'warble': 'bind'},
	
		}
