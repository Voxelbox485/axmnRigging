from pymel.core import *
import pymel.core.datatypes as dt
import colorOverride as col
import utils
reload(utils)



# Load important plugins	
loadPlugin( 'matrixNodes.mll', qt=True)
loadPlugin( 'quatNodes.mll', qt=True)

'''Fitrig class
	pickle into node?
	shaper
	attribute ui

Scaling setup

redo fitrig class

fix up axis
parallelize
fitshape mirroring
fix boneIndic
skip orient option
per-fitrig distance scaling
fix spaceswitch
shaper?

anim commands window
footroll asset is taking over leg

lips:
no neutralize? or just neutralize all

space switches
shoulders
chest
head
tail
spine/neck tangent neutralize blend (no neutral)


wings can be curve offset with linked parameters
combine chain rigs
tangent defaults getting mirrored (ruining fk)



-iksetup pv is rolling back when arms swing back (lined up with shoulder in y) esp when set to 'start'
-mirrored pv Up Axis causes flipping
-rename knee follow
-move percentage attribute and set default values


-Untangle evaluation clusters
-animation tools
-Scaling, volume
	scale modifier stack
-untangled matrix?
-test knee fix
-top jnt
-knee pinning?
-orient controls
-unlock fit pv up/down
-footroll
-bind set global name footroll
-topJnt
-	pointconst to jnt, ori to par
-stretch neutralizing
-footroll
-Tangent handle mult values
-Save transform info into other attributes on rigGroup
-Put fitNode so that it's the first shape in the list
-Can replace the step() inputs w/ a world ls at start and end and compare difference
-control upperarm bezier tangent ori with ik input? fkik switch?
-ramp-aided parameter mapping
-Turning off bezier doFk breaks rigEntrance/Exit


BUILDRIG TABLE OF CONTENTS

init
	step

	createCtrl
	globalVisSDK

naming
	constructNaming
	formatUnnammedList
	clashFix
	renameAll

coloring
	recolor

rebuildRig

deleteRig
selectList

socket
tagNode

padFormat

buildFkSetup
buildIkSetup
buildOffsetSetup
buildBezierSetup
buildParametricCurveRigSetup

finalize
	constructDeleteList
	constructBindList
	attachRigNode
	freezeNodes
	assetize

constructSelectionList


'''


