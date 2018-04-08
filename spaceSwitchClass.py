from pymel.core import *
import utils
import colorOverride as col
import buildRig.rig


class spaceSwitchUI():
	# Separate class for interacting with spaceswitch class
	'''
	'''
	# I want it to be editable from any point of creationg, and to be able to initialize it within rig build
	def __init__(self):

		self.win = 'axmn_spaceSwitch_window'

		if window(self.win, exists=True):
			deleteUI(self.win)

		# self.win = window(self.win, t='Batch Connect', retain=False, width=300, resizeToFitChildren=1, sizeable=1, mxb=0)

		# self.UI(p=self.win)

	def UI():
		pass


class spaceSwitch(buildRig.rig):
	# Class for interactivly editing weighted constraints
	'''
	from pymel.core import *
	import spaceSwitchClass as ss

	sel = ls('hand_L_ik_CTRL')[0]
	reload(ss)
	ssInst = ss.spaceSwitch(controller=sel, constrained=sel.const.get(), p='rig_GRP', targets=['rig_GRP', sel.buf.get()], labels=['World', 'Parent'])
	ssInst.addTarget(target=ls('hips_M_3_socket_GRP')[0], label='Chest')

	ssInst.removeTarget(label='Chest')
	'''
	freezeColor = (0,0,0)
	def __init__(self, rigNode=None, controller=None, constrained=None, targets=None, labels=None, prefix=None, p=None, constraintType='parent', dev=False):
		# If already initialized, instantiate class with rigNode, else create new
		self.dev = dev
		self.deleteList = []
		self.ctrlsList = []
		self.clashList = []
		self.unnammedList = []
		self.freezeList = []
		self.publishList = []
		self.rebuildList = []
		self.nodeCount = 0
		self.sectionTag = 'spaceSwitch'
		self.constraintType = constraintType
		self.parent = p


		self.names = {}


		initialize = True # Checks to see if rig needs to be initialized

		# If no inputs for rigNode or constrained, check controller
		if rigNode is None:
			# If there's a controller input, check if controller has spaceSwitch rigNode attached
			if controller is not None:
				if isinstance(controller, str) or isinstance(controller, unicode):
					if len(ls(controller)) == 1:
						controller = ls(controller)[0]
					elif len(ls(controller)) == 0:
						raise Exception('No controller node found: %s' % controller)
					elif len(ls(controller)) > 0:
						warning('%s' % ls(controller))
						raise Exception('More than one controller object with name found: %s' % controller)
				if not isinstance(controller, PyNode):
					raise Exception('Controller is not a PyNode: %s' % controller)
				else:
					if hasAttr(controller, 'spaceSwitchRigNode'):
						if controller.spaceSwitchRigNode.get():
							rigNode = controller.spaceSwitchRigNode.get()
							

			# If there's a constrained input, check if controller has spaceSwitch rigNode attached
			if rigNode is None and constrained is not None:
				if isinstance(constrained, str) or isinstance(constrained, unicode):
					if len(ls(constrained)) == 1:
						constrained = ls(constrained)[0]
					elif len(ls(constrained)) == 0:
						raise Exception('No constrained node found: %s' % constrained)
					elif len(ls(constrained)) > 0:
						warning('%s' % ls(constrained))
						raise Exception('More than one constrained object with name found: %s' % constrained)
				if not isinstance(constrained, nt.Transform):
					raise Exception('constrained is not a PyNode Transform: %s' % constrained)
				else:
					if hasAttr(constrained, 'spaceSwitchRigNode'):
						if constrained.spaceSwitchRigNode.get():
							rigNode = constrained.spaceSwitchRigNode.get()
							

		if rigNode is not None:
			self.rigNode = rigNode
			self.updateClassInfo()
			
			
			initialize = False


		if initialize:

			if not constrained:
				raise Exception('Specify constrained object')

			# Initialize if not initialized
			self.prefix = 			prefix
			self.controller = 		controller
			self.constrained = 		constrained
			self.targets = 			targets
			self.labels = 			labels
			self.constraintType = 	constraintType
			self.parent = 			p

			self.constraint = 		None
			self.attrCategory =		'%s_spaceSwitch' % self.constrained.nodeName()

			if not self.prefix:
				self.prefix = self.constrained.nodeName()

			
			self.rigGroup = createNode('transform', n=self.names.get('rigGroup', 'rnm_spaceSwitch'), p=self.parent)

			# Create rig node
			self.rigNode = createNode('locator', n=self.names.get('rigNode', 'rnm_spaceSwitch_rigNode'), p=self.rigGroup)
			self.rigNode.lpx.set(k=0, cb=0, l=1)
			self.rigNode.lpy.set(k=0, cb=0, l=1)
			self.rigNode.lpz.set(k=0, cb=0, l=1)
			self.rigNode.lsx.set(k=0, cb=0, l=1)
			self.rigNode.lsy.set(k=0, cb=0, l=1)
			self.rigNode.lsz.set(k=0, cb=0, l=1)
			self.rigNode.hide()
			self.selNode = self.rigNode

			if not objExists('connectorSet'):
				connectorSet = sets([self.rigNode], n='connectorSet')
			else:
				connectorSet = sets('connectorSet', e=True, forceElement=self.rigNode)



			if not hasAttr(self.rigNode, 'rigType'):
				addAttr(self.rigNode, ln='rigType', dt='string', k=1)
				self.rigNode.rigType.set('spaceSwitch', l=1)

			if not hasAttr(self.rigNode, 'prefix'):
				addAttr(self.rigNode, ln='prefix', dt='string', k=1)

			if not hasAttr(self.rigNode, 'constraintType'):
				addAttr(self.rigNode, ln='constraintType', at='enum', enumName='parent:point:orient', k=1)

			if not hasAttr(self.rigNode, 'controller'):
				addAttr(self.rigNode, ln='controller', at='message', k=1)

			if not hasAttr(self.rigNode, 'constrained'):
				addAttr(self.rigNode, ln='constrained', at='message', k=1)


			if not hasAttr(self.rigNode, 'constraint'):
				addAttr(self.rigNode, ln='constraint', at='message', k=1)

			if not hasAttr(self.rigNode, 'targetGroups'):
				addAttr(self.rigNode, ln='targetGroups', at='compound', numberOfChildren=2, multi=True, k=1)
				addAttr(self.rigNode, ln='target', p='targetGroups', at='message', k=1)
				addAttr(self.rigNode, ln='label', p='targetGroups', dt='string', k=1)

			if not hasAttr(self.rigNode, 'controlVis'):
				addAttr(self.rigNode, ln='controlVis', at='short', min=0, max=1, dv=0)
				self.rigNode.controlVis.set(k=0, cb=1)
			self.rigNode.controlVis.connect(self.rigGroup.v)

			# if not hasAttr(self.rigNode, 'indicVis'):
			# 	addAttr(self.rigNode, ln='indicVis', at='short', min=0, max=1, dv=0)
			# 	self.rigNode.indicVis.set(k=0, cb=1)

			self.enumAttrAName = '%sSpaceA' % self.constraintType
			self.enumAttrBName = '%sSpaceB' % self.constraintType
			self.blendAttrName = '%sSpaceBlend' % self.constraintType

			if not hasAttr(self.rigNode, self.enumAttrAName):
				addAttr(self.rigNode, ln= self.enumAttrAName, at='enum', enumName='0:1', k=1)
			if not hasAttr(self.rigNode, self.enumAttrBName):
				addAttr(self.rigNode, ln= self.enumAttrBName, at='enum', enumName='0:1', k=1, dv=1)

			if not hasAttr(self.rigNode, self.blendAttrName):
				addAttr(self.rigNode, ln= self.blendAttrName, min=0, max=1, k=1)

			self.enumAttrA = self.rigNode.attr(self.enumAttrAName)
			self.enumAttrB = self.rigNode.attr(self.enumAttrBName)
			self.blendAttr = self.rigNode.attr(self.blendAttrName)

			if not hasAttr(self.rigNode, 'constraint'):
				addAttr(self.rigNode, ln='constraint', at='message', k=self.dev)

			if not hasAttr(self.rigNode, 'rigGroup'):
				addAttr(self.rigNode, ln='rigGroup', at='message', k=self.dev)

			# if not hasAttr(self.rigNode, 'targets'):
			# 	addAttr(self.rigNode, ln='targets', at='message', multi=True, k=1)

			# if not hasAttr(self.rigNode, 'labels'):
			# 	addAttr(self.rigNode, ln='labels', dt='string', multi=True, k=1)

			self.updateRigNode()
			self.rebuild()
			self.setController()
			self.updateRigNode()



			select(self.rigNode)


	def naming(self, *args, **kwargs):
		self.names = {
			# 'asset':					{'desc':  self.rigNode.prefix.get(), 'side': None,	'warble': 'asset'},
			'asset':					{'desc':  'spaceSwitch', 	'warble': 'asset',			'other': [self.rigNode.prefix.get()],									},
			'rigGroup':					{'desc':  'spaceSwitch',	'warble': 'rigGroup',		'other': [self.rigNode.prefix.get()],									},
			'rigNode':					{'desc':  'spaceSwitch',	'warble': 'rigNode',		'other': [self.rigNode.prefix.get()],									},
			'buf':                      {'desc':  'spaceSwitch',	'warble': 'buf',			'other': [self.rigNode.prefix.get()],									},
			'const':                    {'desc':  'spaceSwitch',	'warble': 'const',			'other': [self.rigNode.prefix.get()],									},
			'offset':                   {'desc':  'spaceSwitch',	'warble': 'offset',			'other': [self.rigNode.prefix.get()],									},
			'ctrl':                     {'desc':  'spaceSwitch',	'warble': 'ctrl',			'other': [self.rigNode.prefix.get()],									},
			'rev':                      {'desc':  'spaceSwitch',	'warble': 'rev',			'other': [self.rigNode.prefix.get()],									},
			'constraint':               {'desc':  'spaceSwitch',	'warble': 'rev',			'other': [self.rigNode.prefix.get(), self.rigNode.constraintType.get()],},
			'cond1':                    {'desc':  'spaceSwitch',	'warble': 'cond',			'other': [self.rigNode.prefix.get(), '1'],								},
			'cond2':                    {'desc':  'spaceSwitch',	'warble': 'cond',			'other': [self.rigNode.prefix.get(), '2'],								},
		}

	def updateClassInfo(self):

		self.selNode =			self.rigNode
		self.prefix = 			self.rigNode.prefix.get()
		self.constraintType = 	self.rigNode.constraintType.get(asString=True)
		self.controller = 		self.rigNode.controller.get()
		self.constraint = 		self.rigNode.constraint.get()
		self.constrained = 		self.rigNode.constrained.get()
		self.rigGroup = 		self.rigNode.rigGroup.get()

		self.enumAttrAName = '%sSpaceA' % self.constraintType
		self.enumAttrBName = '%sSpaceB' % self.constraintType
		self.blendAttrName = '%sSpaceBlend' % self.constraintType

		self.targets = []
		self.labels = []

		for targ in self.rigNode.targetGroups:
			if targ.getChildren()[0].get():
				self.targets.append(targ.getChildren()[0].get())
				self.labels.append(targ.getChildren()[1].get())
		# self.targets = 			self.rigNode.targets.get()
		# self.labels = 			self.rigNode.labels.get()
		self.attrCategory = 		'%s_spaceSwitch' % self.constrained.nodeName()

		# Get enum attributes for both rigNode and controller
		self.enumAttrA = self.rigNode.attr(self.enumAttrAName)
		self.enumAttrB = self.rigNode.attr(self.enumAttrBName)
		self.blendAttr = self.rigNode.attr(self.blendAttrName)
		

		if self.controller:
			if hasAttr(self.controller, self.blendAttrName):
				self.controllerEnumAttrA = self.controller.attr(self.enumAttrAName)
				self.controllerEnumAttrB = self.controller.attr(self.enumAttrBName)
				self.controllerBlendAttr = self.controller.attr(self.blendAttrName)
		
		if self.constraint:
			self.constraint = self.rigNode.constraint.get()

		self.inputsErrorCheck()

	def updateRigNode(self):
		self.inputsErrorCheck()
		if self.prefix:
			self.rigNode.prefix.set(self.prefix)
		
		# 
		self.rigNode.constraintType.set(self.constraintType)
		
		# 
		if self.controller:
			if not isConnected(self.controller.message, self.rigNode.controller):
				self.controller.message.connect( self.rigNode.controller, f=1 )
			if not hasAttr(self.controller, 'spaceSwitchRigNode'):
				addAttr(self.controller, ln='spaceSwitchRigNode', at='message', ct=self.attrCategory)
			if not isConnected(self.rigNode.message, self.controller.spaceSwitchRigNode):
				self.rigNode.message.connect(self.controller.spaceSwitchRigNode)
		# 
		if not isConnected(self.constrained.message, self.rigNode.constrained):
			self.constrained.message.connect( self.rigNode.constrained, f=1 )
		if not hasAttr(self.constrained, 'spaceSwitchRigNode'):
			addAttr(self.constrained, ln='spaceSwitchRigNode', at='message', ct=self.attrCategory)
		if not isConnected(self.rigNode.message, self.constrained.spaceSwitchRigNode):
			self.rigNode.message.connect(self.constrained.spaceSwitchRigNode)

		if not isConnected(self.rigGroup.message, self.rigNode.rigGroup):
			self.rigGroup.message.connect(self.rigNode.rigGroup)

		# Diconnect current targets and rebuild
		if self.targets:
			for targ in self.rigNode.targetGroups:
				for targChild in targ.getChildren():
					targChild.disconnect()

			for i, target in enumerate(self.targets):
				target.message.connect(self.rigNode.targetGroups[i].target)
				self.rigNode.targetGroups[i].label.set(self.labels[i])

		if self.constraint:
			if not isConnected(self.constraint.message, self.rigNode.constraint):
				self.constraint.message.connect(self.rigNode.constraint)

	def setDefaultBlend(self, val):
		try:
			addAttr(self.controllerBlendAttr, e=1, dv=val)
		except:
			pass
		try:
			addAttr(self.blendAttr, e=1, dv=val)
		except:
			try:
				warning('Default blend value could not be changed: %s' % self.blendAttr)
			except:
				warning('Default blend value could not be changed.')

		try:
			self.setBlend(val)
		except:
			pass

	def setBlend(self, val):
		try:
			self.controllerBlendAttr.set(val)
		except:
			try:
				self.blendAttr.set(val)
			except:
				raise Exception('Blend value could not be changed.: %s' % self.blendAttr)

	def inputsErrorCheck(self):
		# Check existing inputs for errors
		
		# Listify inputs in case they're single nodes
		if self.labels is not None:
			if not isinstance(self.labels, list):
				self.labels = [self.labels]
		if self.targets is not None:
			if not isinstance(self.targets, list):
				self.targets = [self.targets]
		

			# If targets specified, check length against labels(unless unspecified)
			if len(self.targets):
				if isinstance(self.labels, list):
					if len(self.labels) != len(self.targets):
						raise Exception('Labels list length does not match targets list length')
					else:
						# Check all labels and make sure they're strings
						for label in self.labels:
							if not isinstance(label, str) and not isinstance(label, unicode):
								raise Exception('Label is not a string: %s' % label)

			# Check each target. convert to pynode if it's a string
			for i, target in enumerate(self.targets):
				if isinstance(target, str) or isinstance(target, unicode):
					if len(ls(target)) == 1:
						self.targets[i] = ls(target)[0]
					elif len(ls(target)) == 0:
						raise Exception('No target found: %s' % target)
					elif len(ls(target)) > 0:
						warning('%s' % ls(target))
						raise Exception('More than one target object with name found: %s' % target)

			for target in self.targets:
				if target:
					if not isinstance(target, nt.Transform):
						raise Exception('Target is not a PyNode Transform: %s' % target)

		if self.parent is not None:
			if isinstance(self.parent, str) or isinstance(self.parent, unicode):
				if len(ls(self.parent)) == 1:
					self.parent = ls(self.parent)[0]
				elif len(ls(self.parent)) == 0:
					raise Exception('No target found: %s' % self.parent)
				elif len(ls(self.parent)) > 0:
					warning('%s' % ls(self.parent))
					raise Exception('More than one target object with name found: %s' % self.parent)


		validConstraintTypes = [
		'parent',
		'point',
		'orient']
		
		if self.constraintType not in validConstraintTypes:
			raise Exception('Constraint type not valid: %s' % self.constraintType)

	def setController(self, node=None):
		# If controller already set, just add to that one. Otherwise assume a switch and delete old connections first
		if not node is None:
			# TODO
			# Remove connections from previous (use category?)
			if self.controller:
				if self.dev: print '\n'
				self.deleteControllerAttributes()


			self.controller = node
			self.updateRigNode()


		if not hasAttr(self.controller, 'spaceSwitchRigNode'):
			addAttr(self.controller, ct=self.attrCategory, ln='spaceSwitchRigNode', at='message', k=self.dev)
		if not isConnected(self.rigNode.message, self.controller.spaceSwitchRigNode):
			self.rigNode.message.connect(self.controller.spaceSwitchRigNode)

		# if not hasAttr(self.controller, 'controlVis'):
		# 	addAttr(self.controller, ct=self.attrCategory, ln='controlVis', at='short', min=0, max=1, k=1, dv=self.dev)
		# self.controller.controlVis.connect(self.rigNode.controlVis)
		
		# if not hasAttr(self.controller, 'indicVis'):
		# 	addAttr(self.controller, ct=self.attrCategory, ln='indicVis', at='short', min=0, max=1, k=1, dv=self.dev)
		# self.controller.indicVis.connect(self.rigNode.indicVis)

		
		# enumName = addAttr(self.enumAttrA, q=1, enumName=1)
		enumName = self.enumAttrA.getEnums()
		enumAttrAName = self.enumAttrA.longName()
		enumAttrBName = self.enumAttrB.longName()

		if not hasAttr(self.controller, enumAttrAName):
			utils.cbSep(self.controller, ct=self.attrCategory)
			addAttr(self.controller, ct=self.attrCategory, ln=enumAttrAName, at='enum', enumName='0:1', k=1)
		self.controller.attr(enumAttrAName).setEnums(enumName)

		if not hasAttr(self.controller, enumAttrBName):
			addAttr(self.controller, ct=self.attrCategory, ln=enumAttrBName, at='enum', enumName='0:1', dv=1, k=1)
		self.controller.attr(enumAttrBName).setEnums(enumName)


		blendAttrName =self.blendAttr.longName()
		if not hasAttr(self.controller, blendAttrName):
			addAttr(self.controller, ct=self.attrCategory, ln=blendAttrName, min=0, max=1, dv=self.dev, k=1)
		

		self.controllerEnumAttrA = self.controller.attr(enumAttrAName)
		self.controllerEnumAttrB = self.controller.attr(enumAttrBName)
		self.controllerBlendAttr = self.controller.attr(blendAttrName)
		
		if not isConnected(self.controllerEnumAttrA, self.enumAttrA):
			self.controllerEnumAttrA.connect(self.enumAttrA)
		if not isConnected(self.controllerEnumAttrB, self.enumAttrB):
			self.controllerEnumAttrB.connect(self.enumAttrB)
		if not isConnected(self.controllerBlendAttr, self.blendAttr):
			self.controllerBlendAttr.connect(self.blendAttr)

	def addTarget(self, target, label=None):
		self.updateClassInfo()

		if not label:
			label = target.nodeName()

		if self.targets:
			for targ in self.rigNode.targetGroups:
				for targChild in targ.getChildren():
					targChild.disconnect()

		self.targets.append(target)
		self.labels.append(label)

		for i, target in enumerate(self.targets):
			target.message.connect(self.rigNode.targetGroups[i].target)
			self.rigNode.targetGroups[i].label.set(self.labels[i])

		self.rebuild()
		self.updateRigNode()
		select(self.rigNode)

	def removeTarget(self, target=None, label=None, ind=None):
		
		self.updateClassInfo()

		# If no index input, get index from label input. If not label input, get index from target input.
		if ind is None:
			if label:
				if label in self.labels:
					ind = self.labels.index(label)
				else:
					raise Exception('Label not found')
			
		if ind is None:
			if target:
				if target in self.targets:
					ind = self.targets.index(target)
				else:
					raise Exception('Label not found')

		# Remove items from class lists
		self.targets.remove(self.targets[ind])
		self.labels.remove(self.labels[ind])

		# reload rigNode targets
		for targ in self.rigNode.targetGroups:
			targ.getChildren()[0].disconnect()
			targ.getChildren()[1].set('')

		for i, target in enumerate(self.targets):
			target.message.connect(self.rigNode.targetGroups[i].target)
			self.rigNode.targetGroups[i].label.set(self.labels[i])

		self.rebuild()
		self.updateRigNode()
		select(self.rigNode)

	def deleteControllerAttributes(self):
		nodes = [self.controller, self.constrained]
		for node in nodes:
			attributes = listAttr(node, ct=self.attrCategory)

			for attribute in attributes:
				attribute = node.attr(attribute)
				deleteAttr(attribute)

	def deleteRig(self):
		self.deleteControllerAttributes()
		buildRig.rig.deleteRig(self)


	def rebuild(self):
		# Build setup with given info
		self.updateClassInfo()
		self.inputsErrorCheck()

		enumName = ':'.join(self.labels)
		self.enumAttrA.setEnums(enumName)
		self.enumAttrB.setEnums(enumName)
		# addAttr(self.enumAttrA, e=1, at='enum', enumName=enumName)
		# addAttr(self.enumAttrB, e=1, at='enum', enumName=enumName)

		if self.rebuildList:
			for item in self.rebuildList:
				if item.exists():
					delete(item)


		self.freezeList = []
		self.ctrlsList = []

		for i, target in enumerate(self.targets):

			label = self.labels[i]
			# Offset controls
			buf = createNode('transform', n=self.names.get('buf', 'rnm_buf_%s' % label), p=self.rigGroup)
			xform(buf, ws=1, m=xform(target, q=1, ws=1, m=1))
			self.step(buf, 'buf')
			self.rebuildList.append(buf)

			const = createNode('transform', n=self.names.get('const', 'rnm_const_%s' % label), p=buf)
			self.step(const, 'const')
			utils.matrixConstraint(target, const, t=1, r=1, s=1, offset=1)
			const.visibility.set(l=1, k=0, cb=0)

			offset = createNode('transform', n=self.names.get('offset', 'rnm_offset_%s' % label), p=const)
			self.step(offset, 'offset', freeze=False)
			xform(offset, ws=1, m=xform(self.constrained, q=1, ws=1, m=1))
			offset.visibility.set(l=1, k=0, cb=0)

			ctrl = createNode('transform', n=self.names.get('ctrl', 'rnm_ctrl_%s' % label), p=offset)
			ctrl.displayHandle.set(1, k=1)
			ctrl.visibility.set(l=1, k=0, cb=0)
			self.ctrlsList.append(ctrl)
			self.step(ctrl, 'ctrl', freeze=False)

			addAttr(ctrl, k=0, h=1, at='message', ln='bufferGroup', sn='buf')
			addAttr(ctrl, k=0, h=1, at='message', ln='constraintGroup', sn='const')
			addAttr(ctrl, k=0, h=1, at='message', ln='extraGroup', sn='extra')

			buf.message >> ctrl.buf
			const.message >> ctrl.const
			offset.message >> ctrl.extra


		rev = createNode('reverse', n=self.names.get('rev', 'rnm_rev'))
		self.step(rev, 'rev')
		self.blendAttr.connect(rev.ix)

		if self.constraintType == 'parent':
			self.constraint = parentConstraint(self.ctrlsList, self.constrained, n=self.names.get('constraint', 'rnm_constraint'))
			self.constraint.interpType.set(2)
		
		elif self.constraintType == 'point':
			self.constraint = pointConstraint(self.ctrlsList, self.constrained, n=self.names.get('constraint', 'rnm_constraint'))
			self.constraint.interpType.set(2)
		
		elif self.constraintType == 'orient':
			self.constraint = orientConstraint(self.ctrlsList, self.constrained, n=self.names.get('constraint', 'rnm_constraint'))
			self.constraint.interpType.set(2)



		for i, target in enumerate(self.targets):

			cond1 = createNode('condition', n=self.names.get('cond1', 'rnm_cond1'))
			self.step(cond1, 'cond1')
			cond1.colorIfFalseR.set(0)
			self.enumAttrA.connect(cond1.firstTerm)
			cond1.secondTerm.set(i)

			cond2 = createNode('condition', n=self.names.get('cond2', 'rnm_cond2'))
			self.step(cond2, 'cond2')
			self.enumAttrB.connect(cond2.firstTerm)
			cond2.secondTerm.set(i)

			rev.outputX.connect(cond1.colorIfTrueR)
			self.blendAttr.connect(cond2.colorIfTrueR)
			cond1.outColorR.connect(cond2.colorIfFalseR)

			cond2.outColorR.connect(self.constraint.attr('w%s' % i))


		self.setController()
		self.constructDeleteList()
		self.freezeNodes()
		self.attachRigNode()
		self.pruneSet(rigNodeSet = 'connectorSet')


