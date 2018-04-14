from pymel.core import *
import utils
import buildRig
class aimIK(buildRig.rig):

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

			if fitNode.rigType.get() != 'aimIK':
				raise Exception('Incorrect rig type: %s' % fitNode.rigType.get())

			if fitNode.hasAttr('inbetweenJoints'):
				inbetweenJoints = fitNode.inbetweenJoints.get()
			else:
				inbetweenJoints = 0

			self.crvs = []

			buildRig.rig.__init__(self, fitNode)

			jointsList = fitNode.jointsList.get()
			orientControlsList = [fitNode.startOriCtrl.get(), fitNode.endOriCtrl.get()]
			# Move rigGroup
			xform(self.rigGroup, ws=1, m=xform(jointsList[0], q=1, ws=1, m=1))
			# fitNode attributes

			bindEnd = self.fitNode.bindEnd.get()
			doFK = self.fitNode.fkEnable.get()
			ikEndInherit = self.fitNode.ikEndInherit.get()
			doStretch = self.fitNode.doStretch.get()
			doTwist = self.fitNode.doTwist.get()
			doVolume = self.fitNode.doVolume.get()
			doScaling = self.fitNode.doScaling.get()
			twistAxis = 0

			if doFK:
				fkShape = 		(self.fitNode.fkShape.get() if self.fitNode.fkVis.get() else None)
			else:
				fkShape = 		None
			
			
			ikShapes = 		[(self.fitNode.startShape.get() if self.fitNode.ikVisStart.get() else None), self.fitNode.endShape.get() if self.fitNode.ikVisEnd.get() else None]
			
			doIkStartCtrl = 	self.fitNode.ikVisStart.get()
			doIkEndCtrl = 		self.fitNode.ikVisEnd.get()

			

			twistAxisChoice = 0
			# up = None:
			up = self.fitNode.up.get()

			# Mirroring
			if self.fitNode.side.get() == 2:
				mirror=True
			else:
				mirror=False

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
			self.rigNode.rigType.set('aimIK', l=1)

			utils.cbSep(self.rigNode)
			if doFK:
				addAttr(self.rigNode, ct='publish', ln='fkVis', nn='FK Vis', at='short', min=0, max=1, dv=1)
				setAttr(self.rigNode.fkVis, keyable=False, channelBox=True)
				

			addAttr(self.rigNode, ct='publish', ln='ikVis', nn='IK Vis', at='short', min=0, max=1, dv=1)
			setAttr(self.rigNode.ikVis, keyable=False, channelBox=True)
			

			addAttr(self.rigNode, ct='publish', ln='offsetCtrlsVis', min=0, max=1, dv=0, keyable=1)
			self.rigNode.offsetCtrlsVis.set(k=0, cb=1)

			if doStretch:
				addAttr(self.rigNode, ct='publish', ln='squash', min=0, max=1, dv=1, keyable=1)
				addAttr(self.rigNode, ct='publish', ln='stretch', min=0, max=1, dv=1, keyable=1)
			

				utils.cbSep(self.rigNode, ct='publish')
				addAttr(self.rigNode, ct='publish', ln='restLength', min=0.01, dv=1, keyable=1)
				addAttr(self.rigNode, ct='publish', ln='currentNormalizedLength', min=0, dv=1, keyable=1)

			utils.cbSep(self.rigNode, ct='publish')
			addAttr(self.rigNode, ln='upAxis', at='enum', enumName='Y=1:Z=2', dv=2, k=1)

			addAttr(self.rigNode, ln='iKCtrlStart', nn='IK Ctrl Start', at='message')
			addAttr(self.rigNode, ln='iKCtrlEnd', nn='IK Ctrl End', at='message')
			addAttr(self.rigNode, ln='fkCtrl', nn='FK Ctrl Start', at='message')


			# ========================= Vis Mults =========================
			# allVis Mults
			if doFK:
				fkVisMult = createNode('multDoubleLinear', n=self.names.get('fkVisMult', 'rnm_fkVisMult'))
				self.rigNode.allVis >> fkVisMult.i1
				self.rigNode.fkVis >> fkVisMult.i2
				self.step(fkVisMult, 'fkVisMult')
				self.fkVis = fkVisMult.o

			ikVisMult = createNode('multDoubleLinear', n=self.names.get('ikVisMult', 'rnm_ikVisMult'))
			self.rigNode.allVis >> ikVisMult.i1
			self.rigNode.ikVis >> ikVisMult.i2
			self.step(ikVisMult, 'ikVisMult')
			self.ikVis = ikVisMult.o

			# offsetVisMult = createNode('multDoubleLinear', n=self.names.get('offsetVisMult', 'rnm_offsetVisMult'))
			# self.rigNode.allVis >> offsetVisMult.i1
			# self.rigNode.ikVis >> offsetVisMult.i2
			# self.step(offsetVisMult, 'offsetVisMult')
			# self.offsetVis = offsetVisMult.o

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
			# 

			self.ssGroup = createNode('transform', n=self.names.get('ssGroup', 'rnm_ssGroup'), p=self.rigGroup)
			self.step(self.ssGroup, 'ssGroup')

			# =========================== FK Setup =================================

			if doFK:
				fkGroup = self.buildFkSetup(shapes=[fkShape], transforms=[jointsList[0]], mirror=mirror)
				self.fkVis.connect(fkGroup.v)
				for fkCtrl in self.fkCtrls:

					if self.dev: 
						print '\n\n'
						print '%s' % self.rigsGroup
						print '%s' % fkCtrl.buf.get()
					fkCtrl.message.connect(self.rigNode.fkCtrl)
					fkOriCtrlSS = buildRig.spaceSwitch(
						constraintType='orient',
						controller = fkCtrl,
						constrained= fkCtrl.const.get(),
						prefix = self.names.get('fkOriCtrlSS', 'rnm_fkOriCtrlSS'),
						# p=self.rigGroup,
						p=self.ssGroup,
						targets=[self.rigsGroup, fkCtrl.buf.get()],
						labels=['World', 'Parent'],
						offsets=True,
					)
					fkOriCtrlSS.setDefaultBlend(1)

					


			# =========================== Aim Ik Setup =================================
			
			aimIKGroup = self.buildAimIkSetup(
				source=orientControlsList[0], 
				dest=orientControlsList[1], 
				worldUpLocation=up, 

				inbetweenJoints=inbetweenJoints, 
				controller=self.rigNode, 
				sourceShape=ikShapes[0], 
				destShape=ikShapes[1],
				registerControls = [bool(doIkStartCtrl), bool(doIkEndCtrl)],
				stretch=doStretch,
				twist=doTwist,
				volume=doVolume,
				scaling=doScaling,
				twistAxisChoice=twistAxisChoice
			)
			self.ikVis.connect(aimIKGroup.v)

			aimIKGroup.results.get()[0].message.connect(self.rigNode.socketList, na=1)
			aimIKGroup.results.get()[1].message.connect(self.rigNode.socketList, na=1)

			# if doIkStartCtrl:
			# 	startOriCtrlSS = buildRig.spaceSwitch(
			# 		constraintType='orient',
			# 		controller = self.aimCtrls[0],
			# 		constrained= self.aimCtrls[0].const.get(),
			# 		prefix = self.names.get('startOriCtrlSS', 'rnm_startOriCtrlSS'),
			# 		p=self.ssGroup,
			# 		targets=[self.rigsGroup, self.aimCtrls[0].buf.get()],
			# 		labels=['World', 'Parent'],
			# 		offsets=True,
			# 	)
			# 	startOriCtrlSS.setDefaultBlend(1)

			if doIkEndCtrl:
				endOriCtrlSS = buildRig.spaceSwitch(
					constraintType='orient',
					controller = self.aimCtrls[1],
					constrained= self.aimCtrls[1].const.get(),
					prefix = self.names.get('endOriCtrlSS', 'rnm_endOriCtrlSS'),
					p=self.ssGroup,
					# p=self.ssGroup,
					targets=[self.rigsGroup, self.aimCtrls[1].buf.get()],
					labels=['World', 'Parent'],
					offsets=True,
				)
				endOriCtrlSS.setDefaultBlend(1)

					
			self.aimCtrls[0].message.connect(self.rigNode.iKCtrlStart)
			self.aimCtrls[1].message.connect(self.rigNode.iKCtrlEnd)

			if doFK:
				self.matrixConstraint(self.socket(fkCtrl), aimIKGroup, r=1, s=1, offset=False)


			for i, trans in enumerate(aimIKGroup.results.get()):
				# If end is not being bound, skip last
				if not bindEnd:
					if trans is aimIKGroup.results.get()[-1]:
						break
			
				# Create a bind joint for each result transform (special naming for midJoints)
				if inbetweenJoints:
					n=i
				else:
					n=0
				self.naming(i=i, n=n)
				self.names = utils.constructNames(self.namesDict)

				bind = createNode('joint', n=self.names.get('bind', 'rnm_bind'), p=trans)
				self.step(bind, 'bind')
				xform(bind, ws=1, ro=xform(jointsList[0], q=1, ws=1, ro=1))
				self.bindList.append(bind)
				bind.hide()


			# Create an exit node
			self.rigExit = createNode('transform', n=self.names.get('rigExit', 'rnm_rigExit'), p=self.rigGroup)
			
			# End result for translation, end control for rotation and scale
			# T
			self.matrixConstraint(self.socket(aimIKGroup.results.get()[-1]), self.rigExit, t=1, offset=False)
			# R (snap offset from jointsList)
			utils.snap(jointsList[-1], self.socket(self.aimCtrls[1]))
			self.matrixConstraint(self.socket(self.aimCtrls[1]), self.rigExit, t=0, r=1, s=1, offset=False)
			self.step(self.rigExit, 'rigExit')

			self.rigExit.message.connect(self.rigNode.socketList, na=1)

			self.naming(i=2)
			self.names = utils.constructNames(self.namesDict)


			doFootRoll = False
			if hasAttr(self.fitNode, 'subNode'):
				if self.fitNode.subNode.get():	
					if self.fitNode.subNode.get().rigType.get() == 'footRoll':
						if self.fitNode.subNode.get().build.get():
							if self.dev:
								print 'FOOTROLL:'
								print self.fitNode.subNode.get()
							doFootRoll = True

			if not doFootRoll:
				if bindEnd:
					# No need for exit bind if there's a rigExtension (expand to include hand rig when it's done)
					rigExitBind = createNode( 'joint', n=self.names.get( 'rigExitBind', 'rnm_rigExitBind'), p=self.rigExit )
					self.step(rigExitBind, 'rigExitBind')
					self.bindList.append(rigExitBind)
					rigExitBind.hide()

			else:
				# self.buildFootRollSetup(self.fitNode.subNode.get()) AIMIK
				pass

			#=========================== Finalize =================================
			if doFK:
				for fkCtrl in self.fkCtrls:
					self.socket(fkCtrl).message.connect(self.rigNode.socketList, na=1)

			try:
				if doFK:
					self.setController(fkRigGroup, self.rigGroup)
				self.setController(aimIKGroup, self.rigGroup)
			except:
				pass


			try:
				if doFK:
					self.constructSelectionList(selectionName='fkCtrls', selectionList=self.fkCtrls)
			
				self.constructSelectionList(selectionName='aimCtrls', selectionList=self.aimCtrls)
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
		if not n is None:
			n = '%s' % (n)

		self.namesDict={
			'asset':				{'desc': globalName, 	'side': side,		'warble': 'asset'},			
			'fkVisMult':          	{ 'desc': globalName,	'side': side,		'warble': 'mult',			'other': ['fk', 'vis'], 						'type': 'multDoubleLinear' },
			'ikVisMult':          	{ 'desc': globalName,	'side': side,		'warble': 'mult',			'other': ['ik', 'vis'], 						'type': 'multDoubleLinear' },
			'debugVisMult':       	{ 'desc': globalName,	'side': side,		'warble': 'mult',			'other': ['debug', 'vis'], 						'type': 'multDoubleLinear' },
			'fkControlsGroup':      { 'desc': globalName,	'side': side,		'warble': 'rigGroup',			'other': ['fk',], 								'type': 'transform' },
			'fkCtrl':               { 'desc': globalName,	'side': side,		'warble': None,				'other': ['fk'], 								'type': 'transform' },
			'aimIkGroup':         	{ 'desc': globalName,	'side': side,		'warble': 'rigGroup',			'other': ['ik'], 									'type': 'transform' },
			'aimIkControlsGroup': 	{ 'desc': globalName,	'side': side,		'warble': 'grp',			'other': ['ik', 'controls'], 							'type': 'transform' },
			'startCtrl':			{ 'desc': subName,		'side': side,		'warble': None,				'other': ['ik', 'start'], 							'type': 'transform' },
			'endCtrl':				{ 'desc': subName,		'side': side,		'warble': None,				'other': ['ik', 'end'], 								'type': 'transform' },
			'midCtrl':				{ 'desc': globalName,	'side': side,		'warble': None,				'other': ['mid',  n], 					'type': 'transform' },
			'startResult':        	{ 'desc': subName,		'side': side,		'warble': 'trans',			'other': ['start', 'result'], 					'type': 'transform' },
			'endResult':          	{ 'desc': subName,		'side': side,		'warble': 'trans',			'other': ['end', 'result'], 					'type': 'transform' },
			'upAxisSwitch':       	{ 'desc': globalName,	'side': side,		'warble': 'cond',			'other': ['upAxis'], 							'type': 'condition' },
			'staticLengthGroup':  	{ 'desc': globalName,	'side': side,		'warble': 'grp',			'other': ['static', 'ctrl', 'distance'], 		'type': 'transform' },
			'staticLocStart':     	{ 'desc': subName,		'side': side,		'warble': 'loc',			'other': ['static', 'distance', 'start'], 		'type': 'transform' },
			'staticLocEnd':       	{ 'desc': subName,		'side': side,		'warble': 'loc',			'other': ['static', 'distance', 'end'], 		'type': 'transform' },
			'staticLength':       	{ 'desc': globalName,	'side': side,		'warble': 'dist',			'other': ['static', 'distance'], 				'type': 'distanceBetween' },
			'locStart':           	{ 'desc': subName,		'side': side,		'warble': 'loc',			'other': ['distance', 'start'], 				'type': 'locator' },
			'locEnd':             	{ 'desc': subName,		'side': side,		'warble': 'loc',			'other': ['distance', 'end'], 					'type': 'locator' },
			'length':             	{ 'desc': globalName,	'side': side,		'warble': 'dist',			'other': ['ctrl', 'distance'], 					'type': 'distanceBetween' },
			'normalizeDiv':       	{ 'desc': globalName,	'side': side,		'warble': 'div',			'other': ['ctrl', 'distance', 'normalize'], 	'type': 'multiplyDivide' },
			'stretchBlend':       	{ 'desc': globalName,	'side': side,		'warble': 'blnd',			'other': ['stretch'], 							'type': 'blendTwoAttr' },
			'squashBlend':        	{ 'desc': globalName,	'side': side,		'warble': 'blnd',			'other': ['squash'], 							'type': 'blendTwoAttr' },
			'stretchMap':         	{ 'desc': globalName,	'side': side,		'warble': 'remap',			'other': ['stretch'], 							'type': 'blendTwoAttr' },
			'fkRigGroup':			{ 'desc': globalName,	'side': side,		'warble': 'rigGroup',			'other': ['fk'], 								'type': 'blendTwoAttr' },
			'bind':          		{'desc': subName, 		'side': side,		'warble': 'bind',			'other': [n]},
			'rigExit':        		 {'desc': globalName, 	'side': side,		'warble': 'trans',			'other': ['rigExit']},
			'rigExitBind':          {'desc': globalName, 	'side': side,		'warble': 'bind',			'other': ['rigExit']},

			'ssGroup':           	{ 'desc': globalName,	'side':	side,		'warble': 'grp',		'other': ['ss'],			'type': 'transform' },
			'aimIkResultGroup':  	{ 'desc': globalName,	'side':	side,		'warble': 'grp',		'other': ['result'],			'type': 'transform' },
			'midResult':         	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['midResult', n],			'type': 'transform' },
			'transMult':         	{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['mid', 'translate', n],			'type': 'multiplyDivide' },
			'mm':                	{ 'desc': globalName,	'side':	side,		'warble': 'multMat',		'other': ['constraint'],			'type': 'multMatrix' },
			'dcmp':              	{ 'desc': globalName,	'side':	side,		'warble': 'decmpMat',		'other': ['constraint'],			'type': 'decomposeMatrix' },
			
			'staticDistMult':    	{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['static', 'dist'],			'type': 'multDoubleLinear' },
			'squashStretchCond': 	{ 'desc': globalName,	'side':	side,		'warble': 'cond',		'other': ['squashStretch'],			'type': 'condition' },
			'restLengthMult':    	{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['restLength'],			'type': 'multDoubleLinear' },


			'fkOriCtrlSS':    	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['fk'],						},
			'offsetCtrl':    	{ 'desc': subName,		'side':	side,		'warble': None,		'other': ['offset'],						},
			'upObject':    		{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['up'],						},
			'upControlSS':    	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['up'],						},
			'endOriCtrlSS':    	{ 'desc': subName,		'side':	side,		'warble': None,		'other': ['ik', 'end'],						},
			

		}