class rig:

	freezeColor = [0,0,0]
	# freezeColor = [0.570, 0.668, 0.668]
	# freezeColor = [0.534, 1.000, 0.699]
	publishColor = [0,0,0]
	ikJointsColor = [1,1,.267]
	# fkJointsColor = [0,1,.165]
	switchJointsColor = [0,0,.165]
	rigNodeColor = [1.000, 0.698, 0.150]

	fkColors=[
	[0.700, 1.000, 0.410], # M
	[0.150, 0.800, 1.000], # L
	[0.950, 0.140, 0.460], # R
	[0.700, 1.000, 0.410], # M
	]
	ikColors=[
	[1.000, 1.000, 0.600], # M
	[0.686, 0.664, 1.300], # L
	[1.300, 0.481, 0.411], # R
	[1.000, 1.000, 0.600], # M
	]

	colorsFK = [
		[0.700, 1.000, 0.410], # M
		[0.150, 0.800, 1.000], # L
		[0.950, 0.140, 0.460], # R
		]
	colorsIK = [
		[1.000, 0.655, 0.225], # M
		[0.686, 0.664, 1.300], # L
		[1.300, 0.481, 0.411], # R
		]
	collectStrayNodes = False


	import maya.mel
	gMainProgressBar = 	uitypes.ProgressBar(melGlobals['gMainProgressBar'])
	gNodeEditor = 		mel.eval('$temp = `getCurrentNodeEditor`')

	useProgressBar = False
	doAssetize = False

	sideStr = ['_M', '_L', '_R', '']

	def __init__(self, fitNode, dev=True):

		self.dev = dev
		
		waitCursor( state=True )

		if self.dev:
			if self.collectStrayNodes:
				self.worldNodesBoolStart = ls()
		
		self.lockNodeEditor()

		if self.useProgressBar:
			if self.gMainProgressBar.getIsMainProgressBar():
				self.gMainProgressBar.setIsInterruptable()
				self.gMainProgressBar.beginProgress()

		'''Delete old rig'''
		if hasAttr(fitNode, 'rigNode'):
			# rigGroup = fitNode.rigNode.get() # Not searching shapes...
			rigGroup = fitNode.rigNode.get() # Not searching shapes...
			if rigGroup:
				print 'Attempting to delete rigGroup: %s' % rigGroup
				# try:
				deleteRig(rigGroup)
				# except:
				# 	pass

		'''Create basic rig node network '''
		if self.dev: print 'Basic Rig Setup...'
		self.sectionTag = 'base'

		# FitNode
		self.fitNode = fitNode
		if self.dev: print 'Fit Node: %s' % self.fitNode.nodeName()

		# Gather Skelenode data
		if hasAttr(self.fitNode, 'skeleNode'):
			if self.fitNode.skeleNode.get():
				self.skeleNode = self.fitNode.skeleNode.get()
				self.globalControl = self.skeleNode.globalMove.get()
				self.rigsGroup = self.skeleNode.rigGroup.get()
				self.fitRigsGroup = self.skeleNode.fitRigsGroup.get()
			else:
				self.skeleNode = None
				self.globalcontrol = None
				self.rigsGroup = None
		# self.socketGroup = self.skeleNode.socketGroup.get()
		# self.outputGroup = self.skeleNode.outputGroup.get()
		
		if self.dev: print 'SkeleNode: %s' % self.skeleNode
		if self.dev: print 'Rigs Group: %s' % self.rigsGroup
		# if self.dev: print 'Socket Group: %s' % self.socketGroup
		# if self.dev: print 'Output Group: %s' % self.outputGroup
		
		# Error check
		# Add naming check
		if not isinstance(self.fitNode, PyNode):
			if isinstance(self.fitNode, str):
				self.fitNode = ls(fitNode)[0]
			else:
				raise Exception('FitNode input is of wrong type: %s' % fitNode)
		if not hasAttr(self.fitNode, 'rigType'):
			raise Exception('Attribute missing: %s.rigType; Verify inputs' % self.fitNode)

		self.publishList = []
		self.deleteList = []
		self.freezeList = []
		self.ctrlsList = []
		self.clashList = []
		self.unnammedList = []
		self.bindList = []
		self.spaceSwitches = {}

		self.tangledMatrixConstraints = []
		self.untangledMatrixConstraints = []
		self.tangledAimConstraints = []
		self.untangledAimConstraints = []

		self.hiddenInOutlinerList = []
		# self.socketList = []

		# self.controllerTags = not self.dev # Adds 'controller' node tag object (Maya 2017+)
		self.controllerTags = True # Adds 'controller' node tag object (Maya 2017+)
		self.ctrlTags = []
		self.nodeCount = 0

		self.side = self.fitNode.side.get()
		
		# ============================= Naming ============================= 
		namesDict = {
		'rigNode': 	{'desc': self.fitNode.globalName.get(), 'side' :self.fitNode.side.get(), 'warble': 'rigNode', 	'other': []},
		'selNode': 	{'desc': self.fitNode.globalName.get(), 'side' :self.fitNode.side.get(), 'warble': 'selNode', 	'other': []},
		'rigGroup': {'desc': self.fitNode.globalName.get(), 'side' :self.fitNode.side.get(), 'warble': 'rigGroup',	'other': []}
		}
		self.names = utils.constructNames(namesDict)
		# names = {}

		# ============================= Selection Node ============================= 
		self.selNode = createNode('network', n=self.names.get('selNode', 'rnm_selNode'))
		self.publishList.append(self.selNode)
		self.step(self.selNode, 'selNode')
		# Attributes
		addAttr(self.selNode, k=1, h=0, dt='string', category='verification', ln='selNodeVer')
		addAttr(self.selNode, k=0, h=0, at='message', multi=1, indexMatters=False, category='selection', ln='ctrlsList')
		# addAttr(self.selNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='socketList')
		addAttr(self.selNode, k=0, h=0, at='message', multi=1, indexMatters=False, category='selection', ln='bindList')
		addAttr(self.selNode, k=0, h=0, at='message', ln='rigNode')


		# ============================= Rig Group =============================
		self.rigGroup = createNode('transform', n=self.names.get('rigGroup', 'rnm_rigGroup'), p=self.rigsGroup)
		if self.dev: print 'RigGroup:'
		self.step(self.rigGroup, 'rigGroup', freeze=False)
		# if self.dev: print 'RigGroup: %s' % self.rigGroup\


		# ============================= Rig Node ============================= 
		if not self.doAssetize:
			self.rigNode = createNode('locator', n=self.names.get('rigNode', 'rnm_rigNode'), p=self.rigGroup)
			self.rigNode.hide()
			hideAttrs = [
			self.rigNode.localPositionX,
			self.rigNode.localPositionY,
			self.rigNode.localPositionZ,
			self.rigNode.localScaleX,
			self.rigNode.localScaleY,
			self.rigNode.localScaleZ,
			]
		else:
			self.rigNode = createNode('transform', n=self.names.get('rigNode', 'rnm_rigNode'), p=self.rigGroup)
			hideAttrs = [
			self.rigNode.translateX,
			self.rigNode.translateY,
			self.rigNode.translateZ,
			self.rigNode.rotateX,
			self.rigNode.rotateY,
			self.rigNode.rotateZ,
			self.rigNode.scaleX,
			self.rigNode.scaleY,
			self.rigNode.scaleZ,
			self.rigNode.visibility
			]
			self.publishList.append(self.rigNode)
		for attr in hideAttrs:
			attr.set(l=1, k=0, cb=0)
		if self.dev: print 'RigNode: %s' % self.rigNode
		

		# Verification that this is a rigNode
		addAttr(self.rigNode, ln='rigNodeVer', k=0)
		# Connect fitNode to rigNode
		if not hasAttr(self.fitNode, 'rigNode'):
			addAttr(self.fitNode, at='message', ln='rigNode', k=1)

		addAttr(self.rigNode, at='message', ln='fitNode', k=1)

		self.fitNode.rigNode.connect(self.rigNode.fitNode)
		# if self.dev: print '%s.rigNode >> %s.fitNode' % (self.fitNode, self.rigNode)

		# Connect rigNode to skeleNode
		if self.skeleNode:
			if not hasAttr(self.skeleNode, 'rigNodes'):
				addAttr(self.skeleNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='rigNodes')
			self.rigNode.message.connect(self.skeleNode.rigNodes, na=1)
			# if self.dev: print '%s.message >> %s.rigNodes' % (self.rigNode, self.skeleNode)

		# print self.side
		# print self.colorsIK[self.side]
		# col.setOutlinerRGB(self.rigGroup, self.colorsIK[self.side])

		# Attributes
		addAttr(self.rigNode, k=1, h=0, dt='string', ln='rigType')
		addAttr(self.rigNode, k=1, h=0, at='message', ln='heirarchy')
		addAttr(self.rigNode, k=0, h=1, at='message', ln='selNode')
		self.rigNode.selNode.connect(self.selNode.rigNode)
		addAttr(self.rigNode, k=0, h=1, at='message', ln='rigGroup')
		self.rigGroup.message.connect(self.rigNode.rigGroup)
		# addAttr(self.rigNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='ctrlsList')
		addAttr(self.rigNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='socketList')
		# addAttr(self.rigNode, k=0, h=1, at='message', multi=1, indexMatters=False, category='selection', ln='bindList')


		addAttr(self.rigNode, ln='allVis', min=0, max=1, at='short', dv=1, keyable=1)
		addAttr(self.rigNode, ln='debugVis', min=0, max=1, at='short', dv=0, keyable=0)
		self.debugVis = self.rigNode.debugVis
		
		setAttr(self.rigNode.allVis, k=0, cb=1)
		setAttr(self.rigNode.debugVis, k=0, cb=1)
		if self.dev:
			self.rigNode.debugVis.set(1)


		addAttr(self.rigNode, k=1, h=0, dt='string', category='naming', ln='globalName')
		addAttr(self.rigNode, k=1, h=0, dt='string', category='naming', multi=1, ln='subName')

		# Set names to rigNode (Easier reference)
		self.rigNode.globalName.set(self.fitNode.globalName.get())
		for i, subN in enumerate(listAttr(self.fitNode, st='subName*')):
			self.rigNode.subName[i].set(self.fitNode.attr(subN).get())


		if self.dev: print 'Basic rigNode complete.'

	def finalize(self, skipAssetize=False):
		if self.dev: print '# finalize'

		if self.dev: print '\n'

		# Settings Node
		if not skipAssetize:
			if self.doAssetize:
					self.assetize(publishFitNode=True)
			else:
				self.attachRigNode()

		# RigNode Set
		if not objExists('rigNodeSet'):
			rigNodeSet = sets([self.rigNode], n='rigNodeSet')
		else:
			rigNodeSet = sets('rigNodeSet', e=True, forceElement=self.rigNode)

		# End progress bar (always end if )
		if self.useProgressBar:
			self.gMainProgressBar.endProgress()
		
		# Stray Nodes
		if self.dev:
			if self.collectStrayNodes:
				self.worldNodesBoolEnd = ls()
				self.strayNodes = []
				for node in self.worldNodesBoolEnd:
					if node not in self.worldNodesBoolStart:
						if node not in self.deleteList:
							self.strayNodes.append(node)

				if self.dev: 
					print 'Stray Nodes: %s' % len(self.strayNodes)
					# for node in self.strayNodes:
					# 	print node.nodeName()
					if not objExists('straySet'):
						sets(self.strayNodes, n='straySet')
					else:
						sets('straySet', e=True, forceElement=self.strayNodes)


		# Control Selection List
		try:
			self.constructSelectionList(selectionName='ctrlsList', selectionList=self.ctrlsList)
		except:
			pass

		# 
		self.constructDeleteList()
		self.constructBindList()
		self.freezeNodes()
		self.untangleConstraints()


		# col.setOutlinerRGB(self.rigGroup, self.colorsIK[self.side])

		for node in self.hiddenInOutlinerList:
			if hasAttr(node, 'hiddenInOutliner'):
				node.hiddenInOutliner.set(1)

		if self.dev: print '\nNodes Counted: %s' % self.nodeCount


		waitCursor( state=False )
		self.unlockNodeEditor()
	
	def matrixConstraint(self, target, constrained, offset=True, t=True, r=False, s=False, force=True, preserve=True, untangling=True):
		'''
		Low overhead constraint
		Look into right handed matrix to left conversion
		'''

		# If passed a list of three bools for any of the 3 inputs, seperate into xyz


		constrainAttrs = [] # List of all 9 bools (for t,r,s)

		outAttrs = ['otx', 'oty', 'otz', 'orx', 'ory', 'orz', 'osx', 'osy', 'osz']
		inAttrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']

		if hasAttr(constrained,'constraintNodes'):
			if len(constrained.constraintNodes.get()):

				if not preserve:
					try:
						removeMatrixConstraint(constrained)
					except:
						pass
		
		for i, channel in enumerate([t, r, s]):
			if isinstance(channel, list) or isinstance(channel, tuple):
				if not len(channel) == 3:
					raise Exception( '3 Inputs required for tuple to be considered valid: %s (%s inputs found)' % (['Translate', 'Rotate', 'Scale'][i], len(channel)) )
				# If t=(True, False, True), append (True, False, True) to bool list
				constrainAttrs.extend(channel)
			else:
				# If t=True, append (True, True, True) to boolList
				constrainAttrs.extend([channel, channel, channel])

		doJointOrient=False
		if objectType(target, isType='joint') and objectType(constrained, isType='joint'):
			doJointOrient=True

		nodeList = []

		multMatrixName = '%s_matrixConstraint_multMatrix#' % (constrained.nodeName())
		decomposeMatrixName = '%s_matrixConstraint_decmpMatrix#' % (constrained.nodeName())
		eulerToQuatName = '%s_matrixConstraint_eulToQuat#' % (constrained.nodeName())
		quatInvertName = '%s_matrixConstraint_quatInv#' % (constrained.nodeName())
		quatProdName = '%s_matrixConstraint_quatProd#' % (constrained.nodeName())
		quatToEulerName = '%s_matrixConstraint_quatToEul#' % (constrained.nodeName())

		mm = createNode('multMatrix', n=multMatrixName)
		self.step(mm, 'mm')
		nodeList.append(mm)

		i=0
		if offset:
			offsetMatrix = createNode('multMatrix', n='localOffsetMatrixTemp')

			constrained.worldMatrix[0] >> offsetMatrix.matrixIn[0]
			target.worldInverseMatrix[0] >> offsetMatrix.matrixIn[1]
			# print offsetMatrix.matrixSum.get()
			mm.matrixIn[i].set(offsetMatrix.matrixSum.get())
			delete(offsetMatrix)
			i=1

		target.worldMatrix[0] >> mm.matrixIn[i]
		i=i+1
		
		constrained.parentInverseMatrix[0] >> mm.matrixIn[i]
		dcmp = createNode('decomposeMatrix', n=decomposeMatrixName)
		self.step(dcmp, 'dcmp')
		nodeList.append(dcmp)
		mm.matrixSum >> dcmp.inputMatrix

		# if len(constrainAttrs[3:6]) != 3:
		# 	raise Exception(inAttrs[3:6])

		if doJointOrient and any(constrainAttrs[3:6]):
			eul = createNode('eulerToQuat', n=eulerToQuatName)
			self.step(eul, 'eul')
			nodeList.append(eul)
			constrained.jointOrient >> eul.inputRotate

			quatInv = createNode('quatInvert', n=quatInvertName)
			self.step(quatInv, 'quatInv')
			nodeList.append(quatInv)
			eul.outputQuat >> quatInv.inputQuat

			quatProd = createNode('quatProd', n=quatProdName)
			self.step(quatProd, 'quatProd')
			nodeList.append(quatProd)
			dcmp.outputQuat >> quatProd.input1Quat
			quatInv.outputQuat >> quatProd.input2Quat

			quatToEuler = createNode('quatToEuler', n=quatToEulerName)
			self.step(quatToEuler, 'quatToEuler')
			nodeList.append(quatToEuler)
			quatProd.outputQuat >> quatToEuler.inputQuat


		for i, constrainAttribute in enumerate(constrainAttrs): # if t
			if constrainAttribute:
				# Connect different input if joint orienations
				if i >= 3 and i <= 5 and doJointOrient:
					quatToEuler.attr(outAttrs[i]).connect(constrained.attr(inAttrs[i]), f=force)
				else:
					dcmp.attr(outAttrs[i]).connect(constrained.attr(inAttrs[i]), f=force)


		# if t:
		# 	dcmp.outputTranslate >> constrained.translate
		# if r:
		# 	if doJointOrient:
		# 		quatToEuler.outputRotate >> constrained.rotate
		# 	else:
		# 		dcmp.outputRotate >> constrained.rotate
		# if s:
		# 	dcmp.outputScale >> constrained.scale
		
		if not hasAttr(constrained,'constraintNodes'):
			addAttr(constrained, ln='constraintNodes', at='message', multi=1, k=0, h=1, indexMatters=False)
		for node in nodeList:
			node.message.connect(constrained.constraintNodes, na=True)
		

		if untangling:
			self.tangledMatrixConstraints.append(constrained)

		return nodeList


	def untangleConstraints(self):
		'''Convert all constraints specified into acyclic constraints to reduce overhead.  For example, replace constrained's parent invert matrix input with constrained's PARENT's world inverse matrix '''

		# Custom matrix constraint conversion
		for constrained in self.tangledMatrixConstraints:
			if self.dev: print constrained

			attrOuts = listConnections(constrained.parentInverseMatrix, t='multMatrix', p=True, d=True, s=False)
			for attrOut in attrOuts:
				# if self.dev: print attrOut
				constrained.parentInverseMatrix.disconnect(attrOut)
				constrained.getParent().worldInverseMatrix[0].connect(attrOut)

			self.tangledMatrixConstraints.remove(constrained)
			self.untangledMatrixConstraints.append(constrained)



		# Aim constraint conversion
		for aimConst in self.tangledAimConstraints:

			skip=False
			constrained = aimConst.constraintRotateX.outputs()
			print constrained
			if len(constrained) > 1:
				warning('More than one constrained output on aim constraint %s' % aimConst)
				constrained = constrained[-1]
			if len(constrained) == 0:
				warning('Constraint has no output: %s. Skipping...' % aimConst)
				skip=True

			constrained = constrained[0]
			constraintParent = constrained.getParent()
			print constraintParent
			if not constraintParent:
				warning('Constraint has no parent: %s. Skipping...' % aimConst)
				skip=True

			constraintParent.worldInverseMatrix.connect(aimConst.constraintParentInverseMatrix, f=1)
			constrained.rotateOrder.disconnect(aimConst.constraintRotateOrder)
			constrained.rotatePivot.disconnect(aimConst.constraintRotatePivot)
			constrained.rotatePivotTranslate.disconnect(aimConst.constraintRotateTranslate)

			attributes = [constrained.t, constrained.tx, constrained.ty, constrained.tz]
			if not any(attr.isDestination() for attr in attributes):
				constrained.translate.disconnect(aimConst.constraintTranslate)

			# self.tangledAimConstraints.remove(aimConst)
			# self.untangledAimConstraints.append(aimConst)
			
			# if isinstance(constraint, nt.ParentConstraint):
			# 	pass
				# attrOuts = listConnections(constrained.parentInverseMatrix, t='multMatrix', p=True, d=True, s=False)
				# for attrOut in attrOuts:
				# 	if self.dev: print attrOut
				# 	constrained.parentInverseMatrix.disconnect(attrOut)
				# 	constrained.getParent().worldInverseMatrix[0].connect(attrOut)
			

	def setController(self, ctrl, ctrlParent):
		if self.dev: print '# setController'
		if self.controllerTags == True:
			if versions.current() > versions.v2017:
				# tag control
				if not isinstance(ctrl, nt.Transform):
					raise Exception('Node is not a transform and cannot be a controller: %s' % ctrl)
				controller(ctrl)
				ctrlTag = ls(controller(ctrl, q=1)[0])[0] # Controller command returns a string because it's dumb.
				if not ctrlTag in self.ctrlTags:
					self.ctrlTags.append(ctrlTag)
				self.step(ctrlTag, 'ctrlTag')
				

				ctrlTag.visibilityMode.set(1)
				if len(ctrlTag.children.get()) > 1:
					ctrlTag.cycleWalkSibling.set(1)
				
				# This breaks when keyed for some reason
				if ctrlParent:
					if not isinstance(ctrlParent, nt.Transform):
						try:
							raise Exception('Controller\'s parent is not a transform: %s, %s' % ctrl , ctrlParent)
						except:
							raise Exception('Controller\'s parent is not a transform: %s' % ctrl)

					# Find controller node associated with control parent
					parentCtrlTag = None
					controller(ctrlParent)
					parentCtrlTag = ls(controller(ctrlParent, q=1)[0])[0]
					if not parentCtrlTag in self.deleteList:
						self.deleteList.append(parentCtrlTag)
				
					if not parentCtrlTag in self.ctrlTags:
						self.ctrlTags.append(parentCtrlTag)
					
					ctrlTag.parentprepopulate.set(1)

					# connect ctrl to parent ctrlTag as children (sort of a hacky 'next available' because indexMatters is on)
					i=0
					while True:
						if not len(parentCtrlTag.children[i].inputs()):
							ctrlTag.parent.connect(parentCtrlTag.children[i])
							break
						i = i+1
						# just in case
						if i == 1000:
							raise Exception('Code cycle detected')

					parentCtrlTag.prepopulate.set(1)
				else:
					ctrlTag.parentprepopulate.set(0)
					
				
	def lockNodeEditor(self):
		if self.dev: print '# lockNodeEditor'
		# TODO: Update icon?
		try:
			nodeEditor(self.gNodeEditor, e=1, addNewNodes=False)
		except:
			pass

	
	def unlockNodeEditor(self):
		if self.dev: print '# unlockNodeEditor'
		try:
			nodeEditor(self.gNodeEditor, e=1, addNewNodes=True)
		except:
			pass

		
	def assetize(self, publishFitNode=False):
		if self.dev: print '# assetize'
		
		# Apply icon to asset node
		iconDict = {
			'chain': 			'kinJoint.png',
			'aimIK': 			'aimConstraint.png',
			'threePointIK': 	'kinHandle.png',
			'hand': 			'kinHandle.png',
			'foot': 			'kinHandle.png',
			'bezier': 			'tangentConstraint.png',
		}
		icon = iconDict.get(self.rigNode.rigType.get(), None)

		# self.deleteList = []
		# self.ctrlsList = []

		if not hasAttr(self.rigNode, 'asset'):
			addAttr(self.rigNode, ln='asset', at='message', k=0)

		# Create Asset
		self.naming()
		self.names = utils.constructNames(self.namesDict)

		assetName = self.names.get('asset', 'rnm_asset')
		self.asset = container(addNode=self.deleteList, n=assetName, includeHierarchyBelow=True)
		container(self.asset, e=1, addNode=[self.rigGroup], includeHierarchyBelow=True)
		self.asset.message.connect(self.rigNode.asset)
		
		# Publish parent/child
		container(self.asset, e=1, publishAsParent=[self.rigGroup, 'parent'])
		container(self.asset, e=1, publishAsChild=[self.rigGroup, 'child'])

		# Publish controls
		# Use a publishList, use tags, and add pertinent groups to it
		warnList = []
		for ctrl in self.publishList:
			try:
				containerPublish(self.asset, publishNode = [ctrl.nodeName(), ''])
				containerPublish(self.asset, bindNode=[ctrl.nodeName(), ctrl])
			except:
				warnList.append(ctrl)

		containerPublish(self.asset, publishNode = ['rigNode', ''])
		containerPublish(self.asset, bindNode =		['rigNode', self.rigNode])

		unpublished = []
		# Either publish fitNode Attributes, or publish every instance of fitNode (Both kind of suck.)
		if publishFitNode:
			publishNodes = [self.rigNode]
			# attributes = listAttr(self.rigNode, cb=1) + listAttr(self.rigNode, k=1)
			for node in publishNodes:
				udAttribute = listAttr(node, userDefined=True)
				attributes = listAttr(node, ct='publish')
				for attri in udAttribute:
					if not attri in attributes:
						unpublished.append(attri)
				blackList = ['rigNode']
				for attribute in attributes:

					if not attribute in blackList:
						container(self.asset, e=1, publishName='%s' % node.attr(attribute).shortName())
						container(self.asset, e=1, bindAttr=[node.attr(attribute), '%s' % node.attr(attribute).shortName()])
		else:
			for i, rigNodeInstance in enumerate(self.rigNode.getOtherInstances()):
				containerPublish(self.asset, publishNode = ['rigNode%s' % i, ''])
				containerPublish(self.asset, bindNode =		['rigNode%s' % i, rigNodeInstance])

		self.asset.blackBox.set(1)
		if icon:
			self.asset.iconName.set(icon)

		if unpublished:
			print '\nUnpublished Attribtues:'
			for attr in unpublished:
				print attr

		if warnList:
			warning('One or more objects could not be published, probably because of clashing asset names: %s' % warnList)


	def formatUnnammedList(self):
		if self.dev: print '# formatUnnammedList'
		'''Takes any unnammed objects detected and formats them into an easy to copy dictionary
		'''
		# Tab formatting
		characters = []
		for node in self.unnammedList:
			characterLen = len(node.tag.get())
			characters.append(characterLen)
		characters.sort()
		# charactersSorted = sort(characters)

		tagList = []
		for node in self.unnammedList:
			tagList.append(node.tag.get())
			count = tagList.count(node.tag.get())
			if count>1:
				neutralize = '#%s ' % count # If more than one named object, notify, but comment out
			else:
				neutralize = ''

			remainingCharacters = ( characters[-1] - len(node.tag.get()) )
			spaces = (" " * remainingCharacters)
			print('%s\'%s\':%s 	{ \'desc\': globalName,\t\'side\':\tside,\t\t\'warble\': None,\t\t\'other\': [\'%s\', \'%s\'],\t\t\t\'type\': \'%s\' },' % (neutralize, node.tag.get(), spaces, node.tag.get(), node.sectionTag.get(), objectType(node)))


	def step(self, node, nodeTag, freeze=True):
		# Iterate for each node created
		
		# Print statement
		if self.dev: print '\t%s' % node

		# Clashlist
		if '|' in node.shortName():
			self.clashList.append(node)

		# Unnammed list
		if 'rnm_' in node.nodeName():
			self.unnammedList.append(node)
		
		# Delete list
		self.deleteList.append(node)
		
		# Lock and hide attributes
		if freeze:
			self.freezeList.append(node)

		# Tag node in case it needs to be found (usually tagged with the variable name)
		self.tagNode(node, nodeTag)

		# Node count
		self.nodeCount = self.nodeCount+1

		# Tic progress bar if progress bar enabled
		if self.useProgressBar:
			if self.gMainProgressBar.getIsCancelled():
				self.gMainProgressBar.endProgress()

				raise Exception('User Cancelled.')
				# Undo?

			self.gMainProgressBar.step()


	def naming(self, *args, **kwargs):
		if self.dev: print '# naming'
		''' Default naming string is empty. Prevents build errors? Could be useless '''
		self.namesDict={}

	# User Operations


	def deleteRig(self):
		'''Deletes rig based on 'deleteList' node connections
		TODO
		Fix so that delete list points to network node
		'''
		if self.dev: print '# deleteRig'
		typ = self.rigNode.rigType.get()

		if self.doAssetize:
			print self.rigNode
			delete(self.rigNode)
		else:
			delete(self.selNode.deleteList.get())
			delete(self.rigGroup)

			print '\n Post delete node gathering'
			self.worldNodesDelete = ls()
			for node in self.worldNodesDelete:
				if node in self.worldNodesBool:
					print node

		print '%s Rig Deleted.' % (typ)


	def selectList(self, attribute, add=False):
		if self.dev: print '# selectList'
		'''Creates node connections for easy selection
		TODO
		Fix so that selection list points to network node
		'''
		selection = ls(sl=1)
		if hasAttr(self.selNode, attribute):
			try:
				select(self.selNode.attr(attribute).get(), add=add)
			except:
				select(selection)
		else:
			raise Exception('Attribute not found.')


	def createControlHeirarchy(self, matrix=None, mirror=False, mirrorStart=False, transformSnap=None, doBuf=True, doConst=True, doExtra=True, orientSnap=None, par=None, name=None, pivot=True, shape=None, rotateOrder='xyz', ctrlSets='controlSet', register=True, globalVis=True, jntBuf=False, selectionPriority=0, t=True, r=True, s=True, ctrlParent=None, doSubCtrl=False, outlinerColor=None):
		if self.dev: print '# createControlHeirarchy'
		'''With some inputs, create a heirarchy of transform nodes (buf --> const --> extra --> control) and set up attributes accordingly.
		matrix = positional matrix input
		transformSnap = derive matrix from transform input
		parent = where to parent buffer group
		pivot = whether to enable rotate pivot controls
		rotateOrder = set rotate order and enable attribute in channelBox.  Set to False to leave hidden.
		ctrlSet = add control node to one or more selection sets
		globalVis = whether to connect global vis set driven key to visiblity of control

		TODO:
		-Name dict setup
		-Custom pickwalk setup
		-Delocalize from rig into separate traversable heirarchy?
		-Const can just be buf with default values
		-Extra can just be gone mebbe
		'''
		
		# Error Check
		last = par
		heirarchy = []
		cFreezeList = []
		# BUF
		if doBuf:
			if jntBuf:
				buf = 		createNode('joint', n='%s_BUF' 			% name, p=last)
				buf.drawStyle.set(2) # None
				par.scale.connect(buf.inverseScale)
				buf.segmentScaleCompensate.set(0, k=1)
			else:
				buf = 		createNode('transform', n='%s_BUF' 		% name, p=last)

			self.step(buf, 'buf')
			last = buf
			heirarchy.append(buf)

	
		# CONST
		if doConst:
			const = 		createNode('transform', n='%s_CONST' 	% name, p=last)
			self.step(const, 'const', freeze=False)
			const.v.set(l=1, k=0)
			last = const
			heirarchy.append(const)


		# MIRROR
		if mirrorStart:
			mir =		createNode('transform', n='%s_MIR'		% name, p=last)
			self.step(mir, 'mir')
			last = mir
			heirarchy.append(mir)
			mir.scale.set(1,1,-1)
			mir.rotate.set(0, 0, 180)

		else:
			heirarchy[0].scale.set(1,1,1)

		# EXTRA
		if doExtra:
			extra = 		createNode('transform', n='%s_EXTRA' 	% name, p=last)
			self.step(extra, 'extra', freeze=False)
			last = extra
			extra.v.set(l=1, k=0)
			heirarchy.append(extra)

			col.setOutlinerRGB(extra, (0.5,0.5,0.5))
			
			cFreezeList.append(extra)


		# CTRL
		if selectionPriority == 1:
			ctrl = 			createNode('joint', n='%s_CTRL' 	% name, p=last)
			ctrl.radius.set(0, k=0, l=1) # Hide radius
		else:
			ctrl = 			createNode('transform', n='%s_CTRL' 	% name, p=last)

			if selectionPriority == 2:
				ctrl.displayHandle.set(1)

		# if not outlinerColor is None:
		# 	col.setOutlinerRGB(ctrl, outlinerColor)

		self.step(ctrl, 'ctrl', freeze=False)
		heirarchy.append(ctrl)
		cFreezeList.append(ctrl)

		if s:
			ctrl.minScaleLimit.set(0.01, 0.01, 0.01)
			ctrl.minScaleLimitEnable.set(True, True, True)

		if doSubCtrl:
			subCtrl = 			createNode('transform', n='%s_SUBCTRL' 	% name, p=ctrl)

		# Meta Attributes


		if doBuf:
			addAttr(ctrl, k=0, h=1, at='message', ln='bufferGroup', sn='buf')
			buf.message >> ctrl.buf

		if doConst:
			addAttr(ctrl, k=0, h=1, at='message', ln='constraintGroup', sn='const')
			const.message >> ctrl.const
			if not doBuf:
				addAttr(ctrl, k=0, h=1, at='message', ln='bufferGroup', sn='buf')
				const.message >> ctrl.buf

		if mirrorStart:
			addAttr(ctrl, k=0, h=1, at='message', ln='mirrorGroup', sn='mirror')
			mir.message >> ctrl.mirror

		if doExtra:
			addAttr(ctrl, k=0, h=1, at='message', ln='extraGroup', sn='extra')
			extra.message >> ctrl.extra

		if doSubCtrl:
			addAttr(ctrl, k=0, h=1, at='message', ln='subCtrl', sn='sub')
			subCtrl.message >> ctrl.sub

		# Snapping
		if transformSnap is not None:
			delete(parentConstraint(transformSnap, heirarchy[0]))
			# matrix = xform(transformSnap, q=1, ws=1, matrix=1)

		if matrix is not None:
			xform(heirarchy[0], ws=True, matrix=matrix)
			# buf.s.set(1,1,1)

		if orientSnap is not None:
			xform(heirarchy[0], ws=True, ro=xform(orientSnap, q=1, ws=1, ro=1))


		# Attach a shape if shape specified
		if shape:
			if len(shape.getShapes()):
				# TODO
				# Check to see whether specified node is a shape or transform

				shapeTransform = duplicate(shape, n='temp')[0]
				# unlock if neccessary
				lhAttributes = [ shapeTransform.tx, shapeTransform.ty, shapeTransform.tz, shapeTransform.rx, shapeTransform.ry, shapeTransform.rz, shapeTransform.sx, shapeTransform.sy, shapeTransform.sz, shapeTransform.v ]
				for attribute in lhAttributes:
					if attribute.isLocked():
						attribute.set(l=0)

				# Delete any children of duplicated node if they're not shapes
				children = shapeTransform.getChildren()
				shapes = shapeTransform.getShapes()

				for child in children:
					if child not in shapes:
						delete(child)

				# If there's more than one shape, return only the first found nurbsCurve, or first found surface, or first poly, or first loc.
				if len(shapes) > 1:
					shape = None
					
					for s in shapes:
						print s.nodeType()

					typeList = [
					'nurbsCurve',
					'surface',
					'poly',
					'locator'
					]

					# Returns the first shape found in a prioritized type list
					for typ in typeList:
						if not shape:
							for s in shapes:
								if s.nodeType() == typ:
									shape = s
									break

					for s in shapes:
						if not s == shape:
							shapes.remove(s)

				# Parent shape to ctrl and delete old transform
				parent(shapeTransform, ctrl)
				makeIdentity(shapeTransform, apply=1, t=1, r=1, s=1, n=0, pn=1)
				shapeTransform.rename('%s' % ctrl.nodeName())
				parent(shapes[0], ctrl, r=1, s=1)
				self.step(shapes[0], 'ctrlShape')
				delete(shapeTransform)
				# shapes[0].rename('%sShape' transform)
			

		# Global Control SDK Vis
		if globalVis:
			self.globalVisSDK(ctrl)

			ctrl.overrideEnabled.set(1)
			ctrl.overrideColor.set(1)

		if pivot and r:
			# Global Control Pivots Vis
			# if not hasAttr(self.globalControl, 'showPivotOffsets'):
			# 	addAttr(self.globalControl, ln='showPivotOffsets', at='short', min=0, max=1, dv=1, k=1)
			# 	self.globalControl.showPivotOffsets.set(k=0, cb=1)

			# Display Rotate Pivot
			# ctrl.rotatePivotX.set(l=0, k=1)
			# ctrl.rotatePivotY.set(l=0, k=1)
			# ctrl.rotatePivotZ.set(l=0, k=1)
			# Link Rotate Pivot to scale and translate pivots
			# ctrl.rotatePivot.connect(ctrl.scalePivot, f=1)
			# ctrl.rotatePivotTranslateX.set(l=1)
			# ctrl.rotatePivotTranslateY.set(l=1)
			# ctrl.rotatePivotTranslateZ.set(l=1)

			# Pivot Vis Indicator
			# pivotStart = 	createNode('joint', n='%s_pivVis1' % ctrl.nodeName(), p=ctrl)
			# self.step(pivotStart, 'pivotStart')
			# pivotEnd = 		createNode('joint', n='%s_pivVis2' % ctrl.nodeName(), p=pivotStart)
			# self.step(pivotEnd, 'pivotEnd')
			# self.globalControl.showPivotOffsets.connect(pivotStart.v)

			# for pivVis in [pivotStart, pivotEnd]:
			# 	pivVis.overrideEnabled.set(1)
			# 	pivVis.overrideDisplayType.set(1)
			# 	pivVis.radius.set(0, l=1)
			# 	pivVis.hiddenInOutliner.set(1) # Maybe
			# ctrl.rotatePivot.connect(pivotEnd.translate)
			pass


		if not rotateOrder is None and not r is False:
			ctrl.rotateOrder.set(rotateOrder, k=0, cb=1)


		if register:
			self.ctrlsList.append(ctrl)
			self.publishList.append(ctrl)
			if doExtra:
				self.publishList.append(extra)

			if ctrlSets is not None:
				if not isinstance(ctrlSets, list):
					ctrlSets = [ctrlSets]

				subCtrlSetName = '%s%s_ControlSet' % (self.globalName, self.sideStr[self.fitNode.side.get()])
				if not objExists(subCtrlSetName):
					subCtrlSet = sets([ctrl], n=subCtrlSetName)
				else:
					subCtrlSet = sets( subCtrlSetName, e=True, forceElement=ctrl )


				for ctrlSet in ctrlSets:
					if ctrlSet is not '':
						if not objExists(ctrlSet):
							sets(subCtrlSetName, n=ctrlSet)
						else:
							sets(ctrlSet, e=True, forceElement=subCtrlSetName)


		for node in cFreezeList:
			if r is False:
				for attribute in node.r.getChildren():
					attribute.set(l=1, k=0)
			if s is False:
				for attribute in node.s.getChildren():
					attribute.set(l=1, k=0)

		if mirror:
			inverseSocket = self.socket(ctrl)
			inverseSocket.sz.set(-1)
			inverseSocket.rz.set(-180)





		self.setController(ctrl, ctrlParent)

		# if versions.current() > versions.v2017:

		# 	if self.controllerTags == True:
		# 		# tag control
		# 		controller(ctrl)
		# 		ctrlTag = ls(controller(ctrl, q=1)[0])[0] # Controller command returns a string because it's dumb.

		# 		ctrlTag.visibilityMode.set(1)
		# 		if len(ctrlTag.children.get()) > 1:
		# 			ctrlTag.cycleWalkSibling.set(1)

		# 		if ctrlParent:
		# 			# Find controller node associated with control parent
		# 			parentCtrlTag = None
		# 			controller(ctrlParent)
		# 			parentCtrlTag = ls(controller(ctrlParent, q=1)[0])[0]
		# 			if parentCtrlTag is not None:
		# 				# connect ctrl to parent ctrlTag as children (next available)
		# 				i=0
		# 				while True:
		# 					if not len(parentCtrlTag.children[i].inputs()):
		# 						ctrlTag.parent.connect(parentCtrlTag.children[i])
		# 						break
		# 					i = i+1
		# 					if i == 1000:
		# 						raise Exception('Code cycle detected')
		# 				parentCtrlTag.prepopulate.connect(ctrlTag.prepopulate)




		return ctrl


	def clashFix(self):
		if self.dev: print '# clashFix'
		numFixed = 0
		for node in self.clashList:
			# get name
			try:
				name = node.nodeName()
			except AttributeError:
				warning('Selection input should be Pymel instance. %s, %s' % (s, s.type()))

			# Check for nodes with name
			withName = ls(name)
			if len(withName) > 1:
				# TODO add a check for end digets and just add to that
				# so that 'nodeName01' doesnt become 'nodeName010'
				for i, dup in enumerate(withName):
					rnm = '%s%s' % (name, i)
					x = i
					while len(rnm) > 0:
						x = x+1
						rnm = '%s%s' % (name, x)

					dup.rename(rnm)
					numFixed = numFixed + 1
					if self.dev: print rnm

		print 'Nodes renamed: %s' % numFixed
		self.clashList = []


	def globalVisSDK(self, nodeList):
		'''Loosely ties the visiblity of the nodeList to the visibility of the global control
		By using a set driven key, nodes can be hidden freely, but also can be cycled back on by hiding and unhiding
		the global move node.
		'''
		if self.dev: print '# globalVisSDK'

		if not isinstance(nodeList, list):
			nodeList = [nodeList]


		if not hasAttr(self.globalControl, 'visSDK'):
			addAttr(self.globalControl, ln='visSDK', at='message', k=0, h=1)

		for node in nodeList:
			node.v.set(l=0)

			if not self.globalControl.visSDK.get():
				# If not already initiated, create Set driven key
				import maya.cmds as cmds
				# set sdk 0
				cmds.setDrivenKeyframe( '%s.visibility' % node.longName(), driverValue=0, value=0, cd='%s.visibility' % self.globalControl.longName(), inTangentType='linear', outTangentType='step' )
				# set sdk 1
				cmds.setDrivenKeyframe( '%s.visibility' % node.longName(), driverValue=1, value=1, cd='%s.visibility'% self.globalControl.longName(), inTangentType='linear', outTangentType='step' )
				
				visSDK = node.visibility.inputs()[0]
				visSDK.rename('globalVisibility_reset_SDK')
				visSDK.message.connect(self.globalControl.visSDK)
				visSDK.ktv.set(l = 1) # template channel
			else:
				visSDK = self.globalControl.visSDK.get()
				visSDK.output.connect(node.visibility)

			# Hide control
			node.v.set(1)
			node.v.set(k=0, cb=0)


	def constructDeleteList(self):
		'''Connect all nodes currently in self.deleteList to rigNode's delete attribute, and remove them from the list
		'''
		if self.dev: print '# constructDeleteList'

		if not hasAttr(self.selNode, 'deleteList'):
			addAttr(self.selNode, ln='deleteList', nn='Related Nodes', at='message', multi=True, k=0, h=1, indexMatters=False)
		if self.deleteList:
			for node in self.deleteList:
				# if not hasAttr(node, 'selNode'):
				# 	addAttr(node, ln='selNode', at='message', k=0, h=1)
				try:
					node.message.connect(self.selNode.deleteList, na=1)
					self.deleteList.remove(node)
				except:
					pass


	def constructBindList(self):
		'''Connect all nodes currently in self.bindList to rigNode's bindList attribute
		'''
		if self.dev: print '# constructBindList'

		if not hasAttr(self.rigNode, 'bindList'):
			addAttr(self.rigNode, ln='bindList', nn='Skin Cluster Joints', at='message', multi=True, k=0, h=1, indexMatters=False)
		
		if self.bindList:
			for node in self.bindList:
				if self.doAssetize:
					if not node in self.publishList:
						self.publishList.append(node)
				try:
					node.message.connect(self.rigNode.bindList, na=1)
				except:
					pass

				subBindSetName = '%s%s_BindSet' % (self.globalName, self.sideStr[self.side])
				if not objExists(subBindSetName):
					subBindSet = sets(self.bindList, n=subBindSetName)
				else:
					subBindSet = sets( subBindSetName, e=True, forceElement=self.bindList )


				if not objExists('bindSet'):
					bindSet = sets(subBindSet, n='bindSet')
				else:
					bindSet = sets( 'bindSet', e=True, forceElement=subBindSet )


	def constructControlSubset(self):
		pass
		utils.createHiddenDisplayLayer(name, nodes, colorIndex=None, colorRGB=None, visibility=None, displayType=None)


	def constructSelectionList(self, selectionName, selectionList):
		'''Create connections between a collection of nodes and the rigNode for UI
		'''
		if self.dev: print '# constructSelectionList'


		if not hasAttr(self.selNode, selectionName):
			addAttr(self.selNode, ln=selectionName, at='message', multi=True, k=0, h=1, indexMatters=False)
		for node in selectionList:
			try:
				node.message.connect(self.selNode.attr(selectionName), na=1)
			except:
				pass


	def freezeNodes(self):
		'''For each node in freezeList, lock transform attributes
		TODO
		Add lockNode
		'''
		if self.dev: print '# freezeNodes'

		freezeAll = not self.dev

		if self.freezeList:
			# for node in self.freezeList:
			# 	if not node.exists():
			# 		self.freezeList.remove(node)

			col.setOutlinerRGB(self.freezeList, self.freezeColor)
			
			for node in self.freezeList:
				if node in self.publishList:
					pass
					# col.setOutlinerRGB(node, self.publishColor)

				attributes = []

				if freezeAll:
					# FreezeAll
					attributes = listAttr(node, k=True)
					attributes.extend(listAttr(node, cb=True))
					if 'visbility' in attributes:
						attributes.remove('visibility')
				else:
					if objectType(node, isAType='transform'):
						attributes.extend(['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'])
					
					if objectType(node, isType='joint'):
						attributes.extend([ 'rotateOrder', 'rotateAxisX', 'rotateAxisY', 'rotateAxisZ', 'jointOrientX', 'jointOrientY', 'jointOrientZ' ])
					
					for attribute in attributes:
						if self.dev:
							node.attr(attribute).set(l=1)
						else:
							node.attr(attribute).set(l=1, k=0)
				
				# self.freezeList.remove(node)


	def attachRigNode(self, nodeList=None):
		if self.dev: print '# attachRigNode'
		
		if not nodeList:
			nodeList = self.ctrlsList

		for node in nodeList:
			if objectType(node, isAType='transform'):
				try:
					parent(self.rigNode, node, s=1, add=1)
				except:
					pass


	def pruneSet(self, rigNodeSet, rigNode=None):
		if self.dev: print '# pruneSet'
		# attachRigNode  instances the shape node.  If they're aleady in the rigNode set, they new instance is added to the set.  This removes other instances than the main one
		if not rigNode:
			rigNode = self.rigNode

		if isinstance(rigNodeSet, str) or isinstance(rigNodeSet, unicode):
			rigNodeSet = ls(rigNodeSet)[0]
		if isinstance(rigNodeSet, nt.ObjectSet):
			if rigNode in rigNodeSet:
				for inst in rigNode.getOtherInstances():
					if inst in rigNodeSet:
						rigNodeSet.remove(inst)
						# rigNodeSet.removeMembers(inst)


	def socket(self, node, buff=False):
		if self.dev: print '# socket'
		# Used as transform offset to allow pivot moving and nondestructive rigging. Prevent doubling up on offsets by saving out sockets to attribute.

		if not hasAttr(node, 'socketNode'):
			addAttr(node, ln='socketNode', k=0, h=1, at='message')

		if not node.socketNode.get():
			p=node
			# if buff:
			# 	socketBuff = createNode('transform', n='%s_socketBuff' % node.nodeName(), p=p)
			# 	self.step(socketBuff, 'socketBuff')
			# 	p=socketBuff
			socketNode = createNode('transform', n='%s_socketNode' % node.nodeName(), p=p)
			self.step(socketNode, 'socketNode')

			if not isConnected(socketNode.message, node.socketNode):
				socketNode.message.connect(node.socketNode)

			return socketNode
		else:
			return node.socketNode.get()


	def tagNode(self, node, tag):
		if not hasAttr(node, 'tag'):
			addAttr(node, ln='tag', dt='string', k=0)
			node.tag.set(tag, l=1)
		else:
			# warning('Attribute already has an attribute named \'tag\': %s' % node)
			node.tag.set(l=0)
			node.tag.set(tag, l=1)


		if self.sectionTag:
			if not hasAttr(node, 'sectionTag'):
				addAttr(node, ln='sectionTag', dt='string', k=0)
				node.sectionTag.set(self.sectionTag, l=1)
			else:
				node.sectionTag.set(l=0)
				node.sectionTag.set(self.sectionTag, l=1)


	def padFormat(self, integer, last):
		if self.dev: print '# padFormat'

		d = '%d' % integer
		if last < 100:
			d = '%01d' % integer
		else:
			d = '%02d' % integer
		
		return d

	# Rig Mini-builds
	# ========================================== FK ==============================================
	def buildFkSetup(self, transforms, shapes=None, nameVar=[], mirror=False, rigGroup=None, selectionPriority=0, startInt=0, register=None):
		if self.dev: print '# buildFkSetup'
		# TODO
		# I need a clean way to convert joint behavior mirroring to scale mirroring

		# fkGroup = self.fkSetup(shapes=fkShapes, transforms=self.fitNode.jointsList.get(), parent=self.rigGroup)
		# if self.dev: print '\n'
		self.sectionTag = 'FK'

		if not rigGroup:
			rigGroup = self.rigGroup

		# FK Group
		fkRigGroup = createNode('transform', n=self.names.get('fkControlsGroup', 'rnm_fkControlsGroup'), parent=rigGroup)
		self.step(fkRigGroup, 'fkRigGroup')
		self.publishList.append(fkRigGroup)

		addAttr(fkRigGroup, ln='results', at='message', multi=True, indexMatters=False, k=1)
		# FK Controls
		fkCtrls = []


		for i, jnt in enumerate(transforms):
			self.naming(i=startInt, n=startInt)
			self.names = utils.constructNames(self.namesDict)

			d = self.padFormat(startInt, len(transforms))
			# if self.dev: print d
			
			fkMirrorStart=False
			if i==0:
				fkMirrorStart = mirror

			if shapes:
				shape = shapes[i]
			else:
				shape = None

			
			outlinerColor = None
			if shape:
				if len(shape.getShapes()):
					outlinerColor = shape.getShapes()[0].overrideColorRGB.get()

			fkCtrl = self.createControlHeirarchy(
					transformSnap=jnt,
					selectionPriority=selectionPriority,
					mirror=mirror,
					mirrorStart=fkMirrorStart,
					name=self.names.get('fkCtrl', 'rnm_fkCtrl'),
					shape=shape,
					par=(fkRigGroup if i==0 else fkCtrls[i-1]),
					ctrlParent=(fkRigGroup if i==0 else fkCtrls[i-1]),
					outlinerColor=outlinerColor,
					register = (True if register is None else register[i]),
					jntBuf=True)
			fkCtrls.append(fkCtrl)

			try:
				self.fkCtrls.append(fkCtrl)
			except AttributeError:
				self.fkCtrls = []
				self.fkCtrls.append(fkCtrl)
			
			if not hasAttr(self.rigNode, 'fkSegmentScaleCompensate'):
				addAttr(self.rigNode, ln='fkSegmentScaleCompensate', min=0, max=1, at='short', dv=1, keyable=1)
			self.rigNode.fkSegmentScaleCompensate.connect(fkCtrl.buf.get().segmentScaleCompensate)
			
			if mirror:
				temp =createNode('transform', p=transforms[i])
				parent(temp, fkCtrl)
				socket = self.socket(fkCtrl)
				socket.t.set(temp.t.get())
				socket.r.set(temp.r.get())
				socket.s.set(temp.s.get())
				delete(temp)

			startInt = startInt + 1

		if len(self.fkCtrls) < 2:
				self.rigNode.fkSegmentScaleCompensate.set(0, k=0)

		for fk in fkCtrls:
			fk.message.connect(fkRigGroup.results, na=1)

		return fkRigGroup



	# ========================================== AIM IK ==============================================
	def buildAimIkSetup(self, source, dest, sourceShape=None, destShape=None, controller=None, rigGroup=None, followInputs=False, inbetweenJoints=0, worldUpLocation=None, scaling=False, stretch=False, volume=False, twist=False, registerControls=[True, True], mirror=False, skipStart=False, skipEnd=False, twistAxisChoice=None):
		if self.dev: print '# buildAimIkSetup'
		if self.dev: print '\n'
		self.sectionTag = 'AimIK'

		if not rigGroup:
			rigGroup = self.rigGroup

		for node in [source, dest]:
			if not isinstance(node, nt.Transform):
				try:
					raise Exception('Node is not a transform: %s' % node)
				except:
					raise Exception('Node is not a transform.')

		

		aimIkGroup = createNode('transform', n=self.names.get('aimIkGroup', 'rnm_aimIkGroup'), parent=rigGroup)
		self.step(aimIkGroup, 'aimIkGroup')
		self.publishList.append(aimIkGroup)

		if not controller:
			controller = aimIkGroup


		# ============================== ATTRIBUTES ==============================
		if stretch:
			if not hasAttr(controller, 'stretch'):
				utils.cbSep(controller)
				addAttr(controller, ln='stretch', dv=1, min=0, max=1, k=1)

			if not hasAttr(controller, 'squash'):
				addAttr(controller, ln='squash', dv=1, min=0, max=1, k=1)

			if volume:
				if not hasAttr(controller, 'volumeY'):
					utils.cbSep(controller)
					addAttr(controller, ln='volumeY', dv=0.5, min=0, softMaxValue=2, k=1)
				if not hasAttr(controller, 'volumeZ'):
					addAttr(controller, ln='volumeZ', dv=0.5, min=0, softMaxValue=2, k=1)
				
			if not hasAttr(controller, 'restLength'):
				utils.cbSep(controller)
				addAttr(controller, ln='restLength', min=0.01, dv=1, keyable=1)

			if not hasAttr(controller, 'currentNormalizedLength'):
				addAttr(controller, ln='currentNormalizedLength', min=0, dv=1, keyable=1)
				controller.currentNormalizedLength.set(k=0, cb=1)

		if not hasAttr(controller, 'offsetCtrlsVis'):
			addAttr(controller, ln='offsetCtrlsVis', min=0, max=1, at='short', dv=0, keyable=0)
			controller.offsetCtrlsVis.set(k=0, cb=1)


		if not hasAttr(controller, 'upAxis'):
			utils.cbSep(controller)
			addAttr(controller, ln='upAxis', at='enum', enumName='Y=1:Z=2', dv=2, k=1)

		if not hasAttr(controller, 'upVis'):
			addAttr(controller, ln='upVis', at='short', min=0, max=1, dv=0, keyable=0)
			controller.upVis.set(k=0, cb=1)




		# ============================== START/END CONTROLS ==============================

		aimIkControlsGroup = createNode('transform', n=self.names.get('aimIkControlsGroup', 'rnm_aimIkControlsGroup'), parent=aimIkGroup)
		self.step(aimIkControlsGroup, 'aimIkControlsGroup')

		# Start
		# Set naming to 0
		self.naming(i=0)
		self.names = utils.constructNames(self.namesDict)



		outlinerColor = None
		if sourceShape:
			if len(sourceShape.getShapes()):
				outlinerColor = sourceShape.getShapes()[0].overrideColorRGB.get()
				
		startCtrl = self.createControlHeirarchy(
			name=self.names.get('startCtrl', 'rnm_startCtrl'), 
			transformSnap=source,
			shape = sourceShape,
			ctrlParent=aimIkGroup,
			register=registerControls[0],
			outlinerColor=outlinerColor,
			par=aimIkControlsGroup
		)
		

		# END
		# Set naming to 1
		self.naming(i=1)
		self.names = utils.constructNames(self.namesDict)

		
		outlinerColor = None
		if destShape:
			if len(destShape.getShapes()):
				outlinerColor = destShape.getShapes()[0].overrideColorRGB.get()
				
		endCtrl = self.createControlHeirarchy(
			name=self.names.get('endCtrl', 'rnm_endCtrl'), 
			transformSnap=dest,
			shape = destShape,
			ctrlParent=startCtrl, 
			register=registerControls[1],
			outlinerColor=outlinerColor,
			par=aimIkControlsGroup
		)

		if twistAxisChoice is None:
			twistAxisChoice = 0
			if self.fitNode.orientation.get(asString=1) == 'world':
				twistAxisChoice = self.fitNode.orientChoice.get()
				
		if twist:
			twistControllerStart = twistExtractorMatrix(points=startCtrl, base=self.socket(startCtrl.buf.get()), settingsNode = startCtrl.buf.get(), twistAxisChoice=twistAxisChoice, dev=self.dev)
			twistControllerEnd = twistExtractorMatrix(points=endCtrl, base=self.socket(endCtrl.buf.get()), settingsNode = endCtrl.buf.get(), twistAxisChoice=twistAxisChoice, dev=self.dev)
		else:
			if self.dev: warning('NO TWIST %s' % self.rigNode)
			# 


		self.aimCtrls = [startCtrl, endCtrl]

		# ============================== START/END RESULTS ==============================

		aimIkResultGroup = createNode('transform', n=self.names.get('aimIkResultGroup', 'rnm_aimIkResultGroup'), parent=aimIkGroup)
		self.step(aimIkResultGroup, 'aimIkResultGroup')


		# Start Result
		startResult = createNode('transform', n=self.names.get('startResult', 'rnm_startResult'), p=aimIkResultGroup)
		self.step(startResult, 'startResult')
		# Point constraint to start ctrl
		self.matrixConstraint(self.socket(startCtrl), startResult, t=1)

		# End Result
		endResult = createNode('transform', n=self.names.get('endResult', 'rnm_endResult'), p=startResult)
		self.step(endResult, 'endResult')
		# snap to end ctrl
		utils.snap(endCtrl, endResult)

		# self.ikAimResults = [startResult, endResult]



		# ============================== MID RESULTS ==============================
		
		ikAimResults = []
		# Create result points
		for i in range(inbetweenJoints+2):
			self.naming(n=i)
			self.names = utils.constructNames(self.namesDict)

			# create transforms
			midResult = createNode('transform', n=self.names.get('midResult', 'rnm_midResult#'), p=startResult)
			self.step(midResult, 'midResult')

			# Insert result into list before end point
			# ikAimResults.insert(-1, midResult) #  ikAimResults.index(ikAimResults[-1])
			ikAimResults.append(midResult) #  ikAimResults.index(ikAimResults[-1])
		



		# ============================== OFFSET CTRLS ==============================
		offsetCtrls = []
		for i, result in enumerate(ikAimResults):
			self.naming(n=i)
			self.names = utils.constructNames(self.namesDict)
			# get parameter
			
			rangeStart = True if i==0 else False
			rangeEnd = True if i==(len(ikAimResults)-1) else False

			if skipStart and rangeStart:
				continue
			if skipEnd and rangeEnd:
				continue

			d = float(i) / float(inbetweenJoints+1)

			# Calculat position of result object
			transMult = createNode('multiplyDivide', n=self.names.get('transMult', 'rnm_transMult#'))
			self.step(transMult, 'transMult')

			endResult.t.connect(transMult.input2)
			transMult.o.connect(result.t)

			# Create control
			offsetCtrl = self.createControlHeirarchy(
				name=self.names.get('offsetCtrl', 'rnm_offsetCtrl'), 
				selectionPriority=2,
				ctrlParent=(offsetCtrls[-1] if i else aimIkGroup),
				mirror=mirror,
				register=(False if followInputs else True),
				par=aimIkControlsGroup
			)
			offsetCtrls.append(offsetCtrl)
			self.matrixConstraint(result, offsetCtrl.const.get(), r=1, offset=False)
			
			# Vis
			controller.offsetCtrlsVis.connect(offsetCtrl.buf.get().v)

			# Parameter attribute
			utils.cbSep(offsetCtrl)
			addAttr(offsetCtrl, ln='parameter', min=0, max=1, dv=d, k=1)

			offsetCtrl.parameter.connect(transMult.input1X)
			offsetCtrl.parameter.connect(transMult.input1Y)
			offsetCtrl.parameter.connect(transMult.input1Z)

			# ikAimResults.append(midResult)


			
				# Rig variables
		results = offsetCtrls
		if inbetweenJoints:
			
			if twist:
						
				twistTransResults = []

				for offset in offsetCtrls:
					# ( startTwist * parameter ) + ( endTwist * reverse(parameter) ) = resultTwist
					# Create twist node
					twistTrans = createNode('transform', n=self.names.get('twistTrans', 'rnm_twistTrans'), p=offset)
					self.step(twistTrans, 'twistTrans')
					twistTransResults.append(twistTrans)

					parameterRev = createNode('reverse', n=self.names.get('parameterRev', 'rnm_parameterRev#'))
					self.step(parameterRev, 'parameterRev')
					offset.parameter.connect(parameterRev.inputX)

					twistAdd = createNode('addDoubleLinear', n=self.names.get('twistAdd', 'rnm_twistAdd#'))
					self.step(twistAdd, 'twistAdd')

					twistMultStart = createNode('multDoubleLinear', n=self.names.get('twistMultStart', 'rnm_twistMultStart#'))
					self.step(twistMultStart, 'twistMultStart')
					parameterRev.outputX.connect(twistMultStart.i1)
					twistControllerStart.twist.connect(twistMultStart.i2)

					twistMultStart.o.connect(twistAdd.i1)

					twistMultEnd = createNode('multDoubleLinear', n=self.names.get('twistMultEnd', 'rnm_twistMultEnd#'))
					self.step(twistMultEnd, 'twistMultEnd')
					offset.parameter.connect(twistMultEnd.i1)
					twistControllerEnd.twist.connect(twistMultEnd.i2)

					twistMultEnd.o.connect(twistAdd.i2)

					twistAdd.o.connect(twistTrans.rotateX)

				results = twistTransResults

			if False:

				scalingTransResults = []
				for result, offset in zip(results, offsetCtrls):
					# ( startScale * parameter ) + ( endScale * reverse(parameter) ) = resultScale
					scaleTrans = createNode('transform', n=self.names.get('scaleTrans', 'rnm_scaleTrans'), p=result)
					self.step(scaleTrans, 'scaleTrans')
					scaleTransResults.append(scaleTrans)

					
					scaleEndMult = createNode('multiplyDivide', n=self.names.get('scaleEndMult', 'rnm_scaleEndMult#'))
					self.step(scaleEndMult, 'scaleEndMult')
					offset.parameter.connect(scaleEndMult.input1X)
					offset.parameter.connect(scaleEndMult.input1Y)
					offset.parameter.connect(scaleEndMult.input1Z)
					endCtrl.scale.connect(scaleEndMult.input2)

					scaleStartMult = createNode('multiplyDivide', n=self.names.get('scaleStartMult', 'rnm_scaleStartMult#'))
					self.step(scaleStartMult, 'scaleStartMult')
					offset.parameter.connect(scaleStartMult.input1X)
					offset.parameter.connect(scaleStartMult.input1Y)
					offset.parameter.connect(scaleStartMult.input1Z)
					startCtrl.scale.connect(scaleStartMult.input2)

					scaleAdd = createNode('multiplyDivide', n=self.names.get('scaleAdd', 'rnm_scaleAdd#'))
					self.step(scaleAdd, 'scaleAdd')
					scaleEndMult.output.connect(scaleAdd.input1)
					scaleStartMult.output.connect(scaleAdd.input2)

					scaleAdd.output.connect(result.scale)

				results = scalingTransResults

			# if volume:


		if followInputs:
			self.matrixConstraint(source, startCtrl.const.get())
			self.matrixConstraint(dest, endCtrl.const.get())
		
		# ============================== RIG ==============================


		upVec=(0,0,1)
		worldUpType = 'objectRotation'
		if worldUpLocation:
			worldUpType = 'object'


		upObject = self.createControlHeirarchy(
			name=self.names.get('upObject', 'rnm_upObject'), 
			selectionPriority=2,
			transformSnap = worldUpLocation,
			par=aimIkControlsGroup,
		)
		if worldUpType == 'objectRotation':
			lockAndHideAttributes = [upObject.tx, upObject.ty, upObject.tz, upObject.sx, upObject.sy, upObject.sz]

		elif worldUpType == 'object':
			lockAndHideAttributes = [upObject.sx, upObject.sy, upObject.sz]

		utils.lockAndHide(lockAndHideAttributes, upObject)

		controller.upVis.connect(upObject.buf.get().v)

		if not followInputs:
			# Twist needs a static up controller to work. If no twist, allow space switching of up control
			# Space switch object
			self.upControlSS = spaceSwitch(controller=upObject,
				constraintType='parent',
				constrained=upObject.const.get(), 
				prefix=self.names.get('upControlSS', 'rnm_upControlSS'),
				p=upObject.buf.get(),
				offsets=True,
				targets=[upObject.buf.get(), startCtrl, endCtrl],
				labels=['Parent', 'Start IK', 'End IK'])


		

		if worldUpLocation:
			utils.snap(worldUpLocation, upObject.buf.get())

			temp = createNode('transform', p=upObject)
			
			upVec = dt.Vector(xform(temp, q=1, ws=1, rp=1)) - dt.Vector(xform(startResult, q=1, ws=1, rp=1))
			upVec.normalize()
			if self.dev:
				print 'Up Vector:'
				print  upVec
			delete(temp)

		# Get aim vector between objects
		temp = createNode('transform', p=endCtrl)
		parent(temp, startResult)
		aimVec = dt.Vector(temp.t.get())
		aimVec.normalize()
		transPoint = dt.Vector(temp.t.get())
		if self.dev:
			print 'Local Vector:'
			print  aimVec

		delete(temp)


		# TODO: up vector can be more varied.  Find a way to get 90deg vector
		aim = aimConstraint(self.socket(endCtrl), startResult, aimVector=aimVec, worldUpObject=upObject, worldUpType=worldUpType, worldUpVector=upVec, upVector=upVec, mo=True)
		self.tangledAimConstraints.append(aim)

		if worldUpType == 'objectRotation':
			# upObject.displayLocalAxis.set(1)

			# Up Axis switch
			upAxisSwitch = createNode('condition', n=self.names.get('upAxisSwitch', 'rnm_upAxisSwitch'))
			self.step(upAxisSwitch, 'upAxisSwitch')
			# Y = 1, Z = 2
			controller.upAxis.connect(upAxisSwitch.firstTerm)
			upAxisSwitch.secondTerm.set(2)
			upAxisSwitch.colorIfFalse.set(upVec)
			upAxisSwitch.colorIfTrue.set(upVec)


			upAxisSwitch.outColor.connect(aim.upVector)
			upAxisSwitch.outColor.connect(aim.worldUpVector)
		else:

			indics = utils.boneIndic(upObject, startCtrl, blackGrey=1)
			# curveIndic = utils.curveIndic(upObject, startCtrl, blackGrey=1)[0]
			# self.step(curveIndic, 'curveIndic')
			indics = utils.boneIndic(upObject, endCtrl, blackGrey=1)
			# curveIndic = utils.curveIndic(upObject, endCtrl, blackGrey=1)[0]
			# self.step(curveIndic, 'curveIndic')


		if stretch:

			# Static Length between controls
			staticLengthGroup = createNode('transform', n=self.names.get('staticLengthGroup', 'rnm_staticLengthGroup'), p=aimIkResultGroup)
			self.step(staticLengthGroup, 'staticLengthGroup')

			staticLocStart = createNode('transform', n=self.names.get('staticLocStart', 'rnm_staticLocStart'), p=staticLengthGroup)
			staticLocStartS = createNode('locator', n='%sShape' % self.names.get('staticLocStart', 'rnm_staticLocStart'), p=staticLocStart)
			self.step(staticLocStart, 'staticLocStart')
			staticLocStartS.hide()
			utils.snap(startCtrl, staticLocStart)
			
			staticLocEnd = createNode('transform', n=self.names.get('staticLocEnd', 'rnm_staticLocEnd'), p=staticLengthGroup)
			staticLocEndS = createNode('locator', n='%sShape' % self.names.get('staticLocEnd', 'rnm_staticLocEnd'), p=staticLocEnd)
			self.step(staticLocEnd, 'staticLocEnd')
			staticLocEndS.hide()
			utils.snap(endCtrl, staticLocEnd)
			
			staticLength = createNode('distanceBetween', n=self.names.get('staticLength', 'rnm_staticLength'))
			self.step(staticLength, 'staticLength')

			staticLocStart.worldPosition.connect(staticLength.point1)
			staticLocEnd.worldPosition.connect(staticLength.point2)


			# Dynamic length between controls
			locStart = createNode('locator', n=self.names.get('locStart', 'rnm_locStart'), p=self.socket(startCtrl))
			self.step(locStart, 'locStart')
			locStart.hide()

			locEnd = createNode('locator', n=self.names.get('locEnd', 'rnm_locEnd'), p=self.socket(endCtrl))
			self.step(locEnd, 'locEnd')
			locEnd.hide()

			self.aimCtrlLocs = [locStart, locEnd]
			
			length = createNode('distanceBetween', n=self.names.get('length', 'rnm_length'))
			self.step(length, 'length')

			locStart.worldPosition.connect(length.point1)
			locEnd.worldPosition.connect(length.point2)


			# Multiply static length by rig input
			staticDistMult = createNode('multDoubleLinear', n=self.names.get('staticDistMult', 'rnm_staticDistMult'))
			self.step(staticDistMult, 'staticDistMult')
			staticLength.distance.connect(staticDistMult.i1)
			controller.restLength.connect(staticDistMult.i2)


			# Normalized distance between controls
			normalizeDiv = createNode('multiplyDivide', n=self.names.get('normalizeDiv', 'rnm_normalizeDiv'))
			self.step(normalizeDiv, 'normalizeDiv')
			normalizeDiv.operation.set(2)

			length.distance.connect(normalizeDiv.input1X)
			staticDistMult.output.connect(normalizeDiv.input2X)
			# staticLength.distance.connect(normalizeDiv.input2X)

			# Stretch
			stretchBlend = createNode( 'blendTwoAttr', n=self.names.get('stretchBlend', 'rnm_stretchBlend') )
			self.step(stretchBlend, 'stretchBlend')
			stretchBlend.i[0].set(1)
			normalizeDiv.outputX.connect(stretchBlend.i[1])
			controller.stretch.connect(stretchBlend.ab)

			# Squash
			squashBlend = createNode( 'blendTwoAttr', n=self.names.get('squashBlend', 'rnm_squashBlend') )
			self.step(squashBlend, 'squashBlend')
			normalizeDiv.outputX.connect(squashBlend.i[1])
			squashBlend.i[0].set(1)
			controller.squash.connect(squashBlend.ab)

			# Squash/Stretch combiner
			squashStretchCond = createNode( 'condition', n=self.names.get('squashStretchCond', 'rnm_squashStretchCond') )
			self.step(squashStretchCond, 'squashStretchCond')
			normalizeDiv.outputX.connect(squashStretchCond.firstTerm)
			squashStretchCond.operation.set(2) # Greater Than
			squashStretchCond.secondTerm.set(1)
			stretchBlend.o.connect(squashStretchCond.colorIfTrueR)
			squashBlend.o.connect(squashStretchCond.colorIfFalseR)
			
			squashStretchCond.outColorR.connect(controller.currentNormalizedLength)
			controller.currentNormalizedLength.set(l=1)

			# normalizeDiv.outputX.connect(self.rigNode.currentNormalizedLength)

			restLengthMult = createNode('multDoubleLinear', n=self.names.get('restLengthMult', 'rnm_restLengthMult'))
			self.step(restLengthMult, 'restLengthMult')
			squashStretchCond.outColorR.connect(restLengthMult.i1)
			controller.restLength.connect(restLengthMult.i2)



			attributes = endResult.t.getChildren()

			for i, attribute in enumerate(attributes):

				stretchMap = createNode('blendTwoAttr', n='%s%s' % (self.names.get('stretchMap', 'rnm_stretchMap'), ['x', 'y', 'z'][i]))
				stretchMap.i[0].set(0)
				stretchMap.i[1].set(transPoint[i])
				self.step(stretchMap, 'stretchMap')

				stretchMap.o.connect(attribute)

				restLengthMult.o.connect(stretchMap.ab)
				# controller.currentNormalizedLength.connect(stretchMap.ab)




		addAttr(aimIkGroup, ln='results', at='message', multi=True)
		for i, ctrl in enumerate(results):
			ctrl.message.connect(aimIkGroup.results[i])


		return aimIkGroup

		# ========================================== ROTATE PLANE IK ==============================================
	

	# ============================================== 3-POINT ROTATE PLANE IK ==============================================
	def buildIkSetup(self, transforms, poleVectorTransform, shapes, ikOrients=None, nameVar=[], pvFollow=True, antipop=True, stretch=True, mirror=False, ):
		if self.dev: print '# buildIkSetup'
		# TODO
		# elbow pinning
		# use joint length to enact antipop on stretchy ik

		if self.dev: print '\n'
		self.sectionTag = 'IK'

		if len(transforms) != 3:
			raise Exception('Incorrect number of input transforms')

		if not isinstance(poleVectorTransform, PyNode):
			raise Exception('Verify input: poleVectorTransform. (%s)' % type(poleVectorTransform))

		ikRigGroup = createNode('transform', n=self.names.get('ikRigGroup', 'rnm_ikRigGroup'), parent=self.rigGroup)
		self.step(ikRigGroup, 'ikRigGroup')
		self.publishList.append(ikRigGroup)

		# ========================= IK Joints =========================

		ikJointsGroup = createNode('transform', n=self.names.get('ikJointsGroup', 'rnm_ikJointsGroup'), parent=ikRigGroup)
		self.step(ikJointsGroup, 'ikJointsGroup')

		# ###
		for i in range(len(transforms)):
			self.naming(i)
			self.names = utils.constructNames(self.namesDict)
			# if self.dev: print i
			if i:
				jointParent = self.ikJoints[i-1]
			else:
				jointParent = ikJointsGroup

			ikJoint = createNode('joint', n=self.names.get('ikJoint', 'rnm_ikJoint'), p=jointParent)
			ikJoint.hide()
			ikJoint.radius.set(0.5)
			
			try:
				self.ikJoints.append(ikJoint)
			except AttributeError:
				self.ikJoints = []
				self.ikJoints.append(ikJoint)

			self.deleteList.append(ikJoint)
			# self.freezeList.append(ikJoint)

			xform(ikJoint, ws=True, matrix=xform(transforms[i], q=1, matrix=1, ws=1))

			# Orient?
			# Negative Y towards pv
			# Add offsets
			self.step(ikJoint, 'ikJoint', freeze=False)
		# ###
		# col.setOutlinerRGB(self.ikJoints, self.ikJointsColor)
		col.setViewportRGB(self.ikJoints, self.ikJointsColor)

		makeIdentity(self.ikJoints[0], apply=1, t=1, r=1, s=1, n=0, pn=1)


		# ========================= IK Handle =========================

		ikh, eff = ikHandle(sj=self.ikJoints[0], ee=self.ikJoints[-1], sol='ikRPsolver')
		rename(ikh, self.names.get('ikh', 'rnm_ikh'))
		rename(eff, self.names.get('eff', 'rnm_eff'))
		self.step(ikh, 'ikh', freeze=False)
		self.step(eff, 'eff', freeze=False)
		ikh.hide()


		# ========================= IK Controls =========================

		ikCtrlsGroup = createNode('transform', n=self.names.get('ikCtrlsGroup', 'rnm_ikCtrlsGroup'), parent=ikRigGroup)
		self.step(ikCtrlsGroup, 'ikCtrlsGroup')

		# ###
		for i in range(len(transforms)):
			self.naming(i)
			self.names = utils.constructNames(self.namesDict)
			# if self.dev: print i
			# Start, PV, End

			ctrlParent = ikCtrlsGroup

			if ikOrients is None:
				oriTrans = self.globalControl
			else:
				oriTrans = ikOrients[i]
			
		
			outlinerColor = None
			if shapes:
				print shapes
				if len(shapes[i].getShapes()):
					outlinerColor = shapes[i].getShapes()[0].overrideColorRGB.get()
			
			print outlinerColor

			if i==1:
				# Pole Vector
				posTrans = poleVectorTransform


				ikCtrl = self.createControlHeirarchy(transformSnap=posTrans, orientSnap=oriTrans, mirror=False, name=self.names.get('pvCtrl', 'rnm_pvCtrl'), shape=shapes[i], outlinerColor=outlinerColor, ctrlParent= (ikRigGroup if i==0 else self.ikCtrls[i-1]), par=ikCtrlsGroup, pivot=False, rotateOrder=None, r=False, s=False)

			else:
				posTrans = transforms[i]
				ikCtrl = self.createControlHeirarchy(transformSnap=posTrans, orientSnap=oriTrans, mirror=False, name=self.names.get('ikCtrl', 'rnm_ikCtrl'), shape=shapes[i], outlinerColor=outlinerColor, ctrlParent= (ikRigGroup if i==0 else self.ikCtrls[i-1]), par=ikCtrlsGroup)
			

			try:
				self.ikCtrls.append(ikCtrl)
			except AttributeError:
				self.ikCtrls = []
				self.ikCtrls.append(ikCtrl)

			# if i==1:
			# 	lockAndHide = [
			# 	ikCtrl.rx,
			# 	ikCtrl.ry,
			# 	ikCtrl.rz,
			# 	ikCtrl.sx,
			# 	ikCtrl.sy,
			# 	ikCtrl.sz,
			# 	]
			# 	for lh in lockAndHide:
			# 		lh.set(l=1, k=0)

			self.step(ikCtrl, 'ikCtrl', freeze=False)
		# ###
		# constraint top joint to first control
		self.matrixConstraint(self.ikCtrls[0], ikJointsGroup)
		# self.matrixConstraint(self.socket(self.ikCtrls[0]), self.ikJoints[0], t=0, r=0, s=1)
		

		# IK Hand Attributes
		# ikCtrl  		>>	hand
		# self.ikCtrls 	>>	[shoulder, pv, hand]
		# TODO
		# Rebuild spaceswitch
		# Add attributes as needed

		utils.cbSep(ikCtrl)
		if stretch:
			addAttr(ikCtrl, ln="stretch", 			dv=0, min=0, max=1, k=1)
		if antipop:
			addAttr(ikCtrl, ln="antiPop",			dv=0, min=0, k=1)
		if stretch or antipop:
			utils.cbSep(ikCtrl)
		
		addAttr(ikCtrl, ln="multLength1", 		dv=1, min=0, k=1)
		addAttr(ikCtrl, ln="multLength2", 		dv=1, min=0, k=1)

		if pvFollow:
			utils.cbSep(ikCtrl)
			addAttr(ikCtrl, ln="swivel", nn="Swivel PV", dv=0, k=1)
		
		addAttr(ikCtrl, ln="showPV",			dv=1, min=0, max=1, at='short', k=1)
		setAttr(ikCtrl.showPV, k=0, cb=1)
		
		# Hand ctrl socket
		# Orient a transform under ik control that follows joint orientation and use to drive joint orient
		ikCtrlSocket = self.socket(ikCtrl, buff=True)
		# ikSocketBuff = ikCtrlSocket.getParent()
		# xform(ikSocketBuff, ws=1, ro=xform(transforms[2], q=1, ro=1))
		delete(orientConstraint(transforms[2], ikCtrlSocket))
		
		ikhBuf = createNode('transform', n=self.names.get('ikhBuf', 'rnm_ikhBuf'), p=ikCtrlSocket)
		self.step(ikhBuf, 'ikhBuf')
		
		self.ikhConst = createNode('transform', n=self.names.get('ikhConst', 'rnm_ikhConst'), p=ikhBuf)
		self.step(self.ikhConst, 'ikhConst')

		parent(ikh, self.ikhConst)
		ikh.rotate.set(0,0,0)

		self.matrixConstraint(ikCtrlSocket, self.ikJoints[2], t=0, r=1, s=1)
		# orientConstraint(ikCtrlSocket, self.ikJoints[2])
		
		# self.matrixConstraint(ikCtrlSocket, self.ikJoints[2], t=0, r=1, s=0, offset=0)

		# utils.spaceSwitch(
		# 	control=ikCtrl, 
		# 	constrained=ikCtrl.const.get(), 
		# 	targets=[self.socketGroup, self.rigGroup],
		# 	labels=['World', 'Rig'],
		# 	constraintType=0, 
		# 	prefix=ikCtrl.nodeName()
		# 	)

		# addAttr(ikCtrl.attr('parentSpaceBlend'), e=1, nn='Parent Follow', dv=1)

		# Pole Vector Attributes
		pv = self.ikCtrls[1]

		ikCtrl.showPV >> pv.buf.get().v
		pvSocket = self.socket(pv)

		poleVectorConstraint(pvSocket, ikh)

		indic = utils.boneIndic(self.ikJoints[1], pv, self.rigGroup)[0]
		pvVisMult = createNode('multDoubleLinear', n=self.names.get('pvVisMult', 'rnm_pvVisMult'))
		self.ikVis.connect(pvVisMult.i1)
		ikCtrl.showPV.connect(pvVisMult.i2)
		pvVisMult.o.connect(indic.v)
		
		# curveIndic = utils.curveIndic(pv, self.ikJoints[1])[0]
		# self.step(curveIndic, 'curveIndic')

		# ========================= PV Follow Setup =========================

		if pvFollow:

			utils.cbSep(pv)

			addAttr(pv, ln='followType', 	nn='PV Follow Type', at='enum', enumName='Parent:Start:End', k=1, dv=0)
			# addAttr(pv, ln="follow", 		dv=1, min=0, max=1, k=1)

			pvFollowTypeChoice = createNode('choice', n=self.names.get('pvFollowTypeChoice', 'rnm_pvFollowTypeChoice'))
			self.step(pvFollowTypeChoice, 'pvFollowTypeChoice')
			pvFollowTypeChoice.input[0].set(4)
			pvFollowTypeChoice.input[1].set(2)
			pvFollowTypeChoice.input[2].set(2)
			pv.followType.connect(pvFollowTypeChoice.selector)

			topIkSocket = self.socket(self.ikCtrls[0])

			pvFollowGroup = createNode('transform', n=self.names.get('pvFollowGroup', 'rnm_pvFollowGroup'), p=ikRigGroup)
			self.step(pvFollowGroup, 'pvFollowGroup')
			# utils.snap(topIkSocket, pvFollowGroup)

			# pvFollowAim = createNode('transform', n=self.names.get('pvFollowAim', 'rnm_pvFollowAim'), p=self.ikCtrls[0])
			pvFollowAim = createNode('transform', n=self.names.get('pvFollowAim', 'rnm_pvFollowAim'), p=pvFollowGroup)
			self.step(pvFollowAim, 'pvFollowAim')
			self.matrixConstraint(topIkSocket, pvFollowAim, offset=False)

			# Used to reverse the twist caused by rotation to be driven only by control
			pvFollowAimTwist = createNode('transform', n=self.names.get('pvFollowAimTwist', 'rnm_pvFollowAimTwist'), p=pvFollowAim)
			self.step(pvFollowAimTwist, 'pvFollowAimTwist')


			pvFollowAimAt = createNode('transform', n=self.names.get('pvFollowAimAt', 'rnm_pvFollowAimAt'), p=ikCtrl)
			self.step(pvFollowAimAt, 'pvFollowAimAt')
			xform(pvFollowAimAt, ws=1, ro=xform(pvFollowGroup, q=1, ws=1, ro=1))

			pvFollowTop = createNode('transform', n=self.names.get('pvFollowTop', 'rnm_pvFollowTop'), p=self.ikCtrls[0])
			self.step(pvFollowTop, 'pvFollowTop')
			xform(pvFollowTop, ws=1, ro=xform(pvFollowGroup, q=1, ws=1, ro=1))


			if mirror:
				aimVector = (-1,0,0)
			else:
				aimVector = (1,0,0)

			# if not hasAttr(self.rigNode, 'pvFollowType'):
			# 	addAttr(self.rigNode, ln='pvFollowType', nn='PV Follow Type', at='enum', enumName='Rotation=2:Static=4', k=1, dv=4)


			wup = 4
			aim = aimConstraint(pvFollowAimAt, pvFollowAim, aimVector=aimVector, upVector=(0,1,0), worldUpVector=(0,1,0), worldUpType=4, mo=False)
			# self.rigNode.pvFollowType.connect(aim.worldUpType)
			pvFollowTypeChoice.output.connect(aim.worldUpType)

			pvFollowResult = createNode('transform', n=self.names.get('pvFollowResult', 'rnm_pvFollowResult'), p=pvFollowAimTwist)
			xform(pvFollowResult, ws=1, m=xform(poleVectorTransform, q=1, ws=1, m=1))
			self.step(pvFollowResult, 'pvFollowResult')


			pvFollowUpChoice = createNode('choice', n=self.names.get('pvFollowUpChoice', 'rnm_pvFollowUpChoice'))
			self.step(pvFollowUpChoice, 'pvFollowUpChoice')
			self.rigGroup.worldMatrix.connect(pvFollowUpChoice.input[0])
			pvFollowTop.worldMatrix.connect(pvFollowUpChoice.input[1])
			pvFollowAimAt.worldMatrix.connect(pvFollowUpChoice.input[2])
			pv.followType.connect(pvFollowUpChoice.selector)
			pvFollowUpChoice.output.connect(aim.worldUpMatrix)

			# twistExtractorMatrix(pvFollowAim, base=ikCtrlsGroup, settingsNode=pvFollowAim)
			# pvFollowAim.mult.set(1)

			# ikCtrlTwistAdd = createNode('addDoubleLinear', n=self.names.get('ikCtrlTwistAdd', 'rnm_ikCtrlTwistAdd'))
			# self.step(ikCtrlTwistAdd, 'ikCtrlTwistAdd')

			# ikCtrl.swivel.connect(ikCtrlTwistAdd.i1)
			# # pvFollowAim.twist.connect(ikCtrlTwistAdd.i2)

			ikCtrl.swivel.connect(pvFollowAimTwist.rotateX)
			# if mirror:
			# 	# ikCtrl.swivel >> aim.offsetX
			# 	ikCtrlTwistAdd.o.connect(pvFollowAimTwist.rotateX)
			# else:
			# 	uc = createNode('unitConversion')
			# 	uc.conversionFactor.set(-0.017)
			# 	ikCtrlTwistAdd.o.connect(uc.i)
			# 	uc.o >> pvFollowAimTwist.rotateX

			# DO SS HERE?
			# Follow switch
			# self.matrixConstraint(pvFollowResult, pv.const.get(), t=1, r=0, offset=0, untangled=True)
			# pvFollowConstraint = pv.const.get().constraintNodes[1].get()
			# pvFollow = pv.constraintNodes.get()[1]
		
			# pvFollowBlend = createNode('blendColors', n=self.names.get('pvFollowBlend', 'rnm_pvFollowBlend'))
			# self.step(pvFollowBlend, 'pvFollowBlend')
			# pvFollowConstraint.outputTranslate >> pvFollowBlend.color1
			# pvFollowBlend.color2.set((0,0,0))
			# pvFollowBlend.output.connect(pv.const.get().translate, f=1)
			# pv.follow.connect(pvFollowBlend.blender)
			# pv.const.get().tx.disconnect()
			# pv.const.get().ty.disconnect()
			# pv.const.get().tz.disconnect()

			pvFollowSS = simpleSpaceSwitch(
				constraintType='point',
				controller = pv,
				constrained= pv.const.get(),
				prefix = self.names.get('pvFollowSS', 'rnm_pvFollowSS'),
				targets=[self.rigsGroup, pvFollowResult],
				labels=['World', 'Follow'],
				offsets=True,
			)
			pvFollowSS.setNiceName('PV Follow')

			self.matrixConstraint(self.rigsGroup, pv.const.get(), t=0, r=1)

		# ========================= IK Stretch Setup =========================
		# Locators
		stretchNodes = []
		antipopNodes = []

		# Distance between start and end ik controls
		self.ikCtrlLocs = []
		for i, ikCtrl in enumerate([self.ikCtrls[0], self.ikCtrls[2]]):
			self.ikCtrlLocs.append(createNode('locator', n='%sDistLoc' % ikCtrl.nodeName(), p=ikCtrl))
			stretchNodes.append(self.ikCtrlLocs[i])
			self.ikCtrlLocs[i].hide()
			self.step(self.ikCtrlLocs[i], 'ikCtrlLoc%s' % i)

		ikCtrlDist = createNode('distanceBetween', n=self.names.get('ikCtrlDist', 'rnm_ikCtrlDist'))
		stretchNodes.append(ikCtrlDist)
		self.step(ikCtrlDist, 'ikCtrlDist')
		self.ikCtrlLocs[0].worldPosition.connect(ikCtrlDist.point1)
		self.ikCtrlLocs[1].worldPosition.connect(ikCtrlDist.point2)

		# static joint lengths
		# Disconnected from rig, but will scale. Use to get default lengths after non-uniform rig scaling
		scaleLenGroup = createNode('transform', n=self.names.get('scaleLenGroup', 'rnm_scaleLenGroup'), p=ikRigGroup)
		stretchNodes.append(scaleLenGroup)
		self.step(scaleLenGroup, 'scaleLenGroup')
		
		scaleLocators = []
		for i, t in enumerate(transforms):
			self.naming(i)
			self.names = utils.constructNames(self.namesDict)
			scaleLocS = createNode('locator')
			stretchNodes.append(scaleLocS)
			scaleLoc = scaleLocS.firstParent()
			scaleLoc.rename(self.names.get('scaleLoc', 'rnm_scaleLoc'))
			scaleLocators.append(scaleLocS)
			parent(scaleLoc, scaleLenGroup)
			scaleLoc.hide()
			xform(scaleLoc, ws=1, m=xform(t, q=1, ws=1, m=1))
			self.step(scaleLoc, 'scaleLoc')


		# Multiply static/scaling length by multLength ikCtrl input
		scaleDistances = []
		scaleLengthMults = []
		staticLengthMults = []
		for i in range(2):
			self.naming(i)
			self.names = utils.constructNames(self.namesDict)
			scaleDist = createNode('distanceBetween', n=self.names.get('scaleDist', 'rnm_scaleDist'))
			scaleDistances.append(scaleDist)
			stretchNodes.append(scaleDist)
			if i==0: # Start to mid
				scaleLocators[0].worldPosition.connect(scaleDist.point1)
				scaleLocators[1].worldPosition.connect(scaleDist.point2)
			else: # Mid to end
				scaleLocators[1].worldPosition.connect(scaleDist.point1)
				scaleLocators[2].worldPosition.connect(scaleDist.point2)
			self.step(scaleDist, 'scaleDist')

			scaleLengthMult = createNode('multDoubleLinear', n=self.names.get('scaleLengthMult', 'rnm_scaleLengthMult'))
			scaleLengthMults.append(scaleLengthMult)
			stretchNodes.append(scaleLengthMult)
			self.step(scaleLengthMult, 'scaleLengthMult')
			scaleLengthMult.i1.set(1)
			scaleDist.distance.connect(scaleLengthMult.i2)

			staticLengthMult = createNode('multDoubleLinear', n=self.names.get('staticLengthMult', 'rnm_staticLengthMult'))
			staticLengthMults.append(staticLengthMult)
			stretchNodes.append(staticLengthMult)
			self.step(staticLengthMult, 'staticLengthMult')

			staticLengthMult.i1.set(1)
			staticLengthMult.i2.set(scaleDist.distance.get())
			# staticDist.distance.connect(staticLengthMult.i2)

		# Length
		# (start-mid) + (mid-end) = full length at any scale
		addStaticLengths = createNode('addDoubleLinear', n=self.names.get('addStaticLengths', 'rnm_addStaticLengths'))
		stretchNodes.append(addStaticLengths)
		self.step(addStaticLengths, 'addStaticLengths')
		staticLengthMults[0].o.connect(addStaticLengths.i1)
		staticLengthMults[1].o.connect(addStaticLengths.i2)



		addScaleLengths = createNode('addDoubleLinear', n=self.names.get('addScaleLengths', 'rnm_addScaleLengths'))
		stretchNodes.append(addScaleLengths)
		self.step(addScaleLengths, 'addScaleLengths')
		scaleLengthMults[0].o.connect(addScaleLengths.i1)
		scaleLengthMults[1].o.connect(addScaleLengths.i2)

		# PV follow length
		addLengths = createNode('addDoubleLinear', n=self.names.get('addLengths', 'rnm_addLengths'))
		stretchNodes.append(addLengths)
		self.step(addLengths, 'addLengths')
		scaleDistances[0].distance.connect(addLengths.i1)
		scaleDistances[1].distance.connect(addLengths.i2)

	
		# Lengths Normalize Div
		# Current full distance divided by static full distance
		# Do for each?
		# Unused here?
		lengthNormalize = createNode('multiplyDivide', n=self.names.get('lengthNormalize', 'rnm_lengthNormalize'))
		stretchNodes.append(lengthNormalize)
		self.step(lengthNormalize, 'lengthNormalize')
		lengthNormalize.operation.set(2)
		# lengthNormalize.i1x.set(addStaticLengths.o.get())
		addStaticLengths.o.connect(lengthNormalize.i1x)
		addScaleLengths.o.connect(lengthNormalize.i2x)

		if stretch:
			# Stretch Normalize Div
			# current length/default length
			ctrlDistNormalize = createNode('multiplyDivide', n=self.names.get('ctrlDistNormalize', 'rnm_ctrlDistNormalize'))
			stretchNodes.append(ctrlDistNormalize)
			self.step(ctrlDistNormalize, 'ctrlDistNormalize')
			ctrlDistNormalize.operation.set(2)
			ikCtrlDist.distance >> ctrlDistNormalize.i1x
			addScaleLengths.o >> ctrlDistNormalize.i2x

			distNormalize = createNode('multiplyDivide', n=self.names.get('distNormalize', 'rnm_distNormalize'))
			stretchNodes.append(distNormalize)
			self.step(distNormalize, 'distNormalize')
			distNormalize.operation.set(2)
			ikCtrlDist.distance >> distNormalize.i1x
			addLengths.o >> distNormalize.i2x
			
			# Stretch On/Off
			stretchBlend = createNode('blendColors', n=self.names.get('stretchBlend', 'rnm_stretchBlend'))
			stretchNodes.append(stretchBlend)
			self.step(stretchBlend, 'stretchBlend')
			stretchBlend.color2.set(1, 1, 1)
			ikCtrl.stretch >> stretchBlend.blender
			


		# Clamp Ik multLength input to prevent div by 0
		multLengthClamp = createNode('clamp', n=self.names.get('multLengthClamp', 'rnm_multLengthClamp'))
		stretchNodes.append(multLengthClamp)
		self.step(multLengthClamp, 'multLengthClamp')
		multLengthClamp.minR.set(0.01)
		multLengthClamp.minG.set(0.01)
		multLengthClamp.maxR.set(999999)
		multLengthClamp.maxG.set(999999)
		# multLengthClamp.opr >> lengthMults[0].i1
		# multLengthClamp.opg >> lengthMults[1].i1

		multLengthClamp.opr >> scaleLengthMults[0].i1
		multLengthClamp.opg >> scaleLengthMults[1].i1
		multLengthClamp.opr >> staticLengthMults[0].i1
		multLengthClamp.opg >> staticLengthMults[1].i1
		ikCtrl.multLength1 >> multLengthClamp.ipr
		ikCtrl.multLength2 >> multLengthClamp.ipg


		if stretch:
			stretchClamp = createNode('clamp', n=self.names.get('stretchClamp', 'rmm_stretchClamp'))
			stretchNodes.append(stretchClamp)
			self.step(stretchClamp, 'stretchClamp')
			stretchClamp.minR.set(1)
			stretchClamp.maxR.set(999999)
			ctrlDistNormalize.outputX >> stretchClamp.inputR
			if stretch:
				stretchClamp.outputR >> stretchBlend.color1R



			#  Demormalize - Remultiply by default length
			denormalize = createNode('multiplyDivide', n=self.names.get('denormalize', 'rnm_denormalize'))
			stretchNodes.append(denormalize)
			self.step(denormalize, 'denormalize')
			if stretch:
				stretchBlend.outputR >> denormalize.i1x
				stretchBlend.outputR >> denormalize.i1y
			else:
				stretchClamp.outputR >> denormalize.i1x
				stretchClamp.outputR >> denormalize.i1y

			# Stretch Mult : StretchME Scale conversion Mult (clamped length * normal)
			stretchMult = createNode('multiplyDivide', n=self.names.get('stretchMult', 'rnm_stretchMult'))
			stretchNodes.append(stretchMult)
			self.step(stretchMult, 'stretchMult')
			multLengthClamp.opr >> stretchMult.i2x
			multLengthClamp.opg >> stretchMult.i2y
			denormalize.outputX >> stretchMult.i1x
			denormalize.outputY >> stretchMult.i1y

			denormalize.i2x.set(scaleDistances[0].distance.get())
			denormalize.i2y.set(scaleDistances[1].distance.get())


			




			if self.dev: self.constructSelectionList(selectionName='stretchNodes', selectionList=stretchNodes)

			staticLengthMults[0].o >> denormalize.input2X
			staticLengthMults[1].o >> denormalize.input2Y

			# # 
			revUnitConv1 = createNode('unitConversion')
			self.step(revUnitConv1, 'revUnitConv1')
			revUnitConv2 = createNode('unitConversion')
			self.step(revUnitConv2, 'revUnitConv2')
			
			denormalize.outputX >> revUnitConv1.i
			denormalize.outputY >> revUnitConv2.i

			if mirror:
				revUnitConv1.conversionFactor.set(-1)
				revUnitConv2.conversionFactor.set(-1)
			else:
				revUnitConv1.conversionFactor.set(1)
				revUnitConv2.conversionFactor.set(1)

			# revUnitConv1.o.connect(addStaticLengths.i1)
			# revUnitConv2.o.connect(addStaticLengths.i2)

			# #
			revUnitConv1.output >> self.ikJoints[1].translateX
			revUnitConv2.output >> self.ikJoints[2].translateX

		else:
			staticLengthMults[0].o >> self.ikJoints[1].translateX
			staticLengthMults[1].o >> self.ikJoints[2].translateX


		if stretch and pvFollow:
			# Stretch should also affect scale of elbow follow rig
			pvFollowNoStretchClamp = createNode('clamp', n=self.names.get('pvFollowNoStretchClamp', 'rnm_pvFollowNoStretchClamp'))
			stretchNodes.append(pvFollowNoStretchClamp)
			self.step(pvFollowNoStretchClamp, 'pvFollowNoStretchClamp')
			pvFollowNoStretchClamp.minR.set(0)
			pvFollowNoStretchClamp.maxR.set(1)

			pvFollowNoStretchClamp.minG.set(0)
			pvFollowNoStretchClamp.maxG.set(1)

			distNormalize.ox >> pvFollowNoStretchClamp.inputR
			distNormalize.ox >> pvFollowNoStretchClamp.inputG


			pvFollowStretchBlend = createNode('blendTwoAttr', n=self.names.get('pvFollowStretchBlend', 'rnm_pvFollowStretchBlend'))
			stretchNodes.append(pvFollowStretchBlend)
			self.step(pvFollowStretchBlend, 'pvFollowStretchBlend')
			pvFollowNoStretchClamp.outputR >> pvFollowStretchBlend.i[0]
			distNormalize.ox >> pvFollowStretchBlend.i[1]

			ikCtrl.stretch >> pvFollowStretchBlend.ab
			pvFollowStretchBlend.output >> pvFollowAim.sx

		if antipop:
			# I'm honestly not sure how this all works. Basic gist is that it's a natural log equasion
			# to that moves ik handle towards arm at an increasing rate until it equals distance between
			# ik controls. Doesn't work when stretching.

			# staticLength = staticDistances[0].distance.get() + staticDistances[1].distance.get() 
			# antipopNodes = []

			# Prevents div by 0 errors
			antipopClamp = createNode('clamp', n=self.names.get('antipopClamp', 'rnm_antipopClamp'))
			antipopNodes.append(antipopClamp)
			self.step(antipopClamp, 'antipopClamp')
			ikCtrl.antiPop >> antipopClamp.ipr
			antipopClamp.minR.set(0.01)
			antipopClamp.maxR.set(9999999)

			antipopSub1 = createNode('plusMinusAverage', n=self.names.get('antipopSub1', 'rnm_antipopSub1'))
			antipopNodes.append(antipopSub1)
			self.step(antipopSub1, 'antipopSub1')
			antipopSub1.operation.set(2)
			# antipopSub1.input1D[0].set(staticLength)
			addScaleLengths.o >> antipopSub1.input1D[0]
			antipopClamp.opr >> antipopSub1.input1D[1]
			ikCtrlDist.distance >> antipopSub1.input1D[2]

			antipopDiv1 = createNode('multiplyDivide', n=self.names.get('antipopDiv1', 'rnm_antipopDiv1'))
			antipopNodes.append(antipopDiv1)
			self.step(antipopDiv1, 'antipopDiv1')
			antipopDiv1.operation.set(2)
			antipopSub1.output1D >> antipopDiv1.i1x
			antipopClamp.opr >> antipopDiv1.i2x

			antipopPow = createNode('multiplyDivide', n=self.names.get('antipopPow', 'rnm_antipopPow'))
			antipopNodes.append(antipopPow)
			self.step(antipopPow, 'antipopPow')
			antipopPow.operation.set(3)
			antipopPow.i1x.set(2.718)
			antipopDiv1.ox >> antipopPow.i2x

			antipopMult1 = createNode('multiplyDivide', n=self.names.get('antipopMult1', 'rnm_antipopMult1'))
			antipopNodes.append(antipopMult1)
			self.step(antipopMult1, 'antipopMult1')
			antipopMult1.operation.set(1)
			antipopClamp.opr >> antipopMult1.i1x
			antipopPow.ox >> antipopMult1.i2x
			
			antipopSub2 = createNode('plusMinusAverage', n=self.names.get('antipopSub2', 'rnm_antipopSub2'))
			antipopNodes.append(antipopSub2)
			self.step(antipopSub2, 'antipopSub2')
			antipopSub2.operation.set(2)
			addScaleLengths.o >> antipopSub2.input1D[0]
			antipopMult1.ox >> antipopSub2.input1D[1]

			antipopSub3 = createNode('plusMinusAverage', n=self.names.get('antipopSub3', 'rnm_antipopSub3'))
			antipopNodes.append(antipopSub3)
			self.step(antipopSub3 ,'antipopSub3')
			antipopSub3.operation.set(2)
			addScaleLengths.o >> antipopSub3.input1D[0]
			antipopClamp.opr >> antipopSub3.input1D[1]

			antipopCond = createNode('condition', n=self.names.get('antipopCond', 'rnm_antipopCond'))
			antipopNodes.append(antipopCond)
			self.step(antipopCond, 'antipopCond')
			antipopCond.operation.set(5)
			ikCtrlDist.d >> antipopCond.ft
			antipopSub3.output1D >> antipopCond.st
			ikCtrlDist.d >> antipopCond.ctr
			antipopSub2.output1D >> antipopCond.cfr


			antipopSub4 = createNode('plusMinusAverage', n=self.names.get('antipopSub4', 'rnm_antipopSub4'))
			antipopNodes.append(antipopSub4)
			self.step(antipopSub4 ,'antipopSub4')
			antipopSub4.operation.set(2)
			ikCtrlDist.d >> antipopSub4.input1D[0]
			antipopCond.outColorR >> antipopSub4.input1D[1]

			if stretch:
				antipopBlend = createNode('blendTwoAttr', n=self.names.get('antipopBlend', 'rnm_antipopBlend'))
				antipopNodes.append(antipopBlend)
				self.step(antipopBlend, 'antipopBlend')
				antipopSub4.output1D >> antipopBlend.i[0]
				antipopBlend.i[1].set(0)
				ikCtrl.stretch >> antipopBlend.ab

			self.ikHandleGroup = createNode('transform', n=self.names.get('ikHandleGroup', 'rnm_ikHandleGroup'), p=ikRigGroup)
			antipopNodes.append(self.ikHandleGroup)
			self.step(self.ikHandleGroup, 'ikHandleGroup')
			self.matrixConstraint( ikCtrlSocket, self.ikHandleGroup, t=1, r=1, offset=False, force=True, preserve=False )

			antipopAimGrp = createNode('transform', n=self.names.get('antipopAimGrp', 'rnm_antipopAimGrp'), p=self.ikHandleGroup)
			antipopNodes.append(antipopAimGrp)
			self.step(antipopAimGrp, 'antipopAimGrp')

			# Protects scaling
			# ikCtrl.t >> antipopAimGrp.t

			antipopGrp = createNode('transform', n=self.names.get('antipopGrp', 'rnm_antipopGrp'), p=antipopAimGrp)
			antipopNodes.append(antipopGrp)
			self.step(antipopGrp, 'antipopGrp')

			antipopAimConst = aimConstraint(self.ikCtrls[0], antipopAimGrp, aimVector=[1,0,0], upVector=[0,0,1], worldUpVector=[0,0,1], worldUpType=2, worldUpObject=self.socket(self.ikCtrls[2]))
			# self.tangledMatrixConstraints.append(antipopAimConst)
			antipopNodes.append(antipopAimConst)
			self.step(antipopAimConst, 'antipopAimConst')
			self.tangledAimConstraints.append(antipopAimConst)

			antipopScale = createNode('multDoubleLinear', n=self.names.get('antipopScale', 'rnm_antipopScale'))
			antipopNodes.append(antipopScale)
			self.step(antipopScale, 'antipopScale')
			if stretch:
				antipopBlend.o >> antipopScale.i1
			else:
				antipopSub4.output1D >> antipopScale.i1

			lengthNormalize.outputX >> antipopScale.i2
				
			

			parent(ikhBuf, antipopGrp)
			antipopScale.o >> antipopGrp.tx

			self.ikh = ikh
			if self.dev: self.constructSelectionList(selectionName='antipopNodes', selectionList=antipopNodes)

		self.constructSelectionList(selectionName='ikControls', selectionList=self.ikCtrls)

		addAttr(ikRigGroup, ln='results', at='message', multi=True)
		for i, ctrl in enumerate(self.ikCtrls):
			ctrl.message.connect(ikRigGroup.results[i])

		return ikRigGroup


	# ============================================== BEZIER CURVE ==============================================

	def buildBezierSetup(self, transforms, shapes, ctrlTransforms=None, controller=None, defaultTangents=None, follow=True, mirror=False, indic=False, bias=True, twist=True, twistAxisChoice=0, doNeutralize=True, doStrength=False, bezChain=False, closeLoop=False):
		if self.dev: print '# buildBezierSetup'
		'''
		Mag blend should be not allow any offset except that of control
		
		editable twist axis? or twist axis based on joints vector?

		curve systems
		Standard
			tangents from each transform
		two tangents

		for each point (transforms and tangents)
			if not startRange and not endRange

		Connect magnitudeMult


		'''
		if self.dev: print '\n'
		self.sectionTag = 'bezier'

		# Error check
		# 

		# Store values

		self.magLengthMults = []

		# Rig Group
		bezierRigGroup = createNode('transform', n=self.names.get('bezierRigGroup', 'rnm_bezierRigGroup'), parent=self.rigGroup)
		self.step(bezierRigGroup, 'bezierRigGroup')
		self.publishList.append(bezierRigGroup)
		

		addAttr(bezierRigGroup, ln='results', at='message', multi=True, indexMatters=False, k=1)

		addAttr(bezierRigGroup, ln='uValues', at='compound', numberOfChildren=len(transforms), k=1)
		for i in range(len(transforms)):
			addAttr(bezierRigGroup, ln='uValues%s' % i, min=0, max=1, k=1, p='uValues')

		if controller is None:
			controller = bezierRigGroup

		# ============================= Rig Attributes =============================

		if not hasAttr(controller, 'tangentsDistanceScaling'):
			addAttr(controller, ln='tangentsDistanceScaling', softMinValue=0, softMaxValue=1, dv=1, k=1)

		if not hasAttr(controller, 'controlsVis'):
			addAttr(controller, ln='controlsVis', at='short', min=0, max=1, dv=1)
			controller.controlsVis.set(k=0, cb=1)
		
		if doNeutralize:
			if not hasAttr(controller, 'neutralizeAll'):
				addAttr(controller, ln='neutralizeAll', min=0, max=1, dv=0, k=1)
			
			

		upAxisSwitch = createNode('condition', n=self.names.get('upAxisSwitch', 'rnm_upAxisSwitch'))
		self.step(upAxisSwitch, 'upAxisSwitch')
		# Y = 1, Z = 2
		self.rigNode.upAxis.connect(upAxisSwitch.firstTerm)
		upAxisSwitch.secondTerm.set(2)
		upAxisSwitch.colorIfFalse.set((0,1,0))
		upAxisSwitch.colorIfTrue.set((0,0,1))

		# if not hasAttr(self.rigNode, 'defaultTangentsVis'):
		# 	addAttr(self.rigNode, ln='defaultTangentsVis', k=1, at='short', min=0, max=1)

		# defaultTangentsVisRev = createNode('reverse', n=self.names.get('defaultTangentsVisRev', 'rnm_defaultTangentsVisRev'))
		# self.rigNode.defaultTangentsVis.connect(defaultTangentsVisRev.iX)
		# defaultTangentsVisMult = createNode('reverse', n=self.names.get('defaultTangentsVisRev', 'rnm_defaultTangentsVisRev'))

		# self.rigNode.tangentCtrlsVis.connect(defaultTangentsVisRev.i2)

		# Controls Group
		bezierControlsGroup = createNode('transform', n=self.names.get('bezierControlsGroup', 'rnm_bezierControlsGroup'), parent=bezierRigGroup)
		self.step(bezierControlsGroup, 'bezierControlsGroup')
		self.publishList.append(bezierControlsGroup)


		staticLocGroup  =createNode('transform', n=self.names.get('staticLocGroup', 'rnm_staticLocGroup'), p=bezierRigGroup)
		self.step(staticLocGroup, 'staticLocGroup')
		



		# Split rigbuild into 2 parts
		# For Each Transform
		# For Each Length
		# ============================= For Each Transform =============================
		
		ctrls = []
		locs = []
		staticLocs = []
		tangentControls = []
		sockets = []
		curves = []
		self.pointsLists = [] # Input transforms of the curve

		for i, trans in enumerate(transforms):
			ctrlTrans = None

			# If ctrlTransforms is specified and valid, use to drive controls
			if isinstance(ctrlTransforms, list):
				if len(ctrlTransforms) == len(transforms):
					ctrlTrans = ctrlTransforms[i]
				else:
					warning('Length of ctrlTransforms list doesn\'t equal that of transforms list. Skipping')

			self.sectionTag = 'bezier'
			self.naming(i)
			self.names = utils.constructNames(self.namesDict)

			# Attribute to determine whether we're operating on the first or last transform
			rangeStart = True if i==0 else False
			rangeEnd = True if i==(len(transforms)-1) else False
			
			# Parent group for bend control and assoc tangent handles
			bendControlGroup = createNode('transform', n=self.names.get('bendControlGroup', 'rnm_bendControlGroup'), p=bezierControlsGroup)
			self.step(bendControlGroup, 'bendControlGroup')
			utils.snap(trans, bendControlGroup)
			self.publishList.append(bendControlGroup)
			bendControlGroup.r.set(0,0,0)
			bendControlGroup.s.set(1,1,1)

			# ============================= Bend Control =============================


			outlinerColor = None
			if shapes:
				if len(shapes[i].getShapes()):
					outlinerColor = shapes[i].getShapes()[0].overrideColorRGB.get()
			

			ctrl = self.createControlHeirarchy(
				transformSnap=ctrlTrans if ctrlTrans else trans,
				name=self.names.get('bendCtrl', 'rnm_bendCtrl'),
				shape=shapes[i],
				outlinerColor=outlinerColor,
				par=bendControlGroup,
				ctrlParent=bezierRigGroup,
				selectionPriority=0,
				mirror=(mirror[i] if isinstance(mirror, list) else mirror),
				mirrorStart=(mirror[i] if isinstance(mirror, list) else mirror)
				)
			ctrls.append(ctrl)
			if mirror and bezChain: 
				ctrl.mirror.get().r.set(0,0,0)
				ctrl.mirror.get().s.set(1,1,-1)
			# col.setViewportRGB(ctrl, (0.5,0.5,0.5))
			controller.controlsVis.connect(ctrl.buf.get().v)

			try:
				self.bendCtrls.append(ctrl)
			except AttributeError:
				self.bendCtrls = []
				self.bendCtrls.append(ctrl)


			# Attributes
			utils.cbSep(ctrl)
			addAttr(ctrl, ln='magnitude', softMinValue=0, softMaxValue=3, dv=1, k=1)
			ctrl.magnitude.set(1)

			if doNeutralize:
				addAttr(ctrl, ln='neutralize', min=0, max=1, dv=1, k=1)
			if doStrength:
				addAttr(ctrl, ln='strength', min=0, max=1, dv=0, k=1)
			
			if bias:
				addAttr(ctrl, ln='orientBias', min=-10, max=10, dv=10, k=1)
			utils.cbSep(ctrl)
			# Joints for main, selection handles for tangents
			if twist:
				addAttr(ctrl, ln='twist', k=1)


			# locator (to measure world position for distance)
			loc = createNode('locator', n='%s_Dist_LOC' % ctrl.nodeName(), p=ctrl)
			locs.append(loc)
			loc.hide()


			# Static locator to get normalized distance after scaling
			staticLoc = createNode('transform', n='%s_Static_LOC' % self.subNames[i], p=staticLocGroup)

			staticLocS = createNode('locator', n='%s_Static_LOCShape' % self.subNames[i], p=staticLoc)
			xform(staticLoc, ws=1, m=xform(ctrl, q=1, ws=1, m=1))
			staticLocs.append(staticLocS)
			staticLoc.hide()

			# grey indic to point bend ctrl to zero
			if indic:
				ind = utils.boneIndic( ctrl, ctrl.const.get(), blackGrey=1 )
				self.debugVis.connect(ind[0].v)

			# TODO Twist
			if twist:
				settingsNode = self.socket(ctrl)
				twistExtractorMatrix( ctrl, base=ctrl.const.get(), settingsNode=settingsNode, rigNode=self.rigNode, twistAxisChoice=twistAxisChoice)
				# if mirror:
				# 	ctrl.const.get().mult.set(-1)
			# twistExtractorMatrix( trans, trans.getParent(), settingsNode=trans, rigNode=self.rigNode, twistAxisChoice=0)
				

			# Either have bend controls follow input transforms, or just be placed at their position
			if follow:
				self.matrixConstraint(trans, ctrl.const.get(), t=1, s=1, offset=1)

				# ============================= Orient Bias ============================= 
				if bias:
					sockets.append(self.socket(trans))
					if rangeStart:

						rigSocket = self.socket(bezierControlsGroup)
						utils.snap(ctrl.const.get(), sockets[i])
						if mirror and bezChain:
							rigSocket.r.set(0,0,180)
							rigSocket.s.set(-1,1,1)
						ori = orientConstraint(rigSocket, sockets[i], ctrl.const.get())
						self.step(ori, 'ori')
						ori.interpType.set(2)
					else:
						ori = orientConstraint(sockets[i-1], sockets[i], ctrl.const.get())
						self.step(ori, 'ori')
						ori.interpType.set(2)

					oriSR = createNode('setRange', n=self.names.get('oriSR', 'rnm_oriSR'))
					oriSR.oldMin.set((-10,0,0))
					oriSR.oldMax.set((10,0,0))
					oriSR.max.set(1,0,0)
					ctrl.orientBias.connect(oriSR.vx)
					oriSR.ox >> ori.w1
					self.step(oriSR, 'oriSR')

					oriRev = createNode('reverse', n=self.names.get('oriRev', 'rnm_oriRev'))
					oriSR.ox >> oriRev.inputX
					oriRev.ox >> ori.w0
					self.step(oriRev, 'oriRev')

			# ============================= Tangent Controls =============================
			
			tangentControl0 = None
			tangentControl1 = None
			
			self.sectionTag = 'tangent'

			

			# Only need distal tangent at first point
			if rangeStart is False:
				tangentControl0 = self.createControlHeirarchy(transformSnap=(trans), name='%s_in' % self.names.get('tangentCtrl', 'rnm_tangentCtrl'), outlinerColor=outlinerColor, par=bendControlGroup, ctrlParent=ctrl, selectionPriority=0, jntBuf=True, r=False, s=False, register=False)
				boneIndic = utils.boneIndic(ctrl, tangentControl0, blackGrey=1)[0]
				# crvIndic = utils.curveIndic(ctrl, tangentControl0, blackGrey=1)[0]
				self.debugVis.connect(boneIndic.v)
				# self.globalControl.debugVis.connect(crvIndic.v)
				self.step(boneIndic, 'boneIndic')
				# self.step(crvIndic, 'crvIndic')
				self.matrixConstraint(ctrl, tangentControl0.buf.get(), t=1, r=1)
				# tangentStrengths.append(tangentStrength1)

			# Only need proximal tangent at last point
			if rangeEnd is False:
				tangentControl1 = self.createControlHeirarchy(transformSnap=(trans), name='%s_out' % self.names.get('tangentCtrl', 'rnm_tangentCtrl'), outlinerColor=outlinerColor, par=bendControlGroup, ctrlParent=ctrl, selectionPriority=0, jntBuf=True, r=False, s=False, register=False)
				boneIndic = utils.boneIndic(ctrl, tangentControl1, blackGrey=1)[0]
				# crvIndic = utils.curveIndic(ctrl, tangentControl1, blackGrey=1)[0]
				self.debugVis.connect(boneIndic.v)
				# self.globalControl.debugVis.connect(crvIndic.v)
				self.step(boneIndic, 'boneIndic')
				# self.step(crvIndic, 'crvIndic')
				self.matrixConstraint(ctrl, tangentControl1.buf.get(), t=1, r=1)
				# tangentStrengths.append(tangentStrength2)

			# Create a list of tangents for each control (can contain None on rangeStart or rangeEnd)
			tangentControls.append([tangentControl0, tangentControl1])
			
			# For tangents created, add attributes and connect
			tangentStrengths = []
			for tang in [tangentControl0, tangentControl1]:

				if not tang is None:
					viewColor = shapes[i].getShapes()[0].overrideColorRGB.get()
					col.setViewportRGB(tang, viewColor)

					# Mirror tangent axis buf
					if mirror: tang.buf.get().s.getChildren()[twistAxisChoice].set(-1)

					# Vis
					# self.rigNode.tangentCtrlsVis.connect(tang.buf.get().v)
					# tang.extra.get().v.set(l=0)
					# defaultTangentsVisMult.o.connect(tang.extra.get().v)
					# tang.extra.get().v.set(l=1)
					# defaultTangentsVisRev.ox.connect(tang.extra.get().v)

					# Attributes
					utils.cbSep(tang)
					addAttr(tang, ln='neutralizeBlend', min=0, max=1, dv=0, k=1)
					addAttr(tang, ln='magnitudeBlend', min=0, max=1, dv=1, k=1)
					# addAttr(tang, ln='distanceBasedMagnitudeMult', min=0, max=1, dv=1, k=1)
					if doStrength:
						utils.cbSep(tang)
						addAttr(tang, ln='strength', min=0, max=1, dv=0, k=0)

					# Store
					try:
						self.tangentCtrls.append(tang)
					except AttributeError:
						self.tangentCtrls = []
						self.tangentCtrls.append(tang)



					if doStrength:

						tangentStrength = createNode('transform', n=self.names.get('tangentStrength', 'rnm_tangentStrength'), p=tang.extra.get().getParent())
						self.step(tangentStrength, 'tangentStrength')
						tangentStrengths.append(tangentStrength)

						strengthMult = createNode('multiplyDivide', n=self.names.get('strengthMult', 'rnm_strengthMult'))
						self.step(strengthMult, 'strengthMult')

						tang.extra.get().t.connect(strengthMult.i1)


						strengthRange = createNode('setRange', n=self.names.get('strengthRange', 'rnm_strengthRange'))
						self.step(strengthRange, 'strengthRange')
						strengthRange.oldMin.set(0,0,0)
						strengthRange.oldMax.set(1,1,1)
						strengthRange.min.set(0.01,0.01,0.01)
						strengthRange.max.set(0.99,0.99,0.99)
					
						tang.strength.connect(strengthRange.vx)
						tang.strength.connect(strengthRange.vy)
						tang.strength.connect(strengthRange.vz)

						strengthRange.outValue.connect(strengthMult.i2)

						strengthMult.output.connect(tangentStrength.t)
				
					else:
						tangentStrengths.append(None)


		

			# ============================= For Each Length =============================
			
			if not rangeStart:
				# (0,1), (1,2), (2,3) etc
				start = i-1
				end = i

				# Example: tangentControls = [[tangentControlA0, tangentControlA1], [tangentControlB0, tangentControlB1]]
				# grab last from first list and first from next list
				# print '\n\n'
				# print 'I == %s' % i
				# print 'TANGENT CONTROLS: %s' % tangentControls
				tangents = [tangentControls[start][1], tangentControls[end][0]]
				print '\n\n\tTANGENTS: %s' % tangents

				# Get tangent start posistions if supplied, else use .33 along length
				if defaultTangents:
					defTans = [defaultTangents[start][1], defaultTangents[end][0]]
					# print 'DEFTANS'
					# print defTans



				# ============================= Orient tangents inward =============================
				# Invert orient controls so that x+ pushes out from each joint
				if mirror:
					tangentMirror = createNode('transform', n=self.names.get('tangentMirror', 'rnm_tangentMirror'), p=tangents[0].const.get())
					parent(tangents[0].extra.get(), tangentMirror)
					if doStrength:
						if tangentStrengths[0]:
							parent(tangentStrengths[0], tangentMirror)
						if tangentStrengths[1]:
							parent(tangentStrengths[1], tangentMirror)
					tangentMirror.sx.set(-1)

				else:
					tangentMirror = createNode('transform', n=self.names.get('tangentMirror', 'rnm_tangentMirror'), p=tangents[1].const.get())
					parent(tangents[1].extra.get(), tangentMirror)
					if doStrength:
						if tangentStrengths[0]:
							parent(tangentStrengths[0], tangentMirror)
						if tangentStrengths[1]:
							parent(tangentStrengths[1], tangentMirror)
					tangentMirror.sx.set(-1)
					self.step(tangentMirror, 'tangentMirror')
			

				if doNeutralize:
					# ============================= Neutralize Control  =============================
					# Consider doing this with a point constraint
					# or optimized aim constraint
					# Operates on start bend's distal tangent, and end bend's proximal tangent (within the span)
					
					# Aim transform

					aimTransStart = createNode('transform', n=self.names.get('aimTransStart', 'rnm_aimTransStart'), p=tangents[0].buf.get())
					# self.step(aimTransStart, 'aimTransStart')
					aimTransEnd = createNode('transform', n=self.names.get('aimTransEnd', 'rnm_aimTransEnd'), p=tangents[1].buf.get())
					# self.step(aimTransEnd, 'aimTransEnd')
					if mirror:
						aimVectors = [(-1,0,0), (1,0,0)]
					else:
						aimVectors = [(1,0,0), (-1,0,0)]

					neutralWorldUpStart = createNode('transform', n=self.names.get('neutralWorldUpStart', 'rnm_neutralWorldUpStart'), p=transforms[start] if follow else ctrls[start])
					self.step(neutralWorldUpStart, 'neutralWorldUpStart')
					utils.snap(aimTransStart, neutralWorldUpStart)

					neutralWorldUpEnd = createNode('transform', n=self.names.get('neutralWorldUpEnd', 'rnm_neutralWorldUpEnd'), p=transforms[end] if follow else ctrls[end])
					self.step(neutralWorldUpEnd, 'neutralWorldUpEnd')
					utils.snap(aimTransEnd, neutralWorldUpEnd)

					# transforms[end]
					# ctrls[start]
					aimStart = aimConstraint(self.socket(ctrls[end]), aimTransStart, aimVector=aimVectors[0], upVector=[0,0,1], worldUpType=2, worldUpVector=[0,0,1], worldUpObject=neutralWorldUpStart)
					aimEnd =   aimConstraint(self.socket(ctrls[start]), aimTransEnd, aimVector=aimVectors[1], upVector=[0,0,1], worldUpType=2, worldUpVector=[0,0,1], worldUpObject=neutralWorldUpEnd)
					aimTransforms = [aimTransStart, aimTransEnd]
					self.tangledAimConstraints.extend([aimStart, aimEnd])
					
					upAxisSwitch.outColor.connect(aimStart.upVector) 
					upAxisSwitch.outColor.connect(aimStart.worldUpVector)
					upAxisSwitch.outColor.connect(aimEnd.upVector)
					upAxisSwitch.outColor.connect(aimEnd.worldUpVector)
					# for each tangent, blend rotation between 0 and aim
						
					

					for q, tang in enumerate(tangents):
						self.naming(q)
						self.names = utils.constructNames(self.namesDict)

						# addAttr(tang, ln='magnitude', min=0, max=1, dv=0, k=1)

						# Global neutralize (for stretch neutralization)
						neutralizeAllBlend = createNode('blendTwoAttr', n=self.names.get('neutralizeAllBlend', 'rnm_neutralizeAllBlend'))
						ctrls[[start, end][q]].neutralize >> neutralizeAllBlend.input[0]
						neutralizeAllBlend.i[1].set(1)
						controller.neutralizeAll.connect(neutralizeAllBlend.ab)
						self.step(neutralizeAllBlend, 'neutralizeAllBlend')

						# tangentControl neutralize
						neutralizeTangentBlend = createNode('blendTwoAttr', n=self.names.get('neutralizeTangentBlend', 'rnm_neutralizeTangentBlend'))
						neutralizeAllBlend.output >> neutralizeTangentBlend.input[0]
						neutralizeTangentBlend.i[1].set(1)
						tang.neutralizeBlend.connect(neutralizeTangentBlend.ab)
						self.step(neutralizeTangentBlend, 'neutralizeTangentBlend')


						# bend control neutralize (to rotation)
						neutralBlend = createNode('blendColors', n=self.names.get('neutralBlend', 'rnm_neutralBlend'))
						aimTransforms[q].rotate.connect(neutralBlend.color1)
						neutralBlend.color2.set(0,0,0)
						neutralizeTangentBlend.output >> neutralBlend.blender
						neutralBlend.output >> tangents[q].const.get().rotate
						self.step(neutralBlend, 'neutralBlend')


						




				# ========================== Curve ============================
				# Operate on straight curve, then replace
				crv = curve(degree=1, p=[xform(transforms[start], q=1, rp=1, ws=1), xform(transforms[end], q=1, rp=1, ws=1)], n=self.names.get('crv', 'rnm_crv'))
				curves.append(crv)

				# TODO
				# Use a different control than the extra
				# Get position of tangent from position along straight line

				if defaultTangents is None:
					move(tangents[0].extra.get(), crv.getPointAtParam(0.333), ws=1, rpr=1)
					move(tangents[1].extra.get(), crv.getPointAtParam(0.666), ws=1, rpr=1)
				else:
					move(tangents[0].extra.get(), xform(defTans[0], q=1, ws=1, rp=1), ws=1)
					move(tangents[1].extra.get(), xform(defTans[1], q=1, ws=1, rp=1), ws=1)
				
				# print crv.findParamFromLength(0.333)
				ctrlDistance = createNode('distanceBetween', n=self.names.get('ctrlDistance', 'rnm_ctrlDistance'))
				self.step(ctrlDistance, 'ctrlDistance')
				locs[start].worldPosition.connect(ctrlDistance.point1)
				locs[end].worldPosition.connect(ctrlDistance.point2)

				staticDistance = createNode('distanceBetween', n=self.names.get('staticDistance', 'rnm_staticDistance'))
				self.step(staticDistance, 'staticDistance')
				staticLocs[start].worldPosition.connect(staticDistance.point1)
				staticLocs[end].worldPosition.connect(staticDistance.point2)

				bendCtrlDistNormalize = createNode('multiplyDivide', n=self.names.get('bendCtrlDistNormalize', 'rnm_bendCtrlDistNormalize'))
				self.step(bendCtrlDistNormalize, 'bendCtrlDistNormalize')
				bendCtrlDistNormalize.operation.set(2)
				ctrlDistance.distance.connect(bendCtrlDistNormalize.input1X)
				staticDistance.distance.connect(bendCtrlDistNormalize.input2X)
				# bendCtrlDistNormalize.input2X.set(ctrlDistance.distance.get())


				# Apply position to editable magnitude via blendTwoAttr nodes (can overdrive)
				# otherwise blend betwen 0 and tangent postion
				# for each tangent
				for q, tang in enumerate(tangents):

					self.naming(i, q)
					self.names = utils.constructNames(self.namesDict)

					# Distance-based magnitude blend
					magDistBlend = createNode( 'blendColors', n=self.names.get( 'magDistBlend', 'rnm_magDistBlend') )
					self.step(magDistBlend, 'magDistBlend')
					bendCtrlDistNormalize.outputX.connect(magDistBlend.color1R)
					bendCtrlDistNormalize.outputX.connect(magDistBlend.color1G)
					bendCtrlDistNormalize.outputX.connect(magDistBlend.color1B)
					magDistBlend.color2.set(1,1,1)
					controller.tangentsDistanceScaling.connect(magDistBlend.blender)
					# tang.distanceBasedMagnitude.connect(magDistBlend.blender)

					# put default position attribute in node
					
					utils.cbSep(tang.extra.get())

					# tangentDefault = createNode('transform', n=self.names.get('tangentDefault', 'rnm_tangentDefault'), p=tang.extra.get().getParent())
					# self.step(tangentDefault, 'tangentDefault')
					# self.rigNode.defaultTangentsVis.connect(tangentDefault.v)
					# tangentDefault.displayHandle.set(1, k=1)

					tangentDefault = self.createControlHeirarchy(
						name='%s_out' % self.names.get('tangentDefault', 'rnm_tangentDefault'),
						par=tang.extra.get().getParent(),
						ctrlParent=tang, 
						selectionPriority=2,
						jntBuf=True,
						outlinerColor=outlinerColor, 
						r=False,
						s=False)
					# self.rigNode.defaultTangentsVis.connect(tangentDefault.buf.get().v)
					self.rigNode.tangentCtrlsVis.connect(tangentDefault.buf.get().v)

					for attribute in [tangentDefault.rx, tangentDefault.ry, tangentDefault.rz, tangentDefault.sx, tangentDefault.sy, tangentDefault.sz, tangentDefault.v]:
						attribute.set(l=1)
				
					# addAttr(tang.extra.get(), ln='default', at='compound', numberOfChildren=3, k=1)
					# addAttr(tang.extra.get(), ln='defaultX', at='float', p='default', k=1)
					# addAttr(tang.extra.get(), ln='defaultY', at='float', p='default', k=1)
					# addAttr(tang.extra.get(), ln='defaultZ', at='float', p='default', k=1)

					tangentDefault.extra.get().t.set(tang.extra.get().translate.get())
					tangentDefaultAdd = createNode('plusMinusAverage', n=self.names.get('tangentDefaultAdd', 'rnm_tangentDefaultAdd'))
					self.step(tangentDefaultAdd, 'tangentDefaultAdd')
					tangentDefault.const.get().t.connect(tangentDefaultAdd.input3D[0])
					tangentDefault.extra.get().t.connect(tangentDefaultAdd.input3D[1])
					tangentDefault.t.connect(tangentDefaultAdd.input3D[2])
					# if mirror:
					# 	tang.defaultY.set((tang.defaultY.get() * -1))
					# 	tang.defaultZ.set((tang.defaultZ.get() * -1))

					# Magnitude blend(based on 1/3 curve param)
					# For each attr in x,y,z

					magBlends = []
					attributes = [tang.extra.get().tx, tang.extra.get().ty, tang.extra.get().tz]
					defattributes = tangentDefaultAdd.output3D.getChildren()
					
					for t, attribute in enumerate(attributes):
						# Magnitude controls
						magnitudeToggleBlend = createNode('blendTwoAttr', n='%s_%s' % ( self.names.get('magnitudeToggleBlend' ,'rnm_magnitudeToggleBlend'), (['X', 'Y', 'Z'][t]) ))
						magnitudeToggleBlend.i[0].set(0)
						defattributes[t].connect(magnitudeToggleBlend.i[1])
						tang.magnitudeBlend.connect(magnitudeToggleBlend.ab)
						# defattributes[t].set(l=1)


						magBlend = createNode('blendTwoAttr', n='%s_%s' % ( self.names.get('magBlend' ,'rnm_magBlend'), (['X', 'Y', 'Z'][t]) ))
						magBlend.i[0].set(0.001)
						magnitudeToggleBlend.o.connect(magBlend.i[1])
						# magBlend.o >> attribute
						magBlends.append(magBlend)
						self.step(magBlend, 'magBlend%s' % (q-1))
						ctrls[[start, end][q]].magnitude >> magBlend.ab
					
					# Distance multiplier input
					magMult = createNode('multiplyDivide', n=self.names.get('magMult', 'rnm_magMult'))
					self.step(magMult, 'magMult%s' % (q-1))

					magDistBlend.output.connect(magMult.input2)

					magBlends[0].o >> magMult.input1X
					magBlends[1].o >> magMult.input1Y
					magBlends[2].o >> magMult.input1Z

					magLengthMult = createNode( 'multiplyDivide', n=self.names.get( 'magLengthMult', 'rnm_magLengthMult' ) )
					self.step(magLengthMult, 'magLengthMult')
					magMult.o.connect(magLengthMult.input1)
					magLengthMult.i2.set(1,1,1)
					self.magLengthMults.append(magLengthMult)

					magLengthMult.o.connect(tang.extra.get().translate)

			# Append a list of subPoint to reorganize later
			if doStrength:
				if self.dev:
					print '\n\n\tTANGENT STRENGTHS'
					print tangentStrengths
					print tangentStrengths[0]
					print tangentStrengths[1]
				self.pointsLists.append([ctrl, tangentControl0, tangentControl1, tangentStrengths[0], tangentStrengths[1]])
			else:
				self.pointsLists.append([ctrl, tangentControl0, tangentControl1, None, None])


		skipMid = False
		# Current setup creates points along curve out of order.  Some work is required to create an ordered cv list.
		# EXAMPLE
		# self.pointsLists = 
			# [ ctrl0, 	NONE, 				tangentControl1, 	NONE, 					tangentStrengths[1] ],
			# [ ctrl1, 	tangentControl0, 	tangentControl1, 	tangentStrengths[0], 	tangentStrengths[1] ],
			# [ ctrl2, 	tangentControl0, 	NONE, 				tangentStrengths[0], 	NONE ]
		# Reorganized into:
		# pointsList = 	ctrl0, 				tangentStrengths[1], tangentControl1,
		# 				tangentControl0,	tangentStrengths[0], tangentStrengths[1], tangentControl1, 


		points = []
		pointsList = []
		for i, p in enumerate(self.pointsLists):
			# If not start or end, it's middle
			rangeMid = False if i==0 or i==(len(self.pointsLists)-1) else True

			# Format:
			# self.pointsList = [1bendCtrl, None, 1tangent1], [2bendCtrl, 2tangent0, 2tangent1], [3bendCtrl, 3tangent0, None]
			# Reordered:
			# pointsList = [1bendCtrl, 1tangent1, 2tangent0, 2bendCtrl, 2tangent1, 3tangent0, 3bendCtrl]
			
			# order of each length is tangent0, strength[0], ctrl, strength[1], tangent[1]
			reorderedList = [p[1],p[3],p[0],p[4],p[2]]
			for n, r in enumerate(reorderedList):
				if skipMid:
					if rangeMid:
						if n == 2:
							r = None

				if not r is None:
					print '%s: %s' % (n,r)
					pointsList.append(r)
					points.append(xform(r, q=1, rp=1, ws=1))

					if n == 0 or n == 4:
						if doStrength:
							reorderedList[2].strength.connect(r.strength)

			

			# 		pointsList.append(p[0])
			# 		points.append(xform(p[0], q=1, rp=1, ws=1))
			# else:
			# 	pointsList.append(p[0])
			# 	points.append(xform(p[0], q=1, rp=1, ws=1))
			# # All included
		

			# if p[2] is not None:
			# 	pointsList.append(p[2])
			# 	points.append(xform(p[2], q=1, rp=1, ws=1))


		if closeLoop:
			points.append(points[0])
			pointsList.append(pointsList[0])

		# Delete guide curves
		for crv in curves:
			delete(crv)
		
		# Create single curve
		crv = curve(degree=3, p=points, periodic=closeLoop, n=self.names.get('crv', 'rnm_crv'))
		self.step(crv, 'crv')
		self.crvs.append(crv)
		parent(crv, self.worldGroup)
		# # retrieve curve shape
		crvS = crv.getShapes()[0]
		# crvS.lineWidth.set(1.5)
		crvS.overrideEnabled.set(1)
		crvS.overrideDisplayType.set(2)
		crvS.rename('%sShape' % crv.nodeName())
		addAttr(crv, ln='offsetCurve', at='message')
		self.debugVis.connect(crv.v)
		# crv.hide()

		# Make clusters and parent
		# clsList = []
		# TODO: It feels weird to make this a class attribute. try to get around this or standardize somehow?
		curveLength = createNode('curveInfo', n=self.names.get('curveLength', 'rnm_curveLength'))
		self.curveLength = curveLength
		self.step(curveLength, 'curveLength')
		crvS.worldSpace.connect(curveLength.inputCurve)
		


		if closeLoop:
			points.remove(points[-1])
			pointsList.remove(pointsList[-1])

		# For each transform in generated pointsList, create a locator for that curve point index and connect to curve inputs.
		paramInd = 0
		q=0
		for i, point in enumerate(pointsList):

			self.naming(n=i)
			self.names = utils.constructNames(self.namesDict)
			d = float(i)/float(len(pointsList))
			d = d*crvS.maxValue.get()

			pointLoc = createNode('locator', n=self.names.get('pointLoc', 'rnm_pointLoc'), p=point)
			self.step(pointLoc, 'pointLoc')
			pointLoc.worldPosition[0].connect(crvS.controlPoints[i])
			pointLoc.hide()
			
			# If bend control, but not start/end bend control, convert parameter uValue to percentage uValue
			
			if not point.sectionTag.get() == 'tangent':
				percentageAttr = bezierRigGroup.attr('uValues%s' % q)

				# percentageAttr = bezierRigGroup.percentage[q]
				# addAttr(point, ln='percentage', min=0, max=1, k=1)
				
				if not point is pointsList[0] and not point is pointsList[-1]:


					if not hasAttr(bezierRigGroup, 'param%s' % paramInd):
						addAttr(bezierRigGroup, ln='param%s' % paramInd, min=0, max=crvS.maxValue.get(), k=1, dv=paramInd)
					addAttr(bezierRigGroup, ln='defaultPercentage%s' % paramInd, min=0, max=1, k=1, dv=paramInd)
				

					pLenS = createNode('arcLengthDimension', n=self.names.get('pLen', 'rnm_pLen'))
					pLen = pLenS.getParent()
					self.step(pLen, 'pLen')
					pLen.rename(self.names.get('pLen', 'rnm_pLen'))
					pLen.hide()
					pLen.overrideEnabled.set(1)
					pLen.overrideDisplayType.set(2)
					crvS.worldSpace.connect(pLenS.nurbsGeometry)
					parent(pLen, bezierRigGroup)
					bezierRigGroup.attr('param%s' % paramInd).connect(pLenS.uParamValue)
				

					# Mid param arcLength/curve arcLength
					midPointPercentage = createNode('multiplyDivide', n=self.names.get('midPointPercentage', 'rnm_midPointPercentage'))
					self.step(midPointPercentage, 'midPointPercentage')
					midPointPercentage.operation.set(2) # Divide
					pLenS.arcLength.connect(midPointPercentage.input1X)
					curveLength.arcLength.connect(midPointPercentage.input2X)

					bezierRigGroup.attr('defaultPercentage%s' % paramInd).set(midPointPercentage.outputX.get())
					addAttr(bezierRigGroup.attr('defaultPercentage%s' % paramInd), e=1, dv=midPointPercentage.outputX.get())
					bezierRigGroup.attr('defaultPercentage%s' % paramInd).connect(midPointPercentage.input1Y)
				
					midPointPercentage.input2Y.set(1)

					
					parameterSwitch = createNode('choice', n=self.names.get('parameterSwitch', 'rnm_parameterSwitch'))
					self.step(parameterSwitch ,'parameterSwitch')
					# parameterSwitch.i[0].set(midPointPercentage.outputX.get())
					midPointPercentage.outputY.connect(parameterSwitch.i[0])
					midPointPercentage.outputX.connect(parameterSwitch.i[1])
					parameterSwitch.o.connect(percentageAttr)

					if not hasAttr(self.rigNode, 'midPointFollow%s' % i):
						addAttr(self.rigNode, ln='midPointFollow%s' % i, at='short', min=0, max=1, dv=1, k=1)
						self.rigNode.attr('midPointFollow%s' % i).connect(parameterSwitch.selector)

					midPointFollowRev = createNode('reverse',  n=self.names.get('midPointFollowRev', 'rnm_midPointFollowRev'))
					self.step(midPointFollowRev, 'midPointFollowRev')
					self.rigNode.attr('midPointFollow%s' % i).connect(midPointFollowRev.ix)
					midPointFollowRev.ox.connect(pLenS.frozen)
					# midPointPercentage.outputY.connect(point.percentage)
				
				elif point is pointsList[0]:
					percentageAttr.set(0)
				elif point is pointsList[-1]:
					percentageAttr.set(1)

				paramInd = paramInd+2
				q=q+1

		for ctrl in ctrls:
			if defaultTangents:
				ctrl.magnitude.set(1)
				if doNeutralize:
					ctrl.neutralize.set(0)
			
			else:	
				ctrl.magnitude.set(0)
				if doNeutralize:
					ctrl.neutralize.set(1)

			if bias:
				ctrl.orientBias.set(0)

		# if self.dev:
		# 	for ctrl in ctrls:
		# 		ctrl.neutralize.set(1)
		# 		if bias:
		# 			ctrl.orientBias.set(0)

		# addAttr(bezierRigGroup, ln='controls', at='message', multi=True)
		# for i, ctrl in enumerate(self.ikCtrls):
		# 	ctrl.message.connect(bezierRigGroup.controls[i])
			
		return bezierRigGroup



	# ============================================== THREEPOINT CURVE ==============================================
	def buildMidBendCurveSetup(self, transforms, follow=True, shapes=None, controller=None, mirror=False):
		# Creates a simple bend controller from a three point curve

		if self.dev: print '\n'
		self.sectionTag = 'midBend'

		if not 1 < len(transforms) < 4:
			raise Exception('buildMidBendCurveSetup requires 2-3 transforms.')

		# Rig Group
		bendRigGroup = createNode('transform', n=self.names.get('bendRigGroup', 'rnm_bendRigGroup'), parent=self.rigGroup)
		self.step(bendRigGroup, 'bendRigGroup')
		self.publishList.append(bendRigGroup)
		

		addAttr(bendRigGroup, ln='uValues', at='compound', numberOfChildren=len(transforms), k=1)
		
		for i in range(len(transforms)):
			addAttr(bendRigGroup, ln='uValues%s' % i, min=0, max=1, k=1, p='uValues')

		addAttr(bendRigGroup, ln='results', at='message', multi=True, indexMatters=False, k=1)

		if controller is None:
			controller = bendRigGroup

		# ============================= Rig Attributes =============================

		# if not hasAttr(controller, 'controlsVis'):
		# 	addAttr(controller, ln='controlsVis', at='short', min=0, max=1, dv=1)
		# 	controller.controlsVis.set(k=0, cb=1)
		

		upAxisSwitch = createNode('condition', n=self.names.get('upAxisSwitch', 'rnm_upAxisSwitch'))
		self.step(upAxisSwitch, 'upAxisSwitch')
		# Y = 1, Z = 2
		self.rigNode.upAxis.connect(upAxisSwitch.firstTerm)
		upAxisSwitch.secondTerm.set(2)
		upAxisSwitch.colorIfFalse.set((0,1,0))
		upAxisSwitch.colorIfTrue.set((0,0,1))

		# Controls Group
		bendControlsGroup = createNode('transform', n=self.names.get('bendControlsGroup', 'rnm_bendControlsGroup'), parent=bendRigGroup)
		self.step(bendControlsGroup, 'bendControlsGroup')

		# staticLocGroup = createNode('transform', n=self.names.get('staticLocGroup', 'rnm_staticLocGroup'), p=bezierRigGroup)
		# self.step(staticLocGroup, 'staticLocGroup')
		

		# ============================= For Each Transform =============================
		
		points = []
		pointTs = []
		bendCtrls = []
		
		for i, trans in enumerate(transforms):

			self.naming(i=i)
			self.names = utils.constructNames(self.namesDict)

			# Attribute to determine whether we're operating on the first or last transform
			rangeStart = True if i==0 else False
			rangeEnd = True if i==(len(transforms)-1) else False

			
			outlinerColor = None
			if shapes:
				if len(shapes[i].getShapes()):
					outlinerColor = shapes[i].getShapes()[0].overrideColorRGB.get()
				
			# ============================= Bend Control =============================
			ctrl = self.createControlHeirarchy(
				transformSnap=trans,
				name=self.names.get('endCtrl', 'rnm_endCtrl%s' % i),
				shape=shapes[i] if shapes else None,
				outlinerColor = outlinerColor,
				par=bendControlsGroup,
				ctrlParent=bendRigGroup,
				selectionPriority=0,
				mirror=mirror,
				mirrorStart=mirror)
			# controller.controlsVis.connect(ctrl.buf.get().v)

			bendCtrls.append(ctrl)
			try:
				self.bendCtrls.append(ctrl)
			except AttributeError:
				self.bendCtrls = []
				self.bendCtrls.append(ctrl)

			points.append(ctrl)


			if follow:
				self.matrixConstraint(self.socket(trans), ctrl.const.get(), r=1, s=1)



		for i, ctrl in enumerate(bendCtrls):
			self.naming(i=i)
			self.names = utils.constructNames(self.namesDict)
			# ============================= For Each Length =============================
			rangeStart = True if i==0 else False
			rangeEnd = True if i==(len(transforms)-1) else False

			if not rangeEnd:

				ctrlStart = bendCtrls[i]
				ctrlEnd = bendCtrls[i+1]
				transStart = transforms[i]
				transEnd = transforms[i+1]

				outlinerColor = None
				if shapes:
					if len(shapes[i].getShapes()):
						outlinerColor = shapes[i].getShapes()[0].overrideColorRGB.get()
				

				# create a control in between each
				midCtrl = self.createControlHeirarchy(
				name=self.names.get('midCtrl', 'rnm_midCtrl%s' % i),
				shape=None,
				par=ctrlStart,
				ctrlParent=bendRigGroup,
				selectionPriority=2,
				mirror=mirror,
				outlinerColor = outlinerColor,
				r=False,
				s=False,
				mirrorStart=mirror)
				col.setViewportRGB(midCtrl, (1,1,1))
				# self.bendCtrlsVis.connect(midCtrl.buf.get().v)

				# lockAndHideAttributes = [
				# midCtrl.rx,
				# midCtrl.ry,
				# midCtrl.rz,
				# midCtrl.sx,
				# midCtrl.sy,
				# midCtrl.sz,
				# ]
				# for attrb in lockAndHideAttributes:
				# 	attrb.set(l=1, k=0)


				aimOri = createNode('transform', n=self.names.get('aimOri', 'rnm_aimOri'), p=ctrlStart)
				self.step(aimOri, 'aimOri')
				
				aimConst = aimConstraint(self.socket(ctrlEnd), aimOri, aimVector=(1,0,0), upVector=(0,1,0), worldUpType=2, worldUpVector=(0,1,0), worldUpObject=transStart if follow else ctrlStart)
				self.step(aimConst, 'aimConst')
				self.tangledAimConstraints.append(aimConst)

				pnt = pointConstraint(self.socket(ctrlStart), self.socket(ctrlEnd), midCtrl.const.get())
				self.step(pnt, 'pnt')

				ori = self.matrixConstraint(aimOri, midCtrl.const.get(), t=0, r=1)
				# self.step(ori, 'ori')

				try:
					self.midCtrls.append(midCtrl)
				except AttributeError:
					self.midCtrls = []
					self.midCtrls.append(midCtrl)


				points.insert(points.index(ctrlStart)+1, midCtrl)
				

		# Append world transforms
		if self.dev: print '\n'
		for point in points:
			if self.dev: print point.nodeName()
			pointTs.append(xform(point, q=1, ws=1, t=1))


		# create curve
		crv = curve(degree=3, p=pointTs, n=self.names.get('crv', 'rnm_crv'))
		self.step(crv, 'crv')
		self.crvs.append(crv)
		parent(crv, self.worldGroup)
		# # retrieve curve shape
		crvS = crv.getShapes()[0]
		# crvS.lineWidth.set(1.5)
		crvS.overrideEnabled.set(1)
		crvS.overrideDisplayType.set(2)
		crvS.rename('%sShape' % crv.nodeName())
		addAttr(crv, ln='offsetCurve', at='message')
		self.debugVis.connect(crv.v)
			# crv.hide()

		# Attach world transforms directly to curve
		for i, point in enumerate(points):
			self.naming(n=i)
			self.names = utils.constructNames(self.namesDict)

			pointLoc = createNode('locator', n=self.names.get('pointLoc', 'rnm_pointLoc'), p=point)
			self.step(pointLoc, 'pointLoc')
			pointLoc.worldPosition[0].connect(crvS.controlPoints[i])
			pointLoc.hide()



		curveLength = createNode('curveInfo', n=self.names.get('curveLength', 'rnm_curveLength'))
		self.curveLength = curveLength
		self.step(curveLength, 'curveLength')
		crvS.worldSpace.connect(curveLength.inputCurve)

		paramInd = 0
		# Get parameter percentage
		for i, ctrl in enumerate(bendCtrls):
			self.naming(i=i)
			self.names = utils.constructNames(self.namesDict)

			rangeStart = True if i==0 else False
			rangeEnd = True if i==(len(transforms)-1) else False

			percentageAttr = bendRigGroup.attr('uValues%s' % i)
			
			if not rangeStart and not rangeEnd:

				if not hasAttr(bendRigGroup, 'param%s' % paramInd):
					addAttr(bendRigGroup, ln='param%s' % paramInd, min=0, max=crvS.maxValue.get(), k=1, dv=paramInd)
				addAttr(bendRigGroup, ln='defaultPercentage%s' % paramInd, min=0, max=1, k=1, dv=paramInd)

				pLenS = createNode('arcLengthDimension', n=self.names.get('pLen', 'rnm_pLen'))
				pLen = pLenS.getParent()
				self.step(pLen, 'pLen')
				pLen.rename(self.names.get('pLen', 'rnm_pLen'))
				pLen.hide()
				pLen.overrideEnabled.set(1)
				pLen.overrideDisplayType.set(2)
				crvS.worldSpace.connect(pLenS.nurbsGeometry)
				parent(pLen, bendRigGroup)
				bendRigGroup.attr('param%s' % paramInd).connect(pLenS.uParamValue)
			

				# Mid param arcLength/curve arcLength
				midPointPercentage = createNode('multiplyDivide', n=self.names.get('midPointPercentage', 'rnm_midPointPercentage'))
				self.step(midPointPercentage, 'midPointPercentage')
				midPointPercentage.operation.set(2) # Divide
				pLenS.arcLength.connect(midPointPercentage.input1X)
				curveLength.arcLength.connect(midPointPercentage.input2X)

				bendRigGroup.attr('defaultPercentage%s' % paramInd).set(midPointPercentage.outputX.get())
				# addAttr(bendRigGroup.attr('defaultPercentage%s' % paramInd), e=1, dv=midPointPercentage.outputX.get())
				bendRigGroup.attr('defaultPercentage%s' % paramInd).connect(midPointPercentage.input1Y)
				

				midPointPercentage.input2Y.set(1)

				
				parameterSwitch = createNode('choice', n=self.names.get('parameterSwitch', 'rnm_parameterSwitch'))
				self.step(parameterSwitch ,'parameterSwitch')
				# parameterSwitch.i[0].set(midPointPercentage.outputX.get())
				midPointPercentage.outputY.connect(parameterSwitch.i[0])
				midPointPercentage.outputX.connect(parameterSwitch.i[1])
				parameterSwitch.o.connect(percentageAttr)

				if not hasAttr(self.rigNode, 'midPointFollow%s' % i):
					addAttr(self.rigNode, ln='midPointFollow%s' % i, at='short', min=0, max=1, dv=1, k=1)
					self.rigNode.attr('midPointFollow%s' % i).connect(parameterSwitch.selector)

				midPointFollowRev = createNode('reverse',  n=self.names.get('midPointFollowRev', 'rnm_midPointFollowRev'))
				self.step(midPointFollowRev, 'midPointFollowRev')
				self.rigNode.attr('midPointFollow%s' % i).connect(midPointFollowRev.ix)
				midPointFollowRev.ox.connect(pLenS.frozen)
				# midPointPercentage.outputY.connect(point.percentage)
			
				paramInd = paramInd + 2

			elif rangeStart:
				percentageAttr.set(0)
				paramInd = paramInd + 1
			elif rangeEnd:
				percentageAttr.set(1)
				paramInd = paramInd + 1



		return bendRigGroup


	# ========================================== IK SPLINE ==============================================
	def buildIKSplineSetup(self, crv, points, shapes=None, nameVar=None, mirror=False, rigGroup=None, selectionPriority=0, twist=True):
		if self.dev: print '# buildIKSplineSetup'

		self.sectionTag = 'splineIK'

		if not rigGroup:
			rigGroup = self.rigGroup

		# IK Group
		ikRigSplineGroup = createNode('transform', n=self.names.get('ikRigSplineGroup', 'rnm_ikRigSplineGroup'), parent=rigGroup)
		self.step(ikRigSplineGroup, 'ikRigSplineGroup')
		self.publishList.append(ikRigSplineGroup)

		addAttr(ikRigSplineGroup, ln='twistStart', k=1)
		addAttr(ikRigSplineGroup, ln='twistEnd', k=1)

		addAttr(ikRigSplineGroup, ln='results', at='message', multi=True, indexMatters=False, k=1)


		# TWIST
		upNode = createNode('transform', n=self.names.get('upNode', 'rnm_upNode'), p=ikRigSplineGroup)
		self.step(upNode, 'upNode', freeze=False)
		freezeAttrs = [ upNode.translateX, upNode.translateY, upNode.translateZ, upNode.scaleX, upNode.scaleY, upNode.scaleZ]
		for attr in freezeAttrs:
			attr.set(l=1, k=0)

		upAxisCond = createNode('condition', n=self.names.get('upAxisCond', 'rnm_upAxisCond'))
		self.step(upAxisCond, 'upAxisCond')
		self.rigNode.upAxis >> upAxisCond.firstTerm
		upAxisCond.secondTerm.set(1)
		upAxisCond.colorIfFalse.set([0,1,0])
		upAxisCond.colorIfTrue.set([0,0,1])

		upAxisIkhCond = createNode('condition', n=self.names.get('upAxisIkhCond', 'rnm_upAxisIkhCond'))
		self.step(upAxisIkhCond, 'upAxisIkhCond')
		self.rigNode.upAxis >> upAxisIkhCond.firstTerm
		upAxisIkhCond.secondTerm.set(1)
		upAxisIkhCond.colorIfFalseR.set(0)
		upAxisIkhCond.colorIfTrueR.set(3)
		
		rootVector = createNode('vectorProduct', n=self.names.get('rootVector', 'rnm_rootVector'))
		self.step(rootVector, 'rootVector')
		upNode.worldMatrix.connect(rootVector.matrix)
		rootVector.operation.set(3)
		# rootVector.input1.set([0,0,1])
		upAxisCond.outColor >> rootVector.input1

		twistReduceMult = createNode('multDoubleLinear', n=self.names.get('twistReduceMult', 'rnm_twistReduceMult'))
		self.step(twistReduceMult, 'twistReduceMult')
		ikRigSplineGroup.twistEnd.connect(twistReduceMult.i1)
		numPoints = len(points)
		print 'REDUCE VAL = %s' % (float(numPoints-1) / float(numPoints))
		print (len(points)-1)
		twistReduceMult.i2.set(float(numPoints-1) / float(numPoints))

		endTwistRestoreSub = createNode('plusMinusAverage', n=self.names.get('endTwistRestoreSub', 'rnm_endTwistRestoreSub'))
		self.step(endTwistRestoreSub, 'endTwistRestoreSub')
		ikRigSplineGroup.twistEnd.connect(endTwistRestoreSub.input1D[0])
		twistReduceMult.o.connect(endTwistRestoreSub.input1D[1])
		endTwistRestoreSub.operation.set(2)

		# JOINTS
		jointsGroup = createNode('transform', n=self.names.get('jointsGroup', 'rnm_jointsGroup'), parent=ikRigSplineGroup)
		self.step(jointsGroup, 'jointsGroup')
		jointsGroup.hide()
		
		splineJnts = []
		for i, point in enumerate(points):
			self.naming(n=i)
			self.names = utils.constructNames(self.namesDict)

			splineJnt = createNode('joint', n=self.names.get('splineJnt', 'rnm_splineJnt#'), p=(splineJnts[i-1] if i else jointsGroup))
			utils.snap(point, splineJnt)
			splineJnts.append(splineJnt)
			self.step(splineJnt, 'splineJnt', freeze=False)
			if not self.dev: splineJnt.hide()
			makeIdentity(splineJnt, apply=1, t=1, r=1, s=1, n=0, pn=1)
			splineJnt.message.connect(ikRigSplineGroup.results, nextAvailable=True)
			col.setViewportRGB(splineJnt, (0,1,1))


		
		# Returns shortName string when there's a name clash.  '#' should prevent further issues
		ikh, eff = ikHandle(sj=splineJnts[0], ee=splineJnts[-1], createCurve=0, parentCurve=0, curve=crv, sol='ikSplineSolver', snapHandleToEffector=1, rootTwistMode=1, n=self.names.get('ikh','rnm_ikh#'))
		if len(ls(ikh)) > 1:
			raise Exception('Ik handle name clash')
		ikh = PyNode(ikh)
		self.step(ikh, 'ikh')
		ikh.hide()
		parent(ikh, ikRigSplineGroup)


		eff = PyNode(eff)
		rename(eff, self.names.get('eff', 'rnm_eff'))
		self.step(eff, 'eff')

		ikh.dTwistControlEnable.set(1)

		ikh.dWorldUpType.set(6) # Vector(Start/End)
		upAxisIkhCond.outColorR >> ikh.dWorldUpAxis
		ikh.dTwistValueType.set(1) # Start/End (Try Ramp?)

		ikRigSplineGroup.twistStart.connect(ikh.dTwistStart)
		# ikRigSplineGroup.twistEnd.connect(ikh.dTwistEnd)
		twistReduceMult.output.connect(ikh.dTwistEnd)

		rootVector.output.connect(ikh.dWorldUpVector)
		rootVector.output.connect(ikh.dWorldUpVectorEnd)

		endTwistRestoreSub.output1D.connect(splineJnts[-1].rotateX)

		if twist:
			self.twistAdds = []
			# startTwist = parametricCurveRigGroup.attr('twistInput%sStart' % i)
			# endTwist = parametricCurveRigGroup.attr('twistInput%sEnd' % i)

			# Use pma for each curve so that twist can have an indeterminate number of inputs.
			twistAdd = createNode('plusMinusAverage', n=self.names.get('twistAdd', 'rnm_twistAdd'))
			self.twistAdds.append(twistAdd)
			self.step(twistAdd, 'twistAdd')


			twistAddOutput2D = twistAdd.output2D.getChildren()
			twistAddOutput2D[0].connect(ikRigSplineGroup.twistStart)
			twistAddOutput2D[1].connect(ikRigSplineGroup.twistEnd)


			# self.twistAdds[0].output2D.getChildren()[0].connect(ikSplineRig.twistStart)
			# self.twistAdds[0].output2D.getChildren()[1].connect(ikSplineRig.twistEnd)



		return ikRigSplineGroup


	# ============================================== PARAMETRIC CURVE ==============================================
	def buildParametricCurveRigSetup(self, crv, paramList=None, paramRange=None, nameVar=None, numJoints=None, mirror=False, par=None, const=None, stretch=True):
		if self.dev: print '# buildParametricCurveRigSetup'
		# TODO
		# It'd be better to be allowed to set up multiple partitions at once somehow.  This is kinda unfinished otherwise
		# So there could be an up axis
		self.sectionTag = 'parametric'
		# Given a curve, create a collection of joints along the length tied with a 
		if self.dev: print '\nbuildParametricCurveRigSetup'


		if not any([numJoints, paramList]):
			# if self.dev: warning('No input parameters for buildParametricCurveRigSetup. Skipping....')
			# return None
			raise Exception('No input parameters for buildParametricCurveRigSetup.')

		if numJoints and paramList:
			# Using paramList
			warning('More than one initilization paramter used for buildParametricCurveRigSetup. Use either paramList or numJoints.')
		
		# If numJoints
		if numJoints and not paramList:
			paramList = []
			for i in range(numJoints):
				d = float(i)
				upperLim = float(numJoints)
				paramList.append(d/upperLim)
		
		# Default Parent
		if par is None:
			par = self.rigGroup



		curvePathGroup = createNode('transform', n=self.names.get('curvePathGroup', 'rnm_curvePathGroup'), parent=par)
		self.step(curvePathGroup, 'curvePathGroup')
		self.publishList.append(curvePathGroup)
		addAttr(curvePathGroup, ln='startPoint', min=0, max=1, dv=0, k=1)
		addAttr(curvePathGroup, ln='endPoint', min=0, max=1, dv=1, k=1)
		addAttr(curvePathGroup, ln='startTwist', dv=0, k=1)
		addAttr(curvePathGroup, ln='endTwist', dv=0, k=1)

		edgeRange = createNode('setRange', n=self.names.get('edgeRange', 'rnm_edgeRange'))
		curvePathGroup.startPoint.connect(edgeRange.valueX)
		curvePathGroup.endPoint.connect(edgeRange.valueY)
		edgeRange.min.set(0.001,0.001,0.001)
		edgeRange.max.set(0.999,0.999,0.999)
		edgeRange.oldMin.set(0,0,0)
		edgeRange.oldMax.set(1,1,1)
		startRange = edgeRange.outValueX
		endRange = edgeRange.outValueY
		self.step(edgeRange, 'edgeRange')

		curveLengthNormalize = createNode('multiplyDivide', n=self.names.get('curveLengthNormalize', 'rnm_curveLengthNormalize'))
		self.step(curveLengthNormalize, 'curveLengthNormalize')
		curveLengthNormalize.operation.set(2)
		# try:
		curveLengthNormalize.input2X.set(self.curveLength.arcLength.get())
		# except:
		# 	self.curveLength = createNode('curveInfo', n=self.names.get('curveLength', 'rnm_curveLength'))
		# 	self.step(self.curveLength, 'curveLength')
		# 	crv.getShapes()[0].worldSpace.connect(self.curveLength.inputCurve)
		# 	curveLengthNormalize.input2X.set(self.curveLength.arcLength.get())

		self.curveLength.arcLength.connect(curveLengthNormalize.input1X)


		ctrls = []
		for i, param in enumerate(paramList):

			self.naming(i=nameVar, n=i)
			self.names = utils.constructNames(self.namesDict)
			# param = 0.333

			# paramDiv = createNode('multiplyDivide', n=self.names.get('paramDiv', 'rnm_paramDiv'))
			# self.step(paramDiv, 'paramDiv')
			# paramDiv.operation.set(2)
			# paramDiv.i2x.set(1)
			# paramDiv.i1x.set(param)
			if self.dev:
				print 'PARAM'
				print param
			# Set range of parameter input to whatever the input setting is.  Used for partitioning out curve into multiple joint groups
			paramRange = createNode('setRange', n=self.names.get('paramRange', 'rnm_paramRange'))
			startRange.connect(paramRange.minX)
			endRange.connect(paramRange.maxX)
			paramRange.oldMin.set(0,0,0)
			paramRange.oldMax.set(1,1,1)
			paramRange.valueX.set(param)
			self.step(paramRange, 'paramRange')

			if nameVar:
				newNameVar = '_%s_' % nameVar
			else:
				newNameVar = ''
			mp = createNode('motionPath', n=self.names.get('mp', 'rnm_mp'))
			self.step(mp, 'mp')
			crv.getShapes()[0].worldSpace[0].connect(mp.geometryPath)
			mp.fractionMode.set(True)
			# mp.follow.set(False)
			paramRange.outValueX.connect(mp.u)
			mp.setFollow(False)
			# Dont need rotation
			# mp.worldUpType.set(2)
			# mp.inverseUp.set(False)
			# mp.inverseFront.set(mirror)
			# mp.frontAxis.set(0)
			# mp.worldUpVector.set((0,0,1))
			# mp.upAxis.set(2)

			ctrlParent = curvePathGroup
			try:
				if len(self.offsetCtrls):
					ctrlParent = self.offsetCtrls[-1]
				else:
					ctrlParent = self.rigGroup
			except:
				ctrlParent = curvePathGroup


			ctrl = self.createControlHeirarchy(name=self.names.get('offset', 'rnm_offset'), selectionPriority=2, ctrlParent=ctrlParent, par=curvePathGroup, outlinerColor=(0,0,0))

			try:
				self.offsetCtrls.append(ctrl)
			except AttributeError:
				self.offsetCtrls = []
				self.offsetCtrls.append(ctrl)


			ctrls.append(ctrl)

			# Twist Input
			addAttr(ctrl.const.get(), ln='parameter', k=1)
			addAttr(ctrl.const.get(), ln='resultTwist', k=1)
			addAttr(ctrl.const.get(), ln='up', at='message', k=1)
			curvePathGroup.message.connect(ctrl.const.get().up)
			ctrl.const.get().parameter.set(param)
			ctrl.const.get().parameter.connect(paramRange.valueX)

			# Twist Param Rev
			twistParamRev = createNode('reverse', n=self.names.get('twistParamRev', 'rnm_twistParamRev'))
			self.step(twistParamRev, 'twistParamRev')


			# Twist Mults
			twistStartMult = createNode('multDoubleLinear', n=self.names.get('twistStartMult', 'rnm_twistStartMult'))
			ctrl.const.get().parameter.connect(twistParamRev.inputX)
			twistParamRev.outputX.connect(twistStartMult.i1)
			curvePathGroup.startTwist.connect(twistStartMult.i2)
			self.step(twistStartMult, 'twistStartMult')


			twistEndMult = createNode('multDoubleLinear', n=self.names.get('twistEndMult', 'rnm_twistEndMult'))
			ctrl.const.get().parameter.connect(twistEndMult.i1)
			curvePathGroup.endTwist.connect(twistEndMult.i2)
			self.step(twistEndMult, 'twistEndMult')


			twistAdd = createNode('addDoubleLinear', n=self.names.get('twistAdd', 'rnm_twistAdd'))
			twistStartMult.o.connect(twistAdd.input1)
			twistEndMult.o.connect(twistAdd.input2)
			self.step(twistAdd, 'twistAdd')

			twistAdd.output.connect(ctrl.const.get().resultTwist)
			



			# Convert MP worldspace to CONST localSpace.
			# Translate
			# TODO
			# Since I'm not actually using rotation or scale, this can probably be something less complicated.
			cmpMtrx = createNode('composeMatrix', n=self.names.get('cmpMtrx', 'rnm_cmpMtrx'))
			self.step(cmpMtrx, 'cmpMtrx')
			mp.allCoordinates.connect(cmpMtrx.inputTranslate)
			mp.rotate.connect(cmpMtrx.inputRotate)

			multMtrx = createNode('multMatrix', n=self.names.get('multMtrx', 'rnm_multMtrx'))
			self.step(multMtrx, 'multMtrx')
			cmpMtrx.outputMatrix.connect(multMtrx.matrixIn[0])
			ctrl.const.get().parentInverseMatrix.connect(multMtrx.matrixIn[1])

			decmpMtrx = createNode('decomposeMatrix', n=self.names.get('decmpMtrx', 'rnm_decmpMtrx'))
			self.step(decmpMtrx, 'decmpMtrx')
			multMtrx.matrixSum.connect(decmpMtrx.inputMatrix)
			
			# Move buf into default position and then constrain const
			# Buff
			# # translate
			# ctrl.buf.get().t.set(decmpMtrx.outputTranslate.get())
			decmpMtrx.outputTranslate.connect(ctrl.const.get().translate)
			
			# # translate
			# # rotate
			# aim = aimConstraint(ctrls[i-1], ctrl.const.get(), aimVector=(1,0,0), upVector=(0,1,0), worldUpVector=(0,1,0), worldUpObject=par, worldUpType='objectRotation')
			# TODO: Scale

			# jnt = createNode('joint', n=self.names.get('jnt', 'rnm_jnt%s%s' % (nameVar, i)), p=ctrl)
			# jnt.hide()
			# jnt.displayLocalAxis.set(1)

			volumeMult = createNode('multiplyDivide', n=self.names.get('volumeMult', 'rnm_volumeMult'))
			self.step(volumeMult, 'volumeMult')

			addAttr(ctrl, ln='volumeMult', nn='Multiply Volume', at='compound', numberOfChildren=3, k=1)
			addAttr(ctrl, ln='volumeMultX', nn='Multiply VolumeX', softMinValue=1, dv=1, at='float', parent='volumeMult', k=1)
			addAttr(ctrl, ln='volumeMultY', nn='Multiply VolumeY', softMinValue=1, dv=1, at='float', parent='volumeMult', k=1)
			addAttr(ctrl, ln='volumeMultZ', nn='Multiply VolumeZ', softMinValue=1, dv=1, at='float', parent='volumeMult', k=1)

			# Scale
			curveLengthNormalize.outputX.connect(volumeMult.input1X)
			curveLengthNormalize.outputX.connect(volumeMult.input1Y)
			curveLengthNormalize.outputX.connect(volumeMult.input1Z)
			ctrl.volumeMult.connect(volumeMult.input2)


			# volumeMult

		if hasAttr(self.rigNode, 'offsetCtrlsVis'):
			self.rigNode.offsetCtrlsVis.connect(curvePathGroup.v)
		# return curvePathGroup

		# def buildJointsAimTwistSetup(self, curveGroups, mirror):
		

	# ============================================== PARAMETRIC CURVE PARTITION ==============================================
	def buildCurvePartitionsSetup(self, crv, partitionParams=None, paramLists=None, constraintTargets=None, nameVars=None, numJointsList=None, mirror=False, stretch=True, upAxisSwitch=True, scale=False, twist=True, rotationStyle='aim', bindEnd=True, createOffsetControls=True):
		if self.dev: print '\nbuildCurvePartitionsSetup'

		# Error check
		# if bindEnd: bindEnd = 1
		# else: bindEnd = 0
		# Check curve type
		# If string find via name (does this need to be a unicode class ..?)
		if isinstance(crv, str):
			if len(ls(crv)) > 1:
				raise Exception('More than one object matches name: %s' % crv)
			if len(ls(crv)) == 0:
				raise Exception('No object matches name: %s' % crv)
			crv = ls(crv)[0]

		elif not isinstance(crv, PyNode):
			raise Exception('Curve input is not a PyNode: %s' % crv)


		partitions = None # Declare empty so that if comparison after first addition
		# numJointsList
		if numJointsList:
			if not isinstance(numJointsList, list):
				numJointsList = [numJointsList]


			# Test list length against others
			if partitions is None:
				partitions = len(numJointsList)

			if self.dev: print len(numJointsList)
			if len(numJointsList) != partitions:
				raise Exception('Partition lists length mismatch: numJointsList (%s)' % len(numJointsList))


			# Check each numJointsList
			for numJoints in numJointsList:
				if not isinstance(numJoints, int):
					raise Exception('Unexpected input for numJoints: %s' % numJoints)


		# paramLists
		if paramLists:
			if not isinstance(paramLists, list):
				paramLists = [paramLists]


			# Test list length against others
			if partitions is None:
				partitions = len(paramLists)

			if self.dev: print len(paramLists)
			if len(paramLists) != partitions:
				raise Exception('Partition lists length mismatch: paramLists (%s)' % len(paramLists))


			# Check each paramLists
			for paramList in paramLists:
				if not isinstance(paramList, list):
					raise Exception('Unexpected input for paramList: %s' % paramList)

		# constraintTargets
		if constraintTargets:
			if not isinstance(constraintTargets, list):
				constraintTargets = [constraintTargets]

			# Test list length against others
			if partitions is None:
				partitions = len(constraintTargets)

			if self.dev: print len(constraintTargets)
			if len(constraintTargets) != partitions:
				raise Exception('Partition lists length mismatch: constraintTargets (%s)' % len(constraintTargets))

			# Check each constraintTarget
			for constraintTarget in constraintTargets:
				if not isinstance(constraintTarget, PyNode):
					raise Exception('Unexpected input for constraintTarget: %s' % constraintTarget)

		
		# uValue data
		if not any([numJointsList, paramLists]):
			raise Exception('No input parameters for buildCurvePartitionsSetup.')

		if all([numJointsList, paramLists]):
			if all([len(numJointsList), len(paramLists)]):
				warning('Only one uValue input requried (numJointsList OR paramLists).  Going with paramLists.')

		# if bindEnd:
		# If partitionsJoints, convert all in list to parameters
		if numJointsList and not paramLists:
			paramLists = []
			for q, numJoints in enumerate(numJointsList):
				paramList = []
				for i in range(numJoints):
					paramList.append(float(i)/float(numJoints))
				
				if bindEnd and q+1 is len(numJointsList):
					paramList.append(1)
				paramLists.append(paramList)
		

		if partitionParams is None:
			partitionParams = []
			partitionParams.append(0)
			for p in range(partitions):
				if not p == 0:
					partitionParams.append(float(p)/float(partitions))
			if self.dev: print partitionParams

		if not partitions == len(partitionParams)-1:
			if self.dev:
				print 'Partitions: %s' % partitions
				print 'Partition Type: %s' % type(partitions)
				print 'PartitionParams-1: %s' % (len(partitionParams)-1)
				print 'PartitionParams Type: %s' % type(len(partitionParams)-1)

			raise Exception('partitionParams should indicate start, middle, and end points, and number of inputs should equal number of partitions-1. (EX: 2 partitions, partitionParam = (0, 0.5, 1))')
			#  (2 partitions, partitionParam = (0, 0.5, 1))
			#  (3 partitions, partitionParam = (0, 0.33, 0.66, 1))

		# Error check end

		# Rig group
		parametricCurveRigGroup = createNode('transform', n=self.names.get('parametricCurveRigGroup', 'rnm_parametricCurveRigGroup'), parent=self.rigGroup)
		self.step(parametricCurveRigGroup, 'parametricCurveRigGroup')
		self.publishList.append(parametricCurveRigGroup)
		addAttr(parametricCurveRigGroup, ln='results', at='message', multi=True, indexMatters=False, k=1)

		# attributes
		addAttr(parametricCurveRigGroup, ln='partitionParameters', at='compound', numberOfChildren=len(partitionParams), k=1)
		for n, p in enumerate(partitionParams):
			addAttr(parametricCurveRigGroup, ln='partitionParameter%s' % n, nn='Partition Parameter %s' % n, min=0, max=1, dv=p, parent='partitionParameters', k=1)
		
		addAttr(parametricCurveRigGroup, ln='twistInputs', at='compound', numberOfChildren=(partitions*2), k=1)
		addAttr(parametricCurveRigGroup, ln='scaleInputs', at='compound', numberOfChildren=(partitions*2), k=1)
		for n in range(partitions):
			if twist:
				addAttr(parametricCurveRigGroup, ln='twistInput%sStart' % n, nn='Twist Input %s Start' % n, dv=0, parent='twistInputs', k=1)
				addAttr(parametricCurveRigGroup, ln='twistInput%sEnd' % n, nn='Twist Input %s End' % n, dv=0, parent='twistInputs', k=1)
			if scale:
				addAttr(parametricCurveRigGroup, ln='scaleInput%sStart' % n, nn='Scale Input %s Start' % n, dv=0, parent='scaleInputs', k=1)
				addAttr(parametricCurveRigGroup, ln='scaleInput%sEnd' % n, nn='Scale Input %s End' % n, dv=0, parent='scaleInputs', k=1)


		upAxisSwitch = createNode('condition', n=self.names.get('upAxisSwitch', 'rnm_upAxisSwitch'))
		self.step(upAxisSwitch, 'upAxisSwitch')
		# Y = 1, Z = 2
		self.rigNode.upAxis.connect(upAxisSwitch.firstTerm)
		upAxisSwitch.secondTerm.set(2)
		upAxisSwitch.colorIfFalse.set((0,1,0))
		upAxisSwitch.colorIfTrue.set((0,0,1))


		curveGroups = []
		ctrls = []

		mps = []

		# For each partition
		for i in range(partitions):
			self.naming(n=i)
			self.names = utils.constructNames(self.namesDict)

			if twist:
				startTwist = parametricCurveRigGroup.attr('twistInput%sStart' % i)
				endTwist = parametricCurveRigGroup.attr('twistInput%sEnd' % i)

			# Group
			curvePathGroup = createNode('transform', n=self.names.get('curvePathGroup', 'rnm_curvePathGroup'), parent=parametricCurveRigGroup)
			self.step(curvePathGroup, 'curvePathGroup')
			curveGroups.append(curvePathGroup)
			
			if constraintTargets:
				self.matrixConstraint(constraintTargets[i], curvePathGroup, t=1, r=1, s=1, offset=False)

			# Keep start and end values from actually reaching the very ends.  They get a little weird there.
			edgeRange = createNode('setRange', n=self.names.get('edgeRange', 'rnm_edgeRange'))
			self.step(edgeRange, 'edgeRange')

			parametricCurveRigGroup.attr('partitionParameter%s' % i).connect(edgeRange.valueX)
			parametricCurveRigGroup.attr('partitionParameter%s' % (i+1)).connect(edgeRange.valueY)
			edgeRange.min.set(0.001,0.001,0.001)
			edgeRange.max.set(0.999,0.999,0.999)
			edgeRange.oldMin.set(0,0,0)
			edgeRange.oldMax.set(1,1,1)
			startRange = edgeRange.outValueX
			endRange = edgeRange.outValueY

			# curveLengthNormalize = createNode('multiplyDivide', n=self.names.get('curveLengthNormalize', 'rnm_curveLengthNormalize'))
			# self.step(curveLengthNormalize, 'curveLengthNormalize')
			# curveLengthNormalize.operation.set(2)
			
			# # Create curveinfo node if it hasnt been created yet
			# try:
			# 	curveLengthNormalize.input2X.set(self.curveLength.arcLength.get())
			# except:
			# 	self.curveLength = createNode('curveInfo', n=self.names.get('curveLength', 'rnm_curveLength'))
			# 	self.step(self.curveLength, 'curveLength')
			# 	crv.getShapes()[0].worldSpace.connect(self.curveLength.inputCurve)
			# 	curveLengthNormalize.input2X.set(self.curveLength.arcLength.get())

			# self.curveLength.arcLength.connect(curveLengthNormalize.input1X)

			# for param in paramLists[i]:
			# 	print param
			


			# Per joint
			for j, param in enumerate(paramLists[i]):
				self.naming(n=j, i=i)
				self.names = utils.constructNames(self.namesDict)

				# Set range of parameter input to whatever the input setting is.  Used for partitioning out curve into multiple joint groups
				paramRange = createNode('setRange', n=self.names.get('paramRange', 'rnm_paramRange'))
				startRange.connect(paramRange.minX)
				endRange.connect(paramRange.maxX)
				paramRange.oldMin.set(0,0,0)
				paramRange.oldMax.set(1,1,1)
				paramRange.valueX.set(param)
				self.step(paramRange, 'paramRange')

				# if nameVar:
				# 	newNameVar = '_%s_' % nameVar
				# else:
				# 	newNameVar = ''

				mp = createNode('motionPath', n=self.names.get('mp', 'rnm_mp'))
				self.step(mp, 'mp')
				crv.getShapes()[0].worldSpace[0].connect(mp.geometryPath)
				mp.fractionMode.set(True)
				# mp.follow.set(False)
				mp.setFollow(False)
				paramRange.outValueX.connect(mp.u)
				mps.append(mp)

				# Offset Control
				ctrlParent = parametricCurveRigGroup
				try:
					if len(self.offsetCtrls):
						ctrlParent = self.offsetCtrls[-1]
					else:
						ctrlParent = self.rigGroup
				except:
					ctrlParent = parametricCurveRigGroup

			
				ctrl = self.createControlHeirarchy(
					name=self.names.get('offset', 'rnm_offset'), 
					selectionPriority=(2 if createOffsetControls else 0), 
					register=(True if createOffsetControls else False), 
					ctrlParent=ctrlParent, 
					outlinerColor = (0,0,0),
					par=curvePathGroup)
				# ctrl.displayLocalAxis.set(1)
					
				ctrls.append(ctrl)

				if createOffsetControls:
					try:
						self.offsetCtrls.append(ctrl)
					except AttributeError:
						self.offsetCtrls = []
						self.offsetCtrls.append(ctrl)


				# Twist Input
				addAttr(ctrl.const.get(), ln='parameter', k=1)
				addAttr(ctrl.const.get(), ln='resultTwist', k=1)
				addAttr(ctrl.const.get(), ln='up', at='message', k=0)

				ctrl.const.get().parameter.set(param)
				ctrl.const.get().parameter.connect(paramRange.valueX)
				curvePathGroup.message.connect(ctrl.const.get().up)

				if twist:
					# Multiply start and end twist by each joint's uValue parameter.
					# TODO: reinterpolation?
					twistParamRev = createNode('reverse', n=self.names.get('twistParamRev', 'rnm_twistParamRev'))
					self.step(twistParamRev, 'twistParamRev')

					# Twist Mults
					twistStartMult = createNode('multDoubleLinear', n=self.names.get('twistStartMult', 'rnm_twistStartMult'))
					ctrl.const.get().parameter.connect(twistParamRev.inputX)
					twistParamRev.outputX.connect(twistStartMult.i1)
					startTwist.connect(twistStartMult.i2)
					self.step(twistStartMult, 'twistStartMult')

					twistEndMult = createNode('multDoubleLinear', n=self.names.get('twistEndMult', 'rnm_twistEndMult'))
					ctrl.const.get().parameter.connect(twistEndMult.i1)
					endTwist.connect(twistEndMult.i2)
					self.step(twistEndMult, 'twistEndMult')

					twistAdd = createNode('addDoubleLinear', n=self.names.get('twistAdd', 'rnm_twistAdd'))
					twistStartMult.o.connect(twistAdd.input1)
					twistEndMult.o.connect(twistAdd.input2)
					self.step(twistAdd, 'twistAdd')

					twistAdd.output.connect(ctrl.const.get().resultTwist)

				# Convert MP worldspace to CONST localSpace.
				# Translate
				# TODO
				# Since I'm not actually using rotation or scale, this can probably be something less complicated.
				cmpMtrx = createNode('composeMatrix', n=self.names.get('cmpMtrx', 'rnm_cmpMtrx'))
				self.step(cmpMtrx, 'cmpMtrx')
				mp.allCoordinates.connect(cmpMtrx.inputTranslate)
				mp.rotate.connect(cmpMtrx.inputRotate)

				multMtrx = createNode('multMatrix', n=self.names.get('multMtrx', 'rnm_multMtrx'))
				self.step(multMtrx, 'multMtrx')
				cmpMtrx.outputMatrix.connect(multMtrx.matrixIn[0])
				ctrl.const.get().parentInverseMatrix.connect(multMtrx.matrixIn[1])

				decmpMtrx = createNode('decomposeMatrix', n=self.names.get('decmpMtrx', 'rnm_decmpMtrx'))
				self.step(decmpMtrx, 'decmpMtrx')
				multMtrx.matrixSum.connect(decmpMtrx.inputMatrix)
				
				# Move buf into default position and then constrain const
				# Buff
				# # translate
				# ctrl.buf.get().t.set(decmpMtrx.outputTranslate.get())
				decmpMtrx.outputTranslate.connect(ctrl.const.get().translate)
				if paramLists[i] is paramLists[-1]:
					decmpMtrx.outputRotate.connect(ctrl.const.get().rotate)

			
				try:
					self.curvePointOffsets.append(ctrl)
				except AttributeError:
					self.curvePointOffsets = [ctrl]

				ctrl.message.connect(parametricCurveRigGroup.results, na=True)


		for i, ctrl in enumerate(ctrls):
			
			if rotationStyle == 'curve':
				mps[i].follow.set(True)
				mps[i].worldUpType.set(2) # Object Rotation Up
				upAxisSwitch.outColor.connect(mps[i].worldUpVector)
				ctrl.const.get().up.get().worldMatrix.connect(mps[i].worldUpMatrix)
				mps[i].inverseUp.set(False)
				mps[i].inverseFront.set(mirror)
				self.rigNode.upAxis.connect(mps[i].upAxis)
				mps[i].frontAxis.set(0) # X
				# mps[i].upAxis.set(1) # Y
				ctrl.const.get().resultTwist.connect(mps[i].frontTwist)

			elif rotationStyle == 'aim':
				# For each control, aim constrain the previous control to point to it, with switchJoint as up axis
				if not ctrl is ctrls[0]:
					aimVector=(1,0,0)
					if mirror:
						aimVector=(-1,0,0)
					aim = aimConstraint(ctrl.const.get(), ctrls[i-1].const.get(), aimVector=aimVector, upVector=(0,1,0), worldUpVector=(0,1,0), worldUpObject=ctrls[i-1].const.get().up.get(), worldUpType='objectRotation')
					self.tangledAimConstraints.append(aim)
					upAxisSwitch.outColor.connect(aim.upVector)
					upAxisSwitch.outColor.connect(aim.worldUpVector)
					ctrls[i-1].const.get().resultTwist.connect(aim.offsetX)

				# If it's the last control, use the motionpath follow option instead.
				if ctrl is ctrls[-1]:
					# last object also means last node set on variable 'mp'
					mp.follow.set(True)
					mp.worldUpType.set(2) # Object Rotation Up
					# mp.worldUpVector.set((0,1,0))
					upAxisSwitch.outColor.connect(mp.worldUpVector)
					ctrl.const.get().up.get().worldMatrix.connect(mp.worldUpMatrix)
					mp.inverseUp.set(False)
					mp.inverseFront.set(mirror)
					self.rigNode.upAxis.connect(mp.upAxis)
					mp.frontAxis.set(0) # X
					# mp.upAxis.set(1) # Y
					ctrl.const.get().resultTwist.connect(mp.frontTwist)
			
			
			elif rotationStyle == 'none':
				# If only using for transform
				mps[i].follow.set(False)
				mps[i].rotate.disconnect()
				ctrls[i].const.get().rotate.disconnect()
				ctrls[i].const.get().rotate.set(0,0,0)




		if twist:
			self.twistAdds = []
			for i, curveGroup in enumerate(curveGroups):

				startTwist = parametricCurveRigGroup.attr('twistInput%sStart' % i)
				endTwist = parametricCurveRigGroup.attr('twistInput%sEnd' % i)

				# Use pma for each curve so that twist can have an indeterminate number of inputs.
				twistAdd = createNode('plusMinusAverage', n=self.names.get('twistAdd', 'rnm_twistAdd'))
				self.twistAdds.append(twistAdd)
				self.step(twistAdd, 'twistAdd')


				twistAddOutput2D = twistAdd.output2D.getChildren()
				twistAddOutput2D[0].connect(startTwist)
				twistAddOutput2D[1].connect(endTwist)



		return parametricCurveRigGroup

	# ============================================== RANGE SEQUENCE ==============================================
	def buildRangeSequenceSetup(self, min, max, initValues):
		''' Create a setup that maps multiple values on a single input, with controllable input variables  a linear interpolation value '''
		if self.dev: print '\nbuildRangeSequenceSetup'
		# Error check?
		# 0 - 1 - 2 - 3
		# v - x - y - z

		for i, val in enumerate(initVals):

			# Normalized partion
			rnge = createNode('blendTwoAttr')
			rnge.i[0].set(0)
			rnge.i[0].set(1)

			blnd = createNode('blendTwoAttr', n=self.names.get('sr', 'rnm_sr'))

	
	# ============================================== SCALE STACK ==============================================
	def buildScaleLengthSetup(self, scaleInputs, nodes, distanceInputs=None, lengthAttribute=None,controlNodes=None, settingsNode=None, parameters=None, doVolume=True, doScaleEnds=True, parentGroup=None):
		if self.dev: print '\nbuildRangeSequenceSetup'
		# TODO
		# Finish volume
		# support parameter inputs (for uvalue)

		if parentGroup is None:
			parentGroup = self.rigGroup

		if settingsNode is None:
			settingsNode = self.rigNode

		if controlNodes is None:
			controlNodes = nodes

		if distanceInputs is None:
			distanceInputs = scaleInputs

		# print ctrls
		# print nodes

		# TODO add support for 2+ ctrls
		if not len(scaleInputs) == 2:
			raise Exception('scaleInputs input should be two PyNode tranform nodes')

		if len(nodes)-1 < 1:
			raise Exception('buildScaleLengthSetup requires more than one input node')
		
		# parameter attribute
		for nodeIndex, node in enumerate(nodes):
			parameter = float(nodeIndex)/float(len(nodes))
			print parameter
			if hasAttr(node, 'parameter'):
				raise Exception('Node already has attribute: parameter: %s' % node)

			utils.cbSep(node)
			addAttr(node, ln='parameter', min=0, max=1, dv=parameter, k=1)
			node.parameter.set(l=1)


		# On off (connect to ik for now?)
		# if not hasAttr(settingsNode, 'ikScale'):
		# 	addAttr(settingsNode, ln='ikScale', min=0, max=1, dv=1, k=1)

		# Scale ends setup
		if doScaleEnds:
			for ctrlIndex, ctrl in enumerate(scaleInputs):
				scaleTransforms = []
				# Create a scale matrix constraint from ctrl (local from buf) to 
				for nodeIndex, node in enumerate(nodes):
					# Get parameters of points (or estimate)
					# print parameter

					# Convert the transform space a single time - don't connect world matrix, add temp matrix



					scaleMatrixSum = createNode('multMatrix', n=self.names.get('scaleMatrixSum', 'rnm_scaleMatrixSum#'))
					self.step(scaleMatrixSum, 'scaleMatrixSum')

					# Control stack
					ctrl.matrix.connect(scaleMatrixSum.matrixIn[0])
					ctrl.extra.get().matrix.connect(scaleMatrixSum.matrixIn[2])
					ctrl.const.get().matrix.connect(scaleMatrixSum.matrixIn[3])

					# Node Inverted matrix
					node.getParent().worldInverseMatrix[0].connect(scaleMatrixSum.matrixIn[4])

					# Inverse Offset
					# tempMatrix = createNode('multMatrix', n='localOffsetMatrixTemp')
					# node.parentInverseMatrix[0] >> tempMatrix.matrixIn[0]
					# ctrl.worldInverseMatrix[0] >> tempMatrix.matrixIn[1]
					# scaleMatrixSum.matrixIn[1].set(tempMatrix.matrixSum.get())
					# delete(tempMatrix)


					scaleMatrixRes = createNode('decomposeMatrix', n=self.names.get('scaleMatrixRes', 'rnm_scaleMatrixRes#'))
					self.step(scaleMatrixRes, 'scaleMatrixRes')
					scaleMatrixSum.matrixSum.connect(scaleMatrixRes.inputMatrix)


					# Blend result by parameter
					scaleBlend = createNode('blendColors', n=self.names.get('scaleBlend', 'rnm_scaleBlend#'))
					self.step(scaleBlend, 'scaleBlend')
					# ctrl.scaleX.connect(scaleBlend.color1G)
					# ctrl.scaleX.connect(scaleBlend.color1B)
					scaleMatrixRes.outputScale.connect(scaleBlend.color1)
					# scaleMatrixRes.outputScaleY.connect(scaleBlend.color1G)
					# scaleMatrixRes.outputScaleZ.connect(scaleBlend.color1B)

					if ctrlIndex == 1:
						node.parameter.connect(scaleBlend.blender)
					else:
						paramRev = createNode('reverse', n=self.names.get('paramRev', 'rnm_paramRev'))
						self.step(paramRev, 'paramRev')
						node.parameter.connect(paramRev.ix)
						paramRev.ox.connect(scaleBlend.blender)

					scaleBlend.color2.set(1,1,1)


					if not hasAttr(node, 'scaleTransform'):
						addAttr(node, ln='scaleTransform', at='message')
						transformParent = node
					else:
						transformParent = node.scaleTransform.get()

					scaleTransform = createNode('transform', n='%s_scale%s' % (node.nodeName(), ctrlIndex), p=transformParent)
					self.step(scaleTransform, 'scaleTransform')
					scaleTransform.message.connect(node.scaleTransform, f=1)

					# scaleBlend.output.connect(scaleTransform.scale)
					scaleBlend.outputG.connect(scaleTransform.scaleY)
					scaleBlend.outputB.connect(scaleTransform.scaleZ)

					scaleTransforms.append(scaleTransform)


		# Volume setup
		if doVolume:
		# if False:
			scaleTransforms = []
			startCtrl, endCtrl = distanceInputs

			# Get noramlized length
			
			# Skip length if already has setup
			if self.dev:
				print hasAttr(settingsNode, 'restLength')
				print hasAttr(settingsNode, 'currentNormalizedLength')
			if hasAttr(settingsNode, 'restLength') and hasAttr(settingsNode, 'currentNormalizedLength'):
				normalizeDiv = settingsNode.currentNormalizedLength.inputs()[0]
				restLengthMult = settingsNode.restLength.outputs()[0]

			else:
				if not hasAttr(settingsNode, 'restLength'):
					addAttr(settingsNode, ln='restLength', min=0.01, dv=1, keyable=1)

				if not hasAttr(settingsNode, 'currentNormalizedLength'):
					addAttr(settingsNode, ln='currentNormalizedLength', min=0, dv=1, keyable=1)
					settingsNode.currentNormalizedLength.set(k=0, cb=1)

				# Static Length between controls
				staticLengthGroup = createNode('transform', n=self.names.get('staticLengthGroup', 'rnm_staticLengthGroup'), p=parentGroup)
				self.step(staticLengthGroup, 'staticLengthGroup')

				staticLocStart = createNode('transform', n=self.names.get('staticLocStart', 'rnm_staticLocStart'), p=staticLengthGroup)
				staticLocStartS = createNode('locator', n='%sShape' % self.names.get('staticLocStart', 'rnm_staticLocStart'), p=staticLocStart)
				self.step(staticLocStart, 'staticLocStart')
				staticLocStartS.hide()
				utils.snap(startCtrl, staticLocStart)
				
				staticLocEnd = createNode('transform', n=self.names.get('staticLocEnd', 'rnm_staticLocEnd'), p=staticLengthGroup)
				staticLocEndS = createNode('locator', n='%sShape' % self.names.get('staticLocEnd', 'rnm_staticLocEnd'), p=staticLocEnd)
				self.step(staticLocEnd, 'staticLocEnd')
				staticLocEndS.hide()
				utils.snap(endCtrl, staticLocEnd)
				
				staticLength = createNode('distanceBetween', n=self.names.get('staticLength', 'rnm_staticLength'))
				self.step(staticLength, 'staticLength')

				staticLocStart.worldPosition.connect(staticLength.point1)
				staticLocEnd.worldPosition.connect(staticLength.point2)

				# Dynamic length between controls
				locStart = createNode('locator', n=self.names.get('locStart', 'rnm_locStart'), p=self.socket(startCtrl))
				self.step(locStart, 'locStart')
				locStart.hide()

				locEnd = createNode('locator', n=self.names.get('locEnd', 'rnm_locEnd'), p=self.socket(endCtrl))
				self.step(locEnd, 'locEnd')
				locEnd.hide()

				ctrlLocs = [locStart, locEnd]
				
				length = createNode('distanceBetween', n=self.names.get('length', 'rnm_length'))
				self.step(length, 'length')

				locStart.worldPosition.connect(length.point1)
				locEnd.worldPosition.connect(length.point2)


				# Multiply static length by rig input
				staticDistMult = createNode('multDoubleLinear', n=self.names.get('staticDistMult', 'rnm_staticDistMult'))
				self.step(staticDistMult, 'staticDistMult')
				staticLength.distance.connect(staticDistMult.i1)
				settingsNode.restLength.connect(staticDistMult.i2)

				# Normalized distance between controls
				normalizeDiv = createNode('multiplyDivide', n=self.names.get('normalizeDiv', 'rnm_normalizeDiv'))
				self.step(normalizeDiv, 'normalizeDiv')
				normalizeDiv.operation.set(2)

				length.distance.connect(normalizeDiv.input1X)
				staticDistMult.output.connect(normalizeDiv.input2X)
				# staticLength.distance.connect(normalizeDiv.input2X)

				# Return length information to user
				normalizeDiv.outputX.connect(settingsNode.currentNormalizedLength)

				# Multiply result by rest length
				restLengthMult = createNode('multDoubleLinear', n=self.names.get('restLengthMult', 'rnm_restLengthMult'))
				self.step(restLengthMult, 'restLengthMult')
				normalizeDiv.outputX.connect(restLengthMult.i1)
				settingsNode.restLength.connect(restLengthMult.i2)



			# continue scaling setup
			volumePow = createNode('multiplyDivide', n=self.names.get('volumePow', 'rnm_volumePow'))
			self.step(volumePow, 'volumePow')
			volumePow.operation.set(3)
			restLengthMult.o >> volumePow.input1X
			restLengthMult.o >> volumePow.input1Y
			restLengthMult.o >> volumePow.input1Z
			volumePow.i2x.set(0.5)
			volumePow.i2y.set(0.5)
			volumePow.i2z.set(0.5)

			volumeDiv = createNode('multiplyDivide', n=self.names.get('volumeDiv', 'rnm_volumeDiv'))
			self.step(volumeDiv, 'volumeDiv')
			volumeDiv.operation.set(2)

			volumeDiv.i1.set(1,1,1)
			volumeDiv.i2.set(1,1,1) # prevent div by zero

			volumePow.output >> volumeDiv.i2

			for nodeIndex, node in enumerate(nodes):
				# Get position between nodes

				# Create attribute
				addAttr(node, ln='volumeBlend', at='compound', numberOfChildren=3, k=1)
				addAttr(node, ln='volumeBlendX', parent='volumeBlend', dv=1, min=0, k=1)
				addAttr(node, ln='volumeBlendY', parent='volumeBlend', dv=1, min=0, k=1)
				addAttr(node, ln='volumeBlendZ', parent='volumeBlend', dv=1, min=0, k=1)
				
				attributes = [
				node.volumeBlendX,
				node.volumeBlendY,
				node.volumeBlendZ
				]
				# Blend each attribute with one
				scaleBlnds = []
				for i, attribute in enumerate(node.volumeBlend.getChildren()): 
					scaleBlnd = createNode('blendTwoAttr', n=self.names.get('scaleBlnd%s' % ['X', 'Y', 'Z'][i], 'rnm_scaleBlnd%s' % ['X', 'Y', 'Z'][i]))
					self.step(scaleBlnd, 'scaleBlnd%s' % ['X', 'Y', 'Z'][i])
					scaleBlnds.append(scaleBlnd)
					attribute >> scaleBlnd.ab
					scaleBlnd.i[0].set(1)
					volumeDiv.output.getChildren()[i] >> scaleBlnd.i[1]

				# volumeDiv.o.connect(scaleBlnd.input2)
				# volumeDiv.o.connect(scaleBlnd.input2)


				# Parent transform under last
				if not hasAttr(node, 'scaleTransform'):
					addAttr(node, ln='scaleTransform', at='message')
					transformParent = node
				else:
					transformParent = node.scaleTransform.get()

				scaleTransform = createNode('transform', n='%s_volume' % (node.nodeName()), p=transformParent)
				self.step(scaleTransform, 'scaleTransform')
				scaleTransform.message.connect(node.scaleTransform, f=1)

				for i, scaleBlend in enumerate(scaleBlnds):
					scaleBlend.output.connect(scaleTransform.scale.getChildren()[i])

				scaleTransforms.append(scaleTransform)

				
				# get noramlized differnce and apply to volume
				# build ramp parameter? Multiply vcontrol voume by parameter
				# node.parameter


		return scaleTransforms

		


