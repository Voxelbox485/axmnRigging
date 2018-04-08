from pymel.core import *
def twistExtractorMatrix(node=None, base=None, twistAxis=(1,0,0), dev=False):
	print '# twistExtractorMatrix'
	'''
	Creates a twist value reader measuring the difference in twist from the base node using matrices.
	Pro: Less overhead, still works with nodes in heirarchy between base and point
	Con: Flips at 180deg (down from 360)

	change rotate order on q2e

	'''
	# if twistAxisChoice < 0 or twistAxisChoice > 2:
	# 	raise Exception('twistAxisChoice out of range')

	# twistAxisChoiceIndex = twistAxisChoice
	# axis = ['rx', 'ry', 'rz'][twistAxisChoiceIndex]
	# rotateOrderOptions = []

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



	for point in points:
		# Names
		prefix = point.shortName()

		else:
			names = {
			'staticLoc':			'%s_twist_static'			% (prefix),
			'multMatrix':			'%s_twist_multMatrix'		% (prefix),
			'decmp':				'%s_twist_decmp'			% (prefix),
			'quatToEuler':			'%s_twist_q2e'				% (prefix),
			'mult':					'%s_twist_mult'				% (prefix),
			}

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
		utils.messageConnect(staticLoc, 'rigNode', settingsNode, 'staticLoc')


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
		# print 'twistAxisChoiceIndex: %s' % twistAxisChoiceIndex
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
			utils.messageConnect(rigNode, 'rigNodes', nodeList, 'rigNode')


	return settingsNode

