
import buildRig
class midBendChain(buildRig.rig):

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
			endShapes = 	self.fitNode.ikShapes.get()
			# midShapes  = 	self.fitNode.midShapes.get()

			numJointsList = []
			for i in range(len(jointsList)):
				if not i==0:
					if i == len(jointsList):
						numJointsList.append(3)
					else:
						numJointsList.append(2)


			# Mirroring
			if self.fitNode.side.get() == 2:
				mirror=True
			else:
				mirror=False

			if self.fitNode.mirror.get() is False:
				mirror=False



			doBend = True
			doFK = False
			oneCurve = False
			autoTwist = True

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
				self.rigNode.rigType.set('midBendChain', l=1)

				if self.doFK:
					utils.cbSep(self.rigNode)
					addAttr(self.rigNode, ln='fkVis', nn='FK Vis', at='short', min=0, max=1, dv=1)
					setAttr(self.rigNode.fkVis, keyable=False, channelBox=True)

				addAttr(self.rigNode, ct='publish', ln='offsetCtrlsVis', at='short', min=0, max=1, dv=0, k=1)
				setAttr(self.rigNode.offsetCtrlsVis, k=0, cb=1)
				utils.cbSep(self.rigNode)
				addAttr(self.rigNode, ct='publish', ln='bendCtrlsVis', nn='Bend Ctrl Vis', at='short', min=0, max=1, dv=1, k=1)
				setAttr(self.rigNode.bendCtrlsVis, k=0, cb=1)


				if not hasAttr(self.rigNode, 'upAxis'):
					utils.cbSep(self.rigNode)
					addAttr(self.rigNode, ln='upAxis', at='enum', enumName='Y=1:Z=2', dv=1, k=1)

				# ========================= Vis Mults =========================
				# allVis Mults
				if self.doFK:
					fkVisMult = createNode('multDoubleLinear', n=self.names.get('fkVisMult', 'rnm_fkVisMult'))
					self.fkCtrlsVis = fkVisMult.o
					self.rigNode.allVis >> fkVisMult.i1
					self.rigNode.fkVis >> fkVisMult.i2
					self.step(fkVisMult, 'fkVisMult')

				bendVisMult = createNode('multDoubleLinear', n=self.names.get('bendVisMult', 'rnm_bendVisMult'))
				self.bendCtrlsVis = bendVisMult.o
				self.rigNode.allVis >> bendVisMult.i1
				self.rigNode.bendCtrlsVis >> bendVisMult.i2
				self.step(bendVisMult, 'bendVisMult')

				offsetVisMult = createNode('multDoubleLinear', n=self.names.get('offsetVisMult', 'rnm_ikVisMult'))
				self.offsetCtrlsVis = offsetVisMult.o
				self.rigNode.allVis >> offsetVisMult.i1
				self.rigNode.offsetCtrlsVis >> offsetVisMult.i2
				self.step(offsetVisMult, 'offsetVisMult')

				debugVisMult = createNode('multDoubleLinear', n=self.names.get('debugVisMult', 'rnm_debugVisMult'))
				self.debugVis = debugVisMult.o
				self.rigNode.allVis >> debugVisMult.i1
				self.rigNode.debugVis >> debugVisMult.i2
				self.step(debugVisMult, 'debugVisMult')

				# ========================= World Group =========================
				worldGroup = createNode('transform', n=self.names.get('worldGroup', 'rnm_worldGroup'), p=self.rigGroup)
				self.worldGroup = worldGroup
				self.step(worldGroup, 'worldGroup')
				worldGroup.inheritsTransform.set(0)
				xform(worldGroup, rp=[0,0,0], ro=[0,0,0], ws=1)


				# =========================== FK Setup =================================
				if self.doFK:
					fkGroup = self.buildFkSetup(shapes=fkShapes, transforms=jointsList, mirror=mirror)
					self.fkCtrlsVis.connect(fkGroup.v)
					self.fkCtrls = fkGroup.results.get()

				# for fkCtrl in self.fkCtrls:
					# fkCtrl.message.connect(self.rigNode.fkCtrls, )

				#=========================== Bend Setup =================================
				bendRigGroup = self.buildMidBendCurveSetup(transforms=(self.fkCtrls if self.doFK else jointsList), follow=(True if self.doFK else False), shapes=endShapes, controller=self.rigNode, mirror=mirror)
				# print numJointsList
				# print bendRigGroup.uValues.get()

				crvPathRig = self.buildCurvePartitionsSetup(
					self.crvs[0],
					constraintTargets=(self.fkCtrls[:-1] if self.doFK else self.bendCtrls[:-1]),
					partitionParams=bendRigGroup.uValues.get(),
					numJointsList=numJointsList,
					mirror=mirror,
					createOffsetControls=True,
					rotationStyle='aim',
					twist=True
				)

				results = crvPathRig.results.get()
				self.offsetCtrlsVis.connect(crvPathRig.v)

				for i in range(len(jointsList)):
					# addAttr(crvPathRig, ln='partitionParameters', multi=True, numberOfChildren=3, k=1)
					print bendRigGroup
					print bendRigGroup.attr('uValues%s' % i)
					print bendRigGroup.attr('uValues%s' % i).get()
					print crvPathRig
					print crvPathRig.attr('partitionParameter%s' % i)
					print crvPathRig.attr('partitionParameter%s' % i).get()
					print '\n'
					bendRigGroup.attr('uValues%s' % i).connect(crvPathRig.attr('partitionParameter%s' % i))


				twistSettingsList = []
				if autoTwist:
					for i in range(len(self.bendCtrls)):
						twistSettings = self.socket(self.bendCtrls[i])
						twistExtractorMatrix(self.bendCtrls[i], (self.fkCtrls[0].buf.get() if self.doFK else self.bendCtrls[i].buf.get()), settingsNode=twistSettings)
						twistSettingsList.append(twistSettings)

			
				for i in range(len(self.bendCtrls)):
					print '\n%s' % i
					addAttr(self.bendCtrls[i], ln='twist', k=1)
					
					rangeStart = True if i==0 else False
					rangeEnd = True if i==(len(self.bendCtrls)-1) else False

					if not rangeEnd:
						self.bendCtrls[i].twist.connect(		self.twistAdds[i].input2D[0].getChildren()[0])
					if not rangeStart:
						self.bendCtrls[i].twist.connect(	self.twistAdds[i-1].input2D[0].getChildren()[1])
						
					if autoTwist:
						if not rangeEnd:
							twistSettingsList[i].twist.connect(	self.twistAdds[i].input2D[1].getChildren()[0])
						if not rangeStart:
							twistSettingsList[i].twist.connect(	self.twistAdds[i-1].input2D[1].getChildren()[1])



				# self.bendCtrls[i-1].percentage.connect(offsetsGroup.startPoint)
				# self.bendCtrls[i-1].twist.connect(offsetsGroup.startTwist)
				# self.bendCtrls[i].percentage.connect(offsetsGroup.endPoint)
				# self.bendCtrls[i].twist.connect(offsetsGroup.endTwist)


				for i, res in enumerate(results):
					# Create a bind joint for each result transform (special naming for midJoints)
					self.naming(n=i)
					self.names = utils.constructNames(self.namesDict)

					bind = createNode('joint', n=self.names.get('bind', 'rnm_bind'), p=res)
					self.step(bind, 'bind')
					xform(bind, ws=1, ro=xform(jointsList[0], q=1, ws=1, ro=1))
					self.bindList.append(bind)
					# bind.attr('type').set(18)
					# bind.otherType.set('%s' % i)
					# bind.drawLabel.set(1)
					bind.hide()



			#=========================== Finalize =================================
			finally:

				self.setController(fkRigGroup, self.rigGroup)
				self.setController(bezierRigGroup, self.rigGroup)
				self.setController(crvPathRig, self.rigGroup)
				try:
					self.constructSelectionList(selectionName='bendCtrls', selectionList=self.bendCtrls)
					self.constructSelectionList(selectionName='tangentCtrls', selectionList=self.tangentCtrls)
					self.constructSelectionList(selectionName='offsetCtrls', selectionList=self.offsetCtrls)
					self.constructSelectionList(selectionName='frozenNodes', selectionList=self.freezeList)
				except:
					pass

				self.finalize()

	def naming(self, i=0, n=None):
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
			'tangentVisMult':         	{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['tangentVisMult', 'base'],			'type': 'multDoubleLinear' },
			'offsetsVisMult':         	{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['offsetsVisMult', 'base'],			'type': 'multDoubleLinear' },
			'bezierRigGroup':         	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['bezierRigGroup', 'bezier'],			'type': 'transform' },
			'bezierControlsGroup':    	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['bezierControlsGroup', 'bezier'],			'type': 'transform' },
			'staticLocGroup':         	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['staticLocGroup', 'bezier'],			'type': 'transform' },
			'bendControlGroup':       	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['bendControlGroup', 'bezier'],			'type': 'transform' },
			'buf':                    	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['buf', 'bezier'],			'type': 'transform' },
			'const':                  	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['const', 'bezier'],			'type': 'transform' },
			'extra':                  	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['extra', 'bezier'],			'type': 'transform' },
			'ctrl':                   	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['ctrl', 'bezier'],			'type': 'transform' },
			'ctrlTag':                	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['ctrlTag', 'bezier'],			'type': 'controller' },
			'socketNode':             	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['socketNode', 'bezier'],			'type': 'transform' },
			'ori':                    	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['ori', 'bezier'],			'type': 'orientConstraint' },
			'oriSR':                  	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['oriSR', 'bezier'],			'type': 'setRange' },
			'oriRev':                 	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['oriRev', 'bezier'],			'type': 'reverse' },
			'tangentMirror':          	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['tangentMirror', 'tangent'],			'type': 'transform' },
			'neutralWorldUpStart':    	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['neutralWorldUpStart', 'tangent'],			'type': 'transform' },
			'neutralWorldUpEnd':      	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['neutralWorldUpEnd', 'tangent'],			'type': 'transform' },
			'neutralizeAllBlend':     	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['neutralizeAllBlend', 'tangent', n],			'type': 'blendTwoAttr' },
			'neutralizeTangentBlend': 	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['neutralizeTangentBlend', 'tangent', n],			'type': 'blendTwoAttr' },
			'neutralBlend':           	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',	'other': ['neutralBlend', 'tangent', n],			'type': 'blendColors' },
			'magDistBlend':           	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',	'other': ['magnitude', 'distance', 'tangent'],			'type': 'blendColors' },
			'magBlend':             	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',	'other': ['magnitude', 'tangent'],			'type': 'blendTwoAttr' },
			'magMult':              	{ 'desc': globalName,	'side':	side,		'warble': 'mult',	'other': ['magnitude', 'tangent'],			'type': 'multiplyDivide' },
			'magLengthMult':          	{ 'desc': globalName,	'side':	side,		'warble': 'mult',	'other': ['magnitude', 'length', 'tangent'],			'type': 'multiplyDivide' },

		}

