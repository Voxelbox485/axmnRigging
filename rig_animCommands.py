from pymel.core import *

def ui():
	'''
	

	if window('axmn_AnimCommands', exists=1):
		deleteUI('axmn_AnimCommands')
	width = 175
	buttonHeight = 30

	ui = window('axmn_AnimCommands', t='Anim Commands', width=width, h=300, resizeToFitChildren=1, sizeable=1, mxb=0)

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
	
	column.redistribute()


	'''




def getAllRigNodes(rigType=None, changeSelection=True, namespace='', setName='rigNodeSet'):
	rigNodes = []
	rigNodesFound = False
	if setName:
		if len(ls(setName))==1:
			for node in ls(setName)[0]:
				if not isinstance(node, nt.ObjectSet):
					rigNodes.append(node)
					rigNodesFound = True
		else:
			warning('No sets with rigNode setName found.')
	
	if rigType:
		typedRigNodes = []
		for rigNode in rigNodes:
			# If rigType specified
			if rigNode.rigType.get() is rigType:
				if rigNode not in typedRigNodes:
					typedRigNodes.append(rigNode)
		rigNodes = typedRigNodes

	if len(rigNodes):
		if changeSelection:
			select(rigNodes)

	else:
		if rigNodesFound:
			raise Exception('No Rignodes of selected type found.')
		else:
			raise Exception('No Rignodes found.')

	return rigNodes


def getRigNodesFromSelection(rigType=None, selection=None, changeSelection=True):
	
	if selection is None:
		selection = ls(sl=1)

	dev=1

	rigNodes = []
	rigNodesFound = False

	# Error check
	# Make sure selection is a list
	if not isinstance(selection, list):
		selection=[selection]
	
	if not len(selection):
		raise Exception('No selection specified.')
	# Check to make sure all of them work
	for i, sel in enumerate(selection):
		if not isinstance(sel, PyNode):
			if not len(ls(sel)):
				raise Exception('Object not found: %s' % sel)
			elif len(ls(sel)) > 1:
				raise Exception('More than one object found: %s' % sel)
			else:
				# Handler for string inputs
				selection[i] = ls(sel)[0]

	# Add all rig nodes found in selection to the pile
	for sel in selection:
		if hasAttr(sel, 'message'):
			if not len(sel.message.outputs()):
				continue

			selNode = None
			rigNode = None
			for outp in sel.message.outputs():
				if objectType(outp, isType='network') and hasAttr(outp, 'rigNode'):
					selNode = outp
					break
			if selNode:
				rigNode = selNode.rigNode.listConnections(sh=True)[0]

			if not rigNode in rigNodes:
				rigNodes.append(rigNode)
				rigNodesFound = True

	# Cull by rigType
	if rigType:
		typedNodes = []
		for rigNode in rigNodes:
			if rigNode.rigType.get() == rigType:
				typedNodes.append(rigNode)
		rigNodes = typedNodes

	# Result
	if not len(rigNodes):
		if rigNodesFound:
			raise Exception( 'No RigNodes of correct type found on selected objects.' )
		else:
			raise Exception( 'No RigNodes found on selected objects.' )
	else:
		if changeSelection:
			select(rigNodes)

	print rigNodes
	return rigNodes


def rigNodeSelectionHandles(onOff, useSelection=False):
	if useSelection:
		rigNodes = getRigNodesFromSelection()
	else:
		rigNodes = getAllRigNodes()

	for rigNode in rigNodes:
		selNode = rigNode.selNode.get()
		rigGroup = selNode.rigGroup.get()
		rigGroup.displayHandle.set(onOff)


