from pymel.core import *
# import utils
__author__ = 'Alexander Mann'
__version__ = '0.1'
__email__ = 'AlexKMann@comcast.net'
__status__ = 'Development'

'''
import naming
reload(naming)
renamingUI = naming.renamingUI()
'''
# Commands

def axmn_rename(renameInput, selection=None, padding=1, start=0, hierarchy=False):

	# Error Check
	# Rename Input
	# print type(renameInput)
	if not isinstance(renameInput, unicode):
		raise Exception('Rename input is not a string.')
	
	# if renameInput.count('*') > 1:
	# 	raise Exception('More than one wildcard tag (\'*\') in rename input.')
	

	# Selection
	if selection is None:
		selection = ls(sl=1)

	if not isinstance(selection, list):
		selection = [selection]

	for sel in selection:
		if not isinstance(sel, PyNode):
			raise Exception('Object %s is not a PyNode instance' % sel)

	if padding is None:
		# Auto padding
		valCheck = len(selection) + (start-1)
		if valCheck >= 0:
			padding = 1
		if valCheck >= 10:
			padding = 2
		if valCheck >= 100:
			padding = 3
		if valCheck >= 1000:
			padding = 4
	# Run rename

	for i, sel in enumerate(selection):
		d = padFormat((i+start), padding)
		ren = renameInput

		if ren.count('*'):
			ren = ren.replace('*', d)
		else:
			ren = '%s%s' % (ren, d)

		sel.rename(ren)

	select(selection)

	return selection

def axmn_replace(search, replace, selection=None, hierarchy=False):
	# Error Check
	# Search Input
	if not isinstance(search, unicode):
		raise Exception('Search input is not a string.')

	# Replace Input
	if not isinstance(replace, unicode):
		raise Exception('Replace input is not a string.')

	warnList = []
	# Selection
	if selection is None:
		selection = ls(sl=1)

	if not isinstance(selection, list):
		selection = [selection]

	for sel in selection:
		if not isinstance(sel, PyNode):
			raise Exception('Object %s is not a PyNode instance' % sel)

	for sel in selection:
		if not search in sel.nodeName():
			warnList.append(sel)
			# raise Exception('Search phrase %s not found in %s' % (search, sel.nodeName()))

	# Run Replace
	for sel in selection:
		nam = sel.nodeName().replace(search, replace)
		sel.rename(nam)

	if len(warnList):
		warning('Some nodes were not successfully renamed: %s' % warnList)

def axmn_prefix(prefix, selection=None, hierarchy=False):
	# Error Check
	# Prefix Input
	if not isinstance(prefix, unicode):
		raise Exception('Prefix input is not a string.')

	# Selection
	if selection is None:
		selection = ls(sl=1)

	if not isinstance(selection, list):
		selection = [selection]

	for sel in selection:
		if not isinstance(sel, PyNode):
			raise Exception('Object %s is not a PyNode instance' % sel)

	for sel in selection:
		sel.rename('%s%s' % (prefix, sel.nodeName()))

def axmn_suffix(suffix, selection=None, hierarchy=False):
	# Error Check
	# Suffix Input
	if not isinstance(suffix, unicode):
		raise Exception('Suffix input is not a string.')

	# Selection
	if selection is None:
		selection = ls(sl=1)

	if not isinstance(selection, list):
		selection = [selection]

	for sel in selection:
		if not isinstance(sel, PyNode):
			raise Exception('Object %s is not a PyNode instance' % sel)

	for sel in selection:
		sel.rename('%s%s' % (sel.nodeName(), suffix))

def getClashingNodes(changeSelection=True):
	nodes = ls(dag=True)
	newList = []
	for node in nodes:
		# Select nodes with node name
		nodeNameSel = ls(node.nodeName())
		if len(nodeNameSel) > 1:
			nodeNameSel = sorted(nodeNameSel)
			for node in nodeNameSel:
				if not node in newList:
					newList.append(node)
		
	if changeSelection:
		select(newList)

	return newList

