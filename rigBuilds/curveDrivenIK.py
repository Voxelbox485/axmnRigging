from pymel.core import *
import utils
import buildRig

class curveDrivenIK(buildRig.rig):

	def __init__(self, fitNode, crv, pointInput):
		with UndoChunk():


			# Initialize rigNode
			# Error Check:
			
			# Convert string input to PyNode if neccessary
			# if isinstance(fitNode, str):
			# 	fitNode = ls(fitNode)[0]

			# if fitNode.rigType.get() != 'bezierIK':
			# 	raise Exception('Incorrect rig type: %s' % fitNode.rigType.get())

			self.crv = crv

			buildRig.rig.__init__(self, fitNode)

			# Move rigGroup
			# xform(self.rigGroup, ws=1, m=xform(jointsList[0], q=1, ws=1, m=1))

			# Naming
			self.globalName = self.fitNode.globalName.get()
			self.subNames = []
			subAttrs = listAttr(self.fitNode, st='subName*')
			for subAttr in subAttrs:
				self.subNames.append(self.fitNode.attr(subAttr).get())


			doParametric = True
			doSplineIK = True

			# NAMING
			self.naming(0)
			self.names = utils.constructNames(self.namesDict)



			# ========================= RigNode Attributes =========================
			self.rigNode.rigType.set('curveDrivenIK', l=1)

			
			utils.cbSep(self.rigNode)

	
			addAttr(self.rigNode, ct='publish', ln='offsetCtrlsVis', at='short', min=0, max=1, dv=0, k=1)
			setAttr(self.rigNode.offsetCtrlsVis, keyable=False, channelBox=True)

			utils.cbSep(self.rigNode, ct='publish')
			# addAttr(self.rigNode, ln='bendCtrlsVis', nn='Bend Ctrl Vis', at='short', min=0, max=1, dv=1, k=1)
			# setAttr(self.rigNode.bendCtrlsVis, k=0, cb=1)

			
			# addAttr(self.rigNode, ln='neutralizeAll', min=0, max=1, dv=1, k=1)

			utils.cbSep(self.rigNode, ct='publish')
			addAttr(self.rigNode, ct='publish', ln='stretch', softMinValue=0, softMaxValue=1, dv=1, k=1)
			addAttr(self.rigNode, ct='publish', ln='squash', softMinValue=0, softMaxValue=1, dv=1, k=1)
			addAttr(self.rigNode, ct='publish', ln='restLength', min=0.01, dv=1, k=1)
			# addAttr(self.rigNode, ln='currentNormalizedLength', dv=0)
			# self.rigNode.currentNormalizedLength.set(k=0, cb=1)
		
			if not hasAttr(self.rigNode, 'upAxis'):
				utils.cbSep(self.rigNode)
				addAttr(self.rigNode,ln='upAxis', at='enum', enumName='Y=1:Z=2', dv=1, k=1)

			

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


			try:

				
				# if doFK:
				# 	self.matrixConstraint(self.fkCtrls[-1], bezierRigGroup, r=1, s=1)

				displaySmoothness(self.crv, pointsWire=16)

				ikSplineRig = self.buildIKSplineSetup(
					crv=self.crv, 
					points=pointInput, 
					selectionPriority=2,
				)

				results = ikSplineRig.results.get()

			

				# # # =========================== Twist ===========================
				# # #### Bend ctrls
				# if doParametric and not doStretchLimit:
				# 	self.bendCtrls[0].twist.connect(				self.twistAdds[0].input2D[0].getChildren()[0])
				# 	self.socket(self.bendCtrls[0]).twist.connect(	self.twistAdds[0].input2D[1].getChildren()[0])

				# 	self.bendCtrls[1].twist.connect(				self.twistAdds[0].input2D[0].getChildren()[1])
				# 	self.socket(self.bendCtrls[1]).twist.connect(	self.twistAdds[0].input2D[1].getChildren()[1])

				# if doSplineIK:
				# 	self.bendCtrls[0].twist.connect(				self.twistAdds[0].input2D[0].getChildren()[0])
				# 	self.socket(self.bendCtrls[0]).twist.connect(	self.twistAdds[0].input2D[1].getChildren()[0])

				# 	self.bendCtrls[1].twist.connect(				self.twistAdds[0].input2D[0].getChildren()[1])
				# 	self.socket(self.bendCtrls[1]).twist.connect(	self.twistAdds[0].input2D[1].getChildren()[1])



				# staticLocatorsGroup = createNode('transform', n=self.names.get('staticLocatorsGroup', 'rnm_staticLocatorsGroup'), p=ikSplineRig)
				# self.step(staticLocatorsGroup, 'staticLocatorsGroup')

				# bezLocs = []
				# staticBezLocs = []
				# i=0
				# print '\n'
				# print crvPathRig.results.get()
				# print ikSplineRig.results.get()
				
				# for bezPoint, ikJnt in zip(crvPathRig.results.get(), ikSplineRig.results.get()):
					
				# 	# if i==4:
				# 	# 	raise Exception('4')

				# 	bezLoc2 = createNode('locator', n='%s_dist_LOC' % bezPoint, p=bezPoint)
				# 	self.step(bezLoc2, 'bezLoc')
				# 	bezLoc2.hide()
				# 	bezLocs.append(bezLoc2)

				# 	# 

				# 	staticBezPoint = createNode('transform', n=self.names.get('staticBezPoint', 'rnm_staticBezPoint'), p=staticLocatorsGroup)
				# 	self.step(staticBezPoint, 'staticBezPoint')
				# 	utils.snap(bezPoint, staticBezPoint)

				# 	staticBezLoc2 = createNode('locator', n='%s_dist_LOC' % staticBezPoint, p=staticBezPoint)
				# 	self.step(staticBezLoc2, 'staticBezLoc')
				# 	staticBezLoc2.hide()
				# 	staticBezLocs.append(staticBezLoc2)

				# 	if not i==0: # Skip 0
				# 		# Distance
				# 		bezLoc1 = bezLocs[i-1]
				# 		staticBezLoc1 = staticBezLocs[i-1]

				# 		bezDist = createNode('distanceBetween', n=self.names.get('bezDist', 'rnm_bezDist'))
				# 		self.step(bezDist, 'bezDist')

				# 		bezLoc1.worldPosition.connect(bezDist.point1)
				# 		bezLoc2.worldPosition.connect(bezDist.point2)

				# 		# Static distance
				# 		staticBezDist = createNode('distanceBetween', n=self.names.get('staticBezDist', 'rnm_staticBezDist'))
				# 		self.step(staticBezDist, 'staticBezDist')

				# 		staticBezLoc1.worldPosition.connect(staticBezDist.point1)
				# 		staticBezLoc2.worldPosition.connect(staticBezDist.point2)

				# 		# # Mult static by rig input
				# 		staticBezDistMult = createNode('multDoubleLinear', n=self.names.get('staticBezDistMult', 'rnm_staticBezDistMult'))
				# 		self.step(staticBezDistMult, 'staticBezDistMult')
				# 		staticBezDist.distance.connect(staticBezDistMult.i1)
				# 		self.rigNode.restLength.connect(staticBezDistMult.i2)

				# 		# Normalize
				# 		normalizeDiv = createNode('multiplyDivide', n=self.names.get('normalizeDiv', 'rnm_normalizeDiv'))
				# 		self.step(normalizeDiv, 'normalizeDiv')
				# 		normalizeDiv.operation.set(2)

				# 		bezDist.distance.connect(normalizeDiv.input1X)
				# 		staticBezDistMult.output.connect(normalizeDiv.input2X)



				# 		# Stretch
				# 		stretchBlend = createNode( 'blendTwoAttr', n=self.names.get('stretchBlend', 'rnm_stretchBlend') )
				# 		self.step(stretchBlend, 'stretchBlend')
				# 		stretchBlend.i[0].set(1)
				# 		normalizeDiv.outputX.connect(stretchBlend.i[1])
				# 		self.rigNode.stretch.connect(stretchBlend.ab)


				# 		# Squash
				# 		squashBlend = createNode( 'blendTwoAttr', n=self.names.get('squashBlend', 'rnm_squashBlend') )
				# 		self.step(squashBlend, 'squashBlend')
				# 		squashBlend.i[0].set(1)
				# 		normalizeDiv.outputX.connect(squashBlend.i[1])
				# 		self.rigNode.squash.connect(squashBlend.ab)


				# 		# Squash/Stretch combiner
				# 		squashStretchCond = createNode( 'condition', n=self.names.get('stretchBlend', 'rnm_stretchBlend') )
				# 		self.step(squashStretchCond, 'squashStretchCond')
				# 		squashStretchCond.operation.set(2) # Greater Than
				# 		normalizeDiv.outputX.connect(squashStretchCond.firstTerm)

				# 		squashStretchCond.secondTerm.set(1)

				# 		stretchBlend.o.connect(squashStretchCond.colorIfTrueR)
				# 		squashBlend.o.connect(squashStretchCond.colorIfFalseR)


				# 		restLengthMult = createNode('multDoubleLinear', n=self.names.get('restLengthMult', 'rnm_restLengthMult'))
				# 		self.step(restLengthMult, 'restLengthMult')
				# 		squashStretchCond.outColorR.connect(restLengthMult.i1)
				# 		self.rigNode.restLength.connect(restLengthMult.i2)


				# 		denormalizeMult = createNode('multDoubleLinear', n=self.names.get('denormalizeMult', 'rnm_denormalizeMult'))
				# 		self.step(denormalizeMult, 'denormalizeMult')
				# 		denormalizeMult.i1.set(bezDist.distance.get())
				# 		restLengthMult.o.connect(denormalizeMult.i2)
						

				# 		denormalizeMult.o.connect(ikJnt.tx)

						

				# 	i=i+1

				# results = ikSplineRig.results.get()



				offsetResults = []
				# Offset controls
				for i, point in enumerate(results):
					ctrlParent = None
				
					ctrlParent = offsetResults[i-1] if i else self.rigGroup

					self.naming(n=i)
					self.names = utils.constructNames(self.namesDict)
					par = point
					offsetCtrl = self.createControlHeirarchy(
						name=self.names.get('offsetCtrl', 'rnm_offsetCtrl'), 
						transformSnap=point,
						selectionPriority=2,
						ctrlParent=ctrlParent,
						outlinerColor = (0,0,0),
						par=par)

					offsetResults.append(offsetCtrl)
					self.rigNode.offsetCtrlsVis.connect(offsetCtrl.buf.get().v)

				results = offsetResults

				# results = self.buildScaleLengthSetup(scaleInputs=self.bendCtrls, distanceInputs=[results[0], results[1]], nodes=results, settingsNode=self.rigNode)

				# results = []
				print 'Results:'
				print results
				for i, point in enumerate(results):

					self.naming(n=i)
					self.names = utils.constructNames(self.namesDict)



					point.message.connect(self.rigNode.socketList, na=1)
					# self.socketList.append(point)
				
					bind = createNode('joint', n=self.names.get('bind', 'rnm_bind'), p=point)
					self.bindList.append(bind)
					self.step(bind, 'bind')
					bind.hide()


				# crvPathRig = self.buildParametricCurveRigSetup(
				# 	self.crv,
				# 	numJoints=1,
				# 	stretch=False
				# 	)
				# results = crvPathRig.results.get()


				# rigExit = createNode('transform', n=self.names.get('rigExit', 'rnm_rigExit'), p=self.rigGroup)
				# self.step(rigExit, 'rigExit')
				# self.socket(rigExit).message.connect(self.rigNode.socketList, na=1)
				# utils.snap(point, rigExit)
				# self.matrixConstraint(point, rigExit, t=1, r=1, s=1, offset=True)

				# if bindEnd:
				# 	# # rig exit bind
				# 	rigExitBind = createNode( 'joint', n=self.names.get( 'rigExitBind', 'rnm_rigExitBind'), p=rigExit )
				# 	self.step(rigExitBind, 'rigExitBind')
				# 	self.bindList.append(rigExitBind)
				# 	rigExitBind.hide()


				#=========================== Finalize =================================

			except:
				raise

			finally:
				# try:
				# 	for bendCtrl in self.bendCtrls:
				# 		attrs = bendCtrl.s.getChildren()
				# 		for a in attrs:
				# 			a.set(l=1, k=0)
				# except:
				# 	pass
				# try:
				# 	self.setController(fkGroup, self.rigGroup)
				# 	self.setController(bezierRigGroup, self.rigGroup)
				# except:
				# 	pass
				try:
					# self.constructSelectionList(selectionName='bendCtrls', selectionList=self.bendCtrls)
					# self.constructSelectionList(selectionName='tangentCtrls', selectionList=self.tangentCtrls)
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
		side = self.fitNode.side.get()
		n = '%s' % n

		self.namesDict={			
			'asset':					{'desc': globalName, 	'side': side,		'warble': 'asset'},
			'bind':          			{'desc': globalName, 	'side': side,		'warble': 'bind',			'other': [n]														},
			'rigExit':        			{'desc': globalName, 	'side': side,		'warble': 'trans',			'other': ['rigExit']												},
			'rigExitBind':       		{'desc': globalName, 	'side': side,		'warble': 'bind',			'other': ['rigExit']												},
		
			'bendCtrl':       			{'desc': subName, 		'side': side,		'warble': None,				'other': ['bend']													},
			'tangentCtrl':       		{'desc': subName, 		'side': side,		'warble': None,				'other': ['tangent']												},
			'offset':       			{'desc': globalName, 	'side': side,		'warble': None,				'other': ['offset', n]												},
			'offsetCtrl':       		{'desc': globalName, 	'side': side,		'warble': None,				'other': ['splineOffset', n]										},
			'fkCtrl':       			{'desc': globalName, 	'side': side,		'warble': None,				'other': ['fk', n]													},
		
			
			'ikVisMult':               	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['ik', 'vis'],												'type': 'multDoubleLinear' },
			'fkVisMult':               	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['fk', 'vis'],												'type': 'multDoubleLinear' },
			'debugVisMult':            	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['debug', 'vis',],											'type': 'multDoubleLinear' },
			'fkIkAutoMult':            	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['fkIkAutoMult', 'fkIkAutoVis'],							'type': 'multDoubleLinear' },
			'fkCond':                  	{ 'desc': globalName,	'side':	side,		'warble': 'cond',			'other': ['fkCond', 'fkIkAutoVis'],									'type': 'condition' },
			'ikCond':                  	{ 'desc': globalName,	'side':	side,		'warble': 'cond',			'other': ['ikCond', 'fkIkAutoVis'],									'type': 'condition' },
			'fkAutoCond':              	{ 'desc': globalName,	'side':	side,		'warble': 'cond',			'other': ['fkAutoCond', 'fkIkAutoVis'],								'type': 'condition' },
			'ikAutoCond':              	{ 'desc': globalName,	'side':	side,		'warble': 'cond',			'other': ['ikAutoCond', 'fkIkAutoVis'],								'type': 'condition' },
			'worldGroup':              	{ 'desc': globalName,	'side':	side,		'warble': 'worldGroup',		'other': [],														'type': 'transform' },
			'bezierRigGroup':          	{ 'desc': globalName,	'side':	side,		'warble': 'rigGroup',		'other': ['bezier'],												'type': 'transform' },
			'fkControlsGroup':			{ 'desc': globalName, 	'side': side,		'warble': 'rigGroup',		'other': ['fk']											},
			'upAxisSwitch':            	{ 'desc': globalName,	'side':	side,		'warble': 'cond',			'other': ['upAxisSwitch', 'bezier'],								'type': 'condition' },
			'bezierControlsGroup':     	{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['bezier', 'controls'],									'type': 'transform' },
			'staticLocGroup':          	{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['bezier', 'staticLocGroup',],								'type': 'transform' },
			'bendControlGroup':        	{ 'desc': subName,		'side':	side,		'warble': 'grp',			'other': ['bendControlGroup', 'bezier'],							'type': 'transform' },
			'bezier':                   { 'desc': subName,		'side':	side,		'warble': None,				'other': [],														'type': 'transform' },
			'tangent':                  { 'desc': subName,		'side':	side,		'warble': None,				'other': [n],												'type': 'transform' },
			'boneIndic':               	{ 'desc': subName,		'side':	side,		'warble': 'indic',			'other': ['tangent'],												'type': 'transform' },
			'tangentMirror':           	{ 'desc': subName,		'side':	side,		'warble': 'mir',			'other': ['tangent'],												'type': 'transform' },
			'magDistBlend':            	{ 'desc': subName,		'side':	side,		'warble': 'blnd',			'other': ['mag', 'dist', 'tangent', n],						'type': 'blendColors' },
			'magBlend-1':              	{ 'desc': subName,		'side':	side,		'warble': 'blnd',			'other': ['mag', 'tangent', n],								'type': 'blendTwoAttr' },
							
			'magMult':               	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['mag', 'tangent', n],								'type': 'multiplyDivide' },
			'magLengthMult':           	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['mag', 'length', 'tangent', n],					'type': 'multiplyDivide' },
			'magBlend':               	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',			'other': ['mag', 'tangent', n],								'type': 'blendTwoAttr' },
			'magMult':                	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['mag', 'tangent', n],								'type': 'multiplyDivide' },
			'crv':                     	{ 'desc': globalName,	'side':	side,		'warble': 'crv',			'other': [],														'type': 'transform' },
			'curveLength':             	{ 'desc': globalName,	'side':	side,		'warble': 'crvInfo',		'other': ['crv', 'length'],											'type': 'curveInfo' },
			'pointLoc':                	{ 'desc': globalName,	'side':	side,		'warble': 'loc',			'other': ['pointLoc', n],									'type': 'locator' },
			'parametricCurveRigGroup': 	{ 'desc': globalName,	'side':	side,		'warble': 'rigGroup',		'other': ['parametric', 'crv'],										'type': 'transform' },
			'curvePathGroup':          	{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['curvePath'],												'type': 'transform' },
			'edgeRange':               	{ 'desc': globalName,	'side':	side,		'warble': 'rng',			'other': ['edge', 'parametric'],									'type': 'setRange' },
			'paramRange':              	{ 'desc': globalName,	'side':	side,		'warble': 'rng',			'other': ['parameter', n],								'type': 'setRange' },
			'mp':                      	{ 'desc': globalName,	'side':	side,		'warble': 'mp',				'other': ['parametric', n],											'type': 'motionPath' },
			'cmpMtrx':                 	{ 'desc': globalName,	'side':	side,		'warble': 'cmpMtrx',		'other': ['mpConst', n],													'type': 'composeMatrix' },
			'multMtrx':                	{ 'desc': globalName,	'side':	side,		'warble': 'multMtrx',		'other': ['multMtrx', 'mpConst', n],										'type': 'multMatrix' },
			'decmpMtrx':               	{ 'desc': globalName,	'side':	side,		'warble': 'decmpMtrx',		'other': ['decmpMtrx', 'mpConst', n],									'type': 'decomposeMatrix' },
			'scaleInput':              	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['scale', 'modifier', n],							'type': 'transform' },
			'ikRigSplineGroup':        	{ 'desc': globalName,	'side':	side,		'warble': 'rigGroup',		'other': ['splineIK'],												'type': 'transform' },
			'upNode':                  	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['upAxis', 'splineIK'],									'type': 'transform' },
			'upAxisCond':              	{ 'desc': globalName,	'side':	side,		'warble': 'cond',			'other': ['upAxis', 'splineIK'],									'type': 'condition' },
			'upAxisIkhCond':           	{ 'desc': globalName,	'side':	side,		'warble': 'cond',			'other': ['upAxis', 'ikh', 'splineIK'],								'type': 'condition' },
			'rootVector':              	{ 'desc': globalName,	'side':	side,		'warble': 'vecProd',		'other': ['rootVector', 'splineIK'],								'type': 'vectorProduct' },
			'twistReduceMult':         	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['twistReduce', 'splineIK'],								'type': 'multDoubleLinear' },
			'endTwistRestoreSub':      	{ 'desc': globalName,	'side':	side,		'warble': 'sub',			'other': ['endTwistRestore', 'splineIK'],							'type': 'plusMinusAverage' },
			'jointsGroup':             	{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['joints', 'splineIK'],									'type': 'transform' },
			'splineJnt':               	{ 'desc': globalName,	'side':	side,		'warble': 'jnt',			'other': [n, 'splineIK'],							'type': 'joint' },
			'ikh':                     	{ 'desc': globalName,	'side':	side,		'warble': 'ikh',			'other': ['splineIK'],												'type': 'ikHandle' },
			'eff':                     	{ 'desc': globalName,	'side':	side,		'warble': 'eff',			'other': ['splineIK'],												'type': 'ikEffector' },
			'twistAdd':                	{ 'desc': globalName,	'side':	side,		'warble': 'add',			'other': ['twist', 'splineIK'],										'type': 'plusMinusAverage' },
			'staticLocatorsGroup':     	{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['staticLocs', 'splineIK'],								'type': 'transform' },
			'bezLoc':                  	{ 'desc': globalName,	'side':	side,		'warble': 'loc',			'other': ['bezier', 'dist', 'splineIK', n],					'type': 'locator' },
			'staticBezPoint':          	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['static', 'bezier', 'dist', 'splineIK', n],		'type': 'transform' },
			'staticBezLoc':            	{ 'desc': globalName,	'side':	side,		'warble': 'loc',			'other': ['static', 'bezier', 'dist', 'splineIK', n],		'type': 'locator' },
			'bezDist':                 	{ 'desc': globalName,	'side':	side,		'warble': 'dist',			'other': ['bezier', 'splineIK', n],							'type': 'distanceBetween' },
			'staticBezDist':           	{ 'desc': globalName,	'side':	side,		'warble': 'dist',			'other': ['static', 'bezier', 'dist', 'splineIK', n],		'type': 'distanceBetween' },
			'staticBezDistMult':       	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['static', 'bezier', 'dist', 'splineIK', n],		'type': 'multDoubleLinear' },
			'normalizeDiv':            	{ 'desc': globalName,	'side':	side,		'warble': 'div',			'other': [ 'bezier', 'dist', 'normalize', 'splineIK', n],	'type': 'multiplyDivide' },
			'stretchBlend':            	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',			'other': ['stretch', 'splineIK', n],							'type': 'blendTwoAttr' },
			'squashBlend':             	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',			'other': ['squash', 'splineIK', n],							'type': 'blendTwoAttr' },
			'squashStretchCond':       	{ 'desc': globalName,	'side':	side,		'warble': 'cond',			'other': ['squashStretch', 'splineIK', n],					'type': 'condition' },
			'restLengthMult':          	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['restLength', 'splineIK', n],						'type': 'multDoubleLinear' },
			'denormalizeMult':         	{ 'desc': globalName,	'side':	side,		'warble': 'mult',			'other': ['denormalize', 'splineIK', n],						'type': 'multDoubleLinear' },
			'fkIkGroup':               	{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['fkIk'],													'type': 'transform' },
			'fkRigGroup':              	{ 'desc': globalName,	'side':	side,		'warble': 'rigGroup',		'other': ['FK'],													'type': 'transform' },
			'fkEntrance':              	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['entrance', 'FK'],										'type': 'transform' },
			'ikEntrance':              	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['entrance', 'IK'],										'type': 'transform' },
			'rigEntrance':             	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['rigEntrance'],											'type': 'transform' },
			'fkExit':                  	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['exit', 'FK'],											'type': 'transform' },
			'ikExit':                  	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['exit', 'IK'],											'type': 'transform' },
			'switch':                  	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['fkIk', 'switch', n],								'type': 'transform' },
			'tangentDefault': 			{ 'desc': subName,		'side':	side,		'warble': None,				'other': ['tangent', 'default'],								'type': 'transform' },
			'switchGroup':    			{ 'desc': globalName,	'side':	side,		'warble': 'grp',			'other': ['switch', 'FK'],										'type': 'transform' },


			'neutralWorldUpStart':    	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['neutral', 'worldUp', 'start', 'tangent'],				'type': 'transform' },
			'neutralWorldUpEnd':      	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['neutral', 'worldUp', 'end', 'tangent'],					'type': 'transform' },
			'neutralizeAllBlend':     	{ 'desc': subName,		'side':	side,		'warble': 'blnd',			'other': ['neutralize', 'all', 'tangent'],							'type': 'blendTwoAttr' },
			'neutralizeTangentBlend': 	{ 'desc': subName,		'side':	side,		'warble': 'blnd',			'other': ['neutralize', 'tangent'],									'type': 'blendTwoAttr' },
			'neutralBlend':           	{ 'desc': subName,		'side':	side,		'warble': 'blnd',			'other': ['neutral', 'tangent'],									'type': 'blendColors' },

			'tangentDefaultAdd':      	{ 'desc': subName,		'side':	side,		'warble': 'add',			'other': ['tangentDefault', 'tangent'],								'type': 'plusMinusAverage' },
			'scaleMatrixSum':         	{ 'desc': globalName,	'side':	side,		'warble': 'multMtrx',		'other': ['scaleMatrixSum', n],					'type': 'multMatrix' },
			'scaleMatrixRes':         	{ 'desc': globalName,	'side':	side,		'warble': 'decmpMtrx',		'other': ['scaleMatrixRes', n],					'type': 'decomposeMatrix' },
			'scaleBlend':             	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',			'other': ['scaleBlend', n],						'type': 'blendColors' },
			'paramRev':               	{ 'desc': globalName,	'side':	side,		'warble': 'rev',			'other': ['paramRev', n],						'type': 'reverse' },

			'rigEntranceBuf':         	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['rigEntrance', 'buf' ],						'type': 'transform' },
			'rigExitBuf':             	{ 'desc': globalName,	'side':	side,		'warble': 'trans',			'other': ['rigExit', 'buf'],							'type': 'transform' },


			'ctrlDistance':          	{ 'desc': globalName,	'side':	side,		'warble': 'dist',		'other': ['ctrl', 'tangent'],			'type': 'distanceBetween' },
			'staticDistance':        	{ 'desc': globalName,	'side':	side,		'warble': 'dist',		'other': ['static', 'tangent'],			'type': 'distanceBetween' },
			'bendCtrlDistNormalize': 	{ 'desc': globalName,	'side':	side,		'warble': 'div',		'other': ['bendCtrl', 'dist', 'normalize', 'tangent'],			'type': 'multiplyDivide' },
			'staticLengthGroup':     	{ 'desc': globalName,	'side':	side,		'warble': 'grp',		'other': ['staticLength', 'scaling'],			'type': 'transform' },
			'staticLocStart':        	{ 'desc': globalName,	'side':	side,		'warble': 'trans',		'other': ['static', 'start', 'scaling'],			'type': 'transform' },
			'staticLocEnd':          	{ 'desc': globalName,	'side':	side,		'warble': 'trans',		'other': ['static', 'end', 'scaling'],			'type': 'transform' },
			'staticLength':          	{ 'desc': globalName,	'side':	side,		'warble': 'dist',		'other': ['static', 'scaling'],			'type': 'distanceBetween' },
			'locStart':              	{ 'desc': globalName,	'side':	side,		'warble': 'loc',		'other': ['start', 'volume'],			'type': 'locator' },
			'locEnd':                	{ 'desc': globalName,	'side':	side,		'warble': 'loc',		'other': ['end', 'volume'],			'type': 'locator' },
			'length':                	{ 'desc': globalName,	'side':	side,		'warble': 'dist',		'other': ['length', 'volume'],			'type': 'distanceBetween' },
			'staticDistMult':        	{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['static', 'volume'],			'type': 'multDoubleLinear' },
			'volumePow':             	{ 'desc': globalName,	'side':	side,		'warble': 'pow',		'other': ['volume', 'volume'],			'type': 'multiplyDivide' },
			'volumeDiv':             	{ 'desc': globalName,	'side':	side,		'warble': 'div',		'other': ['volume', 'volume'],			'type': 'multiplyDivide' },
			'scaleBlndX':            	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',		'other': ['scaleX', 'volume'],			'type': 'blendTwoAttr' },
			'scaleBlndY':            	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',		'other': ['scaleY', 'volume'],			'type': 'blendTwoAttr' },
			'scaleBlndZ':            	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',		'other': ['scaleZ', 'volume'],			'type': 'blendTwoAttr' },
		}

		return self.namesDict
