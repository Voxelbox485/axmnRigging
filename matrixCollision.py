from pymel.core import *
import utils
import buildRig
__author__ = 'Alexander Mann'
__version__ = '0.1'
__email__ = 'AlexKMann@comcast.net'
__status__ = 'Development'
# Based on video tutorial by Marco D'Ambros (https://vimeo.com/49104367) #rigTip - maya collision system with matrix


def matrixCollision(control=None, constrained=None, surface=None):
	# Creates a simple collision detector that orients object to surface

	# Create nodes if not supplied
	if control is None:
		control = createNode('transform', n='matrixCollisionControl')
	if constrained is None:
		constrained = createNode('transform', n='matrixCollisionConstrained')
	if surface is None:
		surface, surfaceCH = polyPlane(n='matrixCollisionSurface', sx=10, sy=10, w=10, h=10, constructionHistory=True, createUVs=0)
		print surface
	# Error checks


	base = control.getParent()
	if base is None:
		raise Exception('Control object has no parent.')

	# Convert to string to pynode if necessary
	if isinstance(control, str) or isinstance(control, unicode):
		if len(ls(control)) == 1:
			control = ls(control)[0]
		elif len(ls(control)) == 0:
			raise Exception('No object found with name: %s' % control)
		else:
			raise Exception('More than one object found with name: %s' % control)

	if isinstance(constrained, str) or isinstance(constrained, unicode):
		if len(ls(constrained)) == 1:
			constrained = ls(constrained)[0]
		elif len(ls(constrained)) == 0:
			raise Exception('No object found with name: %s' % constrained)
		else:
			raise Exception('More than one object found with name: %s' % constrained)

	if isinstance(surface, str) or isinstance(surface, unicode):
		if len(ls(surface)) == 1:
			surface = ls(surface)[0]
		elif len(ls(surface)) == 0:
			raise Exception('No object found with name: %s' % surface)
		else:
			raise Exception('More than one object found with name: %s' % surface)


	# Test input types
	for i, testNode in enumerate([control, constrained]):
		if not isinstance(testNode, nt.Transform):
			raise Exception('Input arugument %s is not a transform: %s' % (['control', 'constrained'][i], testNode))
	
	# Set surface to the actual transform if it's been input as the shape node
	if isinstance(surface, nt.Mesh):
		sufaceShape = surface
		surface = sufaceShape.getParent()
	else:
		if not isinstance(surface, nt.Transform):
			raise Exception('Input arugument surface is not a transform: %s' % (surface))
		else:
			if not surface.getShapes():
				raise Exception('No shape found under surface input: %s' % (surface))
			else:
				surfaceShape = None
				for shp in surface.getShapes():
					if isinstance(shp, nt.Mesh):
						surfaceShape = shp
						break
				if not surfaceShape:
					raise Exception(('No mesh found under surface input: %s' % (surface)))

	# Naming
	names = {
		'collisionPoint': 		'collisionPoint',
		'twistComp': 			'twistComp',
		'collPointDecmp': 		'collPointDecmp',
		'closest': 				'closest',
		'twistAdd': 			'twistAdd',
		'axZ': 					'axZ',
		'axX': 					'axX',
		'fourByFour': 			'fourByFour',
		'diffMat': 				'diffMat',
		'diffDecmp': 			'diffDecmp',
		'distRng': 				'distRng',
		'offsetMat': 			'offsetMat',
		'controlDecmp': 		'controlDecmp',
		'offsetDecmp': 			'offsetDecmp',
		'rotBlnd': 				'rotBlnd',
		'transCond': 			'transCond',
	}

	# Initialize Build


	# Collision Point under control to determine where to halt transform
	collisionPoint = createNode('transform', n=names.get('collisionPoint'), p=control)
	collisionPoint.displayHandle.set(1, k=1)

	utils.cbSep(collisionPoint)
	addAttr(collisionPoint, ln='collisionDistance', min=0, dv=1, k=1)

	collPointDecmp = createNode('decomposeMatrix', n=names.get('collPointDecmp'))
	collisionPoint.worldMatrix.connect(collPointDecmp.inputMatrix)


	# Closest point
	closest = createNode('closestPointOnMesh', n=names.get('closest'))
	collPointDecmp.outputTranslate.connect(closest.inPosition)
	surfaceShape.outMesh.connect(closest.inMesh)
	surface.worldMatrix.connect(closest.inputMatrix)

	# use twist on axis to orient result transform
	buildRig.twistExtractorMatrix(points=[control], base=base, settingsNode=collisionPoint, twistAxisChoice=1)

	twistAdd = createNode('animBlendNodeAdditiveRotation', n=names.get('twistAdd'))
	collisionPoint.twist.connect(twistAdd.inputAY)
	twistAdd.rotateOrder.set(1)
	twistAdd.rotationInterpolation.set(1)



	# Vector Product Z (convert closest point normal to standard matrix by getting double cross product)
	axZ = createNode('vectorProduct', n=names.get('axZ'))
	axZ.operation.set(2) # Cross product
	axZ.input1.set(1,0,0)
	axZ.normalizeOutput.set(1)
	closest.normal.connect(axZ.input2)

	# Vector Product X (convert closest point normal to standard matrix by getting double cross product)
	axX = createNode('vectorProduct', n=names.get('axX'))
	axX.operation.set(2) # Cross product
	axX.normalizeOutput.set(1)
	closest.normal.connect(axX.input1)
	axZ.output.connect(axX.input2)
	
	# Four by four matrix (Construct result of closest point to matrix)
	fourByFour = createNode('fourByFourMatrix', n=names.get('fourByFour'))
	axX.outputX.connect(fourByFour.in00)
	axX.outputY.connect(fourByFour.in01)
	axX.outputZ.connect(fourByFour.in02)

	closest.normalX.connect(fourByFour.in10)
	closest.normalY.connect(fourByFour.in11)
	closest.normalZ.connect(fourByFour.in12)

	axZ.outputX.connect(fourByFour.in20)
	axZ.outputY.connect(fourByFour.in21)
	axZ.outputZ.connect(fourByFour.in22)

	closest.positionX.connect(fourByFour.in30)
	closest.positionY.connect(fourByFour.in31)
	closest.positionZ.connect(fourByFour.in32)

	# Create a matrix to measure difference between collision point and closest point
	diffMat = createNode('multMatrix', n=names.get('diffMat'))
	fourByFour.output.connect(diffMat.matrixIn[0])
	collisionPoint.worldInverseMatrix.connect(diffMat.matrixIn[1])

	diffDecmp = createNode('decomposeMatrix', n=names.get('diffDecmp'))
	diffMat.matrixSum.connect(diffDecmp.inputMatrix)

	distRng = createNode('setRange', n=names.get('distRng'))
	diffDecmp.outputTranslateY.connect(distRng.valueX)
	distRng.minX.set(0)
	distRng.maxX.set(1)
	distRng.oldMinX.set(-1)
	distRng.oldMaxX.set(0)

	uc = createNode('unitConversion')
	uc.conversionFactor.set(-1)

	collisionPoint.collisionDistance.connect(uc.input)
	uc.output.connect(distRng.oldMinX)

	offsetMat = createNode('multMatrix', n=names.get('offsetMat'))
	diffMat.matrixSum.connect(offsetMat.matrixIn[0])
	control.worldMatrix.connect(offsetMat.matrixIn[1])

	

	controlDecmp = createNode('decomposeMatrix', n=names.get('controlDecmp'))
	control.worldMatrix.connect(controlDecmp.inputMatrix)

	offsetDecmp = createNode('decomposeMatrix', n=names.get('offsetDecmp'))
	offsetMat.matrixSum.connect(offsetDecmp.inputMatrix)

	offsetDecmp.outputRotate.connect(twistAdd.inputB)

	rotBlnd = createNode('pairBlend', n=names.get('rotBlnd'))
	rotBlnd.translateXMode.set(1)
	rotBlnd.translateYMode.set(1)
	rotBlnd.translateZMode.set(1)
	rotBlnd.rotInterpolation.set(1)
	distRng.outValueX.connect(rotBlnd.weight)

	twistAdd.o.connect(rotBlnd.inRotate2)
	

	controlDecmp.outputRotate.connect(rotBlnd.inRotate1)
	rotBlnd.outRotate.connect(constrained.rotate)

	transCond = createNode('condition', n=names.get('transCond'))
	diffDecmp.outputTranslateY.connect(transCond.firstTerm)
	transCond.secondTerm.set(0)
	transCond.operation.set(2)
	offsetDecmp.outputTranslate.connect(transCond.colorIfTrue)
	controlDecmp.outputTranslate.connect(transCond.colorIfFalse)
	transCond.outColor.connect(constrained.translate)

	# Freeze collision point control
	for attribute in [ collisionPoint.tx, collisionPoint.tz, collisionPoint.rx, collisionPoint.ry, collisionPoint.rz, collisionPoint.sx, collisionPoint.sy, collisionPoint.sz ]:
		attribute.set(l=1, k=0)
