from pymel.core import *
import fitRig
import buildRig
import spaceSwitch2
import utils as rb
reload (fitRig)
reload (buildRig)

buck = False

def loadAttributes(attributeCol, *args):
	# Last selected object
	dev = True
	nodes = ls(sl=1)

	if len(nodes):
		node = nodes[-1]
		# Get fit node
		fitNodes = axmn_fitRig.getFitNode(ls(sl=1))
		if len(fitNodes)>1:
			warning('More than one fitNode Found!', sl=1)
		if len(fitNodes):
			fitNode = fitNodes[-1]

			# Layout
			attributeForm = formLayout(p=attributeCol)
			scrollingLayout = scrollLayout(panEnabled=1, p=attributeForm, childResizable=1)
			spanLayout = columnLayout(adjustableColumn=True, p=scrollingLayout)
			
			# Titlebar
			titleBar = button(l=fitNode.shortName().split('|')[-1], h=20, bgc=[0.3, 0.2, 0.2], p=spanLayout)
			# Get user-defined attribtue
			categories = ['naming', 'input', 'shape', 'attribute', 'output']
			for category in categories:
				attributes = []

				# Get attributes in category
				attributes.extend(listAttr(fitNode, ct=category, userDefined=1))

				if len(attributes):
					# Category label
					labelLine = horizontalLayout(p=spanLayout)
					text(l=category.upper(), p=labelLine, bgc=[0.3, 0.2, 0.2])
					separator(style='none', bgc=[0.3, 0.2, 0.2])
					labelLine.redistribute(3,6)
					for attr in attributes:
						attrb = fitNode.attr(attr)
						attrType = attrb.type()
						if dev: print '%s.%s' % (attrb, attrType)

						supportedTypes = ['message', 'float', 'double', 'string']
						if attrType in supportedTypes:
							# UI line Layout
							uiLine = horizontalLayout(p=spanLayout)
							text(label=attributeName(attrb, n=1))


						# ===============================================
						if attrType == 'message':
							if len(attrb.inputs(sh=1)):
								messageInput = attrb.inputs(sh=1)[0].split('|')[-1]
							elif len(attrb.outputs()):
								messageInput = attrb.outputs()[-1]
							else:
								messageInput = ''
							
							
							button(l='S')
							messageText = textField(text=messageInput)
							button(l='<<')
							if len(attrb.outputs()):
								textField(messageText, e=1, ed=0)
							uiLine.redistribute(3,1,4,1)

						# ===============================================
						if attrType == 'float' or attrType == 'double':
							value = attrb.get()
							minV = attrb.getMin()
							maxV = attrb.getMax()

							
							button(l='S')
							floatInput = floatField(v=value, precision=2)
							if not minV is None:
								floatField(floatInput, e=1, min=minV)
							if not maxV is None:
								floatField(floatInput, e=1, max=maxV)
							button(l='<<')
							uiLine.redistribute(3,1,4,1)



						# ===============================================
						if attrType == 'string':
							value = attrb.get()
							
							separator(style='none')
							messageText = textField(text=value)
							button(l='X')
							uiLine.redistribute(3,1,4,1)

						# ===============================================
						'''
						if attrType == 'enum':
							value = attrb.get()
							
							separator(style='none')
							messageText = textField(text=value)
							button(l='X')
							uiLine.redistribute(3,1,4,1)
						'''
						# ===============================================
			#
			formLayout(attributeForm, e=1, attachForm=[
				(scrollingLayout, 'top', 0), (scrollingLayout, 'left', 5), (scrollingLayout, 'right', 5), (scrollingLayout, 'bottom', 0),
				])
			return attributeForm


