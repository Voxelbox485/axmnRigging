from pymel.core import *
# import maya.cmds as cmd
# import maya
def resetSkinClusterOld( skinCluster ):
	'''
	splats the current pose of the skeleton into the skinCluster - ie whatever
	the current pose is becomes the bindpose
	'''
	nInf = len( cmd.listConnections( '%s.matrix' % skinCluster, destination=False ) )
	for n in range( nInf ):
		try:
			slotNJoint = cmd.listConnections( '%s.matrix[ %d ]' % (skinCluster, n), destination=False )[ 0 ]
		except IndexError: continue

		matrixAsStr = ' '.join( map( str, cmd.getAttr( '%s.worldInverseMatrix' % slotNJoint ) ) )
		melStr = 'setAttr -type "matrix" %s.bindPreMatrix[ %d ] %s' % (skinCluster, n, matrixAsStr)
		maya.mel.eval( melStr )

		#reset the stored pose in any dagposes that are conn
		for dPose in cmd.listConnections( skinCluster, d=False, type='dagPose' ) or []:
			cmd.dagPose( slotNJoint, reset=True, n=dPose )


