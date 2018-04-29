

class fitRig(buildRig.rig):
	# Subclass of rig, handling variables input and visual feedback

	def __init__(self, dev=True, rigType):

		self.dev = dev

		self.initializeEnvironment()
		
		'''Create basic rig node network '''
		if self.dev: print 'Basic FitRig Setup...'
		self.sectionTag = 'fitRigBase'

		# Initiate fitnode
				
		self.fitNode = self.createFitNode(joints, rigType)
		
		# Otherwise, use the node specified and skip creation
		else:
			self.fitNode = fitNode
			self.getColors()


		# FitNode
		self.fitNode = fitNode
		if self.dev: print 'Fit Node: %s' % self.fitNode.nodeName()

		# Gather Skelenode data
		if hasAttr(self.fitNode, 'skeleNode'):
			if self.fitNode.skeleNode.get():
				self.skeleNode = self.fitNode.skeleNode.get()
				self.globalControl = self.skeleNode.globalMove.get()
				self.rigsGroup = self.skeleNode.rigGroup.get()
				self.fitRigsGroup = self.skeleNode.fitRigsGroup.get()
			else:
				self.skeleNode = None
				self.globalcontrol = None
				self.rigsGroup = None
		# self.socketGroup = self.skeleNode.socketGroup.get()
		# self.outputGroup = self.skeleNode.outputGroup.get()
		
		if self.dev: print 'SkeleNode: %s' % self.skeleNode
		if self.dev: print 'Rigs Group: %s' % self.rigsGroup
		# if self.dev: print 'Socket Group: %s' % self.socketGroup
		# if self.dev: print 'Output Group: %s' % self.outputGroup
		
		# Error check
		# Add naming check
		if not isinstance(self.fitNode, PyNode):
			if isinstance(self.fitNode, str):
				self.fitNode = ls(fitNode)[0]
			else:
				raise Exception('FitNode input is of wrong type: %s' % fitNode)
		if not hasAttr(self.fitNode, 'rigType'):
			raise Exception('Attribute missing: %s.rigType; Verify inputs' % self.fitNode)

		self.publishList = []
		self.deleteList = []
		self.freezeList = []
		self.ctrlsList = []
		self.clashList = []
		self.unnammedList = []
		self.bindList = []
		self.spaceSwitches = {}

		self.tangledMatrixConstraints = []
		self.untangledMatrixConstraints = []
		self.tangledAimConstraints = []
		self.untangledAimConstraints = []

		self.hiddenInOutlinerList = []
		# self.socketList = []

		# self.controllerTags = not self.dev # Adds 'controller' node tag object (Maya 2017+)
		self.controllerTags = True # Adds 'controller' node tag object (Maya 2017+)
		self.ctrlTags = []
		self.nodeCount = 0

		self.side = self.fitNode.side.get()
		
		# ============================= Naming ============================= 
		namesDict = {
		'rigNode': 	{'desc': self.fitNode.globalName.get(), 'side' :self.fitNode.side.get(), 'warble': 'rigNode', 	'other': []},
		'selNode': 	{'desc': self.fitNode.globalName.get(), 'side' :self.fitNode.side.get(), 'warble': 'selNode', 	'other': []},
		'rigGroup': {'desc': self.fitNode.globalName.get(), 'side' :self.fitNode.side.get(), 'warble': 'rigGroup',	'other': []}
		}
		self.names = utils.constructNames(namesDict)
		# names = {}

		# ============================= Selection Node ============================= 
		self.selNode = createNode('network', n=self.names.get('selNode', 'rnm_selNode'))
		self.publishList.append(self.selNode)
		self.step(self.selNode, 'selNode')
		# Attributes
		addAttr(self.selNode, k=1, h=0, dt='string', category='verification', ln='selNodeVer')
		addAttr(self.selNode, k=0, h=0, at='message', multi=1, indexMatters=False, category='selection', ln='ctrlsList')
		# addAttr(self.selNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='socketList')
		addAttr(self.selNode, k=0, h=0, at='message', multi=1, indexMatters=False, category='selection', ln='bindList')
		addAttr(self.selNode, k=0, h=0, at='message', ln='rigNode')


		# ============================= Rig Group =============================
		self.rigGroup = createNode('transform', n=self.names.get('rigGroup', 'rnm_rigGroup'), p=self.rigsGroup)
		if self.dev: print 'RigGroup:'
		self.step(self.rigGroup, 'rigGroup', freeze=False)
		# if self.dev: print 'RigGroup: %s' % self.rigGroup\


		# ============================= Rig Node ============================= 
		if not self.doAssetize:
			self.rigNode = createNode('locator', n=self.names.get('rigNode', 'rnm_rigNode'), p=self.rigGroup)
			self.rigNode.hide()
			hideAttrs = [
			self.rigNode.localPositionX,
			self.rigNode.localPositionY,
			self.rigNode.localPositionZ,
			self.rigNode.localScaleX,
			self.rigNode.localScaleY,
			self.rigNode.localScaleZ,
			]
		else:
			self.rigNode = createNode('transform', n=self.names.get('rigNode', 'rnm_rigNode'), p=self.rigGroup)
			hideAttrs = [
			self.rigNode.translateX,
			self.rigNode.translateY,
			self.rigNode.translateZ,
			self.rigNode.rotateX,
			self.rigNode.rotateY,
			self.rigNode.rotateZ,
			self.rigNode.scaleX,
			self.rigNode.scaleY,
			self.rigNode.scaleZ,
			self.rigNode.visibility
			]
			self.publishList.append(self.rigNode)
		for attr in hideAttrs:
			attr.set(l=1, k=0, cb=0)
		if self.dev: print 'RigNode: %s' % self.rigNode
		

		# Verification that this is a rigNode
		addAttr(self.rigNode, ln='rigNodeVer', k=0)
		# Connect fitNode to rigNode
		if not hasAttr(self.fitNode, 'rigNode'):
			addAttr(self.fitNode, at='message', ln='rigNode', k=1)

		addAttr(self.rigNode, at='message', ln='fitNode', k=1)

		self.fitNode.rigNode.connect(self.rigNode.fitNode)
		# if self.dev: print '%s.rigNode >> %s.fitNode' % (self.fitNode, self.rigNode)

		# Connect rigNode to skeleNode
		if self.skeleNode:
			if not hasAttr(self.skeleNode, 'rigNodes'):
				addAttr(self.skeleNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='rigNodes')
			self.rigNode.message.connect(self.skeleNode.rigNodes, na=1)
			# if self.dev: print '%s.message >> %s.rigNodes' % (self.rigNode, self.skeleNode)

		# print self.side
		# print self.colorsIK[self.side]
		# col.setOutlinerRGB(self.rigGroup, self.colorsIK[self.side])

		# Attributes
		addAttr(self.rigNode, k=1, h=0, dt='string', ln='rigType')
		addAttr(self.rigNode, k=1, h=0, at='message', ln='heirarchy')
		addAttr(self.rigNode, k=0, h=1, at='message', ln='selNode')
		self.rigNode.selNode.connect(self.selNode.rigNode)
		addAttr(self.rigNode, k=0, h=1, at='message', ln='rigGroup')
		self.rigGroup.message.connect(self.rigNode.rigGroup)
		# addAttr(self.rigNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='ctrlsList')
		addAttr(self.rigNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='socketList')
		# addAttr(self.rigNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='bindList')


		addAttr(self.rigNode, ln='allVis', min=0, max=1, at='short', dv=1, keyable=1)
		addAttr(self.rigNode, ln='debugVis', min=0, max=1, at='short', dv=0, keyable=0)
		self.debugVis = self.rigNode.debugVis
		
		setAttr(self.rigNode.allVis, k=0, cb=1)
		setAttr(self.rigNode.debugVis, k=0, cb=1)
		if self.dev:
			self.rigNode.debugVis.set(1)


		addAttr(self.rigNode, k=1, h=0, dt='string', category='naming', ln='globalName')
		addAttr(self.rigNode, k=1, h=0, dt='string', category='naming', multi=1, ln='subName')

		# Set names to rigNode (Easier reference)
		self.rigNode.globalName.set(self.fitNode.globalName.get())
		for i, subN in enumerate(listAttr(self.fitNode, st='subName*')):
			self.rigNode.subName[i].set(self.fitNode.attr(subN).get())


		if self.dev: print 'Basic rigNode complete.'