def getFitNodes(initSelection=None, *args):
	selection = []
	if initSelection == None:
		if buck:
			globalMove = ls('ctl_GlobalMove')[0]
		else:
			globalMove = ls('GlobalMove')[0]
		fitSkeleton = globalMove.fitSkeleton.inputs()[0]
		settingsGroup = fitSkeleton.fitSkeletonSettings.inputs()[0]
		children = settingsGroup.getChildren()
		for child in children:
			if not objectType(child, isType='nurbsCurve'):
				shapes = child.getShapes()
				if not isinstance(shapes, list):
					shapes = [shapes]
				if len(shapes)>0:
					if hasAttr(shapes[0], 'rigType'):
						selection.append(child.getShapes()[0])
	else:
		count = len(initSelection)
		for node in initSelection:
			if hasAttr(node, 'rigType', checkShape=False):
				print "Rig Type Found, node: %s" % node
				selection.append(node)
				count = count-1
			elif hasAttr(node, 'fitNode', checkShape=False):
				selection.extend(node.fitNode.inputs(shapes=1))
				selection.extend(node.fitNode.outputs(shapes=1))
				count = count-1
		if count==0:
			warning('No FitNodes found.')
	return selection

def getRigNodes(*args):
	settingsGroup = ls('Settings_FitSkeleton')[0]
	children = settingsGroup.getChildren()
	selection = []
	for child in children:
		if not objectType(child, isType='nurbsCurve'):
			shapes = child.getShapes()
			if len(shapes)>0:
				if hasAttr(shapes[0], 'rigType'):
					selection.append(child.getShapes()[0])



