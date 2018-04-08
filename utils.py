from pymel.core import *
import colorOverride as col

loadPlugin( 'matrixNodes.mll', qt=True)
loadPlugin( 'quatNodes.mll', qt=True)

'''
A hotkey to graph everything forward or backward of nodes connected to selected attribute
maximize node editor
create new graph unless current one is empty
get cb selection
add item(s) selected
add cb selection (>> or <<)
add items after

Split ctrlSetupStandard into parts (or kill it?)

Cast nodes: replaces all inputs/outputs with other type
holyy

# ls(sl=1)[0].cast(ls(sl=1)[1])

isUniquelyNamed()
nextUniqueName()
	Increment the trailing number of the object until a unique name is found
nextName()
	Increment the trailing number of the object by 1
prevName()
	Decrement the trailing number of the object by 1

sources()
stripNum()

'''
def selectCBInputs(selection=None):
	newSelList = []
	with UndoChunk():
		if selection is None:
			selection = ls(sl=1)
		if not isinstance(selection, list):
			selection = [selection]

		cbList = getFromChannelBox()
		for sel in selection:
			for attributeString in cbList:
				if hasAttr(sel, attributeString):
					for inp in sel.attr(attributeString).inputs():
						if not inp in newSelList:
							newSelList.append(inp)
		if len(newSelList):
			select(newSelList, r=1)
			print ('%s items selected: %s' % (len(newSelList), newSelList))
		else:
			warning('No input nodes found.')
	return newSelList

def selectCBOutputs(selection=None):
	newSelList = []
	with UndoChunk():
		if selection is None:
			selection = ls(sl=1)
		if not isinstance(selection, list):
			selection = [selection]

		cbList = getFromChannelBox()
		for sel in selection:
			for attributeString in cbList:
				if hasAttr(sel, attributeString):
					for outp in sel.attr(attributeString).outputs():
						if not outp in newSelList:
							newSelList.append(outp)
		if len(newSelList):
			select(newSelList, r=1)
			print ('%s items selected: %s' % (len(newSelList), newSelList))
		else:
			warning('No output nodes found.')
	return newSelList


def getFromChannelBox():

	gChannelBox = 		melGlobals['gChannelBoxName']
	# Pulls longName strings of all selected attributes in channelbox
	
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
		# print 'sma'
		for sn in sma:
			# From last selected
			ret.append(selection[-1].attr(sn).longName())
	if ssa:
		# print 'ssa'
		for sn in ssa:
			# From all shapes of last selected
			shapes = selection[-1].getShapes()
			for s in shapes:
				# print 'sn'
				# print sn
				if hasAttr(s, sn):
					if s.attr(sn).longName() not in ret:
						ret.append(s.attr(sn).longName())
	if sha:
		# print 'sha'
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
		# print 'soa'
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

def rjt():
	selection = ls(sl=1, type='joint')
	for sel in selection:
		for jointOrientAttr, jointRotAttr in zip(sel.jointOrient.getChildren(), sel.rotate.getChildren()):
			jointOrientAttr.set(jointRotAttr.get())
			jointRotAttr.set(0)

def constructNames(namesDict):
	# Use text inputs and variables and piece together an editable naming system
	
	# 'fkIkAutoMult':           	{'desc': globalName, 'warble': 'mult',	'other': ['fkIkAuto', 'vis']

	preset = 0
	# 0  --  arm_L_fkIkAuto_vis_MULT
	# 1  --  LF_Mult_arm_fkIkAuto_vis

	# Presets
	warbleDict = {
	'ctrl': 			['CTRL', 			'Ctl', ],
	'extra': 			['EXTRA', 			'Extra', ],
	'const': 			['CONST', 			'Const', ],
	'buf':	 			['BUF', 			'Buf', ],
	'grp': 				['GRP', 			'Grp', ],
	'jnt': 				['JNT', 			'Jnt', ],
	'meta':				['META',			'Meta', ],
	'loc':				['LOC',				'Loc', ],
	'add':				['ADD',				'Add', ],
	'div':				['DIV',				'Div', ],
	'clmp':				['CLMP',			'Clmp', ],
	'sub':				['SUB',				'Sub', ],
	'pow':				['POW',				'Pow', ],
	'rev':				['REV',				'Meta', ],
	'mult':				['MULT',			'Mult', ],
	'matC':				['MCOMP',			'MatC', ],
	'matD':				['MDECMP',			'MatD', ],
	'matM':				['MMULT',			'MatM', ],
	'rng':				['RNG',				'Rng', ],
	'selNode':			['selNode',			'selNode', ],
	'rigNode':			['rigNode',			'rigNode', ],
	'rigGroup':			['rigGroup',		'rigGroup', ],
	'controlsGroup':	['controlsGroup',	'controlsGroup', ],
	'worldGroup':		['worldGroup',		'worldGroup', ],
	'bind':				['BND', 			'Out_Jnt']
	}

	caseDict = [2, 1]

	sideDict = {
	0:		['_M', 'MD'],
	1:		['_L', 'LF'],
	2:		['_R', 'RT'],
	3:		['', '']
	}
	
	nodeTags = []
	dictValue = []
	# Split dictionaries
	for nodeTag in namesDict:
		nameDict = namesDict[nodeTag]
		# if self.dev:
		# 	print 'nodeTag'
		# 	print nodeTag
			# print namesDict[nameDict]

		# Error check
		if not nameDict.has_key('desc'):
			raise Exception('Dictionary key not found: Desc -- %s' % nameDict)
		if not nameDict.has_key('warble'):
			raise Exception('Dictionary key not found: Warble -- %s' % nameDict)

		# if warble not found in warbleDict, default to whatever was sent in, and set case
		try:
			side = nameDict['side']
		except:
			side = 3

		# if warble not found in warbleDict, default to whatever was sent in, and set case
		if nameDict['warble'] is None:
			warble = ''
		else:
			try:
				warble = '%s' % warbleDict[ nameDict['warble'] ][preset]
			except:
				# Auto capitalize
				warble = '%s' % [
				nameDict['warble'].lower(),
				nameDict['warble'].capitalize(),
				nameDict['warble'].upper()
				][caseDict[preset]]
			if preset == 0:
				warble = '_' + warble
			if preset == 1:
				warble = warble + '_'
		# if self.dev: print 'Warble: %s ' % warble

		other = ''
		if nameDict.has_key('other'):
			if len(nameDict['other']):
				other = '_%s' % '_'.join(nameDict['other'])
				# for o in nameDict['other']:
				# 	other.append(o)

		nodeTags.append(nodeTag)

		if preset==0:
			dictValue.append('%s%s%s%s' % (nameDict['desc'], sideDict[side][preset], other, warble) )

		elif preset==1:
			dictValue.append('%s%s%s%s' % (sideDict[side][preset], warble, other, nameDict['desc']) )





	# 	other = []

	# 	if nameDict.has_key('other'):
	# 		for o in nameDict['other']:
	# 			# other.append([nameDict['other'][i].lower(), nameDict['other'][i].capitalize(), nameDict['other'][i].upper()][caseDict[preset]])
	# 			other.append(o)


	# 	# Preset 0	
	# 	if preset == 0:
	# 		# print 'NAME: %s' % nameDict['name']
	# 		# print 'SIDE: %s' % sideDict[side][preset]
	# 		# print 'WARBLE: %s' % warble
	# 		# print 'OTHER: %s' % '_'.join(other)
	# 		# Create string from other.  Add initial '_' if not empty.
	# 		if len(other):
	# 			otherStr = '_' + '_'.join(other)
	# 		else:
	# 			otherStr = ''

	# 		newNames.append('%s%s%s%s' % (nameDict['name'], sideDict[side][preset], warble, otherStr ) )
		
	# 	# Preset 1
	# 	elif preset == 1:
	# 		newNames.append('%s%s%s' % (sideDict[side[preset]], warble, nameDict['name'], ''.join(other)) )
	# 	else:
	# 		raise Exception('Preset is out of range')

	# # Assemble result dictionary
	

	retDict = dict(zip(nodeTags, dictValue))
	# if self.dev:
	# 	print '\nNAMES CONSTRUCTION:'
	# 	for i in range(len(retDict)):
	# 		print nodeTags[i] + ': ' + dictValue[i]
	# 	print '\n'
	return retDict