class simpleSpaceSwitch(rig):
	# Class for interactivly editing weighted constraints
	'''
	from pymel.core import *
	import spaceSwitchClass as ss

	sel = ls('hand_L_ik_CTRL')[0]
	reload(ss)
	ssInst = ss.spaceSwitch(controller=sel, constrained=sel.const.get(), p='rig_GRP', targets=['rig_GRP', sel.buf.get()], labels=['World', 'Parent'])
	ssInst.addTarget(target=ls('hips_M_3_socket_GRP')[0], label='Chest')

	ssInst.removeTarget(label='Chest')
	'''
	freezeColor = (0,0,0)
	def __init__(self, constrained=None, controller=None, targets=None, labels=None, prefix='', constraintType='parent', offsets=True):
		# If already initialized, instantiate class with rigNode, else create new
		# self.dev = dev
		self.deleteList = []
		self.ssCtrlsList = []
		self.clashList = []
		self.unnammedList = []
		self.freezeList = []
		self.publishList = []
		self.rebuildList = []
		self.tangledMatrixConstraints = []
		self.nodeCount = 0
		self.sectionTag = 'spaceSwitch'
		self.constraintType = constraintType
		self.prefix = prefix
		self.offsets = offsets
		self.dev = True
		self.naming(constraintType)
		self.names = utils.constructNames(self.namesDict)

		if not constrained:
			raise Exception('Specify constrained object')

		# Initialize if not initialized
		self.prefix = 			prefix
		self.controller = 		controller
		self.constrained = 		constrained
		self.targets = 			targets
		self.labels = 			labels
		self.constraintType = 	constraintType

		self.constraint = 		None
		self.attrCategory =		'%s_spaceSwitch' % self.constrained.nodeName()

		if not self.prefix:
			self.prefix = self.constrained.nodeName()

		# Create set under rigNode set
		# if not objExists('connectorSet'):
		# 	connectorSet = sets([self.rigNode], n='connectorSet')
		# else:
		# 	connectorSet = sets('connectorSet', e=True, forceElement=self.rigNode)

		# if not objExists('rigNodeSet'):
		# 	rigNodeSet = sets([connectorSet], n='rigNodeSet')
		# else:
		# 	rigNodeSet = sets('rigNodeSet', e=True, forceElement=connectorSet)


		# if not hasAttr(self.rigNode, 'indicVis'):
		# 	addAttr(self.rigNode, ln='indicVis', at='short', min=0, max=1, dv=0)
		# 	self.rigNode.indicVis.set(k=0, cb=1)

		

		self.build()


	def naming(self, constraintType, *args, **kwargs):
		print '# naming'
		self.namesDict = {

			'rev':                      {'desc':  'spaceSwitch',	'warble': 'rev',			'other': [self.prefix],										},
			'rev':                      {'desc':  'spaceSwitch',	'warble': 'rev',			'other': [self.prefix],										},
			'constraint':               {'desc':  'spaceSwitch',	'warble': constraintType,	'other': [self.prefix],	},
			'cond1':                    {'desc':  'spaceSwitch',	'warble': 'cond',			'other': [self.prefix, '1'],								},
			'cond2':                    {'desc':  'spaceSwitch',	'warble': 'cond',			'other': [self.prefix, '2'],								},
		}

	
	def setDefaultBlend(self, val):
		print '# setDefaultBlend'
		try:
			addAttr(self.controllerBlendAttr, e=1, dv=val)
		except:
			pass
		try:
			addAttr(self.blendAttr, e=1, dv=val)
		except:
			try:
				warning('Default blend value could not be changed: %s' % self.blendAttr)
			except:
				warning('Default blend value could not be changed.')

		try:
			self.setBlend(val)
		except:
			pass

	def setNiceName(self, name):
		print '# setNiceName'
		try:
			addAttr(self.controllerBlendAttr, e=1, nn=name)
		except:
			pass
		try:
			addAttr(self.blendAttr, e=1, nn=name)
		except:
			try:
				warning('Nice Name could not be changed: %s' % self.blendAttr)
			except:
				warning('Nice Name could not be changed.')


	def setBlend(self, val):
		print '# setBlend'
		try:
			self.controllerBlendAttr.set(val)
		except:
			try:
				self.blendAttr.set(val)
			except:
				raise Exception('Blend value could not be changed.: %s' % self.blendAttr)

	def inputsErrorCheck(self):
		print '# inputsErrorCheck'
		# Check existing inputs for errors
		
		# Listify inputs in case they're single nodes
		if self.labels is not None:
			if not isinstance(self.labels, list):
				self.labels = [self.labels]
		if self.targets is not None:
			if not isinstance(self.targets, list):
				self.targets = [self.targets]
		

			# If targets specified, check length against labels(unless unspecified)
			if len(self.targets):
				if isinstance(self.labels, list):
					if len(self.labels) != len(self.targets):
						raise Exception('Labels list length does not match targets list length')
					else:
						# Check all labels and make sure they're strings
						for label in self.labels:
							if not isinstance(label, str) and not isinstance(label, unicode):
								raise Exception('Label is not a string: %s' % label)

			# Check each target. convert to pynode if it's a string
			for i, target in enumerate(self.targets):
				if isinstance(target, str) or isinstance(target, unicode):
					if len(ls(target)) == 1:
						self.targets[i] = ls(target)[0]
					elif len(ls(target)) == 0:
						raise Exception('No target found: %s' % target)
					elif len(ls(target)) > 0:
						warning('%s' % ls(target))
						raise Exception('More than one target object with name found: %s' % target)

			for target in self.targets:
				if target:
					if not isinstance(target, nt.Transform):
						raise Exception('Target is not a PyNode Transform: %s' % target)

		
		if not len(self.targets) == 2:
			raise Exception('simpleSpaceSwitch uses 2 input targets.')


		validConstraintTypes = [
		'parent',
		'point',
		'orient']
		
		if self.constraintType not in validConstraintTypes:
			raise Exception('Constraint type not valid: %s' % self.constraintType)

	def setController(self, attributeName=None):
		print '# setController'

		if attributeName is None:
			attributeName = self.blendAttrName

		skip=False
		if isinstance(self.controller, PyNode) and not isinstance(self.controller, Attribute):
			if not hasAttr(self.controller, attributeName):
				addAttr(self.controller, ln= attributeName, min=0, max=1, k=1)
				attribute = self.controller.attr(attributeName)
		elif isinstance(self.controller, Attribute):
			attribute = self.controller
		else:
			skip=True

		# Set attribute to controller
		if not skip:
			attribute.connect(self.blendAttr)


	
	def build(self):
		print '# build'
		# Build setup with given info
		self.inputsErrorCheck()

		# addAttr(self.enumAttrA, e=1, at='enum', enumName=enumName)
		# addAttr(self.enumAttrB, e=1, at='enum', enumName=enumName)

		# Delete old build
		if self.rebuildList:
			for item in self.rebuildList:
				if item.exists():
					delete(item)

		# Reset lists
		self.freezeList = []
		self.ssCtrlsList = []

		# Create target transforms/controls
		for i, target in enumerate(self.targets):
			label = self.labels[i]
			# Offset controls

			ctrl = createNode('transform', n='%sSpace_%s' % (self.constraintType, label), p=target)
			self.ssCtrlsList.append(ctrl)
			ctrl.hiddenInOutliner.set(1)
			self.step(ctrl, 'SSctrl')

			if self.offsets:
				utils.snap(self.constrained, ctrl)


		# Blend reverse
		rev = createNode('reverse', n=self.names.get('rev', 'rnm_rev'))
		self.step(rev, 'rev')

		# Create constraint
		if self.constraintType == 'parent':
			self.constraint = parentConstraint(self.ssCtrlsList, self.constrained, n=self.names.get('constraint', 'rnm_constraint'))
			self.constraint.interpType.set(2)
		
		elif self.constraintType == 'point':
			self.constraint = pointConstraint(self.ssCtrlsList, self.constrained, n=self.names.get('constraint', 'rnm_constraint'))
		
		elif self.constraintType == 'orient':
			self.constraint = orientConstraint(self.ssCtrlsList, self.constrained, n=self.names.get('constraint', 'rnm_constraint'))
			self.constraint.interpType.set(2)

		self.step(self.constraint, 'constraint', freeze=False)

		self.blendAttrName = '%sSpaceBlend' % self.constraintType

		if not hasAttr(self.constraint, self.blendAttrName):
			addAttr(self.constraint, ln= self.blendAttrName, min=0, max=1, k=1)

		self.blendAttr = self.constraint.attr(self.blendAttrName)

		self.blendAttr.connect(rev.ix)

		rev.outputX.connect(self.constraint.attr('w%s' % 0), f=1)
		self.blendAttr.connect(self.constraint.attr('w%s' % 1), f=1)

		

		# self.constructDeleteList()
		self.setController()
		self.freezeNodes()
		self.attachRigNode(nodeList=self.ssCtrlsList)
		# self.untangleConstraints()
		# self.pruneSet(rigNodeSet = 'connectorSet')



