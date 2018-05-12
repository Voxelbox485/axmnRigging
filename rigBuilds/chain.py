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
			try:
				# Initialize rigNode
				# Error Check:
				
				# Convert string input to PyNode if neccessary
				if isinstance(fitNode, str):
					fitNode = ls(fitNode)[0]

				if fitNode.rigType.get() != 'chain':
					raise Exception('Incorrect rig type: %s' % fitNode.rigType.get())

				self.offsetCtrls = []
				# self.crvs = []

				buildRig.rig.__init__(self, fitNode)


				# fitNode attributes

				jointsList = 		self.fitNode.jointsList.get()
				fkShapes = 			self.fitNode.fkShapes.get()
				ikShapes = 			self.fitNode.ikShapes.get()
				doIK = 				self.fitNode.offsets.get()

				multiChain = 0
				if hasAttr(self.fitNode, 'multiChain'):
					multiChain = 		self.fitNode.multiChain.get()


				doHierarchy = True
				if hasAttr(self.fitNode, 'doHierarchy'):
					doHierarchy = 		self.fitNode.doHierarchy.get()

				# if doHierarchy:
					# organize jointsList
				# Move rigGroup
				xform(self.rigGroup, ws=1, m=xform(jointsList[0], q=1, ws=1, m=1))


				# Mirroring
				if self.fitNode.side.get() == 2:
					mirror=True
				else:
					mirror=False

				# Per joint mirroring
				mirrorList = []
				for jnt in jointsList:
					if jnt.autoMirror.get() is False:
						mirrorList.append(False)
					elif jnt.side.get() == 2:
						mirrorList.append(True)
					else:
						mirrorList.append(False)
				if self.dev:
					print 'mirrorList:'
					print mirrorList

				if hasAttr(self.fitNode, 'bind'):
					doBind = self.fitNode.bind.get()
				else:
					doBind = True

				if hasAttr(self.fitNode, 'doFK'):
					doFK = self.fitNode.doFK.get()
				else:
					doFK = True

				# Make sure one of the options are on by default
				if not doFK and not doIK:
					doFK=True

				if hasAttr(self.fitNode, 'doEntranceBind'):
					doEntranceBind = bool(self.fitNode.doEntranceBind.get())
				else:
					doEntranceBind = True


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
				if doFK or doIK:
					utils.cbSep(self.rigNode)
				if doFK:
					addAttr(self.rigNode, ct='publish', ln='fkVis', nn='FK Vis', at='short', min=0, max=1, dv=1)
					setAttr(self.rigNode.fkVis, keyable=False, channelBox=True)
				if doIK:
					addAttr(self.rigNode, ct='publish', ln='ikVis', nn='IK Vis', at='short', min=0, max=1, dv=1)
					setAttr(self.rigNode.ikVis, keyable=False, channelBox=True)
			

				# ========================= Vis Mults =========================
				# allVis Mults
				if doFK:
					fkVisMult = createNode('multDoubleLinear', n=self.names.get('fkVisMult', 'rnm_fkVisMult'))
					self.rigNode.allVis >> fkVisMult.i1
					self.rigNode.fkVis >> fkVisMult.i2
					self.step(fkVisMult, 'fkVisMult')

				if doIK:
					ikVisMult = createNode('multDoubleLinear', n=self.names.get('ikVisMult', 'rnm_ikVisMult'))
					self.rigNode.allVis >> ikVisMult.i1
					self.rigNode.ikVis >> ikVisMult.i2
					self.ikVis = ikVisMult.o
					self.step(ikVisMult, 'ikVisMult')

				# debugVisMult = createNode('multDoubleLinear', n=self.names.get('debugVisMult', 'rnm_debugVisMult'))
				# self.debugVis = debugVisMult.o
				# self.rigNode.allVis >> debugVisMult.i1
				# self.rigNode.debugVis >> debugVisMult.i2
				# self.step(debugVisMult, 'debugVisMult')

				# ========================= World Group =========================
				# worldGroup = createNode('transform', n=self.names.get('worldGroup', 'rnm_worldGroup'), p=self.rigGroup)
				# self.worldGroup = worldGroup
				# self.step(worldGroup, 'worldGroup')
				# worldGroup.inheritsTransform.set(0)
				# xform(worldGroup, rp=[0,0,0], ro=[0,0,0], ws=1)

				#=========================== FK Setup =================================


				if doHierarchy:
					print '\nJointsList:'
					print jointsList
					# We're going to form a hierarchy of controls based on a 'clump' of joints input as a list

					# Reorder joints list so that we create controls top-down
					heirScore = {}
					for item in jointsList:
						heirScore[item] = (len(item.getAllParents()))

					import operator
					sortedHeir = sorted(heirScore.items(), key=operator.itemgetter(1))

					jointsList2 = []
					for s in sortedHeir:
						jointsList2.append(s[0])

					print '\nJointsList2:'
					print jointsList2
					
					# Map controls to each joint
					ctrlMapping = {}
					for i, jnt in enumerate(jointsList2):

						ind = jointsList.index(jnt)
						self.naming(i=ind)
						self.names = utils.constructNames(self.namesDict)

						# Reach upward into each joint's parentage.  If no fit joints in list up to top, it's a root joint. otherwise, use first parent found
						jntParent = jnt.getParent()
						while not jntParent in jointsList2:
							if jntParent is None:
								break
							jntParent = jntParent.getParent()

						# If it found anything, get the control for that joint
						if jntParent:
							ctrlParent = ctrlMapping[jntParent]
						else:
							ctrlParent = None

						if ctrlParent:
							ctrl = self.createControlHeirarchy(selectionPriority=0, transformSnap=jnt, mirrorStart = mirrorList[ind], mirror=mirrorList[ind], name=self.names.get('fkCtrl', 'rnm_fkCtrl'), shape=fkShapes[ind], par=ctrlParent, ctrlParent=ctrlParent, jntBuf=True)
							# ctrl = createNode('transform', name=self.names.get('fkCtrl', 'rnm_fkCtrl'), p=ctrlParent)
						else:
							ctrl = self.createControlHeirarchy(selectionPriority=0, transformSnap=jnt, mirrorStart = mirrorList[ind], mirror=mirrorList[ind], name=self.names.get('fkCtrl', 'rnm_fkCtrl'), shape=fkShapes[ind], par=self.rigGroup, ctrlParent=self.rigGroup, jntBuf=True)
							# ctrl = createNode('transform', name=self.names.get('fkCtrl', 'rnm_fkCtrl'), p=self.rigGroup)

						
						ctrlMapping[jnt] = ctrl

						try:
							self.fkCtrls.append(ctrl)
						except AttributeError:
							self.fkCtrls = []
							self.fkCtrls.append(ctrl)

						if ctrl.getShapes(): fkVisMult.o.connect(ctrl.getShapes()[0].v)
						self.socket(ctrl).message.connect(self.rigNode.socketList, na=1)

					if self.dev:
						print '\nctrlMapping:'
						print ctrlMapping
						for item, key in ctrlMapping.items():
							print '%s\t-\t%s' % (item, key)

				else:
					if doFK:
						fkGroup = self.buildFkSetup(shapes=fkShapes, transforms=jointsList, mirror=mirror)
						fkVisMult.o.connect(fkGroup.v)
						
						if not doIK:
							for fkCtrl in self.fkCtrls:
								self.socket(fkCtrl).message.connect(self.rigNode.socketList, na=1)


				#=========================== Offset Setup =================================
				# Whether or not fk is created
				if doIK:
					for i, jnt in enumerate(jointsList):
						self.naming(i=i)
						self.names = utils.constructNames(self.namesDict)

						# If fk ctrls were created, parent them there
						if doFK:
							offsetCtrl = self.createControlHeirarchy(selectionPriority=0, mirror=mirror, name=self.names.get('offsetCtrl', 'rnm_offsetCtrl'), shape=ikShapes[i], par=self.fkCtrls[i], ctrlParent=self.fkCtrls[i], jntBuf=False, outlinerColor=(0,0,0))

						# Else create offset controls on their own
						else:
							offsetCtrl = self.createControlHeirarchy(selectionPriority=0, mirror=mirror, name=self.names.get('offsetCtrl', 'rnm_offsetCtrl'), shape=ikShapes[i], par=self.rigGroup, ctrlParent=self.rigGroup, jntBuf=False, transformSnap=jnt)
						
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
					if doEntranceBind:
						# Transform to handle distribution of mesh with root moved without rotation
						rigEntranceGrp = createNode('transform', n=self.names.get('rigEntranceGrp', 'rnm_rigEntranceGrp'), p=self.rigGroup)
						self.step(rigEntranceGrp, 'rigEntranceGrp')

						# point constrain to start node
						utils.snap(jointsList[0], rigEntranceGrp)
						self.matrixConstraint(self.ikCtrls[0] if doIK else self.fkCtrls[0], rigEntranceGrp, t=1)
						
						rigEntrance = createNode('joint', n=self.names.get('rigEntrance', 'rnm_rigEntrance'), p=rigEntranceGrp)
						self.step(rigEntrance, 'rigEntrance')
						self.bindList.append(rigEntrance)
						rigEntrance.hide()

					for i, ctrl in enumerate(self.ikCtrls if doIK else self.fkCtrls):
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

			finally:

				#=========================== Finalize =================================

				try:
					self.setController(fkRigGroup, self.rigGroup)
				except:
					pass

				try:
					self.constructSelectionList(selectionName='fkCtrls', selectionList=self.fkCtrls)
					if doIK:
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
			'rigEntranceGrp':          	{'desc': globalName, 'side': self.fitNode.side.get(),	'warble': 'grp',		'other': ['entrance']											},
			'rigEntrance':          	{'desc': globalName, 'side': self.fitNode.side.get(),	'warble': 'bind',		'other': ['entrance']											},
			'bind':          			{'desc': subName, 	 'side': self.fitNode.side.get(),	'warble': 'bind'},
	
		}