def mirrorMatrix(transform, setTransform):
	matrix = transform.getMatrix(worldSpace=True)

	reflectionMatrix_YZ = dt.Matrix(-1.0,0.0,0.0,0.0, 0.0,1.0,0.0,0.0, 0.0,0.0,1.0,0.0, 0.0,0.0,0.0,1.0)

	newMatrix = matrix * reflectionMatrix_YZ

	setTransform.setMatrix(newMatrix , worldSpace=True)
	if self.dev:
		print newMatrix.formated()
		print currentSelection2.getMatrix(worldSpace=True).formated()



def snap(src, dest, t=True, r=True, s=True):
	if all([t, r, s]):
		xform(dest, ws=1, m=xform(src, q=1, ws=1, m=1))
	else:
		if t:
			xform(dest, ws=1, rp=xform(src, q=1, ws=1, rp=1))

		if r:
			xform(dest, ws=1, ro=xform(src, q=1, ws=1, ro=1))

		if s:
			xform(dest, ws=1, s=xform(src, q=1, ws=1, s=1))
		


#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================


def cbSep(node, name=None, ct=None):
	if node is None:
		raise Exception('No object specified or selected')
	else:
		if name == None:
			name = "__________"
		en = ".................................................."
		success = 0
		while success == 0:
			if hasAttr(node, name):
				name = name + '_'
			else:
				success = 1
		addAttr(node, at='enum', ln=name, nn=en, en=en, ct=ct, keyable=False)
		setAttr('%s.%s' % (node, name), channelBox=True, keyable=False)

 
#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================