class spaceSwitch(rig):
	# Class for interactivly editing weighted constraints
	'''
	from pymel.core import *
	import spaceSwitchClass as ss

	sel = ls('hand_L_ik_CTRL')[0]
	reload(ss)
	ssInst = ss.spaceSwitch(controller=sel, constrained=sel.const.get(), p='rig_GRP', targets=['rig_GRP', sel.buf.get()], labels=['World', 'Parent'])
	ssInst.addTarget(target=ls('hips_M_3_socket_GRP')[0], label='Chest')

	ssInst.removeTarget(label='Chest')
	'''
	freezeColor = (0,0,0)
	def __init__(self, rigNode=None, parentRigNode=None, controller=None, constrained=None, targets=None, labels=None, prefix='', p=None, constraintType='parent', offsets=True, separator=True):
		# If already initialized, instantiate class with rigNode, else create new
		# self.dev = dev
		self.parentRigNode = parentRigNode
		self.deleteList = []
		self.ssCtrlsList = []
		self.clashList = []
		self.unnammedList = []
		self.freezeList = []
		self.publishList = []
		self.rebuildList = []
		self.tangledMatrixConstraints = []
		self.nodeCount = 0
		self.sectionTag = 'spaceSwitch'
		self.constraintType = constraintType
		self.parent = p
		self.prefix = prefix
		self.offsets = offsets
		self.dev = True
		self.naming(constraintType)
		self.names = utils.constructNames(self.namesDict)
		self.tangledMatrixConstraints = []


		initialize = True # Checks to see if rig needs to be initialized

		# If no inputs for rigNode or constrained, check controller
		if rigNode is None:
			# If there's a controller input, check if controller has spaceSwitch rigNode attached
			if controller is not None:
				if isinstance(controller, str) or isinstance(controller, unicode):
					if len(ls(controller)) == 1:
						controller = ls(controller)[0]
					elif len(ls(controller)) == 0:
						raise Exception('No controller node found: %s' % controller)
					elif len(ls(controller)) > 0:
						warning('%s' % ls(controller))
						raise Exception('More than one controller object with name found: %s' % controller)
				if not isinstance(controller, PyNode):
					raise Exception('Controller is not a PyNode: %s' % controller)
				else:
					if hasAttr(controller, 'spaceSwitchRigNode'):
						if controller.spaceSwitchRigNode.get():
							rigNode = controller.spaceSwitchRigNode.get()
							

			# If there's a constrained input, check if controller has spaceSwitch rigNode attached
			if rigNode is None and constrained is not None:
				if isinstance(constrained, str) or isinstance(constrained, unicode):
					if len(ls(constrained)) == 1:
						constrained = ls(constrained)[0]
					elif len(ls(constrained)) == 0:
						raise Exception('No constrained node found: %s' % constrained)
					elif len(ls(constrained)) > 0:
						warning('%s' % ls(constrained))
						raise Exception('More than one constrained object with name found: %s' % constrained)
				if not isinstance(constrained, nt.Transform):
					raise Exception('constrained is not a PyNode Transform: %s' % constrained)
				else:
					if hasAttr(constrained, 'spaceSwitchRigNode'):
						if constrained.spaceSwitchRigNode.get():
							rigNode = constrained.spaceSwitchRigNode.get()
							

		if rigNode is not None:
			self.rigNode = rigNode
			self.updateClassInfo()
			initialize = False



		if initialize:
			if not constrained:
				raise Exception('Specify constrained object')

			# Initialize if not initialized
			self.prefix = 			prefix
			self.controller = 		controller
			self.constrained = 		constrained
			self.targets = 			targets
			self.labels = 			labels
			self.constraintType = 	constraintType
			self.parent = 			p

			self.constraint = 		None
			self.attrCategory =		'%s_spaceSwitch' % self.constrained.nodeName()

			if not self.prefix:
				self.prefix = self.constrained.nodeName()

			
			self.rigGroup = createNode('transform', n=self.names.get('rigGroup', 'rnm_spaceSwitch'), p=self.parent)

			# Create rig node
			self.rigNode = createNode('locator', n=self.names.get('rigNode', 'rnm_spaceSwitch_rigNode'), p=self.rigGroup)
			self.rigNode.lpx.set(k=0, cb=0, l=1)
			self.rigNode.lpy.set(k=0, cb=0, l=1)
			self.rigNode.lpz.set(k=0, cb=0, l=1)
			self.rigNode.lsx.set(k=0, cb=0, l=1)
			self.rigNode.lsy.set(k=0, cb=0, l=1)
			self.rigNode.lsz.set(k=0, cb=0, l=1)
			self.rigNode.hide()
			self.selNode = self.rigNode

			if not objExists('connectorSet'):
				connectorSet = sets([self.rigNode], n='connectorSet')
			else:
				connectorSet = sets('connectorSet', e=True, forceElement=self.rigNode)

			if not objExists('rigNodeSet'):
				rigNodeSet = sets([connectorSet], n='rigNodeSet')
			else:
				rigNodeSet = sets('rigNodeSet', e=True, forceElement=connectorSet)


			if not hasAttr(self.rigNode, 'rigType'):
				addAttr(self.rigNode, ln='rigType', dt='string', k=1)
				self.rigNode.rigType.set('spaceSwitch', l=1)

			if not hasAttr(self.rigNode, 'prefix'):
				addAttr(self.rigNode, ln='prefix', dt='string', k=1)

			if not hasAttr(self.rigNode, 'constraintType'):
				addAttr(self.rigNode, ln='constraintType', at='enum', enumName='parent:point:orient', k=1)

			if not hasAttr(self.rigNode, 'controller'):
				addAttr(self.rigNode, ln='controller', at='message', k=1)

			if not hasAttr(self.rigNode, 'constrained'):
				addAttr(self.rigNode, ln='constrained', at='message', k=1)


			if not hasAttr(self.rigNode, 'constraint'):
				addAttr(self.rigNode, ln='constraint', at='message', k=1)

			if not hasAttr(self.rigNode, 'targetGroups'):
				addAttr(self.rigNode, ln='targetGroups', at='compound', numberOfChildren=2, multi=True, k=1)
				addAttr(self.rigNode, ln='target', p='targetGroups', at='message', k=1)
				addAttr(self.rigNode, ln='label', p='targetGroups', dt='string', k=1)

			if not hasAttr(self.rigNode, 'controlVis'):
				addAttr(self.rigNode, ln='controlVis', at='short', min=0, max=1, dv=1)
				self.rigNode.controlVis.set(k=0, cb=1)
			self.rigNode.controlVis.connect(self.rigGroup.v)

			# if not hasAttr(self.rigNode, 'indicVis'):
			# 	addAttr(self.rigNode, ln='indicVis', at='short', min=0, max=1, dv=0)
			# 	self.rigNode.indicVis.set(k=0, cb=1)

			self.enumAttrAName = '%sSpaceA' % self.constraintType
			self.enumAttrBName = '%sSpaceB' % self.constraintType
			self.blendAttrName = '%sSpaceBlend' % self.constraintType

			if not hasAttr(self.rigNode, self.enumAttrAName):
				addAttr(self.rigNode, ln= self.enumAttrAName, at='enum', enumName='0:1', k=1)
			if not hasAttr(self.rigNode, self.enumAttrBName):
				addAttr(self.rigNode, ln= self.enumAttrBName, at='enum', enumName='0:1', k=1, dv=1)

			if not hasAttr(self.rigNode, self.blendAttrName):
				addAttr(self.rigNode, ln= self.blendAttrName, min=0, max=1, k=1)

			self.enumAttrA = self.rigNode.attr(self.enumAttrAName)
			self.enumAttrB = self.rigNode.attr(self.enumAttrBName)
			self.blendAttr = self.rigNode.attr(self.blendAttrName)

			if not hasAttr(self.rigNode, 'constraint'):
				addAttr(self.rigNode, ln='constraint', at='message', k=self.dev)

			if not hasAttr(self.rigNode, 'rigGroup'):
				addAttr(self.rigNode, ln='rigGroup', at='message', k=self.dev)

			# if not hasAttr(self.rigNode, 'targets'):
			# 	addAttr(self.rigNode, ln='targets', at='message', multi=True, k=1)

			# if not hasAttr(self.rigNode, 'labels'):
			# 	addAttr(self.rigNode, ln='labels', dt='string', multi=True, k=1)

			self.updateRigNode()
			self.rebuild()
			self.setControllerNode()
			self.updateRigNode()



			select(self.rigNode)


	def naming(self, constraintType, *args, **kwargs):
		print '# naming'
		self.namesDict = {
			'rigGroup':					{'desc':  'spaceSwitch',	'warble': 'rigGroup',		'other': [self.prefix],										},
			'rigNode':					{'desc':  'spaceSwitch',	'warble': 'rigNode',		'other': [self.prefix],										},
			'buf':                      {'desc':  'spaceSwitch',	'warble': 'buf',			'other': [self.prefix],										},
			'const':                    {'desc':  'spaceSwitch',	'warble': 'const',			'other': [self.prefix],										},
			'offset':                   {'desc':  'spaceSwitch',	'warble': 'offset',			'other': [self.prefix],										},
			'ctrl':                     {'desc':  'spaceSwitch',	'warble': 'ctrl',			'other': [self.prefix],										},
			'rev':                      {'desc':  'spaceSwitch',	'warble': 'rev',			'other': [self.prefix],										},
			'constraint':               {'desc':  'spaceSwitch',	'warble': constraintType,	'other': [self.prefix],	},
			'cond1':                    {'desc':  'spaceSwitch',	'warble': 'cond',			'other': [self.prefix, '1'],								},
			'cond2':                    {'desc':  'spaceSwitch',	'warble': 'cond',			'other': [self.prefix, '2'],								},
		}

	def updateClassInfo(self):
		print '# updateClassInfo'
		self.selNode =			self.rigNode
		self.prefix = 			self.rigNode.prefix.get()
		self.constraintType = 	self.rigNode.constraintType.get(asString=True)
		self.controller = 		self.rigNode.controller.get()
		self.constraint = 		self.rigNode.constraint.get()
		self.constrained = 		self.rigNode.constrained.get()
		self.rigGroup = 		self.rigNode.rigGroup.get()

		self.enumAttrAName = '%sSpaceA' % self.constraintType
		self.enumAttrBName = '%sSpaceB' % self.constraintType
		self.blendAttrName = '%sSpaceBlend' % self.constraintType

		self.targets = []
		self.labels = []

		for targ in self.rigNode.targetGroups:
			if targ.getChildren()[0].get():
				self.targets.append(targ.getChildren()[0].get())
				self.labels.append(targ.getChildren()[1].get())
		# self.targets = 			self.rigNode.targets.get()
		# self.labels = 			self.rigNode.labels.get()
		self.attrCategory = 		'%s_spaceSwitch' % self.constrained.nodeName()

		# Get enum attributes for both rigNode and controller
		self.enumAttrA = self.rigNode.attr(self.enumAttrAName)
		self.enumAttrB = self.rigNode.attr(self.enumAttrBName)
		self.blendAttr = self.rigNode.attr(self.blendAttrName)
		

		if self.controller:
			if hasAttr(self.controller, self.blendAttrName):
				self.controllerEnumAttrA = self.controller.attr(self.enumAttrAName)
				self.controllerEnumAttrB = self.controller.attr(self.enumAttrBName)
				self.controllerBlendAttr = self.controller.attr(self.blendAttrName)
		
		if self.constraint:
			self.constraint = self.rigNode.constraint.get()

		self.inputsErrorCheck()

	def updateRigNode(self):
		print '# updateRigNode'
		if self.prefix:
			self.rigNode.prefix.set(self.prefix)
		
		# 
		self.rigNode.constraintType.set(self.constraintType)
		
		# 
		if self.controller:
			if not isConnected(self.controller.message, self.rigNode.controller):
				self.controller.message.connect( self.rigNode.controller, f=1 )
			if not hasAttr(self.controller, 'spaceSwitchRigNode'):
				addAttr(self.controller, ln='spaceSwitchRigNode', at='message', ct=self.attrCategory)
			if not isConnected(self.rigNode.message, self.controller.spaceSwitchRigNode):
				self.rigNode.message.connect(self.controller.spaceSwitchRigNode)
		# 
		if not isConnected(self.constrained.message, self.rigNode.constrained):
			self.constrained.message.connect( self.rigNode.constrained, f=1 )
		if not hasAttr(self.constrained, 'spaceSwitchRigNode'):
			addAttr(self.constrained, ln='spaceSwitchRigNode', at='message', ct=self.attrCategory)
		if not isConnected(self.rigNode.message, self.constrained.spaceSwitchRigNode):
			self.rigNode.message.connect(self.constrained.spaceSwitchRigNode)

		if not isConnected(self.rigGroup.message, self.rigNode.rigGroup):
			self.rigGroup.message.connect(self.rigNode.rigGroup)

		# Diconnect current targets and rebuild
		if self.targets:
			for targ in self.rigNode.targetGroups:
				for targChild in targ.getChildren():
					targChild.disconnect()

			for i, target in enumerate(self.targets):
				target.message.connect(self.rigNode.targetGroups[i].target)
				self.rigNode.targetGroups[i].label.set(self.labels[i])

		if self.constraint:
			if not isConnected(self.constraint.message, self.rigNode.constraint):
				self.constraint.message.connect(self.rigNode.constraint)

	def setDefaultBlend(self, val):
		print '# setDefaultBlend'
		try:
			addAttr(self.controllerBlendAttr, e=1, dv=val)
		except:
			pass
		try:
			addAttr(self.blendAttr, e=1, dv=val)
		except:
			try:
				warning('Default blend value could not be changed: %s' % self.blendAttr)
			except:
				warning('Default blend value could not be changed.')

		try:
			self.setBlend(val)
		except:
			pass

	def setNiceName(self, name):
		print '# setNiceName'
		try:
			addAttr(self.controllerBlendAttr, e=1, nn=name)
		except:
			pass
		try:
			addAttr(self.blendAttr, e=1, nn=name)
		except:
			try:
				warning('Nice Name could not be changed: %s' % self.blendAttr)
			except:
				warning('Nice Name could not be changed.')


	def setBlend(self, val):
		print '# setBlend'
		try:
			self.controllerBlendAttr.set(val)
		except:
			try:
				self.blendAttr.set(val)
			except:
				raise Exception('Blend value could not be changed.: %s' % self.blendAttr)

	def inputsErrorCheck(self):
		print '# inputsErrorCheck'
		# Check existing inputs for errors
		
		# Listify inputs in case they're single nodes
		if self.labels is not None:
			if not isinstance(self.labels, list):
				self.labels = [self.labels]
		if self.targets is not None:
			if not isinstance(self.targets, list):
				self.targets = [self.targets]
		

			# If targets specified, check length against labels(unless unspecified)
			if len(self.targets):
				if isinstance(self.labels, list):
					if len(self.labels) != len(self.targets):
						raise Exception('Labels list length does not match targets list length')
					else:
						# Check all labels and make sure they're strings
						for label in self.labels:
							if not isinstance(label, str) and not isinstance(label, unicode):
								raise Exception('Label is not a string: %s' % label)

			# Check each target. convert to pynode if it's a string
			for i, target in enumerate(self.targets):
				if isinstance(target, str) or isinstance(target, unicode):
					if len(ls(target)) == 1:
						self.targets[i] = ls(target)[0]
					elif len(ls(target)) == 0:
						raise Exception('No target found: %s' % target)
					elif len(ls(target)) > 0:
						warning('%s' % ls(target))
						raise Exception('More than one target object with name found: %s' % target)

			for target in self.targets:
				if target:
					if not isinstance(target, nt.Transform):
						raise Exception('Target is not a PyNode Transform: %s' % target)

		if self.parent is not None:
			if isinstance(self.parent, str) or isinstance(self.parent, unicode):
				if len(ls(self.parent)) == 1:
					self.parent = ls(self.parent)[0]
				elif len(ls(self.parent)) == 0:
					raise Exception('No target found: %s' % self.parent)
				elif len(ls(self.parent)) > 0:
					warning('%s' % ls(self.parent))
					raise Exception('More than one target object with name found: %s' % self.parent)


		validConstraintTypes = [
		'parent',
		'point',
		'orient']
		
		if self.constraintType not in validConstraintTypes:
			raise Exception('Constraint type not valid: %s' % self.constraintType)

	def setControllerNode(self, node=None):
		print '# setControllerNode'
		# If controller already set, just add to that one. Otherwise assume a switch and delete old connections first
		if not node is None:
			# TODO
			# Remove connections from previous (use category?)
			if self.controller:
				if self.dev: print '\n'
				self.deleteControllerAttributes()


			self.controller = node
			self.updateRigNode()

		if self.controller:
			if not hasAttr(self.controller, 'spaceSwitchRigNode'):
				addAttr(self.controller, ct=self.attrCategory, ln='spaceSwitchRigNode', at='message', k=self.dev)
			if not isConnected(self.rigNode.message, self.controller.spaceSwitchRigNode):
				self.rigNode.message.connect(self.controller.spaceSwitchRigNode, f=1)

			# if not hasAttr(self.controller, 'controlVis'):
			# 	addAttr(self.controller, ct=self.attrCategory, ln='controlVis', at='short', min=0, max=1, k=1, dv=self.dev)
			# self.controller.controlVis.connect(self.rigNode.controlVis)
			
			# if not hasAttr(self.controller, 'indicVis'):
			# 	addAttr(self.controller, ct=self.attrCategory, ln='indicVis', at='short', min=0, max=1, k=1, dv=self.dev)
			# self.controller.indicVis.connect(self.rigNode.indicVis)

			
			# enumName = addAttr(self.enumAttrA, q=1, enumName=1)
			enumName = self.enumAttrA.getEnums()
			enumAttrAName = self.enumAttrA.longName()
			enumAttrBName = self.enumAttrB.longName()

			if not hasAttr(self.controller, enumAttrAName):
				if separator:
					utils.cbSep(self.controller, ct=self.attrCategory)
				addAttr(self.controller, ct=self.attrCategory, ln=enumAttrAName, at='enum', enumName='0:1', k=1)
			self.controller.attr(enumAttrAName).setEnums(enumName)

			if not hasAttr(self.controller, enumAttrBName):
				addAttr(self.controller, ct=self.attrCategory, ln=enumAttrBName, at='enum', enumName='0:1', dv=1, k=1)
			self.controller.attr(enumAttrBName).setEnums(enumName)


			blendAttrName =self.blendAttr.longName()
			if not hasAttr(self.controller, blendAttrName):
				addAttr(self.controller, ct=self.attrCategory, ln=blendAttrName, min=0, max=1, dv=self.dev, k=1)
			

			self.controllerEnumAttrA = self.controller.attr(enumAttrAName)
			self.controllerEnumAttrB = self.controller.attr(enumAttrBName)
			self.controllerBlendAttr = self.controller.attr(blendAttrName)
			
			if not isConnected(self.controllerEnumAttrA, self.enumAttrA):
				self.controllerEnumAttrA.connect(self.enumAttrA)
			if not isConnected(self.controllerEnumAttrB, self.enumAttrB):
				self.controllerEnumAttrB.connect(self.enumAttrB)
			if not isConnected(self.controllerBlendAttr, self.blendAttr):
				self.controllerBlendAttr.connect(self.blendAttr)

			if len(self.labels) <= 2:
				self.controllerEnumAttrA.set(k=0)
				self.controllerEnumAttrB.set(k=0)
			else:
				self.controllerEnumAttrA.set(k=1)
				self.controllerEnumAttrB.set(k=1)

	def addTarget(self, target, label=None):
		print '# addTarget'
		self.updateClassInfo()

		if not label:
			label = target.nodeName()

		if self.targets:
			for targ in self.rigNode.targetGroups:
				for targChild in targ.getChildren():
					targChild.disconnect()

		self.targets.append(target)
		self.labels.append(label)

		for i, target in enumerate(self.targets):
			target.message.connect(self.rigNode.targetGroups[i].target)
			self.rigNode.targetGroups[i].label.set(self.labels[i])

		self.rebuild()
		self.updateRigNode()
		select(self.rigNode)

	def removeTarget(self, target=None, label=None, ind=None):
		print '# removeTarget'
		
		self.updateClassInfo()

		# If no index input, get index from label input. If not label input, get index from target input.
		if ind is None:
			if label:
				if label in self.labels:
					ind = self.labels.index(label)
				else:
					raise Exception('Label not found')
			
		if ind is None:
			if target:
				if target in self.targets:
					ind = self.targets.index(target)
				else:
					raise Exception('Target not found')

		# Remove items from class lists
		self.targets.remove(self.targets[ind])
		self.labels.remove(self.labels[ind])

		# reload rigNode targets
		for targ in self.rigNode.targetGroups:
			targ.getChildren()[0].disconnect()
			targ.getChildren()[1].set('')

		for i, target in enumerate(self.targets):
			target.message.connect(self.rigNode.targetGroups[i].target)
			self.rigNode.targetGroups[i].label.set(self.labels[i])

		self.rebuild()
		self.updateRigNode()
		select(self.rigNode)

	def deleteControllerAttributes(self):
		print '# deleteControllerAttributes'
		nodes = [self.controller, self.constrained]
		for node in nodes:
			attributes = listAttr(node, ct=self.attrCategory)

			for attribute in attributes:
				attribute = node.attr(attribute)
				deleteAttr(attribute)

	def deleteRig(self):

		print '# deleteRig 10115 (spaceSwitch)'
		self.deleteControllerAttributes()
		delete(self.rigNode.deleteList.get())
		delete(self.rigNode)

	def rebuild(self):
		print '# rebuild'
		# Build setup with given info
		self.updateClassInfo()
		self.inputsErrorCheck()

		enumName = ':'.join(self.labels)
		self.enumAttrA.setEnums(enumName)
		self.enumAttrB.setEnums(enumName)

		# addAttr(self.enumAttrA, e=1, at='enum', enumName=enumName)
		# addAttr(self.enumAttrB, e=1, at='enum', enumName=enumName)

		# Delete old build
		if self.rebuildList:
			for item in self.rebuildList:
				if item.exists():
					delete(item)

		# Reset lists
		self.freezeList = []
		self.ssCtrlsList = []

		# Create target transforms/controls
		for i, target in enumerate(self.targets):
			label = self.labels[i]
			# Offset controls

			buf = createNode('transform', n=self.names.get('buf', 'rnm_buf_%s' % label), p=self.rigGroup)
			# if not self.constraintType == 'point':
			xform(buf, ws=1, m=xform(target, q=1, ws=1, m=1))
			self.step(buf, 'buf')
			self.rebuildList.append(buf)

			const = createNode('transform', n=self.names.get('const', 'rnm_const_%s' % label), p=buf)
			self.step(const, 'const')
			self.matrixConstraint(target, const, t=1, r=1, s=1, offset=1)
			const.visibility.set(l=1, k=0, cb=0)

			offset = createNode('transform', n=self.names.get('offset', 'rnm_offset_%s' % label), p=const)
			self.step(offset, 'offset', freeze=False)
			if self.offsets:
				xform(offset, ws=1, m=xform(self.constrained, q=1, ws=1, m=1))
			offset.visibility.set(l=1, k=0, cb=0)

			ctrl = createNode('transform', n=self.names.get('ctrl', 'rnm_ctrl_%s' % label), p=offset)
			ctrl.displayHandle.set(k=1)
			ctrl.visibility.set(l=1, k=0, cb=0)
			self.ssCtrlsList.append(ctrl)
			self.step(ctrl, 'ctrl', freeze=False)

			addAttr(ctrl, k=0, h=1, at='message', ln='bufferGroup', sn='buf')
			addAttr(ctrl, k=0, h=1, at='message', ln='constraintGroup', sn='const')
			addAttr(ctrl, k=0, h=1, at='message', ln='extraGroup', sn='extra')

			buf.message >> ctrl.buf
			const.message >> ctrl.const
			offset.message >> ctrl.extra

		# Blend reverse
		rev = createNode('reverse', n=self.names.get('rev', 'rnm_rev'))
		self.step(rev, 'rev')
		self.blendAttr.connect(rev.ix)

		print 'SSCTRLSLIST:'
		print self.ssCtrlsList
		# Create constraint
		if self.constraintType == 'parent':
			self.constraint = parentConstraint(self.ssCtrlsList, self.constrained, n=self.names.get('constraint', 'rnm_constraint'))
			self.constraint.interpType.set(2)
		
		elif self.constraintType == 'point':
			self.constraint = pointConstraint(self.ssCtrlsList, self.constrained, n=self.names.get('constraint', 'rnm_constraint'))
		
		elif self.constraintType == 'orient':
			self.constraint = orientConstraint(self.ssCtrlsList, self.constrained, n=self.names.get('constraint', 'rnm_constraint'))
			self.constraint.interpType.set(2)

		self.step(self.constraint, 'constraint', freeze=False)

		# Create multi-target blending conditional statements
		for i, target in enumerate(self.targets):
			cond1 = createNode('condition', n=self.names.get('cond1', 'rnm_cond1'))
			self.step(cond1, 'cond1')
			cond1.colorIfFalseR.set(0)
			self.enumAttrA.connect(cond1.firstTerm)
			cond1.secondTerm.set(i)

			cond2 = createNode('condition', n=self.names.get('cond2', 'rnm_cond2'))
			self.step(cond2, 'cond2')
			self.enumAttrB.connect(cond2.firstTerm)
			cond2.secondTerm.set(i)

			rev.outputX.connect(cond1.colorIfTrueR)
			self.blendAttr.connect(cond2.colorIfTrueR)
			cond1.outColorR.connect(cond2.colorIfFalseR)

			cond2.outColorR.connect(self.constraint.attr('w%s' % i), f=1)

		self.setControllerNode()
		self.constructDeleteList()
		self.freezeNodes()
		self.attachRigNode(nodeList=self.ssCtrlsList)
		# self.untangleConstraints()
		self.pruneSet(rigNodeSet = 'connectorSet')