def followSwitch(selectedChannels=None):
	'''
	Based on selected attribute, toggle attribute value and snap transform to previous value
	'''
	dev = 1
	if dev: print '\n'

	with UndoChunk():
		
		selection = ls(sl=1)

		if selectedChannels == None:
			selectedChannels = channelBox('mainChannelBox', q=1, sma=1)

		if not len(selection):
			raise Exception('No objects selected')

		if selectedChannels is None:
			raise Exception('No attributes selected')


		warningCount = 0
		count = 0

		# Error check:
		# check if channel has min and max
		for channel in selectedChannels:
			if selection[-1].attr(channel).getMin() is None:
				raise Exception('No min value on %s' % channel)
			if selection[-1].attr(channel).getMax() is None:
				raise Exception('No max value on %s' % channel)
			if dev: print ' ATTRIBUTE: %s\n CHANNEL MIN: %s\n CHANNEL MAX: %s' % (channel, selection[-1].attr(channel).getMin(), selection[-1].attr(channel).getMax())

		for sel in selection:
			# get tranform values
			trans = xform(sel, q=1, rp=1, ws=1)
			rot = xform(sel, q=1, ro=1, ws=1)
			if dev:
				print trans
				print rot

			for channel in selectedChannels:
					if hasAttr(sel, channel):
						attribute = sel.attr(channel)
						try:
							minV = attribute.getMin()
							maxV = attribute.getMax()
							value = attribute.get()
							if dev: print ' MIN: %s\n MAX: %s\n VALUE: %s' % (minV, maxV, value)
							if value >= (maxV-minV)/2:
								if dev: print ' GREATER: %s' % ((maxV-minV)/2)
								attribute.set(minV)
							else:
								if dev: print ' LESS THAN: %s' % ((maxV-minV)/2)
								attribute.set(maxV)

							# translate to previous position
							move(sel, trans, rpr=1, ws=1)
							xform(sel, ro=rot, ws=1)
							print 'Switch successful on %s' % attribute
							count = count + 1

						except:
							warning('Errors occurred switching %s' % attribute)
							warningCount = warningCount+1


		if warningCount:
			warning('%s warnings: Check script editor.' % warningCount)


def OLDfkIkSwitch():
	'''
	Gathers data based on rigNode associated with selected character control.
	To do:
	check if rigNode shows up more than once
	
	'''
	with pm.UndoChunk():

		dev = 1
		if dev: print '\n'

		# Pull RigNodes from selection

		selection = pm.ls(sl=1)
		rigNodes = getRigNodesFromSelection(rigType='threePointIK', selection=selection, changeSelection=False)
		count = 0
		switchType = None
		for rigNode in rigNodes:
			if dev: print 'RigNode: %s' % rigNode

			# Get current fkIk value
			fkIk = rigNode.fkIk.get()
			if dev: print ' FK/IK Value: %s' % fkIk


			if fkIk < 0.5:
				switchType = 1
			else:
				switchType = 0

			switchString = [
			'IK ==> FK',
			'FK ==> IK'
			]

			print 'Running %s switch.' % switchString[switchType]

			# ==============FK to IK==============
			if switchType:
				import pymel.core.datatypes as dt
				# Locators (under fk controls, pointing to ik control orientation)
				fkLocators = [
				rigNode.FkToIkStart.inputs()[0],
				rigNode.FkToIkMid.inputs()[0],
				rigNode.FkToIkEnd.inputs()[0]
				]
				if dev: print fkLocators

				# Get ik controls
				ikControls = [
				rigNode.ikCtrls.outputs()[1],
				rigNode.ikCtrls.outputs()[2],
				rigNode.ikCtrls.outputs()[0]
				]
				if dev: print ikControls

				# Get current positions
				trans = []
				rot = []
				for loc in fkLocators:
					trans.append(pm.xform(loc, q=1, rp=1, ws=1))
					rot.append(pm.xform(loc, q=1, ro=1, ws=1))

				# Get current lengths
				lengthSM = rigNode.normalizedLengthSM.get()
				lengthME = rigNode.normalizedLengthME.get()

				ikControls[2].multLength1.set(lengthSM)
				ikControls[2].multLength2.set(lengthME)

				# Top
				pm.move(ikControls[0], trans[0], rpr=1, ws=1)
				# pm.xform(ikControls[0], ro=rot[0], ws=1)
				# Hand
				pm.move(ikControls[2], trans[2], rpr=1, ws=1)
				pm.xform(ikControls[2], ro=rot[2], ws=1)
				# PV
				# Vectors
				# transVec0 = trans[0]
				# transVec1 = trans[1]
				# transVec2 = trans[2]
				# SMVec = dt.Vector(transVec1 - transVec0)
				# SEVec = dt.Vector(transVec2 - transVec0)
				# dotP = SMVec.dot(SEVec)
				# dotP.normalize()
				# lenSE = SEVec.length()
				# SEVec.normalize()
				# projectionVector = dotP/lenSE
				# normalizedProjectionVector = lenSE * projectionVector
				# arrowVector = SMVec-normalizedProjectionVector

				# addVec = dt.Vector(1,1,1)
				# worldPosFinal = arrowVector+addVec

				# pvTransNode = createNode('transform', n='pvTransNodeTemp')
				# delete(pvTransNode)

				# pm.move(ikControls[1], worldPosFinal, rpr=1, ws=1)
				pm.move(ikControls[1], trans[1], rpr=1, ws=1)
				# to do: push out with vector somehow

				rigNode.fkIk.set(1)


			# ==============IK to FK==============
			else:
				# Fk controls
				fkControls = [
				rigNode.fkControlStart.inputs()[0],
				rigNode.fkControlMid.inputs()[0],
				rigNode.fkControlEnd.inputs()[0]
				]
				if dev: print fkControls

				# Ik joints
				ikLocators = [
				rigNode.IkToFkStart.inputs()[0],
				rigNode.IkToFkMid.inputs()[0],
				rigNode.IkToFkEnd.inputs()[0]
				]
				if dev: print ikLocators

				trans = []
				rot = []

				for joint in ikLocators:
					trans.append(pm.xform(joint, q=1, rp=1, ws=1))
					rot.append(pm.xform(joint, q=1, ro=1, ws=1))

				for i, ctrl in enumerate(fkControls):
					pm.move(ctrl, trans[i], rpr=1, ws=1)
					pm.xform(ctrl, ro=rot[i], ws=1)

				rigNode.fkIk.set(0)

			print '%s switch completed on %s' % (switchString[switchType], rigNode.shortName())
			count = count+1

		print 'FK/IK switches completed on %s rig partitions.' % count


