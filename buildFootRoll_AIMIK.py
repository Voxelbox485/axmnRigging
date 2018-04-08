

	def buildFootRollSetupAIMIK(self, fitNode):
		# Builds a footroll setup on poleVectorIK using fitNode input
		# Includes a auto toe extend in ik, pivot controls with constraints mapped to a 'roll' and 'bank' range, and fk controls (offset?)
		# TODO
		# This is weirdly organized, but it's kinda a complicated part of the ik rig
		# self.fkCtrls gets overwritten.  fkCtrls can be a temporary attribute? Should I copy out lists to new class variables after they're collected?
		# Should I assign them to a dictionary?

		toeExtendSetup = True

		self.sectionTag = 'footRoll'

		if fitNode is None:
			raise Exception('No data specified.')

		# Error Check:
		if len(fitNode.jointsList.get()) != 3:
			raise Exception('Not enough joints specified')

		
		# if not fitNode.pvikFitNode.get():
		# 	raise Exception('No PVIK fitRig specified')

		# Convert string input to PyNode if neccessary
		if isinstance(fitNode, str):
			fitNode = ls(fitNode)[0]

		if fitNode.rigType.get() != 'footRoll':
			raise Exception('Incorrect rig type: %s' % fitNode.rigType.get())

		# rig.__init__(self, fitNode)

		
		# Naming

		self.globalName = fitNode.globalName.get()
		self.subNames = [
		fitNode.subName0.get(),
		fitNode.subName1.get(),
		fitNode.subName2.get()
		]

		namesDict={			
			'footRollRigGroup':     { 'desc': self.globalName,	'side': fitNode.side.get(),		'warble': 'rigGroup',		'other': ['footRoll'], 						 				},
			'fkControlsGroup':    	{ 'desc': self.globalName,	'side': fitNode.side.get(),		'warble': 'rigGroup',		'other': ['footRoll', 'fk'], 						 				},
			'rigNode':              { 'desc': self.globalName,	'side': fitNode.side.get(),		'warble': 'rigNode',		'other': ['footRoll'], 										},
			'pivGroup':				{ 'desc': self.globalName,	'side': fitNode.side.get(),		'warble': 'grp',			'other': ['footRoll', 'pivots'], 							},
			'pivAnkle':				{ 'desc': self.globalName,	'side': fitNode.side.get(),		'warble': 'grp',			'other': ['footRoll', 'ankle'], 							},
			'fkIkCtrlSwitch':		{ 'desc': self.globalName,	'side': fitNode.side.get(),		'warble': 'trans',			'other': ['footRoll', 'fkIk', 'switch'], 					},
			'toeExtendGroup':		{ 'desc': self.globalName,	'side': fitNode.side.get(),		'warble': 'grp',			'other': ['footRoll', 'toeExtend', 'ankle'], 				},
			'ankleGroup':			{ 'desc': self.subNames[1],	'side': fitNode.side.get(),		'warble': 'grp',			'other': ['footRoll', 'toeExtend', 'ankle'], 				},
			'ankleSource':			{ 'desc': self.subNames[1],	'side': fitNode.side.get(),		'warble': 'trans',			'other': ['footRoll', 'toeExtend', 'ankle', 'source'], 		},
			'ankleDest':			{ 'desc': self.subNames[1],	'side': fitNode.side.get(),		'warble': 'trans',			'other': ['footRoll', 'toeExtend', 'ankle', 'dest'], 		},
			'toeGroup':				{ 'desc': self.subNames[2],	'side': fitNode.side.get(),		'warble': 'grp',			'other': ['footRoll', 'toeExtend', 'toe'],  				},
			'toeSource':			{ 'desc': self.subNames[2],	'side': fitNode.side.get(),		'warble': 'trans',			'other': ['footRoll', 'toeExtend', 'toe', 'source'],		},
			'toeDest':				{ 'desc': self.subNames[2],	'side': fitNode.side.get(),		'warble': 'cond',			'other': ['footRoll', 'toeExtend', 'toe', 'dest'], 			},
		}

		names = utils.constructNames(namesDict)

		# Get parent's class data without overwriting
		legFkCtrls = self.fkCtrls[:]
		legIkCtrls = self.aimCtrls[:]




		# ============================= Rig Group =============================
		rigGroup = createNode('transform', n=names.get('footRollRigGroup', 'rnm_rigGroup'), p=self.rigGroup)
		self.step(rigGroup, 'rigGroup')
		xform(rigGroup, ws=1, m=xform(fitNode.jointsList[0].get(), q=1, ws=1, m=1))
		if self.dev: print 'RigGroup: %s' % rigGroup

		# ============================= Rig Node =============================
		rigNode = createNode('locator', n=names.get('rigNode', 'rnm_rigNode'), p=rigGroup)
		rigNode.hide()
		hideAttrs = [ rigNode.localPositionX, rigNode.localPositionY, rigNode.localPositionZ, rigNode.localScaleX, rigNode.localScaleY, rigNode.localScaleZ ]
		for attr in hideAttrs:
			attr.set(l=1, k=0, cb=0)
		if self.dev: print 'RigNode: %s' % rigNode
		
		# connect fitNode to rigNode
		if not hasAttr(fitNode, 'rigNode'):
			addAttr(fitNode, at='message', ln='rigNode', k=1)
		addAttr(rigNode, at='message', ln='fitNode', k=1)
		fitNode.rigNode.connect(rigNode.fitNode)
		if self.dev: print '%s.rigNode >> %s.fitNode' % (fitNode, rigNode)
		
		# connect rigNode to skeleNode
		if self.skeleNode:
			if not hasAttr(self.skeleNode, 'rigNodes'):
				addAttr(self.skeleNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='rigNodes')
			rigNode.message.connect(self.skeleNode.rigNodes, na=1)

		# rigNode global attributes
		addAttr(rigNode, k=1, h=0, dt='string', ln='rigType')
		rigNode.rigType.set('footRoll', l=1)
		addAttr(rigNode, k=1, h=0, at='message', ln='heirarchy')
		# addAttr(rigNode, k=0, h=1, at='message', ln='selNode')
		addAttr(rigNode, k=0, h=1, at='message', ln='rigGroup')
		rigGroup.message.connect(rigNode.rigGroup)

		col.setOutlinerRGB(rigNode, self.rigNodeColor)

		# ========================= Store Nodes =========================

		# self.fkCtrls = []
		# self.ikJoints = []
		# self.ikCtrls = []
		# self.crvs = []
		# self.pivotCtrls = []

		# ========================= FitNode Inputs =========================
		

		# fkScaleMirror = self.fitNode.fkScale.get()
		fkScaleMirror = True

		# Transforms
		fitJoints = fitNode.jointsList.get()

		# PVIK
		pvikFitNode = self.fitNode

		# Mirroring
		if fitNode.side.get() == 2:
			mirror=True
		else:
			mirror=False

		# Shapes
		pivotShapes = 	{'heel': fitNode.shapeHeel.get(), 'toe': fitNode.shapeToe.get(), 'bankIn': fitNode.shapeBankIn.get(), 'bankOut': fitNode.shapeBankOut.get(), 'ball': fitNode.shapeBall.get()}
		fkShapes = 		[None, fitNode.shapeFK.get()]
		

		pivotPoints = 	{'heel': fitNode.pivot_heel.get(), 'toe': fitNode.pivot_toe.get(), 'bankIn': fitNode.pivot_bankIn.get(), 'bankOut': fitNode.pivot_bankOut.get(), 'ball': fitJoints[1]}


		
		# ========================= RigNode Attributes =========================

		
		# Attributes
		# =====
		utils.cbSep(self.rigNode)
		if toeExtendSetup:
			addAttr(self.rigNode, ct='publish', ln='toePointExtend', min=0, max=1, dv=1, k=1)

		utils.cbSep(self.rigNode)
		addAttr(self.rigNode, ct='publish', ln='roll', softMinValue=-10, softMaxValue=10, k=1)
		addAttr(self.rigNode, ct='publish', ln='bank', softMinValue=-10, softMaxValue=10, k=1)
		
		utils.cbSep(self.rigNode)
		addAttr(self.rigNode, ct='publish', ln='pivotLimits', 		min=0, max=1, at='short', dv=1, k=1)
		# =====
		utils.cbSep(self.rigNode)
		addAttr(self.rigNode, ct='publish', ln='ballBackAngle', 		softMinValue=-1.7, softMaxValue=3.14, at='doubleAngle', dv=0, k=1)
		addAttr(self.rigNode, ct='publish', ln='heelBackAngle', 		softMinValue=-1.7, softMaxValue=3.14, at='doubleAngle', dv=0, k=1)
		addAttr(self.rigNode, ct='publish', ln='ballForwardAngle', 	softMinValue=-1.7, softMaxValue=3.14, at='doubleAngle', dv=0, k=1)
		addAttr(self.rigNode, ct='publish', ln='toeForwardAngle', 	softMinValue=-1.7, softMaxValue=3.14, at='doubleAngle', dv=0, k=1)
		addAttr(self.rigNode, ct='publish', ln='bankAngle', 			softMinValue=-1.7, softMaxValue=3.14, at='doubleAngle', dv=0, k=1)

		# ballHeelBackThreshold
		# ballHeelForwardThreshold
		# ballToeForwardThreshold


		# ========================= Constrain RigGroup =========================
		
		# Rig group should follow leg's result position, and ik control's result orientation when in IK
		# and should follow fk control[2] when in fk

		# ikResult = createNode('transform', n=self.names.get('ikResult', 'rnm_ikResult'), p=self.rigGroup)
		# self.step(ikResult, 'ikResult')
		# utils.snap(rigGroup, ikResult)
		# self.matrixConstraint(self.ikhConst.getParent(), ikResult, t=1, r=0)
		# self.matrixConstraint(self.ikCtrls[2], ikResult, t=0, r=1)
		
		# switch
		fkIkSwitchSS = spaceSwitch(
			constraintType='parent',
			constrained= rigGroup,
			p=self.ssGroup,
			prefix = self.names.get('fkIkSwitch', 'rnm_fkIkSwitch'),
			targets=[ legFkCtrls[-1], legIkCtrls[-1] ],
			offsets=True,
			labels=['FK', 'IK']
		)

		utils.cbSep(self.rigNode)
		addAttr(self.rigNode, ct='publish', k=1, dv=0, min=0, max=1, ln='fkIk', nn='FK/IK')
		self.rigNode.fkIk.connect(fkIkSwitchSS.rigNode.parentSpaceBlend)

		# Constrain swich control instead? or ikhConst could be handled later 
		# ikSwitchConst = fkIkSwitchSS.ctrlsList[0].extra.get()
		# self.matrixConstraint(self.ikhConst.getParent(), ikSwitchConst, t=1, r=0)
		# self.matrixConstraint(self.ikCtrls[2], ikSwitchConst, t=0, r=1)

		# TODO: Scale. Follow switchJoint[2]

		# # Follows either way
		# Source group
		# 	pivots
		# 		ankle source nodes
		# 			toe source node
		# 		aim groups themselves

		# # Switches between ik ctrl and ikhConst
		# Dest group
		# 	aim dest nodes

		# Aim Destination switch node
		# fkIkCtrlSwitch = createNode('transform', n=names.get('fkIkCtrlSwitch', 'rnm_fkIkCtrlSwitch'), p=rigGroup)
		# self.step(fkIkCtrlSwitch, 'fkIkCtrlSwitch')
		
		# fkIkDestSwtichSS = spaceSwitch(
		# 	constraintType='parent',
		# 	controller = fkIkCtrlSwitch,
		# 	constrained= fkIkCtrlSwitch,
		# 	p=rigGroup,
		# 	prefix = self.names.get('fkIkToeSS', 'rnm_fkIkToeSS'),
		# 	targets=[ legFkCtrls[2], legIkCtrls[2] ],
		# 	labels=['FK', 'IK']
		# )

		# self.rigNode.fkIk.connect(fkIkCtrlSwitch.parentSpaceBlend)



		# =============================================== FK setup =============================================== 
		self.fkCtrls = []
		fkRigGroup = self.buildFkSetup(transforms=fitJoints[0:2], shapes=fkShapes, selectionPriority=0, nameVar=['Foot', 'FK'], mirror=mirror, rigGroup=rigGroup)
		self.matrixConstraint(legIkCtrls[-1], fkRigGroup, t=1, r=1, s=1)
		self.fkVis.connect(fkRigGroup.v)
		
		# =============================================== IK setup ==================================================== 
		# ============================================= Pivots setup ================================================== 

		# Follows IK Control
		pivGroup = createNode('transform', n=names.get('pivGroup', 'rnm_pivGroup'), p=rigGroup)
		self.step(pivGroup, 'pivGroup')
		self.matrixConstraint(self.socket(self.aimCtrls[-1]), rigGroup)
		# xform(pivGroup, ws=1, m=xform(fitJoints[0], q=1, ws=1, m=1))
		self.ikVis.connect(pivGroup.v)


		pivotNames = [
		'heel',
		'bankIn',
		'bankOut',
		'toe',
		'ball'
		]

		# Create control heirarchy
		self.pivCtrlsDict = {}
		self.pivCtrls = []
		for i, piv in enumerate(pivotNames):
			# pivotNameCap = pivotNames[0][0].capitalize() + pivotNames[0][0:]

			ctrl = self.createControlHeirarchy(
				name=names.get(piv, 'rnm_%s' % piv), 
				transformSnap=pivotPoints[piv],
				selectionPriority=0,
				shape = pivotShapes[piv],
				ctrlParent=(self.pivCtrls[i-1] if i else pivGroup),
				t=False,
				s=False,
				par=(self.pivCtrls[i-1] if i else pivGroup))

			self.pivCtrlsDict[pivotNames[i]] = ctrl
			self.pivCtrls.append(ctrl)
			
			self.rigNode.pivotLimits.connect(ctrl.minRotZLimitEnable)
			ctrl.minRotZLimit.set(0)
			if i==1 or i==2: #banks
				ctrl.minRotXLimit.set(0)
				ctrl.maxRotXLimit.set(0)
				ctrl.minRotYLimit.set(0)
				ctrl.maxRotYLimit.set(0)
				self.rigNode.pivotLimits.connect(ctrl.minRotXLimitEnable)
				self.rigNode.pivotLimits.connect(ctrl.minRotYLimitEnable)
				self.rigNode.pivotLimits.connect(ctrl.maxRotXLimitEnable)
				self.rigNode.pivotLimits.connect(ctrl.maxRotYLimitEnable)
			if i==3: # Toe
				ctrl.minRotXLimit.set(0)
				ctrl.maxRotXLimit.set(0)
				self.rigNode.pivotLimits.connect(ctrl.minRotXLimitEnable)
				self.rigNode.pivotLimits.connect(ctrl.maxRotXLimitEnable)


		# Output
		pivAnkle = createNode('transform', n=names.get('pivAnkle', 'rnm_pivAnkle'), p=ctrl)
		xform(pivAnkle, ws=1, m=xform(fitJoints[0], q=1, ws=1, m=1))
		self.step(pivAnkle, 'pivAnkle')

		# Move ik stretch locator
		parent(self.aimCtrlLocs[1], pivAnkle, r=True, s=True)

		# Use pivot heirachy to drive ik handle
		# self.matrixConstraint(pivAnkle, self.ikhConst, t=1, r=1, s=1)
		self.matrixConstraint( pivAnkle, self.socket(self.aimCtrls[1]), t=1, r=1, offset=True, force=True, preserve=False )
		# breaks antipop
		# create tranform above antipop

		# Pivot Indicator
		indics = utils.boneIndic(pivAnkle, pivGroup, blackGrey=1)[0]
		self.debugVis.connect(indics.v)



		# ============================================= Pivots Bank ================================================== 
		for pivot in self.pivCtrls[0:2]:
			print 'MARKER'
			if self.dev:
				print pivot


		# TODO: Map values to roll and bank
		# self.buildRangeSequenceSetup(paramMapping=[-10,0,10], outputMapping=[[1,0,0], [0,1,0], [0,0,1]],  )

		# ============================================= Results setup ================================================== 

		# ### ANKLE
		staticGroup  = createNode('transform', n=names.get('staticGroup', 'rnm_staticGroup'), p=rigGroup)
		self.step(staticGroup, 'staticGroup')
		utils.snap(fitJoints[0], staticGroup)
		# self.matrixConstraint(self.rigExit, staticGroup, t=1, r=1, offset=True)
		self.matrixConstraint(pivAnkle, staticGroup, t=1, r=1, offset=True)
		
		staticAnkle = createNode('transform', n=names.get('staticAnkle', 'rnm_staticAnkle'), p=staticGroup)
		self.step(staticAnkle, 'staticAnkle')
		self.matrixConstraint(self.rigExit, staticAnkle)
		self.matrixConstraint(pivAnkle, staticAnkle, t=0, r=1) #

		staticToe = createNode('transform', n=names.get('staticToe', 'rnm_staticToe'), p=staticAnkle)
		self.step(staticToe, 'staticToe')
		utils.snap(fitJoints[1], staticToe)
		# self.matrixConstraint(self.rigExit, staticToe, t=1)
		self.matrixConstraint(self.pivCtrlsDict['toe'], staticToe, t=0, r=1)

		staticResults = [staticAnkle, staticToe]
		results = [staticAnkle, staticToe]

		# ============================================= Toe Extend setup ================================================== 
		# Create pointer objects that follow the ik control, offseting the joints rotations based on the result nodes
		if toeExtendSetup:


			# Source objects
			ankleSource = createNode('transform', n=names.get('ankleSource', 'rnm_ankleSource'), p=staticAnkle)
			self.step(ankleSource, 'ankleSource')

			toeSource = createNode('transform', n=names.get('toeSource', 'rnm_toeSource'), p=staticToe)
			self.step(toeSource, 'toeSource')


			toeExtendGroup  = createNode('transform', n=names.get('toeExtendGroup', 'rnm_toeExtendGroup'), p=rigGroup)
			self.step(toeExtendGroup, 'toeExtendGroup')
			utils.snap(fitJoints[0], toeExtendGroup)
			# self.matrixConstraint(self.rigExit, toeExtendGroup, t=1, r=1, offset=True)

			# Destination objects
			ankleDest = createNode('transform', n=names.get('ankleDest', 'rnm_ankleDest'), p=toeExtendGroup)
			self.step(ankleDest, 'ankleDest')
			utils.snap(fitJoints[1], ankleDest)
			self.matrixConstraint(self.pivCtrlsDict['ball'], ankleDest, t=True, r=1, offset=True)

			toeDest = createNode('transform', n=names.get('toeDest', 'rnm_toeDest'), p=toeExtendGroup)
			self.step(toeDest, 'toeDest')
			utils.snap(fitJoints[2], toeDest)
			self.matrixConstraint(self.pivCtrlsDict['toe'], toeDest, t=True, r=1, offset=True)

			# AIM IK SETUPS

			# # Rig group

			# Aim IK Setup
			ankle = self.buildAimIkSetup(source=ankleSource, dest=ankleDest, followInputs=True, stretch=True, rigGroup=staticAnkle)
			ankle.stretch.set(0)
			ankle.squash.set(1)
			ikAimResults = ankle.results.get()
			ikAimResults.remove(ikAimResults[-1])
			self.matrixConstraint(ikAimResults[0], toeSource)
			

			# toeSourceSS = spaceSwitch(
			# 	constraintType='point',
			# 	controller = toeSource,
			# 	constrained= toeSource,
			# 	prefix = self.names.get('toeExtendSS', 'rnm_toeExtendSS'),
			# 	p=aimGroup,
			# 	targets=[self.rigExit, ikAimResults[-1]],
			# 	labels=['Static', 'Extend']
			# )
			# self.rigNode.toePointExtend.connect(toeSource.pointSpaceBlend)

			# # ankle = self.aimIkSetup(source=ankleSource, dest=ankleDest)
			toe = self.buildAimIkSetup(source=toeSource, dest=toeDest, followInputs=True, stretch=False, rigGroup=staticToe)
			ikAimResults.extend(toe.results.get())
			ikAimResults.remove(ikAimResults[-1])
			# self.matrixConstraint(staticResults[1], toe, t=1, r=1)


			results = ikAimResults

			extendResults = []
			# Static switch
			for static, extend in zip(staticResults, results):
				extendSwitch = createNode('transform', n=self.names.get('extendSwitch', 'rnm_extendSwitch'), p=rigGroup)
				utils.snap(static, extendSwitch)
				self.step(extendSwitch, 'extendSwitch')

				extendSwitchSS = spaceSwitch(
					constraintType='parent',
					constrained= extendSwitch,
					prefix = self.names.get('toeExtendSS', 'rnm_toeExtendSS'),
					p=self.ssGroup,
					targets=[static, extend],
					labels=['Static', 'Extend'],
					offsets=False
				)
				self.rigNode.toePointExtend.connect(extendSwitchSS.rigNode.parentSpaceBlend)

				extendResults.append(extendSwitch)
			results = extendResults
		
		fkIkResults = []
		# fk ik switch
		# print legFkCtrls[2]
		# print self.fkCtrls[0]
		# print self.fkCtrls[1]
		# fkResults = [legFkCtrls[2], self.fkCtrls[0], self.fkCtrls[1]]
		for fk, ik in zip(self.fkCtrls, results):

			fkIkSwitch = createNode('transform', n=self.names.get('fkIkSwitch', 'rnm_fkIkSwitch'), p=rigGroup)
			utils.snap(static, fkIkSwitch)
			self.step(fkIkSwitch, 'fkIkSwitch')

			fkIkSwitchSS = spaceSwitch(
				constraintType='parent',
				constrained= fkIkSwitch,
				prefix = self.names.get('fkIkSwitchSS', 'rnm_fkIkSwitchSS'),
				p=self.ssGroup,
				targets=[self.socket(fk), self.socket(ik)],
				labels=['FK', 'IK'],
				offsets=False,
			)
			self.rigNode.fkIk.connect(fkIkSwitchSS.rigNode.parentSpaceBlend)

			fkIkResults.append(fkIkSwitch)
		if self.dev: print fkIkResults

		#=========================== Finalize =================================
		for n, result in enumerate(fkIkResults):
			namesDict={
				'bind':          		{'desc': self.globalName, 	'side': self.fitNode.side.get(),		'warble': 'bind',			'other': [unicode(n)]},
			}
			names = utils.constructNames(namesDict)
			self.socket(result).message.connect(self.rigNode.socketList, na=1)
			bind = createNode('joint', n=names.get('bind', 'rnm_bind'), p=result)
			self.bindList.append(bind)
			self.step(bind, 'bind')
			bind.hide()


		if self.dev: print '\n'

		if not isConnected(fitNode.rigNode, rigNode.fitNode):
			fitNode.rigNode.connect(rigNode.fitNode)

		# try:
		# 	self.setController(fkRigGroup, self.rigGroup)
		# 	self.setController(ikRigGroup, self.rigGroup)
		# 	self.setController(bezierRigGroup, self.rigGroup)
		# except:
		# 	pass
		# self.assetize()

		# rigNode Set
		# if not objExists('rigNodeSet'):
		# 	rigNodeSet = sets([self.rigNode], n='rigNodeSet')
		# else:
		# 	rigNodeSet = sets('rigNodeSet', e=True, forceElement=self.rigNode)
		

			
		self.freezeNodes()
		if self.dev: print 'Node Count: %s' % self.nodeCount