def clashFix(nodes=None):
	with UndoChunk():

		if not nodes is None:
			if not isinstance(nodes, list):
				nodes = [nodes]
			for node in nodes:
				if not isinstance(node, PyNode):
					try:
						raise Exception('Object in input list is not a PyNode: %s (%s)' % (node, node.type()))
					except:
						raise Exception('Object in input list is not a PyNode')

		else:
			nodes = ls(dagObjects=1)


		for node in nodes:
			# get name
			name = node.nodeName()
		
			withName = ls(name)
			if len(withName) > 1:
				for i, dup in enumerate(withName):
					dup.rename('%s_%s' % (name, i))


class renamingUI:
	# Class for ui window designed to facilitate batch node renaming

	def __init__(self, dev=False):

		# Print development messages in console
		self.dev = dev

		# Restore selection after initialization
		selection = ls(sl=1)

		# ================================================= DATA ========================================================= 
		# Default Values
		self.paddingValue = 0
		self.startValue = 1
		self.formatStyle = 'short'
		

		# Store local settings data in network node to preserve between instances
		if not(len(ls('renameUIData'))):
			self.renameUIDataNode = createNode('network', n='renameUIData')
		else:
			self.renameUIDataNode = ls('renameUIData')[0]

		# Create attributes if they're missing
		if not hasAttr(self.renameUIDataNode, 'padding'):
			addAttr(self.renameUIDataNode, ln='padding', at='short', min=0, max=4, dv=self.paddingValue, k=1)
		if not hasAttr(self.renameUIDataNode, 'start'):
			addAttr(self.renameUIDataNode, ln='start', at='short', min=0, dv=self.startValue, k=1)
		styles = ['short', 'long', 'node']
		if not hasAttr(self.renameUIDataNode, 'formatStyle'):
			addAttr(self.renameUIDataNode, ln='formatStyle', at='enum', enumName=str(':'.join(styles)), dv=styles.index(self.formatStyle), k=1)

		# Create string attribute for each input field
		stringAttrs = ['rename', 'search', 'replace', 'prefix', 'suffix']
		for attribute in stringAttrs:
			if not hasAttr(self.renameUIDataNode, '%sField' % attribute):
				addAttr(self.renameUIDataNode, ln='%sField' % attribute, dt='string', k=1)
		
		self.loadNodeData(self.renameUIDataNode)

		# self.paddingValue = 	self.renameUIDataNode.padding.get()
		# self.startValue = 		self.renameUIDataNode.start.get()
		# self.renameString = 	self.renameUIDataNode.renameField.get()
		# self.searchString = 	self.renameUIDataNode.searchField.get()
		# self.replaceString = 	self.renameUIDataNode.replaceField.get()
		# self.prefixString = 	self.renameUIDataNode.prefixField.get()
		# self.suffixString = 	self.renameUIDataNode.suffixField.get()
		# self.suffixString = 	self.renameUIDataNode.suffixField.get()
		# self.formatStyle = 		self.renameUIDataNode.formatStyle.get(asString=True)

		# Initialize Attributes
		self.clashingNodes = []

		self.renameJobNum = None #ScriptJob
		self.selectInSceneJobNum = None #ScriptJob
		self.nodeDeletedJobNum = None #ScriptJob

		self.defaultHeight=217
		

		self.spacing = 0
		self.minSpacing = 2
		# ================================================= UI ========================================================= 

		self.UI()
		self.loadWindow()

		select(selection)

	def UI(self):

		# create window if invoked alone
		# if win == None:
			# Reset ui if exists
		if window('axmn_rename_window', exists=True):
			deleteUI('axmn_rename_window')

		# Create window
		self.win = window('axmn_rename_window', t='Rename', width=300, height=self.defaultHeight, resizeToFitChildren=1, sizeable=1, mxb=0)
		# else:
		# 	self.win = win


		allLayout = verticalLayout(p=self.win, spacing=1)
		
		renameRow = self.renameRowUI(p=allLayout)
		replaceRow = self.replaceRowUI(p=allLayout)
		prefixRow = self.prefixRowUI(p=allLayout)
		suffixRow = self.suffixRowUI(p=allLayout)
		clashRow = self.clashRowUI(p=allLayout)

		# Stretch across width
		allLayout.redistribute()
		# Take as much vertical space as necessary from top downwards
		stackVerticalLayout(allLayout)

		allLayout.attachForm(clashRow, 'bottom', 5)

		showWindow(self.win)
		self.win.setHeight(self.defaultHeight)

	def updateClassData(self, padding=False, start=False, strings=False, formatStyle=False):
		# Gets input values from window and saves them to class

		# If no inputs, assume all inputs.  If any inputs, assume others False.
		if all([not padding, not start, not strings, not formatStyle]):
			padding=True
			start=True
			strings=True
			formatStyle=True

		if padding:
			# if self.dev: print 'padding'
			self.paddingValue = self.getPaddingInput()
			if self.paddingValue is None:
				self.paddingValue = 0

		if start:
			# if self.dev: print 'start'
			self.startValue = self.paddingStartField.getValue()

		if strings:
			self.renameString = 	self.renameField.getText()
			self.searchString = 	self.searchField.getText()
			self.replaceString = 	self.replaceField.getText()
			self.prefixString = 	self.prefixField.getText()
			self.suffixString = 	self.suffixField.getText()


	def updateNodeData(self, padding=False, start=False, strings=False, formatStyle=False):
		# Gets input values from class and saves them to data node
		# Sets class node attributes
		# If no inputs, assume all inputs.  If any inputs, assume others False.
		if all([not padding, not start, not strings, not formatStyle]):
			padding=True
			start=True
			strings=True
			formatStyle=True

		self.updateClassData(padding, start, strings, formatStyle)

		if padding:
			self.renameUIDataNode.padding.set(self.paddingValue)

		if start:
			self.renameUIDataNode.start.set(self.startValue)
		
		if strings:
			self.renameUIDataNode.renameField.set(self.renameString)
			self.renameUIDataNode.searchField.set(self.searchString)
			self.renameUIDataNode.replaceField.set(self.replaceString)
			self.renameUIDataNode.prefixField.set(self.prefixString)
			self.renameUIDataNode.suffixField.set(self.suffixString)

		if formatStyle:
			self.renameUIDataNode.formatStyle.set(self.formatStyle)


	def loadNodeData(self, node=None, padding=False, start=False, strings=False, formatStyle=False):
		# gets values from data node and applies them to class

		if node is None: node = self.renameUIDataNode

		if all([not padding, not start, not strings, not formatStyle]):
			padding=True
			start=True
			strings=True
			formatStyle=True

		if padding:
			self.paddingValue = node.padding.get()

		if start:
			self.startValue = node.start.get()
			
		if strings:
			self.renameString = 	node.renameField.get()
			self.searchString = 	node.searchField.get()
			self.replaceString = 	node.replaceField.get()
			self.prefixString = 	node.prefixField.get()
			self.suffixString = 	node.suffixField.get()

		if formatStyle:
			self.formatStyle = 	node.formatStyle.get(asString=True)

	def loadWindow(self, padding=False, start=False, strings=False, formatStyle=False):
		# Uses class data to update window
		if all([not padding, not start, not strings, not formatStyle]):
			padding=True
			start=True
			strings=True
			formatStyle=True



		# if padding:
		# 	self.paddingStartField.setValue(self.paddingValue)

		if start:
			self.paddingStartField.setValue = self.startValue
			

		if strings:
			self.renameField.setText(	self.renameString)
			self.searchField.setText(	self.searchString)
			self.replaceField.setText(	self.replaceString)
			self.prefixField.setText(	self.prefixString)
			self.suffixField.setText(	self.suffixString)

	# ========================Rename========================

	def renameRowUI(self, p):
		# Renaming UI Widget
		renameRow = horizontalLayout(p=p)
		with renameRow:
			# Rename Field
			self.renameField = textField(
				alwaysInvokeEnterCommandOnReturn = True,
				annotation = 'Rename Input',
				height = 35,
				enterCommand = Callback(self.renameUICommand),
				changeCommand=Callback(self.updateNodeData, strings=True),
				placeholderText = 'Rename'
				)
			self.renamePopup(p=self.renameField)

			# Start (Padding)
			self.paddingStartField = intField(
				annotation = 'Start',
				min=0,
				v=self.startValue,
				cc=Callback(self.updateNodeData, start=True)
				)

			# Execute Rename
			renameButton = iconTextButton(
				rpt=True,
				style='textOnly',
				bgc = [0.2,0.2,0.2],
				annotation = 'Rename',
				label='>>',
				width=60,
				command = Callback(self.renameUICommand)
				)
		stackHorizontalLayout(renameRow)

	def renamePopup(self, p):
		# Popup under rename text field (for padding value radio options)
		
		namingMenu = popupMenu()
		with namingMenu:
			menuItem(l= 'Padding', enable=False)
			# menuItem(l= 'Padding', enable=False)

			# self.paddingColl = radioCollection()
			self.paddingColl = radioMenuItemCollection()
			self.paddingMenuItems = []

			self.paddingMenuItems.append(menuItem(rb=True, l='Auto', c=Callback(self.updateNodeData, padding=True)))
			self.paddingMenuItems.append(menuItem(rb=True, l= '1', c=Callback(self.updateNodeData, padding=True)))
			self.paddingMenuItems.append(menuItem(rb=True, l= '2', c=Callback(self.updateNodeData, padding=True)))
			self.paddingMenuItems.append(menuItem(rb=True, l= '3', c=Callback(self.updateNodeData, padding=True)))
			self.paddingMenuItems.append(menuItem(rb=True, l= '4', c=Callback(self.updateNodeData, padding=True)))
			
			menuItem(self.paddingMenuItems[self.paddingValue], e=1, rb=1)

	def getPaddingInput(self):
		# Special command for retrieving popup menu radio seleciton. Sorta hacky, but this is how the internet says I should do it
		ret = None
		menuInputs = [ 'Auto', '1', '2', '3', '4' ]
		for item in self.paddingMenuItems:
			if menuItem(item, q=True, rb=True):
				value = menuItem(item, q=True, label=True)
				if value in menuInputs:
					index = menuInputs.index(value)
					if index: ret = index
		return ret

	def renameUICommand(self):
		# Retrieve data from window and use to run renaming

		padding = self.getPaddingInput()
		start = self.paddingStartField.getValue()

		# padding = self.paddingValue
		# start = self.startValue

		# If textfield is empty, use first selected object's nodeName
		# TODO: remove digits at end?

		if self.renameField.getText():
			renameText = self.renameField.getText()
		else:
			renameText = ls(sl=1)[0].nodeName()

			
		axmn_rename(renameText, padding=padding, start=start)

	# ========================Replace========================
	def replaceRowUI(self, p):
		replaceRow = horizontalLayout(p=p)
		with replaceRow:
			inputsRow = horizontalLayout(spacing=0)
			with inputsRow:
				self.searchField = textField(
					alwaysInvokeEnterCommandOnReturn = True,
					annotation = 'Search Input',
					height = 35,
					enterCommand = Callback(self.replaceFocus),
					changeCommand=Callback(self.updateNodeData, strings=True),
					placeholderText = 'Search'
					)

				self.replaceField = textField(
					alwaysInvokeEnterCommandOnReturn = True,
					annotation = 'Replace Input',
					height = 35,
					enterCommand = Callback(self.replaceUICommand),
					changeCommand=Callback(self.updateNodeData, strings=True),
					placeholderText = 'Replace'
					)

			replaceButton = iconTextButton(
				rpt=True,
				style='textOnly',
				bgc = [0.2,0.2,0.2],
				annotation = 'Apply Rename',
				label='>>',
				width=60,
				command = Callback(self.replaceUICommand),
				)

			self.searchPopup(p=replaceButton, replace=True)

		replaceRow.attachForm(replaceButton, 'right', 0)
		replaceRow.attachNone(replaceButton, 'left')
		replaceRow.attachControl(inputsRow, 'right', 0, replaceButton)

	def replaceFocus(self):
		self.replaceField.setInsertionPosition(0)

	def searchPopup(self, p, replace=False, prefix=False, suffix=False):
		menu = popupMenu(p=p)
		with menu:
			menuItem(l='Select', c=Callback(self.selectionUICommands, replace=replace, prefix=prefix, suffix=suffix))

	def replaceUICommand(self):
		axmn_replace( search=self.searchField.getText(), replace=self.replaceField.getText() )

	def replaceSelectionUICommand(self):
		# Use selected nodes and search/replace inputs to get a new selection based on selected nodes' names

		selection = ls(sl=1)
		if not selection:
			warning('Nothing selected.')
			return None

		search = self.searchField.getText()
		replace = self.replaceField.getText()

		# Store a list of nodes that did not successfuly find an analog
		failList = []

		# For each node, return a list of nodes with the replaced name and add them to newSel list
		newSel = []
		for sel in selection:
			newName = sel.nodeName().replace(search, replace)
			# If search not found, will not succesfully replace
			# Check to make sure rename successful before even attempting to add
			# to prevent accidental extra selections (in the event of a name clash on selected node)
			findSel = []
			if not newName == sel.nodeName():

				findSel = ls(newName)

				# If there are any nodes in initial selection that get returned from this, make sure they don't remain in final list
				for node in findSel:
					if node not in selection:
						newSel.append(node)

			# If no analog found, store node to report on in the even of partial success
			if not findSel:
				failList.append(sel)


		# If new selection list is empty, don't change selection, and warn user
		if not len(newSel):
			select(selection)
			raise Exception('No nodes with replace string found.')

		# Expected behavior is to return to user as many nodes as were originally selected.  If less, make sure it's known
		if len(selection) > len(newSel):
			difference = len(selection) - len(newSel)

			print '\nInitial selection nodes with missing results:'
			for node in failList:
				print node.shortName()

			warning('Less nodes found than initially selected: %s' % (difference))

		# If more nodes found than expected, probably due to name clashes. Give user notice recourse for correction
		if len(selection) < len(newSel):

			difference = len(selection) - len(newSel)

			# 
			duplicates = []

			# create a list of nodeName strings to test against for duplicates
			duplicateNodeNames = []
			for node in newSel:
				duplicateNodeNames.append(node.nodeName())


			# Check each node in newSel for others with the same name
			for node in newSel:
				if self.dev: print duplicateNodeNames.count(node.nodeName())

				if duplicateNodeNames.count(node.nodeName()) > 1:
					duplicates.append(node.shortName())


			if duplicates:
				print '\nMulti-selections:'
				for dup in duplicates:
					print dup
				warning('More nodes found than initially selected: %s -- Duplicate Nodes: %s' % (-difference, duplicates) )
			else:
				warning('More nodes found than initially selected: %s' % (difference) )

		# select new nodes
		select(newSel)
		return newSel

	# ========================Prefix========================
	def prefixRowUI(self, p):
		prefixRow = horizontalLayout(p=p)
		with prefixRow:
			self.prefixField = textField(
				alwaysInvokeEnterCommandOnReturn = True,
				annotation = 'Prefix Input',
				height = 35,
				enterCommand = Callback(self.prefixUICommand),
					changeCommand=Callback(self.updateNodeData, strings=True),
				placeholderText = 'Prefix'
				)

			prefixButton = iconTextButton(
				rpt=True,
				style='textOnly',
				bgc = [0.2,0.2,0.2],
				annotation = 'Apply Prefix',
				label='>>',
				width=60,
				command = Callback(self.prefixUICommand)
				)

			self.searchPopup(p=prefixButton, prefix=True)


		stackHorizontalLayout(prefixRow)

	def prefixUICommand(self):
		axmn_prefix( prefix=self.prefixField.getText() )


	def selectionUICommands(self, replace=False, prefix=False, suffix=False):
		# Use selected nodes and search/replace inputs to get a new selection based on selected nodes' names

		selection = ls(sl=1)
		if not selection:
			warning('Nothing selected.')
			return None

		# self.prefixString

		# Store a list of nodes that did not successfuly find an analog
		failList = []

		# For each node, return a list of nodes with the replaced name and add them to newSel list
		newSel = []
		for sel in selection:
			if replace:
				if self.dev: print 'replace'
				if self.dev: print self.searchString
				newName = sel.nodeName().replace(self.searchString, self.replaceString)
				if self.dev: print newName
			if prefix:
				if self.dev: print 'prefix'
				newName = '%s%s' % (self.prefixString, sel.nodeName())
				if self.dev: print newName
			if suffix:
				if self.dev: print 'suffix'
				newName = '%s%s' % (sel.nodeName(), self.suffixString)
				if self.dev: print newName
			# If search not found, will not succesfully replace
			# Check to make sure rename successful before even attempting to add
			# to prevent accidental extra selections (in the event of a name clash on selected node)
			findSel = []
			if not newName == sel.nodeName():

				findSel = ls(newName)

				# If there are any nodes in initial selection that get returned from this, make sure they don't remain in final list
				for node in findSel:
					if node not in selection:
						newSel.append(node)

			# If no analog found, store node to report on in the even of partial success
			if not findSel:
				failList.append(sel)


		# If new selection list is empty, don't change selection, and warn user
		if not len(newSel):
			select(selection)
			raise Exception('No nodes with string found.')

		# Expected behavior is to return to user as many nodes as were originally selected.  If less, make sure it's known
		if len(selection) > len(newSel):
			difference = len(selection) - len(newSel)

			print '\nInitial selection nodes with missing results:'
			for node in failList:
				print node.shortName()

			warning('Less nodes found than initially selected: %s' % (difference))

		# If more nodes found than expected, probably due to name clashes. Give user notice recourse for correction
		if len(selection) < len(newSel):

			difference = len(selection) - len(newSel)

			# 
			duplicates = []

			# create a list of nodeName strings to test against for duplicates
			duplicateNodeNames = []
			for node in newSel:
				duplicateNodeNames.append(node.nodeName())


			# Check each node in newSel for others with the same name
			for node in newSel:
				if self.dev: print duplicateNodeNames.count(node.nodeName())

				if duplicateNodeNames.count(node.nodeName()) > 1:
					duplicates.append(node.shortName())


			if duplicates:
				print '\nMulti-selections:'
				for dup in duplicates:
					print dup
				warning('More nodes found than initially selected: %s -- Duplicate Nodes: %s' % (-difference, duplicates) )
			else:
				warning('More nodes found than initially selected: %s' % (difference) )

		# select new nodes
		select(newSel)
		return newSel

	# ========================Suffix========================
	def suffixRowUI(self, p):
		suffixRow = horizontalLayout(p=p)
		with suffixRow:
			self.suffixField = textField(
				alwaysInvokeEnterCommandOnReturn = True,
				annotation = 'Suffix Input',
				height = 35,
				enterCommand = Callback(self.suffixUICommand),
				changeCommand=Callback(self.updateNodeData, strings=True),
				placeholderText = 'Suffix'
				)

			suffixButton = iconTextButton(
				rpt=True,
				style='textOnly',
				bgc = [0.2,0.2,0.2],
				annotation = 'Suffix',
				label='>>',
				width=60,
				command = Callback(self.suffixUICommand)
				)

			self.searchPopup(p=suffixButton, suffix=True)

		stackHorizontalLayout(suffixRow)

	def suffixUICommand(self):
		axmn_suffix( suffix=self.suffixField.getText() )

	# ========================Clashes========================
	
	def clashRowUI(self, p):
		clashButtonRow = horizontalLayout(p=p)
		with clashButtonRow:

			selClashButton = iconTextButton(
				rpt=True,
				style='textOnly',
				bgc = [0.2,0.2,0.2],
				annotation = 'Select clashing dag nodes in scene',
				label='Select Clashing',
				# width=60,
				command = Callback(self.loadClashing)
				)

		# Clash return list and fix button
		clashSection = verticalLayout(p=p)
		with clashSection:
			self.clashingNodesList = textScrollList(
				allowMultiSelection = True,
				annotation = 'Clashing Nodes List',
				selectCommand=Callback(self.itemSelect),
				visible=False,
				font = 'fixedWidthFont',
				# doubleClickCommand=Callback(self.selectItemInList),
				# deleteKeyCommand=Callback(self.removeItems)
			)
			self.clashTextPopup(self.clashingNodesList)

			self.clashFixButton = iconTextButton(
				rpt=True,
				style='textOnly',
				bgc = [0.2,0.2,0.2],
				annotation = 'Automatically fix clashing dag nodes list',
				label='Fix Clashing',
				visible=False,
				# enable=False,
				command = Callback(self.fixClashingUICommand)
				)
		# Button follows bottom without stretching
		stackVerticalLayout(clashSection, reverse=True)
		 # textScrollList stretches to top of section
		clashSection.attachForm(self.clashingNodesList, 'top', 5)

		return clashSection
	
	def clashTextPopup(self, p):
		clashPopMenu = popupMenu(p=p)

		with clashPopMenu:
			# menuItem(l='Padding', enable=False)
			self.formatOptionShort = menuItem(l='Show Parentage', c=Callback(self.setFormatStyle, 'short'), enable=False if self.formatStyle == 'short' else True )
			self.formatOptionNode = menuItem(l='Hide Parentage', c=Callback(self.setFormatStyle, 'node'), enable=False if self.formatStyle == 'node' else True )
			# self.formatOptionLong = menuItem(l='Long Names', c=Callback(self.setFormatStyle, 'long'), enable=False if self.formatStyle == 'long' else True )


	def setFormatStyle(self, style):
		self.formatStyle = style
		self.updateNodeData(formatStyle=True)
		menuItem(self.formatOptionShort, e=True, enable=False if self.formatStyle == 'short' else True )
		menuItem(self.formatOptionNode, e=True, enable=False if self.formatStyle == 'node' else True )
		# menuItem(self.formatOptionLong, e=True, enable=False if self.formatStyle == 'long' else True )
		self.reloadClashing()

	def loadClashing(self):
		
		if self.dev: print 'loadClashing'
		waitCursor(state=True)
		try:
			# Clear List
			self.clashingNodesList.removeAll()
			
			# Return clashing nodes
			self.clashingNodes = getClashingNodes()

			if len(self.clashingNodes):
				self.initializeScriptJobs()

				self.spacing = self.minSpacing
				for node in self.clashingNodes:
					if len(node.nodeName())+self.minSpacing > self.spacing:
						self.spacing = len(node.nodeName())+self.minSpacing
				# Apply clashing nodes to textList UI
				for node in self.clashingNodes:

					self.clashingNodesList.append(self.formatClashing(node))
					# self.clashingNodesList.append(node.shortName())

				# Make textList visible
				self.clashingNodesList.setVisible(1)
				# Make fixall button visible
				self.clashFixButton.setVisible(1)
				warning('Clashing nodes found: %s' % len(self.clashingNodes))

			else:
				# Kill scriptjobs
				if self.renameJobNum is not None:
					scriptJob(kill=self.renameJobNum)
					self.renameJobNum = None
				if self.selectInSceneJobNum is not None:
					scriptJob(kill=self.selectInSceneJobNum)
					self.selectInSceneJobNum = None
				if self.nodeDeletedJobNum is not None:
					scriptJob(kill=self.nodeDeletedJobNum)
					self.nodeDeletedJobNum = None

				# Make list and button invisible
				self.clashingNodesList.setVisible(0)
				self.clashFixButton.setVisible(0)
				# Reset window height
				self.win.setHeight(self.defaultHeight)
				# Alert user
				warning('No name clashing nodes found in scene.')
		except:
			raise
		finally:
			waitCursor(state=False)

	def reloadClashing(self):
		'''Updates names and fonts of nodes without resetting clash list
		Allows updates upon name-change that without clearing the list.
		Returns fixed nodes in a new font'''

		# Compare the clashing nodes in the list to the a new data pull
		if self.dev: print 'reloadClashing'
		waitCursor(state=True)
		selection = ls(sl=1)
		try:

			if self.clashingNodesList.getNumberOfItems():

				clashingNodes = getClashingNodes()

				# Check for new clashing nodes not previously in list
				for node in clashingNodes:
					if not node in self.clashingNodes:
						warning('Naming changes has resulted in new clashing nodes not previously in list: %s' % node.shortName())
						# newClashes.append(node)

				# Edit spacing if value is greater
				for node in self.clashingNodes:
					if len(node.nodeName())+self.minSpacing > self.spacing:
						self.spacing = len(node.nodeName())+self.minSpacing

				# Reset list
				self.clashingNodesList.removeAll()
				for i, node in enumerate(self.clashingNodes):


					# Not fixed
					self.clashingNodesList.append('%s' % self.formatClashing(node))
					
					# Fixed
					if not node in clashingNodes:
						# Change font
						ind = i + 1 # TextList index is 1-based
						textScrollList(self.clashingNodesList, e=True, lineFont=[ind, 'obliqueLabelFont'])
						# Valid font values are boldLabelFont, smallBoldLabelFont, tinyBoldLabelFont, plainLabelFont, smallPlainLabelFont, obliqueLabelFont, smallObliqueLabelFont, fixedWidthFont and smallFixedWidthFont.

		except:
			raise
		finally:
			waitCursor(state=False)
			select(selection)

	def formatClashing(self, node):
		# Restructures input PyNode object to something more readable in textlist
		varSpacing = ' ' * (self.spacing - len(node.nodeName()))
		secondaryString = '' if node.shortName() == node.nodeName() else '%s*** %s' % (varSpacing, node.shortName())

		print (self.spacing - len(node.nodeName()))

		if self.formatStyle == 'short':
			return ('%s%s' % (node.nodeName(), secondaryString))
		elif self.formatStyle == 'long':
			return ('%s' % (node.longName()))
		elif self.formatStyle == 'node':
			return ('%s' % (node.nodeName()))
		else:
			raise Exception('Format input is not valid: %s' % self.formatStyle)

	def fixClashingUICommand(self):
		nodes = ls(sl=1)
		if not nodes:
			nodes = None
		clashFix(nodes=nodes)
		

	def itemSelect(self):
		textSelectList = []
		for itemSelected in self.clashingNodesList.getSelectIndexedItem():
			textSelectList.append( self.clashingNodes[itemSelected - 1])
		select(textSelectList)

	def selectInScene(self):

		selection = ls(sl=1)

		if len(selection):
			self.clashingNodesList.deselectAll()
			# # Check for any found.  if found, reset list selection
			# for sel in selection:
			# 	if sel in self.clashingNodes:
			# 		break

			# Get list
			inds = []
			for sel in selection:
				if sel in self.clashingNodes:
					inds.append(self.clashingNodes.index(sel) + 1)

			self.clashingNodesList.selectIndexedItems(inds)

	def checkListExists(self):
		# check for deleted nodes
		for node in self.clashingNodes:
			if not node.exists():
				self.clashingNodes.remove(node)
				self.reloadClashing()
		


	# ========================ScriptJobs========================

	def initializeScriptJobs(self):
		# UI parent not working

		if self.dev: print '\ninitializeScriptJobs'
		
		p = self.win
		
		# p=self.dock if self.dockUI else self.win
		self.renameJobNum = scriptJob(
			event=['NameChanged', Callback(self.reloadClashing)],
			killWithScene=True,
			p=p)

		self.selectInSceneJobNum = scriptJob(
			event=['SelectionChanged', Callback(self.selectInScene)],
			killWithScene = True,
			p=p)

		self.nodeDeletedJobNum = scriptJob(
			ct=['delete', Callback(self.checkListExists)],
			killWithScene = True,
			p=p)
		
