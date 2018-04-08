from pymel.core import *
# import utils

class renamingUI:
	# 
	def __init__(self):

		# Print development messages in console
		self.dev = True

		# Restore selection after initialization
		selection = ls(sl=1)

		# ================================================= DATA ========================================================= 
		# Default padding value
		self.paddingValue = 0
		self.startValue = 1


		# Store local settings data in network node to preserve between instances
		if not(len(ls('renameUIData'))):
			self.renameUIDataNode = createNode('network', n='renameUIData')
		else:
			self.renameUIDataNode = ls('renameUIData')[0]

		if not hasAttr(self.renameUIDataNode, 'padding'):
			addAttr(self.renameUIDataNode, ln='padding', at='short', min=0, max=4, dv=self.paddingValue, k=1)
		if not hasAttr(self.renameUIDataNode, 'start'):
			addAttr(self.renameUIDataNode, ln='start', at='short', min=0, dv=self.startValue, k=1)

		if not hasAttr(self.renameUIDataNode, 'start'):
			addAttr(self.renameUIDataNode, ln='start', at='short', min=0, dv=self.startValue, k=1)
		
		self.paddingValue = self.renameUIDataNode.padding.get()
		self.startValue = self.renameUIDataNode.start.get()



		# ================================================= UI ========================================================= 

		self.UI()

		select(selection)

	def UI(self):

		# create window if invoked alone
		# if win == None:
			# Reset ui if exists
		if window('axmn_rename_window', exists=True):
			deleteUI('axmn_rename_window')

		# Create window
		self.win = window('axmn_rename_window', t='Rename', width=300, height=171, resizeToFitChildren=1, sizeable=1, mxb=0)
		# else:
		# 	self.win = win


		allLayout = verticalLayout(p=self.win, spacing=1)
		
		renameRow = self.renameRow(p=allLayout)
		replaceRow = self.replaceRow(p=allLayout)
		prefixRow = self.prefixRow(p=allLayout)
		suffixRow = self.suffixRow(p=allLayout)

		# Stretch across width
		allLayout.redistribute()
		# Take as much vertical space as necessary from top downwards
		stackVerticalLayout(allLayout)

		showWindow(self.win)


	def updateNodeData(self, padding=False, start=False):
		# If no inputs, assume all inputs.  If input, assume others False.
		if all([not padding, not start]):
			padding=True
			start=True

		if padding:
			# if self.dev: print 'padding'
			inp = self.getPaddingInput()
			if inp is None:
				inp = 0
			self.renameUIDataNode.padding.set(inp)
			self.paddingValue = inp

		if start:
			# if self.dev: print 'start'
			inp = self.paddingStartField.getValue()
			self.renameUIDataNode.start.set(inp)
			self.startValue = inp

		# if naming:
		# 	inp = self.renameField.getText()
		# 	self.renameUIDataNode.rename.set(inp)

	# ========================Rename========================

	def renameRow(self, p):
		# Renaming UI Widget
		renameRow = horizontalLayout(p=p)
		with renameRow:
			# Rename Field
			self.renameField = textField(
				alwaysInvokeEnterCommandOnReturn = True,
				annotation = 'Rename Input',
				height = 35,
				enterCommand = Callback(self.renameUICommand),
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

		# padding = self.getPaddingInput()
		# start = self.paddingStartField.getValue()

		padding = self.paddingValue
		start = self.startValue

		# If textfield is empty, use first selected object's nodeName
		# TODO: remove didgets at end?

		if self.renameField.getText():
			renameText = self.renameField.getText()
		else:
			renameText = ls(sl=1)[0].nodeName()

			
		axmn_rename(renameText, padding=padding, start=start)


	# ========================Replace========================
	def replaceRow(self, p):
		replaceRow = horizontalLayout(p=p)
		with replaceRow:
			inputsRow = horizontalLayout(spacing=0)
			with inputsRow:
				self.searchField = textField(
					alwaysInvokeEnterCommandOnReturn = True,
					annotation = 'Search Input',
					height = 35,
					enterCommand = Callback(self.replaceFocus),
					placeholderText = 'Search'
					)

				self.replaceField = textField(
					alwaysInvokeEnterCommandOnReturn = True,
					annotation = 'Replace Input',
					height = 35,
					enterCommand = Callback(self.replaceUICommand),
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

			self.replacePopup(p=replaceButton)

		replaceRow.attachForm(replaceButton, 'right', 0)
		replaceRow.attachNone(replaceButton, 'left')
		replaceRow.attachControl(inputsRow, 'right', 0, replaceButton)

	def replaceFocus(self):
		self.replaceField.setInsertionPosition(0)

	def replacePopup(self, p):
		replaceMenu = popupMenu(p=p)
		with replaceMenu:
			# menuItem(l='Padding', enable=False)
			menuItem(l='Select', c=Callback(self.replaceSelectionUICommand))

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
	def prefixRow(self, p):
		prefixRow = horizontalLayout(p=p)
		with prefixRow:
			self.prefixField = textField(
				alwaysInvokeEnterCommandOnReturn = True,
				annotation = 'Prefix Input',
				height = 35,
				enterCommand = Callback(self.prefixUICommand),
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

		stackHorizontalLayout(prefixRow)

	def prefixUICommand(self):
		axmn_prefix( prefix=self.prefixField.getText() )

	# ========================Suffix========================
	def suffixRow(self, p):
		suffixRow = horizontalLayout(p=p)
		with suffixRow:
			self.suffixField = textField(
				alwaysInvokeEnterCommandOnReturn = True,
				annotation = 'Suffix Input',
				height = 35,
				enterCommand = Callback(self.suffixUICommand),
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

		stackHorizontalLayout(suffixRow)

	def suffixUICommand(self):
		axmn_suffix( suffix=self.suffixField.getText() )


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
		# print valCheck
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
		# print d
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


def clashFix(sel=None):
	with UndoChunk():
		if sel is None:
			sel = ls(dagObjects=1)
		if not isinstance(sel, list):
			sel = [sel]
		for s in sel:
			# get name
			try:
				name = s.nodeName()
			except AttributeError:
				warning('Selection input should be Pymel instance. %s, %s' % (s, s.type()))
			withName = ls(name)
			if len(withName) > 1:
				for i, dup in enumerate(withName):
					dup.rename('%s%s' % (name, i))
					print '%s%s' % (name,  i)

