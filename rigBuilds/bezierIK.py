

import buildRig
class bezierIK(buildRig.rig):

	def __init__(self, fitNode=None, rigNode=None):

		if fitNode is None and rigNode is None:
			raise Exception('No data specified.')

		elif fitNode is None:
			self.rigNode = rigNode
			# Put any attributes needed for initialized rigs here

		else:

			# Initialize rigNode
			# Error Check:
			
			# Convert string input to PyNode if neccessary
			if isinstance(fitNode, str):
				fitNode = ls(fitNode)[0]

			if fitNode.rigType.get() != 'bezierIK':
				raise Exception('Incorrect rig type: %s' % fitNode.rigType.get())

			self.crvs = []

			rig.__init__(self, fitNode)



			# fitNode attributes
			doFK = False
			doOffsetFK = False # end joint orient failure
			doParametric = True
			doSplineIK = False
			# 
			doStretchLimit = False
			# 
			doVolume = False

			doStretchLimit = self.fitNode.stretchLimits.get()

			style = self.fitNode.style.get(asString=True)
			if style == 'FK Only':
				doSplineIK = False
				doParametric = False
			elif style == 'IK Only':
				doFK = False
				if doStretchLimit:
					doSplineIK = True
			elif style == 'IK to FK' or style == ' IK to FK':
				doFK = True
				doOffsetFK = True
				if doStretchLimit:
					doSplineIK = True
			else:
				doFK=True
				doSplineIK = True
				doParametric = True

			# if doFK:
			# 	raise Exception(style)


			if not all([doParametric, doSplineIK]):
				doStretchLimit = False
			if not doFK:
				doOffsetFK = False

			jointsList = 	self.fitNode.jointsList.get()
			numJoints = 	self.fitNode.resultPoints.get()+1
			pointInput = 	self.fitNode.outputJoints.inputs()[:self.fitNode.resultPoints.get()+2]

			fkShapes = 		self.fitNode.fkShapes.get()
			ikShapes = 		[self.fitNode.startShape.get(), self.fitNode.endShape.get()]

			tan1 =			self.fitNode.tangent1.get()
			tan2 =			self.fitNode.tangent2.get()

			orientation = self.fitNode.orientation.get(asString=True)

			bindEnd = False

			doBind = 		self.fitNode.bind.get()

			if not doBind:
				bindEnd = False


			# Mirroring
			if self.fitNode.side.get() == 2:
				mirror=True
			else:
				mirror=False

			if self.fitNode.mirror.get() is False:
				mirror=False

			# Move rigGroup
			xform(self.rigGroup, ws=1, m=xform(jointsList[0], q=1, ws=1, m=1))

			# Naming
			self.globalName = self.fitNode.globalName.get()
			self.subNames = []
			subAttrs = listAttr(self.fitNode, st='subName*')
			for subAttr in subAttrs:
				self.subNames.append(self.fitNode.attr(subAttr).get())

			# NAMING
			self.naming(0)
			self.names = utils.constructNames(self.namesDict)



			# ========================= RigNode Attributes =========================
			self.rigNode.rigType.set('bezier', l=1)

			
			utils.cbSep(self.rigNode)

			if doFK and not doOffsetFK:
				addAttr(self.rigNode, ct='publish', k=1, dv=0, min=0, max=1, ln='fkIk', nn='FK/IK')
				utils.cbSep(self.rigNode, ct='publish')
				addAttr(self.rigNode, ct='publish', ln='autoVis', nn='FK/IK Auto Vis', at='short', min=0, max=1, dv=1)
				setAttr(self.rigNode.autoVis, keyable=False, channelBox=True)
			if doFK:
				addAttr(self.rigNode, ct='publish', ln='fkVis', nn='FK Vis', at='short', min=0, max=1, dv=1)
				setAttr(self.rigNode.fkVis, keyable=False, channelBox=True)
			
			addAttr(self.rigNode, ct='publish', ln='ikVis', nn='IK Vis', at='short', min=0, max=1, dv=1)
			setAttr(self.rigNode.ikVis, keyable=False, channelBox=True)
			

		
			if doParametric or doSplineIK:
				addAttr(self.rigNode, ct='publish', ln='offsetCtrlsVis', at='short', min=0, max=1, dv=0, k=1)
				setAttr(self.rigNode.offsetCtrlsVis, keyable=False, channelBox=True)

			utils.cbSep(self.rigNode, ct='publish')
			# addAttr(self.rigNode, ln='bendCtrlsVis', nn='Bend Ctrl Vis', at='short', min=0, max=1, dv=1, k=1)
			# setAttr(self.rigNode.bendCtrlsVis, k=0, cb=1)

			addAttr(self.rigNode, ct='publish', ln='tangentCtrlsVis', min=0, max=1, dv=0, at='short', k=1)
			setAttr(self.rigNode.tangentCtrlsVis, k=0, cb=1)

			addAttr(self.rigNode, ln='tangentsDistanceScaling', softMinValue=0, softMaxValue=1, dv=0.5, k=1)
			
			# addAttr(self.rigNode, ln='neutralizeAll', min=0, max=1, dv=1, k=1)

			if doStretchLimit:
				utils.cbSep(self.rigNode, ct='publish')
				addAttr(self.rigNode, ct='publish', ln='stretch', softMinValue=0, softMaxValue=1, dv=1, k=1)
				addAttr(self.rigNode, ct='publish', ln='squash', softMinValue=0, softMaxValue=1, dv=1, k=1)
				addAttr(self.rigNode, ct='publish', ln='restLength', min=0.01, dv=1, k=1)
				# addAttr(self.rigNode, ln='currentNormalizedLength', dv=0)
				# self.rigNode.currentNormalizedLength.set(k=0, cb=1)
			if doVolume:
				utils.cbSep(self.rigNode, ct='publish')
				addAttr(self.rigNode, ct='publish', ln='volume', min=0, max=1, dv=0.5, keyable=True)
			
			if not hasAttr(self.rigNode, 'upAxis'):
				utils.cbSep(self.rigNode)
				addAttr(self.rigNode,ln='upAxis', at='enum', enumName='Y=1:Z=2', dv=1, k=1)

			# ========================= Vis Mults =========================
			# allVis Mults
			ikVisMult = createNode('multDoubleLinear', n=self.names.get('ikVisMult', 'rnm_ikVisMult'))
			self.rigNode.allVis >> ikVisMult.i1
			self.rigNode.ikVis >> ikVisMult.i2
			self.step(ikVisMult, 'ikVisMult')
			self.ikVis = ikVisMult.o

			if doFK:
				fkVisMult = createNode('multDoubleLinear', n=self.names.get('fkVisMult', 'rnm_fkVisMult'))
				self.rigNode.allVis >> fkVisMult.i1
				self.rigNode.fkVis >> fkVisMult.i2
				self.step(fkVisMult, 'fkVisMult')
				self.fkVis = fkVisMult.o

			debugVisMult = createNode('multDoubleLinear', n=self.names.get('debugVisMult', 'rnm_debugVisMult'))
			self.debugVis = debugVisMult.o
			self.rigNode.allVis >> debugVisMult.i1
			self.rigNode.debugVis >> debugVisMult.i2
			self.step(debugVisMult, 'debugVisMult')

			if doFK and not doOffsetFK:
				#=================== FK/IK Autovis Setup =========================
				self.sectionTag = 'fkIkAutoVis'

				fkIkAutoMult = createNode('multDoubleLinear', n=self.names.get('fkIkAutoMult', 'rnm_fkIkAutoMult'))
				self.rigNode.allVis >> fkIkAutoMult.i1
				self.rigNode.autoVis >> fkIkAutoMult.i2
				self.step(fkIkAutoMult, 'fkIkAutoMult')

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
				self.fkVis = fkAutoCond.outColorR
				fkAutoCond.operation.set(0)
				fkAutoCond.secondTerm.set(1)
				connectAttr(fkIkAutoMult.o, fkAutoCond.firstTerm)
				connectAttr(fkCond.outColorR, fkAutoCond.colorIfTrueR)
				connectAttr(fkVisMult.o, fkAutoCond.colorIfFalseR)
				connectAttr(fkVisMult.o, fkAutoCond.colorIfFalseG)
				self.step(fkAutoCond, 'fkAutoCond')

				ikAutoCond = createNode('condition', n=self.names.get('ikAutoCond', 'rnm_ikAutoCond'))
				self.ikVis = ikAutoCond.outColorR
				ikAutoCond.operation.set(0)
				ikAutoCond.secondTerm.set(1)
				connectAttr(fkIkAutoMult.o, ikAutoCond.firstTerm)
				connectAttr(ikCond.outColorR, ikAutoCond.colorIfTrueR)
				connectAttr(ikVisMult.o, ikAutoCond.colorIfFalseR)
				connectAttr(ikVisMult.o, ikAutoCond.colorIfFalseG)
				self.step(ikAutoCond, 'ikAutoCond')

			# ========================= World Group =========================
			worldGroup = createNode('transform', n=self.names.get('worldGroup', 'rnm_worldGroup'), p=self.rigGroup)
			self.worldGroup = worldGroup
			self.ikVis.connect(self.worldGroup.v)

			self.step(worldGroup, 'worldGroup')
			worldGroup.inheritsTransform.set(0)
			xform(worldGroup, rp=[0,0,0], ro=[0,0,0], ws=1)


			try:
				#=========================== FK Setup =================================
				# if doFK:
				# 	fkGroup = self.buildFkSetup(shapes=[fkShapes[0]], transforms=[jointsList[0]], mirror=mirror)
					# for fkCtrl in self.fkCtrls:
					# 	fkCtrl.message.connect(self.rigNode.fkCtrl)

				#==========================================================================
				#=========================== Bezier Setup =================================
				bezierTransforms = []
				if str(orientation) == 'world':
					for trans in range(2):
						bezierTransforms.append(createNode('transform', p=[jointsList[0], jointsList[-1]][trans]))
						xform(bezierTransforms[trans], ro=[0,0,0], ws=1)

				twistAxisChoice = 0 # Get from fitNode
				if self.fitNode.orientation.get(asString=1) == 'world':
					twistAxisChoice = self.fitNode.orientChoice.get() # Get from fitNode
				
				bezierRigGroup = self.buildBezierSetup(
					transforms=[jointsList[0], jointsList[-1]],
					ctrlTransforms=bezierTransforms if bezierTransforms else None,
					defaultTangents=[[None, tan1], [tan2, None]],
					shapes=ikShapes,
					follow=False,
					twist=True,
					bias=False,
					twistAxisChoice=twistAxisChoice,
					mirror=mirror,
					# doStrength=True
					)
				self.ikVis.connect(bezierRigGroup.v)
				bezierRigGroup.controlsVis.set(1)

				if str(orientation) == 'world':
					delete(bezierTransforms)
				
				# Chest orientation
				endOriCtrlSS = spaceSwitch(
					constraintType='orient',
					controller = self.bendCtrls[1],
					constrained= self.bendCtrls[1].const.get(),
					prefix = self.names.get('endOriCtrlSS', 'rnm_endOriCtrlSS'),
					p=self.rigGroup,
					# p=self.ssGroup,
					targets=[self.rigsGroup, self.bendCtrls[1].buf.get()],
					labels=['World', 'Parent'],
					offsets=True,
					)
				endOriCtrlSS.setDefaultBlend(1)


				self.rigNode.tangentsDistanceScaling.connect(bezierRigGroup.tangentsDistanceScaling)
				# if doFK:
				# 	self.matrixConstraint(self.fkCtrls[-1], bezierRigGroup, r=1, s=1)

				displaySmoothness(self.crvs[0], pointsWire=16)
				
				if doParametric:
					# Motion path groups
					crvPathRig = self.buildCurvePartitionsSetup(
						self.crvs[0], 
						nameVars='0',
						partitionParams=[0, 1],
						numJointsList=[numJoints],
						mirror=mirror,
						createOffsetControls=(False if doStretchLimit else True),
						rotationStyle=(None if doStretchLimit else 'aim'),
						twist=(False if doStretchLimit else True),
						bindEnd=True
					)
					results = crvPathRig.results.get()


				if doSplineIK:
					ikSplineRig = self.buildIKSplineSetup(
						crv=self.crvs[0], 
						points=pointInput, 
						mirror=mirror, 
						selectionPriority=2,
					)
					results = ikSplineRig.results.get()

				

				# # =========================== Twist ===========================
				# #### Bend ctrls
				if doParametric and not doStretchLimit:
					self.bendCtrls[0].twist.connect(				self.twistAdds[0].input2D[0].getChildren()[0])
					self.socket(self.bendCtrls[0]).twist.connect(	self.twistAdds[0].input2D[1].getChildren()[0])

					self.bendCtrls[1].twist.connect(				self.twistAdds[0].input2D[0].getChildren()[1])
					self.socket(self.bendCtrls[1]).twist.connect(	self.twistAdds[0].input2D[1].getChildren()[1])

				if doSplineIK:
					self.bendCtrls[0].twist.connect(				self.twistAdds[0].input2D[0].getChildren()[0])
					self.socket(self.bendCtrls[0]).twist.connect(	self.twistAdds[0].input2D[1].getChildren()[0])

					self.bendCtrls[1].twist.connect(				self.twistAdds[0].input2D[0].getChildren()[1])
					self.socket(self.bendCtrls[1]).twist.connect(	self.twistAdds[0].input2D[1].getChildren()[1])


				# Squash and stretch limits
				if doStretchLimit:

					staticLocatorsGroup = createNode('transform', n=self.names.get('staticLocatorsGroup', 'rnm_staticLocatorsGroup'), p=ikSplineRig)
					self.step(staticLocatorsGroup, 'staticLocatorsGroup')

					bezLocs = []
					staticBezLocs = []
					i=0
					print '\n'
					print crvPathRig.results.get()
					print ikSplineRig.results.get()
					
					for bezPoint, ikJnt in zip(crvPathRig.results.get(), ikSplineRig.results.get()):
						
						# if i==4:
						# 	raise Exception('4')

						bezLoc2 = createNode('locator', n='%s_dist_LOC' % bezPoint, p=bezPoint)
						self.step(bezLoc2, 'bezLoc')
						bezLoc2.hide()
						bezLocs.append(bezLoc2)

						# 

						staticBezPoint = createNode('transform', n=self.names.get('staticBezPoint', 'rnm_staticBezPoint'), p=staticLocatorsGroup)
						self.step(staticBezPoint, 'staticBezPoint')
						utils.snap(bezPoint, staticBezPoint)

						staticBezLoc2 = createNode('locator', n='%s_dist_LOC' % staticBezPoint, p=staticBezPoint)
						self.step(staticBezLoc2, 'staticBezLoc')
						staticBezLoc2.hide()
						staticBezLocs.append(staticBezLoc2)

						if not i==0: # Skip 0
							# Distance
							bezLoc1 = bezLocs[i-1]
							staticBezLoc1 = staticBezLocs[i-1]

							bezDist = createNode('distanceBetween', n=self.names.get('bezDist', 'rnm_bezDist'))
							self.step(bezDist, 'bezDist')

							bezLoc1.worldPosition.connect(bezDist.point1)
							bezLoc2.worldPosition.connect(bezDist.point2)

							# Static distance
							staticBezDist = createNode('distanceBetween', n=self.names.get('staticBezDist', 'rnm_staticBezDist'))
							self.step(staticBezDist, 'staticBezDist')

							staticBezLoc1.worldPosition.connect(staticBezDist.point1)
							staticBezLoc2.worldPosition.connect(staticBezDist.point2)

							# # Mult static by rig input
							staticBezDistMult = createNode('multDoubleLinear', n=self.names.get('staticBezDistMult', 'rnm_staticBezDistMult'))
							self.step(staticBezDistMult, 'staticBezDistMult')
							staticBezDist.distance.connect(staticBezDistMult.i1)
							self.rigNode.restLength.connect(staticBezDistMult.i2)

							# Normalize
							normalizeDiv = createNode('multiplyDivide', n=self.names.get('normalizeDiv', 'rnm_normalizeDiv'))
							self.step(normalizeDiv, 'normalizeDiv')
							normalizeDiv.operation.set(2)

							bezDist.distance.connect(normalizeDiv.input1X)
							staticBezDistMult.output.connect(normalizeDiv.input2X)



							# Stretch
							stretchBlend = createNode( 'blendTwoAttr', n=self.names.get('stretchBlend', 'rnm_stretchBlend') )
							self.step(stretchBlend, 'stretchBlend')
							stretchBlend.i[0].set(1)
							normalizeDiv.outputX.connect(stretchBlend.i[1])
							self.rigNode.stretch.connect(stretchBlend.ab)


							# Squash
							squashBlend = createNode( 'blendTwoAttr', n=self.names.get('squashBlend', 'rnm_squashBlend') )
							self.step(squashBlend, 'squashBlend')
							squashBlend.i[0].set(1)
							normalizeDiv.outputX.connect(squashBlend.i[1])
							self.rigNode.squash.connect(squashBlend.ab)

	
							# Squash/Stretch combiner
							squashStretchCond = createNode( 'condition', n=self.names.get('stretchBlend', 'rnm_stretchBlend') )
							self.step(squashStretchCond, 'squashStretchCond')
							squashStretchCond.operation.set(2) # Greater Than
							normalizeDiv.outputX.connect(squashStretchCond.firstTerm)

							squashStretchCond.secondTerm.set(1)

							stretchBlend.o.connect(squashStretchCond.colorIfTrueR)
							squashBlend.o.connect(squashStretchCond.colorIfFalseR)


							restLengthMult = createNode('multDoubleLinear', n=self.names.get('restLengthMult', 'rnm_restLengthMult'))
							self.step(restLengthMult, 'restLengthMult')
							squashStretchCond.outColorR.connect(restLengthMult.i1)
							self.rigNode.restLength.connect(restLengthMult.i2)


							denormalizeMult = createNode('multDoubleLinear', n=self.names.get('denormalizeMult', 'rnm_denormalizeMult'))
							self.step(denormalizeMult, 'denormalizeMult')
							denormalizeMult.i1.set(bezDist.distance.get())
							restLengthMult.o.connect(denormalizeMult.i2)
							

							denormalizeMult.o.connect(ikJnt.tx)

							

						i=i+1

					results = ikSplineRig.results.get()


				if doFK:

					fkGroup = self.buildFkSetup(shapes=fkShapes, transforms=results, mirror=mirror)
					self.fkVis.connect(fkGroup.v)

					# FK Offset Option
					if doOffsetFK:
						boneIndic = utils.boneIndic(self.fkCtrls[-1], results[-1], blackGrey=1)[0]
						self.debugVis.connect(boneIndic.v)


						# Create an external result chain with edits (for bend control)
						# Regular ik spline won't allow changes to orientation within heirarchy, but heirarchy still needs to be preserved to allow
						# edits to fk offset controls (no constraints)
						splineHierarchy = []
						for i, point in enumerate(results):
							self.naming(n=i)
							self.names = utils.constructNames(self.namesDict)

							splineRetarget = createNode( 'transform', n=self.names.get('splineRetarget', 'rnm_splineRetarget'), p=splineHierarchy[i-1] if i else ikSplineRig )
							print splineRetarget
							self.step(splineRetarget, 'splineRetarget')
							splineHierarchy.append(splineRetarget)

							if i==0:
								self.matrixConstraint(point, splineRetarget, t=1, s=1, offset=False)
								self.matrixConstraint(self.bendCtrls[0], splineRetarget, t=0, r=1, offset=False)
								splineRetarget.t.connect(self.fkCtrls[i].buf.get().t)
								splineRetarget.r.connect(self.fkCtrls[i].buf.get().r)
								splineRetarget.s.connect(self.fkCtrls[i].buf.get().s)


							elif point == results[-1] :
								self.matrixConstraint(point, splineRetarget, t=1, s=1, offset=False)
								self.matrixConstraint(self.bendCtrls[-1], splineRetarget, t=0, r=1, offset=False)
								# endSS = simpleSpaceSwitch(
								# 	constraintType='orient',
								# 	controller=self.fkCtrls[i],
								# 	constrained=self.fkCtrls[i],
								# 	prefix = self.names.get('endSS', 'rnm_endSS'),
								# 	targets=[point, self.bendCtrls[-1]],
								# 	labels=['Default', 'IK'],
								# 	offsets=True,
								# )
								splineRetarget.t.connect(self.fkCtrls[i].buf.get().t)
								splineRetarget.r.connect(self.fkCtrls[i].buf.get().r)
								splineRetarget.s.connect(self.fkCtrls[i].buf.get().s)
							else:
								self.matrixConstraint(point, splineRetarget, t=1, r=1, s=1, offset=False)


								# FK chain driven by IK rig
								splineRetarget.t.connect(self.fkCtrls[i].buf.get().t)
								splineRetarget.r.connect(self.fkCtrls[i].buf.get().r)
								splineRetarget.s.connect(self.fkCtrls[i].buf.get().s)

						results = self.fkCtrls



					# FK/IK Switch Option
					else:
						fkIkGroup =  createNode('transform', n=self.names.get('fkIkGroup', 'rnm_fkIkGroup'), p=self.rigGroup)
						self.step(fkIkGroup, 'fkIkGroup')
					
						switchGroup = createNode('transform', n=self.names.get('switchGroup','rnm_switchGroup'), p=fkIkGroup)
						self.step(switchGroup, 'switchGroup')
						self.publishList.append(switchGroup)
						# ENTRANCE
						fkEntrance = createNode('transform', n=self.names.get('fkEntrance', 'rnm_fkEntrance'), p=fkIkGroup)
						self.step(fkEntrance, 'fkEntrance')
						utils.snap(self.fkCtrls[0], fkEntrance)
						self.matrixConstraint(self.fkCtrls[0], fkEntrance, t=1, r=0, s=0)

						ikEntrance = createNode('transform', n=self.names.get('ikEntrance', 'rnm_ikEntrance'), p=fkIkGroup)
						self.step(ikEntrance, 'ikEntrance')
						utils.snap(results[0], ikEntrance)
						self.matrixConstraint(results[0], ikEntrance, t=1, r=0, s=0)
						self.matrixConstraint(self.bendCtrls[0], ikEntrance, t=0, r=1, s=1, offset=True)

						rigEntrance = createNode('transform', n=self.names.get('rigEntrance', 'rnm_rigEntrance'), p=fkIkGroup)
						self.step(rigEntrance, 'rigEntrance')
						utils.snap(results[0], rigEntrance)

						rigEntranceScaleBlend = createNode('blendColors', n=self.names.get('rigEntranceScaleBlend', 'rnm_rigEntranceScaleBlend'))
						self.step(rigEntranceScaleBlend, 'rigEntranceScaleBlend')
						fkEntrance.scale.connect(rigEntranceScaleBlend.color1)
						ikEntrance.scale.connect(rigEntranceScaleBlend.color2)
						self.rigNode.fkIk.connect(rigEntranceScaleBlend.blender)
						rigEntranceScaleBlend.output.connect(rigEntrance.scale)
						
						fkIkStartSS = simpleSpaceSwitch(
							constraintType='parent',
							constrained= rigEntrance,
							prefix = self.names.get('fkIkStartSS', 'rnm_fkIkStartSS'),
							targets=[fkEntrance, ikEntrance],
							labels=['FK', 'IK'],
							offsets=True,
						)
						self.rigNode.fkIk.connect(fkIkStartSS.blendAttr)

						self.matrixConstraint(ikEntrance, rigEntrance, t=0, r=0, s=1)

						# EXIT
						fkExit = createNode('transform', n=self.names.get('fkExit', 'rnm_fkExit'), p=fkIkGroup)
						self.step(fkExit, 'fkExit')
						utils.snap(self.fkCtrls[-1], fkExit)
						self.matrixConstraint(self.fkCtrls[-1], fkExit, t=1, r=1, s=0)

						ikExit = createNode('transform', n=self.names.get('ikExit', 'rnm_ikExit'), p=fkIkGroup)
						self.step(ikExit, 'ikExit')
						utils.snap(results[-1], ikExit)
						self.matrixConstraint(results[-1], ikExit, t=1, r=0, s=0)
						self.matrixConstraint(self.bendCtrls[-1], ikExit, t=0, r=1, s=1, offset=True)

						rigExit = createNode('transform', n=self.names.get('rigExit', 'rnm_rigExit'), p=fkIkGroup)
						self.step(rigExit, 'rigExit')
						utils.snap(results[0], rigExit)

						fkIkEndSS = simpleSpaceSwitch(
							constraintType='parent',
							constrained= rigExit,
							prefix = self.names.get('fkIkEndSS', 'rnm_fkIkEndSS'),
							targets=[fkExit, ikExit],
							labels=['FK', 'IK'],
							offsets=True,
						)
						self.rigNode.fkIk.connect(fkIkEndSS.blendAttr)


						rigExitScaleBlend = createNode('blendColors', n=self.names.get('rigExitScaleBlend', 'rnm_rigExitScaleBlend'))
						self.step(rigExitScaleBlend, 'rigExitScaleBlend')
						fkExit.scale.connect(rigExitScaleBlend.color1)
						ikExit.scale.connect(rigExitScaleBlend.color2)
						self.rigNode.fkIk.connect(rigExitScaleBlend.blender)
						rigExitScaleBlend.output.connect(rigExit.scale)


						# Points
						switches = []
						for i, point in enumerate(results):
							self.naming(n=i)
							self.names = utils.constructNames(self.namesDict)
							# result transforms
							switch = createNode('transform', n=self.names.get('switch', 'rnm_switch'), p=switchGroup)
							utils.snap(point, switch)
							self.step(switch, 'switch')
							switches.append(switch)

							fkIkSwitchSS = simpleSpaceSwitch(
								constrained= switch,
								controller=self.rigNode.fkIk,
								targets=[self.fkCtrls[i], results[i]],
								labels=['FK', 'IK'],
								prefix = self.names.get('fkIkSwitchSS', 'rnm_fkIkSwitchSS'),
								constraintType='parent',
								offsets=True,
							)
							# self.rigNode.fkIk.connect(fkIkSwitchSS.rigNode.parentSpaceBlend)
				

					offsetResults = []
					# Offset controls
					for i, point in enumerate(results):
						ctrlParent = None
						if doOffsetFK:
							ctrlParent = self.fkCtrls[i]
						else:
							ctrlParent = offsetResults[i-1] if i else switchGroup

						self.naming(n=i)
						self.names = utils.constructNames(self.namesDict)
						par = self.fkCtrls[i] if doOffsetFK else switches[i]
						offsetCtrl = self.createControlHeirarchy(
							name=self.names.get('offsetCtrl', 'rnm_offsetCtrl'), 
							transformSnap=self.fkCtrls[i],
							selectionPriority=2,
							ctrlParent=ctrlParent,
							outlinerColor = (0,0,0),
							par=par)

						offsetResults.append(offsetCtrl)
						self.rigNode.offsetCtrlsVis.connect(offsetCtrl.buf.get().v)

					results = offsetResults



				results = self.buildScaleLengthSetup(scaleInputs=self.bendCtrls, distanceInputs=[results[0], results[1]], nodes=results, settingsNode=self.rigNode)

				rigEntranceBuf = createNode('transform', n=self.names.get('rigEntranceBuf', 'rnm_rigEntranceBuf'), p=self.rigGroup)
				self.step(rigEntranceBuf, 'rigEntranceBuf')
				utils.snap(results[0], rigEntranceBuf)
				# if style == 'IK Only' or style == 'IK to FK':
				if style == 'IK Only':
					self.matrixConstraint(self.bendCtrls[0], rigEntranceBuf, t=0, r=1, s=0, offset=False)
					self.matrixConstraint(results[0].getParent(), rigEntranceBuf, t=1, r=0, s=1, offset=False)
				else:
					self.matrixConstraint(results[0].getParent(), rigEntranceBuf, t=1, r=1, s=1, offset=False)

				rigEntrance = createNode('transform', n=self.names.get('rigEntrance', 'rnm_rigEntrance'), p=rigEntranceBuf)
				self.step(rigEntrance, 'rigEntrance')
				self.bendCtrls[0].twist.connect(rigEntrance.rx)

				rigExitBuf = createNode('transform', n=self.names.get('rigExitBuf', 'rnm_rigExitBuf'), p=self.rigGroup)
				self.step(rigExitBuf, 'rigExitBuf')
				utils.snap(results[0], rigExitBuf)

				if style == 'IK Only':
					self.matrixConstraint(self.bendCtrls[-1], rigExitBuf, t=0, r=1, s=0, offset=False)
					self.matrixConstraint(results[-1].getParent(), rigExitBuf, t=1, r=0, s=1, offset=False)
				else:
					self.matrixConstraint(results[-1].getParent(), rigExitBuf, t=1, r=1, s=1, offset=False)

				rigExit = createNode('transform', n=self.names.get('rigExit', 'rnm_rigExit'), p=rigExitBuf)
				self.step(rigExit, 'rigExit')
				self.bendCtrls[-1].twist.connect(rigExit.rx)

				results.insert(0, rigEntrance)
				results.append(rigExit)

				# results = []
				print 'Results:'
				print results
				for i, point in enumerate(results):

					self.naming(n=i)
					self.names = utils.constructNames(self.namesDict)


					if mirror:
						point = self.socket(point)
					# 	ctrl.rotateY.set(-180)
					# 	ctrl.scaleX.set(-1)

					point.message.connect(self.rigNode.socketList, na=1)
					# self.socketList.append(point)
					if doBind:
						bind = createNode('joint', n=self.names.get('bind', 'rnm_bind'), p=point)
						self.bindList.append(bind)
						self.step(bind, 'bind')
						bind.hide()

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
					self.constructSelectionList(selectionName='bendCtrls', selectionList=self.bendCtrls)
					self.constructSelectionList(selectionName='tangentCtrls', selectionList=self.tangentCtrls)
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