def ctrlSetupStandard(selection=None, pivot=True, ro=True, vis=True, ctrlSet='controlSet', globalCtrl='globalMove_CTRL'):
	with UndoChunk():

		dev = 0
		warnCount = 0
		visOld = False
		freezeList = []
		
		if globalCtrl is not None:
			if len(ls(globalCtrl)) == 1:
				globalCtrl = ls(globalCtrl)[0]
				if pivot:
					if not hasAttr(globalCtrl, 'showPivotOffsets'):
						addAttr(globalCtrl, ln='showPivotOffsets', at='short', min=0, max=1, dv=1, k=1)
						globalCtrl.showPivotOffsets.set(k=0, cb=1)
			elif len(ls(globalCtrl)) > 1:
				raise Exception('More than one object matches name: %s' % globalCtrl)
			else:
				warning('No objects match name: %s' % globalCtrl)
				globalCtrl = None


		if selection == None:
			selection = ls(sl=1)
		if not isinstance(selection, list):
			selection = [selection]
		
		# reorder selection so that furthest down heirarchy goes first?

		for sel in selection:
			# if sel.getShapes()[0].overrideRGBColors.get() == 1:
			sel.overrideEnabled.set(1)
			sel.overrideColor.set(1)
			# Check if transform
			if dev: print sel.__class__
			if not isinstance(sel, nodetypes.Transform):
				warning('Object: %s is not a tranform.' % sel)
				warnCount = warnCount+1

			else:
				if pivot:
					if sel.rotateX.isLocked() and sel.rotateY.isLocked() and sel.rotateZ.isLocked():
						sel.rotatePivotTranslateX.set(l=1)
						sel.rotatePivotTranslateY.set(l=1)
						sel.rotatePivotTranslateZ.set(l=1)
						sel.rotatePivotX.set(l=1)
						sel.rotatePivotY.set(l=1)
						sel.rotatePivotZ.set(l=1)
					else:
						sel.rotatePivotX.set(l=0, k=1)
						sel.rotatePivotY.set(l=0, k=1)
						sel.rotatePivotZ.set(l=0, k=1)
						if not isConnected(sel.rotatePivotX, sel.scalePivotX):
							sel.rotatePivotX.connect(sel.scalePivotX, f=1)
						if not isConnected(sel.rotatePivotY, sel.scalePivotY):
							sel.rotatePivotY.connect(sel.scalePivotY, f=1)
						if not isConnected(sel.rotatePivotZ, sel.scalePivotZ):
							sel.rotatePivotZ.connect(sel.scalePivotZ, f=1)
						sel.rotatePivotTranslateX.set(l=1)
						sel.rotatePivotTranslateY.set(l=1)
						sel.rotatePivotTranslateZ.set(l=1)

					if sel.scaleX.isLocked() and sel.scaleY.isLocked() and sel.scaleZ.isLocked():
						sel.scalePivotX.set(l=1)
						sel.scalePivotY.set(l=1)
						sel.scalePivotZ.set(l=1)

						# globalCtrl.showPivotOffsets >>  sel.displayRotatePivot


					# Pivot vis indicator

					name1 = '%s_pivotVis1' % sel.shortName()
					name2 = '%s_pivotVis2' % sel.shortName()

					# attributes
					if not hasAttr(sel, 'pivotVis1'):
						addAttr(sel, ln='pivotVis1', at='message', hidden=1, k=0)
					if not hasAttr(sel, 'pivotVis2'):
						addAttr(sel, ln='pivotVis2', at='message', hidden=1, k=0)

					pivotAttrs = {'overrideEnabled': 1, 'overrideDisplayType': 1, 'radius': 0}
					
					if len(sel.pivotVis1.inputs()):
						pivotStart = sel.pivotVis1.inputs()[0]
					else:
						pivotStart = createNode('joint', p=sel)
						freezeList.append(pivotStart)
						pivotStart.message.connect(sel.pivotVis1)
						if globalCtrl:
							globalCtrl.showPivotOffsets >>  pivotStart.v

					if len(sel.pivotVis2.inputs()):
						pivotEnd = sel.pivotVis2.inputs()[0]
					else:

						pivotEnd = createNode('joint', p=pivotStart)
						freezeList.append(pivotEnd)
						sel.rotatePivot >> pivotEnd.translate
						pivotEnd.message.connect(sel.pivotVis2)
						if globalCtrl:
							globalCtrl.showPivotOffsets >>  pivotEnd.v

					
					pivotStart.rename(name1)
					pivotEnd.rename(name2) # Just in case

					setAttrsWithDictionary(pivotStart, pivotAttrs)
					setAttrsWithDictionary(pivotEnd, pivotAttrs)

				if ro:
					sel.rotateOrder.set(k=0, cb=1)

				if globalCtrl:
					if vis:
						sel.v.set(l=0, k=1)
						
						#####
						if not hasAttr(globalCtrl, 'visSDK'):
							addAttr(globalCtrl, ln='visSDK', at='message', k=0, h=1)

						sel.v.set(l=0)

						if not globalCtrl.visSDK.get():
							# If not already initiated, create Set driven key
							import maya.cmds as cmds
							# set sdk 0
							cmds.setDrivenKeyframe( '%s.visibility' % sel.longName(), driverValue=0, value=0, cd='%s.visibility' % globalCtrl.longName(), inTangentType='linear', outTangentType='step' )
							# set sdk 1
							cmds.setDrivenKeyframe( '%s.visibility' % sel.longName(), driverValue=1, value=1, cd='%s.visibility'% globalCtrl.longName(), inTangentType='linear', outTangentType='step' )
							
							visSDK = sel.visibility.inputs()[0]
							visSDK.rename('%s.visibility' % globalCtrl.longName())
							visSDK.message.connect(globalCtrl.visSDK)
							visSDK.ktv.set(l = 1) # template channel
						else:
							visSDK = globalCtrl.visSDK.get()
							visSDK.output.connect(sel.visibility)

						# Hide control
						sel.v.set(1)
						sel.v.set(k=0, cb=0)
						####



				# print '%s' % sel
				# FitNode Set
				if ctrlSet is not None:
					if ctrlSet is not '':
						if not objExists(ctrlSet):
							controlSet = sets([sel], n=ctrlSet)
						else:
							controlSet = sets(ctrlSet, e=True, forceElement=sel)

				if len(freezeList):
					lockAndHide(freezeList, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'])



		if warnCount > 0:
			warning('Warnings logged. Check your script editor.')
		select(selection)

def blendWrap(wrapped, bs, newBs=None, blendsGroup=None):
	dev=1

	base = bs.getBaseObjects()[0]
	newBase = duplicate(wrapped, n=wrapped.nodeName()+'_new')[0]
	if blendsGroup:
		parent(newBase, blendsGroup)

	# Create an empty blendshape on new base
	if newBs is None:
		newBs = blendShape(newBase)[0]
		print newBs

	# data
	if dev:
		print '\n'
		print 'BASE OBJECTS: %s' % base
		print 'ORIGIN: %s' % bs.getOrigin()
		print 'NUM WEIGHT: %s' % bs.numWeights()
		print 'INDEX LIST: %s' % bs.weightIndexList()
		print 'GEO: %s ' % bs.getGeometry()
		print 'TARGET: %s ' % bs.getTarget()

		print '\n'

	# Return a dictionary containting:
	# blendshape attribute
	# input attribute
	# output attribute
	# weight index
	attrDict = {}
	for c in bs.weight.elements():
		if dev:
			print '\n'
			print c
		# print bs.weight.attr(c).inputs()
		# Inputs:
		attr = bs.weight.attr(c)
		weight = bs.weight.attr(c).index()
		inp = listConnections(bs.weight.attr(c), p=1, sh=1, scn=1, s=1, d=0)
		outp = listConnections(bs.weight.attr(c), p=1, sh=1, scn=1, s=0, d=1)
		attrDict[attr] = (c, inp, outp, weight)

		if dev:
			print '%s >> %s >> %s' % (inp, attr.longName(), outp)
	if dev:
		print 'DICTIONARY:'
		print attrDict

	# Disconnect attributes once we have dictionary
	for c in bs.weight.elements():
		attr = bs.weight.attr(c)
		attr.set(l=0)
		# Disconnect
		attr.disconnect()
		attr.set(0)
	
	# For each
	for attr in attrDict:
		if dev:
			print '\n'
			# print base
			print attr
		oldName = attrDict[attr][0]
		inp = attrDict[attr][1]
		outp = attrDict[attr][2]
		weight = attrDict[attr][3]

		newName = '%s_new' % oldName

		# Turn on each blendshape, and duplicate wrapped shape
		attr.set(1)
		new = duplicate(wrapped, n=newName)[0]
		if blendsGroup:
			parent(new, blendsGroup)

		attr.set(0)

		if dev:
			print inp
			print attr
			print outp
			print 'SHAPE'
			print new.getShapes()[0]

		# newBs.addTarget(baseObject=newBase.getShapes()[0], weightIndex = weight, newTarget=new.getShapes()[0], fullWeight=1)

		# newAttr = newBs.weight[weight]

		# If there were inputs, reconnect
		if isinstance(inp, list):
			for i in inp:
				i.connect(attr)
		elif inp is not None:
			inp.connect(attr)

		if isinstance(outp, list):
			for o in outp:
				attr.connect(o)
		elif outp is not None:
			attr.connect(outp)

		# And connect all blendshape attributes directly to new blendshape
		# attr.connect(newAttr)

		# newAttr.set(0)
	


#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================


def multAttrRange(attribute=None):
	'''
	Based on selected channel box attribute or input, edit minimum and maximum value and adjust output so nothing else changes
	Finish this
	'''
	with UndoChunk():
		if attribute is None:
			attribute = channelBox(q=1, sma=1)
		if not isinstance(attribute, list):
			attribute=[attribute]
		for att in attribute:
			sr = createNode('setRange', n=attribute.name())


def selectOutputs(attribute=None):
	# select all outputs from selected attribute
		with UndoChunk():
			returnList = []
			selection = ls(sl=1)
			if attribute is None:
				attribute = channelBox('mainChannelBox', q=1, sma=1)
			if not isinstance(attribute, list):
				attribute=[attribute]

			print attribute

			select(cl=1)
			for sel in selection:
				for attrib in attribute:
					print sel.attr(attrib)
					select(sel.attr(attrib).outputs(sh=1), add=1)
					returnList.append(sel.attr(attrib).outputs(sh=1))
			print returnList
			return returnList



#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================

def localRotationAxisToggle(display=0, objects=None):
	# Applies local rotation axis display to all transforms, or all transforms defined by objects input
	if objects is None:
		dagObjs = ls(dagObjects=1, type='transform')
	else:
		dagObjs = objects
		if not isinstance(dagObjs, list):
			dagObjs = [dagObjs]
	for obj in dagObjs:
		if not isinstance(obj, PyNode):
			print ('%s is not a PyNode' % obj)
		if hasAttr(obj, 'displayLocalAxis'):
			try:
				obj.displayLocalAxis.set(onOff)
			except:
				warning('%s.displayLocalAxis could not be set' % obj)

#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================


def setAttrsWithDictionary(node, setAttrs):
	# Use dictionary input to set attributes of specified nodes
	if node:
		for attribute, val in setAttrs.items():
			if hasAttr(node, attribute):
				PyNode( node ).attr( attribute ).set(val)
			else:
				raise Exception ('Attribute doesnt exist: ' + attribute)
	else:
		raise Exception('Verify inputs.')

#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================


def lockAndHide(objs, attrs):

	if not isinstance(objs, list):
		objs = [objs]

	newObjs = []
	for obj in objs:
		if isinstance(obj, str) or isinstance(obj, unicode):
			newObj = ls(obj)
			if not len(newObj):
				warning('Object could not be found: %s' % obj)
			if len(newObj) > 1:
				warning('More than one object found with name: %s' % newObj)

			newObjs.extend(newObj)
		else:
			newObjs.append(obj)

	for obj in newObjs:
		for attribute in attrs:
			try:
				if hasAttr(obj, attribute):
					obj.attr(attribute).set(lock=True, keyable=False, channelBox=False)
			except TypeError:
				try:
					raise TypeError('Object: %s and attribute: %s returned a TypeError.' % (obj, attribute))
				except:
					raise TypeError('Object: %s returned a TypeError.' % obj)



#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================


def createHiddenDisplayLayer(name, nodes, colorIndex=None, colorRGB=None, visibility=None, displayType=None):

	lyr = createNode('displayLayer', n=name)
	
	if not colorIndex is None:
		lyr.color.set('Index')
		lyr.colorIndex.set(colorIndex)
	if not colorRGB is None:
		lyr.color.set('RGB')
		lyr.colorRGB.set(colorRGB)
	if not displayType is None:
		lyr.displayType.set(displayType)
	if not visibility is None:
		lyr.visibility.set(visibility)

	for node in nodes:
		displayLayer.drawInfo.connect(node.drawOverride)

	return lyr
#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================


def messageConnect(sourceNodes, sourceAttr, destNodes, destAttr, sourceParent=None, destParent=None):
	'''Connect sourceNode.sourceAttr message to each destNode.destAttr message'''

	dev=False

	# ====== Error checks ======
	if not all([sourceNodes, sourceAttr, destNodes, destAttr]):
		raise Exception('Verify arguments')
	# List check - if not a list, convert to a list
	sourceNodeisList=False
	if isinstance(sourceNodes, tuple) or isinstance(sourceNodes, list):
		sourceNodeisList=True
	if not sourceNodeisList:
		sourceNodes = [sourceNodes]

	destNodeisList=False
	if isinstance(destNodes, tuple) or isinstance(destNodes, list):
		destNodeisList=True
	if not destNodeisList:
		destNodes = [destNodes]

	# Check attributes
	for sourceNode in sourceNodes:
		if hasAttr(sourceNode, sourceAttr):
			try:
				if not PyNode( sourceNode ).attr( sourceAttr ).isType('message'):
					raise Exception('%s.%s found - Not of message type' % (sourceNode, sourceAttr))
			except:
				pass
		else:
			if sourceParent is not None:
				addAttr(sourceNode, ln=sourceAttr, at='message', keyable=False, hidden=True, parent=sourceParent)
			else:
				addAttr(sourceNode, ln=sourceAttr, at='message', keyable=False, hidden=True)


	for destNode in destNodes:
		if dev:
			print '%s.%s >> %s.%s' % (sourceNode, sourceAttr, destNode, destAttr)
		if not isinstance(destNode, PyNode):
			raise Exception('%s is not a Pynode' % destNode)
		if hasAttr(destNode, destAttr):
			try:
				if not PyNode( destNode ).attr( destAttr ).isType('message'):
					raise Exception('%s.%s found - Not of message type' % (destNode, destAttr))
			except:
				pass
		else:
			if destParent is not None:
				addAttr(destNode, ln=destAttr, at='message', keyable=False, hidden=True, parent=destParent)
			else:
				addAttr(destNode, ln=destAttr, at='message', keyable=False, hidden=True)

		try:
			connectAttr(sourceNode.attr( sourceAttr ), destNode.attr( destAttr ), f=True)
			if dev:
				print 'Connected %s.%s to %s.%s' % (sourceNode, sourceAttr, destNode, destAttr)
		except:
			raise Exception('Attribute %s.%s could not be connected to %s.%s' % (sourceNode, sourceAttr, destNode, destAttr))


#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================

def matrixConstraint(target, constrained, offset=True, t=True, r=False, s=False, force=True, preserve=True, untangled=False):
	'''
	Low overhead constraint using matrix nodes
	offset - 	Determines whether the current local matrix of the constrained object will be added to the matrix sum as a static value
	t, r, s - 	Choose channels to constrain.  Use list/tuple of bools to connect subchannels
	force - 	Force connection of attributes if connections already found.
	preserve - 	If off, deletes old constraint
	untangled - Constraints create a benign evaluation cycle by default to preserve reparenting ability.  In many situations, it's not necessary to preserve that functionality. May speed evaluation slightly if True

	TODO:
	Look into right handed matrix to left conversion?
	'''

	loadPlugin( 'matrixNodes.mll', qt=True)
	loadPlugin( 'quatNodes.mll', qt=True)

	doJointOrient=True

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

	if doJointOrient:
		# If default, check to see if constrained nodes are both joints and apply if so.  If specified in doJointOrientParameter, skip this process
		doJointOrient=False
		if objectType(target, isType='joint') and objectType(constrained, isType='joint'):
			doJointOrient=True
	else:
		doJointOrient=False

	nodeList = []

	multMatrixName = '%s_matrixConstraint_multMatrix#' % (constrained.nodeName())
	decomposeMatrixName = '%s_matrixConstraint_decmpMatrix#' % (constrained.nodeName())
	eulerToQuatName = '%s_matrixConstraint_eulToQuat#' % (constrained.nodeName())
	quatInvertName = '%s_matrixConstraint_quatInv#' % (constrained.nodeName())
	quatProdName = '%s_matrixConstraint_quatProd#' % (constrained.nodeName())
	quatToEulerName = '%s_matrixConstraint_quatToEul#' % (constrained.nodeName())

	mm = createNode('multMatrix', n=multMatrixName)
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
	if untangled:
		constrained.getParent().worldInverseMatrix[0] >> mm.matrixIn[i]
	else:
		constrained.parentInverseMatrix[0] >> mm.matrixIn[i]
	dcmp = createNode('decomposeMatrix', n=decomposeMatrixName)
	nodeList.append(dcmp)
	mm.matrixSum >> dcmp.inputMatrix

	if len(constrainAttrs[3:6]) != 3:
		raise Exception(inAttrs[3:6])

	if doJointOrient and any(constrainAttrs[3:6]):
		eul = createNode('eulerToQuat', n=eulerToQuatName)
		nodeList.append(eul)
		constrained.jointOrient >> eul.inputRotate

		quatInv = createNode('quatInvert', n=quatInvertName)
		nodeList.append(quatInv)
		eul.outputQuat >> quatInv.inputQuat

		quatProd = createNode('quatProd', n=quatProdName)
		nodeList.append(quatProd)
		dcmp.outputQuat >> quatProd.input1Quat
		quatInv.outputQuat >> quatProd.input2Quat

		quatToEuler = createNode('quatToEuler', n=quatToEulerName)
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
	
	return nodeList

def removeMatrixConstraint(node):
	# Removes matrix constraint from nodes based on attribute input connection
	if hasAttr(node, 'constraintNodes'):
		delete(node.constraintNodes.get())


def symmetryConstraint(source, target, midPoint=None):
	# Makes symmetry constraint connections between joints.
	# Error checks
	for node in [source, target]:
		if not isinstance(node, PyNode):
			raise Exception('Object is not a PyNode: %s' % node)

		if not objectType(node, isType='joint'):
			raise Exception('Object is not a joint: %s' % node)

	targetAttributesCheck = [
	'translate',
	'tx',
	'ty',
	'tz',
	'rotate',
	'rx',
	'ry',
	'rz',
	'scale',
	'sx',
	'sy',
	'sz',
	'rotateOrder',
	'jointOrient'
	]

	for attribute in targetAttributesCheck:
		existingConnections = target.attr(attribute).inputs()
		if len(existingConnections):
			if objectType(existingConnections[0], isType='symmetryConstraint'):
				# warning('Target object already has incomming connections: %s from %s. Deleting old constraint...' % (attribute, existingConnections[0]))
				delete(existingConnections[0])
			else:
				raise Exception('%s.%s already has incomming connections' % (node, attribute, existingConnections[0]))

	sym = createNode('symmetryConstraint', n='%s_symmetryConstraint' % target.shortName().split('|')[-1])

	source.translate 				>> sym.targetTranslate
	source.rotate 					>> sym.targetRotate
	source.scale 					>> sym.targetScale
	source.rotateOrder 				>> sym.targetRotateOrder
	source.jointOrient 				>> sym.targetJointOrient
	source.worldMatrix[0] 			>> sym.targetWorldMatrix
	source.parentMatrix[0] 			>> sym.targetParentMatrix
	
	target.parentInverseMatrix[0] 	>> sym.constraintInverseParentWorldMatrix

	sym.constraintTranslate			>> target.translate
	sym.constraintRotate			>> target.rotate
	sym.constraintScale				>> target.scale
	sym.constraintRotateOrder		>> target.rotateOrder
	sym.constraintJointOrient		>> target.jointOrient


	if not midPoint is None:
		midPoint.worldMatrix[0] 	>> sym.symmetryRootWorldMatrix

	hide(sym)
	parent(sym, target)
	select([source, target])

	return sym



#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================

def meshIndic(transforms, groupNode=None, color=(0,0,0), live=True):
	# Creates a polygon shape with polyFacet history for indics requiring 3+ points
	# in space, or a visible plane
	
	loadPlugin( 'matrixNodes.mll', qt=True )
	
	# Where to parent the node if not specified
	if groupNode is None:
		groupNode = transforms[0]

	# Get a list of initial values
	points = []
	for trans in transforms:
		points.append(xform(trans, q=1, ws=1, rp=1))

	histName = '%s_hist_meshIndic' % groupNode.nodeName()
	polygonName = '%s_poly_meshIndic' % groupNode.nodeName()

	nodeList = []

	polyFacet = polyCreateFacet( p=points, n=polygonName)
	polygon = ls(polyFacet[0])[0]
	polygonHist = ls(polyFacet[1])[0]
	polygonHist.rename(histName)
	
	polygonS = polygon.getShapes()[0]
	polygonS.overrideEnabled.set(1)
	polygonS.overrideDisplayType.set(1)
	polygonS.castsShadows.set(0)
	polygonS.receiveShadows.set(0)
	polygonS.visibleInReflections.set(0)
	polygonS.visibleInRefractions.set(0)

	if live: # Interactive in scene
		for i, trans in enumerate(transforms):
			# convert inputs to local space of transform (not sure if required)
			# TODO Just transforms, so it should be less complicated than this
			# If it's even needed, you can just get ws by doing
			# dt.Vector(transLoc.ws.get()) - dt.Vector(polygon.ws.get()) I think
			multMatrixName = '%s_matrixConstraint_multMatrix#' % (trans.nodeName())
			decomposeMatrixName = '%s_matrixConstraint_decmpMatrix#' % (trans.nodeName())

			mm = createNode('multMatrix', n=multMatrixName)
			nodeList.append(mm)

			offsetMatrix = createNode('multMatrix', n='localOffsetMatrixTemp')
			polygon.worldMatrix[0] >> offsetMatrix.matrixIn[0]
			trans.worldInverseMatrix[0] >> offsetMatrix.matrixIn[1]
			mm.matrixIn[i].set(offsetMatrix.matrixSum.get())
			delete(offsetMatrix)

			trans.worldMatrix[0] >> mm.matrixIn[i]
		
			polygon.parentInverseMatrix[0] >> mm.matrixIn[i]

			dcmp = createNode('decomposeMatrix', n=decomposeMatrixName)
			nodeList.append(dcmp)
			mm.matrixSum >> dcmp.inputMatrix

			dcmp.outputTranslate.connect(polygonHist.points[i])

	return polygon


def boneIndic(start, end, group=None, blackGrey=0):
	# Gonna do this for now until parallel evaluation works
	return curveIndic(start, end, worldGroup=group, blackGrey=blackGrey)
	'''
	loadPlugin( 'matrixNodes.mll', qt=True )
	nodeList = []
	freezeList = []

	# Group default
	if group is None:
		group = start

	# Transpose blackGrey info to display type
	if blackGrey:
		disp = 1
	else:
		disp = 2

	# Name nodes
	indic1Name = '%s_bone_indic' % start.nodeName()
	indic2Name = '%s_bone_indic_end' % start.nodeName()


	indicAttrs = {'radius':0.01, 'overrideEnabled': 1, 'overrideDisplayType': disp}

	# indic1 = createNode('joint', n='%s' % indic1Name, p=group)
	indic1 = createNode('joint', n='%s' % indic1Name, p=group)
	xform(indic1, ws=1, matrix=xform(start, q=1, ws=1, m=1))
	nodeList.append(indic1)
	freezeList.append(indic1)
	setAttrsWithDictionary(indic1, indicAttrs)
	matrixConstraint(start, indic1, offset=0)

	indic2 = createNode('joint', n='%s' % indic2Name, p=indic1)
	xform(indic2, ws=1, matrix=xform(end, q=1, ws=1, m=1))
	nodeList.append(indic2)
	freezeList.append(indic2)
	setAttrsWithDictionary(indic2, indicAttrs)
	# pointConstraint(end, indic2)
	matrixConstraint(end, indic2, offset=0)

	# orientConstraint(indic1, indic2)

	indic1.hiddenInOutliner.set(0)
	lockAndHide(freezeList, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'])

	return nodeList
	'''
	
def curveIndic(start, end, worldGroup=None, blackGrey=0):
	
	loadPlugin( 'matrixNodes.mll', qt=True )
	nodeList = []
	freezeList = []

	# Transpose blackGrey info to display type
	if blackGrey:
		disp = 1
	else:
		disp = 2

	# Name nodes
	indicCurveName = '%s_curve_indic' % start.nodeName()
	localPos1Name = '%s_curve_indic_LOC' % start.nodeName()
	localPos2Name = '%s_curve_indic_LOC' % start.nodeName()
	pos1Name = '%s_curve_indic_LOC' % start.nodeName()
	pos2Name = '%s_curve_indic_LOC_end' % start.nodeName()

	# Get initial posistions
	startT = xform(start, q=1, rp=1, ws=1)
	endT = xform(end, q=1, rp=1, ws=1)

	# Create curve
	indicCurve = curve(degree=1, p=[startT, endT], n='%s' % indicCurveName)
	nodeList.append(indicCurve)
	freezeList.append(indicCurve)
	indicCurve.hiddenInOutliner.set(1)
	

	# Set group
	if not worldGroup:
		parent(indicCurve, start)
		# indicCurve.inheritsTransform.set(0)
	else:
		parent(indicCurve, worldGroup)

	indicCurve.t.set(0,0,0)
	indicCurve.r.set(0,0,0)
	indicCurve.s.set(1,1,1)

	# Get first point in curve's local space
	localPos1 = createNode('multMatrix', n=localPos1Name)
	pos1 = createNode('decomposeMatrix', n=pos1Name)
	start.worldMatrix.connect(localPos1.matrixIn[0])
	indicCurve.parentInverseMatrix.connect(localPos1.matrixIn[1])
	localPos1.matrixSum.connect(pos1.inputMatrix)

	# Get second point in curve's local space
	localPos2 = createNode('multMatrix', n=localPos2Name)
	pos2 = createNode('decomposeMatrix', n=pos2Name)
	end.worldMatrix.connect(localPos2.matrixIn[0])
	indicCurve.parentInverseMatrix.connect(localPos2.matrixIn[1])
	localPos2.matrixSum.connect(pos2.inputMatrix)
	
	# Connect to curve inputs
	curveShape = indicCurve.getShapes()[0]
	pos1.outputTranslate.connect(curveShape.controlPoints[0])
	pos2.outputTranslate.connect(curveShape.controlPoints[1])

	# Set curve attributes
	curveShape.overrideEnabled.set(1)
	curveShape.overrideDisplayType.set(disp)
	# curveShape.lineWidth.set(1.5)

	lockAndHide(freezeList, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'])

	return nodeList



#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================

def shapeMaker(name, shape=0):
	import maya.mel as mel
	node = ls(mel.eval('am_createShape(%s)' % shape))[0]
	node.rename(name)
	# shape = node.getShapes()[0]
	# print shape
	return node


# ikNode, ikShape = rb.shapeMaker(name=names['ikShape'], parent=ikShapeGrp, shape=0)


def shaper(fitNode, attribute, transform, fitrigTransform):
	'''
	'''
	if not attrExists(fitNode, attribute):
		print 'No shape attribute found.'
	else:
		if not len(fitNode.attr(attribute).inputs()):
			shapeNodes = [createNode('locator', n=attribute)]
		else:
			node = fitNode.attr(attribute).inputs()[0]
			dup = duplicate(node, po=1, p=transform)[0]
			shapeNodes = dup.getShapes()
			parent(shapeNodes, transform, r=1, s=1)
			delete(dup)

#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================

 

def getSize(geometry):
	'''
	finds the bounding box of a geometry and
	returns a dictionary with the height, width and depth

	height: y axis units
	width: x axis units
	depth: z axis units

	'''

	#check the variable type
	variableType(geometry, basestring, raise_error=True)

	#check if object exists
	objectExists(geometry, raise_error=True)

	#check the object type
	objectType(geometry, 'transform', raise_error=True)

	#get the boundingbox
	boundingbox = xform(geometry, q=True, bb=True)
	min = {'x': boundingbox[0], 'y': boundingbox[1], 'z': boundingbox[2]}
	max = {'x': boundingbox[3], 'y': boundingbox[4], 'z': boundingbox[5]}

	#get the distance betwen points
	height = max['y'] - min['y']
	width = max['x'] - min['x']
	depth = max['z'] - min['z']

	return {'height': height, 'width': width, 'depth': depth}


#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================
   
   
def deleteOtherInstances(shapeNode):
	'''Deletes all found instances of specified shape.
	Facilitates settings nodes to be instanced onto many other nodes at once.
	'''
	dev = False
	failList = []
	if shapeNode:
		instances = shapeNode.getOtherInstances()
		if dev:
			print "Deleting other instances of "
			print shapeNode
		for instance in instances:
			if dev:
				print instance
				print '\n'
			try:
				parent(instance, s=True, rm=True)
			except:
				failList.append(instance)
				if dev: print failList



#=========================================================================================================================
#=========================================================================================================================
#=========================================================================================================================

def deleteByAttrOutput(node, attribute):
	'''Deletes rig node and all associated nodes
	'''
	if hasAttr(node, attribute):
		outputs = node.attr( attribute ).outputs(shapes=True)
		for outputN in outputs:
			if objExists(outputN):
				delete(outputN)



def deleteByAttrInput(node, attribute):
	'''Deletes rig node and all associated nodes
	'''
	if hasAttr(node, attribute):
		inputs = node.attr( attribute ).inputs(shapes=True)
		for inputN in inputs:
			print inputN
			if objExists(inputN):
				delete(inputN)
				inputs.remove(inputN)


def filterChildren(parent, node, attribute):
	'''Unparents children not connected by attribute
	'''
	dev = True
	if dev:
		print parent
		print node
		print attribute

	if hasAttr(node, attribute):
		outputs = node.attr(attribute).outputs()
		if dev: print outputs

		heirarchy = [parent]
		# Make hierarchy list
		for child in heirarchy:
			heirarchy.extend(ls(listRelatives(child, c=True), type='transform'))

		if dev: print heirarchy
		for child in heirarchy:
			if child not in outputs:
				if dev: print '%s not found in output list' % child
				# If child has children in this list, assume mistake and send warning. Otherwise remove
				subHeirarchy = [child]
				# Get subHeirarchy list
				for subChild in subHeirarchy:
					subHeirarchy.extend(listRelatives(subChild, c=True))
				for subChild in subHeirarchy:
					if subChild in outputs:
						print '%s found under %s, however.' % (subChild, child)
						found=1
					else:
						found=0
				if found:
					print 'WARNING: parents of %s in heirarchy, but not in node list connections.' % child
				else:
					parent(child, w=1)
					if dev: print 'parenting %s to world' % child
					# rebuild heirarchy list and remove subHeirarchy
					heirarchy = [child for child in heirarchy if child not in subHeirarchy]
					if dev:
						print 'Removing list from operation:'
						print subHeirarchy
						print 'New List:'
						print heirarchy



def spaceSwitch(gen=2, control=None, constrained=None, targets=None, labels=None, constraintType=0, prefix=None):
	with UndoChunk():
		dev = 0
		nodeList = []

		if constrained is None:
			if control is None:
				raise Exception('Specify either constrained or control')
			constrained = control.getParent(generations=gen)

		if control is None:
			if constrained is None:
				raise Exception('Specify either constrained or control')

		if targets is None:
			raise Exception('Specify targets')

		if not isinstance(targets, list):
			targets = [targets]

		if labels is None or not len(labels) == len(targets):
			labels = None
			for target in targets:
				print labels
				labels.append(target.shortName().split('|')[-1])

		if prefix is None:
			print control
			prefix = control.shortName().split('|')[-1]

		constT = xform(constrained, q=1, rp=1, ws=1)
		constR = xform(constrained, q=1, ro=1, ws=1)
		constMatrix = xform(constrained, q=1, matrix=1, ws=1)


		constNames = ['parent', 'point', 'orient']
		if isinstance(constraintType, str):
			if constraintType in constNames:
				constraintType = constNames.index(constraintType)
			else:
				raise Exception('Constraint Type not recognized: %s (valid options are %s' % (constraintType), ', '.join(constNames))

		if dev: print 'Running %s spaceSwitch constraint.' % constNames[constraintType]

		names = {
		'rev': 				'%s_%s_REV' % 				(prefix, constNames[constraintType]),
		'offsetTrans': 		'Socket'  					,
		'cond1': 			'%s_%s_space1_COND' % 		(prefix, constNames[constraintType]),
		'cond2': 			'%s_%s_space2_COND' % 		(prefix, constNames[constraintType]),
		}
		if dev:
			print '\n\n\n'
			print 'Constrained: %s\nConstraint Type: %s' % (constrained, constraintType)
		for i, target in enumerate(targets):
			if dev:
				print '\n\n\n'
				print 'Target %s: %s, %s, %s' % (i, targets[i], labels[i], offsets[i])
				print 'Prefix: %s' % prefix

		# Control attributes
		cbSep(control)
		s = ':'
		enumName = s.join(labels)
		print enumName
		if not hasAttr(control, '%sSpace1' % constNames[constraintType]):
			addAttr(control, ln='%sSpace1' % constNames[constraintType], at='enum', enumName=enumName, dv=0, k=1)
		else:
			addAttr(control.attr('%sSpace1' % constNames[constraintType]), e=1, ln='%sSpace1' % constNames[constraintType], at='enum', enumName=enumName, dv=0, k=1)
		
		if not hasAttr(control, '%sSpace2' % constNames[constraintType]):
			addAttr(control, ln='%sSpace2' % constNames[constraintType], at='enum', enumName=enumName, dv=1, k=1)
		else:
			addAttr(control.attr('%sSpace1' % constNames[constraintType]), e=1, ln='%sSpace2' % constNames[constraintType], at='enum', enumName=enumName, dv=1, k=1)
		
		if not hasAttr(control, '%sSpaceBlend' % constNames[constraintType]):
			addAttr(control, ln='%sSpaceBlend' % constNames[constraintType], at='float', min=0, max=1, k=1)
		else:
			addAttr(control.attr('%sSpaceBlend' % constNames[constraintType]), e=1, ln='%sSpaceBlend' % constNames[constraintType], min=0, max=1, k=1)

		# Reverse
		rev = createNode('reverse', n=names.get('rev', 'rev'))
		nodeList.append(rev)
		control.attr('%sSpaceBlend' % constNames[constraintType]).connect(rev.inputX)

		conds1 = []
		conds2 = []


		for i, target in enumerate(targets):
			offsetTrans = createNode('transform', n='%s_%s_%s_%s' % (prefix, labels[i], constNames[constraintType], names['offsetTrans']), p=target)
			nodeList.append(offsetTrans)

			xform(offsetTrans, worldSpace=True, matrix=constMatrix )

				# move(offsetTrans, constT, rpr=1, ws=1)
				# xform(offsetTrans, ro=constR, ws=1)
			if constraintType == 0: #parent
				const = parentConstraint(offsetTrans, constrained)
				const.interpType.set(2)
			elif constraintType == 1: #point
				const = pointConstraint(offsetTrans, constrained)
			elif constraintType == 2: #orient
				print offsetTrans
				print constrained
				const = orientConstraint(offsetTrans, constrained)
				const.interpType.set(2)
			if dev: print const
			
			cond1 = createNode('condition', n=names.get('cond1', 'cond1'))
			conds1.append(cond1)
			nodeList.append(cond1)
			cond1.colorIfFalseR.set(0)
			control.attr('%sSpace1' % constNames[constraintType]).connect(cond1.firstTerm)
			cond1.secondTerm.set(i)

			cond2 = createNode('condition', n=names.get('cond2', 'cond2'))
			conds1.append(cond2)
			nodeList.append(cond2)
			control.attr('%sSpace2' % constNames[constraintType]).connect(cond2.firstTerm)
			cond2.secondTerm.set(i)

			control.attr('%sSpaceBlend' % constNames[constraintType]).connect(cond2.colorIfTrueR)
			cond1.outColorR.connect(cond2.colorIfFalseR)
			rev.outputX.connect(cond1.colorIfTrueR)
			cond2.outColorR.connect(const.attr('w%s' % i))

		if len(targets) == 2:
			setAttr(control.attr('%sSpace1' % constNames[constraintType]), l=1)
			control.attr('%sSpace1' % constNames[constraintType]).set(k=0)
			setAttr(control.attr('%sSpace2' % constNames[constraintType]), l=1)
			control.attr('%sSpace2' % constNames[constraintType]).set(k=0)

		

def pp(matrix, title = None, footer = "\n"):
		"""
		pretty prints a matrix with an optional title and end of matrix separator 
		"""
		if not (title == None):
			print(title)
		for row in matrix:
			print("["),
			for cell in row:
				print("{0:.3f},".format(cell)),
			print("]")
		if not (footer == None):
			print(footer)


def follicleConst(mesh=None):

	selection = ls(sl=1)

	if mesh is None:
		mesh = selection[0]
		selection.remove(mesh)

	shape = mesh.getShapes()[-1]

	if objectType(shape, isType='mesh'):

		for sel in selection:
			if not objectType(sel, isAType='transform'):
				raise Exception('Object is not a transform: %s' % sel)

		if not objExists('follicle_RigNode'):
			follicleRigNode = createNode('transform', n='follicle_RigNode')
		else:
			follicleRigNode = ls('follicle_RigNode')[0]
		
		nodeList = []

		for sel in selection:

			loc = createNode('transform', p=follicleRigNode, n='%s_%s_LOC' % (sel.shortName().split('_')[0], sel.shortName().split('_')[1]))
			locS = createNode('locator', p=loc)
			nodeList.append(loc)

			parConst = parentConstraint(sel, loc)
			delete(parConst)

			closest = createNode('closestPointOnMesh', n='%s_%s_CLOSEST' % (sel.shortName().split('_')[0], sel.shortName().split('_')[1]))
			locS.worldPosition.connect(closest.inPosition)
			shape.outMesh.connect(closest.inMesh)
			nodeList.append(closest)

			fol = createNode('follicle')
			folTrans = fol.getParent()
			folTrans.rename('%s_%s_FOLL' % (sel.shortName().split('_')[0], sel.shortName().split('_')[1]))
			parent(folTrans, follicleRigNode)
			fol.outRotate.connect(folTrans.rotate)
			fol.outTranslate.connect(folTrans.translate)
			mesh.worldMatrix.connect(fol.inputWorldMatrix)
			shape.outMesh.connect(fol.inputMesh)
			fol.simulationMethod.set(0)
			nodeList.append(fol)

			jnt = createNode('joint', p=folTrans, n='%s_%s_JNT' % (sel.shortName().split('_')[0], sel.shortName().split('_')[1]))
			nodeList.append(jnt)

			u = getAttr(closest.result.parameterU)
			v = getAttr(closest.result.parameterV)

			# fol.parameterU.set(u)
			# fol.parameterV.set(v)

			# delete(closest, closest2, loc2, loc, clus)

			addAttr(jnt, ln='parameterU', sn='pU', at='float', min=0, max=10, dv=0, k=1)
			addAttr(jnt, ln='parameterV', sn='pV', at='float', min=0, max=10, dv=0, k=1)
			jnt.pU.set(k=0, cb=1)
			jnt.pV.set(k=0, cb=1)
			mult = createNode('multiplyDivide', n='%s_%s_MULT' % (sel.shortName().split('_')[0], sel.shortName().split('_')[1]))
			nodeList.append(mult)


			jnt.parameterU.connect(mult.input1X)
			jnt.parameterV.connect(mult.input1Y)
			mult.input2.set([.1,.1,.1])

			
			

			add = createNode('plusMinusAverage', n='%s_%s_ADD' % (sel.shortName().split('_')[0], sel.shortName().split('_')[1]))
			mult.output.connect(add.input3D[0])
			closest.result.parameterU.connect(add.input3D[1].input3Dx)
			closest.result.parameterV.connect(add.input3D[1].input3Dy)
			nodeList.append(add)

			add.output3Dx.connect(fol.parameterU)
			add.output3Dy.connect(fol.parameterV)


		if len(nodeList):
			messageConnect(follicleRigNode, 'rigNodes', nodeList, 'rigNode')

		select(folTrans)

	else:
		raise Exception('Object is not correct type: %s' % mesh)


def averagePoint(transform='joint'):
	selection = ls(sl=1)
	print selection
	currentTool = currentCtx()
	setToolTo('moveSuperContext')
	vecPos = manipMoveContext('Move', q=1, p=True)
	res = createNode(transform, n='average#')
	move(res, vecPos, ws=1, a=1)
	setToolTo(currentTool)
	selectMode(component=1)
	select(selection)

def eachPoint(transform='joint'):
	selection = ls(sl=1, flatten=1)
	print selection
	for sel in selection:
		select(sel, r=1)
		currentTool = currentCtx()
		setToolTo('moveSuperContext')
		vecPos = manipMoveContext('Move', q=1, p=True)
		res = createNode(transform, n='average#')
		move(res, vecPos, ws=1, a=1)
		setToolTo(currentTool)
		selectMode(component=1)
	select(selection)

def findSkinCluster(mesh):
	for each in listHistory(mesh):
		if objectType(each, isType='skinCluster'):
			skincluster=each
			return skincluster

def fnSaveSkinning(mesh,path): 
	## Collect data
	skincluster = fnFindSkinCluster(mesh)
  
	## Check if skincluster even exists
	if skincluster!=None:   
		## Prepare XML xml_document
		xml_doc = minidom.Document()
		xml_header = xml_doc.createElement("influences") 
		xml_doc.appendChild(xml_header)   
 
		## Write out the joint id/name table  
		for each in skincluster.getInfluence():
			getData = skincluster.getPointsAffectedByInfluence(each)  
			tmpJoint= xml_doc.createElement(each)
			vertData = []
			if len(getData[0])>0:
				## Gather all vertex ids and store it in the vertData list
				for each in getData[0][0]:
				 vertData.append(each.currentItemIndex())
				## Then store the vertData list as "vertices" attribute value 
				tmpJoint.setAttribute("vertices",str(vertData))
				tmpJoint.setAttribute("weights",str(getData[1]))
				xml_header.appendChild(tmpJoint)

		## Save XML
		file = open(path, 'w')
		file.write(xml_doc.toprettyxml())
		pm.warning("Saved '%s.skinning' to '%s'"%(mesh,path))
	else:
		pm.warning('No skincluster connected to %s'%mesh)



def populateCurve2(curve, joints=7):

	resultsGroup = createNode('transform', n=curve.nodeName()+'GRP')

	for i in (range(joints)):
		if range(joints) < 10:
			d = float(i)
		elif range(joints) < 100:
			d = '%01d' % i
		else:
			d = '%02d' % i
		addAttr(resultsGroup, ln='uValue%s' % d, min=0, max=1, k=1)
	for i in (range(joints)):
		if range(joints) < 10:
			d = float(i)
		elif range(joints) < 100:
			d = '%01d' % i
		else:
			d = '%02d' % i
		addAttr(resultsGroup, ln='uValueOffset%s' % d, softMinValue=-1, softMaxValue=1, k=1)
	for i in (range(joints)):
		if range(joints) < 10:
			d = float(i)
		elif range(joints) < 100:
			d = '%01d' % i
		else:
			d = '%02d' % i
		addAttr(resultsGroup, ln='uValueOffsetMult%s' % d, dv=1, min=0, softMaxValue=1, k=1)

	
	for i in (range(joints)):
		# name objects
		if range(joints) < 10:
			d = float(i)
		elif range(joints) < 100:
			d = '%01d' % i
		else:
			d = '%02d' % i

		name = '%s_%s_' % (curve.shortName(), d)

		uValue = resultsGroup.attr('uValue%s' % d)
		uValueOffset = resultsGroup.attr('uValueOffset%s' % d)
		uValueOffsetMult = resultsGroup.attr('uValueOffsetMult%s' % d)

		mp = createNode('motionPath', n=name+'MP')
		buf = createNode('transform', n=name+'BUF', p=resultsGroup)
		extra = createNode('transform', n=name+'EXTRA', p=buf)
		ctrl = createNode('transform', n=name+'CTRL', p=extra)
		jnt = createNode('joint', n=name+'BIND', p=ctrl)

		uValue.set(float(d)/float(joints))
		addAttr(uValue, e=1, dv=(float(d)/float(joints)))
		



		uOffsetAdd = createNode('addDoubleLinear', n=name+'offsetMult')
		uOffsetMult = createNode('multDoubleLinear', n=name+'offsetMult')
		
		uValueOffset.connect(uOffsetMult.i1)
		uValueOffsetMult.connect(uOffsetMult.i2)
		uValue.connect(uOffsetAdd.i1)
		uOffsetMult.o.connect(uOffsetAdd.i2)
		uOffsetAdd.o.connect(mp.uValue)

		mp.fractionMode.set(1)
		mp.follow.set(1)
		mp.worldUpType.set(2)
		mp.frontAxis.set(0) # X
		mp.inverseUp.set(1)
		mp.upAxis.set(2) # -Z

		curve.getShapes()[0].worldSpace[0].connect(mp.geometryPath)
		mp.allCoordinates.connect(buf.translate)
		mp.rotate.connect(buf.rotate)



def populateCurve(curve, joints=7):
	for i in (range(joints+1)):
		# name objects
		if range(joints) < 10:
			d = float(i)
		elif range(joints) < 100:
			d = '%01d' % i
		else:
			d = '%02d' % i

		name = '%s_%s_' % (curve.shortName(), d)

		mp = createNode('motionPath', n=name+'MP')
		buf = createNode('transform', n=name+'BUF')
		extra = createNode('transform', n=name+'EXTRA', p=buf)
		ctrl = createNode('transform', n=name+'CTRL', p=extra)
		jnt = createNode('joint', n=name+'BIND', p=ctrl)

		mp.uValue.set(float(d)/float(joints))
		mp.fractionMode.set(1)
		mp.follow.set(1)
		mp.worldUpType.set(2)
		mp.frontAxis.set(0) # X
		mp.inverseUp.set(1)
		mp.upAxis.set(2) # -Z

		curve.getShapes()[0].worldSpace[0].connect(mp.geometryPath)
		mp.allCoordinates.connect(buf.translate)
		mp.rotate.connect(buf.rotate)

		if i == 0 or i == joints:
			# create a secondary orientation joint that's static

			name = '%s_%s_Static_' % (curve.shortName(), d)

			mp = createNode('motionPath', n=name+'MP')
			buf = createNode('transform', n=name+'BUF')
			jnt = createNode('joint', n=name+'BIND', p=buf)

			mp.uValue.set(float(d)/float(joints))
			mp.fractionMode.set(1)
			mp.follow.set(0)

			curve.getShapes()[0].worldSpace[0].connect(mp.geometryPath)
			mp.allCoordinates.connect(buf.translate)


'''

skinPercent -q -value "skinCluster1" "bezier2.cv[1]"; 

# influence name
string $getArray[] = `skinPercent -q -transform "skinCluster1" "bezier2.cv[1]"`; 
// Result: bendUpArmCp_ctrl bendUpArmHndl_A_ctrl // 

skinPercent -transformValue bendUpArmCp_ctrl 1 skinCluster1 "bezier2.cv[1]"
;'''


def eyelidToEyeball(joints=None, sphere=None):

	selection = ls(sl=1)
	if sphere is None:
		sphere = selection[-1]
		selection.remove(sphere)
	if joints is None:
		joints = selection

	if not sphere or len(joints)<1:
		raise Exception('Verify inputs')

	sphereS = sphere.getShapes()[0]

	for jnt in joints:
		loc = createNode('locator', p=jnt, n='%s_LOC' % (jnt.shortName()))
		loc.hide()
		jnt.hide()
		closest = createNode('closestPointOnSurface', n='%s_%s_CLOSEST' % (jnt.shortName().split('_')[0], jnt.shortName().split('_')[1]))
		sphereS.worldSpace[0].connect(closest.inputSurface)
		loc.worldPosition.connect(closest.inPosition)
		newJnt = createNode('joint', n='%s_%s_result_JNT' % (jnt.shortName().split('_')[0], jnt.shortName().split('_')[1]))
		closest.result.position.connect(newJnt.translate)
		orientConstraint(jnt, newJnt)