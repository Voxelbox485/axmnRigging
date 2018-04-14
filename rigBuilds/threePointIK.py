from pymel.core import *
import utils
import buildRig

class threePointIK(buildRig.rig):

	def __init__(self, fitNode=None, rigNode=None):

		if fitNode is None and rigNode is None:
			raise Exception('No data specified.')

		elif fitNode is None:
			self.rigNode = rigNode
			# Put any attributes needed for initialized rigs here

		else:

			# Initialize rigNode
			# Error Check:
			if len(fitNode.jointsList.get()) != 3:
				raise Exception('Not enough joints specified')

			# Convert string input to PyNode if neccessary
			if isinstance(fitNode, str):
				fitNode = ls(fitNode)[0]

			if fitNode.rigType.get() != 'poleVectorIK':
				raise Exception('Incorrect rig type: %s' % fitNode.rigType.get())



			buildRig.rig.__init__(self, fitNode)

			try:
				# ========================= Store Nodes =========================
				self.fkCtrls = []
				self.ikJoints = []
				self.ikCtrls = []
				self.crvs = []

				# ========================= FitNode Inputs =========================
				
				# Naming
				self.globalName = self.fitNode.globalName.get()
				self.subNames = [
				self.fitNode.subName0.get(),
				self.fitNode.subName1.get(),
				self.fitNode.subName2.get()
				]

				# NAMING
				self.naming(0)
				self.names = utils.constructNames(self.namesDict)

				# fkScaleMirror = self.fitNode.fkScale.get()
				fkScaleMirror = True

				# Transforms
				self.fitJoints = self.fitNode.jointsList.get()
				self.fitPV = self.fitNode.pv.get()

				# Move rigGroup
				xform(self.rigGroup, ws=1, m=xform(self.fitJoints[0], q=1, ws=1, m=1))

				# Mirroring
				if self.fitNode.side.get() == 2:
					mirror=True
				else:
					mirror=False

				# Shapes
				fkShapes = 		[self.fitNode.fkStartShape.get(), self.fitNode.fkMidShape.get(), self.fitNode.fkEndShape.get()]
				ikShapes = 		[self.fitNode.ikStartShape.get(), self.fitNode.pvShape.get(), self.fitNode.ikEndShape.get()]
				bezierShapes = 	[self.fitNode.bendStartShape.get(), self.fitNode.bendMidShape.get(), self.fitNode.bendEndShape.get()]

				# Bend/Twist Joints
				subJoints0 = self.fitNode.outputJoints0.get()[:self.fitNode.resultPoints_0.get()] # Only up to the amount of joints unhidden on rig
				subJoints1 = self.fitNode.outputJoints1.get()[:self.fitNode.resultPoints_1.get()+1]

				bendStyle = 'bezier'
				if hasAttr(self.fitNode, 'bendStyle'):
					bendStyle = self.fitNode.bendStyle.get(asString=True)
				
				if self.dev: print '\nBend Style: %s' % bendStyle
				doBend = True
				doAim = False
				doBezier = False
				doMidBend = False
				if bendStyle == 'None':
					doBend = False
				if bendStyle == 'Aim':
					doAim = True
				if bendStyle == 'Bezier':
					doBezier = True
				if bendStyle == 'Mid Bend':
					doMidBend = True

				subParams = [[],[]]

				subJointLists = [subJoints0, subJoints1]
				for i, subJoints in enumerate(subJointLists):
					if len(subJoints):
						for subJoint in subJoints:
							subParams[i].append(subJoint.uValue.get())

				
				doFootRoll = False
				if hasAttr(self.fitNode, 'subNode'):
					if self.fitNode.subNode.get():	
						if self.fitNode.subNode.get().rigType.get() == 'footRoll':
							if self.fitNode.subNode.get().build.get():
								if self.dev:
									print 'FOOTROLL:'
									print self.fitNode.subNode.get()
								doFootRoll = True
				
				# ========================= RigNode Attributes =========================
				self.rigNode.rigType.set('threePointIK', l=1)
				# =====
				utils.cbSep(self.rigNode)
				addAttr(self.rigNode, ct='publish', k=1, dv=0, min=0, max=1, ln='fkIk', nn='FK/IK')
				# =====
				utils.cbSep(self.rigNode, ct='publish')
				addAttr(self.rigNode, ct='publish', ln='autoVis', nn='FK/IK Auto Vis', at='short', min=0, max=1, dv=1)
				setAttr(self.rigNode.autoVis, keyable=False, channelBox=True)
				
				addAttr(self.rigNode, ct='publish', ln='fkVis', nn='FK Vis', at='short', min=0, max=1, dv=1)
				setAttr(self.rigNode.fkVis, keyable=False, channelBox=True)
				
				addAttr(self.rigNode, ct='publish', ln='ikVis', nn='IK Vis', at='short', min=0, max=1, dv=1)
				setAttr(self.rigNode.ikVis, keyable=False, channelBox=True)

				if doBezier or doAim:
					# =====
					utils.cbSep(self.rigNode, ct='publish')
					addAttr(self.rigNode, ct='publish', ln='bendCtrlsVis', nn='Bend Ctrl Vis', at='short', min=0, max=1, dv=0, k=1)
					setAttr(self.rigNode.bendCtrlsVis, k=0, cb=1)

				if doBezier:
					addAttr(self.rigNode, ct='publish', ln='tangentCtrlsVis', min=0, max=1, dv=0, at='short', k=1)
					setAttr(self.rigNode.tangentCtrlsVis, k=0, cb=1)

				if doBezier or doMidBend or doAim:
					addAttr(self.rigNode, ct='publish', ln='offsetCtrlsVis', nn='Offset Ctrl Vis', min=0, max=1, at='short', dv=0, k=1)
					setAttr(self.rigNode.offsetCtrlsVis, k=0, cb=1)

				# =====
				utils.cbSep(self.rigNode)
				addAttr(self.rigNode, ln='fkSegmentScaleCompensate', nn='Segment Scale Compensate', min=0, max=1, at='short', dv=1, keyable=1)

				# =====
				

				if doBezier or doMidBend:
					# =====
					utils.cbSep(self.rigNode, ct='publish')
					addAttr(self.rigNode, ln='neutralizeAll', min=0, max=1, dv=0, k=1)
					addAttr(self.rigNode, ln='tangentsDistanceScaling', softMinValue=0, softMaxValue=1, dv=1, k=1)
					# addAttr(self.rigNode, ln='midParam', nn='Elbow Slide', min=-1, max=1, dv=0, k=1)
					addAttr(self.rigNode, ln='twistDistribution', min=0, max=1, dv=1, k=1)
				if doFootRoll or doBezier or doMidBend:
					addAttr(self.rigNode, ln='upAxis', at='enum', enumName='Y=1:Z=2', dv=1, k=1)
					



				# ========================= Vis Mults =========================
				# allVis Mults
				fkIkAutoMult = createNode('multDoubleLinear', n=self.names.get('fkIkAutoMult', 'rnm_fkIkAutoMult'))
				self.rigNode.allVis >> fkIkAutoMult.i1
				self.rigNode.autoVis >> fkIkAutoMult.i2
				self.step(fkIkAutoMult, 'fkIkAutoMult')

				fkVisMult = createNode('multDoubleLinear', n=self.names.get('fkVisMult', 'rnm_fkVisMult'))
				self.rigNode.allVis >> fkVisMult.i1
				self.rigNode.fkVis >> fkVisMult.i2
				self.step(fkVisMult, 'fkVisMult')

				ikVisMult = createNode('multDoubleLinear', n=self.names.get('ikVisMult', 'rnm_ikVisMult'))
				self.rigNode.allVis >> ikVisMult.i1
				self.rigNode.ikVis >> ikVisMult.i2
				self.step(ikVisMult, 'ikVisMult')

				if doBezier or doAim:
					bendVisMult = createNode('multDoubleLinear', n=self.names.get('bendVisMult', 'rnm_bendVisMult'))
					self.bendVis = bendVisMult.o
					self.rigNode.allVis >> bendVisMult.i1
					self.rigNode.bendCtrlsVis >> bendVisMult.i2
					self.step(bendVisMult, 'bendVisMult')

				if doBezier or doMidBend or doAim:
					offsetVisMult = createNode('multDoubleLinear', n=self.names.get('offsetVisMult', 'rnm_offsetVisMult'))
					self.rigNode.allVis >> offsetVisMult.i1
					self.rigNode.offsetCtrlsVis >> offsetVisMult.i2
					self.step(offsetVisMult, 'offsetVisMult')
					self.offsetCtrlVis = offsetVisMult.o

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

				
				# ========================= Space Switch Group =========================
				self.ssGroup = createNode('transform', n=self.names.get('spaceSwitchGroup', 'rnm_spaceSwitchGroup'), p=self.rigGroup)
				self.step(self.ssGroup, 'spaceSwitchGroup')

				#=================== FK/IK Autovis Setup =========================
				self.sectionTag = 'fkIkAutoVis'

				fkCond = createNode('condition', n=self.names.get('fkCond', 'rnm_fkCond'))
				fkCond.operation.set(4)
				fkCond.secondTerm.set(0.9)
				fkCond.colorIfTrue.set(1,1,1)
				fkCond.colorIfFalse.set(0,0,0)
				connectAttr(self.rigNode.fkIk, fkCond.firstTerm)
				self.step(fkCond, 'fkCond')

				ikCond = createNode('condition', n=self.names.get('ikCond', 'rnm_ikCond'))
				fkCond.operation.set(4)
				fkCond.secondTerm.set(0.9)
				fkCond.colorIfTrue.set(1,1,1)
				fkCond.colorIfFalse.set(0,0,0)
				connectAttr(self.rigNode.fkIk, ikCond.firstTerm)
				self.step(ikCond, 'ikCond')

				fkAutoCond = createNode('condition', n=self.names.get('fkAutoCond', 'rnm_fkAutoCond'))
				self.fkAutoCond = fkAutoCond.outColorR
				fkAutoCond.operation.set(0)
				fkAutoCond.secondTerm.set(1)
				connectAttr(fkIkAutoMult.o, fkAutoCond.firstTerm)
				connectAttr(fkCond.outColorR, fkAutoCond.colorIfTrueR)
				connectAttr(fkVisMult.o, fkAutoCond.colorIfFalseR)
				connectAttr(fkVisMult.o, fkAutoCond.colorIfFalseG)
				self.step(fkAutoCond, 'fkAutoCond')
				self.fkVis = fkAutoCond.outColorR

				ikAutoCond = createNode('condition', n=self.names.get('ikAutoCond', 'rnm_ikAutoCond'))
				self.ikAutoCond = ikAutoCond.outColorR
				ikAutoCond.operation.set(0)
				ikAutoCond.secondTerm.set(1)
				connectAttr(fkIkAutoMult.o, ikAutoCond.firstTerm)
				connectAttr(ikCond.outColorR, ikAutoCond.colorIfTrueR)
				connectAttr(ikVisMult.o, ikAutoCond.colorIfFalseR)
				connectAttr(ikVisMult.o, ikAutoCond.colorIfFalseG)
				self.step(ikAutoCond, 'ikAutoCond')
				self.ikVis = ikAutoCond.outColorR

				#=========================== FK Setup =================================
				if fkScaleMirror and mirror:
					fkMirror=True
				else:
					fkMirror=False

				fkRigGroup = self.buildFkSetup(transforms=self.fitJoints, shapes=fkShapes, mirror=fkMirror)
				self.fkAutoCond >> fkRigGroup.v

				self.spaceSwitches[self.fkCtrls[0]] = buildRig.spaceSwitch(
					controller=self.fkCtrls[0],
					constraintType='orient',
					constrained=self.fkCtrls[0].const.get(),
					prefix=self.names.get('fk0ControlSS', 'rnm_fk0ControlSS'),
					p=self.ssGroup,
					targets=[self.rigsGroup, self.fkCtrls[0].buf.get()],
					labels=['World', 'Parent'])
				self.spaceSwitches[self.fkCtrls[0]].setDefaultBlend(1)

				self.spaceSwitches[self.fkCtrls[2]] = buildRig.spaceSwitch(
					controller=self.fkCtrls[2],
					constraintType='orient',
					constrained=self.fkCtrls[2].const.get(),
					prefix=self.names.get('fk2ControlSS', 'rnm_fk2ControlSS'),
					p=self.ssGroup,
					targets=[self.rigsGroup, self.fkCtrls[2].buf.get()],
					labels=['World', 'Parent'])
				self.spaceSwitches[self.fkCtrls[2]].setDefaultBlend(1)

				#=========================== IK Setup =================================

				ikRigGroup = self.buildIkSetup(
					transforms=self.fitJoints,
					poleVectorTransform=self.fitPV,
					shapes=ikShapes,
					ikOrients=None,
					pvFollow=True,
					stretch=True,
					antipop=True,
					mirror=mirror,
					nameVar=[]
					)
				self.ikAutoCond >> ikRigGroup.v


				self.spaceSwitches[self.ikCtrls[2]] = buildRig.spaceSwitch(
					controller=self.ikCtrls[2],
					constraintType='parent',
					constrained=self.ikCtrls[2].const.get(),
					prefix=self.names.get('ikControlSS', 'rnm_ikControlSS'),
					p=self.ssGroup,
					targets=[self.rigsGroup, self.ikCtrls[2].buf.get()],
					labels=['World', 'Parent'])
				self.spaceSwitches[self.ikCtrls[2]].setDefaultBlend(0)
				


				# =========================== FK/IK Switching Setup =================================
				fkIkGroup = createNode('transform', n=self.names.get('fkIkGroup', 'rnm_fkIkGroup'), p=self.rigGroup)
				self.step(fkIkGroup, 'fkIkGroup')

				fkIkRev = createNode('reverse', n=self.names.get('fkIkRev', 'rnm_fkIkRev'))
				self.rigNode.fkIk.connect(fkIkRev.inputX)
				self.step(fkIkRev, 'fkIkRev')

				switchJoints = []
				switchTwists = []
				for i, fkIk in enumerate(zip(self.fkCtrls, self.ikJoints)):
					self.naming(i)
					self.names = utils.constructNames(self.namesDict)

					switchJnt = createNode('joint', n=self.names.get('switchJnt', 'rnm_switchJnt%s' % i), p=(switchJoints[i-1] if i else fkIkGroup))
					
					self.step(switchJnt, 'switchJnt')
					
					switchJoints.append(switchJnt)
					switchJnt.drawStyle.set('None', k=1)
					# Snap to fk
					xform(switchJnt, ws=1, m=xform(self.fitJoints[i], q=1, ws=1, m=1))

					# Record default positions for one-click switch
					addAttr(switchJnt, ln='defaultTranslate', at='compound', numberOfChildren=3, k=1)
					for xyz in ['X', 'Y', 'Z']:
						addAttr(switchJnt, ln='defaultTranslate%s' % xyz, parent='defaultTranslate', dv=switchJnt.attr('translate%s' % xyz).get(), k=1)
					for xyz in ['X', 'Y', 'Z']:
						switchJnt.attr('defaultTranslate%s' % xyz).set(l=1)

					# switchTwist = createNode('transform', n=self.names.get('switchTwist', 'rnm_switchTwist'))
					# self.step(switchTwist, 'switchTwist')
					# switchTwists.append(switchTwist)
					switchTwists.append(buildRig.twistExtractorMatrix(switchJnt, switchJnt.getParent(), switchJnt))

				makeIdentity(switchJoints[0], apply=1, t=1, r=1, s=1, n=0, pn=1)
				# raise

				for i, fkIk in enumerate(zip(self.fkCtrls, self.ikJoints)):
					self.naming(i)
					self.names = utils.constructNames(self.namesDict)
					# Orient IK socket (in case controls were not oriented and Ik needed to go down x axis?)
					fkSocket = self.socket(self.socket(fkIk[0]))
					ikSocket = self.socket(fkIk[1])

					# xform(ikSocket, ws=1, ro=xform(fkIk[0], q=1, ws=1, ro=1))
					
					# Constrain result
					const = parentConstraint(fkSocket, ikSocket, switchJoints[i])
					fkIkRev.outputX.connect(const.w0)
					self.rigNode.fkIk.connect(const.w1)

					fkScaleConstNodes = self.matrixConstraint(fkSocket, switchJoints[i], t=0, r=0, s=1)
					fkScaleConstNodes[1].outputScaleX // switchJoints[i].scaleX
					fkScaleConstNodes[1].outputScaleY // switchJoints[i].scaleY
					fkScaleConstNodes[1].outputScaleZ // switchJoints[i].scaleZ
					ikScaleConstNodes = self.matrixConstraint(ikSocket, switchJoints[i], t=0, r=0, s=1)
					
					scaleBlend = createNode('blendColors', n=self.names.get('scaleBlend', 'rnm_scaleBlend'))
					self.step(scaleBlend, 'scaleBlend')
					fkScaleConstNodes[1].outputScale.connect(scaleBlend.color1)
					ikScaleConstNodes[1].outputScale.connect(scaleBlend.color2)

					fkIkRev.outputX.connect(scaleBlend.blender)
					scaleBlend.output.connect(switchJoints[i].scale, f=1)


				#=========================== One-Click Switching Setup =================================
				self.fkPoints = []
				self.ikPoints = []
				for i, fkIk in enumerate(zip(self.fkCtrls, self.ikCtrls)):
					self.naming(i)
					self.names = utils.constructNames(self.namesDict)

					fkPoint = createNode('transform', n=self.names.get('fkPoint', 'rnm_fkPoint'), p=switchJoints[i])
					self.fkPoints.append(fkPoint)
					xform(fkPoint, ws=1, m=xform(fkIk[0], q=1, ws=1, m=1))
					fkPoint.t.set(0,0,0)
					self.step(fkPoint, 'fkPoint')
					# if self.dev: fkPoint.displayLocalAxis.set(1)

					ikPoint = createNode('transform', n=self.names.get('ikPoint', 'rnm_ikPoint'), p=switchJoints[i])
					xform(ikPoint, ws=1, m=xform(fkIk[1], q=1, ws=1, m=1))
					ikPoint.t.set(0,0,0)
					self.step(ikPoint, 'ikPoint')
					# if self.dev: ikPoint.displayLocalAxis.set(1)
					self.ikPoints.append(ikPoint)




				#=========================== Beizer Setup =================================

				if doBezier:
					
					bezierRigGroup = self.buildBezierSetup(transforms=switchJoints, shapes=bezierShapes, mirror=mirror, indic=True, doNeutralize=True)
					bendVisMult.o.connect(bezierRigGroup.controlsVis)
					self.rigNode.tangentsDistanceScaling.connect(bezierRigGroup.tangentsDistanceScaling)
					self.rigNode.neutralizeAll.connect(bezierRigGroup.neutralizeAll)

					# pvPinningSS = buildRig.spaceSwitch(
					# 	constraintType='point',
					# 	controller = self.bendCtrls[1],
					# 	constrained= self.bendCtrls[1].extra.get(),
					# 	p=self.ssGroup,
					# 	prefix = self.names.get('pvPinningSS', 'rnm_pwvPinningSS'),
					# 	targets=[ self.bendCtrls[1].const.get(), self.ikCtrls[1] ],
					# 	offsets=False,
					# 	labels=['Free', 'Pinned']
					# )
					# pvPinningSS.setDefaultBlend(0)
					# pvPinningSS.setNiceName('Pinning')
					
					# Use ik lengths to update magnitude calculation
					# Needs work
					# magLens = [self.magLengthMults[0:2], self.magLengthMults[2:4]]
					# for i in range(2):
					# 	fkIkDefLenInput = createNode('blendTwoAttr', n=self.names.get('fkIkDefLenInput', 'rnm_fkIkDefLenInput'))
					# 	fkIkDefLenInput.i[0].set(1)
					# 	self.ikCtrls[2].attr('multLength%s' % (i+1)) >> fkIkDefLenInput.i[1]
					# 	self.rigNode.fkIk.connect(fkIkDefLenInput.ab)
					# 	for magLen in [self.magLengthMults[0:2], self.magLengthMults[2:4]][i]:
					# 		fkIkDefLenInput.o.connect(magLen.input2X)
					# 		fkIkDefLenInput.o.connect(magLen.input2Y)
					# 		fkIkDefLenInput.o.connect(magLen.input2Z)


					# Do work on result curve
					crv = self.crvs[0]

					# Make curve pretty for demo
					displaySmoothness(crv, pointsWire=16)
					
					# Motion path groups
					crvPathRig = self.buildCurvePartitionsSetup(
						crv, 
						nameVars='0',
						partitionParams=[0, bezierRigGroup.uValues.get()[1], 1], 
						constraintTargets=[switchJoints[0], switchJoints[1]], 
						paramLists=[subParams[0], subParams[1]], 
						mirror=mirror )

					results = crvPathRig.results.get()
				
					if hasAttr(self.rigNode, 'offsetCtrlsVis'):
						self.rigNode.offsetCtrlsVis.connect(crvPathRig.v)

					# crvPathGroup1 = self.buildParametricCurveRigSetup(crv, nameVar=1, p=bezierRigGroup, c=switchJoints[1], paramList=subParams[1], mirror=mirror)
					parent(crvPathRig, bezierRigGroup)
			
					for i in range(3):
						# addAttr(crvPathRig, ln='partitionParameters', multi=True, numberOfChildren=3, k=1)
						# print bezierRigGroup
						# print bezierRigGroup.attr('uValues%s' % i)
						# print bezierRigGroup.attr('uValues%s' % i).get()
						# print crvPathRig
						# print crvPathRig.attr('partitionParameter%s' % i)
						# print crvPathRig.attr('partitionParameter%s' % i).get()
						bezierRigGroup.attr('uValues%s' % i).connect(crvPathRig.attr('partitionParameter%s' % i))

					# =========================== Twist ===========================
					# #### Bend ctrls
					for i in range(2):
						self.bendCtrls[i+0].twist.connect(self.twistAdds[i].input2D[0].getChildren()[0])
						self.socket(self.bendCtrls[i+0]).twist.connect(self.twistAdds[i].input2D[1].getChildren()[0])

						self.bendCtrls[i+1].twist.connect(self.twistAdds[i].input2D[0].getChildren()[1])
						self.socket(self.bendCtrls[i+1]).twist.connect(self.twistAdds[i].input2D[1].getChildren()[1])


					# #### Auto
					# Mirror twists
					switchTwists[0].mult.set(-1) # (1 if mirror else -1)
					switchTwists[1].mult.set(-1) # (1 if mirror else -1)
					switchTwists[2].mult.set(1) # (-1 if mirror else 1)

					autoTwistMult = createNode('multiplyDivide', n=self.names.get('autoTwistMult', 'rnm_autoTwistMult'))
					self.step(autoTwistMult, 'autoTwistMult')
					self.rigNode.twistDistribution.connect(autoTwistMult.input2X)
					self.rigNode.twistDistribution.connect(autoTwistMult.input2Y)

					switchTwists[0].twist.connect(autoTwistMult.input1X)
					switchTwists[1].twist.connect(autoTwistMult.input1Y)
					switchTwists[2].twist.connect(autoTwistMult.input1Z)


					autoTwistMult.outputX.connect(self.twistAdds[0].input2D[2].input2Dx)
					autoTwistMult.outputY.connect(self.twistAdds[1].input2D[2].input2Dx)
					autoTwistMult.outputZ.connect(self.twistAdds[1].input2D[3].input2Dy)

					# print 'SUB PARAAAAMS'
					print len(subParams)
					print len(subParams[0])
					print len(subParams[1])
					print results[:len(subParams[0])]
					print results[len(subParams[0]):]

					startResults = results[:len(subParams[0])]
					endResults = results[len(subParams[0]):]
					
					
					scaleResults0 = self.buildScaleLengthSetup(scaleInputs=[self.bendCtrls[0], self.bendCtrls[1]], nodes=startResults, parameters=subParams[0], settingsNode=switchJoints[0], parentGroup=bezierRigGroup)
					scaleResults1 = self.buildScaleLengthSetup(scaleInputs=[self.bendCtrls[1], self.bendCtrls[2]], nodes=endResults, parameters=subParams[1], settingsNode=switchJoints[1], parentGroup=bezierRigGroup)

					results = scaleResults0
					results.extend(scaleResults1)
					
					# results = self.curvePointOffsets


				
				elif doAim:
					# create controls
					# for i in range(3):
					# 	endCtrl = createControlHeirarchy(
					# 		selectionPriority=0,
					# 		mirror=mirrorList[i],
					# 		shape=bendCtrlShapes,
					# 		name=self.names.get('lipCtrl', 'rnm_lipCtrl'), shape=fkShapes[i],
					# 		par=controlGroup,
					# 		ctrlParent=fkCtrl,
					# 		jntBuf=False
					# 	)
					# raise Exception(subJoints0)

					aimRigGroup0 = self.buildAimIkSetup(switchJoints[0], switchJoints[1],
						followInputs=True,
						rigGroup=switchJoints[0],
						inbetweenJoints=len(subJoints0)-1,
						registerControls=[True,False],
						stretch=True,
						mirror=mirror,
						sourceShape=bezierShapes[0],
						# destShape=bezierShapes[1],
						twist=True,
						skipEnd=True,
						twistAxisChoice=0
						)

					aimRig0Ctrls = self.aimCtrls[:]

					aimRigGroup1 = self.buildAimIkSetup(switchJoints[1], switchJoints[2],
						followInputs=True,
						rigGroup=switchJoints[1],
						inbetweenJoints = len(subJoints1)-2,
						registerControls=[True,True],
						stretch=True,
						mirror=mirror,
						sourceShape=bezierShapes[1],
						destShape=bezierShapes[2],
						twist=True,
						twistAxisChoice=0
						)
					aimRig1Ctrls = self.aimCtrls[:]


					self.bendVis.connect(aimRigGroup0.v)
					self.bendVis.connect(aimRigGroup1.v)

					self.matrixConstraint(aimRig1Ctrls[0], aimRig0Ctrls[1].const.get(), t=1, r=1, s=1)
					# aimRig1Ctrls[0].scale.connect(aimRig0Ctrls[1].const.get())
					self.matrixConstraint(switchJoints[2], aimRig1Ctrls[1].const.get(), t=0, r=1, s=1)

					self.offsetCtrlVis.connect(aimRigGroup0.offsetCtrlsVis)
					self.offsetCtrlVis.connect(aimRigGroup1.offsetCtrlsVis)

					self.matrixConstraint(self.rigNode, aimRig0Ctrls[0].const.get(), t=0, r=1, s=1)

					# =========================== Twist ===========================

					results = aimRigGroup0.results.get()
					results.extend(aimRigGroup1.results.get())

					# # #### Bend ctrls
					# for i in range(2):
					# 	self.aimRig0Ctrls[i+0].twist.connect(self.twistAdds[i].input2D[0].getChildren()[0])
					# 	self.socket(self.aimRig0Ctrls[i+0]).twist.connect(self.twistAdds[i].input2D[1].getChildren()[0])

					# 	self.aimRig0Ctrls[i+1].twist.connect(self.twistAdds[i].input2D[0].getChildren()[1])
					# 	self.socket(self.aimRig0Ctrls[i+1]).twist.connect(self.twistAdds[i].input2D[1].getChildren()[1])


					# # #### Auto
					# # Mirror twists
					# switchTwists[0].mult.set(1 if mirror else -1)
					# switchTwists[1].mult.set(1 if mirror else -1)
					# switchTwists[2].mult.set(-1 if mirror else 1)

					# autoTwistMult = createNode('multiplyDivide', n=self.names.get('autoTwistMult', 'rnm_autoTwistMult'))
					# self.step(autoTwistMult, 'autoTwistMult')
					# self.rigNode.twistDistribution.connect(autoTwistMult.input2X)
					# self.rigNode.twistDistribution.connect(autoTwistMult.input2Y)

					# switchTwists[0].twist.connect(autoTwistMult.input1X)
					# switchTwists[1].twist.connect(autoTwistMult.input1Y)
					# switchTwists[2].twist.connect(autoTwistMult.input1Z)


					# autoTwistMult.outputX.connect(self.twistAdds[0].input2D[2].input2Dx)
					# autoTwistMult.outputY.connect(self.twistAdds[1].input2D[2].input2Dx)
					# autoTwistMult.outputZ.connect(self.twistAdds[1].input2D[3].input2Dy)
					
					# scaleResults0 = 

					# scaleResults0 = self.buildScaleLengthSetup(scaleInputs=aimRig0Ctrls, nodes=aimRigGroup0.results.get(), settingsNode=self.rigNode)
					# scaleResults1 = self.buildScaleLengthSetup(scaleInputs=aimRig1Ctrls, nodes=aimRigGroup1.results.get(), settingsNode=self.rigNode)

					# results = scaleResults0
					# results.extend(scaleResults1)

					results = aimRigGroup0.results.get()
					results.extend(aimRigGroup1.results.get())


				elif doMidBend:
					
					# bendRigGroup = self.buildMidBendCurveSetup(transforms=switchJoints, follow=True, shapes=bezierShapes, controller=self.rigNode, mirror=mirror)
					

					# print self.fkCtrls[:2]
					# print self.fkCtrls[1:]
					# raise Exception('Here')

					# bendRigGroup = self.buildMidBendCurveSetup(transforms=switchJoints, follow=True, shapes=bezierShapes, controller=self.rigNode, mirror=mirror)

					bendRigGroup0 = self.buildMidBendCurveSetup(transforms=(switchJoints[:2]), follow=True, shapes=bezierShapes[:2], controller=self.rigNode, mirror=mirror)
					# Do work on result curve
					crv0 = self.crvs[0]
					displaySmoothness(crv0, pointsWire=16)
					# print bendRigGroup0.uValues.get()[1]
					# Motion path groups
					crvPathRig0 = self.buildCurvePartitionsSetup(
						crv0, 
						nameVars='0',
						partitionParams=[0, 0.5], 
						constraintTargets=[switchJoints[0]], 
						paramLists=[subParams[0]], 
						mirror=mirror )

				
					if hasAttr(self.rigNode, 'offsetCtrlsVis'):
						self.rigNode.offsetCtrlsVis.connect(crvPathRig0.v)

					# crvPathGroup1 = self.buildParametricCurveRigSetup(crv, nameVar=1, p=bendRigGroup, c=switchJoints[1], paramList=subParams[1], mirror=mirror)
					parent(crvPathRig0, bendRigGroup0)
			
					bendRigGroup1 = self.buildMidBendCurveSetup(transforms=(switchJoints[2:]), follow=True, shapes=bezierShapes[2:], controller=self.rigNode, mirror=mirror)
					# bendRigGroup1 = self.buildMidBendCurveSetup(transforms=(self.fkCtrls[1:] if self.doFK else jointsList[1:]), follow=(True if self.doFK else False), shapes=endShapes[1:], controller=self.rigNode, mirror=mirror)
					# Do work on result curve
					crv1 = self.crvs[0]


					# Make curve pretty for demo
					displaySmoothness(crv1, pointsWire=16)
					# Motion path groups
					crvPathRig1 = self.buildCurvePartitionsSetup(
						crv1, 
						nameVars='0',
						partitionParams=[0.5, 1], 
						constraintTargets=[switchJoints[1]], 
						paramLists=[subParams[1]], 
						mirror=mirror )

					if hasAttr(self.rigNode, 'offsetCtrlsVis'):
						self.rigNode.offsetCtrlsVis.connect(crvPathRig1.v)

					# crvPathGroup1 = self.buildParametricCurveRigSetup(crv, nameVar=1, p=bendRigGroup, c=switchJoints[1], paramList=subParams[1], mirror=mirror)
					parent(crvPathRig1, bendRigGroup1)
			
					# for i in range(3):
						# addAttr(crvPathRig, ln='partitionParameters', multi=True, numberOfChildren=3, k=1)
						# print bendRigGroup
						# print bendRigGroup.attr('uValues%s' % i)
						# print bendRigGroup.attr('uValues%s' % i).get()
						# print crvPathRig
						# print crvPathRig.attr('partitionParameter%s' % i)
						# print crvPathRig.attr('partitionParameter%s' % i).get()
						# bendRigGroup.attr('uValues%s' % i).connect(crvPathRig.attr('partitionParameter%s' % i))

					# # =========================== Twist ===========================
					# # #### Bend ctrls 
					# for i in range(2):
					# 	self.bendCtrls[i+0].twist.connect(self.twistAdds[i].input2D[0].getChildren()[0])
					# 	self.socket(self.bendCtrls[i+0]).twist.connect(self.twistAdds[i].input2D[1].getChildren()[0])

					# 	self.bendCtrls[i+1].twist.connect(self.twistAdds[i].input2D[0].getChildren()[1])
					# 	self.socket(self.bendCtrls[i+1]).twist.connect(self.twistAdds[i].input2D[1].getChildren()[1])


					# # #### Auto
					# # Mirror twists
					# switchTwists[0].mult.set(1 if mirror else -1)
					# switchTwists[1].mult.set(1 if mirror else -1)
					# switchTwists[2].mult.set(-1 if mirror else 1)

					# autoTwistMult = createNode('multiplyDivide', n=self.names.get('autoTwistMult', 'rnm_autoTwistMult'))
					# self.step(autoTwistMult, 'autoTwistMult')
					# self.rigNode.twistDistribution.connect(autoTwistMult.input2X)
					# self.rigNode.twistDistribution.connect(autoTwistMult.input2Y)

					# switchTwists[0].twist.connect(autoTwistMult.input1X)
					# switchTwists[1].twist.connect(autoTwistMult.input1Y)
					# switchTwists[2].twist.connect(autoTwistMult.input1Z)


					# autoTwistMult.outputX.connect(self.twistAdds[0].input2D[2].input2Dx)
					# autoTwistMult.outputY.connect(self.twistAdds[1].input2D[2].input2Dx)
					# autoTwistMult.outputZ.connect(self.twistAdds[1].input2D[3].input2Dy)

					# results = self.curvePointOffsets

					# # bendVisMult.o.connect(bendRigGroup.controlsVis)
					results = crvPathRig0.results.get()
					results.extend(crvPathRig1.results.get())

				else:
					results = switchJoints


				# =========================== Shoulder Setup =================================
				# Create a joint that follows top joint placement, but doesnt bend with top joint.
				# Make it so that top ik affects this joint when ik is on?

				rigEntrance = createNode('transform', n=self.names.get('rigEntrance', 'rnm_rigEntrance'), p=self.rigGroup)
				self.step(rigEntrance, 'rigEntrance')
				self.matrixConstraint(results[0], rigEntrance, t=1)
				results.insert(0, rigEntrance)
				

				#=========================== Bind Joints =================================
				for n, output in enumerate(results):
					self.naming(n=n)
					self.names = utils.constructNames(self.namesDict)
					
					output.message.connect(self.rigNode.socketList, na=1)
					
					bind = createNode('joint', n=self.names.get('bind', 'rnm_bind'), p=output)
					self.bindList.append(bind)
					self.step(bind, 'bind')
					bind.hide()

				
				self.rigExit = createNode('transform', n=self.names.get('rigExit', 'rnm_rigExit'), p=self.rigGroup)
				# This doesn't work when its just switch joints
				self.matrixConstraint(results[-1].getParent(), self.rigExit, t=1, offset=False)
				# self.matrixConstraint(results[-1], self.rigExit, t=1, r=1, s=1, offset=False)
				self.matrixConstraint(switchJoints[2], self.rigExit, t=0, r=1, s=1, offset=False)
				self.step(self.rigExit, 'rigExit')

				self.rigExit.message.connect(self.rigNode.socketList, na=1)

				self.naming(i=2)
				self.names = utils.constructNames(self.namesDict)
				# # rig exit bind
				

				if not doFootRoll:
					# No need for exit bind if there's a rigExtension (expand to include hand rig when it's done)
					rigExitBind = createNode( 'joint', n=self.names.get( 'rigExitBind', 'rnm_rigExitBind'), p=self.rigExit )
					self.bindList.append(rigExitBind)
					rigExitBind.hide()
				
				else:
					self.buildFootRollSetup(self.fitNode.subNode.get())

				self.rigNode.fkIk.set(1)
			finally:
				#=========================== Finalize =================================


				try:
					self.setController(fkRigGroup, self.rigGroup)
					self.setController(ikRigGroup, self.rigGroup)
					self.setController(bezierRigGroup, self.rigGroup)
				except:
					pass
				# self.setController(crvPathGroup0, self.rigGroup)
				# self.setController(crvPathGroup1, self.rigGroup)

				try:
					for ctrl in self.ikCtrls[:2]:
						for attrb in ctrl.scale.getChildren():
							attrb.set(l=1, k=0)
				except:
					pass

				try:
					self.constructSelectionList(selectionName='fkCtrls', selectionList=self.fkCtrls)
					self.constructSelectionList(selectionName='fkPoints', selectionList=self.fkPoints)
					self.constructSelectionList(selectionName='ikPoints', selectionList=self.ikPoints)
					self.constructSelectionList(selectionName='ikCtrls', selectionList=self.ikCtrls)
					self.constructSelectionList(selectionName='switchJoints', selectionList=switchJoints)
					self.constructSelectionList(selectionName='bendCtrls', selectionList=self.bendCtrls)
					self.constructSelectionList(selectionName='tangentCtrls', selectionList=self.tangentCtrls)
					self.constructSelectionList(selectionName='offsetCtrls', selectionList=self.offsetCtrls)
					self.constructSelectionList(selectionName='frozenNodes', selectionList=self.freezeList)
				
				except:
					pass
				
				self.finalize()


	def buildFootRollSetup(self, fitNode):
		# Builds a footroll setup on poleVectorIK using fitNode input
		# Includes a auto toe extend in ik, pivot controls with constraints mapped to a 'roll' and 'bank' range, and fk controls (offset?)
		# TODO
		# This is weirdly organized, but it's kinda a complicated part of the ik rig
		# self.fkCtrls gets overwritten.  fkCtrls can be a temporary attribute? Should I copy out lists to new class variables after they're collected?
		# Should I assign them to a dictionary?

		toeExtendSetup = True

		self.sectionTag = 'foot'

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
		side = fitNode.side.get()

		namesDict={			
			'footRollRigGroup':     { 'desc': self.globalName,	'side': side,		'warble': 'rigGroup',		'other': ['footRoll'], 						 				},
			'fkControlsGroup':    	{ 'desc': self.globalName,	'side': side,		'warble': 'rigGroup',		'other': ['footRoll', 'fk'], 						 				},
			'rigNode':              { 'desc': self.globalName,	'side': side,		'warble': 'rigNode',		'other': ['footRoll'], 										},
			'pivGroup':				{ 'desc': self.globalName,	'side': side,		'warble': 'grp',			'other': ['footRoll', 'pivots'], 							},
			'pivAnkle':				{ 'desc': self.globalName,	'side': side,		'warble': 'grp',			'other': ['footRoll', 'ankle'], 							},
			'fkIkCtrlSwitch':		{ 'desc': self.globalName,	'side': side,		'warble': 'trans',			'other': ['footRoll', 'fkIk', 'switch'], 					},
			'toeExtendGroup':		{ 'desc': self.globalName,	'side': side,		'warble': 'grp',			'other': ['footRoll', 'toeExtend', 'ankle'], 				},
			'ankleGroup':			{ 'desc': self.subNames[0],	'side': side,		'warble': 'grp',			'other': ['footRoll', 'toeExtend', 'ankle'], 				},
			'ankleSource':			{ 'desc': self.subNames[0],	'side': side,		'warble': 'trans',			'other': ['footRoll', 'toeExtend', 'ankle', 'source'], 		},
			'ankleDest':			{ 'desc': self.subNames[0],	'side': side,		'warble': 'trans',			'other': ['footRoll', 'toeExtend', 'ankle', 'dest'], 		},
			'toeGroup':				{ 'desc': self.subNames[1],	'side': side,		'warble': 'grp',			'other': ['footRoll', 'toeExtend', 'toe'],  				},
			'toeSource':			{ 'desc': self.subNames[1],	'side': side,		'warble': 'trans',			'other': ['footRoll', 'toeExtend', 'toe', 'source'],		},
			'toeDest':				{ 'desc': self.subNames[1],	'side': side,		'warble': 'cond',			'other': ['footRoll', 'toeExtend', 'toe', 'dest'], 			},
			'heel':					{ 'desc': self.globalName,	'side': side,		'warble': None,				'other': ['footRoll', 'piv'],			 			},
			'bankIn':				{ 'desc': self.globalName,	'side': side,		'warble': None,				'other': ['footRoll', 'piv'],			 			},
			'bankOut':				{ 'desc': self.globalName,	'side': side,		'warble': None,				'other': ['footRoll', 'piv'],			 			},
			'toe':					{ 'desc': self.globalName,	'side': side,		'warble': None,				'other': ['footRoll', 'piv'],			 			},
			'ball':					{ 'desc': self.globalName,	'side': side,		'warble': None,				'other': ['footRoll', 'piv'],			 			},
			'staticGroup':			{ 'desc': self.globalName,	'side': side,		'warble': 'grp',			'other': ['pivResults'],			 			},
			'staticAnkle':			{ 'desc': self.subNames[0],	'side': side,		'warble': 'trans',			'other': ['pivResult'],			 			},
			'staticToe':			{ 'desc': self.subNames[1],	'side': side,		'warble': 'trans',			'other': ['pivResult'],			 			},
			
			'startCtrl':			{ 'desc': self.globalName,	'side': side,		'warble': None,				'other': ['start', 'aim'],			 			},
			'endCtrl':				{ 'desc': self.globalName,	'side': side,		'warble': None,				'other': ['end', 'aim'],			 			},
			'offsetCtrl':			{ 'desc': self.globalName,	'side': side,		'warble': None,				'other': ['end', 'aim'],			 			},
			'extendSwitch0':		{ 'desc': self.subNames[0],	'side': side,		'warble': 'trans',			'other': ['toeExtend', 'switch'],			 			},
			'extendSwitch1':		{ 'desc': self.subNames[1],	'side': side,		'warble': 'trans',			'other': ['toeExtend', 'switch'],			 			},
			'fkIkSwitch0':			{ 'desc': self.subNames[0],	'side': side,		'warble': 'trans',			'other': ['fkIk', 'switch'],			 			},
			'fkIkSwitch1':			{ 'desc': self.subNames[1],	'side': side,		'warble': 'trans',			'other': ['fkIk', 'switch'],			 			},
			'toeCtrl':				{ 'desc': self.globalName,	'side': side,		'warble': None,				'other': ['toe', 'offset' 'switch'],			 			},
			'bankInRemap':              	{ 'desc': self.globalName,	'side':	side,		'warble': 'remap',		'other': ['bankIn', 'FK'],			'type': 'remapValue' },
			'bankOutRemap':             	{ 'desc': self.globalName,	'side':	side,		'warble': 'remap',		'other': ['bankOut', 'FK'],			'type': 'remapValue' },
			'heelBackRemap':            	{ 'desc': self.globalName,	'side':	side,		'warble': 'remap',		'other': ['heelBack', 'FK'],			'type': 'remapValue' },
			'ballForwardRemap':         	{ 'desc': self.globalName,	'side':	side,		'warble': 'remap',		'other': ['ballForward', 'FK'],			'type': 'remapValue' },
			'rollThresholdConv':        	{ 'desc': self.globalName,	'side':	side,		'warble': 'mult',		'other': ['rollThresholdConv', 'FK'],			'type': 'multDoubleLinear' },
			'rollCorrectThresholdConv': 	{ 'desc': self.globalName,	'side':	side,		'warble': 'mult',		'other': ['rollCorrectThresholdConv', 'FK'],			'type': 'multDoubleLinear' },
			'toeForwardRemap':          	{ 'desc': self.globalName,	'side':	side,		'warble': 'remap',		'other': ['toeForward', 'FK'],			'type': 'remapValue' },
			
			'fkIkSwitch':               	{ 'desc': self.globalName,	'side':	side,		'warble': None,		'other': ['fkIkSwitch', 'AimIK'],			'type': 'transform' },
			#2 'fkIkSwitch':               	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['fkIkSwitch', 'AimIK'],			'type': 'transform' },
			#5 'socketNode':               	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['socketNode', 'AimIK'],			'type': 'transform' },

		}

		names = utils.constructNames(namesDict)

		# Get parent's class data without overwriting
		legFkCtrls = self.fkCtrls[:]
		legIkCtrls = self.ikCtrls[:]




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

		# col.setOutlinerRGB(rigGroup, self.colorsIK[self.side])
		# col.setOutlinerRGB(rigNode, self.rigNodeColor)

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
		ikController = self.ikCtrls[2]
		# ikController = self.rigNode

		utils.cbSep(ikController)
		addAttr(ikController, ln='roll', softMinValue=-10, softMaxValue=10, k=1)
		addAttr(ikController, ln='bank', softMinValue=-10, softMaxValue=10, k=1)
		
		# =====
		utils.cbSep(self.rigNode)
		addAttr(self.rigNode, ln='bankAngle', 			softMinValue= -90, softMaxValue= 90, 	dv=45, k=1)
		addAttr(self.rigNode, ln='heelBackAngle', 		softMinValue= -90, softMaxValue= 90, 	dv=45, k=1)
		addAttr(self.rigNode, ln='ballForwardAngle', 		softMinValue= -90, softMaxValue= 90, 	dv=45, k=1)
		addAttr(self.rigNode, ln='toeForwardAngle', 		softMinValue= -90, softMaxValue= 90, 	dv=45, k=1)

		utils.cbSep(self.rigNode)
		addAttr(self.rigNode, ln='rollThreshold', 		softMinValue= 0,   softMaxValue= 10, 	dv=5,  k=1)
		addAttr(self.rigNode, ln='rollCorrectThreshold', 	softMinValue= 0,   softMaxValue= 10, 	dv=7,  k=1)

		utils.cbSep(self.rigNode)
		addAttr(self.rigNode, ln='rollSmoothing', 		softMinValue= 1,   softMaxValue= 3, 	dv=1,  at='short', 	k=1)
		addAttr(self.rigNode, ct='publish', ln='pivotLimits', 		min=0, max=1, at='short', dv=1, k=1)


		utils.cbSep(self.rigNode)
		if toeExtendSetup:
			addAttr(self.rigNode, ct='publish', ln='toePointExtend', min=0, max=1, dv=1, k=1)

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

		fkIkSwitchSS = buildRig.simpleSpaceSwitch(
			constraintType='parent',
			constrained= rigGroup,
			prefix = names.get('fkIkSwitch', 'rnm_fkIkSwitch'),
			targets=[self.socket(legFkCtrls[2]), self.socket(legIkCtrls[2])],
			labels=['FK', 'IK'],
			offsets=True,
			)
		self.rigNode.fkIk.connect(fkIkSwitchSS.blendAttr)

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
		
		# fkIkDestSwtichSS = buildRig.spaceSwitch(
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
		# Create fkCtrl on ankle and toe joint (hide ankle)
		self.fkCtrls = []
		fkRigGroup = self.buildFkSetup(transforms=fitJoints[0:2], register=[False, True], shapes=fkShapes, selectionPriority=0, nameVar=['Foot', 'FK'], mirror=mirror, rigGroup=rigGroup)
		self.matrixConstraint(legFkCtrls[2], fkRigGroup, t=1, r=1, s=1)
		self.fkAutoCond.connect(fkRigGroup.v)
		
		# =============================================== IK setup ==================================================== 
		# ============================================= Pivots setup ================================================== 

		# Follows IK Control
		pivGroup = createNode('transform', n=names.get('pivGroup', 'rnm_pivGroup'), p=rigGroup)
		self.step(pivGroup, 'pivGroup')
		self.matrixConstraint(self.socket(self.ikCtrls[2]), rigGroup)
		# xform(pivGroup, ws=1, m=xform(fitJoints[0], q=1, ws=1, m=1))
		self.ikAutoCond.connect(pivGroup.v)


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

			outlinerColor = None
			if pivotShapes:
				if len(pivotShapes[piv].getShapes()):
					outlinerColor = pivotShapes[piv].getShapes()[0].overrideColorRGB.get()
				

			ctrl = self.createControlHeirarchy(
				name=names.get(piv, 'rnm_%s' % piv), 
				transformSnap=pivotPoints[piv],
				selectionPriority=0,
				shape = pivotShapes[piv],
				outlinerColor = outlinerColor,
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
		parent(self.ikCtrlLocs[1], pivAnkle, r=True, s=True)

		# Use pivot heirachy to drive ik handle
		# self.matrixConstraint(pivAnkle, self.ikhConst, t=1, r=1, s=1)
		self.matrixConstraint( pivAnkle, self.ikHandleGroup, t=1, r=1, offset=True, force=True, preserve=False )
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


		bankInRemap = createNode('remapValue', n=names.get('bankInRemap', 'rnm_bankInRemap'))
		self.step(bankInRemap, 'bankInRemap')
		self.rigNode.rollSmoothing.connect(bankInRemap.value[0].value_Interp)
		self.rigNode.rollSmoothing.connect(bankInRemap.value[1].value_Interp)
		ikController.bank.connect(bankInRemap.inputValue)
		bankInRemap.inputMin.set(-10)
		bankInRemap.inputMax.set(0)
		self.rigNode.bankAngle.connect(bankInRemap.outputMin)
		bankInRemap.outputMax.set(0)
		bankInRemap.outValue.connect(self.pivCtrls[1].const.get().rotateZ)

		bankOutRemap = createNode('remapValue', n=names.get('bankOutRemap', 'rnm_bankOutRemap'))
		self.step(bankOutRemap, 'bankOutRemap')
		self.rigNode.rollSmoothing.connect(bankOutRemap.value[0].value_Interp)
		self.rigNode.rollSmoothing.connect(bankOutRemap.value[1].value_Interp)
		ikController.bank.connect(bankOutRemap.inputValue)
		bankOutRemap.inputMin.set(0)
		bankOutRemap.inputMax.set(10)
		bankOutRemap.outputMin.set(0)
		self.rigNode.bankAngle.connect(bankOutRemap.outputMax)
		bankOutRemap.outValue.connect(self.pivCtrls[2].const.get().rotateZ)



		# ============================================= Pivots Roll ================================================== 
		# Heel Roll
		heelBackRemap = createNode('remapValue', n=names.get('heelBackRemap', 'rnm_heelBackRemap'))
		self.step(heelBackRemap, 'heelBackRemap')
		self.rigNode.rollSmoothing.connect(heelBackRemap.value[0].value_Interp)
		self.rigNode.rollSmoothing.connect(heelBackRemap.value[1].value_Interp)
		
		ikController.roll.connect(heelBackRemap.inputValue)
		
		heelBackRemap.inputMin.set(-10)
		heelBackRemap.inputMax.set(0)
		
		self.rigNode.heelBackAngle.connect(heelBackRemap.outputMin)
		heelBackRemap.outputMax.set(0)
		
		heelBackRemap.outValue.connect(self.pivCtrls[0].const.get().rotateZ)
		# 

		# Ball Roll
		ballForwardRemap = createNode('remapValue', n=names.get('ballForwardRemap', 'rnm_ballForwardRemap'))
		self.step(ballForwardRemap, 'ballForwardRemap')
		
		ikController.roll.connect(ballForwardRemap.inputValue)
		
		ballForwardRemap.inputMin.set(0)
		ballForwardRemap.inputMax.set(20)

		rollThresholdConv = createNode('multDoubleLinear', n=names.get('rollThresholdConv', 'rnm_rollThresholdConv'))
		self.step(rollThresholdConv, 'rollThresholdConv')
		self.rigNode.rollThreshold.connect(rollThresholdConv.i1)
		rollThresholdConv.i2.set(0.05)

		rollCorrectThresholdConv = createNode('multDoubleLinear', n=names.get('rollCorrectThresholdConv', 'rnm_rollCorrectThresholdConv'))
		self.step(rollCorrectThresholdConv, 'rollCorrectThresholdConv')
		self.rigNode.rollCorrectThreshold.connect(rollCorrectThresholdConv.i1)
		rollCorrectThresholdConv.i2.set(0.1)

		# 0 Zero
		ballForwardRemap.value[0].value_Position.set(0)
		# 1 Roll
		ballForwardRemap.value[1].value_FloatValue.set(1)
		rollThresholdConv.o.connect(ballForwardRemap.value[1].value_Position)
		# 2 Correction threshold
		ballForwardRemap.value[2].value_FloatValue.set(1)
		rollCorrectThresholdConv.o.connect(ballForwardRemap.value[2].value_Position)
		# 3 Final
		ballForwardRemap.value[3].value_FloatValue.set(0)
		ballForwardRemap.value[3].value_Position.set(1)
		# 4 Back to zero



		self.rigNode.rollSmoothing.connect(ballForwardRemap.value[0].value_Interp)
		self.rigNode.rollSmoothing.connect(ballForwardRemap.value[1].value_Interp)
		self.rigNode.rollSmoothing.connect(ballForwardRemap.value[2].value_Interp)
		self.rigNode.rollSmoothing.connect(ballForwardRemap.value[3].value_Interp)

		ballForwardRemap.outputMin.set(0)
		self.rigNode.ballForwardAngle.connect(ballForwardRemap.outputMax)

		ballForwardRemap.outValue.connect(self.pivCtrls[4].const.get().rotateZ)
		# 

		# Toe Roll
		toeForwardRemap = createNode('remapValue', n=names.get('toeForwardRemap', 'rnm_toeForwardRemap'))
		self.step(toeForwardRemap, 'toeForwardRemap')
		self.rigNode.rollSmoothing.connect(toeForwardRemap.value[0].value_Interp)
		self.rigNode.rollSmoothing.connect(toeForwardRemap.value[1].value_Interp)
		
		ikController.roll.connect(toeForwardRemap.inputValue)
		
		# toeForwardRemap.inputMin.set(5)
		self.rigNode.rollThreshold.connect(toeForwardRemap.inputMin)
		toeForwardRemap.inputMax.set(20)
		
		toeForwardRemap.outputMin.set(0)
		self.rigNode.toeForwardAngle.connect(toeForwardRemap.outputMax)

		toeForwardRemap.value[0].value_Position.set(0)
		ballForwardRemap.value[0].value_FloatValue.set(0)
		toeForwardRemap.value[1].value_Position.set(0.5)
		ballForwardRemap.value[1].value_FloatValue.set(1)
		toeForwardRemap.value[2].value_Position.set(1)
		ballForwardRemap.value[2].value_FloatValue.set(0)
		
		toeForwardRemap.outValue.connect(self.pivCtrls[3].const.get().rotateZ)
		# 

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
			ankle = self.buildAimIkSetup(source=ankleSource, dest=ankleDest, followInputs=True, stretch=False, rigGroup=staticAnkle)
			# ankle.stretch.set(0)
			# ankle.squash.set(1)
			ikAimResults = ankle.results.get()
			ikAimResults.remove(ikAimResults[-1])
			self.matrixConstraint(ikAimResults[0], toeSource)
			self.rigNode.upAxis.connect(ankle.upAxis)
			

			# toeSourceSS = buildRig.spaceSwitch(
			# 	constraintType='point',
			# 	controller = toeSource,
			# 	constrained= toeSource,
			# 	prefix = names.get('toeExtendSS', 'rnm_toeExtendSS'),
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
			self.rigNode.upAxis.connect(toe.upAxis)


			results = ikAimResults

			extendResults = []
			# Static switch
			q = 0
			for static, extend in zip(staticResults, results):
				extendSwitch = createNode('transform', n=names.get('extendSwitch%s' % q, 'rnm_extendSwitch%s' % q), p=rigGroup)
				utils.snap(static, extendSwitch)
				self.step(extendSwitch, 'extendSwitch')

			
				extendSwitchSS = buildRig.simpleSpaceSwitch(
				constraintType='parent',
				constrained= extendSwitch,
				prefix = names.get('toeExtendSS', 'rnm_toeExtendSS'),
				targets=[static, extend],
				labels=['Static', 'Extend'],
				offsets=True,
				)
				self.rigNode.toePointExtend.connect(extendSwitchSS.blendAttr)


				extendResults.append(extendSwitch)
				q=q+1
			results = extendResults
		
		fkIkResults = []
		# fk ik switch
		# print legFkCtrls[2]
		# print self.fkCtrls[0]
		# print self.fkCtrls[1]
		# fkResults = [legFkCtrls[2], self.fkCtrls[0], self.fkCtrls[1]]
		q = 0
		for fk, ik in zip(self.fkCtrls, results):

			fkIkSwitch = createNode('transform', n=names.get('fkIkSwitch%s' % q, 'rnm_fkIkSwitch'), p=rigGroup)
			utils.snap(static, fkIkSwitch)
			self.step(fkIkSwitch, 'fkIkSwitch')

			fkIkSwitchSS = buildRig.simpleSpaceSwitch(
				constraintType='parent',
				constrained= fkIkSwitch,
				prefix = names.get('fkIkSwitchSS', 'rnm_fkIkSwitchSS'),
				targets=[self.socket(fk), self.socket(ik)],
				labels=['FK', 'IK'],
				offsets=False,
			)
			self.rigNode.fkIk.connect(fkIkSwitchSS.blendAttr)

			fkIkResults.append(fkIkSwitch)

			q=q+1
		if self.dev: print fkIkResults

		#=========================== Toe ResultFK =================================

		toeCtrl = self.createControlHeirarchy(
			name=names.get('toeCtrl', 'rnm_toeCtrl'), 
			transformSnap=fitJoints[1],
			selectionPriority=2,
			ctrlParent=(self.ikCtrls[-1]),
			doConst=False,
			t=False,
			outlinerColor = (0,0,0),
			par=fkIkSwitch)

		fkIkResults.remove(fkIkResults[-1])
		fkIkResults.append(toeCtrl)
		self.offsetCtrlVis.connect(toeCtrl.buf.get().v)

		#=========================== Finalize =================================
		for n, result in enumerate(fkIkResults):
			namesDict={
				'bind':          		{'desc': self.subNames[n], 	'side': self.fitNode.side.get(),		'warble': 'bind',			'other': []},
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
		
		# Restore class data
		self.fkCtrls = legFkCtrls
		self.ikCtrls = legIkCtrls

		self.globalName = self.fitNode.globalName.get()
		self.subNames = [
		self.fitNode.subName0.get(),
		self.fitNode.subName1.get(),
		self.fitNode.subName2.get()
		]

			
		self.freezeNodes()
		if self.dev: print 'Node Count: %s' % self.nodeCount


	def naming(self, i=0, n=0):
		try:
			globalName = self.globalName
		except:
			globalName = ''

		try:
			subName = self.subNames[i]
		except:
			subName = globalName

		n = '%s' % n
		side = self.fitNode.side.get()

		self.namesDict={			
			'asset':					{'desc': globalName, 'side': side,	'warble': 'asset'},
			'rigGroup':					{'desc': globalName, 'side': side,	'warble': 'rigGroup'},
			'fkIkAutoMult':           	{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['fkIkAuto', 'vis']							},
			'fkVisMult':              	{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['fk', 'vis']									},
			'ikVisMult':              	{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['ik', 'vis']									},
			'bendVisMult':            	{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['bend', 'vis']								},
			'offsetVisMult':          	{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['offset', 'vis']								},
			'debugVisMult':           	{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['debug', 'vis']								},
			'worldGroup':             	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['world']										},
			'fkCond':                 	{'desc': globalName, 'side': side,	'warble': 'cond',		'other': ['fkVis']										},
			'ikCond':                 	{'desc': globalName, 'side': side,	'warble': 'cond',		'other': ['ikVis']										},
			'fkAutoCond':             	{'desc': globalName, 'side': side,	'warble': 'cond',		'other': ['fkAuto', 'vis']								},
			'ikAutoCond':             	{'desc': globalName, 'side': side,	'warble': 'cond',		'other': ['ikAuto', 'vis']								},
			'fkRigGroup':             	{'desc': globalName, 'side': side,	'warble': 'rigGroup',	'other': ['fkRig']										},
			'fkControlsGroup':          {'desc': globalName, 'side': side,	'warble': 'rigGroup',	'other': ['fk']										},
			'fkCtrl':          			{'desc': subName, 	 'side': side,	'warble': None,			'other': ['fk']											},
			'ikRigGroup':             	{'desc': globalName, 'side': side,	'warble': 'rigGroup',	'other': ['ik']										},
			'ikJointsGroup':          	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['ik', 'joints']								},
			'ikJoint':          		{'desc': subName,	 'side': side,	'warble': 'jnt',		'other': ['ik']											},
			'ikh':                    	{'desc': globalName, 'side': side,	'warble': 'ikh',		'other': ['ik']											},
			'eff':                    	{'desc': globalName, 'side': side,	'warble': 'eff',		'other': ['ik']											},
			'ikCtrlsGroup':           	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['ik', 'controls']								},
			'pvCtrl':           		{'desc': globalName, 'side': side,	'warble': None,			'other': ['ik', 'pv']									},
			'ikCtrl':           		{'desc': subName, 	'side': side,	'warble': None,			'other': ['ik']											},
			'pvFollowAim':            	{'desc': globalName, 'side': side,	'warble': 'trans',		'other': ['ik', 'pvFollow', 'aim']						},
			'pvFollowAimTwist':       	{'desc': globalName, 'side': side,	'warble': 'trans',		'other': ['ik', 'pvFollow', 'twist']					},
			'pvFollowAimAt':          	{'desc': globalName, 'side': side,	'warble': 'trans',		'other': ['ik', 'pvFollow', 'aimAt']					},
			'pvFollowResult':         	{'desc': globalName, 'side': side,	'warble': 'trans',		'other': ['ik', 'pvFollow', 'result']					},
			'pvFollowBlend':          	{'desc': globalName, 'side': side,	'warble': 'blnd',		'other': ['ik', 'pvFollow', 'toggle']					},
			'ikCtrlDist':             	{'desc': globalName, 'side': side,	'warble': 'dist',		'other': ['ik', 'ctrls']								},
			'scaleLenGroup':          	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['ik', 'dist', 'scaling']						},
			'scaleLoc':               	{'desc': subName,	 'side': side,	'warble': 'loc',		'other': ['ik', 'dist', 'scaling']						}, #x3
			'scaleDist':              	{'desc': subName,	 'side': side,	'warble': 'dist',		'other': ['ik', 'scaling']								}, #x2
			'scaleLengthMult':        	{'desc': subName,	 'side': side,	'warble': 'mult',		'other': ['ik', 'dist', 'scaling']						}, #x2
			'staticLengthMult':       	{'desc': subName,	 'side': side,	'warble': 'mult',		'other': ['ik', 'dist', 'scaling']						}, #x2
			'addStaticLengths':       	{'desc': globalName, 'side': side,	'warble': 'add',		'other': ['ik', 'dist', 'static'], 						}, #'type':addDoubleLinear},
			'addScaleLengths':        	{'desc': globalName, 'side': side,	'warble': 'add',		'other': ['ik', 'dist', 'scaling'], 					}, #'type':addDoubleLinear},
			'addLengths':             	{'desc': globalName, 'side': side,	'warble': 'add',		'other': ['ik', 'dist', 'scaling'], 					}, #'type':addDoubleLinear},
			'lengthNormalize':        	{'desc': globalName, 'side': side,	'warble': 'div',		'other': ['ik', 'pvFollow', 'dist', 'scaling'], 		}, #'type':multiplyDivide},
			'ctrlDistNormalize':      	{'desc': globalName, 'side': side,	'warble': 'div',		'other': ['ik', 'dist', 'ctrls', 'normalize'], 			}, #'type':multiplyDivide},
			'distNormalize':          	{'desc': globalName, 'side': side,	'warble': 'div',		'other': ['ik', 'dist', 'normalize'], 					}, #'type':multiplyDivide},
			'stretchBlend':           	{'desc': globalName, 'side': side,	'warble': 'blnd',		'other': ['ik', 'stretch', 'toggle'], 					}, #'type':blendColors},
			'multLengthClamp':        	{'desc': globalName, 'side': side,	'warble': 'clmp',		'other': ['ik', 'multLength'], 							}, #'type':clamp},
			'stretchClamp':             {'desc': globalName, 'side': side,	'warble': 'clmp',		'other': ['ik', 'stretch'], 							}, #'type':clamp},
			'denormalize':            	{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['ik', 'denormalize'], 						}, #'type':multiplyDivide},
			'stretchMult':            	{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['ik', 'multLength', 'stretch'], 				}, #'type':multiplyDivide},
			'pvFollowNoStretchClamp': 	{'desc': globalName, 'side': side,	'warble': 'clmp',		'other': ['ik', 'pvFollow', 'noStretch'], 				}, #'type':clamp},
			'pvFollowStretchBlend':   	{'desc': globalName, 'side': side,	'warble': 'blnd',		'other': ['ik', 'pvFollow', 'stretch', 'toggle'], 		}, #'type':blendTwoAttr},
			'antipopClamp':           	{'desc': globalName, 'side': side,	'warble': 'clmp',		'other': ['ik', 'antipop'], 							}, #'type':clamp},
			'antipopSub1':            	{'desc': globalName, 'side': side,	'warble': 'sub',		'other': ['ik', 'antipop'], 							}, #'type':plusMinusAverage},
			'antipopDiv1':            	{'desc': globalName, 'side': side,	'warble': 'div',		'other': ['ik', 'antipop'], 							}, #'type':multiplyDivide},
			'antipopPow':             	{'desc': globalName, 'side': side,	'warble': 'pow',		'other': ['ik', 'antipop'], 							}, #'type':multiplyDivide},
			'antipopMult1':           	{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['ik', 'antipop'], 							}, #'type':multiplyDivide},
			'antipopSub2':            	{'desc': globalName, 'side': side,	'warble': 'sub',		'other': ['ik', 'antipop'], 							}, #'type':plusMinusAverage},
			'antipopSub3':            	{'desc': globalName, 'side': side,	'warble': 'sub',		'other': ['ik', 'antipop'], 							}, #'type':plusMinusAverage},
			'antipopCond':            	{'desc': globalName, 'side': side,	'warble': 'cond',		'other': ['ik', 'antipop'], 							}, #'type':condition},
			'antipopSub4':            	{'desc': globalName, 'side': side,	'warble': 'sub',		'other': ['ik', 'antipop'], 							}, #'type':plusMinusAverage},
			'antipopBlend':           	{'desc': globalName, 'side': side,	'warble': 'blnd',		'other': ['ik', 'antipop', 'toggle'], 					}, #'type':blendTwoAttr},
			'antipopAimGrp':          	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['ik', 'antipop', 'aim'], 							}, #'type':transform},
			'antipopGrp':             	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['ik', 'antipop'], 							}, #'type':transform},
			# 'antipopAimConst':        {'desc': globalName, 'side': side,	'warble': 'aim',		'other': [], 											}, #'type':aimConstraint},
			'antipopScale':           	{'desc': globalName, 'side': side,	'warble': 'trans',		'other': ['ik', 'antipop', 'scale'], 					}, #'type':multDoubleLinear},
			'fkIkGroup':              	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['fkIk'], 										}, #'type':transform},
			'fkIkRev':                	{'desc': globalName, 'side': side,	'warble': 'rev',		'other': ['fkIk'], 										}, #'type':reverse},
			'switchJnt':              	{'desc': subName,	 'side': side,	'warble': 'jnt',		'other': ['switch'], 									}, #'type':joint},
			'bezierRigGroup':         	{'desc': globalName, 'side': side,	'warble': 'rigGroup',	'other': ['bezier'], 									}, #'type':transform},
			'bezierControlsGroup':    	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['bezier', 'ctrls'], 							}, #'type':transform},
			'bendControlGroup':    	{'desc': subName, 	'side': side,	'warble': 'grp',		'other': ['bezier', 'ctrl'], 							}, #'type':transform},
			'staticLocGroup':			{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['bezier', 'static', 'scaling'], 				}, #'type':transform},}
			'bendCtrl':    				{'desc': subName, 	 'side': side,	'warble': None,			'other': ['bezier',], 									}, #'type':transform},
			'tangentCtrl':    			{'desc': subName, 	 'side': side,	'warble': None,			'other': ['bezier', n], 								}, #'type':transform},
			'crv':    					{'desc': subName, 	 'side': side,	'warble': 'crv',		'other': ['bezier'], 									}, #'type':transform},
			# 'socketNode':             {'desc': subName, 	''side': side,	warble': None,			'other': [], 											}, #'type':transform},
			'oriSR':                  	{'desc': subName, 	 'side': side,	'warble': 'rng',		'other': ['tangent', 'ori'], 							},
			'oriRev':                 	{'desc': subName, 	 'side': side,	'warble': 'rev',		'other': ['tangent', 'ori'], 							},
			'tangentMirror':          	{'desc': subName, 	'side': side,	'warble': 'mir',		'other': ['tangent', n], 									},
			'neutralBlend':      		{'desc': globalName, 'side': side,	'warble': 'blnd',		'other': ['tangent', 'neutral', '%s' % i] 				},
			'magDistBlend':      		{'desc': globalName, 'side': side,	'warble': 'blnd',		'other': ['tangent', 'mag', 'dist', '%s' % i]			}, #'type':blendColors},
			'magBlend':          		{'desc': globalName, 'side': side,	'warble': 'blnd',		'other': ['tangent', 'mag', '%s' % i]					}, #'type':blendTwoAttr},
			'magMult':          		{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['tangent', 'mag', '%s' % i]					}, 
			'magLengthMult':     		{'desc': globalName, 'side': side,	'warble': 'mult',		'other': ['tangent', 'mag', 'length', '%s' % i]			}, #'type':multiplyDivide},
			'pointCls':          		{'desc': globalName, 'side': side,	'warble': 'cls',		'other': ['point', '%s' % i]							}, #'type':transform},
			'pLen':          	     	{'desc': globalName, 'side': side,	'warble': 'arcLen',		'other': ['curve', 'midPoint']							}, #'type':transform},

			'nearest':                  {'desc': globalName, 'side': side,	'warble': 'cp',			'other': ['bez', 'midPoint']}, # 'type':curveInfo},
			'midPointInfo':             {'desc': globalName, 'side': side,	'warble': 'arcLen',		'other': ['bez', 'midPoint']}, # 'type':curveInfo},
			'curveLength':             	{'desc': globalName, 'side': side,	'warble': 'curveLen',	'other': ['bez']}, # 'type':curveInfo},
			'midPointPercentage':     	{'desc': globalName, 'side': side,	'warble': 'div',		'other': ['midPoint', 'percentage']}, # 'type':multiplyDivide},
			'curvePathGroup':         	{'desc': subName, 	 'side': side,	'warble': 'rigGroup',	'other': ['offsets', n]}, # 'type':transform},
			'edgeRange':              	{'desc': subName, 	 'side': side,	'warble': 'rng',		'other': ['edge']}, # 'type':setRange},
			'curveLengthNormalize':   	{'desc': subName, 	 'side': side,	'warble': 'div',		'other': ['curveLen', 'normalize', n]}, # 'type':multiplyDivide},
			'paramRange':         		{'desc': subName, 	 'side': side,	'warble': 'rng',		'other': ['param', n]}, # 'type':setRange},
			'mp':                 		{'desc': subName, 	 'side': side,	'warble': 'mp',			'other': ['offset', n]}, # 'type':motionPath},
			'offset':                	{'desc': subName, 	 'side': side,	'warble': None,			'other': ['offset', n]}, # 'type':transform},
			'twistParamRev':      		{'desc': subName, 	 'side': side,	'warble': 'rev',		'other': ['offset', n]}, # 'type':reverse},
			'twistStartMult':     		{'desc': subName, 	 'side': side,	'warble': 'mult',		'other': ['offset', n]}, # 'type':multDoubleLinear},
			'twistEndMult':       		{'desc': subName, 	 'side': side,	'warble': 'mult',		'other': ['offset', n]}, # 'type':multDoubleLinear},
			'twistAdd':           		{'desc': subName, 	 'side': side,	'warble': 'add',		'other': ['offset', n]}, # 'type':addDoubleLinear},
			'cmpMtrx':            		{'desc': subName, 	 'side': side,	'warble': 'matC',		'other': ['offset', n]}, # 'type':composeMatrix},
			'multMtrx':           		{'desc': subName, 	 'side': side,	'warble': 'matM',		'other': ['offset', n]}, # 'type':multMatrix},
			'decmpMtrx':          		{'desc': subName, 	 'side': side,	'warble': 'matD',		'other': ['offset', n]}, # 'type':decomposeMatrix},
			'volumeMult':         		{'desc': subName, 	 'side': side,	'warble': 'mult',		'other': ['offset', n]}, # 'type':multiplyDivide},
			'twistAdd0':              	{'desc': subName, 	 'side': side,	'warble': 'add',		'other': ['twist' , '0']}, # 'type':plusMinusAverage},
			'twistAdd1':              	{'desc': subName, 	 'side': side,	'warble': 'add',		'other': ['twist' , '1']}, # 'type':plusMinusAverage},
			'autoTwistMult':          	{'desc': subName, 	 'side': side,	'warble': 'mult',		'other': ['twist']}, # 'type':multiplyDivide}
			'bind':   			       	{'desc': globalName, 'side': side,	'warble': 'bind',		'other': [n]}, # 'type':multiplyDivide}
			'rigExitBind':   			{'desc': globalName,  'side': side,	'warble': 'bind',		'other': ['rigExit']}, # 'type':multiplyDivide}
			'topJnt':   				{'desc': globalName,  'side': side,	'warble': 'bind',		'other': ['rigEntrance']}, # 'type':multiplyDivide}
			'fk0ControlSS': 			{'desc': subName, 	 'side': side,	'warble': None,			'other': ['fk0', 'ori']			}, 
			'fk2ControlSS': 			{'desc': subName, 	 'side': side,	'warble': None,			'other': ['fk2', 'ori']			}, 
			'ikControlSS': 				{'desc': subName, 	 'side': side,	'warble': None,			'other': ['ik', 'par']			}, 
			'spaceSwitchGroup':        	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['spaceSwitch'],						'type': 'transform' },
			'ikhBuf':                  	{'desc': globalName, 'side': side,	'warble': 'buf',		'other': ['ikh', 'buf', 'ik'],					'type': 'transform' },
			'ikhConst':                	{'desc': globalName, 'side': side,	'warble': 'const',		'other': ['ikh', 'ik'],							'type': 'transform' },
			'pvFollowTypeChoice':      	{'desc': globalName, 'side': side,	'warble': 'choice',		'other': ['pvFollowType', 'ik'],				'type': 'choice' },
			'pvFollowGroup':           	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['pvFollow', 'ik'],					'type': 'transform' },
			'pvFollowTop':             	{'desc': globalName, 'side': side,	'warble': 'trans',		'other': ['pvFollow', 'top', 'ik'],				'type': 'transform' },
			'pvFollowUpChoice':        	{'desc': globalName, 'side': side,	'warble': 'choice',		'other': ['pvFollowUpChoice', 'ik'],			'type': 'choice' },
			'ikHandleGroup':      		{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['ikHandle', 'ik'],					'type': 'transform' },
			'scaleBlend':              	{'desc': globalName, 'side': side,	'warble': 'blnd',		'other': ['scale', 'ik'],						'type': 'blendColors' },
			'fkPoint':                 	{'desc': subName, 	 'side': side,	'warble': 'trans',		'other': ['fkSwitch'],						'type': 'transform' },
			'ikPoint':                 	{'desc': subName, 	 'side': side,	'warble': 'trans',		'other': ['ikSwitch'],						'type': 'transform' },
			'pvPoint':                 	{'desc': subName, 	 'side': side,	'warble': 'trans',		'other': ['pvSwitch', 'ik'],							'type': 'transform' },
			'ori':                     	{'desc': globalName, 'side': side,	'warble': 'oriConst',	'other': ['ori', 'ik'],							'type': 'orientConstraint' },
			'bendRigGroup':            	{'desc': globalName, 'side': side,	'warble': 'rigGroup',	'other': ['bend'],							'type': 'transform' },
			'upAxisSwitch':            	{'desc': globalName, 'side': side,	'warble': 'cond',		'other': ['upAxisSwitch', n],		'type': 'condition' },
			'bendControlsGroup':       	{'desc': globalName, 'side': side,	'warble': 'grp',		'other': ['controls'],				'type': 'transform' },
			
			'midBend':                  {'desc': subName, 	'side': side,	'warble': None,			'other': ['midBend'],							'type': 'transform' },
			'pointLoc':                	{'desc': subName, 	 'side': side,	'warble': 'loc',		'other': ['pointLoc',],				'type': 'locator' },
			'parametricCurveRigGroup': 	{'desc': subName, 	 'side': side,	'warble': 'rigGroup',	'other': ['parametricCurve'],					'type': 'transform' },
			'scaleInput':              	{'desc': globalName, 'side':side,	'warble': 'trans',		'other': ['scaleInput', n],						'type': 'transform' },
			'rigEntrance':             	{'desc': globalName, 'side':side,	'warble': 'trans',		'other': ['rigEntrance'],						'type': 'transform' },
			'rigExit':                 	{'desc': globalName, 'side':side,	'warble': 'trans',		'other': ['rigExit'],							'type': 'transform' },
			# 'midBend':    				{'desc': globalName, 'side': side,	'warble': None,			'other': ['midBend'], 							}, #'type':transform},

			'aimIkGroup':         		{ 'desc': subName,	'side':	side,		'warble': 'rigGroup',	'other': ['aimIK'],					'type': 'transform' },
			'aimIkControlsGroup': 		{ 'desc': subName,	'side':	side,		'warble': 'grp',		'other': ['controls', 'aimIK'],		'type': 'transform' },
			'aimIK':               		{ 'desc': subName,	'side':	side,		'warble': None,			'other': ['ctrl', 'aimIK'],						'type': 'transform' },
			'offsetCtrl':               { 'desc': globalName,	'side':	side,		'warble': None,			'other': [n],						'type': 'transform' },
			
			'aimIkResultGroup':   		{ 'desc': globalName,	'side':	side,		'warble': 'grp',		'other': ['resultGroup', 'aimIK'],			'type': 'transform' },
			'startResult':        		{ 'desc': subName,	'side':	side,		'warble': 'trans',		'other': ['startResult', 'aimIK'],			'type': 'transform' },
			'endResult':          		{ 'desc': subName,	'side':	side,		'warble': 'trans',		'other': ['endResult', 'aimIK'],			'type': 'transform' },
			'midResult':          		{ 'desc': globalName,	'side':	side,		'warble': 'trans',		'other': ['midResult', 'aimIK', n],			'type': 'transform' },
			
			'transMult':          	{ 'desc': globalName,	'side':	side,			'warble': 'mult',		'other': ['trans', 'aimIK', n],			'type': 'multiplyDivide' },
			'twistTrans':         		{ 'desc': globalName,	'side':	side,		'warble': 'trans',		'other': ['twistTrans', 'aimIK', n],			'type': 'transform' },
			'parameterRev':       		{ 'desc': globalName,	'side':	side,		'warble': None,			'other': ['parameterRev', 'aimIK', n],			'type': 'reverse' },
			'twistMultStart':     		{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['twist', 'start', 'aimIK', n],			'type': 'multDoubleLinear' },
			'twistMultEnd':       		{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['twist', 'end', 'aimIK', n],			'type': 'multDoubleLinear' },
			
			'staticLengthGroup':  	{ 'desc': globalName,	'side':	side,		'warble': 'grp',		'other': ['static', 'length', 'aimIK'],			'type': 'transform' },
			'staticLocStart':     	{ 'desc': globalName,	'side':	side,		'warble': 'loc',		'other': ['static', 'start', 'aimIK'],			'type': 'transform' },
			'staticLocEnd':       	{ 'desc': globalName,	'side':	side,		'warble': 'loc',		'other': ['static', 'end', 'aimIK'],			'type': 'transform' },
			'staticLength':       	{ 'desc': globalName,	'side':	side,		'warble': 'dist',		'other': ['static', 'length', 'aimIK'],			'type': 'distanceBetween' },
			'locStart':           	{ 'desc': globalName,	'side':	side,		'warble': 'loc',		'other': ['start', 'aimIK'],			'type': 'locator' },
			'locEnd':             	{ 'desc': globalName,	'side':	side,		'warble': 'loc',		'other': ['end', 'aimIK'],			'type': 'locator' },
			'length':             	{ 'desc': globalName,	'side':	side,		'warble': 'dist',		'other': ['length', 'aimIK'],			'type': 'distanceBetween' },
			'staticDistMult':     	{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['static', 'dist', 'aimIK'],			'type': 'multDoubleLinear' },
			'normalizeDiv':       	{ 'desc': globalName,	'side':	side,		'warble': 'div',		'other': ['normalize', 'aimIK'],			'type': 'multiplyDivide' },
			'squashBlend':        	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',		'other': ['squash', 'aimIK'],			'type': 'blendTwoAttr' },
			'restLengthMult':     	{ 'desc': globalName,	'side':	side,		'warble': 'mult',		'other': ['restLength', 'aimIK'],			'type': 'multDoubleLinear' },
			'stretchMap':         	{ 'desc': globalName,	'side':	side,		'warble': 'blnd',		'other': ['stretchMap', 'aimIK', n],			'type': 'blendTwoAttr' },
			'scaleMatrixSum':     	{ 'desc': globalName,	'side':	side,		'warble': 'matM',		'other': ['scale', 'aimIK', n],			'type': 'multMatrix' },
			'scaleMatrixRes':     	{ 'desc': globalName,	'side':	side,		'warble': 'matD',		'other': ['scale', 'aimIK', n],			'type': 'decomposeMatrix' },
			'paramRev':           	{ 'desc': globalName,	'side':	side,		'warble': 'rev',		'other': ['param', 'aimIK', n],			'type': 'reverse' },
			'scaleTransform':     	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['scaleTransform', 'aimIK', n],			'type': 'transform' },

			'neutralWorldUpStart':    	{ 'desc': subName,		'side':	side,		'warble': None,		'other': ['neutralWorldUpStart', 'tangent'],			'type': 'transform' },
			'neutralWorldUpEnd':      	{ 'desc': subName,		'side':	side,		'warble': None,		'other': ['neutralWorldUpEnd', 'tangent'],			'type': 'transform' },
			'neutralizeAllBlend':     	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['neutralizeAllBlend', 'tangent', n],			'type': 'blendTwoAttr' },
			'neutralizeTangentBlend': 	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['neutralizeTangentBlend', 'tangent', n],			'type': 'blendTwoAttr' },
			#2 'neutralizeAllBlend':     	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['neutralizeAllBlend', 'tangent'],			'type': 'blendTwoAttr' },
			#2 'neutralizeTangentBlend': 	{ 'desc': globalName,	'side':	side,		'warble': None,		'other': ['neutralizeTangentBlend', 'tangent'],			'type': 'blendTwoAttr' },
			'tangentDefault':           { 'desc': subName,	'side':	side,		'warble': None,		'other': ['tangentDefault', n],			'type': 'transform' },
			'tangentDefaultAdd':      	{ 'desc': subName,	'side':	side,		'warble': 'add',		'other': ['tangentDefault', 'tangent', n],			'type': 'plusMinusAverage' },
		
			'parameterSwitch':        	{ 'desc': globalName,	'side':	side,		'warble': 'choice',		'other': ['parameterSwitch'],			'type': 'choice' },
			'midPointFollowRev':      	{ 'desc': globalName,	'side':	side,		'warble': 'rev',		'other': ['midPointFollow'],			'type': 'reverse' },
			'volumePow':              	{ 'desc': subName,	'side':	side,		'warble': 'pow',		'other': ['volume'],				'type': 'multiplyDivide' },
			'volumeDiv':              	{ 'desc': subName,	'side':	side,		'warble': 'div',		'other': ['volume'],				'type': 'multiplyDivide' },
			'scaleBlndX':             	{ 'desc': subName,	'side':	side,		'warble': 'blnd',		'other': ['scaleX', n],			'type': 'blendTwoAttr' },
			'scaleBlndY':             	{ 'desc': subName,	'side':	side,		'warble': 'blnd',		'other': ['scaleY', n],			'type': 'blendTwoAttr' },
			'scaleBlndZ':             	{ 'desc': subName,	'side':	side,		'warble': 'blnd',		'other': ['scaleZ', n],			'type': 'blendTwoAttr' },

			'ctrlDistance':          	{ 'desc': subName,	'side':	side,		'warble': 'dist',		'other': ['ctrl', 'bend'],			'type': 'distanceBetween' },
			'staticDistance':        	{ 'desc': subName,	'side':	side,		'warble': 'dist',		'other': ['static', 'bend'],			'type': 'distanceBetween' },
			'bendCtrlDistNormalize': 	{ 'desc': subName,	'side':	side,		'warble': 'div',		'other': ['bendCtrl', 'normalize', 'bend'],			'type': 'multiplyDivide' },		


		}