def resetAll():
	for rigNode in getAllRigNodes(changeSelection=False):
		resetRigNode(rigNode=rigNode)
		resetControls(rigNode=rigNode)


def resetControls(selection=None, rigNode=None):
	controls = rigNodeControls(selection=selection, rigNode=rigNode, changeSelection=False)
	
	for ctrl in controls:
		setToDefault(ctrl)


def resetRigNode(selection=None, rigNode=None):
	
	if rigNode is None:
		rigNodes = getRigNodesFromSelection(selection=selection, changeSelection=False)
	else:
		rigNodes = [rigNode]

	for rigNode in rigNodes:
		setToDefault(rigNode, ignoreCBSelection=True)


def setToDefault(selection=None, ignoreCBSelection=False):
	if selection is None:
		selection = ls(sl=1)

	if not isinstance(selection, list):
		selection = [selection]

	for sel in selection:

		attrs = getFromChannelBox()
		if ignoreCBSelection or len(attrs) == 0:
			attrs = listAttr(sel, cb=1, output=1) + listAttr(sel, k=1, output=1)

		for attribute in attrs:
			if not hasAttr(sel, attribute):
				warning('Attribute not found on object: %s' % sel)
				break
			# Instantiate attribute
			attribute = sel.attr(attribute)
			
			defaultV = None

			if attribute.isFreeToChange():
				if attribute.isSettable():
					# if not attribute.isLocked():
					if attribute.isDynamic():

						# Get default value
						defaultV = addAttr(attribute, q=1, dv=1)

					else:
						transformAttrs = [
							'tx',
							'ty',
							'tz',
							'rx',
							'ry',
							'rz',
							'sx',
							'sy',
							'sz',
						]

						if attribute.shortName() in transformAttrs:
							defaultV = 0
							if attribute.shortName() in transformAttrs[6:]:
								defaultV = 1

			# Set default value
			if not defaultV is None:
				# print '%s.%s  =  %s' % (sel.nodeName(), attribute.longName(), defaultV)
				attribute.set(defaultV)




def getFromChannelBox():
	# Pulls longName strings of all selected attributes in channelbox
	
	# import maya.mel

	gChannelBox = 		melGlobals['gChannelBoxName']

	# Get selection to help determine attribute longName
	selection = ls(sl=1)

	# Store return list
	ret = []
	# Returns a list of strings, the names of all the selected attributes in the top section of the channel box.
	sma = channelBox(gChannelBox, q=1, sma=1)
	# Returns a list of strings, the names of all the selected attributes in the middle (shape) section of the channel box.
	ssa = channelBox(gChannelBox, q=1, ssa=1)
	# Returns a list of strings, the names of all the selected attributes in the INPUT section of the channel box.
	sha = channelBox(gChannelBox, q=1, sha=1)
	# Returns a list of strings, the names of all the selected attributes in the OUTPUT section of the channel box.
	soa = channelBox(gChannelBox, q=1, soa=1)
	
	# Get longnames from shortNames
	if sma:
		for sn in sma:
			# From last selected
			ret.append(selection[-1].attr(sn).longName())
	if ssa:
		for sn in ssa:
			# From all shapes of last selected
			shapes = selection[-1].getShapes()
			for s in shapes:
				if hasAttr(s, sn):
					if s.attr(sn).longName() not in ret:
						ret.append(s.attr(sn).longName())
	if sha:
		for sn in sha:
			# Get input list from channelbox (might be better to get from selection to avoid strings)
			strInputs = channelBox(gChannelBox, q=1, historyObjectList=1)
			inputs = []
			for strInput in strInputs:
				if len(ls(strInput)) > 1:
					# Probably fine. Just looking for attribute longname.
					warning('More than one Input matches name %s' % strInput)
				inputs.extend(ls(strInput))

			for i in inputs:
				if hasAttr(i, sn):
					if i.attr(sn).longName() not in ret:
						ret.append(i.attr(sn).longName())

		# ret.extend(soa)

	if soa:
		for sn in soa:
			# Get output list from channelbox (might be better to get from selection to avoid strings)
			strOutputs = channelBox(gChannelBox, q=1, outputObjectList=1)
			outputs = []
			for strOutput in strOutputs:
				if len(ls(strOutput)) > 1:
					# Probably fine. Just looking for attribute longname.
					warning('More than one output matches name %s' % strOutput)
				outputs.extend(ls(strOutput))

			for o in outputs:
				if hasAttr(o, sn):
					if o.attr(sn).longName() not in ret:
						ret.append(o.attr(sn).longName())


	return ret

