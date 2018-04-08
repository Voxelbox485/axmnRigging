
import buildRig
class lips(buildRig.rig):

	def __init__(self, fitNode=None, rigNode=None):

		if fitNode is None and rigNode is None:
			raise Exception('No data specified.')

		elif fitNode is None:
			self.rigNode = rigNode
			# Put any attributes needed for initialized rigs here

		else:

			jointsList = fitNode.jointsList.get()
			# Initialize rigNode
			# Error Check:
			
			# Convert string input to PyNode if neccessary
			if isinstance(fitNode, str):
				fitNode = ls(fitNode)[0]

			if fitNode.rigType.get() != 'chain':
				raise Exception('Incorrect rig type: %s' % fitNode.rigType.get())

			self.crvs = []

			rig.__init__(self, fitNode)

			jointsList = fitNode.jointsList.get()
			# Move rigGroup
			xform(self.rigGroup, ws=1, m=xform(jointsList[0], q=1, ws=1, m=1))


			# fitNode attributes
			fkShapes = 		self.fitNode.fkShapes.get()
			ikShapes = 		self.fitNode.ikShapes.get()

			doBezier = False
			if hasAttr(self.fitNode, 'doBezier'):
				doBezier = bool(self.fitNode.doBezier.get())

			doMidBend = True
			if hasAttr(self.fitNode, 'doMidBend'):
				doMidBend = bool(self.fitNode.doMidBend.get())

			autoTwist = True
			if hasAttr(self.fitNode, 'autoTwist'):
				self.autoTwist = bool(self.fitNode.autoTwist.get())

			inbetweenJoints = 2
			if hasAttr(self.fitNode, 'inbetweenJoints'):
				inbetweenJoints = self.fitNode.inbetweenJoints.get()


			numJointsList = []
			for i in range(len(jointsList)-1):
				if not i==0:
					if i == len(jointsList):
						numJointsList.append(inbetweenJoints+1)
					else:
						numJointsList.append(inbetweenJoints)


			# Mirroring
			if self.fitNode.side.get() == 2:
				mirror=True
			else:
				mirror=False

			if self.fitNode.mirror.get() is False:
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



			# Naming
			self.globalName = self.fitNode.globalName.get()
			self.subNames = []
			subAttrs = listAttr(self.fitNode, st='subName*')
			for subAttr in subAttrs:
				self.subNames.append(self.fitNode.attr(subAttr).get())
			# print 'subnames:'
			# print self.subNames

			self.naming(0)
			self.names = utils.constructNames(self.namesDict)


			try:
				# ========================= RigNode Attributes =========================
				self.rigNode.rigType.set('lips', l=1)

				utils.cbSep(self.rigNode)
				addAttr(self.rigNode, ct='publish', ln='bendCtrlsVis', nn='Bend Ctrl Vis', at='short', min=0, max=1, dv=1, k=1)
				setAttr(self.rigNode.bendCtrlsVis, k=0, cb=1)

				addAttr(self.rigNode, ct='publish', ln='tangentCtrlsVis', min=0, max=1, dv=0, at='short', k=1)
				setAttr(self.rigNode.tangentCtrlsVis, k=0, cb=1)

				addAttr(self.rigNode, ct='publish', ln='offsetsCtrlsVis', min=0, max=1, dv=0, at='short', k=1)
				setAttr(self.rigNode.offsetsCtrlsVis, k=0, cb=1)

				utils.cbSep(self.rigNode)
				addAttr(self.rigNode, ln='upAxis', at='enum', enumName='Y=1:Z=2', dv=1, k=1)

				addAttr(self.rigNode, ln='tangentsDistanceScaling', softMinValue=0, softMaxValue=1, dv=0.5, k=1)

				# ========================= Vis Mults =========================
				# allVis Mults

				bendVisMult = createNode('multDoubleLinear', n=self.names.get('bendVisMult', 'rnm_bendVisMult'))
				self.bendVis = bendVisMult.o
				self.rigNode.allVis >> bendVisMult.i1
				self.rigNode.bendCtrlsVis >> bendVisMult.i2
				self.step(bendVisMult, 'bendVisMult')

				debugVisMult = createNode('multDoubleLinear', n=self.names.get('debugVisMult', 'rnm_debugVisMult'))
				self.debugVis = debugVisMult.o
				self.rigNode.allVis >> debugVisMult.i1
				self.rigNode.debugVis >> debugVisMult.i2
				self.step(debugVisMult, 'debugVisMult')

				tangentVisMult = createNode('multDoubleLinear', n=self.names.get('tangentVisMult', 'rnm_tangentVisMult'))
				self.tangentVis = tangentVisMult.o
				self.rigNode.allVis >> tangentVisMult.i1
				self.rigNode.tangentCtrlsVis >> tangentVisMult.i2
				self.step(tangentVisMult, 'tangentVisMult')

				offsetsVisMult = createNode('multDoubleLinear', n=self.names.get('offsetsVisMult', 'rnm_offsetsVisMult'))
				self.offsetsVis = offsetsVisMult.o
				self.rigNode.allVis >> offsetsVisMult.i1
				self.rigNode.offsetsCtrlsVis >> offsetsVisMult.i2
				self.step(offsetsVisMult, 'offsetsVisMult')

				# ========================= World Group =========================
				worldGroup = createNode('transform', n=self.names.get('worldGroup', 'rnm_worldGroup'), p=self.rigGroup)
				self.worldGroup = worldGroup
				self.step(worldGroup, 'worldGroup')
				worldGroup.inheritsTransform.set(0)
				xform(worldGroup, rp=[0,0,0], ro=[0,0,0], ws=1)

				
				controlGroup = createNode('transform', n=self.names.get('controlGroup', 'rnm_controlGroup'), p=self.rigGroup)
				self.step(controlGroup, 'controlGroup')

				self.lipCtrls = []
				# For each joint, create a control
				for i, jnt in enumerate(jointsList):
					lipCtrl = self.createControlHeirarchy(
						transformSnap = jnt,
						selectionPriority=0,
						mirror=mirrorList[i],
						name=self.names.get('lipCtrl', 'rnm_lipCtrl'), shape=fkShapes[i],
						par=controlGroup,
						ctrlParent=controlGroup,
						jntBuf=False)

					self.lipCtrls.append(lipCtrl)

				leftLipJnt, topLipJnt, rightLipJnt, botLipJnt = jointsList # TODO: determine in some other way?
				leftLipCtrl, topLipCtrl, rightLipCtrl, botLipCtrl = self.lipCtrls # TODO: determine in some other way?

				#=========================== Bezier Setup =================================
				print jointsList[:2]
				bezierRigGroup0 = self.buildBezierSetup(
					transforms=[leftLipJnt, topLipJnt, rightLipJnt],
					ctrlTransforms=[leftLipCtrl, topLipCtrl, rightLipCtrl],
					shapes=fkShapes,
					follow=True,
					twist=True,
					bias=False,
					twistAxisChoice=0,
					doNeutralize=True,
					mirror=False,
					bezChain=True, # ?
					)
				self.bendVis.connect(bezierRigGroup0.controlsVis)
				self.rigNode.tangentsDistanceScaling.connect(bezierRigGroup0.tangentsDistanceScaling)
		

				# bezierRigGroup1 = self.buildBezierSetup(
				# 	transforms=[leftLipJnt, botLipJnt, rightLipJnt],
				# 	ctrlTransforms=[leftLipCtrl, botLipCtrl, rightLipCtrl],
				# 	shapes=fkShapes,
				# 	follow=True,
				# 	twist=True,
				# 	bias=False,
				# 	twistAxisChoice=0,
				# 	doNeutralize=True,
				# 	mirror=False,
				# 	bezChain=True, # ?
				# 	)
				# self.bendVis.connect(bezierRigGroup1.controlsVis)
				# self.rigNode.tangentsDistanceScaling.connect(bezierRigGroup1.tangentsDistanceScaling)
				
				for ctrl in self.bendCtrls:
					ctrl.neutralize.set(1)
					ctrl.magnitude.set(1)


				#=========================== Bend Setup =================================
				# bendRigGroup = self.buildMidBendCurveSetup(transforms=self.fkCtrls, follow=True, shapes=ikShapes, controller=self.rigNode, mirror=mirror)

				# =========================== CurvePath =================================
				print numJointsList
				print bezierRigGroup0.uValues.get()
				
				if self.dev:
					print 'Control uValues:'
					print bezierRigGroup0.uValues.get()
					print 'NumJointsList: %s' % numJointsList
				
				crvPathRig0 = self.buildCurvePartitionsSetup(
					self.crvs[0], 
					partitionParams=bezierRigGroup0.uValues.get(),
					numJointsList=numJointsList,
					mirror=False,
					createOffsetControls=True,
					rotationStyle='curve',
					twist=True
				)
				results = crvPathRig0.results.get()
				self.offsetsVis.connect(crvPathRig0.v)

				for i in range(len(self.bendCtrls)):
					# addAttr(crvPathRig0, ln='partitionParameters', multi=True, numberOfChildren=3, k=1)
					print '\n'
					print bezierRigGroup0
					print bezierRigGroup0.attr('uValues%s' % i)
					print bezierRigGroup0.attr('uValues%s' % i).get()
					print crvPathRig0
					print crvPathRig0.attr('partitionParameter%s' % i)
					print crvPathRig0.attr('partitionParameter%s' % i).get()
					print '\n'
					bezierRigGroup0.attr('uValues%s' % i).connect(crvPathRig0.attr('partitionParameter%s' % i))

				print 'LEN'
				print len(self.twistAdds)
				print len(self.bendCtrls)
				for i in range(len(self.bendCtrls)):
					print '\n%s' % i
					# addAttr(self.bendCtrls[i], ln='twist', k=1)
					
					rangeStart = True if i==0 else False
					rangeEnd = True if i==(len(self.bendCtrls)-1) else False

					if not rangeEnd:
						self.bendCtrls[i].twist.connect(		self.twistAdds[i].input2D[0].getChildren()[0])
					if not rangeStart:
						self.bendCtrls[i].twist.connect(	self.twistAdds[i-1].input2D[0].getChildren()[1])
						
					if not rangeEnd:
						self.socket(self.bendCtrls[i]).twist.connect(	self.twistAdds[i].input2D[1].getChildren()[0])
					if not rangeStart:
						self.socket(self.bendCtrls[i]).twist.connect(	self.twistAdds[i-1].input2D[1].getChildren()[1])

				

				for i, res in enumerate(results):

					# Create a bind joint for each result transform (special naming for midJoints)
					
					self.naming(n=i)
					self.names = utils.constructNames(self.namesDict)
 					
 					if mirror:
 						res.scaleZ.set(-1)
 						res.rotateZ.set(180)

					bind = createNode('joint', n=self.names.get('bind', 'rnm_bind'), p=res)
					self.step(bind, 'bind')
					# xform(bind, ws=1, ro=xform(jointsList[0], q=1, ws=1, ro=1))
					self.bindList.append(bind)
					bind.rotate.set(0,0,0)
					bind.jointOrient.set(0,0,0)
					# bind.attr('type').set(18)
					# bind.otherType.set('%s' % i)
					# bind.drawLabel.set(1)
					bind.hide()




			#=========================== Finalize =================================
			finally:
				try:
					self.setController(bezierRigGroup, self.rigGroup)
					self.setController(crvPathRig, self.rigGroup)
				except:
					pass
				try:
					self.constructSelectionList(selectionName='bendCtrls', selectionList=self.bendCtrls)
					self.constructSelectionList(selectionName='tangentCtrls', selectionList=self.tangentCtrls)
					self.constructSelectionList(selectionName='offsetCtrls', selectionList=self.offsetCtrls)
					self.constructSelectionList(selectionName='frozenNodes', selectionList=self.freezeList)
				except:
					pass

				self.finalize()

	def naming0(self, i=0, n=0):
		try:
			globalName = self.globalName
		except:
			globalName = ''

		try:
			subName = self.subNames[i]
		except:
			subName = globalName

		side = self.fitNode.side.get()
		n = str(n)

		self.namesDict={			
			'asset':					{ 'desc': globalName, 	'side': side,		'warble': 'asset'},
			'bind':   					{ 'desc': globalName, 	'side': side,		'warble': 'bind',			'other': ['%s' % n]}, 								# 'type':multiplyDivide}

			'fkCtrl':   				{ 'desc': subName, 		'side': side,		'warble': None,			'other': ['FK']}, 								# 'type':multiplyDivide}
			'bendCtrl':   				{ 'desc': subName, 		'side': side,		'warble': None,			'other': ['bend']}, 								# 'type':multiplyDivide}
			'tangentCtrl':   			{ 'desc': subName, 		'side': side,		'warble': None,			'other': ['tangent', '%s' % n]}, 								# 'type':multiplyDivide}
			'offset':   				{ 'desc': subName, 		'side': side,		'warble': None,			'other': ['offset', '%s' % n]}, 								# 'type':multiplyDivide}

			'bendVisMult':             	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['bendVis'],			'type': 'multDoubleLinear' },
			'debugVisMult':            	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['debugVis'],			'type': 'multDoubleLinear' },
			'tangentVisMult':          	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['tangentVis'],		'type': 'multDoubleLinear' },
			'offsetsVisMult':          	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['offsetsVis'],		'type': 'multDoubleLinear' },

			'worldGroup':              	{ 'desc': globalName,	'side':	side,		'warble': 'worldGroup',		'other':[],					'type': 'transform' },
			'fkRigGroup':              	{ 'desc': globalName,	'side':	side,		'warble': 'rigGroup',		'other': ['fkRigGroup', 'FK'],			'type': 'transform' },

			'bezierRigGroup':          	{ 'desc': globalName,	'side':	side,		'warble': 'rigGroup',		'other': ['bezier'],						'type': 'transform' },
			'upAxisSwitch':            	{ 'desc': globalName,	'side':	side,		'warble': 'cond',			'other': ['upAxisSwitch', 'bezier'],			'type': 'condition' },
			'bezierControlsGroup':     	{ 'desc': globalName,	'side':	side,		'warble': 'controlsGroup',	'other': [ 'bezier'],							'type': 'transform' },
			'staticLocGroup':          	{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['staticLocGroup', 'bezier'],			'type': 'transform' },
			'bendControlGroup':        	{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['bendControl', n],				'type': 'transform' },
			'fkControlsGroup':        	{ 'desc': globalName,	'side':	side,		'warble': 'rigGroup',		'other': ['fk'],							'type': 'transform' },
			
			'ori':                     	{ 'desc': globalName,	'side':	side,		'warble': 'ori',			'other': ['ori', 'bezier', n],				'type': 'orientConstraint' },
			'oriSR':                   	{ 'desc': globalName,	'side':	side,		'warble': 'rng',			'other': ['oriSR', 'bezier', n],			'type': 'setRange' },
			'oriRev':                  	{ 'desc': globalName,	'side':	side,		'warble': 'rev',			'other': ['oriRev', 'bezier', n],			'type': 'reverse' },
			
			
			'tangentMirror':           	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['mirror', 'tangent'],			'type': 'transform' },
			'neutralWorldUpStart':     	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['neutralWorldUpStart', 'tangent'],			'type': 'transform' },
			'neutralWorldUpEnd':       	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['neutralWorldUpEnd', 'tangent'],			'type': 'transform' },
			'neutralizeAllBlend':      	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',			'other': ['neutralizeAllBlend', 'tangent', n],			'type': 'blendTwoAttr' },
			'neutralizeTangentBlend':  	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',			'other': ['neutralizeTangentBlend', 'tangent', n],			'type': 'blendTwoAttr' },
			'neutralBlend':            	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',			'other': ['neutralBlend', 'tangent', n],			'type': 'blendColors' },
				
			'magDistBlend':            	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',			'other': ['magDistBlend', 'tangent', n],			'type': 'blendColors' },
			'magBlend':              	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',			'other': ['magBlend', 'tangent', n],			'type': 'blendTwoAttr' },
			'magMult':               	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['magMult-1', n, 'tangent'],			'type': 'multiplyDivide' },
			'magLengthMult':           	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['magLengthMult', 'tangent', n],			'type': 'multiplyDivide' },
			'magMult0':                	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['magMult0', 'tangent', n],			'type': 'multiplyDivide' },
			'crv':                     	{ 'desc': globalName,	'side':	side,		'warble': 'crv',			'other': ['bezier'],				'type': 'transform' },
			'curveLength':             	{ 'desc': globalName,	'side':	side,		'warble': 'crvInfo',		'other': ['length', 'tangent', n],				'type': 'curveInfo' },
			'pointLoc':                	{ 'desc': globalName,	'side':	side,		'warble': 'loc',			'other': ['point', 'tangent', n],				'type': 'locator' },
			'parametricCurveRigGroup': 	{ 'desc': globalName,	'side':	side,		'warble': 'rigGroup',		'other': ['curve'],			'type': 'transform' },
			'curvePathGroup':          	{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['curvePathGroup', 'tangent', n],			'type': 'transform' },
			'edgeRange':               	{ 'desc': globalName,	'side':	side,		'warble': 'rng',			'other': ['edgeRange', 'tangent', n],			'type': 'setRange' },
			'paramRange':              	{ 'desc': globalName,	'side':	side,		'warble': 'rng',			'other': ['paramRange', 'tangent', n],			'type': 'setRange' },
			'mp':                      	{ 'desc': globalName,	'side':	side,		'warble': 'mp',				'other': ['mp', 'tangent', n],			'type': 'motionPath' },
			'twistParamRev':           	{ 'desc': globalName,	'side':	side,		'warble': 'rev',			'other': ['twistParamRev', 'tangent', n],			'type': 'reverse' },
			'twistStartMult':          	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['twistStartMult', 'tangent', n],			'type': 'multDoubleLinear' },
			'twistEndMult':            	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['twistEndMult', 'tangent', n],			'type': 'multDoubleLinear' },
			'twistAdd':                	{ 'desc': globalName,	'side':	side,		'warble': 'add',			'other': ['twistAdd', 'tangent', n],			'type': 'addDoubleLinear' },
			'cmpMtrx':                 	{ 'desc': globalName,	'side':	side,		'warble': 'cmpMtrx',		'other': ['cmpMtrx', 'tangent', n],			'type': 'composeMatrix' },
			'multMtrx':                	{ 'desc': globalName,	'side':	side,		'warble': 'multMtrx',		'other': ['multMtrx', 'tangent', n],			'type': 'multMatrix' },
			'decmpMtrx':               	{ 'desc': globalName,	'side':	side,		'warble': 'decmpMtrx',		'other': ['decmpMtrx', 'tangent', n],			'type': 'decomposeMatrix' },
			'scaleInput':              	{ 'desc': globalName,	'side':	side,		'warble': 'scaleInput',		'other': ['scaleInput', 'tangent', n],			'type': 'transform' },
		}


