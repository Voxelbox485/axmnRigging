import pymel.core as pm
'''
Created by Alex Mann

A couple of scripts to hook up the vehicle rig to a motion path. Select path curve and run:
import axmn_vehicle
axmn_vehicle.path()

To remove from path, select path curve and run:
axmn_vehicle.disconnectPath()
'''

def path():
	with pm.UndoChunk():
		rigNode = pm.ls('vehicleRigNode')[0]

		root = rigNode.root.inputs()[0]
		start = rigNode.start.inputs()[0]
		end = rigNode.end.inputs()[0]
		conversionMult = rigNode.conversionMult.inputs()[0]
		offsetAdd = rigNode.offsetAdd.inputs()[0]
		ctlCog = rigNode.ctlCog.inputs()[0]
		extraCog = rigNode.extraCog.inputs()[0]
		extraSteering = rigNode.extraSteering.inputs()[0]
		steering = rigNode.steering.inputs()[0]

		# get curve
		if not len(pm.ls(sl=1)):
			raise Exception('Select a curve.')
		if not len(pm.ls(sl=1)[-1].getShapes()):
			raise Exception('Select a curve.')
		curve = pm.ls(sl=1)[-1].getShapes()[0]
		if not pm.objectType(curve, isAType='nurbsCurve'):
			raise Exception('Select a curve.')

		# first check if curve is part of rig?


		# Create rig node to track nodes
		rigNode = pm.createNode('network', n='vehiclePathRigNode')
		pm.addAttr(rigNode, ln='nodes', at='message', k=1)
		pm.addAttr(rigNode, ln='curveNode', at='message', k=1)
		nodeList = []
		if not pm.hasAttr(curve, 'pathNode'):
			pm.addAttr(curve, ln='pathNode', at='message')
		curve.pathNode.connect(rigNode.curveNode)


		# move root to start of curve

		# attach a curve info node
		curveInfo = pm.createNode('curveInfo', n='crvInfo_%s' % curve)
		nodeList.append(curveInfo)
		curve.worldSpace[0] >> curveInfo.inputCurve
		
		curveInfo.arcLength >> ctlCog.mpLength

		# ======================== Start MP ========================
		motionPathStart = pm.createNode('motionPath', n='mp_vehicle_start_%s' % curve)
		nodeList.append(motionPathStart)
		curve.local >> motionPathStart.geometryPath
		motionPathStart.fractionMode.set(1)
		motionPathStart.follow.set(1)
		motionPathStart.worldUpType.set(0)
		motionPathStart.worldUpVector.set([0,1,0])
		motionPathStart.frontAxis.set(0)
		motionPathStart.upAxis.set(1)

		offsetAdd.output1D >> motionPathStart.uValue

		# move root to start of curve

		startWorldLoc = pm.createNode('transform', n='loc_world_motionPath_start_%s' % curve)
		nodeList.append(startWorldLoc)
		# constrain
		nodeList.append(pm.parentConstraint(startWorldLoc, start))
		motionPathStart.allCoordinates >> startWorldLoc.translate
		motionPathStart.rotate >> startWorldLoc.rotate



		# ======================== End MP ========================
		motionPathEnd = pm.createNode('motionPath', n='mp_vehicle_end_%s' % curve)
		nodeList.append(motionPathEnd)
		curve.local >> motionPathEnd.geometryPath
		motionPathEnd.fractionMode.set(1)
		motionPathEnd.follow.set(1)
		motionPathEnd.worldUpType.set(0)
		motionPathEnd.worldUpVector.set([0,1,0])
		motionPathEnd.frontAxis.set(0)
		motionPathEnd.upAxis.set(1)

		conversionMult.o >> motionPathEnd.uValue

		endWorldLoc = pm.createNode('transform', n='loc_world_motionPath_end_%s' % curve)
		nodeList.append(endWorldLoc)
		nodeList.append(pm.parentConstraint(endWorldLoc, end))
		motionPathEnd.allCoordinates >> endWorldLoc.translate
		motionPathEnd.rotate >> endWorldLoc.rotate

		# create mid loc
	

		pm.move(root, pm.xform(endWorldLoc, q=1, rp=1, ws=1), rpr=1, ws=1)
		pm.xform(root, ro=pm.xform(endWorldLoc, q=1, ro=1, ws=1), ws=1)

		# steering constraint
		steeringConst = pm.orientConstraint(start, extraSteering, skip=['x','z'])
		nodeList.append(steeringConst)

		for node in nodeList:
			if not pm.hasAttr(node, 'pathRigNode'):
				pm.addAttr(node, ln='pathRigNode', at='message')
			pm.connectAttr(rigNode.nodes, node.pathRigNode, force=1)




def disconnectPath(pathRigNode=None):
	with pm.UndoChunk():
		# get curve
		rigNode = pm.ls('vehicleRigNode')[0]

		if pathRigNode is None:
			if not len(pm.ls(sl=1)):
				raise Exception('Select path curve.')
			if not len(pm.ls(sl=1)[-1].getShapes()):
				raise Exception('Select path curve.')
			curve = pm.ls(sl=1)[-1].getShapes()[0]
			if not pm.objectType(curve, isAType='nurbsCurve'):
				raise Exception('Select path curve.')
			# get pathRigNode
			pathRigNode = curve.pathNode.outputs()
		else:
			pathRigNode = [pathRigNode]


		if len(pathRigNode):
			nodes = pathRigNode[0].nodes.outputs()
			for node in nodes:
				try:
					pm.delete(node)
				except:
					pass

		

		cog = rigNode.ctlCog.inputs()[0]
		extraSteering = rigNode.extraSteering.inputs()[0]
		start = rigNode.start.inputs()[0]
		end = rigNode.end.inputs()[0]
		root = rigNode.root.inputs()[0]

		# reset stuff
		cog.mpLength.set(1)
		extraSteering.rotateY.set(0)
		start.translate.set([0,0,0])
		start.rotate.set([0,0,0])
		end.translate.set([0,0,0])
		end.rotate.set([0,0,0])
		root.translate.set([0,0,0])
		root.rotate.set([0,0,0])
