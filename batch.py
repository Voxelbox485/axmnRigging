from pymel.core import *
import maya.mel
import utils
import colorOverride as col
from copy import deepcopy

'''

TODO
workspace control 
load outputs/inputs based on field
Print all data about attribute selected?

TEST When using Insert Nodes, replace destination nodes with insert nodes, and cut and paste destination list to NEXT history window.

Context specific marking menus (Within node editor)
http://bindpose.com/custom-marking-menu-maya-python/
http://bindpose.com/custom-marking-menus-maya-editors/
http://bindpose.com/custom-global-hotkey-maya/

Add integer sorting
TEST auto remove AC_divider from add list

Add 'other' writeIn to Insert Nodes

Use '#' to quickly add multiple numbered attributes from write-in
# attr[#]
Handling of multi-attributes:
	when detected, add [#]
	or add one for each initialized, if that's something that can be detected
	or simulate initialization by adding a new autocomplete option -- .attr[1]

'''

class axmn_batch:

	'''Creates a UI for managing multiple node and attribute interactions at once, especially direct connections,
	but also constraints and parenting.'''

	# Get ui globals
	# gChannelBox = 		mel.eval('global string $gChannelBoxName; $temp=$gChannelBoxName;')
	gChannelBox = 		melGlobals['gChannelBoxName']
	# gMainProgressBar = 	mel.eval('global string $gMainProgressBar; $temp = $gMainProgressBar')
	gMainProgressBar = 	melGlobals['gMainProgressBar']
	# gWSElement = 		mel.eval('getUIComponentDockControl("Channel Box / Layer Editor", false);') 
	gWSElement = 		mel.getUIComponentDockControl("Channel Box / Layer Editor", False)
	# gNodeEditor = 	mel.eval('$temp = `getCurrentNodeEditor`')
	gNodeEditor = 		mel.getCurrentNodeEditor()
	

	def __init__(self, dev=False):
		'''Initializes class attributes and UI'''
		# ============================================ SCRIPT SETTINGS ==================================================== 
		self.dev = dev
		self.dockUI = True
		self.buttonHeight = 25
		self.frameColor = (0.119, 0.484, 0.395)



		# Reload any scripts I might also be working on
		if self.dev:
			reload(utils)
			reload(col)

		# ================================================= DATA ========================================================= 

		# Defaults
		self.writeInMode = 'attributes' #default writein setting ('attributes' or 'nodes')
		self.autoSorted = False
		self.useShortNames = False
		self.searchSelected = False
		self.resultListMaxHeight = 0 # 0: No max
		self.lsLimit = 500 # Will stop node lookup after a certain point in large scenes
		
		# Data Storage
		self.defaultAutoCompleteList = []
		self.sortedAutoCompleteList = []
		self.autoCompleteList = []
		self.resultListExpanded = True
		self.AC_divider = '***'
		self.historyButtons = []
		self.sequence = False # Determines whether next connection will move the history forward (for insert nodes)
	
		# Node creation naming dictionary
		self.typeDict = {
			'multDoubleLinear'	:	'mdl',
			'multiplyDivide'	:	'mdv',
			'condition'			:	'cond',
			'setRange'			:	'sr',
			'addDoubleLinear'	:	'adl',
			'plusMinusAverage'	:	'pma',
			'clamp'				:	'clmp',
			'remapValue'		:	'rmap',
			'blendColors'		:	'blndC',
			'blendTwoAttr'		:	'blnd',
			'reverse'			:	'rev',
			'animCurveUU'		:	'sdk'
		}

		# ================================================= UI ========================================================= 
		# Initialize as strings, and replace with ui objects. That way code will take a guess before giving up if ui object not initialized
		self.win = 'axmn_batch_window'
		self.dock = 'axmn_batch_dock'
		self.workspace = 'axmn_batch_workspace'
 
		# If ui is to be dockable and current ver of maya uses workspaces, use workspaces
		self.workspaceUI = False
 		# TODO: Been spinning my wheels on this one. Not sure how to get it to behave properly
		# if self.dockUI:
		# 	if versions.current() > versions.v2017:
		# 		self.dockUI = False
		# 		self.workspaceUI = True
		self.unhiddenAttributes = [] # cbShowAll stores here

		# History
		# This is how the nodes and attributes data (for the text lists) are stored. They hold not only the current visible data, but saveable instances
		# of previous connections, allowing users to reuse recent inputs
		self.itemLists = [ [ [], [], [], [] ] ]
		self.hIndex = 0 # index of visible data

		# Collect ui control objects for later update
		self.textLists = []
		self.popupMenus = []
		self.frames = []
		# 

		# Delete any existing UI elements (based on string)

		if versions.current() > versions.v2017:
			if workspaceControl(self.workspace, exists=True):
				try:
					workspaceControl(self.workspace, close=True)
					deleteUI(self.workspace, control=True)
				except:
					warning('Workspace found, but could not be deleted')

		if window(self.win, exists=True):
			deleteUI(self.win)

		if dockControl(self.dock, exists=True):
			deleteUI(self.dock)
 		

		self.win = window('axmn_batch_window', t='Batch Connect', retain=False, width=300, resizeToFitChildren=1, sizeable=1, mxb=0)
		self.UI(p=self.win)


		# Workspace

		if versions.current() > versions.v2017:
			if self.workspaceUI:
				self.workspace = workspaceControl(self.workspace, retain=False, floating=True, tabToControl=[self.gWSElement, -1], wp="preferred", mw=420, uiScript=self.win)
			
		# Dock
		if self.dockUI:
			self.dock = dockControl(
				self.dock,
				l='Batch Connection Editor',
				area='left',
				content=self.win,
				allowedArea=['right', 'left'],
				retain=False
				)

		# Window
		if not self.workspaceUI and not self.dockUI:
			showWindow(self.win)

		self.everything.redistribute()
		self.stackVerticalLayout(self.everything)
		self.everything.attachForm(self.overallPane, 'bottom', 0)

		self.updateHistUI()
		self.setInitialHeight() # Sets textLists to take up larger percentage of window
		self.initializeScriptJobs()


	def UI(self, p=None):
		'''Does the work of initializing the UI. Individual sections handled by other defs for easy reordering and such
		
		Potentially useful icons:
		Dash_Expand.png ( > )
		Dash_Expand_150.png
		Dash_Expand_200.png

		hsUpStreamCon.png ( >[ ] )
		hsDownStreamCon.png ( [ ]> )
		hsDownStreamCon.png ( >[ ]> )

		QR_refresh.png (refresh)
		RS_accept_import.png (refresh list)
		QR_delete.png (trash)
		QR_rename.png (writeIn)
		QR_add.png (+, add)
		QR_settings.png (settings)
		RS_quick_settings_popup.png (settings popup)
		RS_disable.png (circle cross)

		UVTkVerticalToggleOff_100.png (Toggle on)
		UVTkVerticalToggleOn.png (Toggle off)


		polyStackOrient.png (Sort)
		polyStackShell.png (Default Sort)
		polyUnitizeUVs.png (copy)

		polyDeleteInvalidUVset.png (delete 4 frames)

		polySplitUVs.png (Cross Connection pattern)
		polyUVRectangle.png (one to one conection pattern?)

		polyOptimizeUV.png (4 panels checks out)
		polyPinUV.png (pin panels)
		polyCreateUVShell.png (panels add)

		absolute.png(square cross)

		'''

		if not p is None:
			self.everything = verticalLayout(p=p)
		else:
			self.everything = verticalLayout()

		# Show all attributes row
		attrRow = self.attributesRowUI(p=self.everything)

		# Previous commands history row
		historyRow = self.historyRowUI(p=self.everything)

		self.overallPane  = paneLayout(configuration= 'horizontal2', separatorThickness=5, staticHeightPane=1, p=self.everything)
		with self.overallPane:
			self.mainForm = verticalLayout()
			with self.mainForm:
				# Text list panes
				self.pane = paneLayout(configuration= 'horizontal2', separatorThickness=5)
				with self.pane:
					self.textListsUI()

			otherPane = verticalLayout()
			self.otherPane = otherPane
			with otherPane:
				scroller = scrollLayout(rc = self.resizeScroller)
				with scroller:

					self.scrollStretch = verticalLayout()
					with self.scrollStretch:
						self.autoCompleteUI()
	
						self.commandsFrameUI()

						self.nodesFrameUI()

					self.stackVerticalLayout(self.scrollStretch)
		

		return self.everything

	# ------------------- Widgets --------------------

	def attributesRowUI(self, p):
		# Show all attributes row
		attrRow = verticalLayout(p=p, spacing=0)
		with attrRow:
			# row1 = horizontalLayout(ratios = [4,1])
			# with row1:
			# 	button(l='Show Attributes in CB',
			# 		c=Callback(self.cbShowAll))

			# 	button(l='Save Sel',
			# 		c=Callback(self.cbSaveSel))

			row2 = horizontalLayout()
			with row2:
				button(l='<< CB Inputs',
					command = Callback(self.selectCBInputs))
				button(l='CB Outputs >>',
					command = Callback(self.selectCBOutputs))
		return attrRow

	def historyRowUI(self, p):
		# Previous commands history row
		settings = False # Button that opens settings window. No settings yet.
		histColumn = verticalLayout(p=p)
		with histColumn:

			self.histCounterView = horizontalLayout(spacing=1)
			with self.histCounterView:
				if settings:
					if versions.current() > versions.v2017:
						self.settingsButton = iconTextButton(
							image = 'QR_settings.png',
							style='iconOnly',
							c = Callback(self.settingsPopup),
							p = self.histCounterView
							)
					else:
						self.settingsButton = iconTextButton(
							l = 'S',
							style='textOnly',
							c = Callback(self.settingsPopup),
							p = self.histCounterView
							)

				# self.histScroll = scrollLayout(p=self.histCounterView, h=30)
				self.histButtons = horizontalLayout(p = self.histCounterView, spacing=1)
				self.newHistButton = iconTextButton(
					style='iconOnly',
					image = 'hsClearView.png',
					c = Callback(self.addToHistory, True),
					p = self.histCounterView
					)
				self.histCounter = text(l='0', width=10, p=self.histCounterView)
				
				


			self.stackHorizontalLayout(self.histCounterView)
			if settings:
				self.histCounterView.attachForm(self.settingsButton, 'left', 5)
				self.histCounterView.attachNone(self.settingsButton, 'right')


			self.histCounterView.attachForm(self.histCounter, 'right', 10)
			self.histCounterView.attachNone(self.histCounter, 'left')

			self.histCounterView.attachControl(self.newHistButton, 'right', 1, self.histCounter)


			historyRow = horizontalLayout(ratios = [8,2,8])
			with historyRow:

				# Prev history button
				if versions.current() > versions.v2018:
					self.histBackButton = iconTextButton(
					image = 'Dash_Expand.png',
					style='iconOnly',
					rotation=3.14, # Turned
					bgc = [0.2,0.2,0.2],
					enable=0,
					c = Callback(self.histBack)
					)
				else:
					self.histBackButton = iconTextButton(
					l='<<',
					style='textOnly',
					bgc = [0.2,0.2,0.2],
					enable=0,
					c = Callback(self.histBack)
					)

				# Clear window button
				if versions.current() > versions.v2017:
					clearWindowButton = iconTextButton(
					image = 'QR_delete.png',
					style='iconOnly',
					bgc = [0.2,0.2,0.2],
					c = Callback(self.clearWindow),
					dcc = Callback(self.deleteSave)
					)
				else:
					clearWindowButton = iconTextButton(
					l='X',
					style='textOnly',
					bgc = [0.1,0.1,0.1],
					c = Callback(self.clearWindow),
					dcc = Callback(self.deleteSave)
					)


				if versions.current() > versions.v2018:
				# Next history button
					self.histForwardButton = iconTextButton(
					image = 'Dash_Expand.png',
					style='iconOnly',
					bgc = [0.2,0.2,0.2],
					enable=0,
					c = Callback(self.histForward)
					)
				else:
					# Next history button
					self.histForwardButton = iconTextButton(
					l='>>',
					style='textOnly',
					bgc = [0.2,0.2,0.2],
					enable=0,
					c = Callback(self.histForward),
					)
		self.stackVerticalLayout(histColumn)

		return histColumn



	def textListsUI(self):
		# TextLists row
		q=0
		leftRightString = ['Source', 'Destination']
		upDownString = ['Nodes', 'Attributes']
		for j in range(2):
			# Node, attributes rows
			row = horizontalLayout(spacing=0)
			with row:#================================================================================================
				# Source, destination Columns
				for i in range(2):
					column = verticalLayout(spacing=1)
					with column:#================================================================================================
						frame = frameLayout(l='%s %s' % (leftRightString[i], upDownString[j]), collapsable=0, bgc=self.frameColor)
						self.frames.append(frame)
						with frame:#================================================================================================
							
							inFrameColumn = verticalLayout(ratios=[0,0], spacing=0)
							with inFrameColumn:#================================================================================================
								# List / '^' 'v' buttons
								listButtons = horizontalLayout(ratios=[0,0], spacing=0)

								with listButtons:
									height = 200
									if j:
										height = 150
									objectList = textScrollList(
										allowMultiSelection = True,
										annotation = '%s %s List' % (leftRightString[i], upDownString[j]),
										selectCommand=Callback(self.itemSelect, q),
										doubleClickCommand=Callback(self.selectItemInList, q),
										deleteKeyCommand=Callback(self.removeItems, q)
									)
									
									self.textLists.append(objectList)

									popMen = self.popUpOptions(q)

									# Button Column
									buttonColumn = verticalLayout(spacing=0, width=15)
									with buttonColumn:
										updnCol = verticalLayout(spacing=1)
										with updnCol:
											
											# Check version before using icons
											if versions.current() > versions.v2017:
												upButton = iconTextButton(
												style='iconOnly',
												image = 'UVTkPointRight.png',
												rotation = 3.1315/2,
												flipX= True,
												bgc = [.17,.17,.17],
												c = Callback(self.moveUp, q)
												)
												dnButton = iconTextButton(
												l='v',
												style='iconOnly',
												image = 'UVTkPointRight.png',
												rotation = 3.1315/2,
												bgc = [.17,.17,.17],
												c = Callback(self.moveDown, q)
												)
											else:
												upButton = iconTextButton(
												l='^',
												style='textOnly',
												bgc = [.17,.17,.17],
												c = Callback(self.moveUp, q)
												)

												dnButton = iconTextButton(
												l='v',
												style='textOnly',
												bgc = [.17,.17,.17],
												c = Callback(self.moveDown, q)
												)
								
								# Stack horizontally so that side buttons retain width when horizontally scaling
								self.stackHorizontalLayout(listButtons)


								buttonRow = horizontalLayout(height=30, ratios=[1,1], spacing=2)
								with buttonRow:#================================================================================================
									addButton = iconTextButton(
									rpt=True,
									style='textOnly',
									bgc = [0.2,0.2,0.2],
									annotation = 'Add %s %ss' % (leftRightString[i], upDownString[j]),
									label='Add')
									addButton.setCommand(Callback(self.addItems, q))
									if q>1:
										addButton.setDoubleClickCommand(Callback(self.addNodesAndAttributes, q))
									else:
										addButton.setDoubleClickCommand(Callback(self.selectAllItemsInList, q))


									removeButton = iconTextButton(
									rpt=True,
									style='textOnly',
									bgc = [0.2,0.2,0.2],
									annotation = 'Remove %s %ss' % (leftRightString[i], upDownString[j]),
									label='Remove')
									removeButton.setCommand(Callback(self.removeItems, q))
									removeButton.setDoubleClickCommand(Callback(self.removeAllItems, q))
									q = q + 1

							
							# Stack each frame quadrant so that buttons are attached to bottom, list is attached to top, and midList bottomline follows buttons vertically
							inFrameColumn.attachForm(listButtons, 'top', 5)
							inFrameColumn.attachControl(listButtons, 'bottom', 5, buttonRow)
							inFrameColumn.attachNone(buttonRow, 'top')
							inFrameColumn.attachForm(buttonRow, 'bottom', 5)


	def autoCompleteUI(self):
		autoCompleteMenuColumn = horizontalLayout()
		with autoCompleteMenuColumn:

			writeIn = textField(
				alwaysInvokeEnterCommandOnReturn = True,
				annotation = 'Manual Input',
				height = 25,
				)
			self.writeIn = writeIn

			writeInMenu = self.autoCompleteWriteInPopup(self.writeIn)

			# self.inputValueButton = button(
			# 	l='<<',
			# 	width = 10,
			# 	c=Callback(self.writeInInsert)
			# 	)
			# Check version before using icons
			if versions.current() > versions.v2017:
				insertFieldButton = iconTextButton(
				style='iconOnly',
				image = 'Dash_Expand.png',
				rotation = 3.14,
				c=Callback(self.writeInInsert),
				width = 30
				)
			else:
				insertFieldButton = iconTextButton(
				style='textOnly',
				l = '<<',
				rotation = 3.14,
				c=Callback(self.writeInInsert),
				width = 30
				)
			if versions.current() > versions.v2017:
				clearFieldButton = iconTextButton(
				style='iconOnly',
				image = 'RS_disable.png',
				width = 30,
				c=Callback(self.clearWriteIn)
				)
			else:
				clearFieldButton = iconTextButton(
				l='X',
				width = 20,
				c=Callback(self.clearWriteIn)
				)

			
		self.stackHorizontalLayout(autoCompleteMenuColumn)


		self.resultListExpandButton = button(
			height = 10,
			l='',
			bgc=self.frameColor,
			c=Callback(self.toggleResultListExpanded)
			)

		resultListColumn = horizontalLayout()
		with resultListColumn:


			self.AC_resultList = textScrollList(
				height=25,
				allowMultiSelection = True,
				annotation = 'Autocomplete List',
				font = 'fixedWidthFont',
				doubleClickCommand=Callback(self.selectItemInList, 4),
				visible=False
				)
			self.textLists.append(self.AC_resultList)

			autoCompleteMenu = self.autoCompleteListPopup(self.AC_resultList)
		# self.stackHorizontalLayout(resultListColumn)
		# Auto Complete right-click window
		
		writeIn.changeCommand(Callback(self.autoComplete))
		writeIn.enterCommand(Callback(self.autoComplete))

	def commandsFrameUI(self):
		# standardCommandsColor = 	(0.45,0.45,0.45)
		standardCommandsColor = 	(0.3,0.3,0.3)
		nodeCommandsColor = 		(0.55,0.55,0.55)

		commandsFrame = frameLayout(l='Functions', bgc=self.frameColor, collapsable=1, collapse=0)
		self.frames.append(commandsFrame)
		with commandsFrame:
			commandsColumn = verticalLayout()
			with commandsColumn:

				# connectButton
				row = horizontalLayout(spacing=0, ratios=[1,4], height=self.buttonHeight+8)
				with row:

					iconTextButton(
						style = 'iconAndTextCentered',
						rpt = True,
						i = 'hsUpDownStreamCon.png',
						annotation = 'Direct attribute connection.',
						height = self.buttonHeight-5,
						# width = self.buttonHeight-5,
						flat=1,
						bgc=(standardCommandsColor),
						c=Callback(self.connect)
						)
					iconTextButton(
						style = 'iconAndTextCentered',
						rpt = True,
						l = 'Connect',
						annotation = 'Direct attribute connection.',
						height = self.buttonHeight,
						bgc=(standardCommandsColor),
						c=Callback(self.connect)
						)
				# transferInputsButton
				row = horizontalLayout(spacing=0, ratios=[1,4], height=self.buttonHeight+8)
				with row:
					iconTextButton(
						style = 'iconAndTextCentered',
						rpt = True,
						i = 'hsUpStreamCon.png',
						annotation = 'Transfer attribute input plugs from source to destination.',
						height = self.buttonHeight-5,
						# width = self.buttonHeight-5,
						flat=1,
						bgc=(standardCommandsColor),
						c=Callback(self.transferInputs)
						)
					iconTextButton(
						style = 'iconAndTextCentered',
						rpt = True,
						l = 'Transfer Inputs',
						annotation = 'Transfer attribute input plugs from source to destination.',
						height = self.buttonHeight,
						bgc=(standardCommandsColor),
						c=Callback(self.transferInputs)
						)

				# transferOutputsButton
				row = horizontalLayout(spacing=0, ratios=[1,4], height=self.buttonHeight+8)
				with row:
					iconTextButton(
						style = 'iconAndTextCentered',
						rpt = True,
						i = 'hsDownStreamCon.png',
						annotation = 'Transfer attribute output plugs from source to destination.',
						height = self.buttonHeight-5,
						# width = self.buttonHeight-5,
						flat=1,
						bgc=(standardCommandsColor),
						c=Callback(self.transferOutputs)
						)
					iconTextButton(
						style = 'iconAndTextCentered',
						rpt = True,
						l = 'Transfer Outputs',
						annotation = 'Transfer attribute output plugs from source to destination.',
						height = self.buttonHeight,
						bgc=(standardCommandsColor),
						c=Callback(self.transferOutputs)
						)
				

			self.stackVerticalLayout(commandsColumn)
			
			nodeCommandsColumn = verticalLayout()
			with nodeCommandsColumn:	
				# Cast nodes
				row = horizontalLayout(spacing=0, ratios=[1,4], height=self.buttonHeight+8)
				with row:

				
					iconTextButton(
						style = 'textOnly',
						rpt = True,
						l='',
						annotation = 'Transfer all Inputs and Outputs to new node.',
						height = self.buttonHeight-5,
						# width = self.buttonHeight-5,
						flat=1,
						bgc=(nodeCommandsColor),
						c=Callback(self.castNodes)
						)
					iconTextButton(
						style = 'iconAndTextCentered',
						rpt = True,
						l = 'Cast Node',
						annotation = 'Transfer all Inputs and Outputs to new node.',
						height = self.buttonHeight,
						bgc=(nodeCommandsColor),
						c=Callback(self.castNodes)
						)
									
				# constrain lists
				row = horizontalLayout(spacing=0, ratios=[1,4], height=self.buttonHeight+8)
				with row:

				
					iconTextButton(
						style = 'textOnly',
						rpt = True,
						l='',
						annotation = 'Constrain transform attributes using worldMatrix.',
						height = self.buttonHeight-5,
						# width = self.buttonHeight-5,
						flat=1,
						bgc=(nodeCommandsColor),
						c=Callback(self.constrainLists)
						)
					iconTextButton(
						style = 'iconAndTextCentered',
						rpt = True,
						l = 'Matrix Constraint',
						annotation = 'Constrain transform attributes using worldMatrix.',
						height = self.buttonHeight,
						bgc=(nodeCommandsColor),
						c=Callback(self.constrainLists)
						)

				# parentButton
				row = horizontalLayout(spacing=0, ratios=[1,4], height=self.buttonHeight+8)
				with row:
					iconTextButton(
						style = 'textOnly',
						rpt = True,
						l='',
						annotation = 'Parent destination nodes to source nodes.',
						height = self.buttonHeight-5,
						# width = self.buttonHeight-5,
						flat=1,
						bgc=(nodeCommandsColor),
						c=Callback(self.parentLists)
						)
					iconTextButton(
						style = 'iconAndTextCentered',
						rpt = True,
						l = 'Parent',
						annotation = 'Parent destination nodes to source nodes.',
						height = self.buttonHeight,
						bgc=(nodeCommandsColor),
						c=Callback(self.parentLists)
						)

			self.stackVerticalLayout(nodeCommandsColumn)
		
		return commandsFrame

	def nodesFrameUI(self):
		nodesFrame = frameLayout(l='Insert Nodes', bgc=self.frameColor, collapsable=1, collapse=0)
		self.frames.append(nodesFrame)
		with nodesFrame:
			nodesDict = {
			'Mult Double Linear' : 		['render_multDoubleLinear.png', 	'multDoubleLinear'		],
			'Multiply Divide' : 		['render_multiplyDivide.png', 		'multiplyDivide'		],
			'Condition' : 				['render_condition.png', 			'condition'				],
			'Set Range' : 				['render_setRange.png', 			'setRange'				],
			'Add Double Linear' : 		['render_addDoubleLinear.png', 		'addDoubleLinear'		],
			'Plus Minus Average' : 		['render_plusMinusAverage.png', 	'plusMinusAverage'		],
			'Clamp' : 					['render_clamp.png', 				'clamp'					],
			'Remap' : 					['render_remapValue.png', 			'remapValue'			],
			'Blend Colors' : 			['render_blendColors.png', 			'blendColors'			],
			'Blend Two Attributes' : 	['render_blendTwoAttr.png', 		'blendTwoAttr'			],
			'Reverse' : 				['render_reverse.png', 				'reverse'				],
			'Set Driven Key' : 			['bezNormalSelect.png', 			'animCurveUU'			],
			}
			nodeButtons = verticalLayout()
			with nodeButtons:
				for node in nodesDict.keys():
					row = horizontalLayout(spacing=0, ratios=[1,4], height=self.buttonHeight+8)
					with row:
						annotataion = 'Insert %s' % node
						icon = nodesDict[node][0]
						label = node
						bgc = (0.3,0.3,0.3)
						c = Callback(self.insertNodes, nodesDict[node][1])
						# dcc = Callback(self.createNodes, nodesDict[node][1])

						iconTextButton(style = 'iconAndTextCentered', i = icon, annotation = annotataion, height = self.buttonHeight-5, flat=1, bgc=bgc, c=c)
						iconTextButton(style = 'iconAndTextCentered', l = label, annotation = annotataion, height = self.buttonHeight, bgc=bgc, c=c)
				
				separator(style='none', height=10)

			return nodesFrame



	def getSelectedInAutoComplete(self):
		index = self.textLists[4].getSelectIndexedItem()
		index = self.convertIndex(index)

		newList = []
		for ind in index:
			newList.append(self.autoCompleteList[ind])
		
		return newList

	# ------------------- Popup Windows --------------------
	def popUpOptions(self, listIndex):
		menu = popupMenu()
		with menu:
			menuItem(l='Refresh',
				c=Callback(self.updateLists))
			menuItem(l='Alphabetize',
				c=Callback(self.sortList, listIndex))
			menuItem(l='Reverse Order',
				c=Callback(self.reverseList, listIndex))
			menuItem(l='Swap',
				c=Callback(self.swap, listIndex))
			menuItem(l='Copy',
				c=Callback(self.copyList, listIndex))
			# menuItem(l='Select Inputs')
			# menuItem(l='Select Outputs')
			# TODO
			# menuItem(l='Load Inputs')
			# menuItem(l='Load Outputs')
			menuItem(l='To Top',
				c=Callback(self.moveToTop, listIndex))
			menuItem(l='To Bottom',
				c=Callback(self.moveToBot, listIndex))
		return menu
	

	def autoCompleteWriteInPopup(self, parent):
		menu = popupMenu(p=parent)
		with menu:
			self.modeAutoCompleteMenu = menuItem(
				l='Nodes Mode',
				c=Callback(self.autoListTypeToggle),
				)
		return menu


	def autoCompleteListPopup(self, parent):
		menu = popupMenu(p=parent)
		with menu:
			self.searchSelectedAutoCompleteMenu = menuItem(
				l='Query Nodes Selected',
				c=Callback(self.searchSelectedToggle),
				)
			self.selectAllAutoCompleteMenu = menuItem(
				l='Select All',
				c=Callback(self.selectAllItemsInAutoCompleteList),
				)
			self.sortAutoCompleteMenu = menuItem(
				l='Alphabetize',
				c=Callback(self.autoListSortToggle),
				)
			self.shortAutoCompleteMenu = menuItem(
				l='Use Short Names',
				c=Callback(self.useShortNamesToggle),
				)
			self.unhideAutoCompleteMenu = menuItem(
				l='Unhide Selected Attributes',
				c=Callback(self.unhideAttributeSelected)
				)

		return menu


	def settingsPopup(self):
		if self.dev:
			if window('axmn_batch_settings', exists=True):
				deleteUI('axmn_batch_settings')
			else:
				self.settingsWin = window('axmn_batch_settings', t='Settings', width=300, resizeToFitChildren=1, sizeable=1, mxb=0)
				with self.settingsWin:
					with verticalLayout():
						self.lsLimitField = intField(min=0, value=self.lsLimit, cc=self.setLsLimit)
						saveButton = button(l='Save', c=self.saveSettings())

	def setLsLimit(self):
		self.lsLimit = self.lsLimitField.getValue()

	# ------------------- Settings --------------------

	# ======================================== Commands ========================================
	
	# TODO
	def insertNodes(self, nodeType):
		'''
		Instead of directly connecting attributes in input lists, this script creates and inserts nodes between the connecting nodes.
		It does this by splitting the operation into two steps by utilizing the 'conneciton history' feature.
		Creates a new history item AFTER current item, and organizes:
		
		SOURCE --> DEST
		
		into:
		
		SOURCE --> INSERT
		INSERT --> DEST
		'''
		if self.dev: print '\ninsertNodes'

		connections = self.getConnectionPattern()

		# createNodes
		insertNodes = []
		for line in connections:
			# generate a list of names for all inbetween node names
			nodeName = '%s_%s_%s' % (line[1].nodeName(), self.typeDict.get(nodeType, nodeType), line[1].attrName())
			print nodeName
			node = createNode(nodeType, n=nodeName)
			insertNodes.append(node)
			
			if self.dev: 
				print '%s >> %s >> %s' % (line[0], node.nodeName(), line[1])

		# duplicate history
		self.addToHistory(force=True, updateIndex=False)


		# Compose lists
		# sourceList = 	deepcopy(self.itemLists[self.hIndex])
		destList = 		deepcopy(self.itemLists[self.hIndex][3])
		print 'destList:'
		print destList

		self.itemLists[self.hIndex]

		self.removeAllItems(1)
		self.removeAllItems(3)
		
		self.removeAllItems(0, histIndex = self.hIndex+1)
		self.removeAllItems(2, histIndex = self.hIndex+1)

		# Put insert nodes empty spots on both lists
		self.itemLists[self.hIndex][1].extend(insertNodes) 

		self.itemLists[self.hIndex+1][0].extend(insertNodes) # B Source Nodes

		# Reload ui
		self.updateLists()
		self.sequence = True
		self.updateHistUI()

	def createNodes(self, nodeType):
		if self.dev: print '\ncreateNodes'
		pass
		# insertNodes = []
		# for node in inputList:
		# 	# generate a list of names for all inbetween node names
		# 	nodeName = '%s_%s_%s' % (line[1].nodeName(), self.typeDict.get(nodeType, nodeType), line[1].attrName())
		# 	print nodeName
		# 	node = createNode(nodeType, n=nodeName)
		# 	insertNodes.append(node)
	# -------------------
	# TODO

	def cbShowAll(self):
		# Temporarily makes all attributes that can keyable keyable, so that they can be seen in channelBox.  Automatically rehides them at next selection.
		
		# To make sure this doesn't get pressed twice
		if self.unhiddenAttributes:
			self.cbRehide()

		else:
			selection = ls(sl=1)
			node = selection[-1]

			# For each node on last selected, 
			for attribute in listAttr(node):
				# try:
				attribute = node.attr(attribute)
				# Check if hidden
				if not attribute.isInChannelBox():
					# Check if compound
					if not attribute.isCompound():
						node.attr(attribute).setKeyable(True)
						self.unhiddenAttributes.append(node.attr(attribute))
				# except:
				# 	pass

			self.cbShowAllJobName = scriptJob(
			event=['SelectionChanged', Callback(self.cbRehide)],
			runOnce = True,
			killWithScene = True)


	def cbRehide(self):
		print self.unhiddenAttributes
		print bool(self.unhiddenAttributes)

		rehiddenAttributes = []
		if self.unhiddenAttributes:
			for attribute in self.unhiddenAttributes:
				if self.dev: print attribute
				attribute.setKeyable(False)
				rehiddenAttributes.append(attribute)
		
		if rehiddenAttributes:
			for attribute in rehiddenAttributes:
				if attribute in self.unhiddenAttributes:
					self.unhiddenAttributes.remove(attribute)
				
		if self.unhiddenAttributes:
			warning('One or more attributes could not be rehidden: %s' % self.unhiddenAttributes)


	def cbSaveSel(self):
		# Takes attributes selected in channelbox and makes them keyable for all selected objects.  Then removes attribute from cbShowAll's 'Rehide list' to prevent it from getting overwritten
		for node in ls(sl=1):
			for attrLN in getFromChannelBox():
				attribute = node.attr(attrLN)
				attribute.setKeyable()
				if attribute in self.unhiddenAttributes:
					self.unhiddenAttributes.remove(attribute)

	# -------------------

	def connect(self):

		if self.dev: print 'connect'
		connections = self.getConnectionPattern()


		if self.dev: 
			for line in connections:
				print '%s >> %s' % (line[0], line[1])


		warnList = []
		for conn in connections:
			# Check if locked
			locked = []
			for c in conn:
				if c.isLocked():
					locked.append(True)
					c.set(l=False)
				else:
					locked.append(False)
			# Check if already connected
			if not isConnected(conn[0], conn[1]):
				connectAttr(conn[0], conn[1], f=1)


			for i, c in enumerate(conn):
				if locked[i]:
					c.set(l=1)


		if len(warnList):
			for warn in warnList:
				warning('Attributes could not be connected: %s >> %s' % (warn[0], warn[1]))
		else:

			if self.sequence and self.hIndex < len(self.itemLists)-1:
				# If insertNodes in effect, after making this connection, move history forward to facilitate output connection.
				self.histForward()
				self.sequence = False
				self.updateHistUI()
			else:
				self.addToHistory()


	def transferInputs(self, nodesOnly=False):
		if self.dev: print '\ntransfer inputs'
			
		connections = self.getConnectionPattern()
		
		if self.dev: 
			for line in connections:
				print '>%s >> >%s' % (line[0], line[1])
		

		warnList = []
		for conn in connections:
			# Check if locked
			locked = []
			# Include inputs!
			for c in conn:
				if c.isLocked():
					locked.append(True)
					c.set(l=False)
				else:
					locked.append(False)
			
			# Check if already connected
			inputs = conn[0].inputs(p=1)
			if inputs:
				if not isConnected(inputs[0], conn[1]):
					disconnectAttr(inputs[0], conn[0])
					connectAttr(inputs[0], conn[1], f=1)

			# except:
			# 	warnList.append([inputs[0], conn[1]])

			# finally:
			# 	for i, c in enumerate(conn):
			# 		if locked[i]:
			# 			l.set(l=1)


		if len(warnList):
			for warn in warnList:
				warning('Attributes could not be connected: %s >> %s' % (warn[0], warn[1]))


	def transferOutputs(self):
		if self.dev: print '\nTransfer outputs'
		connections = self.getConnectionPattern()

		if self.dev: 
			for line in connections:
				print '%s> >> %s>' % (line[0], line[1])
		
		warnList = []
		for conn in connections:
			# Include outputs!
			# Check if locked
			locked = []
			for c in conn:
				if c.isLocked():
					locked.append(True)
					c.set(l=False)
				else:
					locked.append(False)
			
			# Check if already connected
			outputs = conn[0].outputs(p=1)
			if outputs:
				for output in outputs:
					if not isConnected(conn[1], output):
						disconnectAttr(conn[0], output)
						connectAttr(conn[1], output, f=1)

			# except:
			# 	warnList.append([inputs[0], conn[1]])

			# finally:
			# 	for i, c in enumerate(conn):
			# 		if locked[i]:
			# 			l.set(l=1)


		if len(warnList):
			for warn in warnList:
				warning('Attributes could not be connected: %s >> %s' % (warn[0], warn[1]))

	def castNodes(self):
		if self.dev: print '\nCast Nodes'
		# For each connection, do a matrixConstraint based on inputs.
		# t = translate
		# r = rotate
		# s = scale
		# All will except 3-item tuples of bools (for just rx, etc)

		connections = self.getConnectionPattern(attributes=False)
		warnList = []

		for conn in connections:
			locked = []
			# try:
			for c in conn:
				# 
				for i, attribute in enumerate(listAttr(c, locked=True)):
					locked.append(c.attr(attribute))
					c.attr(attribute).set(l=0)

			nodeCast(conn[0], conn[1], copyDynamicAttrs=True)
			# except:
			# 	warnList.append([conn[0], conn[1]])

			# finally:
			for l in locked:
				l.set(l=1)


		if len(warnList):
			for warn in warnList:
				warning('Nodes could not be cast: %s >> %s' % (warn[0], warn[1]))

		self.selectAllItemsInList(listIndex=1)



	def constrainLists(self, t=True, r=True, s=True, force=False):
		if self.dev: print '\nConstrain Lists'
		# For each connection, do a matrixConstraint based on inputs.
		# t = translate
		# r = rotate
		# s = scale
		# All will except 3-item tuples of bools (for just rx, etc)

		constrainAttrs = [] # List of all 9 bools (for t,r,s)
		attributeCheck = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
		for i, channel in enumerate([t, r, s]):
			if isinstance(channel, list) or isinstance(channel, tuple):
				if not len(channel) == 3:
					raise Exception( '3 Inputs required for tuple to be considered valid: %s (%s inputs found)' % (['Translate', 'Rotate', 'Scale'][i], len(channel)) )
				# If t=(True, False, True), append (True, False, True) to bool list
				constrainAttrs.extend(channel)
			else:
				# If t=True, append (True, True, True) to boolList
				constrainAttrs.extend([channel, channel, channel])


		connections = self.getConnectionPattern(attributes=False)
		warnList = []

		for conn in connections:
			# Check if locked
			locked = []
			for c in conn:
				for i, attribute in enumerate(attributeCheck):
					if constrainAttrs[i]:
						if c.attr(attribute).get(l=1):
							locked.append(c.attr(attribute))
							c.attr(attribute).set(l=0)

			
			# try:
			fromCB = False
			cbSel = self.getFromChannelBox()
			transformAttrs = [ 'translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ' ]
			
			transformInputs = []
			if cbSel:
				fromCB = True
				for cbAttr in cbSel:
					print cbAttr
					# Check if there are any attributes selected that are not transform attributes. If so, just do a regular constraint
					if cbAttr not in transformAttrs:
						fromCB = False

			if fromCB:
				boolCheckList = []
				for i in range(9):
					if transformAttrs[i] in cbSel:
						boolCheckList.append(True)
					else:
						boolCheckList.append(False)

				transformTranslate =	boolCheckList[0:3]
				transformRotate = 		boolCheckList[3:6]
				transformScale = 		boolCheckList[6:9]

				utils.matrixConstraint(conn[0], conn[1], t=transformTranslate, r=transformRotate, s=transformScale, offset=1)
				
			else:
				utils.matrixConstraint(conn[0], conn[1], t=t, r=r, s=s, offset=1)


			# finally:
			for l in locked:
				l.set(l=1)


		if len(warnList):
			for warn in warnList:
				warning('Nodes could not be constrained: %s >> %s' % (warn[0], warn[1]))

		self.selectAllItemsInList(listIndex=1)


	def parentLists(self):
		if self.dev: print '\nParent Lists'
		connections = self.getConnectionPattern(attributes=False)

		warnList = []
		attributeCheck = [ 'tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz' ]
		for conn in connections:

			# Check if locked
			locked = []
			for c in conn:
				for attribute in attributeCheck:
					if c.attr(attribute).get(l=1):
						locked.append(c.attr(attribute))
						c.attr(attribute).set(l=0)

			# Check if already parented, etc
			try:
				parent(conn[1], conn[0])
			except:
				warnList.append(conn)

			finally:
				for l in locked:
					l.set(l=1)

		if len(warnList):
			for warn in warnList:
				warning('Nodes could not be parented: %s >> %s' % (warn[1], warn[0]))


	def getConnectionPattern(self, nodes=True, attributes=True):
		'''Deduces a connection solution based on the length of each list. By default, returns a list Pynode Attribute instances for that solution:
		return = [
		[sourceNode.sourceAttribute, destinationNode1.destinationAttribute],
		[sourceNode.sourceAttribute, destinationNode2.destinationAttribute]
		]
		If only nodes specified, will return a list of pyNode instances.
		If only attributes specified, will return a list of strings.

		If there are empty lists, script will attempt to fill in empty lists with node/cb attribute selection, logically based on which lists are empty
		'''

		# Check variable inputs
		if not any([nodes, attributes]):
			raise Exception('Check for either nodes or attributes or both.')
		
		itemLists = deepcopy(self.itemLists[self.hIndex])

		selection = ls(sl=1)
		cbSelection = self.getFromChannelBox()

		# Possible Matching Applications:
		oneToAllNode = False
		oneToOneNode = False
		oneToAllAttr = False
		oneToOneAttr = False
		sourceAttrToDestNode = False
		sourceNodeToDestAttr = False

		# Variable(empty list) applications:
		varNodes = False
		varAttrs = False
		varSrc = False
		varDest = False
		varSN = not bool(len(itemLists[0]))
		varDN = not bool(len(itemLists[1]))
		varSA = not bool(len(itemLists[2]))
		varDA = not bool(len(itemLists[3]))
		listEmpty = [varSN, varDN, varSA, varDA]

		varCross = False

		if all(listEmpty):
			raise Exception('Not enough information in input fields')

		if all([nodes, attributes]):
			# If any are empty
			if any(listEmpty):
				
				# Check for 3 or more empty lists
				numEmptyLists =(int(listEmpty[0]) + int(listEmpty[1]) + int(listEmpty[2]) + int(listEmpty[3]))
				

				if numEmptyLists >= 3 :
					raise Exception('Not enough information in input fields')

				elif numEmptyLists == 2:
					# Both Node lists empty
					if all(listEmpty[0:2]):
						if self.dev: print 'Variable Nodes'
						varNodes=True

					# Both attribute lists empty
					if all(listEmpty[2:4]):
						if self.dev: print 'Variable Attributes'
						varAttrs=True

					# Both source lists empty
					if all([listEmpty[0], listEmpty[2]]):
						if self.dev: print 'Variable Source'
						varSrc=True

					# Both destination lists empty
					if all([listEmpty[1], listEmpty[3]]):
						if self.dev: print 'Variable Destination'
						varDest=True

					# Possible Errors
					if all([listEmpty[0], listEmpty[3]]):
						if self.dev: print 'Variable cross (down)'
						raise Exception('Not enough information in input fields')
						varCross=True
					if all([listEmpty[1], listEmpty[2]]):
						if self.dev: print 'Variable cross (up)'
						raise Exception('Not enough information in input fields')
						varCross=True

				elif numEmptyLists == 1:
					for empt in listEmpty:
						if empt is True:
							varSingle = listEmpty.index(empt)
							if self.dev: print 'Variable Single: [%s]' % varSingle
							break
		
		# If running a command that uses only nodes
		elif nodes:
			if self.dev: print listEmpty[0:2]
			if any(listEmpty[0:2]):
				for empt in listEmpty[0:2]:
						if empt is True:
							varSingle = listEmpty.index(empt)

		# Fill in empty lists with selection
		if varNodes:
			if len(selection):
				itemLists[0].extend([selection[0]])
				itemLists[1].extend(selection[1:])

				# srcNodes = [selection[0]]
				# destNodes = selection[1:]

		elif varAttrs:
			if len(cbSelection):
				itemLists[2].extend([cbSelection[0]])
				itemLists[3].extend(cbSelection[1:])

				# srcAttrs = [cbSelection[0]]
				# destAttrs = cbSelection[1:]

		elif varSrc:
			if len(selection) and len(cbSelection):
				itemLists[0].extend(selection)
				itemLists[2].extend(cbSelection)

				# srcNodes = selection
				# srcAttrs = cbSelection
		elif varDest:
			if len(selection) and len(cbSelection):
				itemLists[1].extend(selection)
				itemLists[3].extend(cbSelection)

				# destNodes = selection
				# destAttrs = cbSelection

		elif varSN:
			if len(selection):
				itemLists[0].extend(selection)

		elif varDN:
			if len(selection):
				itemLists[1].extend(selection)

		elif varSA:
			if len(cbSelection):
				itemLists[2].extend(cbSelection)

		elif varDA:
			if len(cbSelection):
				itemLists[3].extend(cbSelection)
				
		# TODO
		listSizes = [len(itemList) for itemList in itemLists]
		# ================== Guess which connection to use =================
		
		# Flipped lists
		if listSizes[1] == listSizes[2] and listSizes[0] == 1 and listSizes[3] == 1:
			if self.dev: print 'Source Attributes to Dest Nodes'
			sourceAttrToDestNode = True

		elif listSizes[0] == listSizes[3] and listSizes[1] == 1 and listSizes[2] == 1:
			if self.dev: print 'Source Nodes to Dest Attributes'
			sourceNodeToDestAttr = True


		# Split by type (Nodes and AttDibutes)
		# if not any([sourceAttrToDestNode, sourceNodeToDestAttr]):
		else:
			for i, listSize in enumerate([listSizes[0:2], listSizes[2:4]]):
				listString = ['Nodes', 'Attributes'][i]

				# oneToAll
				if listSize[0] == 1 and listSize[1] > 1:
					if i:
						if self.dev: print 'One To All Attributes'
						oneToAllAttr = True
					else:
						if self.dev: print 'One To All Nodes'
						oneToAllNode = True

				# oneToOne
				if listSize[0] == listSize[1]:
					if i:
						if self.dev: print 'One To One Attributes'
						oneToOneAttr = True
					else:
						if self.dev: print 'One To One Nodes'
						oneToOneNode = True



		# ================== Return connection list based on guess =================
		nodeList = []
		# One to All
		if oneToAllNode:
			for sn in itemLists[0]:
				for dn in itemLists[1]:
					nodeList.append([sn, dn])
		# One to One
		elif oneToOneNode:
			for sn, dn in zip(itemLists[0], itemLists[1]):
				nodeList.append([sn, dn])


		attributeList = []
		if oneToAllAttr:
			for sa in itemLists[2]:
				for da in itemLists[3]:
					attributeList.append([sa, da])
		# One to One
		elif oneToOneAttr:
			for sa, da in zip(itemLists[2], itemLists[3]):
				attributeList.append([sa, da])

		# Source attribute dest nodes flip
		if sourceAttrToDestNode:
			for sa, dn in zip(itemLists[2], itemLists[1]):
				for sn, da in zip(itemLists[0], itemLists[3]):
					nodeList.append([sn, dn])
					attributeList.append([sa, da])

		# Source nodes Dest attributes flip
		if sourceNodeToDestAttr:
			for sn, da in zip(itemLists[0], itemLists[3]):
				for sa, dn in zip(itemLists[2], itemLists[1]):
					nodeList.append([sn, dn])
					attributeList.append([sa, da])


		if nodes and attributes:
			connectionsList = []
			if not any([sourceAttrToDestNode, sourceNodeToDestAttr]):
				for nodes in nodeList:
					for attributes in attributeList:
						connectionsList.append(self.testConnections( [nodes[0], attributes[0], nodes[1], attributes[1]] ) )
			else:
				for nodes, attributes in zip(nodeList, attributeList):
					connectionsList.append(self.testConnections( [nodes[0], attributes[0], nodes[1], attributes[1]] ) )

			ret = connectionsList



		elif nodes:
			ret = nodeList
			if self.dev:
				print 'Only Nodes'


		elif attributes:
			ret = attributeList
			if self.dev:
				print 'Only attributes'
		else:
			ret = None


		if not len(ret):
			warning('Connection pattern could not be determined.')

		return ret


	def testConnections(self, connectionData):

		sn, sa, dn, da = connectionData
		

		if not sn.exists():
			raise Exception('Source Node not found: %s' % sn)
			
		if not hasAttr(sn, sa):
			raise Exception('Source Attribute not found: %s.%s' % (sn,sa))
			
		if not dn.exists():
			raise Exception('Destination Node not found: %s' % dn)

		if not hasAttr(dn, da):
			raise Exception('Destination Attribute not found: %s.%s' % (dn,da))


		return [sn.attr(sa), dn.attr(da)]



	# ------------------- Channelbox Manipulation  --------------------
	def selectCBInputs(self, selection=None):
		newSelList = []
		with UndoChunk():
			if selection is None:
				selection = ls(sl=1)
			if not isinstance(selection, list):
				selection = [selection]

			cbList = self.getFromChannelBox()
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

	def selectCBOutputs(self, selection=None):
		newSelList = []
		with UndoChunk():
			if selection is None:
				selection = ls(sl=1)
			if not isinstance(selection, list):
				selection = [selection]

			cbList = self.getFromChannelBox()
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



	# ------------------- History Mangement  --------------------
	
	def addToHistory(self, new=False, force=False, copy=True, updateIndex=True):
		'''
		Copies the current active layout and adds it to the command history if it's not already in there
		new: Adds an empty layout to history and sets to that index
		force: Adds whether or not a duplicate is found
		'''
		if self.dev: print '\naddToHistory'

		# TODO
		# Check to see if lists contain contents.
		# Remove this later, and replace so that only triggers on successful connection.
		# if len(self.history[self.hIndex][0]) or len(self.history[self.hIndex][1]) or len(self.history[self.hIndex][2]) or len(self.history[self.hIndex][3]):
		
		
		# if self.history[self.hIndex] == self.history[self.hIndex-1]:
		
		if new:
			# Append empty list to end and set index there
			self.itemLists.append([[],[],[],[]])
			self.hIndex = (len(self.itemLists)-1)

		else:
			add = True # Test conditions. If false, do not add.
			if not force:
				# skip copy if not enough items to test
				if len(self.itemLists) > 1:
					# Create a copy of lists with current list removed, then check to see if there
					# are any matching lists.  Skip copy if there are.
					try:
						testLists = deepcopy(self.itemLists[self.hIndex])
						testLists.remove(testLists[self.hIndex])
						for itemList in testLists:
							if self.itemLists[self.hIndex] == itemList:
								add = False
								warning('Not added. Current state matches previous state.')
								break
					except:
						# warning('Not added. Error detected.')
						pass

			if add:
				# Copy a new version of the current list and add it to the end of the history lineup
				self.itemLists.append( deepcopy(self.itemLists[self.hIndex]) )
				# Switch to last item in history?
				if updateIndex:
					self.hIndex = (len(self.itemLists)-1)

		self.updateHistUI()
		self.updateLists()

	def histBack(self):
		if self.dev: print '\nhistBack'

		if self.hIndex > 0:
			self.hIndex = self.hIndex-1

		self.updateHistUI()
		self.updateLists()

	def histForward(self):
		if self.dev: print '\nhistForward'

		# self.addToHistory()
		if len(self.itemLists) > self.hIndex:
			self.hIndex = self.hIndex + 1

		self.updateHistUI()
		self.updateLists()
	
	def loadHistory(self, i):
		if self.dev: print '\nloadHistory'
		self.hIndex = i
		self.updateHistUI()
		self.updateLists()
	
	def updateHistUI(self):
		if self.dev: print '\nupdateHistUI'


		# =================== UI Update ==================
		# Update History UI (buttons and hist counter)
		# History Counter Text (Top Left)
		self.histCounter.setLabel('%s' % (self.hIndex))

		# History << / >> buttons
		self.histBackButton.setEnable(0)
		self.histForwardButton.setEnable(0)
		# If there are history items to the left
		# If 2 history items and index is set to -1, disable
		if len(self.itemLists) > ((self.hIndex+1)):
			self.histForwardButton.setEnable(1)

		if self.hIndex > 0:
			self.histBackButton.setEnable(1)

		# If we're at front of list and there's info in field, use forward button as a save/new feature
		if self.hIndex == (len(self.itemLists)+1):
			for itemList in self.itemLists[self.hIndex]:
				if len(itemList):
					# self.histBackButton.setEnable(1)
					self.histForwardButton.setEnable(1)


		# Clear old
		for uiItem in self.historyButtons:
			deleteUI(uiItem)



		# For each list in history, add button object to list, then reverse order and align right
		self.historyButtons = []
		if len(self.itemLists) > 10:
			self.historyButtons.append(
				iconTextButton(
				style = 'textOnly',
				l='...',
				# image = icon,
				c = Callback(self.loadHistory, 0),
				p = self.histButtons
				)
			)

		for i, h in enumerate(self.itemLists):
			if self.dev: print h
			inNodes, outNodes, inAttrs, outAttrs = h

			empties = [
				not bool(len(inNodes)),
				not bool(len(outNodes)),
				not bool(len(inAttrs)),
				not bool(len(outAttrs))
			]
			
			bgc = (0.2,0.2,0.2)
			icon = 'hsNothing.png'

			if i <= 10:
				self.historyButtons.append(
					iconTextButton(
					style = 'iconOnly',
					# l=i,
					image = icon,
					# bgc = (0.4,0.4,0.4),
					c = Callback(self.loadHistory, i),
					p = self.histButtons
					)
				)
			else:
				break


				

		

		# Initialize layout
		self.stackHorizontalLayout(self.histButtons)
		
		# # Attach settings button to left side
		# self.histCounterView.attachForm(self.settingsButton, 'left', 5)
		# self.histCounterView.attachNone(self.settingsButton, 'right')
		# # Attach counter to right side
		# self.histCounterView.attachForm(self.histCounter, 'right', 10)
		# self.histCounterView.attachNone(self.histCounter, 'left')
		

		# Attach all buttons to counter view
		self.historyButtonsReversed = self.historyButtons[::-1]
		
		for i, histButton in enumerate(self.historyButtonsReversed):
			if i==0:
				self.histButtons.attachForm(histButton, 'right', 1)
			else:
				self.histButtons.attachControl(histButton, 'right', 1, self.historyButtonsReversed[i-1])
			self.histButtons.attachNone(histButton, 'left')

		if self.hIndex <= 10:
			self.historyButtons[self.hIndex].setBackgroundColor(bgc)
		else:
			self.historyButtons[10].setBackgroundColor(bgc)


		
	
	# -------------------- TextList Construction --------------------


	def updateLists(self, devPrint=True):
		'''Updates textScrollList ui with python lists
		pymel.PyNode("name")
		'''
		if self.dev: print '\nupdateLists'


		# =================== Print Info ==================
		if self.dev:
			if devPrint:
				for i, h in enumerate(self.itemLists):
					print i
					for itemList in h:
						print itemList


		# =================== Check Data ==================
		# for i, il in enumerate(self.history[self.hIndex]):
		# 	if i < 2:
		# 		for node in il:
		# 			if not node.exists():
		# 				warning('Node no longer exists: %s' % node)
		# 				il.remove(node)
		# self.checkExists()


		# For each list, empty and replace ui contents with class info, then reselect items in previous selection
		# from inner list
		# [ [],[],[],[] ]
		for tl, il in zip(self.textLists, self.itemLists[self.hIndex]):
			selection = tl.getSelectItem()
			tl.removeAll()
			tl.append(il)
				

			# Check python instance type to warn me whenever incorrect nodeTypes are entered
			# Doesnt work for some reason
			# TODO
			# if self.textLists.index(tl) < 2: # Node lists
			# 	if not isinstance(il[index], pymel.core.nodetypes.DagNode):
			# 		raise Exception('Object not of correct instance type: %s, DagNode' % il )
			# if index >= 2: #Attribute Lists
			# 	if not isinstance(il[index], str):
			# 		raise Exception('Object not of correct instance type: %s, String' % il )
			# Reselect previous selection
			
			# self.sequence = False

			for sel in selection:
				if sel in tl.getAllItems():
					tl.setSelectItem(sel)

	def checkExists(self):
		if self.dev: print '\ncheckExists'
		'''Determines whether nodes in node lists still exist in scene (In case deleted)
		'''
		# =================== Check Data ==================
		for h in range(len(self.itemLists)):
			for i, il in enumerate(self.itemLists[h][0:2]):
				for node in il:
					if not node == self.AC_divider:
						if isinstance(node, PyNode):
							try:
								node.nodeName()
							except:
								warning('Node no longer exists: %s' % node)
								il.remove(node)
						else:
							raise Exception('Item in list is not a pyNode instance: %s' % node)
				
	def addItems(self, listIndex, items=None):
		if self.dev: print '\naddItems'
		# Click 'Add' Button

		# Get current ui list and current list selection to determine placement
		textList = self.textLists[listIndex]
		selIndex = self.getSelectedListItemsIndex(listIndex)
		selItems = self.getSelectedListItems(listIndex)
		
		# Assign current data list
		# itemList = self.history[self.hIndex][listIndex]

		selection = ls(sl=1)
		warnList = []
		items = []

		# TODO
		# Mouse-drag attributes to a textlist?

		# If populating node list, use either autoComplete or node selection
		selectedAC = self.getSelectedInAutoComplete()
		
		if listIndex <= 1:

			if selectedAC and self.writeInMode == 'nodes':
				items = selectedAC

			else:
				items = selection


		# If populating attributes list, use autoComplete OR channel selection
		else:
			if selectedAC and self.writeInMode == 'attributes':
					items = selectedAC

			elif self.writeIn.getText():
				writeInText = self.writeIn.getText()

				# Replace with integer value automatically when adding from the writein
				if '#' in writeInText:
					i = 0
					newWriteInText = writeInText.replace('#', '%s' % i)
					
					while newWriteInText in textList.getAllItems():
						newWriteInText = writeInText.replace('#', '%s' % i)
						i = i + 1
						if i == 1000:
							raise Exception('Code cycle detected')

					writeInText = newWriteInText

				items = [writeInText]

			else:
				items = self.getFromChannelBox()

		# If list is empty
		if not items:
			if listIndex <= 1:
				raise Exception('No nodes selected.')
			else:
				raise Exception('No attributes selected.')

		# Test each item
		newItemsList = []
		warnList = []
		for item in items:
			if item not in self.itemLists[self.hIndex][listIndex]:
				newItemsList.append(item)
			else:
				warnList.append(item)

		items = newItemsList
		

		if selIndex:
			# place new items above selected item
			for item in items:
				self.itemLists[self.hIndex][listIndex].insert(selIndex[0], item)
				selIndex[0] = selIndex[0]+1
		else:
			for item in items:
				self.itemLists[self.hIndex][listIndex].append(item)

		self.updateLists()

		if len(warnList):
			warning('Object(s) already in list: %s' % warnList)
		


		select(selection)

	def addNodesAndAttributes(self, listIndex):
		if self.dev: print '\naddNodesAndAttributes'
		
		# Attribute section: Double-click 'Add'
		# Adds selected nodes AND attributes to column
		# Try/Except block to prevent attribute non-selection error
		if listIndex > 1:
			try:
				self.addItems(listIndex)
			except:
				pass
			try:
				self.addItems(listIndex-2)
			except:
				pass
		if listIndex <= 1:
			try:
				self.addItems(listIndex)
			except:
				pass
			try:
				self.addItems(listIndex+2)
			except:
				pass

	# --------------------TextList Deconstruction--------------------
	
	def clearWindow(self):
		if self.dev: print '\nclearWindow'
		# textLists = self.itemLists[self.hIndex]
		for il in self.itemLists[self.hIndex]:
			del il[:]
		self.updateLists()
		self.updateHistUI()


	def deleteSave(self):
		if self.dev: print '\ndeleteSave'
		# self.itemLists.remove(self.itemLists[self.hIndex])
		if len(self.itemLists) > 1:
			self.itemLists.pop(self.hIndex)
			self.updateLists()
			self.updateHistUI()
		else:
			self.clearWindow()
		
	def removeItems(self, listIndex):
		if self.dev: print '\nremoveItems'
		# Click 'Remove' button
		textList = self.textLists[listIndex]
		itemList = self.itemLists[self.hIndex][listIndex]
		selIndex = self.convertIndex(textList.getSelectIndexedItem())
		removed = []
		if selIndex:
			# Reverse direction so indcies don't change each iteration
			selIndex.reverse()
			for index in selIndex:
				removed.append(itemList[index])
				itemList.remove(itemList[index])
		else:
			warning('No items in list selected.')
			textList.setSelectItem()
		if self.dev: print 'Removed items: %s' % removed
		self.updateLists()

	def removeAllItems(self, listIndex, histIndex=None):
		if self.dev: print '\nremoveAllItems'
		if histIndex is None:
			histIndex = self.hIndex
		# Double-click 'Remove' button
		del self.itemLists[histIndex][listIndex][:]
		self.updateLists()


	# --------------------TextList Selection--------------------
	
	def itemSelect(self, listIndex):
		pass

	def selectItemInList(self, listIndex):
		if self.dev: print '\nselectItemInList'
		# Double-click textScrollList item
		textList = self.textLists[listIndex]
		if listIndex < 4:
			itemList = self.itemLists[self.hIndex][listIndex]
		
			if listIndex == 0 or listIndex == 1:
				selIndex = self.convertIndex(textList.getSelectIndexedItem())
				if self.dev: print type(itemList[selIndex[0]])
				select(itemList[selIndex[0]])
			if listIndex == 2 or listIndex == 3:
				self.writeIn.setText(textList.getSelectItem()[-1])
				self.autoComplete()

			self.updateLists()

		
		else:
			itemList = self.autoCompleteList
			selIndex = self.convertIndex(textList.getSelectIndexedItem())

			if self.dev: print type(itemList[selIndex[0]])
			select(itemList[selIndex[0]])

	def selectAllItemsInList(self, listIndex):
		# Double-click 'Add' button
		if self.dev: print '\nselectAllItemsInList'
		itemList = self.itemLists[self.hIndex][listIndex]
		textList = self.textLists[listIndex]
		if len(itemList):
			select(itemList, r=1)

		textList.selectAll()

	# --------------------TextList Reordering--------------------
	
	def moveUp(self, listIndex):
		'''Move items selected in list up one position.'''

		if self.dev: print '\nmoveUp'
		itemList = self.itemLists[self.hIndex][listIndex]
		textList = self.textLists[listIndex]

		uiSelection = textList.getSelectItem()
		selIndex = self.getSelectedListItemsIndex(listIndex)
		
		xTop=0
		for x in selIndex:
			try:
				# x = itemList.index(i)
				# Lower ceiling to prevent flipping values at top
				if x == xTop:
					xTop = xTop+1
					continue
				itemList[x-1], itemList[x] = itemList[x], itemList[x-1]
			except IndexError:
				continue

		self.updateLists()
		textList.setSelectItem(uiSelection)

	def moveDown(self, listIndex):
		'''Move items selected in down up one position.'''
		if self.dev: print '\nmoveDown'
		itemList = self.itemLists[self.hIndex][listIndex]
		textList = self.textLists[listIndex]
		uiSelection = textList.getSelectItem()

		selIndex = self.getSelectedListItemsIndex(listIndex)
		selIndex.reverse()

		xBot = len(selIndex)+1
		for x in selIndex:
			try:
				itemList[x+1], itemList[x] = itemList[x], itemList[x+1]
			except IndexError:
				continue

		self.updateLists()
		textList.setSelectItem(uiSelection)

	def moveToTop(self, listIndex):
		if self.dev: print '\nmoveToTop'
		itemList = self.itemLists[self.hIndex][listIndex]
		textList = self.textLists[listIndex]

		uiSelection = textList.getSelectItem()
		itemSel = self.getSelectedListItems(listIndex)
		# selIndex = self.getSelectedListItemsIndex(listIndex)

		topIndex = 0
		for i in itemSel:
			itemList.remove(i)
			itemList.insert(topIndex, i)
			topIndex = topIndex+1

		self.updateLists()
		textList.setSelectItem(uiSelection)

	def moveToBot(self, listIndex):
		if self.dev: print '\nmoveToBot'
		itemList = self.itemLists[self.hIndex][listIndex]
		textList = self.textLists[listIndex]


		selItemsIndex = self.convertIndex(textList.getSelectIndexedItem())
		selItems = textList.getSelectItem()
		pyItems = []
		for i in selItemsIndex:
			pyItems.append(itemList[i])
		for i in pyItems:
			itemList.remove(i)
			itemList.append(i)
		self.updateLists()
		textList.setSelectItem(selItems)
	
	def swap(self, listIndex):
		if self.dev: print '\nswap'

		# Get other listIndex
		if listIndex == 0 or listIndex == 2:
			otherListIndex = listIndex + 1  # Left to Right
		else:
			otherListIndex = listIndex - 1  # Right to Left

		itemLists = self.itemLists[self.hIndex]
		
		textList = self.textLists[listIndex]
		otherTextList = self.textLists[otherListIndex]
		itemList = itemLists[listIndex]
		otherItemList = itemLists[otherListIndex]

		# List of lookup indices
		indexList = self.convertIndex(textList.getSelectIndexedItem())
		otherIndexList = self.convertIndex(otherTextList.getSelectIndexedItem())

		if self.dev:
			print 'indexLists'

		# If there are objects in list selected
		if indexList or otherIndexList:
			if self.dev: print 'Selection Swap'
			# Retrieve class information from selection index
			pyItems = []
			otherPyItems = []

			for index in indexList:
				pyItems.append(itemList[index])

			for index in otherIndexList:
				otherPyItems.append(otherItemList[index])
			

			warnList = []
			# Check for problems
			for pyItem in pyItems:
				# If item already in other list
				if pyItem in otherItemList:
					# and not part of reverse swap
					if pyItem not in otherPyItems:
						warnList.append(pyItem)

			if warnList:
				raise Exception('Items already in destination list: %s' % warnList)


			warnList = []
			for pyItem in otherPyItems:
				if pyItem in itemList:
					if pyItem not in pyItems:
						warnList.append(pyItem)

			if warnList:
				raise Exception('Items already in source list: %s' % warnList)


			for pyItem in pyItems:
				itemList.remove(pyItem)
				otherItemList.append(pyItem)
			
			for pyItem in otherPyItems:
				otherItemList.remove(pyItem)
				itemList.append(pyItem)

		else:
			if self.dev: print 'Standard Swap'
			self.itemLists[self.hIndex][listIndex], self.itemLists[self.hIndex][otherListIndex] = list(otherItemList), list(itemList)


		self.updateLists()

	def copyList(self, listIndex):
		# TODO
		if self.dev: print '\ncopyList'
		if listIndex == 0 or listIndex == 2:
			otherListIndex = listIndex + 1  # Left to Right
		else:
			otherListIndex = listIndex - 1  # Right to Left
		
		itemList = self.itemLists[self.hIndex][listIndex]
		otherItemList = self.itemLists[self.hIndex][otherListIndex]

		selIndex = self.getSelectedListItemsIndex(listIndex)

		warnList = []
		for index in selIndex:
			if itemList[index] in otherItemList:
				warnList.append(itemList[index])
		if len(warnList):
			raise Exception('Item(s) already found in other list: %s' % warnList)

		for index in selIndex:
			otherItemList.append(itemList[index])
			itemList.remove(itemList[index])



	def getSelectedListItems(self, listIndex):
		if self.dev: print '\ngetSelectedListItems'
		
		textList = self.textLists[listIndex]
		itemList = self.itemLists[self.hIndex][listIndex]

		# List of lookup indices
		indexList = self.convertIndex(textList.getSelectIndexedItem())

		returnList = []

		for index in indexList:
			returnList.append(itemList[index])

		return returnList

	def getSelectedListItemsIndex(self, listIndex):
		if self.dev: print '\ngetSelectedListItemsIndex'
		
		textList = self.textLists[listIndex]
		itemList = self.itemLists[self.hIndex][listIndex]

		# List of lookup indices
		indexList = self.convertIndex(textList.getSelectIndexedItem())

		return indexList


	def sortList(self, listIndex, integerSort=False):
		if self.dev: print '\nsortList'
		textList = self.textLists[listIndex]
		selItems = textList.getSelectItem()
		if integerSort:
			# TODO

			# sortList = []
			# import re
			# for item in self.history[self.hIndex][listIndex]:
			# 	retItem = re.findall(r'\d+', str(item))
			# 	sortList.append(int(retItem[0]))
			# sortList.sort()
			unsortedList = self.itemLists[self.hIndex][listIndex]
			sortList = self.segregated_sort(self.to_int_where_possible(unsortedList))


			# self.history[self.hIndex][listIndex].sort(key=lambda x: float(x))
				
		else:
			self.itemLists[self.hIndex][listIndex].sort()
		self.updateLists()
		textList.setSelectItem(selItems)

	def reverseList(self, listIndex):
		if self.dev: print '\nreverseList'
		# Get selection to restore later, invert list direction, rebuild
		selItems = self.textLists[listIndex].getSelectItem()
		self.itemLists[self.hIndex][listIndex].reverse()
		self.updateLists()
		self.textLists[listIndex].setSelectItem(selItems)

	def segregatedSort(self, inputList):
		'''TODO
		'''
		types = [type(datum) for datum in inputList]
		sortedDataByType = {
			t: iter(sorted(filter(lambda datum: type(datum) == t, inputList)))
			for t in set(types)
		}
		return [next(sortedDataByType[t]) for t in types]

	def segregated_sort(self, input_list):
		"""Returns a sorted copy of the input list that maintains the same
		type of data at each index of the output as the type of data at that
		index in the input."""
		types = [type(datum) for datum in input_list]
		sorted_data_by_type = {
			t: iter(sorted(filter(lambda datum: type(datum) == t, input_list)))
			for t in set(types)
		}
		return [next(sorted_data_by_type[t]) for t in types]

	def to_int_where_possible(self, words):
		"""Returns a copy of the input list in which any word that can be
		an int is replaced with its int value."""
		def convert(word):
			try:
				return int(str(word))
			except ValueError:
				return word
		return [convert(word) for word in words]

	# --------------------TextList Extra Functions--------------------

	def getSelectedNodeType(self, listIndex):
		'''Will eventually select objects in list that do not share a type with selected list item
		'''
		# reload textLists to check for name change?

		if self.dev: print '\ngetSelectedNodeType'
		textList = self.textLists[listIndex]
		itemList = self.itemLists[self.hIndex][listIndex]

		indexList = textList.getSelectIndexedItem()
		indexList = self.convertIndex(indexList)

		checkTypes = []
		for i in indexList:
			itemType = itemList[i].nodeType()
			if not itemType in checkTypes:
				checkTypes.append(itemType)
		
		return checkTypes

	def getNodesNotOfType(self, types, listIndex):
		if self.dev: print '\ngetNodesNotOfType'
		# Listify
		if not isinstance(types, list):
			types = [types]
		textList = self.textLists[listIndex]
		itemList = self.itemLists[self.hIndex][listIndex]

		checkTypes = self.getSelectedNodeType(listIndex)
		
		# Select all objects in list
		textList.selectAll()
		for item in itemList:
			for checkType in checkTypes:
				if not objectType(item, isType=checkType):
					textListIndex = itemList.index(item)
					textList.deselectIndexedItem(textListIndex)

		return textList.selectedItems()

	# -------------------- AutoComplete --------------------
	
	def writeInInsert(self):
		if self.dev: print '\nwriteInInsert'
		cb = self.getFromChannelBox()
		if len(cb):
			self.writeIn.setText(cb[-1])
		self.autoComplete()

	def selectAllItemsInAutoCompleteList(self):
		if self.dev: print '\nselectAllItemsInAutoCompleteList'
		self.textLists[4].selectAll()

	def refreshAutoCompleteList(self):
		# Refresh ui list
		if self.dev: print '\nrefreshAutoCompleteList'
		limitLines = 0 # if 0, no limit

		self.autoCompleteList = self.defaultAutoCompleteList
		if self.autoSorted:
			self.autoCompleteList = self.sortedAutoCompleteList

		self.textLists[4].removeAll()
		if not len(self.autoCompleteList):
			self.textLists[4].setVisible(0)
		for i, attr in enumerate(self.autoCompleteList):
			self.textLists[4].setVisible(1)
			self.textLists[4].append(attr)
			if limitLines:
				if i >= limitLines:
					self.textLists[4].append('')
					self.textLists[4].append('...')
					break

		self.setResultListHeight()

	def autoComplete(self):
		'''Check write-in against currently selected node for attributes that match and apply them to
		a menu
		'''

		# Get current text
		text = self.writeIn.getText()
		# In case this has to change
		resList = self.textLists[4]


		nodes = []
		# Reset lists
		self.defaultAutoCompleteList = []
		self.sortedAutoCompleteList = []
		waitCursor( state=True )

		# If write-in field isn't empty
		if text:


			# auto complete mode (attributes or nodes)
			if self.writeInMode == 'attributes':

				# Combine selection, and nodeLists into a larger list
				# Construct a list of nodes to check.  (Selection, Src Node List, Dest Node List)
				nodes = []

				if self.searchSelected:
					nodes = ls(sl=1)

				else:
					for item in self.itemLists[self.hIndex][0]:
						if item not in nodes:
							nodes.append(item)

					for item in self.itemLists[self.hIndex][1]:
						if item not in nodes:
							nodes.append(item)


				if len(nodes):
					for node in nodes:
						# retrive list of attributes from nodes based on text
						attrList = listAttr(node, st=text, sn=self.useShortNames)
						
						# For ease of use, assume wildcards unless specific wildcard already specified
						if '*' not in text:
							searchListText = [
							'%s*' % text,
							# '*%s'  % text,
							# '*%s*' % text,
							]
							# For each list
							for i in range(len(searchListText)):
								# Retrieve lists
								searchList = listAttr(node, st=searchListText[i], sn=self.useShortNames)
								# If items found
								if len(searchList):

									prunedList = []
									for item in searchList:

										if item not in attrList:
											prunedList.append(item)

									if len(prunedList):
										searchList = prunedList
										# If there's any data in list so far, add a divider
										if len(attrList) > 0:
											attrList.append(self.AC_divider)

										attrList.extend(searchList)


						for att in attrList:
							if att not in self.defaultAutoCompleteList:
								self.defaultAutoCompleteList.append(att)


			elif self.writeInMode == 'nodes':
				nodeList = ls(text, recursive=True, objectsOnly=True)
				
				if '*' not in text:

					searchListText = [
					'%s*' % text,
					# '*%s'  % text,
					# '*%s*' % text,
					]

					for i in range(len(searchListText)):
						# Retrieve lists
						searchList = ls('%s' % searchListText[i], head=self.lsLimit, recursive=True, objectsOnly=True)

						if len(searchList):
							prunedList = []
							for item in searchList:
								if item not in nodeList:
									prunedList.append(item)

							if len(prunedList):
								searchList = prunedList
								# If there's any data in list so far, add a divider
								if len(nodeList) > 0:
									nodeList.append(self.AC_divider)

								nodeList.extend(searchList)

				print 'Nodes: %s' % len(nodeList)
				for node in nodeList:
					self.defaultAutoCompleteList.append(node)


		# TODO
		# sorted list
		self.sortedAutoCompleteList = sorted(self.defaultAutoCompleteList)

		self.refreshAutoCompleteList()

		waitCursor( state=False )
	
	def autoListSortToggle(self):
		if self.dev: print '\nautoListSortToggle'

		self.autoSorted = not self.autoSorted
		
		if self.autoSorted:
			menuItem(self.sortAutoCompleteMenu, e=1, l='Default')
		else:
			menuItem(self.sortAutoCompleteMenu, e=1, l='Alphabetize')

		self.refreshAutoCompleteList()
	
	def autoListTypeToggle(self):
		'''Switches between 'node' and 'attribute' mode for autocomplete list
		'''
		if self.dev: print '\nautoListTypeToggle'

		if self.writeInMode == 'nodes':
			self.writeInMode = 'attributes'
			menuItem(self.modeAutoCompleteMenu,
				e=True,
				l='Nodes Mode'
			)
			menuItem(self.unhideAutoCompleteMenu, e=1, en=1)
			menuItem(self.sortAutoCompleteMenu, e=1, en=1)
			menuItem(self.shortAutoCompleteMenu, e=1, en=1)
		else:
			self.writeInMode = 'nodes'
			menuItem(self.modeAutoCompleteMenu,
				e=True,
				l='Attributes Mode'
			)
			menuItem(self.unhideAutoCompleteMenu, e=1, en=0)
			menuItem(self.sortAutoCompleteMenu, e=1, en=0)
			menuItem(self.shortAutoCompleteMenu, e=1, en=0)


		self.autoComplete()

		# TODO
		# Update popup menu, etc

	def useShortNamesToggle(self):
		if self.dev: print '\nuseShortNamesToggle'

		self.useShortNames = not self.useShortNames
		if self.useShortNames:
			menuItem(self.shortAutoCompleteMenu, e=1, l='Use Long Names')
		else:
			menuItem(self.shortAutoCompleteMenu, e=1, l='Use Short Names')

		self.autoComplete()

	def searchSelectedToggle(self):
		if self.dev: print '\nsearchSelectedToggle'

		self.searchSelected = not self.searchSelected
		if self.useShortNames:
			menuItem(self.searchSelectedAutoCompleteMenu, e=1, l='Query Nodes Selected')
		else:
			menuItem(self.searchSelectedAutoCompleteMenu, e=1, l='Query Nodes In Lists')

		self.autoComplete()


	def clearWriteIn(self):
		self.writeIn.setText('')
		self.autoComplete()

	def toggleResultListExpanded(self):
		'''Toggles expansion of the autocomplete result list
		'''
		self.resultListExpanded = not self.resultListExpanded
		if self.resultListExpanded:
			self.resultListExpandButton.setBackgroundColor(self.frameColor)
		else:
			self.resultListExpandButton.setBackgroundColor((0.5,0.5,0.5))
		self.setResultListHeight()

	def setResultListHeight(self):
		height = 25
		if self.resultListExpanded:
			resNum = self.textLists[4].getNumberOfItems()
			# update textList height
			if resNum:
				self.textLists[4].setVisible(1)
				height = ((resNum+2)*14)
				# Height limit
				if self.resultListMaxHeight > 0:
					if height>self.resultListMaxHeight:
						height = self.resultListMaxHeight
		else:
			self.textLists[4].setVisible(0)
		
		self.textLists[4].setHeight(height)

	def unhideAttributeSelected(self):
		# If set to attributes, for each node selected, and for attributes selected in autocomplete list
		# that exist on node, set keyable to true (to view in cb)

		if self.dev: print '\nunhideAttributeSelected'
		
		print self.getSelectedInAutoComplete()
		attributes = self.getSelectedInAutoComplete()

		for node in ls(sl=1):
			for attribute in attributes:
				if hasAttr(node, attribute):
					node.attr(attribute).set(cb=1)


	# ======================================== UI Conversion Helpers ========================================
	
	def getFromChannelBox(self):
		# Pulls longName strings of all selected attributes in channelbox
		

		# Get selection to help determine attribute longName
		selection = ls(sl=1)

		# Store return list
		ret = []
		# Returns a list of strings, the names of all the selected attributes in the top section of the channel box.
		sma = channelBox(self.gChannelBox, q=1, sma=1)
		# Returns a list of strings, the names of all the selected attributes in the middle (shape) section of the channel box.
		ssa = channelBox(self.gChannelBox, q=1, ssa=1)
		# Returns a list of strings, the names of all the selected attributes in the INPUT section of the channel box.
		sha = channelBox(self.gChannelBox, q=1, sha=1)
		# Returns a list of strings, the names of all the selected attributes in the OUTPUT section of the channel box.
		soa = channelBox(self.gChannelBox, q=1, soa=1)
		
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
				strInputs = channelBox(self.gChannelBox, q=1, historyObjectList=1)
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
				strOutputs = channelBox(self.gChannelBox, q=1, outputObjectList=1)
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

	def convertIndex(self, selIndex):
		if self.dev: print '\nconvertIndex'
		indexRet = []
		if selIndex:
			for index in selIndex:
				indexRet.append(int(index-1))
		return indexRet

	def initializeScriptJobs(self):
		# UI parent not working

		if self.dev: print '\ninitializeScriptJobs'
		
		p = None
		if dockControl(self.dock, exists=True):
			p = self.dock
		if versions.current() > versions.v2017:
			if workspaceControl(self.workspace, exists=True):
				p = self.workspace
		if window(self.win, exists=True):
			p = self.win
		if p is None:
			raise Exception('No parent object found for scriptjob.')
		
		# p=self.dock if self.dockUI else self.win
		self.renameJobNum = scriptJob(
			event=['NameChanged', Callback(self.updateLists)],
			p=p)

		# self.checkExistsJobName = scriptJob(
		# 	event=['SelectionChanged', Callback(self.checkExists)],
		# 	killWithScene = False,
		# 	p=self.dockControl)



	def setInitialHeight(self):
		if self.dev: print '\nsetInitialHeight'
		self.pane.setPaneSize([1, 100, 70])
		self.overallPane.setPaneSize([1, 100, 60])

	# ======================================== UI Layout Commands ========================================

	def meetVerticalLayout(self, form, objects, midObject):
		# Get middle index
		# Unused
		if not len(objects) > 3:
			raise Exception('Not enough ui objects to preform meetVerticalLayout')

		index = objects.index(midObject)
		topObjects = []
		botObjects = []

		if self.dev: print '\nTop'
		for obj in objects[0:index]:
			topObjects.append(obj)
			if self.dev: print obj
		if self.dev: print 'Mid'
		if self.dev: print objects[index]
		if self.dev: print 'Bottom'
		for obj in objects[index+1:]:
			botObjects.append(obj)
			if self.dev: print obj

		# attach top to top
		form.attachForm(topObjects[0], 'top', 0)
		form.attachNone(topObjects[0], 'bottom')
		if len(topObjects) > 1:
			for i, obj in enumerate(topObjects):
				if i > 0: # skip 0
					
					form.attachControl(obj, 'top', 5, objects[i-1])
					form.attachNone(obj, 'bottom')

		# attach bottom to bottom
		form.attachForm(botObjects[-1], 'bottom', 0)
		form.attachNone(botObjects[-1], 'top')

		# if len(botObjects)>1:

		for i, obj in enumerate( botObjects ):
			# print obj
			if not obj is botObjects[-1]:
				objIndex = objects.index(obj)
				form.attachControl(obj, 'bottom', 5, objects[objIndex+1])
				form.attachNone(obj, 'top')

		# attach mid object
		form.attachControl(midObject, 'top', 5, objects[index-1])
		form.attachControl(midObject, 'bottom', 5, objects[index+1])

	def stackVerticalLayout(self, form, reverse=False):
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
					
	def stackHorizontalLayout(self, form, reverse=False):
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

	def resizeScroller(self):

		if window(self.win, exists=True):
			width=window(self.win, q=True, w=True)
			self.scrollStretch.setWidth(width-30)
		elif dockControl(self.dock, exists=True):
			width=dockControl(self.dock, q=True, w=True)
			self.scrollStretch.setWidth(width-30)