def rigNodeControls(selection=None, rigNode=None, changeSelection=True):

	if selection is None and rigNode is None:
		selection = ls(sl=1)

	if rigNode is not None:
		selection = rigNode

	if not isinstance(selection, list):
		selection = [selection]

	rigNodes = getRigNodesFromSelection(selection=selection, changeSelection=False)

	if rigNode: rigNodes = [rigNode]

	# raise Exception(rigNodes[0].selNode.get())

	controlsList = []
	for rigNode in rigNodes:
		print rigNode.selNode.get()
		controlsList.append(rigNode.selNode.get().ctrlsList.get())
	
	if changeSelection:
		select(controlsList)

	return controlsList


def mirrorRigNodeAttributes():
	pass

#================================================================================================
#================================================================================================
#================================================================================================
#================================================================================================


def getRigNode(selection=None, rigType=None, changeSelection=True):
	if selection is None:
		selection = ls(sl=1)

	dev=1

	rigNodes = []
	rigNodesFound = False

	# Error check
	# Make sure selection is a list
	if not isinstance(selection, list):
		selection=[selection]
	
	if not len(selection):
		raise Exception('No selection specified.')
	# Check to make sure all of them work
	for i, sel in enumerate(selection):
		if not isinstance(sel, PyNode):
			if not len(ls(sel)):
				raise Exception('Object not found: %s' % sel)
			elif len(ls(sel)) > 1:
				raise Exception('More than one object found: %s' % sel)
			else:
				# Handler for string inputs
				selection[i] = ls(sel)[0]

	# Add all rig nodes found in selection to the pile
	for sel in selection:
		if hasAttr(sel, 'message'):
			if not len(sel.message.outputs()):
				continue

			selNode = None
			rigNode = None
			for outp in sel.message.outputs():
				if objectType(outp, isType='network') and hasAttr(outp, 'rigNode'):
					selNode = outp
					break
			if selNode:
				rigNode = selNode.rigNode.listConnections(sh=True)[0]

			if not rigNode in rigNodes:
				rigNodes.append(rigNode)
				rigNodesFound = True

	# Cull by rigType
	if rigType:
		typedNodes = []
		for rigNode in rigNodes:
			if rigNode.rigType.get() == rigType:
				typedNodes.append(rigNode)
		rigNodes = typedNodes

	# Result
	if not len(rigNodes):
		if rigNodesFound:
			raise Exception( 'No RigNodes of correct type found on selected objects.' )
		else:
			raise Exception( 'No RigNodes found on selected objects.' )
	else:
		if changeSelection:
			select(rigNodes)

	return rigNodes