def ui():
	'''Notes:
	Use maya.cmds?
	3 Sections:
	Overall Settings:
		Scene Forward Axis
		Scene Up Axis
	First section is buttons that set up fitRigs
	Create a window that automatically updates based on selected object (with lock button)
		ScriptJob to update window on selection
		Check attribute type or category to load more useful view of each attribute, as well as useful buttons in relation
	Message:
		Button to load selection into field, (and auto load successive objects based on heirarchy data?) ct=inputHier0, inputHeir1 etc)
	LinStep:
		Ramp/curve input?

	
	'''
	column1 = 1
	column2 = 1
	column3 = 0

	def loadFitNodes():
		fitNodes = getFitNodes()
		if isinstance(fitNodes, list):
			for fitNode in getFitNodes():
				textScrollList(fitNodeList, e=1, append=fitNode.shortName().split("|")[-1])

	if window('axmnRigging', exists=1):
		deleteUI('axmnRigging')
	width = 175
	buttonHeight = 30

	ui = window('axmnRigging', t='FitRig Setup', width=width, h=300, resizeToFitChildren=1, sizeable=1, mxb=0)

	columns = horizontalLayout()
	if column1:
		buttonCol = verticalLayout(p=columns)
		#================================================================================================
		initFrame = frameLayout(l='Init', collapsable=0, w=width, bgc=[0.3, 0.2, 0.2], p=buttonCol)
		#================================================================================================
		initCol = verticalLayout(p=initFrame)
		initButton = 		iconTextButton(l='Init', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=initCol)
		unInitButton = 		iconTextButton(l='Deinit', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=initCol)
		toggleVisButton = 	iconTextButton(l='Toggle Vis', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=initCol)

		#================================================================================================
		fitRigFrame = frameLayout(l='Fit Rig', collapsable=0, w=width, bgc=[0.3, 0.2, 0.2], p=buttonCol)
		#================================================================================================
		fitRigCol = verticalLayout(p=fitRigFrame)
		threePntButton = 			iconTextButton(l='Three Point IK', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=fitRigCol)
		twoPntButton = 				iconTextButton(l='Two Point IK', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=fitRigCol)
		splineButton = 				iconTextButton(l='Spline', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=fitRigCol)
		footButton = 				iconTextButton(l='Foot', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=fitRigCol)
		delFitRigButton = 			iconTextButton(l='Delete FitRig', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=fitRigCol)
		selectFitNodesButton = 		iconTextButton(l='Select FitNodes', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=fitRigCol)

		#================================================================================================
		buildRigFrame = frameLayout(l='Build Rig', collapsable=0, w=width, bgc=[0.3, 0.2, 0.2], p=buttonCol)
		#================================================================================================
		buildRigCol = verticalLayout(p=buildRigFrame)
		buildAllButton = 			iconTextButton(l='Build All', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=buildRigCol)
		buildSelectedButton = 		iconTextButton(l='Build Selected', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=buildRigCol)
		selectBuildNodesButton = 	iconTextButton(l='Select RigNodes', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=buildRigCol)
		deleteBuild = 				iconTextButton(l='Delete Selected RigNode', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=buildRigCol)
		deleteAll = 				iconTextButton(l='Delete All RigNodes', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=buildRigCol)
		

		#================================================================================================
		spaceSwitchFrame = frameLayout(l='Space Switch', collapsable=0, w=width, bgc=[0.3, 0.2, 0.2], p=buttonCol)
		#================================================================================================
		spaceSwitchCol = verticalLayout(p=spaceSwitchFrame)
		spaceSwitchNodeButton = 	iconTextButton(l='SpaceSwitch Node', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=spaceSwitchCol)
		spaceSwitchBuildButton = 	iconTextButton(l='SpaceSwitch Build', h=buttonHeight, bgc=(0.4, 0.4, 0.4), rpt=1, style='iconAndTextHorizontal', p=spaceSwitchCol)

		#================================================================================================
		#================================================================================================
	if column2:
		attributeCol = verticalLayout(p=columns)
		attributeForm = loadAttributes(attributeCol)

	#================================================================================================
	#================================================================================================
	if column3:
		nodeListColumn = verticalLayout(p=columns)
		nodeListForm = formLayout(p=nodeListColumn)
		fitNodeList = textScrollList(p=nodeListForm)
		rigNodeList = textScrollList(p=nodeListForm)
		formLayout(nodeListForm, e=1, attachForm=[
			(fitNodeList, 'top', 0), (fitNodeList, 'left', 0), (fitNodeList, 'right', 5),
			 (rigNodeList, 'left', 0), (rigNodeList, 'right', 5), (rigNodeList, 'bottom', 0),
			],
			attachPosition=[
			(fitNodeList, 'bottom', 5, 50)
			],
			attachControl=[
			(rigNodeList, 'top', 0, fitNodeList)
			])

		loadFitNodes()
	

	# for rigNode in getRigNodes():
	# 	textScrollList(figNodeList, e=1, append=rigNode.shortName.split("|")[-1])

	# Redistribute
	#================================================================================================
	if column1 and column2 and column3:
		columns.redistribute(1,3,1)
	elif column1 and column2:
		columns.redistribute(1,4)
	elif column2 and column3:
		columns.redistribute(4,1)
	else:
		columns.redistribute()
	#
	if column1:
		buttonCol.redistribute(3,5,5,2)
		##
		initCol.redistribute()
		fitRigCol.redistribute()
		buildRigCol.redistribute()
		spaceSwitchCol.redistribute()
	##
	if column2:
		attributeCol.redistribute()
	##
	if column3:
		nodeListColumn.redistribute()

	#================================================================================================




	def initRig(*args):
		axmn_fitRig.fitRigInitialize(ls(sl=1)[0])
	initButton.setCommand(initRig)

	def unInitRig(*args):
		axmn_fitRig.deleteFitRigSkeleAttrs(ls(sl=1)[0])
	unInitButton.setCommand(initRig)

	def toggleVis(*args):
		GlobalMoveName = ('GlobalMove')
		if buck: GlobalMoveName = 'ctl_GlobalMove'
		if objExists(GlobalMoveName):
			globalMove = ls(GlobalMoveName)[0]
			fitSkel = globalMove.fitSkeleton.inputs()[0]
			rig = globalMove.rig.inputs()[0]

			if fitSkel.v.get() == 0 and rig.v.get() == 0:
				rig.v.set(1)
			elif fitSkel.v.get() == 1 and rig.v.get() == 1:
				fitSkel.v.set(0)
			elif fitSkel.v.get() == 0:
				fitSkel.v.set(1)
				rig.v.set(0)
			elif rig.v.get() == 0:
				fitSkel.v.set(0)
				rig.v.set(1)
		else:
			raise Exception('Global move not found.')
	toggleVisButton.setCommand(toggleVis)
	#================================================================================================


	def twoPointFitNode(*args):
		reload (axmn_fitRig)
		axmn_fitRig.fitNodeTwoPointIK(ls(sl=1)) #startEnd
	twoPntButton.setCommand(twoPointFitNode)

	def threePointFitNode(*args):
		reload (axmn_fitRig)
		axmn_fitRig.fitNodeThreePointIK(ls(sl=1)) #startMidEnd
	threePntButton.setCommand(threePointFitNode)

	def splineFitNode(*args):
		reload (axmn_fitRig)
		axmn_fitRig.fitNodeSpline(ls(sl=1)) #startEnd
	splineButton.setCommand(splineFitNode)

	def footFitNode(*args):
		reload (axmn_fitRig)
		axmn_fitRig.fitNodeFoot(ls(sl=1)) #startEnd
	footButton.setCommand(footFitNode)

	def deleteFitRig(*args):
		'''
		To Do:
		Make sure only the primary joint selection deletes the fit rig.  Shared joints are killing multiple at a time
		'''
		# Delete fitNode
		# Get fit node
		fitNodes = getFitNodes(ls(sl=1))
		for fitNode in fitNodes:
			rb.deleteOtherInstances(fitNode)
			rb.deleteByAttrOutput(fitNode, 'fitNodes')
			delete(fitNode)
	delFitRigButton.setCommand(deleteFitRig)

	def selectFitNodes(*args):
		# All
		selection = getFitNodes()
		select(selection)
	selectFitNodesButton.setCommand(selectFitNodes)

	#================================================================================================

	def buildAll(*args):
		#Build Rig
		reload (axmn_buildRig)
		selection = getFitNodes()
		for sel in selection:
			if sel.rigType.get() == 'twoPointIK':
				axmn_buildRig.rigBuildTwoPointIK(sel)
			if sel.rigType.get() == 'spline':
				axmn_buildRig.rigBuildSpline(sel)
			if sel.rigType.get() == 'threePointIK':
				axmn_buildRig.rigBuildThreePointIK(sel)
	buildAllButton.setCommand(buildAll)

	def buildSelected(*args):
		#Build Rig
		reload (axmn_buildRig)
		with UndoChunk():
			# Selection
			selection = getFitNodes(initSelection=ls(sl=1))
			# selection = ls(sl=1)
			for sel in selection:
				if sel.rigType.get() == 'twoPointIK':
					axmn_buildRig.rigBuildTwoPointIK(sel)
				if sel.rigType.get() == 'spline':
					axmn_buildRig.rigBuildSpline(sel)
				if sel.rigType.get() == 'threePointIK':
					axmn_buildRig.rigBuildThreePointIK(sel)
				if sel.rigType.get() == 'spaceSwitch':
					axmn_spaceSwitch2.axmn_spaceSwitch(sel)
				if sel.rigType.get() == 'footRoll':
					axmn_buildRig.rigBuildFootRoll(sel)
	buildSelectedButton.setCommand(buildSelected)

	def deleteSelectedRigNode(*args):
		selection = ls(sl=1)
		count = 0
		for sel in selection:
			if hasAttr(sel, 'rigNode', checkShape=0):
				rigNode = sel.rigNode.inputs(shapes=1)
				if len(rigNode):
					rb.deleteOtherInstances(rigNode[0])
					rb.deleteByAttrOutput(rigNode[0], 'rigNodes')
					count = count+1
		if count == 0:
			raise Exception('No rigNode found.')
	deleteBuild.setCommand(deleteSelectedRigNode)

	def selectRigNodes(*args):
		if objExists('rigNodeSet'):
			rigNodes = sets('rigNodeSet', q=1)
			select(rigNodes, r=1)
		else:
			warning("No rigNodes or no rigNode set found in scene.")
		
	selectBuildNodesButton.setCommand(selectRigNodes)

	def deleteAllRigNodes(*args):
		if objExists('rigNodeSet'):
			rigNodes = sets('rigNodeSet', q=1)
			for rigNode in rigNodes:
				print rigNode
				rb.deleteOtherInstances(rigNode)
				rb.deleteByAttrOutput(rigNode, 'rigNodes')
		else:
			warning("No rigNodes or no rigNode set found in scene.")
	deleteAll.setCommand(deleteAllRigNodes)
		



	#================================================================================================
	def spaceSwitchNode(*args):
		# FitNode space switch
		axmn_fitRig.fitRigSpaceSwitch()
	spaceSwitchNodeButton.setCommand(spaceSwitchNode)

	def spaceSwitchBuild(*args):
		# Build spaceSwitch
		selection = ls(sl=1)
		for sel in selection:
			axmn_spaceSwitch2.axmn_spaceSwitch(sel)
	spaceSwitchBuildButton.setCommand(spaceSwitchBuild)

	ui.show()