# =================================================================================

# =================================================================================

# =================================================================================


def deleteRig(nodes=None):
	print '# deleteRig 10236 ALL' 

	# print nodes
	rigNodes = getRigNodesFromSelection(nodes)
	if rigNodes:
		for rigNode in rigNodes:
			print rigNode
			selNode = rigNode.selNode.get()
			print selNode
			rigGroup = rigNode.rigGroup.get()
			print rigGroup
			typ = rigNode.rigType.get()
			delete(selNode.deleteList.get())
			try:
				delete(selNode)
			except:
				pass
			try:
				delete(rigGroup)
			except:
				pass
			
			print '%s Rig Deleted.' % (typ)
	else:
		warning('No rigNodes found on selected object(s).')



def getRigNodesFromSelection(selection=None, raiseExc=False):
	if selection is None:
		selection = ls(sl=1)

	# Error checks
	if not isinstance(selection, list):
		selection = [selection]
	if not len(selection):
		if raiseExc:
			raise Exception('Verify inputs')
		else:
			pass

	for i, node in enumerate(selection):
		if isinstance(node, unicode) or isinstance(node, str):
			if len(ls(node)) != 1:
				if len(ls(node)) == 0:
					raise Exception('No node with name found in scene: %s' % node)
				if len(ls(node)) > 1:
					raise Exception('More than one node with name found in scene: %s' % node)
			else:
				selection[i] = ls(node)[0]

	for i, node in enumerate(selection):	
		if not isinstance(node, PyNode):
			print node
			raise Exception('Node is not a PyNode.' % node)


	# Retrieve rigNodes
	rigNodes = []
	for i, node in enumerate(selection):
		# Get message outputs
		if hasAttr(node, 'message'):
			outps = node.message.outputs()
			for out in outps:
				if hasAttr(out, 'selNodeVer'):
					selNode = out
					rigNode = selNode.rigNode.get()
					rigNodes.append(rigNode)
				elif hasAttr(out, 'rigNodeVer'):
					rigNode = out
					rigNodes.append(rigNode)

	return rigNodes





