from pymel.core import *
import utils as rb
reload(rb)
#find the skined matrix index from a joint
#and connnect the inverseMatrix of the anchor joint to the skin cluster
#
#HOW TO USE:
#1.- select the skinned joint first,
#2.- the anchor joint second,
#3.- and the skinned geometry last.
#4.- run the script.


def axmn_inverseMatrixJoints(joints=None, anchors=[], gen=None, skin=None):
	dev = 1
	selection = ls(sl=1)

	anchorsFirst = False
	# Determine whether to use selection, and how.
	# if joints is None and skin is None and anchors is None:
	# 	if gen is None:
	# 		if not len(selection) == 3:
	# 			raise RuntimeError('Selection not valid. Select joint, anchor, and skin, or manually specify.')
	# 		joints = selection[0]
	# 		anchors = selection[1]
	# 		skin = selection[2]
	# 	else:
	# 		if not len(selection) >= 2:
	# 			raise RuntimeError('Selection not valid. Select joints and skin, or manually specify.')
	# 		joints = selection[0:-1]
	# 		skin = selection[-1]
	
	# elif joints is None and anchors is None:
	# 	if gen is None:
	# 		if len(selection):
	# 			joints = selection[0]
	# 			anchors = selection[1]
	# 	else:
	# 		joints = selection
	# elif joints is None:
	# 	if gen is None:
	# 		raise RuntimeError('Inputs not valid. Use joints, or set generations value.')
	# 	else:
	# 		anchorsFirst = True
	# 		for a in anchors:
	# 			j = anchors.getDescendants(generations=gen)
	# 			if dev: print '%s joint: %s' (a, j)
	# 			joints.append(j)


	if not isinstance(joints, list):
		joints = [joints]
	if not isinstance(anchors, list):
		anchors = [anchors]

	# if gen is not None and anchorsFirst is False:
	# 	for j in joints:
	# 		anchor = j.getParent(generations=gen)
	# 		anchors.append(anchor)
	# 		if dev: print '%s anchor: %s' % (j, anchor)

	if dev:
		print 'Skin: %s' % skin
		print 'Joints: (%s)' % len(joints)
		for j in joints: print j
		print '\nAnchors: (%s)' % len(anchors)
		for a in anchors: print a

	if len(joints) != len(anchors):
		print joints
		print anchors
		raise Exception('Length of joints list is not equal to length of anchors list.')

	sc = rb.findSkinCluster(skin)
	if dev: print 'Skincluster: %s' % sc
	if not sc:
		raise RuntimeError('No skinCluster found on %s' % mesh)

	# Matrix connections
	matrixInputList = sc.matrix.inputs()
	if dev: print matrixInputList

	for i, jnt in enumerate(joints):
		prematAttr = None

		if jnt in matrixInputList:
			if dev: print '%s found in list' % jnt
			index = matrixInputList.index(jnt)
			if dev: print index
			prematAttr = sc.bindPreMatrix[index]
			if dev: print prematAttr

	 	if prematAttr is None:
			raise RuntimeError('Pre-matrix attribute for %s not found in skincluster' % jnt)
		if not prematAttr.get():
			raise RuntimeError('Pre-matrix attribute for %s not found in skincluster' % jnt)

		anchors[i].worldInverseMatrix[0] >> prematAttr
		select(anchors[i])
		print('%s connected to %s' % (anchors[i].worldInverseMatrix[0], prematAttr))


#execute script
#axmn_inverseMatrixJoints()