# UI utilities

def stackVerticalLayout(form, reverse=False):
	objects = form.getChildren()
	if not reverse:
		form.attachForm(objects[0], 'top', 0)
		form.attachNone(objects[0], 'bottom')
		for i, obj in enumerate(objects):
			if i != 0:
				form.attachControl(obj, 'top', 5, objects[i-1])
				form.attachNone(obj, 'bottom')
	else:
		objects.reverse()
		form.attachNone(objects[0], 'top')
		for i, obj in enumerate(objects):
			if i != 0:
				form.attachControl(obj, 'bottom', 5, objects[i-1])
				form.attachNone(obj, 'top')
				
def stackHorizontalLayout(form, reverse=False):
	objects = form.getChildren()
	if not reverse:
		objects = list(reversed(objects))
		form.attachForm(objects[0], 'right', 0)
		form.attachNone(objects[0], 'left')
		for i, obj in enumerate(objects):
			if i != 0:
				form.attachControl(obj, 'right', 0, objects[i-1])
				form.attachNone(obj, 'left')
			if i == len(objects)-1:
				form.attachForm(obj, 'left', 2)

	else:
		form.attachForm(objects[0], 'left', 2)
		form.attachNone(objects[0], 'right')
		for i, obj in enumerate(objects):
			if i != 0:
				form.attachControl(obj, 'left', 2, objects[i-1])

def padFormat(integer, padding):

	d = '%d' % integer
	if padding == 1:
		d = '%01d' % integer
	elif padding == 2:
		d = '%02d' % integer
	elif padding == 3:
		d = '%03d' % integer
	elif padding == 4:
		d = '%04d' % integer

	return d	

