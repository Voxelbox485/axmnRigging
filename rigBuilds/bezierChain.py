from pymel.core import *
import utils
import buildRig
class bezierChain(buildRig.rig):

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

			buildRig.rig.__init__(self, fitNode)

			jointsList = fitNode.jointsList.get()
			# Move rigGroup
			xform(self.rigGroup, ws=1, m=xform(jointsList[0], q=1, ws=1, m=1))
			# fitNode attributes

			fkShapes = 		self.fitNode.fkShapes.get()
			ikShapes = 		self.fitNode.ikShapes.get()



			doCloseLoop = False
			if hasAttr(self.fitNode, 'closeLoop'):
				doCloseLoop = bool(self.fitNode.closeLoop.get())

			doFK = True
			if hasAttr(self.fitNode, 'doFK'):
				doFK = bool(self.fitNode.doFK.get())

			doBend = True
			if hasAttr(self.fitNode, 'doBend'):
				doBend = bool(self.fitNode.doBend.get())

			autoTwist = True
			if hasAttr(self.fitNode, 'autoTwist'):
				autoTwist = bool(self.fitNode.autoTwist.get())

			doOffsets = True
			if hasAttr(self.fitNode, 'offsets'):
				doOffsets = bool(self.fitNode.offsets.get())

			fkTwist = True
			if hasAttr(self.fitNode, 'fkTwist'):
				fkTwist = bool(self.fitNode.fkTwist.get())

			if not doFK:
				fkTwist = False

			doBias = False
			if hasAttr(self.fitNode, 'doBias'):
				doBias = bool(self.fitNode.doBias.get())

			inbetweenJoints = 3
			if hasAttr(self.fitNode, 'inbetweenJoints'):
				inbetweenJoints = self.fitNode.inbetweenJoints.get()

			rotationStyle = 'aim'
			if hasAttr(self.fitNode, 'rotationStyle'):
				rotationStyle = self.fitNode.rotationStyle.get(asString=True)

			doNeutralize = 'aim'
			if hasAttr(self.fitNode, 'doNeutralize'):
				doNeutralize = bool(self.fitNode.doNeutralize.get())


			twistAxis = 0

			numJointsList = []
			for i in range(len(jointsList)):
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


			print 'mirrorList:'
			print mirrorList



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
				self.rigNode.rigType.set('bezier', l=1)

				utils.cbSep(self.rigNode)
				# addAttr(self.rigNode, ln='ikVis', nn='IK Vis', at='short', min=0, max=1, dv=1)
				# setAttr(self.rigNode.ikVis, keyable=False, channelBox=True)
				
				if doBend:
					utils.cbSep(self.rigNode)
					addAttr(self.rigNode, ct='publish', ln='bendCtrlsVis', nn='Bend Ctrl Vis', at='short', min=0, max=1, dv=1, k=1)
					setAttr(self.rigNode.bendCtrlsVis, k=0, cb=1)

					addAttr(self.rigNode, ct='publish', ln='tangentCtrlsVis', min=0, max=1, dv=0, at='short', k=1)
					setAttr(self.rigNode.tangentCtrlsVis, k=0, cb=1)

					addAttr(self.rigNode, ct='publish', ln='offsetsCtrlsVis', min=0, max=1, dv=0, at='short', k=1)
					setAttr(self.rigNode.offsetsCtrlsVis, k=0, cb=1)


					if not hasAttr(self.rigNode, 'upAxis'):
						utils.cbSep(self.rigNode)
						addAttr(self.rigNode, ln='upAxis', at='enum', enumName='Y=1:Z=2', dv=1, k=1)


					addAttr(self.rigNode, ln='tangentsDistanceScaling', softMinValue=0, softMaxValue=1, dv=0.5, k=1)
				# ========================= Vis Mults =========================
				# allVis Mults
				# ikVisMult = createNode('multDoubleLinear', n=self.names.get('ikVisMult', 'rnm_ikVisMult'))
				# self.rigNode.allVis >> ikVisMult.i1
				# self.rigNode.ikVis >> ikVisMult.i2
				# self.step(ikVisMult, 'ikVisMult')

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


				# =========================== FK Setup =================================
				if doFK:
					fkGroup = self.buildFkSetup(shapes=fkShapes, transforms=jointsList, mirror=mirror)

				if doOffsets:
					offsetGroup = createNode('transform', n=self.names.get('offsetGroup', 'rnm_offsetGroup'), p=self.rigGroup)
					self.step(offsetGroup, 'offsetGroup')

					self.offsetCtrls = []
					for i, jnt in enumerate(jointsList):

						par = self.fkCtrls[i] if doFK else offsetGroup
						
						ctrlPar = None
						if i:
							ctrlPar = self.offsetCtrls[i-1]
						if doFK:
							ctrlpar =  self.fkCtrls[i]

						offsetCtrl = self.createControlHeirarchy(
							name=self.names.get('offsetCtrl', 'rnm_offsetCtrl'), 
							transformSnap=jnt,
							selectionPriority=0,
							shape=ikShapes[i],
							ctrlParent=ctrlPar,
							outlinerColor = (0,0,0),
							par=par)

						self.offsetCtrls.append(offsetCtrl)

					# for fkCtrl in self.fkCtrls:
						# fkCtrl.message.connect(self.rigNode.fkCtrls, )

				#=========================== Bezier Setup =================================
					
				transforms = jointsList
				if doFK:
					transforms = self.fkCtrls
				if doOffsets:
					transforms = self.offsetCtrls

				bezierRigGroup = self.buildBezierSetup(
					transforms=transforms,
					ctrlTransforms=transforms,
					shapes=ikShapes,
					follow=True if doFK or doOffsets else False,
					twist=autoTwist,
					bias=doBias,
					twistAxisChoice=0,
					doNeutralize=doNeutralize,
					mirror=mirrorList,
					bezChain=doFK,
					closeLoop=doCloseLoop
					)
				self.bendVis.connect(bezierRigGroup.controlsVis)

				self.rigNode.tangentsDistanceScaling.connect(bezierRigGroup.tangentsDistanceScaling)

				for ctrl in self.bendCtrls:
					if doNeutralize:
						ctrl.neutralize.set(1)
					ctrl.magnitude.set(1)



				#=========================== Bend Setup =================================
				# bendRigGroup = self.buildMidBendCurveSetup(transforms=self.fkCtrls, follow=True, shapes=ikShapes, controller=self.rigNode, mirror=mirror)

				# if self.dev: print 'Control uValues: %s' % (bezierRigGroup.uValues.get())
				
				crvPathRig = self.buildCurvePartitionsSetup(
					self.crvs[0], 
					partitionParams=bezierRigGroup.uValues.get(),
					constraintTargets=(self.fkCtrls[:-1] if doFK else None),
					numJointsList=numJointsList,
					mirror=mirror,
					createOffsetControls=True,
					rotationStyle=rotationStyle,
					twist=True
				)
				results = crvPathRig.results.get()
				self.offsetsVis.connect(crvPathRig.v)

				for i in range(len(self.bendCtrls)):
					# addAttr(crvPathRig, ln='partitionParameters', multi=True, numberOfChildren=3, k=1)
					if self.dev:
						print bezierRigGroup
						print bezierRigGroup.attr('uValues%s' % i)
						print bezierRigGroup.attr('uValues%s' % i).get()
						print crvPathRig
						print crvPathRig.attr('partitionParameter%s' % i)
						print crvPathRig.attr('partitionParameter%s' % i).get()
						print '\n'
					bezierRigGroup.attr('uValues%s' % i).connect(crvPathRig.attr('partitionParameter%s' % i))

				twistSettingsList = []
				if fkTwist:
					for i in range(len(jointsList)):
						twistSettings = self.socket(self.fkCtrls[i])
						buildRig.twistExtractorMatrix(self.fkCtrls[i], (self.fkCtrls[i].buf.get()), settingsNode=twistSettings)
						twistSettings.mult.set(-1)
						twistSettingsList.append(twistSettings)
			
				for i in range(len(self.bendCtrls)):
					# addAttr(self.bendCtrls[i], ln='twist', k=1)
					
					rangeStart = True if i==0 else False
					rangeEnd = True if i==(len(self.bendCtrls)-1) else False

					if not rangeEnd:
						self.bendCtrls[i].twist.connect(		self.twistAdds[i].input2D[0].getChildren()[0])
					if not rangeStart:
						self.bendCtrls[i].twist.connect(	self.twistAdds[i-1].input2D[0].getChildren()[1])
						
					if autoTwist:
						if not rangeEnd:
							self.socket(self.bendCtrls[i]).twist.connect(	self.twistAdds[i].input2D[1].getChildren()[0])
						if not rangeStart:
							self.socket(self.bendCtrls[i]).twist.connect(	self.twistAdds[i-1].input2D[1].getChildren()[1])

				if fkTwist:
					for i in range(len(self.fkCtrls)):
						rangeEnd = True if i==(len(self.bendCtrls)-1) else False
						if not rangeEnd:
							(twistSettingsList[i].twist.connect(			self.twistAdds[i].input2D[2].getChildren()[0]	))

				# scaleLengthGroup = self.buildScaleLengthSetup(scaleInputs=self.bendCtrls, nodes=results, settingsNode=self.rigNode)

				for i, res in enumerate(results):

					# Create a bind joint for each result transform (special naming for midJoints)
					
					self.naming(n=i)
					self.names = utils.constructNames(self.namesDict)
 					

					res.message.connect(self.rigNode.socketList, na=1)

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
					self.setController(fkGroup, self.rigGroup)
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

	def naming(self, i=0, n=0):
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