def fkIkSwitch(dev=False):
	with UndoChunk():
		import pymel.core.datatypes as dt
		selection = ls(sl=1)

		rigNodes = getRigNode(rigType='threePointIK', changeSelection=False)
		
		# if dev: print rigNodes

		# if not a list, just pretend
		if not isinstance(rigNodes, list):
			rigNodes = [rigNodes]
		
		# Error checks
		for rigNode in rigNodes:
			selNode = rigNode.selNode.get()
			if not selNode:
				raise Exception('No selNode found: %s' % rigNode)
				
			fkCtrls = selNode.fkCtrls.get() 
			if not len(fkCtrls) == 3:
				raise Exception('Not enough fkCtrls specified in selNode: %s (%s)' % (selNode, fkCtrls))

			ikCtrls = selNode.ikCtrls.get()
			if not len(ikCtrls) == 3:
				raise Exception('Not enough ikCtrls specified in selNode: %s (%s)' % (selNode, ikCtrls))

			fkPoints = selNode.fkPoints.get()
			if not len(fkPoints) == 3:
				raise Exception('Not enough fkPoints specified in selNode: %s (%s)' % (selNode, fkPoints))

			ikPoints = selNode.ikPoints.get()
			if not len(ikPoints) == 3:
				raise Exception('Not enough ikPoints specified in selNode: %s (%s)' % (selNode, ikPoints))

		# Seperate data collection and application for baking?
		# List of dictionaries
		# data = []
		for rigNode in rigNodes:
			# mirror = True if rigNode.side.get()
			selNode = rigNode.selNode.get()
			# ========================== FK ---> IK ========================== 
			if rigNode.fkIk.get() < 0.5:
				
				# =========================
				# Data gather
				ikMatrices = []
				ikPoints = rigNode.selNode.get().ikPoints.get()
				# ikPoints = [ikPoints[0], ikPoints[2], ikPoints[1]]
				noramlizedCurrentDists = []
				
				for i, point in enumerate(ikPoints):
					ikMatrices.append(xform(point, q=1, ws=1, m=1))
					
					# Get normalized lengths to apply to ik multLength
					if not i==0:
						noramlizedCurrentDists.append(dt.length(selNode.switchJoints.get()[i].translate.get())/dt.length(selNode.switchJoints.get()[i].defaultTranslate.get()))

				# fk2ikDictionary = {'rigNode': rigNode, 'selNode': selNode, style: 'fk2ik', 'fkMatrices': fkMatrices} # 'frame': getCurrentFrame()}
				
				# =========================
				# Action
				ikCtrls = selNode.ikCtrls.get()
				# Change to desired settings
				# ikCtrls[2].stretch.set(1)
				# ikCtrls[2].swivelPV.set(0).set(1)
				
				# set values
				# mult length
				ikCtrls[2].multLength1.set(noramlizedCurrentDists[0])
				ikCtrls[2].multLength2.set(noramlizedCurrentDists[1])

				# Calculate pv position
				if dev: print selNode.switchJoints.get()
				startV = dt.Vector(xform(selNode.switchJoints.get()[0], q=1, ws=1, t=1))
				midV   = dt.Vector(xform(selNode.switchJoints.get()[1], q=1, ws=1, t=1))
				endV   = dt.Vector(xform(selNode.switchJoints.get()[2], q=1, ws=1, t=1))
				if dev:
					print 'startV: %s' % startV
					print 'midV: %s' % midV
					print 'endV: %s' % endV

				# Get halfway point between result joints to drive initial positions
				# midFactor = 0.5
				# midFactor =  (endV - startV).length() / (midV - startV).length()
				line = (endV - startV)
				point = (midV - startV)

				midFactor = (line * point) / (line * line)
				print 'midFactor: %s' % midFactor

				projVec = (endV - startV) * midFactor + startV
				print 'projVec: %s' % projVec

				startMidL = (midV - startV).length()
				midEndL = (endV - midV).length()
				if dev:
					print 'startMidL: %s' % startMidL
					print 'midEndL: %s' % midEndL

				totalLength =  startMidL + midEndL

				pvPos = (midV - projVec).normal() * totalLength + midV
				if dev: print pvPos

				rigNode.fkIk.set(1)

				ikCtrlsSnap = [ikCtrls[0], ikCtrls[2], ikCtrls[1]]
				for ikMatrix, ctrl in zip ( [ikMatrices[0], ikMatrices[2], ikMatrices[1]], ikCtrlsSnap ):
						xform(ctrl, ws=1, m=ikMatrix)


				move(ikCtrls[1], pvPos, ws=1, rpr=1)
				# xform(ikCtrls[1], ws=1, t=pvPos)



			# ========================== IK ---> FK ========================== 
			else: 
				# gather data
				fkMatrices = []
				for point in rigNode.selNode.get().fkPoints.get():
					fkMatrices.append(xform(point, q=1, ws=1, m=1))

				# ik2fkDictionary = {'rigNode': rigNode, 'selNode': selNode, style: 'ik2fk', 'ikMatrices': ikMatrices} # 'frame': getCurrentFrame()}
				# =========================

				rigNode.fkIk.set(0)

				# set values
				for fkMatrix, ctrl in zip ( fkMatrices, selNode.fkCtrls.get() ):
					xform(ctrl, ws=1, m=fkMatrix)


		# select(rigNode.selNode)