def twistExtractorMatrix(points=None, base=None, settingsNode=None, rigNode=None, twistAxisChoice=0, dev=False):
	print '# twistExtractorMatrix'
	'''
	Creates a twist value reader measuring the difference in twist from the base node using matrices.
	Pro: Less overhead, still works with nodes in heirarchy between base and point
	Con: Flips at 180deg (down from 360)

	Fix weird twist axis inputs (in splineBuild too)
	change rotate order on q2e

	'''
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




class gShowProgress(object):
	"""
	Function decorator to show the user (progress) feedback.
	@usage
 
	import time
	@gShowProgress(end=10)
	def createCubes():
		for i in range(10):
			time.sleep(1)
			if createCubes.isInterrupted(): break
			iCube = cmds.polyCube(w=1,h=1,d=1)
			cmds.move(i,i*.2,0,iCube)
			createCubes.step()
	"""

	def __init__(self, status='Busy...', start=0, end=100, interruptable=True):
		import maya.cmds as cmds
		import maya.mel
 
		self.mStartValue = start
		self.mEndValue = end
		self.mStatus = status
		self.mInterruptable = interruptable
		self.mMainProgressBar = maya.mel.eval('$tmp = $gMainProgressBar')
 
	def step(self, inValue=1):
		"""Increase step
		@param inValue (int) Step value"""
		cmds.progressBar(self.mMainProgressBar, edit=True, step=inValue)
 
	def isInterrupted(self):
		"""Check if the user has interrupted the progress
		@return (boolean)"""
		return cmds.progressBar(self.mMainProgressBar, query=True, isCancelled=True)
 
	def start(self):
		"""Start progress"""
		cmds.waitCursor(state=True)
		cmds.progressBar( self.mMainProgressBar,
				edit=True,
				beginProgress=True,
				isInterruptable=self.mInterruptable,
				status=self.mStatus,
				minValue=self.mStartValue,
				maxValue=self.mEndValue
			)
		cmds.refresh()
 
	def end(self):
		"""Mark the progress as ended"""
		cmds.progressBar(self.mMainProgressBar, edit=True, endProgress=True)
		cmds.waitCursor(state=False)
 
	def __call__(self, inFunction):
		"""
		Override call method
		@param inFunction (function) Original function
		@return (function) Wrapped function
		@description
			If there are decorator arguments, __call__() is only called once,
			as part of the decoration process! You can only give it a single argument,
			which is the function object.
		"""
		def wrapped_f(*args, **kwargs):
			# Start progress
			self.start()
			# Call original function
			inFunction(*args,**kwargs)
			# End progress
			self.end()
 
		# Add special methods to the wrapped function
		wrapped_f.step = self.step
		wrapped_f.isInterrupted = self.isInterrupted
 
		# Copy over attributes
		wrapped_f.__doc__ = inFunction.__doc__
		wrapped_f.__name__ = inFunction.__name__
		wrapped_f.__module__ = inFunction.__module__
 
		# Return wrapped function
		return wrapped_f


