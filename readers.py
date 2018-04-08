from pymel.core import *
import utils as rb
import colorOverride as col

def twistExtractor(points=None, twistAxis=[1.0, 0.0, 0.0], upVector=[0.0, 1.0, 0.0], rigNode=None, twistAxisChoice=0):
	'''
	Creates a twist value reader on each point, which determines a twist value based on the
	difference between it's base orientation and it's current orientation, up to 360deg in either direction.
	Also creates a group with nullified twist values, which can have its own uses.
	(It may be preferrable to inverse the twist output value (setting multiplier to -1) and nullify existing twist rotation), which will allow manual
	control over the presense of twist)

	Works on selection when no points specified.
	'''

	# Script variables
	dev = False
	buck = False
	axis = ['rx', 'ry', 'rz']


	# Error check
	if points is None:
		points = ls(sl=True)
	if not isinstance(points, list):
		points = [points]
	if len(points) > 2 or len(points) < 1:
		raise Exception('Select one/two transforms')
	for point in points:
		if not isinstance(point, PyNode):
			raise Exception('%s is not a PyNode.' % point)
		if not objectType(point, isAType='transform'):
			raise Exception('%s is not a transform.' % point)

	startT = xform(points[0], q=1, t=1, ws=1)
	startR = xform(points[0], q=1, ro=1, ws=1)
	if len(points) == 2:
		endT = xform(points[1], q=1, t=1, ws=1)
		endR = xform(points[1], q=1, ro=1, ws=1)

	# Names
	prefix = points[0].shortName().split('|')[-1]
	if buck:
		names = {
		# 'parentGrp':		'%s_twistParent'				% (prefix),
		'rigGrp':			'grp_%s_twistExtractor'			% (prefix),
		'aimAt':			'null_%s_twistAimAt'			% (prefix),
		'aimBuf':			'buf_%s_twistAim'				% (prefix),
		'twistRes':			'null_%s_twist'					% (prefix),
		'aimGrp':			'grp_%s_aim'					% (prefix),
		'constParent':		'const_%s'						% (prefix),
		'constBuf':			'buf_%s_const'					% (prefix),
		'constTrans':		'null_%s_const'					% (prefix),
		'mult':				'mult_%s_twistDouble'			% (prefix),
		'inputMult':		'mult_%s_twistInput'			% (prefix),
		'flipFixAdd':		'add_%s_flipFix'				% (prefix),
		}
	else:
		names = {
		# 'parentGrp':		'%s_twistParent'				% (prefix),
		'rigGrp':			'%s_twistExtractor'				% (prefix),
		'aimAt':			'%s_twistAimAt'					% (prefix),
		'aimBuf':			'%s_twistAim_BUF'				% (prefix),
		'twistRes':			'%s_twist'						% (prefix),
		'aimGrp':			'%s_aim'						% (prefix),
		'constParent':		'%s_CONST'						% (prefix),
		'constBuf':			'%s_const_BUF'					% (prefix),
		'constTrans':		'%s_const_TRANS'				% (prefix),
		'mult':				'%s_twistDouble_MULT'			% (prefix),
		'inputMult':		'%s_twistInput_MULT'			% (prefix),
		'flipFixAdd':		'%s_flipFix_ADD'				% (prefix),
		}

	nodeList = []
	freezeList = []

	with UndoChunk():
		if objExists(names['rigGrp']):
			oldRigGrp = ls(names['rigGrp'])[0]
			# if objExists(names['parentGrp']):
			# 	oldParentGrp = ls(names['parentGrp'])[0]
			# 	parent = oldParentGrp.getParent()[0]
			# 	if dev: print 'Reparenting %s' % points[0]
			# 	parent(points[0], parent)
			# 	if dev: print 'Deleting parent group %s' % oldParentGrp
			if dev: print 'Deleting %s' % (oldRigGrp.name())
			delete(oldRigGrp)
		if objExists(names['aimAt']):
			if dev: print 'Deleting %s' % (ls(names['aimAt']))
			delete(ls(names['aimAt']))


		pointParent = listRelatives(points[0], p=True)

		if dev:
			if not hasAttr(points[0], "twist"):
				addAttr(points[0], ln="twist", k=1)

		# Aim At Locator
		'''Create a locator under the transform (to be read) for the twist group to point to
		'''
		aimAt = createNode('transform', n=names['aimAt'], p=points[0])
		nodeList.append(aimAt)
		freezeList.append(aimAt)
		# If no point2, move along twist axis specified
		if len(points) == 2:
			move(aimAt, endT, rpr=1, ws=1)
			xform(aimAt, ro=endR, ws=1)
		else:
			move(aimAt, twistAxis, ls=1, r=1)
		if dev: print aimAt

		'''Parent Group
		'''
		# parentGrp = createNode('transform', n=names['parentGrp'])
		# if len(parent) == 1:
		# 	parent(parentGrp, parent[0])
		# nodeList.append(parentGrp)
		# freezeList.append(parentGrp)
		# move(parentGrp, startT, rpr=1, ws=1)
		# xform(parentGrp, ro=startR, ws=1)
		# if dev: print parentGrp
		# parent(points[0], parentGrp)

		# Rig Group
		'''The buffer/rig group
		'''
		rigGrp = createNode('transform', n=names['rigGrp'], p=points[0])
		nodeList.append(rigGrp)
		freezeList.append(rigGrp)
		if len(pointParent) == 1:
		 	parent(rigGrp, pointParent[0])
	 	else:
	 		parent(rigGrp, w=1)
		addAttr(rigGrp, ln="mult", dv=1, k=1)
		addAttr(rigGrp, ln="twist", k=1)
		addAttr(rigGrp, ln="flipFix", at='short', min=0, max=1, dv=0, k=1)
		if dev: print rigGrp

		# Aim Group
		'''Create a group above the aimed object
		'''
		aimBuf = createNode('transform', n=names['aimBuf'], p=rigGrp)
		nodeList.append(aimBuf)
		freezeList.append(aimBuf)
		move(aimBuf, startT, rpr=1, ws=1)

		

		# Temp Aim Constraint
		# aimConst = aimConstraint(aimAt, aimBuf, worldUpType='none', aimVector=[1,0,0], worldUpVector=upVector)
		aimConst = aimConstraint(aimAt, aimBuf, worldUpType='none', aimVector=twistAxis, worldUpVector=upVector)
		delete(aimConst)

		# Aim Group
		'''Create a group that will be aimed at the locator
		'''
		aimGrp = createNode('transform', n=names['aimGrp'], p=aimBuf)
		nodeList.append(aimGrp)
		freezeList.append(aimGrp)
		move(aimGrp, startT, rpr=1, ws=1)
		xform(aimGrp, ro=startR, ws=1)
		if dev: print aimGrp
		aimConst = aimConstraint(aimAt, aimGrp, worldUpType='none', aimVector=twistAxis, worldUpVector=upVector)
		# aimConst = aimConstraint(aimAt, aimGrp, worldUpType='none', aimVector=[1,0,0], worldUpVector=upVector)


		# Twist result
		'''The transform that recieves the orientation constraint, outputs X axis rotation
		'''
		twistRes = createNode('transform', n=names['twistRes'], p=aimGrp)
		nodeList.append(twistRes)
		# parent(twistRes, aimGrp)
		if dev: print twistRes

		'''Point constrain the rig group to the original transform
		'''
		point = pointConstraint(points[0], rigGrp)

		'''Orient constraint the result locator to the point and the aim group. Splits halfway between
		a static value and the rotation value of the object, so that output can doubles up to 360deg
		'''


		constParent = createNode('transform', name=names['constParent'], p=rigGrp)
		nodeList.append(constParent)
		move(constParent, startT, rpr=1, ws=1)
		xform(constParent, ro=startR, ws=1)
		# parent(constParent, rigGrp)
		if len(pointParent):
			orientConstraint(pointParent, constParent)
		pointConstraint(points[0], constParent)

		constBuf =  createNode('transform', name=names['constBuf'], p=constParent)
		nodeList.append(constBuf)
		move(constBuf, startT, rpr=1, ws=1)
		xform(constBuf, ro=startR, ws=1)

		constTrans =  createNode('transform', name=names['constTrans'], p=constBuf)
		nodeList.append(constTrans)
		points[0].r.connect(constTrans.r)

		# orient = orientConstraint(aimGrp, points[0], twistRes)
		orient = orientConstraint(aimGrp, constTrans, twistRes)

		flipFixAdd = createNode('addDoubleLinear', n=names['flipFixAdd'])
		nodeList.append(flipFixAdd)
		flipFixAdd.i2.set(1)
		rigGrp.flipFix >> flipFixAdd.i1
		flipFixAdd.o >> orient.interpType
		# Mult
		'''Doubles the halved output of the orientation constraint (which flips at 180deg)
		'''
		mult = createNode('multDoubleLinear', n=names['mult'])
		nodeList.append(mult)
		connectAttr(twistRes.attr(axis[twistAxisChoice]), mult.i1)
		mult.i2.set(2)
		if dev: print mult

		# MultInput
		'''Value for changing the result twist output (good for getting negative values etc)
		'''
		inputMult = createNode('multDoubleLinear', n=names['inputMult'])
		nodeList.append(inputMult)
		connectAttr(mult.o, inputMult.i1)
		connectAttr(rigGrp.mult, inputMult.i2)
		connectAttr(inputMult.o, rigGrp.twist)
		setAttr(rigGrp.twist, l=1, cb=1, k=0)
		if dev: print inputMult



		# Freeze nodes
		if len(freezeList):
			if not dev:
				rb.lockAndHide(freezeList, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'])
				col.setOutlinerRGB(freezeList, [0.36, 0.58, 0.64])
		

		if dev:
			connectAttr(rigGrp.twist, points[0].twist)

		if rigNode:
			rb.messageConnect(rigNode, 'rigNodes', nodeList, 'rigNode')

		return rigGrp

# sel = ls(sl=True)
# twistExtractor(points=sel, twistAxis=[-1,0,0])


def twistExtractorMatrix(points=None, base=None, settingsNode=None, rigNode=None, twistAxisChoice=0):
	'''
	Creates a twist value reader measuring the difference in twist from the base node using matrices.
	Pro: Less overhead, still works with nodes in heirarchy between base and point
	Con: Flips at 180deg (down from 360)

	Fix weird twist axis inputs (in splineBuild too)
	change rotate order on q2e

	'''
	dev = True
	buck = False
	# if twistAxisChoice < 0 or twistAxisChoice > 2:
	# 	raise Exception('twistAxisChoice out of range')
	twistAxisChoiceIndex = twistAxisChoice
	axis = ['rx', 'ry', 'rz'][twistAxisChoiceIndex]
	rotateOrderOptions = []

	# Error check
	if points is None:
		points = ls(sl=True)[0]
	if base is None:
		base = ls(sl=1)[1]
	if not isinstance(points, list):
		points = [points]
	if len(points) < 1:
		raise Exception('Select one or more transforms')
	for point in points:
		if not isinstance(point, PyNode):
			raise Exception('%s is not a PyNode.' % point)
		if not objectType(point, isAType='transform'):
			raise Exception('%s is not a transform.' % point)

	# Load important plugins	
	loadPlugin( 'matrixNodes.mll', qt=True)
	loadPlugin( 'quatNodes.mll', qt=True)

	with UndoChunk():
		for point in points:
			# Names
			prefix = point.shortName()
			if buck:
				names = {
				'staticLoc':			'null_%s_twist_static'		% (prefix),
				'multMatrix':			'multMatrix_%s_twist'		% (prefix),
				'decmp':				'decmp_%s_twist'			% (prefix),
				'quatToEuler':			'q2e_%s_twist'				% (prefix),
				'mult':					'mult_%s_twist'				% (prefix),
				}
			else:
				names = {
				'staticLoc':			'%s_twist_static'			% (prefix),
				'multMatrix':			'%s_twist_multMatrix'		% (prefix),
				'decmp':				'%s_twist_decmp'			% (prefix),
				'quatToEuler':			'%s_twist_q2e'				% (prefix),
				'mult':					'%s_twist_mult'				% (prefix),
				}


			nodeList = []

			startT = xform(point, q=1, t=1, ws=1)
			startR = xform(point, q=1, ro=1, ws=1)

			if not settingsNode:
				settingsNode = points[0]

			if not hasAttr(settingsNode, 'twist'):
				addAttr(settingsNode, ln='twist', keyable=True)
			if not hasAttr(settingsNode, 'mult'):
				addAttr(settingsNode, ln='mult', dv=1, keyable=True)


			if objectType(point, isType='joint'):
				staticLoc = createNode('joint', n=names['staticLoc'], p=base)
			else:
				staticLoc = createNode('transform', n=names['staticLoc'], p=base)
			nodeList.append(staticLoc)
			move(staticLoc, startT, rpr=1, ws=1)
			xform(staticLoc, ro=startR, ws=1)
			if objectType(point, isType='joint'):
				# Add check for rotate values
				makeIdentity(staticLoc, apply=1, t=1, r=1, s=1, n=0, pn=1)
				staticLoc.hide()
			rb.messageConnect(staticLoc, 'rigNode', settingsNode, 'staticLoc')


			multMatrix= createNode('multMatrix', n=names['multMatrix'])
			nodeList.append(multMatrix)
			
			point.worldMatrix[0] >> multMatrix.matrixIn[0]
			staticLoc.worldInverseMatrix[0] >> multMatrix.matrixIn[1]
			if dev: print '%s >> %s' % (point.worldMatrix[0], multMatrix.matrixIn[0])
			if dev: print '%s >> %s' % (staticLoc.worldInverseMatrix[0],  multMatrix.matrixIn[1])


			decmp = createNode('decomposeMatrix', n=names['decmp'])
			nodeList.append(decmp)
			multMatrix.matrixSum >> decmp.inputMatrix

			quatToEuler = createNode('quatToEuler', n=names['quatToEuler'])
			nodeList.append(quatToEuler)

			decmp.outputQuatW >> quatToEuler.inputQuatW
			print 'twistAxisChoiceIndex: %s' % twistAxisChoiceIndex
			if twistAxisChoiceIndex == 0:
				decmp.outputQuatX >>quatToEuler.inputQuatX
				quatToEuler.inputQuatY.set(0)
				quatToEuler.inputQuatZ.set(0)
				quatToEuler.inputRotateOrder.set(0)
			elif twistAxisChoiceIndex == 1:
				decmp.outputQuatY >>quatToEuler.inputQuatY
				quatToEuler.inputQuatX.set(0)
				quatToEuler.inputQuatZ.set(0)
				quatToEuler.inputRotateOrder.set(4)
			elif twistAxisChoiceIndex == 2:
				decmp.outputQuatZ >>quatToEuler.inputQuatZ
				quatToEuler.inputQuatX.set(0)
				quatToEuler.inputQuatY.set(0)
				quatToEuler.inputRotateOrder.set(2)
			else:
				raise Exception('Twist Axis Failure')

			mult = createNode('multDoubleLinear', n=names['mult'])
			nodeList.append(mult)
			settingsNode.mult >> mult.i1
			[quatToEuler.outputRotateX, quatToEuler.outputRotateY, quatToEuler.outputRotateZ][twistAxisChoiceIndex].connect(mult.i2)
			mult.o >> settingsNode.twist

			if rigNode:
				rb.messageConnect(rigNode, 'rigNodes', nodeList, 'rigNode')


	return settingsNode





def coneAngleReader(base, target, prefix=None, suffix=None, targetOffset=1.0, coneAxis=(0,0,-1), forwardAxis=(1,0,0), coneAngle=90):
	nodeList = []
	freezeList = []

	dev = 1
	if prefix is None:
		prefix=target.shortName()
	names = {
	'axisGroup':			'%s_angleReader_GRP' % 	(prefix),
	'baseVecProd':			'%s_base_VP' % 			(prefix),
	'targetVecProd':		'%s_target_VP' % 		(prefix),
	'angle':				'%s_ANGBETW' % 			(prefix),
	'mult':					'%s_MULT' % 			(prefix),
	'div':					'%s_DIV' % 				(prefix),
	'cond':					'%s_COND' % 			(prefix),
	'rev':					'%s_REV' % 				(prefix),
	'coneBuf':				'%s_cone_BUF' % 		(prefix),
	'previewCone':			'%s_previewCone_GEO' % 	(prefix),
	'radExpression':		'%s_rad_EXPR' % 		(prefix),
	'heightExpression':		'%s_height_EXPR' % 		(prefix),
	'transYExpression':		'%s_transY_EXPR' % 		(prefix)
	}
	if dev: print names


	axisGroup = createNode('transform', n=names.get('axisGroup', 'rnm_axisGroup'), p=base)
	nodeList.append(axisGroup)
	pointConstraint(target, axisGroup)

	if dev: print axisGroup


	baseVecProd = createNode('vectorProduct', n=names.get('baseVecProd', 'rnm_baseVecProd'))
	nodeList.append(baseVecProd)
	axisGroup.worldMatrix.connect(baseVecProd.matrix)
	baseVecProd.operation.set(3)
	baseVecProd.normalizeOutput.set(1)
	baseVecProd.input1.set(coneAxis)
	if dev: print baseVecProd

	targetVecProd = createNode('vectorProduct', n=names.get('targetVecProd', 'rnm_targetVecProd'))
	nodeList.append(targetVecProd)
	target.worldMatrix.connect(targetVecProd.matrix)
	targetVecProd.operation.set(3)
	targetVecProd.normalizeOutput.set(1)
	targetVecProd.input1.set(forwardAxis)
	if dev: print targetVecProd


	#reader custom attributes
	if not hasAttr(target, 'coneAngle%s' % suffix.capitalize()) and not hasAttr(target, 'value%s' % suffix.capitalize()):
		rb.cbSep(target)
	
	if not hasAttr(target, 'coneAngle%s' % suffix.capitalize()):
		addAttr(target, ln='coneAngle%s' % suffix.capitalize(), at='double', min=1, max=359, dv=coneAngle, k=True)
	if not hasAttr(target, 'value%s' % suffix.capitalize()):
		addAttr(target, ln='value%s' % suffix.capitalize(), k=1)
		target.attr('value%s' % suffix.capitalize()).set(k=0, cb=1)

	# Angle between
	angle = createNode('angleBetween', n=names.get('angle', 'rnm_angle'))
	nodeList.append(angle)
	baseVecProd.output >> angle.vector1
	targetVecProd.output >> angle.vector2
	if dev: print angle

	# Multiply
	mult = createNode('multDoubleLinear', n=names.get('mult', 'rnm_mult'))
	nodeList.append(mult)
	target.attr('coneAngle%s' % suffix.capitalize()) >> mult.input1
	mult.i2.set(0.5)
	if dev: print mult

	div = createNode('multiplyDivide', n=names.get('div', 'rnm_div'))
	nodeList.append(div)
	angle.angle >> div.input1X
	mult.o >> div.input2X
	div.operation.set(2)
	if dev: print div

	cond = createNode('condition', n=names.get('cond', 'rnm_cond'))
	nodeList.append(cond)
	div.outputX >> cond.firstTerm
	div.outputX >> cond.colorIfTrueR
	cond.secondTerm.set(1.0)
	cond.operation.set(4)
	if dev: print cond

	# reverse
	rev = createNode('reverse', n=names.get('rev', 'rnm_rev'))
	nodeList.append(rev)
	cond.outColor >> rev.input
	rev.outputX >> target.attr('value%s' % suffix.capitalize())
	if dev: print rev

	# Cone preview
	coneBuf = createNode('transform', n=names.get('coneBuf', 'rnm_coneBuf'), p=axisGroup)
	nodeList.append(coneBuf)
	if dev: print coneBuf

	coneHeight = 1.0
	previewConeTransform, previewCone = polyCone(n=names.get('previewCone', 'rnm_previewCone'), r=1, h=coneHeight, sx=12, sy=1, sz=0, ax=(0,-1,0), rcp=0, cuv=3, ch=1)
	nodeList.append(previewConeTransform)
	nodeList.append(previewCone)
	previewConeTransform.overrideEnabled.set(1)
	previewConeTransform.overrideDisplayType.set(2)
	previewConeTransform.overrideShading.set(0)
	parent(previewConeTransform, coneBuf)
	previewConeTransform.translate.set([0, 0, 0])
	previewConeTransform.rotate.set([0, 0, 0])
	previewCone.createUVs.set(0)
	if dev: print previewConeTransform
	if dev: print previewCone

	coneOri = createNode('transform', p=target)
	coneOri.translate.set(coneAxis)
	if dev: print coneOri

	aim = aimConstraint(coneOri, coneBuf, aimVector=[0,1,0], upVector=[0,1,0], worldUpVector=forwardAxis, worldUpObject=target, worldUpType='objectRotation')
	delete(aim)
	delete(coneOri)

	# Expressions
	radExpression = expression(s= '%s=sind(%s*0.5)' % (previewCone.radius, target.attr('coneAngle%s' % suffix.capitalize())), o=previewCone, ae=1, uc='all', name=names.get('radExpression', 'rnm_radExpression'))
	heightExpression = expression(s= '%s=cosd(%s*0.5)' % (previewCone.height, target.attr('coneAngle%s' % suffix.capitalize())), o=previewCone, ae=1, uc='all', name=names.get('heightExpression', 'rnm_heightExpression'))
	transYExpression = expression(s= '%s=(%s/2)' % (previewConeTransform.translateY, previewCone.height), o=previewCone, ae=1, uc='all', name=names.get('transYExpression', 'rnm_transYExpression'))
	if dev: print radExpression
	if dev: print heightExpression
	if dev: print transYExpression

	nodeList.extend([radExpression, heightExpression, transYExpression])


	# Finalize
	rb.messageConnect(axisGroup, 'rigNodes', nodeList, 'angleReader')
	if len(freezeList):
			if not dev:
				rb.lockAndHide(freezeList, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'])
				col.setOutlinerRGB(freezeList, [0.36, 0.58, 0.64])
		

	select(target)