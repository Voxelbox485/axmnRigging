from pymel.core import *
import utils as rb
import colorOverride as col
reload(col)
import buildRig
reload(buildRig)
import readers
reload(rb)




'''
ToDo:

orient lock foot

shaper node

Layered rigs:
	2 point IK --> 2 point bezier IK
	chain --> bezier chain
	3 point ik --> bezier 3 point ik

clean up poleVector socket group parenting

Vis category input (to global move)
Shoulder bias constraint
(and fix upper ik ctrl twist base)


Skinning:
	bonesel
	checks:
		negative weights
		maximum weight influences
		weight value(=0)
	automate ngskintools basic setup

standardize rignode color

Separate bind rig
	Preserve between rig builds
	fix scaling issue

Resize global move based on bounding box

Pole Vector Ik rig orientation should be between 'inherit' and 'Custom' (Initially oriented to world)


Rig Node classes
	Rig Node Global Scripts:
		Rebuild

		Output Socket Attributes UI
			for output in outputsList:

		Save to parent index attribute


		Selection Lists?

Bezier Option
Ik Scale:
	affect position onOff
	affect scale onOff
Distance based magnitude scaling

Space Switch UI?
Use same script to get space switch into Rig itself
	throw overall FK control into bezier rig (like 2 point IK)
	orient switch top and bottom FK ctrl of 3 point to world (default parent)

Have constraint world position locator be directly editable


Archive Fit Nodes:
	Enable fitNode attribute pasting
	Delete fit rig construction nodes and save as raw data

Pole vector
	scale inheritance to hand
	


Visualize rig parenting by connecting output world translation of parent to a switch, and porting that to indics
'''



# =================================================================================
class rigSetupUI:
	'''
	UI For utilizing fitSkeleton/fitRig class
	'''

	'''
	Vis:
		Fit
			Joints
			Controls
			Shapes
			Settings (Handles)
		Rig
			Controls
			Bind Joints
			Geometry
			Debug
	Skeleton
		Create Joint
			Joint tool
			Average-Selection Joint
			Per-Selection Joint
			Chain
			Remove
			Joint Size
		Mirror
			Passive (Mirror joints created)
			Manual
		Labels
			Remove Labels
			Add 
		Auto Orient All


	'''

	dev = 1
	# frameColor = 		[0.0, 0.3, 0.3]
	frameColor = 		[0.108, 0.519, 0.519]
	# frameColor = 		[1.000, 0.093, 0.554]
	# frameColor = 		[0.468, 0.406, 0.665]
	# frameColor = 		[0.468, 0.406, 0.665]
	# frameColor = 		[0.678, 0.608, 0.855]
	frameHeight = 		20

	buttonColor = 		[0.400, 0.400, 0.400]
	buttonHeight = 		30

	onStateColor = 		[0.700, 1.000, 0.410]
	offStateColor = 	[0.950, 0.140, 0.460]
	# onColor = 		[1.000, 0.000, 0.000]
	# offColor = 		[1.000, 0.000, 0.000]
	neutralStateColor = [0.200, 0.200, 0.200]

	
	sideStr = ['_M', '_L', '_R', '']

	def __init__(self):
		# UI variable color initialization
		self.fkColors=[
		[0.150, 0.800, 1.000], # L
		[0.700, 1.000, 0.410], # M
		[0.950, 0.140, 0.460], # R
		]
		self.ikColors=[
		[0.686, 0.664, 1.300], # L
		[1.000, 1.000, 0.600], # M
		[1.300, 0.481, 0.411], # R
		]

		self.fitSkeleton = fitSkeleton()

		self.skeleNode = 		self.fitSkeleton.skeleNode
		self.fitGroup = 		self.fitSkeleton.fitGroup
		self.fitRigsGroup = 	self.fitSkeleton.fitRigsGroup
		self.fitSkeletonGroup = self.fitSkeleton.fitSkeletonGroup
		self.rigGroup = 		self.fitSkeleton.rigGroup
		self.globalMove = 		self.fitSkeleton.globalMove
		self.joints = 			self.fitSkeleton.joints

		self.ui()



	def ui(self, *args):
		if window('axmnRiggingToolkit', exists=1):
			deleteUI('axmnRiggingToolkit')
		if window('axmnLabelsUI', exists=1):
			deleteUI('axmnLabelsUI')

		if dockControl('axmnLabelsDock', exists=1):
			deleteUI('axmnLabelsDock')

		if dockControl('axmnRiggingDock', exists=1):
			deleteUI('axmnRiggingDock')

		riggingUI = window('axmnRiggingToolkit',
			t = 'Rig Setup',
			resizeToFitChildren = 1,
			sizeable = 1,
			) 
		
		self.riggingUI=riggingUI

		self.toggleVisOn = []
		self.toggleVisOff = []

		# with riggingUI:
		scroll = scrollLayout(panEnabled=1, rc=self.resizeScroller, p=riggingUI)
	
		self.mainForm = verticalLayout(p=scroll)
		with self.mainForm:
			# ===============================================================================
			sections = []
			section1 = verticalLayout(spacing=5)
			sections.append(section1)
			bits = []
			with section1: # Settings Section
				# Title
				bits.append(text('settingsTitle', l='Settings', bgc=self.frameColor, height=self.frameHeight))
				topthing = horizontalLayout()
				bits.append(topthing)
				with topthing:
					with verticalLayout(): # Vis options
						for i, visGroup in enumerate(['Joints', 'Controls', 'Shapes']):
							visibilityRow = horizontalLayout(ratios=[0,0], spacing=2)
							with visibilityRow: # Split between titles and buttons
								visTitle = text(l=visGroup)
								onOffBar = horizontalLayout()
								with onOffBar:
									self.toggleVisOn.append(iconTextButton(
										label='0',
										width=20,
										bgc=self.offStateColor,
										rpt=1,
										))

									self.toggleVisOff.append(iconTextButton(
										label='1',
										width=20,
										bgc=self.neutralStateColor,
										rpt=1,
										))
									self.toggleVisOn[i].setCommand(Callback(self.toggleVis, visGroup))
									self.toggleVisOff[i].setCommand(Callback(self.toggleVis, visGroup))
									
							# Final Collumn at ratio 0 hotfix
							# attach the last element to the bottom
							visibilityRow.attachForm(onOffBar, 'right', 2)
							# detach the top of the last element, so it respects its specified height
							visibilityRow.attachNone(onOffBar, 'left')
							 # attach the previous element to the top of the last element
							visibilityRow.attachControl(visTitle, 'right', 2, onOffBar)
						self.visState()
					with verticalLayout(ratios=[2,5], spacing=0):
						with horizontalLayout(ratios = [1,4], spacing=0):
							separator(style='none')
							
							text(l='Default Colors')
						with horizontalLayout(spacing=0):
							self.fkColorButtons = []
							self.ikColorButtons = []
							for i, colorGroup in enumerate(['L', 'M', 'R']):
								with verticalLayout():
									text(l=colorGroup)
									
									self.fkColorButtons.append(iconTextButton(
									bgc=self.fkColors[i],
									rpt=1))
									self.fkColorButtons[i].setCommand(Callback(self.colorSwatch, i, 0))

									self.ikColorButtons.append(iconTextButton(
									bgc=self.ikColors[i],
									rpt=1))
									self.ikColorButtons[i].setCommand(Callback(self.colorSwatch, i, 1))

				separator(style='none')
			section1.attachForm(bits[0], 'top', 0)
			section1.attachNone(bits[0], 'bottom')
			for i, t in enumerate(bits):
				if i is not 0:
					section1.attachControl(t, 'top', 5, bits[i-1])
					section1.attachNone(t, 'bottom')

			# ===============================================================================
			section2 = verticalLayout(spacing=5)
			sections.append(section2)
			bits = []
			with section2: # Joint tools

				bits.append(text('jointsTitle', l='Skeleton', bgc=self.frameColor, height=self.frameHeight))

				jointToolButtonsRow = horizontalLayout()
				bits.append(jointToolButtonsRow)
				with jointToolButtonsRow:
					jointToolButton = iconTextButton(
						annotation='Create Joint Tool', # 'Create Joint Tool',
						i='kinJoint.png',
						bgc=self.buttonColor,
						rpt=1,
						style='iconAndTextCentered'
					)
					jointToolButton.setCommand(runtime.JointTool)
					jointOnAveButton = iconTextButton(
						annotation='Joint on Average Selection',
						i='geometryConstraint.png',
						bgc=self.buttonColor,
						rpt=1,
						style='iconAndTextCentered'
					)
					jointOnAveButton.setCommand(rb.averagePoint)
					jointOnEachButton = iconTextButton(
						annotation='Joint on Each Selected',
						i='kinDisconnect.png',
						bgc=self.buttonColor,
						rpt=1,
						style='iconAndTextCentered'
					)
					jointOnEachButton.setCommand(rb.eachPoint)

					mirrorJointButton = iconTextButton(
						annotation='Mirror Joint',
						i='kinMirrorJoint_S.png',
						bgc=self.buttonColor,
						# bgc=[0.2,0.2,0.2],
						rpt=1,
						style='iconAndTextCentered'
					)
					mirrorJointButton.setCommand(self.fitSkeleton.mirrorSelectedJoint)

					# removeJointButton = iconTextButton(
					# 	annotation='Remove Joint',
					# 	i='kinRemove.png',
					# 	# bgc=self.buttonColor,
					# 	bgc=[0.2,0.2,0.2],
					# 	rpt=1,
					# 	style='iconAndTextCentered'
					# )
					# removeJointButton.setCommand(runtime.RemoveJoint)

				jointToolButtonsRow = horizontalLayout()
				bits.append(jointToolButtonsRow)
				with jointToolButtonsRow:

					orientJointButton = iconTextButton(
						annotation='Orient Joint',
						i='orientJoint.png',
						bgc=self.buttonColor,
						rpt=1,
						style='iconAndTextCentered'
					)
					orientJointButton.setCommand(self.fitSkeleton.autoOrient)


					createUpButton = iconTextButton(
						annotation='Create Up Object',
						i='locator.png',
						bgc=self.buttonColor,
						rpt=1,
						style='iconAndTextCentered'
					)
					createUpButton.setCommand(self.fitSkeleton.buildOrientUpObject)

					
					labelsButton = iconTextButton(
						# label='Labels',
						annotation='Labels',
						height=self.buttonHeight,
						i='outliner.png',
						bgc=self.buttonColor,
						rpt=1,
						style='iconAndTextCentered')
					labelsButton.setCommand(self.labelsUI)

					initButton = iconTextButton(
						# label='Initialize',
						i='goToBindPose.png',
						annotation = 'Initialize - Select one or more joints. Affects joint heirarchy.',
						height=self.buttonHeight,
						bgc=[0.6, 0.6, 0.6],
						rpt=1,
						style='iconAndTextCentered')
					initButton.setCommand(self.initJoints)

					# Other tools:
					# menuIconListed.png -- Labels
					# Erase.png -- Delete Fit Rig
					# goToBindPose.png -- Auto Heirarchy?
				with horizontalLayout(ratios = [3,1]): # Joint size slider
					self.jointSizeSlider = floatSlider(v=1, minValue=0.001, maxValue=3, dc=self.jsSlider)
					self.jointSizeField = floatField(v=1, minValue=0.001, cc=self.jsField)

				# with horizontalLayout():
				# 	text(l='Mirror')
				# 	text(l='Preserve Children')


			
				separator(style='none')

			section2.attachForm(bits[0], 'top', 0)
			section2.attachNone(bits[0], 'bottom')
			for i, t in enumerate(bits):
				if i is not 0:
					section2.attachControl(t, 'top', 5, bits[i-1])
					section2.attachNone(t, 'bottom')

			# ===============================================================================
			section3 = verticalLayout(spacing=5)
			sections.append(section3)
			bits = []
			with section3: # Fit Rigs
				fitRigTitle = text('fitRigTitle', l='Fit Rig', bgc=self.frameColor, height=self.frameHeight)
				bits.append(fitRigTitle)


				rigsText = text(l='Rigs')
				bits.append(rigsText)


				row = horizontalLayout(spacing=0, ratios=[1,4])
				bits.append(row)
				with row:

					chainButton = iconTextButton(
						# l='Chain',
						bgc=self.buttonColor,
						i='kinJoint.png',
						rpt=1,
						height=self.buttonHeight,
						style='iconAndTextCentered')
					chainButton.setCommand(self.chainFitRigUI)

					chainButtonLabel = iconTextButton(
						l='Chain',
						bgc=self.buttonColor,
						rpt=1,
						height=self.buttonHeight,
						style='iconAndTextCentered')
					chainButtonLabel.setCommand(self.chainFitRigUI)

				row = horizontalLayout(spacing=0, ratios=[1,4])
				bits.append(row)
				with row:

					twoPntButton = iconTextButton(
						i='aimConstraint.png',
						bgc=self.buttonColor,
						rpt=1,
						height=self.buttonHeight,
						style='iconAndTextCentered')
					twoPntButton.setCommand(self.aimIKFitRigUI)
					# bits.append(twoPntButton)
					
					twoPntButtonLabel = iconTextButton(
						l='Aim IK',
						bgc=self.buttonColor,
						rpt=1,
						height=self.buttonHeight,
						style='iconAndTextCentered')
					twoPntButtonLabel.setCommand(self.aimIKFitRigUI)

				row = horizontalLayout(spacing=0, ratios=[1,4])
				bits.append(row)
				with row:

					threePntButton = iconTextButton(
						i='kinHandle.png',
						bgc=self.buttonColor,
						rpt=1,
						height=self.buttonHeight,
						style='iconAndTextCentered')
					threePntButton.setCommand(self.poleVectorIKFitRigUI)

					threePntButtonLabel = iconTextButton(
						l='Pole Vector IK',
						bgc=self.buttonColor,
						rpt=1,
						height=self.buttonHeight,
						style='iconAndTextCentered')
					threePntButtonLabel.setCommand(self.poleVectorIKFitRigUI)
					
				reverseRow = horizontalLayout(ratios=[1,4,4])
				bits.append(reverseRow)
				with reverseRow:
					separator(style='none')
					row = horizontalLayout(spacing=0, ratios=[1,2])
					# bits.append(row)
					with row:
						handButton = iconTextButton(
							i='kinHandle.png',
							bgc=self.buttonColor,
							rpt=1,
							height=self.buttonHeight,
							style='iconAndTextCentered')
						handButton.setCommand(self.poleVectorIKFitRigUI)

						handButtonLabel = iconTextButton(
							l='Hand',
							bgc=self.buttonColor,
							rpt=1,
							height=self.buttonHeight,
							style='iconAndTextHorizontal')
						handButtonLabel.setCommand(self.poleVectorIKFitRigUI)

					# row = horizontalLayout(spacing=0, ratios=[1,4])
					# bits.append(row)
					with horizontalLayout(spacing=0, ratios=[1,2]):
						footButton = iconTextButton(
							i='kinHandle.png',
							bgc=self.buttonColor,
							rpt=1,
							height=self.buttonHeight,
							style='iconAndTextCentered')
						footButton.setCommand(self.footRollFitRigUI)

						footButtonLabel = iconTextButton(
							l='Foot',
							bgc=self.buttonColor,
							rpt=1,
							height=self.buttonHeight,
							style='iconAndTextHorizontal')
						footButtonLabel.setCommand(self.footRollFitRigUI)

					
				row = horizontalLayout(spacing=0, ratios=[1,4])
				bits.append(row)
				with row:

					splineButton = iconTextButton(
						# l='Spline IK (2)',
						i='tangentConstraint.png',
						bgc=self.buttonColor,
						rpt=1,
						height=self.buttonHeight,
						style='iconAndTextCentered')
					splineButton.setCommand(self.bezierSplineFitRigUI)
					# bits.append(splineButton)

					splineButtonLabel = iconTextButton(
						l='Bezier Spline IK',
						bgc=self.buttonColor,
						rpt=1,
						height=self.buttonHeight,
						style='iconAndTextCentered')
					splineButtonLabel.setCommand(self.bezierSplineFitRigUI)
					
					# kinConnect.png - Split to fitJointsA

				

				# rRibbonButton = iconTextButton(
				# 	l='Ribbon',
				# 	bgc=(0.4, 0.4, 0.4),
				# 	rpt=1,
				# 	height=self.buttonHeight,
				# 	style='iconAndTextCentered')
				# bits.append(rRibbonButton)

				

				# reverseHandButton = iconTextButton(
				# 	l='Reverse Hand',
				# 	bgc=(0.4, 0.4, 0.4),
				# 	rpt=1,
				# 	height=self.buttonHeight,
				# 	style='iconAndTextCentered')
				# bits.append(reverseHandButton)

				sep1 = separator(height=10, style='none')
				bits.append(sep1)

				# selectFitRigButton = iconTextButton(
				# 	l='Select Fit Rig',
				# 	bgc=(0.49, 0.49, 0.49),
				# 	rpt=1,
				# 	height=self.buttonHeight,
				# 	style='iconAndTextHorizontal')
				# bits.append(selectFitRigButton)
				# selectFitRigButton.setCommand(getFitNode)

				# deleteFitRigRow = horizontalLayout()
				# with deleteFitRigRow:
				# 	selectAllFitRigsButton = iconTextButton(
				# 		l='Select All Fit Rigs',
				# 		bgc=self.buttonColor,
				# 		rpt=1,
				# 		height=self.buttonHeight,
				# 		style='iconAndTextHorizontal')
				# 	selectAllFitRigsButton.setCommand(getFitNode)
				# 	# bits.append(selectAllFitRigsButton)

				deleteFitRigButton = iconTextButton(
					l='Delete Selected Fit Rig',
					bgc=(0.2, 0.2, 0.2),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal')
				deleteFitRigButton.setCommand(deleteFitRig)
				bits.append(deleteFitRigButton)

					# deleteAllFitRigsButton = iconTextButton(
					# 	l='Delete All Fit Rigs',
					# 	bgc=(0.2, 0.2, 0.2),
					# 	rpt=1,
					# 	height=self.buttonHeight,
					# 	style='iconAndTextHorizontal')
					# # bits.append(deleteAllFitRigsButton)
					# deleteAllFitRigsButton.setCommand(self.deleteAllFitRigs)
				# bits.append(deleteFitRigRow)


				sep2 = separator(height=10, style='none')
				bits.append(sep2)

			section3.attachForm(bits[0], 'top', 0)
			section3.attachNone(bits[0], 'bottom')
			for i, t in enumerate(bits):
				if i != 0:
					section3.attachControl(t, 'top', 5, bits[i-1])
					section3.attachNone(t, 'bottom')

			# ===============================================================================
			section4 = verticalLayout(spacing=5)
			sections.append(section4)
			bits = []
			with section4: # Relationships
				relationshipsTitle = text('relationshipsTitle', l='Relationships', bgc=self.frameColor, height=self.frameHeight)
				bits.append(relationshipsTitle)


				autoHeirarchyButton = iconTextButton(
					l='Auto Heirarchy',
					bgc=(0.4, 0.4, 0.4),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal')
				autoHeirarchyButton.setCommand(self.fitSkeleton.autoHeirarchy)
				
				# parentButton = iconTextButton(
				# 	l='Parent',
				# 	bgc=(0.4, 0.4, 0.4),
				# 	rpt=1,
				# 	height=self.buttonHeight,
				# 	style='iconAndTextHorizontal')

				spaceSwitchButton = iconTextButton(
					l='Space Switch',
					bgc=(0.4, 0.4, 0.4),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal',
					# c=self.spaceSwitchUI,
					enable=False)
				separator(height=10, style='none')

				bits.extend([autoHeirarchyButton, spaceSwitchButton])

			section4.attachForm(bits[0], 'top', 0)
			section4.attachNone(bits[0], 'bottom')
			for i, t in enumerate(bits):
				if i != 0:
					section4.attachControl(t, 'top', 5, bits[i-1])
					section4.attachNone(t, 'bottom')

			# ===============================================================================
			section5 = verticalLayout(spacing=5)
			sections.append(section5)
			bits = []
			with section5: # Rig Build
				buildRigTitle = text('buildRigTitle', l='Build Rig', bgc=self.frameColor, height=self.frameHeight)
				bits.append(buildRigTitle)

				buildAllButton = iconTextButton(
					l='Build Rig',
					bgc=(0.4, 0.4, 0.4),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal',
					c= self.fitSkeleton.buildRigs
					)
				bits.append(buildAllButton)

				buildSelButton = iconTextButton(
					l='Build Selected Rigs',
					bgc=(0.4, 0.4, 0.4),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal',
					c = self.buildSelUI
					)
				bits.append(buildSelButton)

				heirarchyButton = iconTextButton(
					l='Reconstruct Heirarchy',
					bgc=(0.4, 0.4, 0.4),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal',
					c = self.fitSkeleton.rigHeirarchy)
				bits.append(heirarchyButton)


				outputSkeletonButton = iconTextButton(
					l='Output Skeleton',
					bgc=(0.4, 0.4, 0.4),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal')
				outputSkeletonButton.setCommand(self.fitSkeleton.outputSkeleton)
				bits.append(outputSkeletonButton)

				bits.append(separator(height=10, style='none'))

				deleteButton = iconTextButton(
					l='Delete Selected Rigs',
					bgc=(0.2, 0.2, 0.2),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal')
				deleteButton.setCommand(Callback(buildRig.deleteRig))
				bits.append(deleteButton)

				
				bits.append(separator(height=10, style='none'))

			section5.attachForm(bits[0], 'top', 0)
			section5.attachNone(bits[0], 'bottom')
			for i, t in enumerate(bits):
				if i != 0:
					section5.attachControl(t, 'top', 5, bits[i-1])
					section5.attachNone(t, 'bottom')

			section6 = verticalLayout(spacing=5)
			sections.append(section6)
			bits = []
			with section6: # Rig Build
				readerTitle = text('readerTitle', l='Readers', bgc=self.frameColor, height=self.frameHeight)
				bits.append(readerTitle)

				twistReaderButton = iconTextButton(
					l='Twist Reader',
					bgc=(0.4, 0.4, 0.4),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal')
				twistReaderButton.setCommand(readers.twistExtractor)
				coneReaderButton = iconTextButton(
					l='Cone Reader',
					bgc=(0.4, 0.4, 0.4),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal')
				coneReaderButton.setCommand(readers.coneAngleReader)

				deleteReaderButton = iconTextButton(
					l='Delete Reader',
					bgc=(0.2, 0.2, 0.2),
					rpt=1,
					height=self.buttonHeight,
					style='iconAndTextHorizontal')
				


				separator(height=10, style='none')
				bits.extend([twistReaderButton, coneReaderButton, deleteReaderButton])
			section6.attachForm(bits[0], 'top', 0)
			section6.attachNone(bits[0], 'bottom')
			for i, t in enumerate(bits):
				if i != 0:
					section6.attachControl(t, 'top', 5, bits[i-1])
					section6.attachNone(t, 'bottom')

		for section in sections:
			self.mainForm.attachNone(section, 'bottom')

		allowedAreas = ['right', 'left']
		self.dock = dockControl(
			'axmnRiggingDock',
			area='left',
			content=riggingUI,
			allowedArea=allowedAreas
			)



	# =========================================== UI STUFF ===========================================
	def colorSwatch(self, side, fkIk):
		# Standardize side
		sideJ = [1,0,2]
		if fkIk == 0:
			buttons = self.fkColorButtons
		else:
			buttons = self.ikColorButtons

		color = colorEditor(rgbValue=buttons[side].getBackgroundColor())
		parsedColor = [float(i) for i in color.split()]
		buttons[side].setBackgroundColor(parsedColor[0:-1])

		if fkIk == 0:
			self.fkColors[side] = parsedColor[0:-1]
			self.fitSkeleton.fitJointsColor[sideJ[side]] = parsedColor[0:-1]
		else:
			self.ikColors[side] = parsedColor[0:-1]




	def labelsUI(self):

		if dockControl('axmnLabelsDock', exists=1):
			deleteUI('axmnLabelsDock')
			if window('axmnLabelsUI', exists=1):
				deleteUI('axmnLabelsUI')
		else:

			labelsUI = window('axmnLabelsUI',
				t = 'Labels',
				resizeToFitChildren = 1,
				sizeable = 1,
				mxb = 0)
			
			labelsLayout = verticalLayout(p=labelsUI)
			labelButtons = []
			labels = [
			{'label': 'COG',		'color': [0.150, 0.800, 1.000]},
			{'label': 'Spine',		'color': [0.150, 0.800, 1.000]},
			{'label': 'Chest',		'color': [0.150, 0.800, 1.000]},
			{'label': 'Neck',		'color': [0.150, 0.800, 1.000]},
			{'label': 'Head',		'color': [0.150, 0.800, 1.000]},
			{'label': 'Shoulder',	'color': [0.150, 1.000, 0.410]},
			{'label': 'Arm',		'color': [0.150, 1.000, 0.410]},
			{'label': 'Lower Arm',	'color': [0.150, 1.000, 0.410]},
			{'label': 'Hand',		'color': [0.150, 1.000, 0.410]},
			{'label': 'Thumb',		'color': [0.686, 0.664, 1.300]},
			{'label': 'Index',		'color': [0.686, 0.664, 1.300]},
			{'label': 'Middle',		'color': [0.686, 0.664, 1.300]},
			{'label': 'Ring',		'color': [0.686, 0.664, 1.300]},
			{'label': 'Pinky',		'color': [0.686, 0.664, 1.300]},
			{'label': 'Leg',		'color': [0.950, 0.140, 0.460]},
			{'label': 'Lower Leg',	'color': [0.950, 0.140, 0.460]},
			{'label': 'Foot',		'color': [0.950, 0.140, 0.460]},
			{'label': 'Ball',		'color': [1.300, 0.481, 0.411]},
			{'label': 'Toe',		'color': [1.300, 0.481, 0.411]}
			]
			labelNoneButton = iconTextButton(
				label = 'Toggle Labels',
				annotation = 'Toggle Labels',
				height=self.buttonHeight,
				bgc=self.buttonColor,
				rpt=1,
				p=labelsLayout,
				style='iconAndTextHorizontal')
			labelNoneButton.setCommand(Callback(self.fitSkeleton.jointLabels))
				# jointLabelNone))

			for l in labels:
				labelButton = iconTextButton(
				label = 'Label %s' % l['label'],
				annotation = 'Label %s' % l['label'],
				height=self.buttonHeight,
				bgc=l['color'],
				rpt=1,
				p=labelsLayout,
				style='iconAndTextHorizontal')
				labelButton.setCommand(Callback(self.jointLabel, l['label']))

			renameJointsButton = iconTextButton(
				label = 'Rename',
				annotation = 'Rename',
				height=self.buttonHeight,
				bgc=[0.2,0.2,0.2],
				rpt=1,
				p=labelsLayout,
				style='iconAndTextHorizontal')
			renameJointsButton.setCommand(Callback(self.renameByLabels))
			labelsLayout.redistribute()

			allowedAreas = ['right', 'left']
			labelDock = dockControl(
				'axmnLabelsDock',
				area='right',
				content=labelsUI,
				allowedArea=allowedAreas
				)
	def renameByLabels(self):
		self.joints = self.skeleNode.joints.get()
		for j in self.joints:
			if j.attr('type').get():
				side = self.sideStr[j.side.get()]
				name = j.otherType.get()
				if name == '':
					name = j.attr('type').get(asString=1)
				if name == '':
					warning('No labels found for %s' % j)
				else:
					name = '%s%s' % (name.lower(), side)
					j.rename(name)

	def jointLabel(self, label):
		for sel in ls(sl=1):
			if objectType(sel, isType='joint'):
				sel.drawLabel.set(1)
				sel.attr('type').set(18)
				sel.otherType.set(label)
				if hasAttr(sel, 'mirror'):
					if sel.mirror.get():
						mir = sel.mirror.get()
						mir.drawLabel.set(1)
						mir.attr('type').set(18)
						mir.otherType.set(label)

	def jointLabelNone(self):
		for sel in ls(sl=1):
			if objectType(sel, isType='joint'):
				sel.drawLabel.set(0)
				sel.attr('type').set(18)
				sel.otherType.set('')
				if hasAttr(sel, 'mirror'):
					if sel.mirror.get():
						mir = sel.mirror.get()
						mir.drawLabel.set(0)
						mir.attr('type').set(18)
						mir.otherType.set('')


	def resizeScroller(self):
		if window('axmnRiggingToolkit', exists=1):
			width=window(self.riggingUI, q=True, w=True)
			formLayout(self.mainForm, e=1, w=width-20)
		elif dockControl('axmnLabelsDock', exists=1):
			width=dockControl(self.dock, q=True, w=True)
			formLayout(self.mainForm, e=1, w=width-20)


	def visState(self):
		visAttrs = [
		self.fitGroup.jointsVis,
		self.fitGroup.controlsVis,
		self.fitGroup.shapesVis
		]
		for i, vattr in enumerate(visAttrs):
			if vattr.get():
				self.toggleVisOn[i].setBackgroundColor(self.onStateColor)
				self.toggleVisOff[i].setBackgroundColor(self.neutralStateColor)
			else:
				self.toggleVisOn[i].setBackgroundColor(self.neutralStateColor)
				self.toggleVisOff[i].setBackgroundColor(self.offStateColor)

	def toggleVis(self, visRow):
		visAttrs = [
		self.fitGroup.jointsVis,
		self.fitGroup.controlsVis,
		self.fitGroup.shapesVis
		]
		visOptions = ['Joints', 'Controls', 'Shapes']
		i = visOptions.index(visRow)
		
		targetState = not visAttrs[i].get()
		if targetState:
			self.toggleVisOn[i].setBackgroundColor(self.onStateColor)
			self.toggleVisOff[i].setBackgroundColor(self.neutralStateColor)
		else:
			self.toggleVisOn[i].setBackgroundColor(self.neutralStateColor)
			self.toggleVisOff[i].setBackgroundColor(self.offStateColor)

		visAttrs[i].set(targetState)

		# if visRow == 'Settings':
		# 	self.fitGroup.controlsVis.set(not self.fitGroup.controlsVis.get())

		# if visRow == 'Controls':
		# 	self.fitGroup.shapesVis.set(not self.fitGroup.shapesVis.get())


	def deleteAllFitRigs(self, *args):
		fitRigs = self.skeleNode.fitRigsList.get()
		print fitRigs

		deleteFitRig(fitRigs)

	def jsSlider(self, *args):
		sliderValue = self.jointSizeSlider.getValue()
		jointDisplayScale(sliderValue)
		self.jointSizeField.setValue(sliderValue)

	def jsField(self, *args):
		fieldValue = self.jointSizeField.getValue()
		jointDisplayScale(fieldValue)
		self.jointSizeSlider.setValue(fieldValue)

	# ========================================= FIT SKELETON =========================================

	def chainFitRigUI(self):
		chainFitRig(ls(sl=1))
	def poleVectorIKFitRigUI(self):
		poleVectorIKFitRig(ls(sl=1))
	def aimIKFitRigUI(self):
		aimIKFitRig(ls(sl=1))
	def bezierSplineFitRigUI(self):
		bezierSplineFitRig(ls(sl=1))
	
	def footRollFitRigUI(self):
		footRollFitRigNew(joints=ls(sl=1)[1:], pvikFitNode=ls(sl=1)[0])
	
	def spaceSwitchUI(self):
		spaceSwitchFitRig(ls(sl=1))

	def buildSelUI(self):
		fitNodes = getFitNode(selection=ls(sl=1))
		self.fitSkeleton.buildRigs(fitNodes)
		



	def mirrorSelectedJoints():
		selection = ls(sl=1)
		# Determine which side joints are on and give warning if both on one side
		# Run Symmetry setup on selected joints


	def initRig(self, *args):

		sel = ls(sl=1)

		self.fitSkeleton = fitSkeleton()

		self.skeleNode = 		ls('skeleNode_META')[0]
		self.fitGroup = 		self.skeleNode.fitGroup.get()
		self.fitRigsGroup = 	self.skeleNode.fitRigsGrp.get()
		self.fitSkeletonGroup = self.skeleNode.fitSkeletonGroup.get()
		self.rigGroup = 		self.skeleNode.rigGroup.get()
		self.globalMove = 		self.skeleNode.globalMove.get()

		self.fitSkeleton.initializeJointGroup()

		self.joints = 			self.skeleNode.joints.get()

		select(sel)

	def initJoints(self, *args):

		sel = ls(sl=1)
		self.fitSkeleton.initializeJointGroup()
		select(sel)



	# =========================================== FIT RIGS ===========================================


# =================================================================================

class fitSkeleton:
	'''
	Class for fitSkeleton to create home for fitRigs and rig builds.
	'''
	dev = 1
	hidden = not dev
	offsets = 0 # Amount of offset controls for global move (add to all controls?)
	
	# ===================================  Colors ==========================================
	# Manage this a little better.  All discrete color options should be at least accessible
	colorControls = {
	'globalMove' : 		[1.000, 0.009, 0.267],
	'offset' : 			[1.000, 0.303, 0.484],
	'fitGroup' : 		[0.610, 1.000, 0.400],
	}

	fitJointsInitColor = [
	(0.700, 1.000, 0.410), # M
	(0.150, 0.800, 1.000), # L
	(0.950, 0.140, 0.460), # R
	]

	# Naming string for center, left, right, none. Determines mirror joint
	sideStr = ['_M', '_L', '_R', '']

	#  ===================================  Init ==========================================
	def __init__(self, skeleNode=None):
		'''
		Finds or creates the skeleton node from which future data should be pulled
		(This allows class behavior to be saved to scene. Eventually add meta class methods/getters/setters)
		'''

		# Maintain selection
		selection = ls(sl=1)

		loadPlugin( 'matrixNodes.mll', qt=True )

		self.freezeList = []

		self.namesList = {}
		self.namesList['skeleNode'] = { 'desc': 'skeleNode',  'warble': 'meta', 	'other': [] }
		
		names = rb.constructNames(self.namesList)

		# Declare skeleNode
		if skeleNode is None:
			if len(ls(names.get('skeleNode', 'rnm_skeleNode'))) > 0:
				self.skeleNode = ls(names.get('skeleNode', 'rnm_skeleNode'))[0]
				if len(ls(names.get('skeleNode', 'rnm_skeleNode'))) > 1:
					warning('More than one object matches name: %s' % names.get('skeleNode', 'rnm_skeleNode'))
			else:
				self.skeleNode = createNode('network', n=names.get('skeleNode', 'rnm_skeleNode'))
		else:
			self.skeleNode = skeleNode

		# Make sure rig groups exist
		self.initializeRig(selection)

		self.fitJointsColor = [
		self.skeleNode.fitJointsColorM.get(),
		self.skeleNode.fitJointsColorL.get(),
		self.skeleNode.fitJointsColorR.get()
		]

		self.joints = self.skeleNode.joints.get()

		select(selection)

	# @property
	# def exampleAttribute(self)
	# 	return self.rigNode.exampleAttribute.get()

	# @exampleAttribute.setter
	# def exampleAttributeS(self, value)
	# 	self.rigNode.exampleAttribute.set()

	def initializeRig(self, selection):
		'''
		Initilize (or verify) overall rig group nodes
		'''

		# self.skeleNode.fitJointsColorM
		# self.skeleNode.fitJointsColorL
		# self.skeleNode.fitJointsColorR
		# Color attributes
		if not hasAttr(self.skeleNode, 'fitJointsColorM'):
			addAttr(self.skeleNode, ln='fitJointsColorM', at='float3', uac=1, hidden=self.hidden)
			addAttr(self.skeleNode, ln='fitJointsColorMR', at='float', parent='fitJointsColorM', hidden=self.hidden)
			addAttr(self.skeleNode, ln='fitJointsColorMG', at='float', parent='fitJointsColorM', hidden=self.hidden)
			addAttr(self.skeleNode, ln='fitJointsColorMB', at='float', parent='fitJointsColorM', hidden=self.hidden)
			self.skeleNode.fitJointsColorM.set(self.fitJointsInitColor[0])
		if not hasAttr(self.skeleNode, 'fitJointsColorL'):
			addAttr(self.skeleNode, ln='fitJointsColorL', at='float3', uac=1, hidden=self.hidden)
			addAttr(self.skeleNode, ln='fitJointsColorLR', at='float', parent='fitJointsColorL', hidden=self.hidden)
			addAttr(self.skeleNode, ln='fitJointsColorLG', at='float', parent='fitJointsColorL', hidden=self.hidden)
			addAttr(self.skeleNode, ln='fitJointsColorLB', at='float', parent='fitJointsColorL', hidden=self.hidden)
			self.skeleNode.fitJointsColorL.set(self.fitJointsInitColor[1])
		if not hasAttr(self.skeleNode, 'fitJointsColorR'):
			addAttr(self.skeleNode, ln='fitJointsColorR', at='float3', uac=1, hidden=self.hidden)
			addAttr(self.skeleNode, ln='fitJointsColorRR', at='float', parent='fitJointsColorR', hidden=self.hidden)
			addAttr(self.skeleNode, ln='fitJointsColorRG', at='float', parent='fitJointsColorR', hidden=self.hidden)
			addAttr(self.skeleNode, ln='fitJointsColorRB', at='float', parent='fitJointsColorR', hidden=self.hidden)
			self.skeleNode.fitJointsColorR.set(self.fitJointsInitColor[2])

		# multi attributes
		if not hasAttr(self.skeleNode, 'joints'):
			addAttr(self.skeleNode, ln='joints', sn='jnts', at='message', multi=1, indexMatters=0, hidden=self.hidden)
		if not hasAttr(self.skeleNode, 'symmetryConstraints'):
			addAttr(self.skeleNode, ln='symmetryConstraints', sn='sym', at='message', multi=1, indexMatters=0, hidden=self.hidden )
		if not hasAttr(self.skeleNode, 'fitRigs'):
			addAttr(self.skeleNode, ln='fitRigs', at='message', multi=1, indexMatters=0, hidden=self.hidden )

		# # control attributes
		if not hasAttr(self.skeleNode, 'controlScale'):
			addAttr(self.skeleNode, ln='controlScale', hidden=self.hidden )

		# ========================================= Construct Names ==========================================
		# Title, warble, side, args
		namesDict = {
		'globalMove':		{'desc': 'globalMove', 		'warble': 'ctrl',	'side': 3, 	'other': [] },
		'offset':			{'desc': 'offset', 			'warble': 'ctrl',	'side': 3, 	'other': [] },
		'fitSkeleton':		{'desc': 'fitSkeleton',		'warble': 'grp',	'side': 3, 	'other': [] },
		'fitHeirarchy':		{'desc': 'fitHeirarchy',	'warble': 'grp',	'side': 3, 	'other': [] },
		'symmetry':			{'desc': 'symmetry',		'warble': 'grp',	'side': 3, 	'other': [] },
		'fit':				{'desc': 'fit',				'warble': 'grp',	'side': 3, 	'other': [] },
		'fitRigs':			{'desc': 'fitRigs',			'warble': 'grp',	'side': 3, 	'other': [] },
		'rig':				{'desc': 'rig',				'warble': 'grp',	'side': 3, 	'other': [] },
		'socket':			{'desc': 'socket',			'warble': 'grp',	'side': 3, 	'other': [] },
		'output':			{'desc': 'output',			'warble': 'grp',	'side': 3, 	'other': [] },
		'geometry':			{'desc': 'geometry',		'warble': 'grp',	'side': 3, 	'other': [] },
		# 
		'globalMoveHist':	{'desc': 'skele', 			'warble': 'hist',	'side': 3, 	'other': ['global', 'radius'] },
		'radMult':			{'desc': 'skele', 			'warble': 'mult',	'side': 3, 	'other': ['global', 'radius'] },
		'fitRadMult':		{'desc': 'skele', 			'warble': 'mult',	'side': 3, 	'other': ['fit', 'radius'] },
		'offsetHist':		{'desc': 'skele', 			'warble': 'hist',	'side': 3, 	'other': ['offset', 'radius'] },
		'fitGroupHist':		{'desc': 'skele', 			'warble': 'hist',	'side': 3, 	'other': ['fit', 'radius'] },
		}
		names = rb.constructNames(namesDict)
		


		# ========================================= Global Move ==========================================
		'''
		The thing that what moves the rig
		ToDo:
		Use a fancier looking control
		'''

		try:
			self.globalMove = self.skeleNode.globalMove.get()
		except:
			self.globalMove, gmHist = circle(r=1, nr=[0, 1, 0], ch=True)
			self.globalMove.rename(names.get('globalMove', 'rnm_globalMove'))
			gmHist.rename(names.get('globalMoveHist', 'rnm_globalMoveHist'))
			globalMoveShape = self.globalMove.getShapes()
			col.setViewportRGB(globalMoveShape, self.colorControls['globalMove'])
			rb.cbSep(self.globalMove)
			addAttr(self.globalMove, ln='radius', dv=10, k=1)
			self.globalMove.radius.connect(gmHist.radius)

		self.skeleConnect(self.globalMove, 'globalMove')

		
		# ========================================= Offsets =============================================
		'''
		It's potentially useful to have one or more offset controls between the globalMove and the rig.
		Creates as many as is set by global class attribute 'offsets' and sets the last to the parent of fit/rig/geo grps
		'''

		# Overwrite to determine parentage
		self.lastOffset = self.globalMove
		scaleFactor = (1.0 - 0.1)

		for i in range(self.offsets):
			# Vis attribute
			if not self.globalMove.hasAttr('offsetVis'):
				rb.cbSep(self.globalMove)
				addAttr(self.globalMove, ln='offsetVis', at='short', min=0, max=1, dv=0, k=1)
				self.globalMove.offsetVis.set(k=0, cb=1)

			globalOffset, goHist = circle(nr=[0, 1, 0], ch=True)
			globalOffset.rename(names.get('offset', 'rnm_globalOffset'))
			parent(globalOffset, self.lastOffset)
			goHist.rename('%s_#' % names.get('offsetHist', 'rnm_globalOffsetHist'))

			globalOffsetShape = listRelatives(globalOffset, s=True)[0]
			col.setViewportRGB([globalOffsetShape], self.colorControls['offset'])
			self.globalMove.offsetVis.connect(globalOffsetShape.v)
			
			radMult = createNode('multDoubleLinear', n='%s_#' % names.get('radMult', 'rnm_radMult'))
			self.globalMove.radius.connect(radMult.i1)
			radMult.i2.set(scaleFactor)
			radMult.o.connect(goHist.radius)


			# Make last globalOffset parent of next globalOffset
			self.lastOffset = globalOffset
			scaleFactor = (scaleFactor - 0.1)

		# self.skeleConnect(self.offsets, 'offset')
			

		# ============================================ Fit Rig ============================================
		'''
		Overall group for the fit setups
		Contains fitRigs_GRP and fitSkeleton_GRP, and has attributes for useful overall controls
			Control scale
			Length-based Scaling OnOff
			Controls Vis
			Shapes Vis
			Skeleton Vis
			FitRig Selection Handles
			Joint Labels
		'''
		try:
			self.fitGroup = self.skeleNode.fitGroup.inputs()[0]
		except:
			self.fitGroup, fitGroupHist = circle(n=names.get('fit', 'rnm_fit'), nr=[0, 1, 0], ch=True)
			parent(self.fitGroup, self.lastOffset)
			fitGroupShape = listRelatives(self.fitGroup, s=True)[0]
			col.setViewportRGB([fitGroupShape], self.colorControls['fitGroup'])
			self.freezeList.append(self.fitGroup)

			fitGroupHist.rename(names.get('fitGroupHist', 'rnm_fitGroupHist'))

			fitRadMult = createNode('multDoubleLinear', n=names.get('fitRadMult', 'rnm_fitRadMult'))
			try:
				radMult.o.connect(fitRadMult.i1)
			except:
				self.globalMove.radius.connect(fitRadMult.i1)
			fitRadMult.i2.set(scaleFactor)
			fitRadMult.o.connect(fitGroupHist.radius)

			attrs = ['rx', 'ry', 'rz', 'sx', 'sy', 'sz']
			for attribute in attrs:
				self.fitGroup.attr(attribute).set(l=1, k=0)
			scaleFactor = (scaleFactor - 0.1)
			self.fitGroup.inheritsTransform.set(0)

		

		print self.fitGroup
		if not hasAttr(self.fitGroup, 'controlScale'):
			rb.cbSep(self.fitGroup)
			addAttr(self.fitGroup, ln='controlScale', min=0, dv=1, k=1) # Overall controls scaling

		if not hasAttr(self.fitGroup, 'lengthBasedScaling'):
			addAttr(self.fitGroup, ln='lengthBasedScaling', min=0, dv=1, k=1) # Length assisted controls scaling
		
		if not hasAttr(self.fitGroup, 'jointsVis'):
			addAttr(self.fitGroup, ln='jointsVis', at='short', min=0, max=1, dv=1, k=1) # View fit joints

		if not hasAttr(self.fitGroup, 'shapesVis'):
			addAttr(self.fitGroup, ln='shapesVis', at='short', min=0, max=1, dv=1, k=1) # View curve controls for all connected fitRigs
		
		if not hasAttr(self.fitGroup, 'controlsVis'):
			addAttr(self.fitGroup, ln='controlsVis', at='short', min=0, max=1, dv=1, k=1) # View curve controls for all connected fitRigs
		
		
		self.skeleConnect(self.fitGroup, 'fitGroup')
		
		# ========================================= Fit Skeleton ==========================================
		
		try:
			self.fitSkeletonGroup = self.skeleNode.fitSkeletonGroup.inputs()[0]
		except:
			self.fitSkeletonGroup = createNode('transform', n=names.get('fitSkeleton', 'rnm_fitSkeleton'), p=self.fitGroup)
			self.freezeList.append(self.fitSkeletonGroup)
		
		if not isConnected(self.fitGroup.jointsVis, self.fitSkeletonGroup.v):
			self.fitGroup.jointsVis >> self.fitSkeletonGroup.v

		self.skeleConnect(self.fitSkeletonGroup, 'fitSkeletonGroup')
		# ========================================= Symmetry Group =======================================

		try:
			self.symmetryGroup = self.skeleNode.symmetryGroup.inputs()[0]
		except:
			self.symmetryGroup = createNode('transform', n=names.get('symmetry', 'rnm_symmetryGroup'), p=self.fitSkeletonGroup)
			self.freezeList.append(self.symmetryGroup)


		self.skeleConnect(self.symmetryGroup, 'symmetryGroup')
		# ========================================= Heirarchy Group =======================================
		try:
			self.fitHeirarchy = self.skeleNode.fitHeirarchy.inputs()[0]
		except:
			self.fitHeirarchy = createNode('transform', n=names.get('fitHeirarchy', 'rnm_fitHeirarchyGrp'), p=self.fitGroup)
			self.freezeList.append(self.fitHeirarchy)
		
		if not isConnected(self.fitGroup.controlsVis, self.fitHeirarchy.v):
			self.fitGroup.controlsVis >> self.fitHeirarchy.v

		self.skeleConnect(self.fitHeirarchy, 'fitHeirarchy')

		# ========================================= Fit Rigs Group =======================================
		try:
			self.fitRigsGroup = self.skeleNode.fitRigsGroup.inputs()[0]
		except:
			self.fitRigsGroup = createNode('transform', n=names.get('fitRigs', 'rnm_fitRigs'), p=self.fitGroup)
			self.freezeList.append(self.fitRigsGroup)

		self.skeleConnect(self.fitRigsGroup, 'fitRigsGroup')
		# ========================================= Rig Group ==========================================
		try:
			self.rigGroup = self.skeleNode.rigGroup.inputs()[0]
		except:
			self.rigGroup = createNode('transform', n=names.get('rig', 'rnm_rig'), p=self.lastOffset)
			self.freezeList.append(self.rigGroup)

		self.skeleConnect(self.rigGroup, 'rigGroup')
		# ========================================= Socket Group ==========================================
		# if not self.skeleNode.socketGroup.get():
		# 	self.socketGroup = createNode('transform', n=names.get('socket', 'rnm_socketGroup'), p=self.rigGroup)
		# 	self.freezeList.append(self.socketGroup)
		# else:
		# 	self.socketGroup = ls(names.get('socket', 'rnm_socketGroup'))[0]

		# self.skeleConnect(self.socketGroup, 'socketGroup')
		# # ========================================= Output Group ==========================================
		try:
			self.outputGroup = self.skeleNode.outputGroup.inputs()[0]
		except:
			self.outputGroup = createNode('transform', n=names.get('output', 'rnm_outputGroup'), p=self.rigGroup)
			self.freezeList.append(self.outputGroup)

		self.skeleConnect(self.outputGroup, 'outputGroup')
		# ========================================= Geo Group ==========================================
		'''
		Not sure if this should really be locked. add ability to offset the geo from rig controls?
		'''
		try:
			self.geometryGroup = self.skeleNode.geometryGroup.inputs()[0]
		except:
			self.geometryGroup = createNode('transform', n=names.get('geometry', 'rnm_geometry'), p=self.lastOffset)
			self.geometryGroup.inheritsTransform.set(0)


		self.skeleConnect(self.geometryGroup, 'geometryGroup')
		# ========================================= Finalize ==========================================

		# Freeze nodes to be frozen
		rb.lockAndHide(self.freezeList, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'])
		for node in self.freezeList:
			col.setOutlinerRGB(node, [0.570, 0.668, 0.668])

		print 'Fit Rig Initialization Completed.\n'

	def skeleConnect(self, node, attribute, multi=False):
		print node
		if not hasAttr(node, 'skeleNode'):
			addAttr(node, ln='skeleNode', at='message', h=self.hidden)
		if not hasAttr(self.skeleNode, attribute):
			addAttr(self.skeleNode, ln=attribute, at='message', h=self.hidden)
		if not multi:
			if not isConnected(node.skeleNode, self.skeleNode.attr(attribute)):
				node.skeleNode.connect(self.skeleNode.attr(attribute), f=1)
		else:
			if not isConnected(node.skeleNode, self.skeleNode.attr(attribute)):
				node.skeleNode.connect(self.skeleNode.attr(attribute), f=1, na=True)

	def initializeJointGroup(self):
		'''
		Initializes or updates all joints in fitSkeleton group.

		TODO:
		When INITIALIZING:
		Check to see which side joints are on, and label them accordingly.
		Try to guess which joint is considered its mirror and initialize mirror connection

		Anytime:
		Checks side label value and sets colors accordingly

		Mirror Search Input:
		Checks naming conventions for mirroring behavior. Automatically adds mirror attribute, and
		sets up symmetry constraints.
		
		TODO
		Make this more interactive
		Set going every time joint is created?
		use mirroring command to create joint mirroring, or sel 2 and connect?
		'''

		selection = ls(sl=1)

		nodeList = []
		warnCount = 0

		jointsList = ls(self.skeleNode.fitSkeletonGroup.get().listRelatives(allDescendents=1), type='joint')

		# If no joints found in group, use parent selection (if sel is a joint) and try again
		if not len(jointsList):
			if len(ls(sl=1, type='joint')):
				parent(ls(sl=1), self.skeleNode.fitSkeletonGroup.get())
				jointsList = ls(self.skeleNode.fitSkeletonGroup.get().listRelatives(allDescendents=1), type='joint')


		if self.dev:
			print '%s Joints in FitSkeleton.' % len(jointsList)
			print jointsList

		if not len(jointsList):
			raise Exception('No data specified.')

		for jnt in jointsList:
			if not isinstance(jnt, PyNode):
				if not objectType(jnt, isType='joint'):
					raise Exception('Specify joints, or ensure selected objects are joints: %s' % jnt)


		# TODO - needs a tolerance factor
		# Comparrison list to make sure overlapping joints are sized accordingly

		for jnt in jointsList:
			self.initializeSkeleJoint(jnt)



	def skeleInitFromFile(self):
		'''
		Potential start for future csv skeleton reader (just save and import it for now)
		'''
		raise Exception('Not ready yet')
		import csv
		with open(file, 'rb') as f:
			reader = csv.reader(f)
			for row in reader:
				attributes = row.split(',')
				newSkeleJnt(name=attributes[0], side=attributes[1], up=attributes[2], label=attributes[3], parent=attributes[4], t=attributes[5], end=attributes[6])

	def initializeSkeleJoint(self, bone, side=None, up=1, upObject=None, worldOrientUp=3, label=None):
		'''
		Do some cleanup on each joint
		Radius
		Side label
		Auto orient options

		'''
		# Error check
		if not isinstance(bone, nt.Joint):
			raise Exception('Object is not a joint: %s' % bone)

		# If up is specified in code as an object, but no object is specified, give warning
		if up == 0:
			if upObject is None:
				warning('No up object specified')
			elif not isinstance(upObject, PyNode):
				raise Exception('Up object is not a PyNode')
			elif not upObject.exists():
				warning('upObject cannot be found in scene.')

		warnCount = 0

		# Radius
		bone.radius.set(0.5)

		# Side
		bone.side.set(k=1)
		if side is None:
			jntT = xform(bone, q=1, rp=1, ws=1)
			# Automatically apply left/right/mid, and mirror based on worldX
			if jntT[0] > (0.01):
				side = 1
				firstTerm, secondTerm = self.sideStr[1], self.sideStr[2]
			elif jntT[0] < (-0.01):
				side = 2
				firstTerm, secondTerm = self.sideStr[2], self.sideStr[1]
			else: 
				side = 0


			if side == 1: # If Left
				
					# if self.dev: print self.sideStr[side]
					replaceName = bone.shortName().replace(firstTerm, secondTerm)
					# If name is successfully different
					if not replaceName == bone.shortName():
						# if self.dev: print 'Replace string found: %s --> %s' % (replaceName, sel.shortName())
						matches = ls(replaceName)
						# if 1 joint with new name found
						if len(matches) == 1:
							reverseChild = matches[0]
							# if self.dev: print 'Mirror Found: %s' % reverseChild
							autoMirror=1
							if hasAttr(reverseChild, 'autoMirror'):
								autoMirror = reverseChild.autoMirror.get()
							if autoMirror:
								self.mirrorJoint(bone, mirrored=reverseChild)

						# Too many joints found
						elif len(matches) > 1:
							warning('Error: %s \nMore than one object matches name: %s' % (bone, replaceName))
							warnCount = warnCount + 1
						# No Mirror joints found
						else:
							warning('No mirror joint found for %s. (Searched for %s' % (bone, replaceName))
							warnCount = warnCount + 1


		if side is not None:
			bone.side.set(side)
			for attribute in bone.jointOrient.getChildren():
				attribute.set(k=0, cb=1)
			# Auto orient attributes
			if not all( [hasAttr(bone, 'worldOrientUp'), hasAttr(bone, 'worldOrientObject'), hasAttr(bone, 'worldOrientObject')] ):
				rb.cbSep(bone)
				addAttr(bone, ln='up', sn='up', at='enum', dv=0, enumName=':'.join(['Y', 'Y-', 'Z', 'Z-']), keyable=1)
				addAttr(bone, ln='worldOrientUp', sn='wup', at='enum', dv=3, enumName='X=1:Y=2:Z=3:-X=-1:-Y=-2:-Z=-3:Object=0:World=4', keyable=1)
				addAttr(bone, ln='worldOrientObject', sn='upo', at='message')

				bone.wup.set(up)
				bone.up.set(0)
				if upObject:
					bone.upo.set(upObject)

			if not hasAttr(bone, 'autoMirror'):
				rb.cbSep(bone)
				addAttr(bone, ln='autoMirror', at='short', min=0, max=1, dv=1, k=1)
				# addAttr(bone, ln='reverse', sn='rev', at='enum', dv=0, enumName=':'.join(['Behavior', 'None']), keyable=1)

			if not hasAttr(bone, 'skeleNode'):
				addAttr(bone, ln='skeleNode', at='message', hidden=self.hidden)


			# Highlighting
			bone.selectionChildHighlighting.set(0)

			# Set default manipulator to 'Smart'
			# (use 'T' button to access default manipulator)
			bone.showManipDefault.set(6)
		
		self.updateSkeleJoint(bone)

		return bone


	def updateSkeleJoint(self, bone):

		#Color
		side = bone.side.get()
		if side < 3:
			color = self.fitJointsColor[side]
			col.setViewportRGB(bone, color)
			col.setOutlinerRGB(bone, color)

		try:
			bone.skeleNode.connect(self.skeleNode.joints, nextAvailable=1, f=1)
		except RuntimeError:
			pass

		if self.dev:
			print(bone + " initialized.")

	def mirrorSelectedJoint(self):
		# Use buttons to link/unlink mirrored joints
		# Based on length of selection.
		# If none selected, if all joints on one side, mirror all unmirrored joints
		# If one selected, create mirroring on heirarchy
		# If two selected on either side, link or unlink joints (second constrained to first)
		# if more than two selected on either side, error?

		selJoints = ls(sl=1, type='joint')
		if len(selJoints) == 0:
			# Get each top joint with side data
			joints = heirSort(self.skeleNode.joints.get())
			sideJoints = []
			for jnt in joints:
				if not jnt.getParent() in sideJoints: # (make sure it's top joint only)
					if jnt.side.get(asString=True) == 'Left' or jnt.side.get(asString=True) == 'Right':
						sideJoints.append(jnt)
			for jnt in sideJoints:
				if not self.sideStr[1] in jnt.nodeName() and not self.sideStr[2] in jnt.nodeName():
					# Get side based on position:
					wsx = xform(jnt, q=1, ws=1, rp=1)[0]
					if wsx < 0.01:
						jnt.rename('%s%s' (jnt.nodeName(), self.sideStr[1]))
					elif wsx > 0.01:
						jnt.rename('%s%s' (jnt.nodeName(), self.sideStr[2]))
					else:
						raise Exception('Joint side cannot be determined.')

				# if jnt.nodeName().replace()
				self.mirrorJoint(jnt)
				

		if len(selJoints) == 2:
			pass
		print selJoints
		for selJoint in selJoints:
			self.mirrorJoint(selJoint)

	def mirrorJoint(self, bone, mirrored=None):
		''' Connects fitJoints across with symmetry constraint
		Either specify mirrored joint, or find using naming conventions.
		'''
		boneT = xform(bone, q=1, rp=1, ws=1)
			# Automatically apply left/right/mid, and mirror
		
		if mirrored is None:
			# Check to see what side joint is on, and pick naming convention
			if boneT[0] > (0.01):
				side = 1 # Right
				oppSide = 2
				firstTerm, secondTerm = self.sideStr[1], self.sideStr[2]
			elif boneT[0] < (-0.01):
				side = 2 # Left
				oppSide = 1
				firstTerm, secondTerm = self.sideStr[2], self.sideStr[1]
			else: 
				side = 0

			mirroredName = bone.nodeName().replace(firstTerm, secondTerm)
			if mirroredName == bone.nodeName():
				warning('Rename unsuccessful (%s, %s) (%s, %s)' % (firstTerm, secondTerm, bone.nodeName(), mirroredName))

			# mirroredParent()
			mirrored = createNode('joint', n=mirroredName, p=self.fitSkeletonGroup)
			self.initializeSkeleJoint(mirrored, side=oppSide)
			# mirrored.side.set(side)
			

		if not hasAttr(bone, 'mirror'):
			addAttr(bone, ln='mirror', sn='mir', at='message', hidden=self.hidden)
		if not hasAttr(mirrored, 'mirror'):
			addAttr(mirrored, ln='mirror', sn='mir', at='message', hidden=self.hidden)
		if not isConnected(bone.mirror, mirrored.mirror):
			bone.mirror >> mirrored.mirror

		sym = rb.symmetryConstraint(bone, mirrored)
		addAttr(sym, ln='skeleNode', at='message', h=self.hidden)
		if not isConnected(sym.skeleNode, self.skeleNode.symmetryConstraints):
			sym.skeleNode.connect(self.skeleNode.symmetryConstraints, na=1, f=1)
		for sym in self.skeleNode.symmetryConstraints.get():
			parent(sym, self.skeleNode.symmetryGroup.get())

			
	
	def autoHeirarchy(self):
		self.fitHeir =  self.skeleNode.fitHeirarchy.get()
		self.fitRigs =  self.skeleNode.fitRigsList.get()
		# self.fitRigs = self.fitHeir.getChildren()
		# print self.fitRigs
		# Sort fitrigs in dictionary based on length of each heirarchy
		heirScore = {}
		for fr in self.fitRigs:
			heirScore[fr] = (len(fr.jointsList.get()[0].getAllParents()))

		import operator
		sortedHeir = sorted(heirScore.items(), key=operator.itemgetter(1))
		# heirScore.sort()
		# heirScore = sorted(heirScore.iteritems(), key=lambda (k,v): (v,k)):
		# for key, value in sorted(mydict.iteritems(), key=lambda (k,v): (v,k)):
		#	print "%s: %s" % (key, value)

		# run parenting in order
		for fr, val in sortedHeir:
			jnt0 = fr.jointsList.get()[0]
			# check each parent and if there's a fitRig connected, parent it there
			p = jnt0.getParent()
			for i in range(3): # Check three times? messy tho
				if len(p.message.outputs()):
					outp = p.message.outputs()
					for o in outp:
						if o.hasAttr('rigType'):
							if p in o.jointsList.get():
								ind = o.jointsList.get().index(p)
							parent(fr, o, r=1)
							continue
				else:
					p = p.getParent()

	def autoOrient(self):
		'''
		For each joint in fitSkeleton, use it's cb orient information to orient

		'''
		print self.fitSkeletonGroup

		selection = ls(sl=1)
		
		# If there are fitSkeleton joints selected, operate on those joints.  Otherwise, operate on them all.
		useSelection = False
		if len(selection):
			useSelection = True

		for sel in selection:
			if sel not in self.skeleNode.joints.get():
				useSelection = False

		if useSelection:
			joints = heirSort(selection)
		else:
			joints = heirSort(self.skeleNode.joints.get())

		orientJoints = [] # Joints to be oriented
		roots = [] # Find root joint and use to freeze hierarchy
		for jnt in joints:
			# Check if is a joint
			if not isinstance(jnt, nodetypes.Joint):
				raise Exception('Object %s is not a joint.' % jnt)
			
			if jnt.getParent() is self.fitSkeletonGroup:
				roots.append(jnt)
			
			# Check for symmtery constraint
			appnd = True # Append Yes/No
			targetAttributesCheck = [
			jnt.translate,
			jnt.tx,
			jnt.ty,
			jnt.tz,
			jnt.rotate,
			jnt.rx,
			jnt.ry,
			jnt.rz,
			]

			for attribute in targetAttributesCheck:
				# check if attributes have inputs
				if len(attribute.inputs()):
					appnd = False # if any attributes have inputs, shut it down
					warning('Joint has incoming connections. Skipping... : %s.%s' % (jnt, attribute))
					break

			if appnd:
				# Check for duplicates
				if not jnt in orientJoints:
					orientJoints.append(jnt)


		# create a proxy object, and point constrain all joints to world to prevent unwanted repositioning
		transList = []
		pntList = []
		for jnt in self.skeleNode.joints.get():
			trans = createNode('transform')
			transList.append(trans)
			# point constraints to lock down positions
			try:
				delete(pointConstraint(jnt, trans)) # Snap to location
				pntList.append(pointConstraint(trans, jnt))
			except:
				pass

		

		endJnts = []
		for jnt in orientJoints:	
			nextJ = jnt.getChildren()
			if not len(nextJ):
				# Add to end joints if joint has no children
				endJnts.append(nextJ)
			else:
				nextJ = nextJ[0]
				aimAtTrans = createNode('transform')
				delete(pointConstraint(nextJ, aimAtTrans)) # Snap to location


				# Assign values from attributes to orientation settings 
				wut = [
					'vector', 	# -3 = Z-
					'vector', 	# -2 = Y-
					'vector', 	# -1 = X-
					'object', 	# 0 = Object
					'vector', 	# 1 = X
					'vector', 	# 2 = Y
					'vector', 	# 3 = Z
					'none', 	# 4 = World
				]
				wuv = [
					[0,0,-1], 	# -3 = Z-
					[0,-1,0], 	# -2 = Y-
					[-1,0,0], 	# -1 = X-
					[0,1,0], 	# 0 = Object
					[1,0,0], 	# 1 = X
					[0,1,0], 	# 2 = Y
					[0,0,1], 	# 3 = Z
					[0,1,0] 	# 4 = World
				]
				upV=[
					[0,1,0], 	# Y
					[0,-1,0],	# Y-
					[0,0,1], 	# Z
					[0,0,-1],	# Z-
				]

				if jnt.worldOrientUp.get() == 0 and jnt.worldOrientObject.get():
					aimConst = aimConstraint(aimAtTrans, jnt,
						maintainOffset=0,
						aimVector=[1,0,0],
						upVector=upV[jnt.up.get()],
						worldUpType=wut[jnt.worldOrientUp.get()+3],
						worldUpVector=wuv[jnt.worldOrientUp.get()+3],
						worldUpObject=jnt.worldOrientObject.get()
						)
				else:
					aimConst = aimConstraint(aimAtTrans, jnt,
						maintainOffset=0,
						aimVector=[1,0,0],
						upVector=upV[jnt.up.get()],
						worldUpType=wut[jnt.worldOrientUp.get()+3],
						worldUpVector=wuv[jnt.worldOrientUp.get()+3],
						)

				delete(aimAtTrans)
		delete(pntList)
		delete(transList)

		if roots:
			for root in roots:
				makeIdentity(root, apply=1, t=1, r=1, s=1, n=0, pn=1)

		for jnt in endJnts:
			rjt(jnt)

		select(selection)

		# delete(pntConsts)
		# delete(aimConsts)
		# delete(transList)
		# delete(aimAtList)



	def buildOrientUpObject(self):
		selection = ls(sl=1)

		# Make sure joints selected are initialized
		for sel in selection:
			if not sel in self.skeleNode.joints.get():
				raise Exception('One or more objects selected are not initialized joints. %s' % sel)

		# Create the up control
		trans = createNode('transform', n='%s_upObject' % selection[0], p=self.fitRigsGroup)
		trans.displayHandle.set(1, k=1)
		trans.scaleX.set(l=1, k=0)
		trans.scaleY.set(l=1, k=0)
		trans.scaleZ.set(l=1, k=0)

		constList = []
		for sel in selection:
			val = 5
			upAve = createNode('transform',  n='%s_upAve' % sel, p=sel)
			if sel.worldOrientUp.get() == -3:
				upAve.translateZ.set(-val)
			if sel.worldOrientUp.get() == -2:
				upAve.translateY.set(-val)
			if sel.worldOrientUp.get() == -1:
				upAve.translateX.set(-val)
			if sel.worldOrientUp.get() == 1:
				upAve.translateX.set(val)
			if sel.worldOrientUp.get() == 2:
				upAve.translateY.set(val)
			if sel.worldOrientUp.get() == 3:
				upAve.translateZ.set(val)
			constList.append(upAve)

		# constList.append(trans)
		delete(pointConstraint(constList, trans))
		# delete(pointConstraint(constList))

		for i, sel in enumerate(selection):
			rb.boneIndic(trans, sel, blackGrey=1)
			# if len(selection)>2:
			# 	if not i==0:
			# 		rb.meshIndic([trans, selection[i-1], sel], group=trans, color=(0.5,0.5,0.5) )
			
			sel.worldOrientUp.set(0)
			trans.message.connect(sel.worldOrientObject, f=1)
		
		delete(constList)
		
		select(trans)


	def outputSkeleton(self):
		# Creates a single joint heirarchy based on combining all bind joints in each subrig
		# Gets preserved between builds
		print 'Output Skeleton...'
		selection = ls(sl=1)

		if not objExists('rigNodeSet'):
			raise Exception('No rigs built yet. (rigNodeSet not found)')

		rigNodeSet = ls('rigNodeSet')[0]

		outputJoints = []
		outputMembers = []

		# check bind joints for clashing nodes
		testList = []
		bindSet = nt.ObjectSet('bindSet')
		for bind in bindSet:
			if bind.nodeName() in testList:
				raise Exception('Clashing nodes: %s' % bind)
			else:
				testList.append(bind.nodeName())

		# Convert set to list
		rigNodes = []
		for rigNode in rigNodeSet:
			# if self.dev: print rigNode
			if isinstance(rigNode, nt.Locator) or isinstance(rigNode, nt.Transform):
				rigNodes.append(rigNode)


		for rigNode in rigNodes:
			# Create subskeleton
			# if self.dev: print rigNode
			rigJoints = [] # Output joints within rig

			# print rigNode

			if not hasAttr(rigNode, 'exportJoints'):
				addAttr(rigNode, at='message', k=0, h=1, ln='exportJoints', multi=1, indexMatters=0)
			
			if not hasAttr(rigNode, 'bindList'):
				warning('rigNode has no bindList attribute: %s' % rigNode)
			
			else:
				bindList = rigNode.bindList.get()
				
				# print bindList
				
				if not hasAttr(rigNode, 'bindEnd'):
					doBindEnd = False
				else:
					doBindEnd = False
					# doBindEnd = rigNode.bindEnd.get()
					
				if doBindEnd:

					if not hasAttr(bindList[-1], 'bindEndJoint'):
						addAttr(bindList[-1], ln='bindEndJoint', at='message')
					if not bindList[-1].bindEndJoint.get():
						bindEnd = createNode('joint', n='%s_END' % bindList[-1].nodeName(), p=bindList[-1])
						bindEnd.message.connect(bindList[-1].bindEndJointint)
						bindEnd.tx.set(5)
						bindEnd.hide()
					else:
						bindEnd = bindList[-1].bindEndJoint.get()
					
					bindList.append(bindEnd)

				for i, jnt in enumerate(bindList): # For each Bind
					# Determine if joint needs to be created
					new = True
					name = jnt.nodeName().replace('BND', 'OUTPUT')
					if name == jnt.nodeName():
						name = jnt.nodeName().replace('BIND', 'OUTPUT')
					if name == jnt.nodeName():
						name = jnt.nodeName().replace('bind', 'OUTPUT')
					if name == jnt.nodeName():
						name = '%s_%s' % (jnt.nodeName(), 'OUTPUT')

					# Check if joint needs to be created
					if objExists(name):
						# if len(ls(name)) > 1:
						# 	raise Exception('Names Clashing: %s' % name)
						if len(ls(name)) == 1:
							# If joint already exists, remove constraint
							if hasAttr((ls(name))[0], 'exportJoint'):
								outJnt = ls(name)[0]
								new = False
								rb.removeMatrixConstraint(outJnt)
					# If new joint required, build
					if new:
						# Output Joint
						outJnt = createNode('joint', n=name)
						addAttr(outJnt, at='message', k=0, h=1, ln='exportJoint')
						col.setViewportRGB(outJnt, (0.052, 0.026, 0.100))
						outJnt.radius.set(0.1)
						outJnt.attr('type').set(18) # other
						# outJnt.drawLabel.set(1)
						if self.dev: print outJnt

					
					# outJnt.otherType.set(jnt.otherType.get())
					
					
					# if self.dev: print outJnt
					rigJoints.append(outJnt)
					# Create Constraint
					# outJnt.jointOrient.set(j.jointOrient.get())
					rb.matrixConstraint(jnt, outJnt, t=1, r=1, s=1, offset=0)
					outJnt.jointOrientX.set(k=1)
					outJnt.jointOrientY.set(k=1)
					outJnt.jointOrientZ.set(k=1)
					outJnt.segmentScaleCompensate.set(k=1)


					if not i==0:
						try:
							parent(outJnt, rigJoints[i-1])
						except:
							warning('Joints parenting error -- parent target %s[%s], search index: %s' % (rigJoints[-1], rigJoints.index(rigJoints[-1]), (i-1)))
					else:
						parent(outJnt, self.skeleNode.outputGroup.get())

						
					if not outJnt in rigNode.exportJoints.get():
						outJnt.exportJoint.connect(rigNode.exportJoints, na=1, f=1)
						
						outputJoints.append(outJnt)
					
					col.resetOutlinerRGB(outJnt)
					outputMembers.append(outJnt)


		
		# Connect joints from disparate rigGroups using heirarchy input
		for rigNode in rigNodes:

			# Get parent index
			index = -1
			if rigNode.fitNode.get():
				index = rigNode.fitNode.get().parentSocketIndex.get()

			if hasAttr(rigNode, 'heirarchy'):
				rigNodeParent = rigNode.heirarchy.inputs()
				if rigNodeParent:
					if rigNodeParent[0].hasAttr('rigType'):

						rigNodeParent = rigNodeParent[0]

						# print 'Top Joint: %s' % rigNode.exportJoints.get()[0]
						if not len(rigNode.exportJoints.get()):
							warning('No joints found on rig: %s' % rigNode)
							continue

						# Check to make sure top node is joint
						if not isinstance(rigNode.exportJoints.get()[0], nt.Joint):
							raise Exception('Top joint on rig is not a joint: %s' % rigNode.exportJoints.get()[0])
						
						# print 'End Joint: %s' % rigNodeParent[0].exportJoints.get()[index]
						if not len(rigNodeParent.exportJoints.get()):
							warning('No joints found on rig: %s' % rigNodeParent)
							continue

						if not len(rigNodeParent.exportJoints.get()) > index:
							warning('Rig node: %s doesn\'t have a joint at index: %s' % (rigNodeParent, index))
							index = -1
							
						if not isinstance(rigNodeParent.exportJoints.get()[index], nt.Joint):
							raise Exception('End joint on rig parent is not a joint: %s' % rigNodeParent.exportJoints.get()[index])

						print rigNode.exportJoints.get()[0]
						print rigNodeParent.exportJoints.get()[index]
						parent(rigNode.exportJoints.get()[0], rigNodeParent.exportJoints.get()[index])




		# finalize
		# Check for malignant nodes
		for node in listRelatives(self.skeleNode.outputGroup.get(), allDescendents=True):
			if not node in outputMembers:
				col.setOutlinerRGB(node, (1,0,0))

		for outputJnt in outputMembers:
			outputJnt.jointOrient.set((0,0,0))
			outputJnt.segmentScaleCompensate.set(0)
		
		for outputJnt in outputMembers:
			outputJnt.jointOrient.set((outputJnt.rotate.get()))

		# Create set from bind joints
		if outputJoints:
			if objExists('outputSet'):
				delete(ls('outputSet'))
			outputSet = sets(outputJoints, n='outputSet')
			# else:
			# 	outputSet = sets( 'outputSet', e=True, forceElement=outputJoints )

		# if self.dev:
		# 	for jnt in outputJoints:
		# 		cube = polyCube(ch=False, h=1, d=1, n='%s' % jnt.nodeName.replace('OUTPUT', 'CUBE'))
		# 		parent(cube, jnt)
		# 		cube.t.set(0,0,0)
		# 		cube.r.set(0,0,0)
		# 		cube.s.set(1,1,1)
		select(selection)

		print 'Output Skeleton Completed.'


	def buildRigs(self, fitRigs=None):
		with UndoChunk():
			# Collect fitRigs in skelenode
			if fitRigs is None:
				fitRigs = self.skeleNode.fitRigsList.get()

			self.globalMove = self.skeleNode.globalMove.get()


			# Error Check
			# Naming
			globalNamesCheck = []

			for fr in fitRigs:
				if fr.side.get() != 2: # If not right side
					# if self.dev: print fr
					for otherFitRig in globalNamesCheck:
						if otherFitRig.globalName.get() == fr.globalName.get():
							raise Exception('FitRigs have clashing Global Name (attribute): %s, %s' % (fr, otherFitRig))
					globalNamesCheck.append(fr)


			# Debug vis
			if not hasAttr(self.globalMove, 'debugVis'):
				addAttr(self.globalMove, ln='debugVis', at='short', min=0, max=1, dv=1, k=0)
				self.globalMove.debugVis.set(cb=1)

			self.disconnectRigHeirarchy()
			self.disconnectOutputSkeleton(raiseExc=False)

			# Build Rigs
			rigNodes = [] # Gather result rigNodes
			buildList = []

			for fitNode in fitRigs:
				build=True
				if hasAttr(fitNode, 'build'):
					if not fitNode.build.get():
						build=False
				
				if build:
					if self.dev: print fitNode
					if fitNode.rigType.get() == 'footRoll' or fitNode.rigType.get() == 'hand':
						pass
					else:
						buildList.append(fitNode)

			if len(buildList) == 0:
				raise Exception('No fitRigs found.')
			print '\n Building:'
			for b in buildList: print b
			print '\n'

			for fitNode in buildList:
				# rigParent = fitNode.getParent() # Get fitNode transform heirarchy
				fitInstance = fitRig(fitNode = fitNode) # Initiate Fitnode class
				
				rigNode = fitInstance.build() # Build rig

				if rigNode:
					if self.dev: print rigNode
					rigNodes.append(rigNode)

					# Connect debug vis
					self.globalMove.debugVis >> rigNode.debugVis
					rigNode.debugVis.set(k=0, cb=0)


			self.rigHeirarchy()

			# Hide fitrigGroup
			hide(self.skeleNode.fitGroup.inputs()[0])
			self.skeleNode.rigGroup.inputs()[0].visibility.set(1)

			# attrName = '%sVis' % rigNode.fitNode.inputs()[0].globalName.get()
			# if not hasAttr(self.globalMove, attrName):
			# 	addAttr(self.globalMove, ln=attrName, at='short', k=1, min=0, max=1, dv=1)
			# 	self.globalMove.attr(attrName).set(k=0, cb=1)
			# self.globalMove.attr(attrName) >> rigNode.allVis

			# self.outputSkeleton()

	def disconnectOutputSkeleton(self, raiseExc=True):	
		# Disconnect output joints
		if objExists('outputSet'):
			if len(sets('outputSet', q=1)): 
				for jnt in sets('outputSet', q=1):
					try:
						rb.removeMatrixConstraint(jnt)
					except:
						warning('Remove Matrix Constraint failed on joint: %s' % jnt)
		else:
			if raiseExc:
				raise Exception('Output set not found.')

	def disconnectRigHeirarchy(shelf):
		if objExists('rigNodeSet'):
			if len(sets('rigNodeSet', q=1)):
				for rigNode in sets('rigNodeSet', q=1):
					if isinstance(rigNode, nt.Locator):
						rigGroup = rigNode.rigGroup.get()
						try:
							rb.removeMatrixConstraint(rigGroup)
						except:
							warning('Remove Matrix Constraint failed on rigGroup: %s' % rigGroup)


	def rigHeirarchy(self):
		if self.dev: print '\nrigHeirarchy'
		# Connect Rigs
		# for rigNode in self.skeleNode.rigNodes.get():
		rigNodeHeirarchyTypes=[
		'chain',
		'aimIK',
		'bezierIK',
		'poleVectorIK'
		]

		# For each rigNode
		for rigNode in ls('rigNodeSet')[0]:
			print rigNode
			if isinstance(rigNode, nt.Locator) or isinstance(rigNode, nt.Transform):
				# Add heirarchy attribute
				if not hasAttr(rigNode, 'heirarchy'):
					addAttr(rigNode, ln='heirarchy', at='message', k=1)

				fitNode = rigNode.fitNode.get()
				if not fitNode:
					warning('Heirarchy could not be determined for rig: %s' % rigNode)
					continue
				# If fitNode type is valid
				if fitNode.rigType.get() in rigNodeHeirarchyTypes:
					
					# get heirarchy
					fitParent = fitNode.getParent()
					if fitParent:
						# get parent rigNode
						if hasAttr(fitParent, 'rigNode'):

							if fitParent.rigNode.get():
								# Determine which socket to parent under
								# User opportunity to adjust socket to use (if not found default to last socket [-1])
								parentSocketIndex = -1
								if hasAttr(fitNode, 'parentSocketIndex'):
									parentSocketIndex = fitNode.parentSocketIndex.get()
								
								try:
									socket = fitParent.rigNode.outputs()[0].socketList.get()[parentSocketIndex]

									# Matrix constraint
									inheritScale = True
									try:
										inheritScale = fitNode.inheritScale.get()
									except:
										pass
									if inheritScale:
										rb.matrixConstraint(socket, rigNode.rigGroup.get(), t=1, r=1, s=1, offset=1)
									else:
										rb.matrixConstraint(socket, rigNode.rigGroup.get(), t=1, r=1, s=0, offset=1)

									if not hasAttr(fitParent.rigNode.get(), 'heirarchy'):
										addAttr(fitParent.rigNode.get(), ln='heirarchy', at='message', k=1)
									
									if not isConnected(fitParent.rigNode.get().heirarchy, rigNode.heirarchy):
										fitParent.rigNode.get().heirarchy.connect(rigNode.heirarchy, f=1)

									if fitParent.rigType.get() == 'aimIK':
										if fitParent.ikEndInherit.get() == 1:
											# rb.matrixConstraint(rigNode.socketList.get()[0], fitParent.rigNode.get().endConst.get())
											rb.matrixConstraint(rigNode.socketList.get()[0], fitParent.rigNode.get().iKCtrlEnd.get().const.get())
											fitParent.rigNode.get().ikVis.set(0)
								except:
									pass


	def autoSkinSetup(self, mesh=None):
		pass
		'''
		Sets up the layers for easy weight painting using ngSkinTools
		In progress
		'''
		# from ngSkinTools.mllInterface import MllInterface

		# # Create class instance
		# mll = MllInterface()
		# mll.setCurrentMesh(mesh)

		# mll.initLayers()

		# # Batch data update mode, which puts layers in suspended state
		# # mll.beginDataUpdate()
		# with mll.batchUpdateContext()
		# 	for rigNode in rigNodeSet():

				
		# 		# Create a new skin layer for each rig node's bind set
		# 		bindJoints = rigNode.bindList.get()
		# 		lyrID = mll.createLayer(rigNode.globalName.get())
		# 		# Disable Layer
		# 		mll.setLayerEnabled(lyrID, False)


		# 		# Mirror Layer
		# 		mll.mirrorLayerWeights(lyrID)

				# mll.setInfluenceWeights(id,0,[0.0,0.0,1.0,1.0])

				# Seems to be missing commands for setting weights based on assigned joints
		# mll.endDataUpdate()

	def jointLabels(self, onOffToggle=2):
		self.joints = self.skeleNode.joints.get()
		for j in self.joints:
			if onOffToggle == 2:
				onOffToggle = not j.drawLabel.get() # Toggle
			j.drawLabel.set(onOffToggle)

	#===================================================================================================
	#===================================================================================================
	#===================================================================================================
	#===================================================================================================

# =================================================================================
# =================================================================================

class fitRig:
	'''
	Class for fitRigs

	TODO:
	color editing
	Unlink individual fitrigs from length-based-scaling
	Automate rig parenting (heirarchy sux)

	'''
	dev = 1
	hidden = not dev
	# sideStr = [unicode('_M'), unicode('_L'), unicode('_R'), unicode('')]
	sideStr = ['_M', '_L', '_R', '']

	def __init__(self, fitNode=None, joints=None, rigType=None, rigParent=None):
		# =================================== GATHER SKELENODE INFO ===================================
		self.skeleNode = ls('skeleNode_META')[0]
		self.globalMove = self.skeleNode.globalMove.get()
		self.fitSkeletonGroup = self.skeleNode.fitSkeletonGroup.get()
		self.fitGroup = self.skeleNode.fitGroup.get()
		self.fitRigsGrp = self.skeleNode.fitRigsGroup.get()
		self.rigGroup = self.skeleNode.rigGroup.get()
		self.fitHeirarchy = self.skeleNode.fitHeirarchy.get()


		# Initiate fitnode if existing fitnoe not specified
		if fitNode is None:
			if rigType is None:
				raise Exception('No data specified.')
			self.getColors()
			self.fitNode = self.createFitNode(joints, rigType)
		# Otherwise, use the node specified and skip creation
		else:
			self.fitNode = fitNode
			self.getColors()

		# Initialize Color data


	def build(self, fitNode=None):
		if fitNode is None:
			fitNode = self.fitNode
		print fitNode
		rigNode = None
		
		if fitNode.rigType.get() == 'aimIK':
			# if self.dev: reload(buildRig_twoPointIK)
			# rigNode = buildRig_twoPointIK.rigBuildTwoPointIK(fitNode)
			import aimIK
			if self.dev: reload(aimIK)
			rigNode = aimIK.aimIK(fitNode).rigNode
		
		elif fitNode.rigType.get() == 'bezierIK':
			# if self.dev: reload(buildRig_spline)
			# rigNode = buildRig_spline.rigBuildSpline(fitNode)
			import bezierIK
			if self.dev: reload(bezierIK)
			rigNode = bezierIK.bezierIK(fitNode).rigNode
		
		elif fitNode.rigType.get() == 'poleVectorIK':
			import threePointIK
			if self.dev: reload(threePointIK)
			rigNode = threePointIK.threePointIK(fitNode).rigNode
			# if self.dev: reload(buildRig_threePointIK)
			# rigNode = buildRig_threePointIK.rigBuildThreePointIK(fitNode)
		
		elif fitNode.rigType.get() == 'chain':
			if fitNode.rigStyle.get(asString=True) == 'fk':
				import chain
				if self.dev: reload(chain)
				rigNode = chain.chain(fitNode).rigNode
			else:
				import bezierChain
				if self.dev: reload(bezierChain)
				rigNode = bezierChain.bezierChain(fitNode).rigNode
			
		elif fitNode.rigType.get() == 'footRoll':
			pass
			
		else:
			warning('Rig type: %s not supported.' % fitNode.rigType.get())


		return rigNode
	
	

	def getColors(self):
		# Replace later
		self.colorsFK = [
		[0.700, 1.000, 0.410], # M
		[0.150, 0.800, 1.000], # L
		[0.950, 0.140, 0.460], # R
		]
		self.colorsIK = [
		[1.000, 0.655, 0.225], # M
		[0.686, 0.664, 1.300], # L
		[1.300, 0.481, 0.411], # R
		]
		self.colorsOffset = [
		[0.000, 0.000, 0.000], # M
		[0.000, 0.000, 0.000], # L
		[0.000, 0.000, 0.000], # R
		]
		self.colorJoints = [
		[0.700, 1.000, 0.410], # M
		[0.150, 0.800, 1.000], # L
		[0.950, 0.140, 0.460], # R
		]


	def createFitNode(self, joints, rigType):

		loadPlugin( 'matrixNodes.mll', qt=True )
		freezeList = []
		# =================================== ERROR CHECKS ===================================
		for i, j in enumerate(joints):
			if self.dev: print 'Joint %s: %s' % (i, j)

			# PyNode check
			if not isinstance(j, PyNode):
				raise Exception('Object is not a PyNode: %s' % j)
			
			# Joint check
			if not objectType(j, isType='joint'):
				raise Exception('Object is not a joint: %s' % j)


			# # Heirarchy check?
			# if not i==0:
			# 	if self.dev:
			# 		print 'JOINT: %s' % j
			# 		print 'PARENT: %s' % j.getParent()

			# 	if not j.getParent() == joints[i-1]:
			# 		raise Exception('Joints not in heirarchy: %s' % j)
			# 	else:
			# 		print 'HEIRARCHY VERIFIED'

			# Name clash check
			if len(ls(j.nodeName())) > 1:
				raise Exception('Clashing nodes: %s' % j)


		# NAMING
		side = joints[0].side.get()
		suffix = joints[0].shortName().split('_')[0]

		if self.dev: 
			print '\nNAMING:'
			print 'SIDE: %s' % side
			print 'SUFFIX: %s\n' % suffix

		namesDict = {
		'fitNode': {'desc': 'fitNode', 		'warble': 'meta',	'side': side, 	'other': [suffix, rigType] },
		}


		# fitHeirarchy_GRP
		# fitNode
		# fitNodeSet
		# vecProd # Naming handled further in code

		names = rb.constructNames(namesDict)



		#  =================================== FIT NODE =================================== 
		# if objExists(names.get('fitNode', 'rnm_fitNode')):
		# 	# Check to see if the current fitNode is connected to the same joints here
		# 	# oldFitNode = ls(names.get('fitNode', 'rnm_fitNode'))[0]
		# 	# if hasAttr(oldFitNode, 'jointsList'):
		# 	# 	oldJoints = oldFitNode.jointsList.get()
		# 	# 	for j in joints:
		# 	# 		if not j in oldJoints:

		# 	deleteFitRig(ls(names.get('fitNode', 'rnm_fitNode'))[0])
			
		# Use a transform for manual rig heirarchy
		# To do - Check joint heirarchy and run that way
		if not objExists('fitHeirarchy_GRP'):
			fitHeirarchy_GRP = createNode('transform', n='fitHeirarchy_GRP', p=self.fitGroup)
		else:
			fitHeirarchy_GRP = ls('fitHeirarchy_GRP')[0]
		fitNode = createNode('transform', n=names.get('fitNode', 'rnm_fitNode'), p=fitHeirarchy_GRP)

		self.fitNode = fitNode
		if self.dev: print fitNode
		move(fitNode, xform(joints[0], q=1, rp=1, ws=1), rpr=1, ws=1)
		xform(fitNode, ro=xform(joints[0], q=1, ro=1, ws=1), ws=1)
		rb.matrixConstraint(joints[0], fitNode, t=1, r=1, s=0, offset=1)
		self.fitNode.displayHandle.set(1)
		self.fitNode.selectHandleX.set(k=1)
		self.fitNode.selectHandleY.set(k=1)
		self.fitNode.selectHandleZ.set(k=1)
		col.setOutlinerRGB([fitNode], [0.5,1,0.5])
		col.setViewportRGB([fitNode], [0.5,1,0.5])
		
		# Or use network node for ui and clear outliner
		# fitNode = createNode('network', n=names.get('fitNode', 'rnm_fitNode'))
		
		# Or use instanced shape node easy access
		# fitNode = createNode('locator', n=names.get('fitNode', 'rnm_fitNode'), p=self.fitRigsGrp)
		# fitNode.hide()
		# attrs = ['lpx','lpy','lpz','lsx','lsy','lsz']
		# for attribute in attrs:
		# 	fitNode.attr(attribute).set(l=1, cb=0, k=0)

		# attach to skeleNode
		if not hasAttr(self.skeleNode, 'fitRigsList'):
			addAttr(self.skeleNode, ln='fitRigsList', at='message', multi=1, k=1, h=self.hidden, indexMatters=0)
		addAttr(fitNode, ln='skeleNode', at='message', k=1, h=self.hidden)
		fitNode.skeleNode.connect(self.skeleNode.fitRigsList, nextAvailable=1)


		# FitNode Set
		if not objExists('fitNodeSet'):
			fitNodeSet = sets([fitNode], n='fitNodeSet')
		else:
			fitNodeSet = sets('fitNodeSet', e=True, forceElement=fitNode)


		# ---------- Attributes ----------
		if self.dev: print 'ATTRIBUTES:'
		# RIGTYPE
		addAttr(fitNode, h=self.hidden, dt='string', ct='verification', ln='rigType')
		fitNode.rigType.set(rigType, l=1)
		# BUILD
		addAttr(fitNode, h=0, dv=1, min=0, max=1, at='short', ct='inputs', ln='build', k=1)
		# BIND
		addAttr(fitNode, h=0, dv=1, min=0, max=1, at='short', ct='inputs', ln='bind', k=1)
		# MIRROR
		addAttr(fitNode, k=1, at='short', min=0, max=1, ct='inputs', ln='inheritScale', dv=1)
		if not hasAttr(fitNode, 'mirror'):
			addAttr(fitNode, h=0, dv=1, min=0, max=1, at='short', ln='mirror', k=1)
		# PARENT SOCKET INDEX
		addAttr(fitNode, k=1, dv=-1, min=-1, at='short', ln='parentSocketIndex')
		# SIDE
		addAttr(fitNode, k=1, at='enum', ct='naming', ln='side', enumName='Center:Left:Right:None', dv=side)


		# # naming

		# GLOBAL NAME
		addAttr(fitNode, k=1, dt='string', ct='naming', ln='globalName')

		globalName = str(joints[0].nodeName())
		for sideStr in self.sideStr:
			if sideStr in globalName:
				globalName = globalName.replace(sideStr, '')
				
		fitNode.globalName.set(globalName)

		if self.dev: print 'GLOBAL NAME: %s' % globalName
		
		# subName
		for i, j in enumerate(joints):
			addAttr(fitNode, k=1, dt='string', ct='naming', ln='subName%s' % i)
			subName = j.nodeName()
			for sideStr in self.sideStr:
				if sideStr in subName:
					subName = subName.replace(sideStr, '')

			fitNode.attr('subName%s' % i).set(subName)
			if self.dev: print 'SUB NAME %s: %s' % (i, subName)

		# # controls
		rb.cbSep(fitNode)
		addAttr(fitNode, k=1, dv=1, min=0, max=1, at='short', ct='control', ln='controlsVis')
		# # shapes
		addAttr(fitNode, k=1, dv=1, min=0, max=1, at='short', ct='control', ln='shapesVis')
		addAttr(fitNode, k=1, dv=1, min=0, ct='input', ln='controlScale')
		addAttr(fitNode, k=1, ct='output', ln='controlScaleResult')
		self.fitGroup.shapesVis >> self.fitNode.shapesVis
		self.fitGroup.controlsVis >> self.fitNode.controlsVis
		self.fitNode.shapesVis.set(k=0)
		self.fitNode.controlsVis.set(k=0)


		# # lists
		rb.cbSep(fitNode)
		addAttr(fitNode, k=1, at='message', ct=['selection', 'input'], multi=1, ln='jointsList')
		# # input joints
		for i, j in enumerate(joints):
			j.message >> fitNode.jointsList[i]
		
		addAttr(fitNode, k=1, h=self.hidden, at='message', ct='selection', ln='shapesList')
		addAttr(fitNode, k=1, h=self.hidden, at='message', ct=['selection', 'hidden'], ln='deleteList')

		addAttr(fitNode, k=1, dt='string', ln='visCategory')

		nodeList = []

		# # VectorX results
		# rb.cbSep(fitNode)
		vectorX = []
		for i, j in enumerate(joints):
			suffix = fitNode.attr('subName%s' % i).get(asString=1)
			namesList = [
			{'name': 'vecProd', 		'warble': 'vp',		'side': side, 	'other': [suffix, rigType] },
			]
			names = constructNames(namesList)

			addAttr(fitNode, k=0, h=self.hidden, at='compound', ct='output', numberOfChildren=3, ln='jointVector%s' % i)
			addAttr(fitNode, k=0, h=self.hidden, at='float', ln='jointVector%sX' % i, parent='jointVector%s' % i)
			addAttr(fitNode, k=0, h=self.hidden, at='float', ln='jointVector%sY' % i, parent='jointVector%s' % i)
			addAttr(fitNode, k=0, h=self.hidden, at='float', ln='jointVector%sZ' % i, parent='jointVector%s' % i)
			# fitNode.attr('jointVector%sX' % i).set(k=0, cb=1)
			# fitNode.attr('jointVector%sY' % i).set(k=0, cb=1)
			# fitNode.attr('jointVector%sZ' % i).set(k=0, cb=1)
			vecProd = createNode('vectorProduct', n=names.get('vecProd', 'rnm_vecProd'))
			nodeList.append(vecProd)
			vectorX.append(vecProd)
			connectAttr(j.worldMatrix[0], vecProd.matrix)
			vecProd.input1.set([1,0,0])
			vecProd.operation.set(3)
			connectAttr(vecProd.outputX, fitNode.attr('jointVector%sX' % i))
			connectAttr(vecProd.outputY, fitNode.attr('jointVector%sY' % i))
			connectAttr(vecProd.outputZ, fitNode.attr('jointVector%sZ' % i))



		fitNode.scaleX.connect(fitNode.controlScale)
		fitNode.scaleX.connect(fitNode.scaleY)
		fitNode.scaleX.connect(fitNode.scaleZ)

		# Delete List
		for node in nodeList:
			addAttr(node, k=1, h=self.hidden, at='message', ln='fitNode')
			fitNode.deleteList.connect(node.fitNode)
		# Freeze List
		rb.lockAndHide([fitNode], ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sy', 'sz'])



		'''
		'''
		#  ================================= Specific attributes =================================

		# SIDE SPECIFIC
		side = fitNode.side.get()
		col.setOutlinerRGB([fitNode], self.colorJoints[side])
		col.setViewportRGB([fitNode], self.colorJoints[side])

		return fitNode

	#===================================================================================================
	#===================================================================================================

	def mirrorFitRig(self, attributes):
		'''Make this relevant'''
		joints = fitNode.jointsList.get()
		if self.dev:
			print 'Joints:'
			print joints

		# Error check
		if not all(self.hasMirror(j) for j in joints):
			print 'Failed Joints: '
			print failList
			raise Exception('Not all joints associated with fitNode have mirrored joints connected.')
			# Add options for specifying joints to be mirrored?

		# Get mirror joints
		mirrorJoints = []
		for j in joints:
			mirrorJoints.append(j.mirror.get())


		if not hasAttr(fitNode, 'mirror'):
			addAttr(fitNode, ln='mirror', at='message', k=1)
		if not hasAttr(mirrorFitNode, 'mirror'):
			addAttr(mirrorFitNode, ln='mirror', at='message', k=1)
		mirrorFitNode.mirror.connect(fitNode.mirror)

		if self.dev: 
			print 'Mirrored Joints:'
			print mirrorJoints

		if len(attributes):
			for attribute in attributes:
				fitNode.attr(attribute).connect(mirrorFitNode.attr(attribute))
				# mirrorFitNode.attr(attribute).set(k=0, cb=0)

		# for shape in fitnode.shapeList.get():



		if self.dev: print 'Mirror Fit Node: %s' % mirrorFitNode
		return mirrorFitNode

	#===================================================================================================
	#===================================================================================================

	def hasMirror(self, jnt):
		'''Determines if there are any objects in the list that do not have 'mirrored' nodes (via message connection to mirror attribute)
		'''
		# if not objectType(jnt, isType='joint'):
		# 	raise Exception('Object is not a joint: %s' % jnt)
		r = False
		if hasAttr(jnt, 'mirror'):
			if len(jnt.mirror.inputs()) == 1 or len(jnt.mirror.outputs()) == 1:
				r = True
		return r


	def mirrorFitShapes(self):
		pass
	

	#===================================================================================================
	#===================================================================================================
class fkHeirarchy(fitRig):
	def __init__(self, joints=None, fitSkele=None, fitNode=None, mirrorFitRig=False, *args, **kwargs):
		if fitSkele is None:
			try:
				fitSkele = ls('skeleNode_META')[0]
			except:
				raise Exception('Fit Skeleton node not found.')

		self.fitSkeleton = fitSkele

		# ERROR CHECKS
		self.rigType = 'chain'
		if self.dev: print 'RUNNING CHAIN RIG'
		if self.dev: print 'CHECKING FOR ERRORS...'

		# FITNODE GLOBAL ATTRIBUTES
		fitNode = fitRig.__init__(self, joints=joints, rigType='chain')
		if self.dev:
			print 'FITNODE'
			print self.fitNode

		# FITNODE SPECIFIC ATTRIBUTES
		self.fitNode = self.chainInit(self.fitNode, mirrorFitRig=mirrorFitRig)

		# MIRRORING
		# Automatically mirror if all mirror joints found (and mirroring hasn't already been done)
		if not mirrorFitRig and all(self.hasMirror(j) for j in joints):
			if self.dev: print 'Apply Mirroring'
			mirrorFitNode = self.mirrorFitRig(self.fitNode)


	def fkHeirarchyInit(self, fitNode, mirrorFitRig=False):
		'''Takes three points and converts them into fkIk rig
		To Do:
		Debug mode
		Spline limit addon

		'''
		# fitNode = self.fitNode


		#===================================================================================================
		#===================================================================================================
		# Start data
		jnts = fitNode.jointsList.get()
		settings = self.fitGroup
		fitRigsGrp = self.fitRigsGrp

		# Naming
		globalName = fitNode.globalName.get()
		subNames = fitNode.subName0.get()
		rigType = fitNode.rigType.get()
		suffix = ''
		side = fitNode.side.get()
		
		# ========================================= Names ==========================================
		names = {
		'fitNode':					'%s_fitNode%s'						% (jnts[0], rigType),
		'grp':						'%s_%s'								% (jnts[0], rigType),
		'vec':						'%s_upVector%s' 					% (rigType, suffix),
		'controlScaleMult':			'%s_ctrlScale_MULT%s' 				% (rigType, suffix),
		'adjustMult':				'%s_adjust_MULT%s' 					% (rigType, suffix),
		'shapesGrp':				'%s_shapes_GRP%s' 					% (rigType, suffix),
		'fkGrp':					'%s_FK_GRP%s' 						% (rigType, suffix),
		'ikGrp':					'%s_IK_GRP%s' 						% (rigType, suffix),
		'fkShape':					'%s_FK_shape%s' 					% (rigType, suffix),
		'ikShape':					'%s_IK_shape%s' 					% (rigType, suffix),
		}
		# names = constructNames(namesList)
		
		# Collections
		nodeList = []
		shapesList = []
		ctrlList = []
		freezeList = []

		# Rig-specific attributes
		rb.cbSep(fitNode)
		
		addAttr(fitNode, ln='rigStyle', at='enum', ct='input', enumName='fk:bezier', keyable=True)

		addAttr(fitNode, ln='offsets', ct='input', at='short', k=1, min=0, max=1, dv=0)
		addAttr(fitNode, ln='multiChain', ct='input', at='short', k=1, min=0, max=1, dv=0)

		addAttr(fitNode, ln='fkShapes', ct='shape', at='message', multi=1, indexMatters=0, keyable=True, h=self.hidden)
		addAttr(fitNode, ln='ikShapes', ct='shape', at='message', multi=1, indexMatters=0, keyable=True, h=self.hidden)
		
		

		jnt0T = xform(jnts[0], q=1, rp=1, ws=1)
		jnt0R = xform(jnts[0], q=1, ro=1, ws=1)
		# MAIN GROUPS
		# Group
		grp = createNode('transform', n=names.get('grp', 'rnm_grp'), p=fitRigsGrp)
		nodeList.append(grp)
		freezeList.append(grp)
		if self.dev: print grp
		move(grp, jnt0T, rpr=1, ws=1)
		xform(grp, ro=jnt0R, ws=1)
		self.fitNode.v.connect(grp.v)
		rb.messageConnect([grp], 'message', fitNode, 'fitGroup')
		# parent(fitNode, grp, r=True, s=True)


# =================================================================================
class lipsFitRig(fitRig):
	
	def __init__(self, joints=None, fitSkele=None, fitNode=None, mirrorFitRig=False, *args, **kwargs):
		if fitSkele is None:
			try:
				fitSkele = ls('skeleNode_META')[0]
			except:
				raise Exception('Fit Skeleton node not found.')

		self.fitSkeleton = fitSkele

		# ERROR CHECKS
		self.rigType = 'lips'
		if self.dev: print 'RUNNING LIPS RIG'
		if self.dev: print 'CHECKING FOR ERRORS...'

		# FITNODE GLOBAL ATTRIBUTES
		fitNode = fitRig.__init__(self, joints=joints, rigType='lips')
		if self.dev:
			print 'FITNODE'
			print self.fitNode

		# FITNODE SPECIFIC ATTRIBUTES
		self.fitNode = self.chainInit(self.fitNode, mirrorFitRig=mirrorFitRig)

		# MIRRORING
		# Automatically mirror if all mirror joints found (and mirroring hasn't already been done)
		if not mirrorFitRig and all(self.hasMirror(j) for j in joints):
			if self.dev: print 'Apply Mirroring'
			mirrorFitNode = self.mirrorFitRig(self.fitNode)


	def chainInit(self, fitNode, mirrorFitRig=False):
		'''Takes three points and converts them into fkIk rig
		To Do:
		Debug mode
		Spline limit addon

		'''
		# fitNode = self.fitNode


		#===================================================================================================
		#===================================================================================================
		# Start data
		jnts = fitNode.jointsList.get()
		settings = self.fitGroup
		fitRigsGrp = self.fitRigsGrp

		# Naming
		globalName = fitNode.globalName.get()
		subNames = fitNode.subName0.get()
		rigType = fitNode.rigType.get()
		suffix = ''
		side = fitNode.side.get()
		
		# ========================================= Names ==========================================
		names = {
		'fitNode':					'%s_fitNode%s'						% (jnts[0], rigType),
		'grp':						'%s_%s'								% (jnts[0], rigType),
		'vec':						'%s_upVector%s' 					% (rigType, suffix),
		'controlScaleMult':			'%s_ctrlScale_MULT%s' 				% (rigType, suffix),
		'adjustMult':				'%s_adjust_MULT%s' 					% (rigType, suffix),
		'shapesGrp':				'%s_shapes_GRP%s' 					% (rigType, suffix),
		'fkGrp':					'%s_FK_GRP%s' 						% (rigType, suffix),
		'ikGrp':					'%s_IK_GRP%s' 						% (rigType, suffix),
		'fkShape':					'%s_FK_shape%s' 					% (rigType, suffix),
		'ikShape':					'%s_IK_shape%s' 					% (rigType, suffix),
		}
		# names = constructNames(namesList)
		
		# Collections
		nodeList = []
		shapesList = []
		ctrlList = []
		freezeList = []

		# Rig-specific attributes
		rb.cbSep(fitNode)
		
		addAttr(fitNode, ln='rigStyle', at='enum', ct='input', enumName='fk:bezier', keyable=True)

		addAttr(fitNode, ln='offsets', ct='input', at='short', k=1, min=0, max=1, dv=0)
		addAttr(fitNode, ln='multiChain', ct='input', at='short', k=1, min=0, max=1, dv=0)

		addAttr(fitNode, ln='fkShapes', ct='shape', at='message', multi=1, indexMatters=0, keyable=True, h=self.hidden)
		addAttr(fitNode, ln='ikShapes', ct='shape', at='message', multi=1, indexMatters=0, keyable=True, h=self.hidden)
		
		

		jnt0T = xform(jnts[0], q=1, rp=1, ws=1)
		jnt0R = xform(jnts[0], q=1, ro=1, ws=1)

		# MAIN GROUPS
		# Group
		grp = createNode('transform', n=names.get('grp', 'rnm_grp'), p=fitRigsGrp)
		nodeList.append(grp)
		freezeList.append(grp)
		if self.dev: print grp
		move(grp, jnt0T, rpr=1, ws=1)
		xform(grp, ro=jnt0R, ws=1)
		self.fitNode.v.connect(grp.v)
		rb.messageConnect([grp], 'message', fitNode, 'fitGroup')
		# parent(fitNode, grp, r=True, s=True)




		for i, jnt in enumerate(jnts):
			# name objects
			if len(jnts) < 10:
				d = i
			elif len(jnts) < 100:
				d = '%01d' % i
			else:
				d = '%02d' % i

			if self.dev:
				print "\n"
				print d

			# Get input transform space
			jntT = xform(jnt, q=1, rp=1, ws=1)
			jntR = xform(jnt, q=1, ro=1, ws=1)
			# Shapes
			shapesGrp = createNode('transform', n='%s_%s' %(jnt, names.get('shapesGrp', 'rnm_shapesGrp')), p=grp)
			nodeList.append(shapesGrp)
			fitNode.controlScaleResult >> shapesGrp.scaleX
			fitNode.controlScaleResult >> shapesGrp.scaleY
			fitNode.controlScaleResult >> shapesGrp.scaleZ
			move(shapesGrp, jntT, rpr=1, ws=1)
			xform(shapesGrp, ro=jntR, ws=1)
			freezeList.append(shapesGrp)
			parentConstraint(jnt, shapesGrp)
			fitNode.shapesVis >> shapesGrp.v
			if self.dev:
				print shapesGrp
			# VectorY (?)
			vecProd = createNode('vectorProduct', n='%s_%s' %(jnt, names.get('vec', 'rnm_vector')))
			vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
			rb.setAttrsWithDictionary(vecProd, vecSetAttr)
			connectAttr(jnt.worldMatrix[0], vecProd.matrix)
			if not hasAttr(fitNode, 'upVector%s' % d):
				addAttr(fitNode, ln='upVector%s' % d, at='compound', numberOfChildren=3, keyable=0)
				addAttr(fitNode, ln='upVector%sX' % d, at='float', parent='upVector%s' % d, keyable=0)
				addAttr(fitNode, ln='upVector%sY' % d, at='float', parent='upVector%s' % d, keyable=0)
				addAttr(fitNode, ln='upVector%sZ' % d, at='float', parent='upVector%s' % d, keyable=0)
			connectAttr(vecProd.outputX, fitNode.attr('upVector%sX' % d))
			connectAttr(vecProd.outputY, fitNode.attr('upVector%sY' % d))
			connectAttr(vecProd.outputZ, fitNode.attr('upVector%sZ' % d))
			nodeList.append(vecProd)
			if self.dev:
				print vecProd


			if mirrorFitRig:
				unitConvert = createNode('unitConversion')
				unitConvert.conversionFactor.set(-1)
				fitNode.controlScaleResult >> unitConvert.input
				unitConvert.output >> shapesGrp.scaleX
				
			# CONTROL SCALING
			controlScaleMult = createNode('multDoubleLinear', n='%s_%s' % (jnt.shortName(), names.get('controlScaleMult', 'rnm_controlScaleMult'))) # Local * Global Scale
			nodeList.append(controlScaleMult)
			if self.dev: print controlScaleMult
			fitNode.controlScale 		>> controlScaleMult.i1
			settings.controlScale 		>> controlScaleMult.i2

			
			adjustMult = createNode('multDoubleLinear', n='%s_%s' % (jnt.shortName(), names.get('adjustMult', 'rnm_adjustMult')))
			nodeList.append(adjustMult)
			if self.dev: print adjustMult
			adjustMult.i2.set(1.4)
			controlScaleMult.o 	>> adjustMult.i1

			adjustMult.o >> fitNode.controlScaleResult


			fkGrp = createNode('transform', n='%s_%s' % (jnt.shortName(), names.get('fkGrp', 'rnm_fkGrp')), p=shapesGrp)
			nodeList.append(fkGrp)
			fkNode = ls(rb.shapeMaker(name='%s_%s' % (jnt.shortName(), names.get('fkShape', 'rnm_fkShape')), shape=2))[0]
			# fitNode.shapesVis >> fkNode.v
			parent(fkNode, fkGrp)
			fkNode.translate.set([0,0,0])
			fkNode.rotate.set([0,0,90])
			fkNode.scale.set([8,8,8])
			makeIdentity(fkNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
			fkShape = fkNode.getShapes()[0]
			fkNode.message.connect(fitNode.fkShapes, na=1)
			col.setViewportRGB([fkShape], self.colorsFK[side])
			nodeList.append(fkNode)
			shapesList.append(fkNode)
			if self.dev:
				print fkGrp

			ikGrp = createNode('transform', n='%s_%s' % (jnt.shortName(), names.get('ikGrp', 'rnm_ikGrp')), p=shapesGrp)
			nodeList.append(ikGrp)
			fitNode.offsets >> ikGrp.v
			ikNode = ls(rb.shapeMaker(name='%s_%s' % (jnt.shortName(), names.get('ikShape', 'rnm_ikShape')), shape=1))[0]
			# fitNode.shapesVis >> ikNode.v
			parent(ikNode, ikGrp)
			ikNode.translate.set([0,0,0])
			ikNode.rotate.set([0,0,90])
			ikNode.scale.set([10,10,10])
			ikNode.message.connect(fitNode.ikShapes, na=1)
			makeIdentity(ikNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
			ikShape = ikNode.getShapes()[0]
			col.setViewportRGB([ikShape], self.colorsIK[side])
			nodeList.append(ikNode)
			shapesList.append(ikNode)
			if self.dev:
				print ikGrp

		# Finalize
		for ctrl in ctrlList:
			# parent(fitNode, ctrl, s=1, add=1)
			rb.ctrlSetupStandard(ctrl, ctrlSet=None, pivot=False, ro=False, )


		for node in nodeList:
			addAttr(node, k=1, h=self.hidden, at='message', ln='fitNode')
			fitNode.deleteList.connect(node.fitNode)
			# node.fitNode.connect(fitNode.deleteList, nextAvailable=1, f=1)

		return fitNode

	#===================================================================================================
	#===================================================================================================

	def mirrorFitRig(self, fitNode):
		'''
		Digs through and finds mirror joints to each join in provided fitrig, and uses those joints to create a new one.
		Connects result attributes
		'''
		attributes = [
		'controlScale',
		'parentSocketIndex',
		'offsets',
		'globalName',
		'visCategory',
		'inheritScale',
		]

		i=0
		while hasAttr(fitNode, 'subName%s' % i):
			attributes.append('subName%s' % i)
			i = i + 1

		# fitRig.mirrorFitRig()
		

		# Get joints 
		joints = fitNode.jointsList.get()
		if self.dev:
			print 'Joints:'
			print joints

		# Error check
		if not all(self.hasMirror(j) for j in joints):
			print 'Failed Joints: '
			print failList
			raise Exception('Not all joints associated with fitNode have mirrored joints connected.')
			# Add options for specifying joints to be mirrored?

		# Get mirror joints
		mirrorJoints = []
		for j in joints:
			mirrorJoints.append(j.mirror.get())

		if self.dev: 
			print 'Mirrored Joints:'
			print mirrorJoints

		# Create mirrored fitRig class instance (or maintain standard class instance? easy link wouldnt be so bad?)
		mirrorFitRig = chainFitRig(mirrorJoints, self.fitSkeleton, mirrorFitRig=True)

		# Get fitNode
		mirrorFitNode = mirrorFitRig.fitNode

		# connect attributes in this list and hide right side
		for attribute in attributes:
			fitNode.attr(attribute).connect(mirrorFitNode.attr(attribute), force=1)
			# mirrorFitNode.attr(attribute).set(k=0, cb=0)


		if not hasAttr(fitNode, 'mirror'):
			addAttr(fitNode, ln='mirror', at='message', k=1)
		if not hasAttr(mirrorFitNode, 'mirror'):
			addAttr(mirrorFitNode, ln='mirror', at='message', k=1)
		mirrorFitNode.mirror.connect(fitNode.mirror)


		if self.dev: print 'Mirror Fit Node: %s' % mirrorFitNode
		return mirrorFitNode


# =================================================================================
class chainFitRig(fitRig):
	
	def __init__(self, joints=None, fitSkele=None, fitNode=None, mirrorFitRig=False, *args, **kwargs):
		if fitSkele is None:
			try:
				fitSkele = ls('skeleNode_META')[0]
			except:
				raise Exception('Fit Skeleton node not found.')

		self.fitSkeleton = fitSkele

		# ERROR CHECKS
		self.rigType = 'chain'
		if self.dev: print 'RUNNING CHAIN RIG'
		if self.dev: print 'CHECKING FOR ERRORS...'

		# FITNODE GLOBAL ATTRIBUTES
		fitNode = fitRig.__init__(self, joints=joints, rigType='chain')
		if self.dev:
			print 'FITNODE'
			print self.fitNode

		# FITNODE SPECIFIC ATTRIBUTES
		self.fitNode = self.chainInit(self.fitNode, mirrorFitRig=mirrorFitRig)

		# MIRRORING
		# Automatically mirror if all mirror joints found (and mirroring hasn't already been done)
		if not mirrorFitRig and all(self.hasMirror(j) for j in joints):
			if self.dev: print 'Apply Mirroring'
			mirrorFitNode = self.mirrorFitRig(self.fitNode)


	def chainInit(self, fitNode, mirrorFitRig=False):
		'''Takes three points and converts them into fkIk rig
		To Do:w
		Debug mode
		Spline limit addon

		'''
		# fitNode = self.fitNode


		#===================================================================================================
		#===================================================================================================
		# Start data
		jnts = fitNode.jointsList.get()
		settings = self.fitGroup
		fitRigsGrp = self.fitRigsGrp

		# Naming
		globalName = fitNode.globalName.get()
		subNames = fitNode.subName0.get()
		rigType = fitNode.rigType.get()
		suffix = ''
		side = fitNode.side.get()
		
		# ========================================= Names ==========================================
		names = {
		'fitNode':					'%s_fitNode%s'						% (jnts[0], rigType),
		'grp':						'%s_%s'								% (jnts[0], rigType),
		'vec':						'%s_upVector%s' 					% (rigType, suffix),
		'controlScaleMult':			'%s_ctrlScale_MULT%s' 				% (rigType, suffix),
		'adjustMult':				'%s_adjust_MULT%s' 					% (rigType, suffix),
		'shapesGrp':				'%s_shapes_GRP%s' 					% (rigType, suffix),
		'fkGrp':					'%s_FK_GRP%s' 						% (rigType, suffix),
		'ikGrp':					'%s_IK_GRP%s' 						% (rigType, suffix),
		'fkShape':					'%s_FK_shape%s' 					% (rigType, suffix),
		'ikShape':					'%s_IK_shape%s' 					% (rigType, suffix),
		}
		# names = constructNames(namesList)
		
		# Collections
		nodeList = []
		shapesList = []
		ctrlList = []
		freezeList = []

		# Rig-specific attributes
		rb.cbSep(fitNode)
		
		addAttr(fitNode, ln='rigStyle', at='enum', ct='input', enumName='fk:bezier', keyable=True)

		addAttr(fitNode, ln='offsets', ct='input', at='short', k=1, min=0, max=1, dv=0)
		
		# addAttr(fitNode, ln='multiChain', ct='input', at='short', k=1, min=0, max=1, dv=0)

		addAttr(fitNode, ln='closeLoop', ct='input', at='short', k=1, min=0, max=1, dv=0)

		addAttr(fitNode, ln='doFK', ct='input', at='short', k=1, min=0, max=1, dv=0)
		addAttr(fitNode, ln='doBend', ct='input', at='short', k=1, min=0, max=1, dv=0)
		addAttr(fitNode, ln='doBias', ct='input', at='short', k=1, min=0, max=1, dv=0)
		addAttr(fitNode, ln='doNeutralize', ct='input', at='short', k=1, min=0, max=1, dv=0)
		addAttr(fitNode, ln='rotationStyle', ct='input', at='enum', enumName='none:aim:curve', k=1, dv=0)

		addAttr(fitNode, ln='fkShapes', ct='shape', at='message', multi=1, indexMatters=0, keyable=True, h=self.hidden)
		addAttr(fitNode, ln='ikShapes', ct='shape', at='message', multi=1, indexMatters=0, keyable=True, h=self.hidden)
		
		

		jnt0T = xform(jnts[0], q=1, rp=1, ws=1)
		jnt0R = xform(jnts[0], q=1, ro=1, ws=1)
		# MAIN GROUPS
		# Group
		grp = createNode('transform', n=names.get('grp', 'rnm_grp'), p=fitRigsGrp)
		nodeList.append(grp)
		freezeList.append(grp)
		if self.dev: print grp
		move(grp, jnt0T, rpr=1, ws=1)
		xform(grp, ro=jnt0R, ws=1)
		self.fitNode.v.connect(grp.v)
		rb.messageConnect([grp], 'message', fitNode, 'fitGroup')
		# parent(fitNode, grp, r=True, s=True)




		for i, jnt in enumerate(jnts):
			# name objects
			if len(jnts) < 10:
				d = i
			elif len(jnts) < 100:
				d = '%01d' % i
			else:
				d = '%02d' % i

			if self.dev:
				print "\n"
				print d

			# Get input transform space
			jntT = xform(jnt, q=1, rp=1, ws=1)
			jntR = xform(jnt, q=1, ro=1, ws=1)
			# Shapes
			shapesGrp = createNode('transform', n='%s_%s' %(jnt, names.get('shapesGrp', 'rnm_shapesGrp')), p=grp)
			nodeList.append(shapesGrp)
			fitNode.controlScaleResult >> shapesGrp.scaleX
			fitNode.controlScaleResult >> shapesGrp.scaleY
			fitNode.controlScaleResult >> shapesGrp.scaleZ
			move(shapesGrp, jntT, rpr=1, ws=1)
			xform(shapesGrp, ro=jntR, ws=1)
			freezeList.append(shapesGrp)
			parentConstraint(jnt, shapesGrp)
			fitNode.shapesVis >> shapesGrp.v
			if self.dev:
				print shapesGrp
			# VectorY (?)
			vecProd = createNode('vectorProduct', n='%s_%s' %(jnt, names.get('vec', 'rnm_vector')))
			vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
			rb.setAttrsWithDictionary(vecProd, vecSetAttr)
			connectAttr(jnt.worldMatrix[0], vecProd.matrix)
			if not hasAttr(fitNode, 'upVector%s' % d):
				addAttr(fitNode, ln='upVector%s' % d, at='compound', numberOfChildren=3, keyable=0)
				addAttr(fitNode, ln='upVector%sX' % d, at='float', parent='upVector%s' % d, keyable=0)
				addAttr(fitNode, ln='upVector%sY' % d, at='float', parent='upVector%s' % d, keyable=0)
				addAttr(fitNode, ln='upVector%sZ' % d, at='float', parent='upVector%s' % d, keyable=0)
			connectAttr(vecProd.outputX, fitNode.attr('upVector%sX' % d))
			connectAttr(vecProd.outputY, fitNode.attr('upVector%sY' % d))
			connectAttr(vecProd.outputZ, fitNode.attr('upVector%sZ' % d))
			nodeList.append(vecProd)
			if self.dev:
				print vecProd


			if mirrorFitRig:
				unitConvert = createNode('unitConversion')
				unitConvert.conversionFactor.set(-1)
				fitNode.controlScaleResult >> unitConvert.input
				unitConvert.output >> shapesGrp.scaleX
				
			# CONTROL SCALING
			controlScaleMult = createNode('multDoubleLinear', n='%s_%s' % (jnt.shortName(), names.get('controlScaleMult', 'rnm_controlScaleMult'))) # Local * Global Scale
			nodeList.append(controlScaleMult)
			if self.dev: print controlScaleMult
			fitNode.controlScale 		>> controlScaleMult.i1
			settings.controlScale 		>> controlScaleMult.i2

			
			adjustMult = createNode('multDoubleLinear', n='%s_%s' % (jnt.shortName(), names.get('adjustMult', 'rnm_adjustMult')))
			nodeList.append(adjustMult)
			if self.dev: print adjustMult
			adjustMult.i2.set(1.4)
			controlScaleMult.o 	>> adjustMult.i1

			adjustMult.o >> fitNode.controlScaleResult


			fkGrp = createNode('transform', n='%s_%s' % (jnt.shortName(), names.get('fkGrp', 'rnm_fkGrp')), p=shapesGrp)
			nodeList.append(fkGrp)
			fkNode = ls(rb.shapeMaker(name='%s_%s' % (jnt.shortName(), names.get('fkShape', 'rnm_fkShape')), shape=2))[0]
			# fitNode.shapesVis >> fkNode.v
			parent(fkNode, fkGrp)
			fkNode.translate.set([0,0,0])
			fkNode.rotate.set([0,0,90])
			fkNode.scale.set([8,8,8])
			makeIdentity(fkNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
			fkShape = fkNode.getShapes()[0]
			fkNode.message.connect(fitNode.fkShapes, na=1)
			col.setViewportRGB([fkShape], self.colorsFK[side])
			nodeList.append(fkNode)
			shapesList.append(fkNode)
			if self.dev:
				print fkGrp

			ikGrp = createNode('transform', n='%s_%s' % (jnt.shortName(), names.get('ikGrp', 'rnm_ikGrp')), p=shapesGrp)
			nodeList.append(ikGrp)
			fitNode.offsets >> ikGrp.v
			ikNode = ls(rb.shapeMaker(name='%s_%s' % (jnt.shortName(), names.get('ikShape', 'rnm_ikShape')), shape=1))[0]
			# fitNode.shapesVis >> ikNode.v
			parent(ikNode, ikGrp)
			ikNode.translate.set([0,0,0])
			ikNode.rotate.set([0,0,90])
			ikNode.scale.set([10,10,10])
			ikNode.message.connect(fitNode.ikShapes, na=1)
			makeIdentity(ikNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
			ikShape = ikNode.getShapes()[0]
			col.setViewportRGB([ikShape], self.colorsIK[side])
			nodeList.append(ikNode)
			shapesList.append(ikNode)
			if self.dev:
				print ikGrp

		# Finalize
		for ctrl in ctrlList:
			# parent(fitNode, ctrl, s=1, add=1)
			rb.ctrlSetupStandard(ctrl, ctrlSet=None, pivot=False, ro=False, )


		for node in nodeList:
			addAttr(node, k=1, h=self.hidden, at='message', ln='fitNode')
			fitNode.deleteList.connect(node.fitNode)
			# node.fitNode.connect(fitNode.deleteList, nextAvailable=1, f=1)

		return fitNode

	#===================================================================================================
	#===================================================================================================

	def mirrorFitRig(self, fitNode):
		'''
		Digs through and finds mirror joints to each join in provided fitrig, and uses those joints to create a new one.
		Connects result attributes
		'''
		attributes = [
		'controlScale',
		'parentSocketIndex',
		'offsets',
		'globalName',
		'visCategory',
		'inheritScale',
		]

		i=0
		while hasAttr(fitNode, 'subName%s' % i):
			attributes.append('subName%s' % i)
			i = i + 1

		# fitRig.mirrorFitRig()
		

		# Get joints 
		joints = fitNode.jointsList.get()
		if self.dev:
			print 'Joints:'
			print joints

		# Error check
		if not all(self.hasMirror(j) for j in joints):
			print 'Failed Joints: '
			print failList
			raise Exception('Not all joints associated with fitNode have mirrored joints connected.')
			# Add options for specifying joints to be mirrored?

		# Get mirror joints
		mirrorJoints = []
		for j in joints:
			mirrorJoints.append(j.mirror.get())

		if self.dev: 
			print 'Mirrored Joints:'
			print mirrorJoints

		# Create mirrored fitRig class instance (or maintain standard class instance? easy link wouldnt be so bad?)
		mirrorFitRig = chainFitRig(mirrorJoints, self.fitSkeleton, mirrorFitRig=True)

		# Get fitNode
		mirrorFitNode = mirrorFitRig.fitNode

		# connect attributes in this list and hide right side
		for attribute in attributes:
			fitNode.attr(attribute).connect(mirrorFitNode.attr(attribute), force=1)
			# mirrorFitNode.attr(attribute).set(k=0, cb=0)


		if not hasAttr(fitNode, 'mirror'):
			addAttr(fitNode, ln='mirror', at='message', k=1)
		if not hasAttr(mirrorFitNode, 'mirror'):
			addAttr(mirrorFitNode, ln='mirror', at='message', k=1)
		mirrorFitNode.mirror.connect(fitNode.mirror)


		if self.dev: print 'Mirror Fit Node: %s' % mirrorFitNode
		return mirrorFitNode

# =================================================================================

class poleVectorIKFitRig(fitRig):

	def __init__(self, joints=None, fitSkele=None, fitNode=None, mirrorFitRig=False, *args, **kwargs):
		if fitSkele is None:
			try:
				fitSkele = ls('skeleNode_META')[0]
			except:
				raise Exception('Fit Skeleton node not found.')

		self.fitSkeleton = fitSkele

		# ERROR CHECKS
		self.rigType = 'poleVectorIK'
		if self.dev: print 'RUNNING POLE VECTOR RIG'
		if self.dev: print 'CHECKING FOR ERRORS...'

		if self.dev: print len(joints)
		if not len(joints) == 3:
			raise Exception('Wrong number of joints specified for PoleVectorIK fitRig. Select 3 joints.')

		# FITNODE GLOBAL ATTRIBUTES
		fitNode = fitRig.__init__(self, joints=joints, rigType='poleVectorIK')
		if self.dev:
			print 'FITNODE'
			print self.fitNode

		# FITNODE SPECIFIC ATTRIBUTES
		self.fitNode = self.poleVectorIKInit(self.fitNode, mirrorFitRig=mirrorFitRig)

		# MIRRORING
		# Automatically mirror if all mirror joints found (and mirroring hasn't already been done)
		if not mirrorFitRig and all(self.hasMirror(j) for j in joints):
			if self.dev: print 'Apply Mirroring'
			mirrorFitNode = self.mirrorFitRig(self.fitNode)


	def poleVectorIKInit(self, fitNode, mirrorFitRig=False):
		'''Takes three points and converts them into fkIk rig
		'''
		# fitNode = self.fitNode

		defaultJ = 3
		minJ = 2
		maxJ = 12

		settings = self.fitGroup
		fitrigGroup = self.fitRigsGrp

		start, mid, end = fitNode.jointsList.get()
		startMidEnd = [start, mid, end]


		side = fitNode.side.get()
		globalName = fitNode.globalName.get()
		rigType = fitNode.rigType.get()
		suffix = '_%s' % rigType

		# ========================================= Names ==========================================
		suffix = '_poleVectorIK'
		sme = ['start', 'mid', 'end']
		names={
		'fitNode': 						'%s_fitNode%s' % 							(start.shortName(), suffix),
		'vecStartName':					'%s_vec%s'	% 								(start.shortName(), suffix),
		'vecMidName':					'%s_vec%s'	% 								(mid.shortName(), suffix),
		'vecEndName':					'%s_vec%s'	% 								(end.shortName(), suffix),
		'lengthSM':						'%s_SM_distance%s'	% 						(start.shortName(), suffix),
		'lengthME':						'%s_ME_distance%s'	% 						(mid.shortName(), suffix),
		'lengthAdd':					'%s_length_ADD%s'	% 						(start.shortName(), suffix),
		'controlScaleMult':				'%s_ctrlScale_MULT%s'	% 					(start.shortName(), suffix),
		'lengthAdjustMult':				'%s_len_ctrlScaleAdjust_MULT%s'	% 			(start.shortName(), suffix),
		'lengthCtrlScaleResult':		'%s_len_ctrlScale_MULT%s'	% 				(start.shortName(), suffix),
		'lengthBasedScalingBlend':		'%s_len_scaling_Blend%s'	% 				(start.shortName(), suffix),
		'reverseCtrlScale':				'%s_scale_reverse_MULT%s'	% 				(start.shortName(), suffix),
		'grpName': 						'%s_fitRig%s' % 							(start.shortName(), suffix),
		'worldGrpName': 				'%s_world_GRP%s' % 							(start.shortName(),suffix),
		'triangle': 					'%s_triangle_VIS%s' % 						(start.shortName(), suffix),
		'ctrlGrp': 						'%s_controls_GRP%s' % 						(start.shortName(), suffix),
		'bufName':						'BUF%s' % 									suffix,
		'ctrlName':						'CTRL%s' % 									suffix,
		'clsName':						'CLS%s' % 									suffix,
		'elbowName':					'%s_PV_BUF%s' % 							(start.shortName(), suffix),
		'pvName':						'%s_PV%s' % 								(start.shortName(), suffix),
		'orientOffset':					'%s_orient_offset%s' % 						(end.shortName(), suffix),
		'decmp': 						'decmp_PV%s' % 								suffix,		
		'startMid':						'%s_PV_startMid_vector%s' % 				(start.shortName(), suffix),
		'startEnd':						'%s_PV_startEnd_vector%s' % 				(start.shortName(), suffix),
		'dotP' :						'%s_PV_dotP_vector%s' % 					(start.shortName(), suffix),
		'seLen' :						'%s_PV_startEnd_len%s' % 					(start.shortName(), suffix),
		'proj' :						'%s_PV_projection_vector%s' % 				(start.shortName(), suffix),
		'sen' :							'%s_PV_startEnd_normalize%s' % 				(start.shortName(), suffix),
		'nProj' :						'%s_PV_projection_vector_normalize%s' % 	(start.shortName(), suffix),
		'arrowV' :						'%s_PV_arrow_vector%s' % 					(start.shortName(), suffix),
		'finalV' :						'%s_PV_final_vector%s' % 					(start.shortName(), suffix),
		'adjust' :						'%s_PV_adjust_MULT%s' % 					(start.shortName(), suffix),
		'curve1':						'%s_SM_CRV%s' % 							(start.shortName(), suffix),
		'curve2':						'%s_ME_CRV%s' % 							(start.shortName(), suffix),
		'clsStart':						'%s_CLS%s' % 								(start.shortName(), suffix),
		'clsMid':						'%s_CLS%s' % 								(mid.shortName(), suffix),
		'clsEnd':						'%s_CLS%s' % 								(end.shortName(), suffix),
		'upperJointsGroup':				'%s_subJnts_GRP%s' % 						(start.shortName(), suffix),
		'lowerJointsGroup':				'%s_subJnts_GRP%s' % 						(mid.shortName(), suffix),
		'shapesGrp':					'%s_shapes_GRP%s' % 						(start.shortName(), suffix),
		'ikShapeOrient':				'%s_ikShape_ORI%s' % 						(start.shortName(), suffix),
		'fkShapeGrp':					'FK_shape_GRP%s' % 							(suffix),
		'fkShape':						'FK_shape%s' % 								(suffix),
		'ikShapeGrp':					'IK_shape_GRP%s' % 							(suffix),
		'ikShape':						'IK_shape%s' % 								(suffix),
		'pvShapeGrp':					'PV_shape_GRP%s' % 							(suffix),
		'pvShape':						'PV_shape%s' % 								(suffix),
		}


		# Collections
		nodeList = []
		shapesList = []
		ctrlList = []
		freezeList = []


		# Rig-specific attributes

		addAttr(fitNode, ln='stretch', at='enum', ct='input', enumName='scale:translation', keyable=True)
		addAttr(fitNode, ln='noMirror', at='enum', ct='input', enumName='False:True', keyable=True)
		addAttr(fitNode, ln='fkScale', at='enum', ct='input', enumName='mirror:behavior:orientation', keyable=True)

		addAttr(fitNode, ln='bendStyle', ct='input', at='enum', enumName='None:Aim:Mid Bend:Bezier', dv=3, keyable=True)

		addAttr(fitNode, ln='orientation', nn='IK Orientation', at='enum', enumName='world:inherit', keyable=True)
		addAttr(fitNode, ln='orientChoice', nn='IK Orientation Choice', ct='output', at='enum', enumName='X:Y:Z', keyable=True)
		addAttr(fitNode, ln='doBend', ct='input', at='short', min=0, max=1, dv=1, k=1)
		addAttr(fitNode, ln='subNode', ct='subRig', at='message', keyable=True)
		###
		# Shapes
		addAttr(fitNode, ln='fkStartShape', ct='shape', at='message', keyable=True)
		addAttr(fitNode, ln='fkMidShape', ct='shape', at='message', keyable=True)
		addAttr(fitNode, ln='fkEndShape', ct='shape', at='message', keyable=True)

		addAttr(fitNode, ln='bendStartShape', ct='shape', at='message', keyable=True)
		addAttr(fitNode, ln='bendMidShape', ct='shape', at='message', keyable=True)
		addAttr(fitNode, ln='bendEndShape', ct='shape', at='message', keyable=True)

		addAttr(fitNode, ln='ikStartShape', ct='shape', at='message', keyable=True)
		addAttr(fitNode, ln='ikEndShape', ct='shape', at='message', keyable=True)
		addAttr(fitNode, ln='pvShape', ct='shape', at='message', keyable=True)

		# Outputs
		addAttr(fitNode, ln='pv', ct='output', at='message', keyable=True)
		addAttr(fitNode, ln='outputJoints0', ct='output', at='message', multi=True, keyable=True)
		addAttr(fitNode, ln='outputJoints1', ct='output', at='message', multi=True, keyable=True)

		# =================================== Y Vectors ===================================
		# Vector Start
		vecProdStart = createNode('vectorProduct', n=names['vecStartName'])
		nodeList.append(vecProdStart)
		vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
		rb.setAttrsWithDictionary(vecProdStart, vecSetAttr)
		connectAttr(start.worldMatrix[0], vecProdStart.matrix)	
		addAttr(fitNode, ln='upVectorStart', at='compound', numberOfChildren=3, keyable=True)
		addAttr(fitNode, ln='upVectorStartX', at='float', parent='upVectorStart', keyable=True)
		addAttr(fitNode, ln='upVectorStartY', at='float', parent='upVectorStart', keyable=True)
		addAttr(fitNode, ln='upVectorStartZ', at='float', parent='upVectorStart', keyable=True)
		fitNode.upVectorStartX.set(k=0, cb=1)
		fitNode.upVectorStartY.set(k=0, cb=1)
		fitNode.upVectorStartZ.set(k=0, cb=1)
		connectAttr(vecProdStart.outputX, fitNode.upVectorStartX)
		connectAttr(vecProdStart.outputY, fitNode.upVectorStartY)
		connectAttr(vecProdStart.outputZ, fitNode.upVectorStartZ)
		rb.cbSep(fitNode)
		if self.dev: print vecProdStart


		# Vector Mid
		vecProdMid = createNode('vectorProduct', n=names['vecMidName'])
		nodeList.append(vecProdMid)
		vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
		rb.setAttrsWithDictionary(vecProdMid, vecSetAttr)
		connectAttr(mid.worldMatrix[0], vecProdMid.matrix)	
		addAttr(fitNode, ln='upVectorMid', at='compound', numberOfChildren=3, keyable=True)
		addAttr(fitNode, ln='upVectorMidX', at='float', parent='upVectorMid', keyable=True)
		addAttr(fitNode, ln='upVectorMidY', at='float', parent='upVectorMid', keyable=True)
		addAttr(fitNode, ln='upVectorMidZ', at='float', parent='upVectorMid', keyable=True)
		fitNode.upVectorMidX.set(k=0, cb=1)
		fitNode.upVectorMidY.set(k=0, cb=1)
		fitNode.upVectorMidZ.set(k=0, cb=1)
		connectAttr(vecProdMid.outputX, fitNode.upVectorMidX)
		connectAttr(vecProdMid.outputY, fitNode.upVectorMidY)
		connectAttr(vecProdMid.outputZ, fitNode.upVectorMidZ)
		rb.cbSep(fitNode)
		if self.dev: print vecProdMid


		# Vector End
		vecProdEnd = createNode('vectorProduct', n=names['vecEndName'])
		nodeList.append(vecProdEnd)
		vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
		rb.setAttrsWithDictionary(vecProdEnd, vecSetAttr)
		connectAttr(end.worldMatrix[0], vecProdEnd.matrix)	
		addAttr(fitNode, ln='upVectorEnd', at='compound', numberOfChildren=3, keyable=True)
		addAttr(fitNode, ln='upVectorEndX', at='float', parent='upVectorEnd', keyable=True)
		addAttr(fitNode, ln='upVectorEndY', at='float', parent='upVectorEnd', keyable=True)
		addAttr(fitNode, ln='upVectorEndZ', at='float', parent='upVectorEnd', keyable=True)
		fitNode.upVectorEndX.set(k=0, cb=1)
		fitNode.upVectorEndY.set(k=0, cb=1)
		fitNode.upVectorEndZ.set(k=0, cb=1)
		connectAttr(vecProdEnd.outputX, fitNode.upVectorEndX)
		connectAttr(vecProdEnd.outputY, fitNode.upVectorEndY)
		connectAttr(vecProdEnd.outputZ, fitNode.upVectorEndZ)
		rb.cbSep(fitNode)
		if self.dev: print vecProdEnd


		decmp = []
		# Decompose Matrix
		for i in range(3):
			decmpName = '%s_%s_%s' % (start, sme[i], names['decmp'])
			decmp.append(createNode('decomposeMatrix', n=decmpName))
			nodeList.append(decmp[i])
			if self.dev: print decmp[i]
		lengths = []
		# Length Start-Mid
		if not hasAttr(fitNode, 'lengthSM'):
			addAttr(fitNode, ln='lengthSM', nn='Length Start/Mid', keyable=True)
			fitNode.lengthSM.set(k=0, cb=1)
		lengthSM = createNode('distanceBetween', n=names['lengthSM'])
		lengths.append(lengthSM)
		decmp[0].outputTranslate >> lengthSM.point1
		decmp[1].outputTranslate >> lengthSM.point2
		lengthSM.distance >> fitNode.lengthSM
		# Length Mid-End
		if not hasAttr(fitNode, 'lengthME'):
			addAttr(fitNode, ln='lengthME', nn='Length Mid/End', keyable=True)
			fitNode.lengthME.set(k=0, cb=1)
			rb.cbSep(fitNode)
		lengthME = createNode('distanceBetween', n=names['lengthME'])
		nodeList.append(lengthME)
		lengths.append(lengthME)
		decmp[1].outputTranslate >> lengthME.point1
		decmp[2].outputTranslate >> lengthME.point2
		lengthME.distance >> fitNode.lengthME


		# CONTROL SCALING
		lengthAdd = createNode('addDoubleLinear', n=names['lengthAdd'])
		nodeList.append(lengthAdd)
		lengthSM.distance >> lengthAdd.i1
		lengthME.distance >> lengthAdd.i2

		controlScaleMult = createNode('multDoubleLinear', n=names.get('controlScaleMult', 'rnm_controlScaleMult')) # Local * Global Scale
		nodeList.append(controlScaleMult)
		if self.dev: print controlScaleMult
		fitNode.controlScale 		>> controlScaleMult.i1
		settings.controlScale 		>> controlScaleMult.i2
		
		lengthCtrlScaleResult = createNode('multDoubleLinear', n=names.get('lengthCtrlScaleResult', 'rnm_lengthCtrlScaleResult')) # (local * global) * length
		nodeList.append(lengthCtrlScaleResult)
		if self.dev: print lengthCtrlScaleResult
		controlScaleMult.o 			>> lengthCtrlScaleResult.i1
		lengthAdd.o 		>> lengthCtrlScaleResult.i2

		lengthAdjustMult = createNode('multDoubleLinear', n=names.get('lengthAdjustMult', 'rnm_lengthAdjustMult'))
		nodeList.append(lengthAdjustMult)
		if self.dev: print lengthAdjustMult
		lengthAdjustMult.i2.set(0.4)
		lengthCtrlScaleResult.o 	>> lengthAdjustMult.i1

		lengthBasedScalingBlend = createNode('blendTwoAttr', n=names.get('lengthBasedScalingBlend', 'rnm_lengthBasedScalingBlend'))
		nodeList.append(lengthBasedScalingBlend)
		if self.dev: print lengthBasedScalingBlend
		controlScaleMult.o 			>> lengthBasedScalingBlend.i[0]
		lengthAdjustMult.o 			>> lengthBasedScalingBlend.i[1]
		settings.lengthBasedScaling >> lengthBasedScalingBlend.ab
		lengthBasedScalingBlend.o 	>> fitNode.controlScaleResult


		rb.messageConnect(start, 'fitNode', [fitNode], 'start')
		rb.messageConnect(mid, 'fitNode', [fitNode], 'mid')
		rb.messageConnect(end, 'fitNode', [fitNode], 'end')
		# fitNode.startLabel.set(start.shortName().split("|")[-1].split("_")[0]) # Removes all but last '|' block and returns first '_' block
		# fitNode.endLabel.set(end.shortName().split("|")[-1].split("_")[0])
		# fitNode.side.set(start.skeleSide.get())

		# Get points
		startT = xform(start, q=1, rp=1, ws=1)
		startR = xform(start, q=1, ro=1, ws=1)
		midT = xform(mid, q=1, rp=1, ws=1)
		midR = xform(mid, q=1, ro=1, ws=1)
		endT = xform(end, q=1, rp=1, ws=1)
		endR = xform(end, q=1, ro=1, ws=1)

		startMidEndT = [startT, midT, endT]
		startMidEndR = [startR, midR, endR]



		# ===================================================================================
		# =================================== Nodes =========================================
		# ===================================================================================

		# Group
		groupAttrs =  {'inheritsTransform': 0}
		grp = createNode('transform', n=names['grpName'])
		freezeList.append(grp)
		nodeList.append(grp)
		rb.setAttrsWithDictionary(grp, groupAttrs)
		parent(grp, fitrigGroup)
		# parent(fitNode, grp, r=True, s=True)
		rb.messageConnect(grp, 'message', fitNode, 'fitRig')
		self.fitNode.v.connect(grp.v)
		if self.dev: print grp


		# No-Translate Group
		worldGroupAttrs =  {'inheritsTransform': 0}
		worldGrp = createNode('transform', n=names['worldGrpName'])
		nodeList.append(worldGrp)
		freezeList.append(worldGrp)
		rb.setAttrsWithDictionary(worldGrp, worldGroupAttrs)
		fitNode.controlsVis >> worldGrp.v
		parent(worldGrp, grp)
		if self.dev: print worldGrp


		# Triangle vis
		polyFacet = polyCreateFacet( p=[ (startT), (midT), (endT) ], n=names['triangle'])
		triangle = ls(polyFacet[0])[0]
		triangleCH = ls(polyFacet[1])[0]
		nodeList.append(triangle)
		freezeList.append(triangle)
		triangleCH.rename('%s_History' % names['triangle'])
		# Shape
		triangleSAttrs =  {
		'overrideEnabled': True,
		'overrideDisplayType': 2,
		'castsShadows': 0,
		'receiveShadows': 0,
		'visibleInReflections': 0,
		'visibleInRefractions': 0
		}
		triangleS = triangle.getShapes()[0]
		rb.setAttrsWithDictionary(triangleS, triangleSAttrs)
		parent (triangle, worldGrp)
		polyColorPerVertex(triangle, colorRGB=[0.1,0.1,0.1], a=0.3, cdo=True)
		if self.dev: print triangle
		if self.dev: print triangleCH

		if self.dev:
			print "\n"


		# # ============================ Fit Rig Controls ================================
		# Control Group
		ctrlGrp = createNode('transform', n=names['ctrlGrp'], p=grp)
		if mirrorFitRig:
			ctrlGrp.scaleX.set(-1)
		nodeList.append(ctrlGrp)
		freezeList.append(ctrlGrp)
		fitNode.controlsVis >> ctrlGrp.v
		if self.dev: print ctrlGrp

		# Lists to store results
		buf = []
		ctrl = []
		clust = []
		forwardVector = [fitNode.jointVector0, fitNode.jointVector1, fitNode.jointVector2]
		forwardVectorX = [fitNode.jointVector0X, fitNode.jointVector0X, fitNode.jointVector0X]
		forwardVectorY = [fitNode.jointVector1Y, fitNode.jointVector1Y, fitNode.jointVector1Y]
		forwardVectorZ = [fitNode.jointVector2Z, fitNode.jointVector2Z, fitNode.jointVector2Z]

		for i in range(3):
			bufName = '%s_%s' % (startMidEnd[i].shortName(), names['bufName'])
			ctrlName = '%s_%s' % (startMidEnd[i].shortName(), names['ctrlName'])
			clsName = '%s_%s' % (startMidEnd[i].shortName(), names['clsName'])
			if self.dev: print i

			# Buffer
			buf.append(createNode('transform', n='%s' % bufName, p=ctrlGrp))
			nodeList.append(buf[i])
			move(buf[i], startMidEndT[i], rpr=1, ws=1)
			xform(buf[i], ro=startMidEndR[i], ws=1)
			if self.dev: print buf[i]

			connectAttr(startMidEnd[i].worldMatrix[0], decmp[i].inputMatrix)
			

			# Constraint
			pointC = pointConstraint(startMidEnd[i], buf[i])
			nodeList.append(pointC)
			if self.dev: print pointC

			# Cluster
			clust.append(cluster(triangle.vtx[i], n='%s' % clsName)[1])
			nodeList.append(clust[i])
			clust[i].hide()
			parent(clust[i], buf[i])
			if self.dev: print clust[i]
			

		# Done with per-joint nodes

		if self.dev: print '\n'



		# ==================== Pole vector placement calculation ========================

		# startMid
		startMidAttrs =  {'operation': 2}
		startMid = createNode('plusMinusAverage', n=names['startMid'])
		nodeList.append(startMid)
		rb.setAttrsWithDictionary(startMid, startMidAttrs)
		decmp[1].outputTranslate >> startMid.input3D[0]
		decmp[0].outputTranslate >> startMid.input3D[1]
		if self.dev: print startMid

		# startEnd
		startEndAttrs =  {'operation': 2}
		startEnd = createNode('plusMinusAverage', n=names['startEnd'])
		nodeList.append(startEnd)
		rb.setAttrsWithDictionary(startEnd, startEndAttrs)
		decmp[2].outputTranslate >> startEnd.input3D[0]
		decmp[0].outputTranslate >> startEnd.input3D[1]
		if self.dev: print startEnd

		# dotP
		dotPAttrs =  {'operation': 1, 'normalizeOutput': 0}
		dotP = createNode('vectorProduct', n=names['dotP'])
		nodeList.append(dotP)
		rb.setAttrsWithDictionary(dotP, dotPAttrs)
		startMid.output3D >> dotP.input1
		startEnd.output3D >> dotP.input2
		if self.dev: print dotP

		# startEndLength
		seLenAttrs =  {'point2': (0,0,0) }
		seLen = createNode('distanceBetween', n=names['seLen'])
		nodeList.append(seLen)
		rb.setAttrsWithDictionary(seLen, seLenAttrs)
		startEnd.output3D >> seLen.point1
		if self.dev: print seLen

		# proj div
		projAttrs =  {'operation': 2}
		proj = createNode('multiplyDivide', n=names['proj'])
		nodeList.append(proj)
		rb.setAttrsWithDictionary(proj, projAttrs)
		dotP.output >> proj.input1
		seLen.distance >> proj.input2X
		seLen.distance >> proj.input2Y
		seLen.distance >> proj.input2Z
		if self.dev: print proj

		# normalize startEnd
		senAttrs =  {'operation': 0, 'normalizeOutput': 1}
		sen = createNode('vectorProduct', n=names['sen'])
		nodeList.append(sen)
		rb.setAttrsWithDictionary(sen, senAttrs)
		startEnd.output3D >> sen.input1
		if self.dev: print sen

		# normalize proj
		nProjAttrs =  {'operation': 1}
		nProj = createNode('multiplyDivide', n=names['nProj'])
		nodeList.append(nProj)
		rb.setAttrsWithDictionary(nProj, nProjAttrs)
		sen.output >> nProj.input1
		proj.output >> nProj.input2
		if self.dev: print nProj

		# arrowV
		arrowVAttrs =  {'operation': 2}
		arrowV = createNode('plusMinusAverage', n=names['arrowV'])
		nodeList.append(arrowV)
		rb.setAttrsWithDictionary(arrowV, arrowVAttrs)
		startMid.output3D >> arrowV.input3D[0]
		nProj.output >> arrowV.input3D[1]
		if self.dev: print arrowV

		# adjust
		# if mirrorFitRig:
		# 	adjustAttrs =  {'operation': 1, 'i2': (0.1,0.1,0.1)}
		# else:
		adjustAttrs =  {'operation': 1, 'i2': (-0.1,-0.1,-0.1)}
		adjust = createNode('multiplyDivide', n=names['adjust'])
		nodeList.append(adjust)
		rb.setAttrsWithDictionary(adjust, adjustAttrs)
		arrowV.output3D >> adjust.input1
		if self.dev: print adjust


			# finalV
		finalVAttrs =  {'operation': 1}
		finalV = createNode('plusMinusAverage', n=names['finalV'])
		nodeList.append(finalV)
		rb.setAttrsWithDictionary(finalV, finalVAttrs)
		adjust.output >> finalV.input3D[0]
		decmp[1].outputTranslate >> finalV.input3D[1]
		if self.dev: print finalV


		# Elbow Group
		elbowAttrs =  { 'radius': 0 , 'overrideEnabled': 1, 'overrideDisplayType': 2}
		elbow = createNode('joint', n=names['elbowName'], p=worldGrp)
		nodeList.append(elbow)
		rb.setAttrsWithDictionary(elbow, elbowAttrs)
		finalV.output3D >> elbow.t
		aimConst = aimConstraint(startMidEnd[1], elbow)
		nodeList.append(aimConst)
		if self.dev: print elbow


		# PV 
		pvAttrs = { 'radius': 0.75, 'overrideEnabled': 1, 'overrideDisplayType': 0, 'tx': 10 }
		pv = createNode('joint', n=names['pvName'], p=elbow)
		nodeList.append(pv)
		rb.setAttrsWithDictionary(pv, pvAttrs)
		rb.lockAndHide([pv], ['ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'])
		col.setViewportRGB(pv, self.colorJoints[side])
		pv.message >> fitNode.pv
		# rb.messageConnect(pv, 'message', [fitNode], 'pv')
		ctrlList.append(pv)
		if self.dev: print pv



		curve1 = curve(degree=1, p=[startT, midT], n=names['curve1'])
		parent(curve1, worldGrp)
		hide(curve1)
		nodeList.append(curve1)
		if self.dev: print curve1

		curve2 = curve(degree=1, p=[midT, endT], n=names['curve2'])
		parent(curve2, worldGrp)
		hide(curve2)
		nodeList.append(curve2)
		if self.dev: print curve2

		startClusterAttr = { 'v': 0 }
		clsStart = cluster((curve1.cv[0]), n=names['clsStart'])[1]
		nodeList.append(clsStart)
		rb.setAttrsWithDictionary(clsStart, startClusterAttr)
		parent(clsStart, worldGrp)
		pointConstraint(startMidEnd[0], clsStart)
		if self.dev: print clsStart

		# Make sure this takes care of both curves
		midClusterAttr = { 'v': 0 }
		clsMid = cluster((curve1.cv[1], curve2.cv[0]), n=names['clsMid'])[1]
		nodeList.append(clsMid)
		rb.setAttrsWithDictionary(clsMid, midClusterAttr)
		parent(clsMid, worldGrp)
		pointConstraint(startMidEnd[1], clsMid)
		# parent(clsMid, ctrl[1])
		if self.dev: print clsMid

		endClusterAttr = { 'v': 0 }
		clsEnd = cluster((curve2.cv[1]), n=names['clsEnd'])[1]
		nodeList.append(clsEnd)
		rb.setAttrsWithDictionary(clsEnd, endClusterAttr)
		parent(clsEnd, worldGrp)
		pointConstraint(startMidEnd[2], clsEnd)
		# parent(clsEnd, ctrl[2])
		if self.dev: print clsEnd

		# pointConstraint(start, clsStart)
		# pointConstraint(mid, clsMid)
		# pointConstraint(end, clsEnd)

		upperJointsGroup = createNode('transform', n=names['upperJointsGroup'], p=worldGrp)
		nodeList.append(upperJointsGroup)
		freezeList.append(upperJointsGroup)
	
		lowerJointsGroup = createNode('transform', n=names['lowerJointsGroup'], p=worldGrp)
		nodeList.append(lowerJointsGroup)
		freezeList.append(lowerJointsGroup)


		if self.dev: print "\nPopulating Curves..."
		upGrps, upJoints = populateCurveWithJoints(curve1, fitNode, prefix=start.shortName(), attrSuffix = '0', suffix='0_%s' % suffix, vectorAttribute='upVectorStart')
		dnGrps, dnJoints = populateCurveWithJoints(curve2, fitNode, prefix=mid.shortName(), attrSuffix = '1', suffix='1_%s' % suffix, vectorAttribute='upVectorMid', last=True)
		if self.dev: print "\nFinished Populating Curves."
		
		self.resultJoints = []
		self.resultJoints.extend(upGrps)
		self.resultJoints.extend(dnGrps)

		parent(upGrps, upperJointsGroup)
		parent(dnGrps, lowerJointsGroup)

		for i, resJoint in enumerate(upJoints):
			connectAttr(resJoint.message, fitNode.outputJoints0[i])
			if self.dev: print resJoint
		for i, resJoint in enumerate(dnJoints):
			connectAttr(resJoint.message, fitNode.outputJoints1[i])
			if self.dev: print resJoint


		# Shapes Group
		shapesGrp = createNode('transform', n=names['shapesGrp'], p=grp)
		nodeList.append(shapesGrp)
		freezeList.append(shapesGrp)
		fkShapeAttr = [fitNode.fkStartShape, fitNode.fkMidShape, fitNode.fkEndShape]
		bendShapeAttr = [fitNode.bendStartShape, fitNode.bendMidShape, fitNode.bendEndShape]
		ikShapeAttr = [fitNode.ikStartShape, fitNode.pvShape, fitNode.ikEndShape]
		fitNode.shapesVis >> shapesGrp.v

		if mirrorFitRig:
			reverseCtrlScale = createNode('multDoubleLinear', n=names['reverseCtrlScale'])
			nodeList.append(reverseCtrlScale)
			shapesGrp.scaleX.set(-1)

		

		ikShapeOrient = createNode('transform', n=names.get('ikShapeOrient', 'rnm_ikShapeOrient'), p=shapesGrp)
		nodeList.append(ikShapeOrient)
		rb.lockAndHide([ikShapeOrient], [ 'tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'v' ])
		addAttr(ikShapeOrient, ln='vectorOption1', at='compound', numberOfChildren=3, keyable=True)
		addAttr(ikShapeOrient, ln='vectorOption1X', at='float', parent='vectorOption1', keyable=True, dv=1.5708)
		addAttr(ikShapeOrient, ln='vectorOption1Y', at='float', parent='vectorOption1', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption1Z', at='float', parent='vectorOption1', keyable=True, dv=0)
		# 
		addAttr(ikShapeOrient, ln='vectorOption2', at='compound', numberOfChildren=3, keyable=True)
		addAttr(ikShapeOrient, ln='vectorOption2X', at='float', parent='vectorOption2', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption2Y', at='float', parent='vectorOption2', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption2Z', at='float', parent='vectorOption2', keyable=True, dv=1.5708)
		# 
		addAttr(ikShapeOrient, ln='vectorOption3', at='compound', numberOfChildren=3, keyable=True)
		addAttr(ikShapeOrient, ln='vectorOption3X', at='float', parent='vectorOption3', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption3Y', at='float', parent='vectorOption3', keyable=True, dv=1.5708)
		addAttr(ikShapeOrient, ln='vectorOption3Z', at='float', parent='vectorOption3', keyable=True, dv=0)
		# expose option to fitNode
		orientChoice = createNode('choice', name=names.get('orientChoice', 'rnm_orientChoice'))
		nodeList.append(orientChoice)

		
		ikShapeOrient.vectorOption1 >> orientChoice.input[0]
		ikShapeOrient.vectorOption2 >> orientChoice.input[1]
		ikShapeOrient.vectorOption3 >> orientChoice.input[2]

		fitNode.orientChoice >> orientChoice.selector
		orientChoice.output >> ikShapeOrient.rotate


		# For each control, create a default node with a shape to apply to the rig.
		for i in range(3):
			# FK Shapes
			fkShapeGrp = createNode('transform', n='%s_%s' % (startMidEnd[i].shortName(), names['fkShapeGrp']), p=shapesGrp)
			nodeList.append(fkShapeGrp)
			# Control scaling

			fitNode.controlScaleResult >> fkShapeGrp.scaleX
			fitNode.controlScaleResult >> fkShapeGrp.scaleY
			fitNode.controlScaleResult >> fkShapeGrp.scaleZ
			freezeList.append(fkShapeGrp)
			fkNode = ls(rb.shapeMaker(name='%s_%s' % (startMidEnd[i].shortName(), names['fkShape']), shape=2))[0]
			nodeList.append(fkNode)
			parent(fkNode, fkShapeGrp)
			# fitNode.shapesVis >> fkNode.v
			fkNode.translate.set([0,0,0])
			fkNode.rotate.set([0,0,90])
			fkNode.scale.set([1,1,1])
			fkNode.message >> fkShapeAttr[i]
			makeIdentity(fkNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
			fkShape = fkNode.getShapes()[0]
			col.setViewportRGB(fkShape, self.colorsFK[side])
			parentConstraint(startMidEnd[i], fkShapeGrp)

			if i is not 1:
				# IK Shapes
				ikShapeGrp = createNode('transform', n='%s_%s' % (startMidEnd[i].shortName(), names['ikShapeGrp']), p=shapesGrp)
				nodeList.append(ikShapeGrp)
				if mirrorFitRig:
					unitConvert = createNode('unitConversion')
					unitConvert.conversionFactor.set(-1)
					fitNode.controlScaleResult >> unitConvert.input
					unitConvert.output >> ikShapeGrp.scaleX
				else:
					fitNode.controlScaleResult >> ikShapeGrp.scaleX
				fitNode.controlScaleResult >> ikShapeGrp.scaleY
				fitNode.controlScaleResult >> ikShapeGrp.scaleZ
				freezeList.append(ikShapeGrp)
				ikNode = ls(rb.shapeMaker(name='%s_%s' % (startMidEnd[i].shortName(), names['ikShape']), shape=1))[0]
				nodeList.append(ikNode)
				fitNode.shapesVis >> ikNode.v
				parent(ikNode, ikShapeGrp)
				ikNode.translate.set([0,0,0])
				ikNode.rotate.set([0,0,90])
				ikNode.scale.set([1.2,1.2,1.2])
				ikNode.message >> ikShapeAttr[i]
				makeIdentity(ikNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
				ikShape = ikNode.getShapes()[0]
				col.setViewportRGB([ikShape], self.colorsIK[side])
				pointConstraint(startMidEnd[i], ikShapeGrp)
				# orientConstraint(ikShapeOrient, ikShapeGrp)
				oriC = orientConstraint(startMidEnd[i], ikShapeOrient, ikShapeGrp)
				rev = createNode('reverse', n=names.get('endOriOrientRev', 'rnm_endOriOrientRev'))
				nodeList.append(rev)
				fitNode.orientation >> rev.inputX
				fitNode.orientation >> oriC.w0
				rev.outputX >> oriC.w1
				oriC.interpType.set(2)

			# Bend shapes
			bendShapeGrp = createNode('transform', n='%s_%s' % (startMidEnd[i].shortName(), names.get('bendShapeGrp', 'rnm_bendShapeGrp')), p=shapesGrp)
			nodeList.append(bendShapeGrp)

			fitNode.controlScaleResult >> bendShapeGrp.scaleX
			fitNode.controlScaleResult >> bendShapeGrp.scaleY
			fitNode.controlScaleResult >> bendShapeGrp.scaleZ
			freezeList.append(bendShapeGrp)
			bendNode = ls(rb.shapeMaker(name='%s_%s' % (startMidEnd[i].shortName(), names.get('bendShape', 'rnm_bendShape')), shape=6))[0]
			nodeList.append(bendNode)
			parent(bendNode, bendShapeGrp)
			bendNode.translate.set([0,0,0])
			bendNode.rotate.set([0,0,180])
			bendNode.scale.set([0.5,0.5,0.5])
			bendNode.message >> bendShapeAttr[i]
			makeIdentity(bendNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
			bendShape = bendNode.getShapes()[0]
			col.setViewportRGB(bendShape, self.colorsOffset[side])
			parentConstraint(startMidEnd[i], bendShapeGrp)

		# PV Shape
		pvShapeGrp = createNode('transform', n='%s_%s' % (startMidEnd[1].shortName(), names['pvShapeGrp']), p=shapesGrp)
		if mirrorFitRig:
			unitConvert.output >> pvShapeGrp.scaleX
		else:
			fitNode.controlScaleResult >> pvShapeGrp.scaleX
		fitNode.controlScaleResult >> pvShapeGrp.scaleY
		fitNode.controlScaleResult >> pvShapeGrp.scaleZ
		nodeList.append(pvShapeGrp)
		freezeList.append(pvShapeGrp)
		pvNode = ls(rb.shapeMaker(name='%s_%s' % (startMidEnd[1].shortName(), names['pvShape']), shape=4))[0]
		nodeList.append(pvNode)
		parent(pvNode, pvShapeGrp)
		pvNode.translate.set([0,0,0])
		pvNode.rotate.set([0,0,90])
		pvNode.scale.set([0.2,0.2,0.2])
		pvNode.message >> ikShapeAttr[1]
		makeIdentity(pvNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
		pvShape = pvNode.getShapes()[0]
		col.setViewportRGB([pvShape], self.colorsIK[side])
		parentConstraint(pv, pvShapeGrp)


		# for j in range(2):
		# 	for i in range(12):
		# 		#Offset shapes
		# 		pass

		for jnt in fitNode.jointsList.get():
			if hasAttr(jnt, 'worldOrientUp'):
				jnt.worldOrientUp.set(0)
				jnt.up.set(1)
				connectAttr(fitNode.pv.inputs()[0].message, jnt.worldOrientObject)



		for node in nodeList:
			# print node
			if not hasAttr(node, 'fitNode'):
				addAttr(node, k=1, h=self.hidden, at='message', ln='fitNode')
			fitNode.deleteList.connect(node.fitNode)
			# if not isConnected(node.fitNode, fitNode.deleteList):
			# 	node.fitNode.connect(fitNode.deleteList, nextAvailable=1, f=1)

		print "\nThree point fitRig Finished"
		return fitNode


	def mirrorFitRig(self, fitNode):
		'''
		Digs through and finds mirror joints to each join in provided fitrig, and uses those joints to create a new one.
		Connects result attributes
		'''
		# Get joints 
		joints = fitNode.jointsList.get()
		if self.dev:
			print 'Joints:'
			print joints

		# Error check
		if not all(self.hasMirror(j) for j in joints):
			print 'Failed Joints: '
			print failList
			raise Exception('Not all joints associated with fitNode have mirrored joints connected.')
			# Add options for specifying joints to be mirrored?

		# Get mirror joints
		mirrorJoints = []
		for j in joints:
			mirrorJoints.append(j.mirror.get())

		if self.dev: 
			print 'Mirrored Joints:'
			print mirrorJoints


		# rigParent = self.fitNode.getParent()
		# mirrorFitRig = fitRig.__init__(self, joints=mirrorJoints, rigType='poleVectorIK')

		# Create mirrored fitRig class instance (or maintain standard class instance? easy link wouldnt be so bad?)
		mirrorFitRig = poleVectorIKFitRig(mirrorJoints, self.fitSkeleton, mirrorFitRig=True)

		# Get fitNode
		mirrorFitNode = mirrorFitRig.fitNode

		attributes = [
		'controlScale',
		'parentSocketIndex',
		'stretch',
		'noMirror',
		'fkScale',
		'orientation',
		'orientChoice',
		'resultPoints_0',
		'startBounds_0',
		'endBounds_0',
		'resultPoints_1',
		'startBounds_1',
		'endBounds_1',
		'globalName',
		'subName0',
		'subName1',
		'subName2',
		'visCategory',
		'bendStyle',
		'inheritScale',
		'doBend'
		]
		# connect attributes in this list and hide right side
		for attribute in attributes:
			fitNode.attr(attribute).connect(mirrorFitNode.attr(attribute), force=1)
			# mirrorFitNode.attr(attribute).set(k=0, cb=0)

		# Pole Vector Control
		fitNode.pv.inputs()[0].translateX 	>> mirrorFitNode.pv.inputs()[0].translateX
		# fitNode.pv.inputs()[0].translateX.set(k=0, cb=0)

		# Gather Output Joints
		oldOutputJointAttrs = fitNode.outputJoints0.elements() + fitNode.outputJoints1.elements()
		outputJointAttrs = mirrorFitNode.outputJoints0.elements() + mirrorFitNode.outputJoints1.elements()
		# Connect offset Values
		for oldOutputJointAttr, outputJointAttr in zip(oldOutputJointAttrs, outputJointAttrs): #attribute
			oldOutputJoint = fitNode.attr(oldOutputJointAttr).inputs()[0]
			outputJoint = mirrorFitNode.attr(outputJointAttr).inputs()[0]
			oldOutputJoint.offset 					>> outputJoint.offset

			# outputJoint.offset.set(k=0, cb=0)


		if not hasAttr(fitNode, 'mirror'):
			addAttr(fitNode, ln='mirror', at='message', k=1)
		if not hasAttr(mirrorFitNode, 'mirror'):
			addAttr(mirrorFitNode, ln='mirror', at='message', k=1)
		mirrorFitNode.mirror.connect(fitNode.mirror)

		if self.dev: print 'Mirror Fit Node: %s' % mirrorFitNode
		return mirrorFitNode
		



	# def build(self):
	# 	if self.dev: print self.fitNode

	# 	rigNode = None
	# 	if self.dev: reload(buildRig)
	# 	rigNode = buildRig.threePointIK(self.fitNode).rigNode
		
	# 	if rigNode:
	# 		col.setOutlinerRGB([rigNode], self.colorsIK[self.fitNode.side.get()])
	# 		if not isConnected(self.fitNode.rigNode, rigNode.self.fitNode):
	# 			self.fitNode.rigNode.connect(rigNode.self.fitNode)

	# 	return rigNode

# =================================================================================

class aimIKFitRig(fitRig):

	def __init__(self, joints=None, fitSkele=None, fitNode=None, mirrorFitRig=False, *args, **kwargs):
		if fitSkele is None:
			try:
				fitSkele = ls('skeleNode_META')[0]
			except:
				raise Exception('Fit Skeleton node not found.')

		self.fitSkeleton = fitSkele

		# ERROR CHECKS
		self.rigType = 'aimIK'
		if self.dev: print 'RUNNING AIM IK RIG'
		if self.dev: print 'CHECKING FOR ERRORS...'

		if self.dev: print len(joints)
		if not len(joints) == 2:
			raise Exception('Wrong number of joints specified for AimIK fitRig. Select 2 joints.')

		# FITNODE GLOBAL ATTRIBUTES
		fitRig.__init__(self, joints=joints, rigType=self.rigType)
		if self.dev:
			print 'FITNODE'
			print self.fitNode

		self.fitNode.subName1.set('%sEnd' % self.fitNode.subName0.get())

		# FITNODE SPECIFIC ATTRIBUTES
		self.fitNode = self.aimIKInit(self.fitNode, mirrorFitRig=mirrorFitRig)

		# MIRRORING
		# Automatically mirror if all mirror joints found (and mirroring hasn't already been done)
		if not mirrorFitRig and all(self.hasMirror(j) for j in joints):
			print 'Apply Mirroring'
			mirrorFitNode = self.mirrorFitRig(self.fitNode)


	def aimIKInit(self, fitNode, mirrorFitRig=False):
		'''Takes two points and converts them into aimIK rig
		'''

		start, end = fitNode.jointsList.get()

		startEnd = [start, end]


		globalName = fitNode.globalName.get()
		suffix = ''
		rigType = fitNode.rigType.get()

		settings = self.fitGroup
		fitrigGroup = self.fitRigsGrp

		side = fitNode.side.get()

		# ========================================= Names ==========================================
		names = {
		'fitNodeName':				'%s_fitNode%s'						% (start, suffix),
		'startDecmpName':			'%s_fitNode_startDecmp%s'			% (start, suffix),
		'endDecmpName':				'%s_fitNode_endDecmp%s'				% (start, suffix),
		'distName':					'%s_fitNode_length%s'				% (start, suffix),
		'vecName': 					'%s_%s_upVector%s' 					% (start, rigType, suffix),
		'controlScaleMult': 		'%s_%s_controlScaleMult%s' 			% (start, rigType, suffix),
		'lengthCtrlScaleResult': 	'%s_%s_lengthCtrlScaleResult%s'		% (start, rigType, suffix),
		'lengthAdjustMult': 		'%s_%s_lengthAdjustMult%s' 			% (start, rigType, suffix),
		'lengthBasedScalingBlend': 	'%s_%s_lengthBasedScalingBlend%s' 	% (start, rigType, suffix),
		'grpName': 					'%s_%s%s' 							% (start, rigType, suffix),
		'worldGrpName': 			'%s_%s_noTransform%s' 				% (start, rigType, suffix),
		'controlsGroup': 			'%s_%s_controlsGroup%s' 			% (start, rigType, suffix),
		'shapesGrp': 				'%s_%s_shapesGroup%s' 				% (start, rigType, suffix),
		'startShapeGrp': 			'%s_%s_startShapeGrp%s' 			% (start, rigType, suffix),
		'endShapeGrp': 				'%s_%s_endShapeGrp%s' 				% (start, rigType, suffix),
		'startShape': 				'%s_%s_startShape%s' 				% (start, rigType, suffix),
		'fkShape': 					'%s_%s_FKShape%s' 					% (start, rigType, suffix),
		'endShape': 				'%s_%s_endShape%s' 					% (start, rigType, suffix),
		'startOriBuf': 				'%s_%s_startOriBuf%s' 				% (start, rigType, suffix),
		'startOriCtrl': 			'%s_%s_startOriCtrl%s' 				% (start, rigType, suffix),
		'endOriBuf': 				'%s_%s_endOriBuf%s' 				% (start, rigType, suffix),
		'endOriCtrl': 				'%s_%s_endOriCtrl%s' 				% (start, rigType, suffix),
		'startCtrl': 				'%s_%s_startCtrl%s' 				% (start, rigType, suffix),
		'endCtrl': 					'%s_%s_endCtrl%s' 					% (start, rigType, suffix),
		'startPiv': 				'%s_%s_startPiv%s' 					% (start, rigType, suffix),
		'endPiv': 					'%s_%s_endPiv%s' 					% (start, rigType, suffix),
		'startPivBuf': 				'%s_%s_startPivBuf%s' 				% (start, rigType, suffix),
		'endPivBuf': 				'%s_%s_endPivBuf%s' 				% (start, rigType, suffix),
		'bufUpName':				'%s_%s_bufUp%s' 					% (start, rigType, suffix),
		'oriUpName':				'%s_%s_oriUp%s' 					% (start, rigType, suffix),
		'oriUpJointName':			'%s_%s_oriUpJoint%s' 				% (start, rigType, suffix),
		'upName':					'%s_%s_up%s' 						% (start, rigType, suffix),
		'orientChoice':				'%s_%s_oriChoice%s' 				% (start, rigType, suffix),
		'endOriOrientRev':			'%s_%s_endOriOrientRev%s' 			% (start, rigType, suffix),
		'startOriBufOriOrientRev':	'%s_%s_startOriBufOriOrientRev%s' 	% (start, rigType, suffix),
		'midCtrlsGrp':				'%s_%s_midCtrlsGrp%s' 				% (start, rigType, suffix),
		'parameterAdd':				'%s_%s_parameterAdd%s' 				% (start, rigType, suffix),
		'parameterDiv':				'%s_%s_parameterDiv%s' 				% (start, rigType, suffix),
		'pointRev':					'%s_%s_pointRev%s' 					% (start, rigType, suffix),
		'midCtrl':					'%s_%s_midCtrl%s' 					% (start, rigType, suffix),
		'startOriUnMirror':			'%s_%s_startOriUnMirror%s' 			% (start, rigType, suffix),
		'endOriUnMirror':			'%s_%s_endOriUnMirror%s' 			% (start, rigType, suffix),

		}

		# Collections
		nodeList = []
		shapesList = []
		ctrlList = []
		ctrlsPiv = []
		freezeList = []

		if not hasAttr(fitNode, 'length'):
			rb.cbSep(fitNode)
			addAttr(fitNode, ln='length', ct='input', at='float', keyable=True)
			rb.cbSep(fitNode)
			addAttr(fitNode, ln='stretch', nn='Stretch Behavior', ct='attribute', at='enum', enumName='scale:translation', keyable=True)
			addAttr(fitNode, ln='fkScale', nn='Mirroring Behavior', ct='attribute', at='enum', enumName='mirror:behavior:none', keyable=True)
			addAttr(fitNode, ln='orientation', nn='IK Control Orientation', ct='attribute', at='enum', enumName='world:inherit', dv=1, keyable=True)
			addAttr(fitNode, ln='orientChoice', nn='IK Orientation Choice', ct='output', at='enum', enumName='X:Y:Z', keyable=True)

			attributes = [
			'doStretch',
			'doTwist',
			'doVolume',
			'doScaling'
			]
			for attribute in attributes:
				addAttr(fitNode, ln=attribute, dv=1, k=1, min=0, max=1, at='short')


			addAttr(fitNode, ln='orientControls', ct='vis', at='short', min=0, max=1, dv=0, keyable=True)

			rb.cbSep(fitNode)
			addAttr(fitNode, ln='fkVis', ct='vis', at='short', min=0, max=1, dv=1, keyable=True)
			addAttr(fitNode, ln='ikVisStart', ct='vis', at='short', min=0, max=1, dv=1, keyable=True)
			addAttr(fitNode, ln='ikVisEnd', ct='vis', at='short', min=0, max=1, dv=1, keyable=True)
			
			rb.cbSep(fitNode)
			addAttr(fitNode, ln='bindEnd', ct='input', min=0, max=1, dv=0, at='short', k=1)
			addAttr(fitNode, ln='fkEnable', sn='fk', ct='input', min=0, max=1, dv=1, at='short', k=1)
			addAttr(fitNode, ln='ikEndInherit', ct='input', min=0, max=1, dv=1, at='short', k=1)
			addAttr(fitNode, ln='inbetweenJoints', ct='input', at='short', min=0, dv=0, keyable=True)
			rb.cbSep(fitNode)

			# Control Object
			addAttr(fitNode, ln='control', ct='input', at='message', keyable=True)
			addAttr(fitNode, ln='startSocket', ct='input', at='message', keyable=True)
			addAttr(fitNode, ln='endSocket', ct='input', at='message', keyable=True)
			addAttr(fitNode, ln='upSocket', ct='input', at='message', keyable=True)

			# Outputs
			addAttr(fitNode, ln='up', ct='output', at='message', keyable=True)
			addAttr(fitNode, ln='endOutput', ct='output', at='message', keyable=True)
			addAttr(fitNode, ln='startShape', ct='output', at='message', keyable=True)
			addAttr(fitNode, ln='endShape', ct='output', at='message', keyable=True)
			addAttr(fitNode, ln='fkShape', ct='output', at='message', keyable=True)

			
			addAttr(fitNode, ln='subNode', ct='subRig', at='message', keyable=True)


		# Get points
		startEndT = [
		xform(start, q=1, rp=1, ws=1),
		xform(end, q=1, rp=1, ws=1)
		]
		startEndR = [
		xform(start, q=1, ro=1, ws=1),
		xform(end, q=1, ro=1, ws=1)
		]
		
		# Decompose Matrix
		if objExists(names['startDecmpName']):
			delete(ls(names['startDecmpName']))
		startDecmp = createNode('decomposeMatrix', n=names['startDecmpName'])
		nodeList.append(startDecmp)

		if objExists(names['endDecmpName']):
			delete(ls(names['endDecmpName']))
		endDecmp = createNode('decomposeMatrix', n=names['endDecmpName'])
		nodeList.append(endDecmp)

		connectAttr(start.worldMatrix[0], startDecmp.inputMatrix)
		connectAttr(end.worldMatrix[0], endDecmp.inputMatrix)

		# Lengths
		if objExists(names['distName']):
			delete(ls(names['distName']))
		dist = createNode('distanceBetween', n=names['distName'])
		nodeList.append(dist)
		connectAttr(startDecmp.outputTranslate, dist.point1)
		connectAttr(endDecmp.outputTranslate, dist.point2)
		connectAttr(dist.distance, fitNode.length)
		boneLength = dist.distance.get()


		# Vector
		if objExists(names['vecName']):
			delete(ls(names['vecName']))
		vecProd = createNode('vectorProduct', n=names['vecName'])
		vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
		rb.setAttrsWithDictionary(vecProd, vecSetAttr)
		connectAttr(start.worldMatrix[0], vecProd.matrix)
		if not hasAttr(fitNode, 'upVector'):
			addAttr(fitNode, ln='upVector', at='compound', numberOfChildren=3, keyable=True)
			addAttr(fitNode, ln='upVectorX', at='float', parent='upVector', keyable=True)
			addAttr(fitNode, ln='upVectorY', at='float', parent='upVector', keyable=True)
			addAttr(fitNode, ln='upVectorZ', at='float', parent='upVector', keyable=True)
		if refresh:
			connectAttr(vecProd.outputX, fitNode.upVectorX)
			connectAttr(vecProd.outputY, fitNode.upVectorY)
			connectAttr(vecProd.outputZ, fitNode.upVectorZ)
		nodeList.append(vecProd)
		if self.dev:
			print vecProd



		# Control Scaling

		controlScaleMult = createNode('multDoubleLinear', n=names['controlScaleMult']) # Local * Global Scale
		nodeList.append(controlScaleMult)
		fitNode.controlScale >> controlScaleMult.i1
		settings.controlScale >> controlScaleMult.i2

		lengthCtrlScaleResult = createNode('multDoubleLinear', n=names['lengthCtrlScaleResult']) # (local * global) * length
		nodeList.append(lengthCtrlScaleResult)
		controlScaleMult.o >> lengthCtrlScaleResult.i1

		dist.distance >> lengthCtrlScaleResult.i2

		lengthAdjustMult = createNode('multDoubleLinear', n=names['lengthAdjustMult'])
		nodeList.append(lengthAdjustMult)
		lengthCtrlScaleResult.o >> lengthAdjustMult.i1
		lengthAdjustMult.i2.set(0.4)

		lengthBasedScalingBlend = createNode('blendTwoAttr', n=names['lengthBasedScalingBlend'])
		nodeList.append(lengthBasedScalingBlend)
		controlScaleMult.o >> lengthBasedScalingBlend.i[0]
		lengthAdjustMult.o >> lengthBasedScalingBlend.i[1]
		settings.lengthBasedScaling >> lengthBasedScalingBlend.ab

		lengthBasedScalingBlend.o >> fitNode.controlScaleResult


		# Group
		if ls(names['grpName']):
			delete(ls(names['grpName']))
		grpSetAttr = {}
		grp = createNode('transform', n=names['grpName'])
		nodeList.append(grp)
		freezeList.append(grp)
		move(grp, startEndT[0], rpr=1, ws=1)
		xform(grp, ro=startEndR[0], ws=1)
		rb.setAttrsWithDictionary(grp, grpSetAttr)
		parent(grp, fitrigGroup)
		# parent(fitNode, grp, r=True, s=True)
		self.fitNode.v.connect(grp.v)
		if self.dev: print grp


		# No-Translate Group
		if ls(names['worldGrpName']):
			delete(ls(names['worldGrpName']))
		worldGroupAttrs =  {'inheritsTransform': 0}
		worldGrp = createNode('transform', n=names['worldGrpName'])
		rb.setAttrsWithDictionary(worldGrp, worldGroupAttrs)
		parent(worldGrp, grp)
		move(worldGrp, (0, 0, 0), rpr=1, ws=1)
		xform(worldGrp, ro=(0, 0, 0), ws=1)
		nodeList.append(worldGrp)
		freezeList.append(worldGrp)
		if self.dev: print worldGrp


		# Controls Group
		
		controlsGroup = createNode('transform', n=names['controlsGroup'], p=grp)
		move(controlsGroup, [0,0,0], rpr=1, ws=1)
		xform(controlsGroup, ro=[0,0,0], ws=1)
		freezeList.append(controlsGroup)
		nodeList.append(controlsGroup)
		fitNode.controlsVis >> controlsGroup.v
		if self.dev: print controlsGroup


		if mirrorFitRig:
			controlsGroup.sx.set(-1)

		ikShapeOrientMirrorGrp = createNode('transform', n=names.get('ikShapeOrientMirrorGrp', 'rnm_ikShapeOrientMirrorGrp'), p=worldGrp)
		nodeList.append(ikShapeOrientMirrorGrp)
		if mirrorFitRig:
			ikShapeOrientMirrorGrp.sx.set(-1)

		# World oriented object to lock ik controls to
		ikShapeOrient = createNode('transform', n=names.get('ikShapeOrient', 'rnm_ikShapeOrient'), p=ikShapeOrientMirrorGrp)
		nodeList.append(ikShapeOrient)
		rb.lockAndHide([ikShapeOrient], [ 'tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'v' ])
		addAttr(ikShapeOrient, ln='vectorOption1', at='compound', numberOfChildren=3, keyable=True)
		addAttr(ikShapeOrient, ln='vectorOption1X', at='float', parent='vectorOption1', keyable=True, dv=1.5708)
		addAttr(ikShapeOrient, ln='vectorOption1Y', at='float', parent='vectorOption1', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption1Z', at='float', parent='vectorOption1', keyable=True, dv=0)
		# 
		addAttr(ikShapeOrient, ln='vectorOption2', at='compound', numberOfChildren=3, keyable=True)
		addAttr(ikShapeOrient, ln='vectorOption2X', at='float', parent='vectorOption2', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption2Y', at='float', parent='vectorOption2', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption2Z', at='float', parent='vectorOption2', keyable=True, dv=1.5708)
		# 
		addAttr(ikShapeOrient, ln='vectorOption3', at='compound', numberOfChildren=3, keyable=True)
		addAttr(ikShapeOrient, ln='vectorOption3X', at='float', parent='vectorOption3', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption3Y', at='float', parent='vectorOption3', keyable=True, dv=1.5708)
		addAttr(ikShapeOrient, ln='vectorOption3Z', at='float', parent='vectorOption3', keyable=True, dv=0)
		# expose option to fitNode
		orientChoice = createNode('choice', name=names.get('orientChoice', 'rnm_orientChoice'))
		nodeList.append(orientChoice)

		
		ikShapeOrient.vectorOption1 >> orientChoice.input[0]
		ikShapeOrient.vectorOption2 >> orientChoice.input[1]
		ikShapeOrient.vectorOption3 >> orientChoice.input[2]

		fitNode.orientChoice >> orientChoice.selector
		orientChoice.output >> ikShapeOrient.rotate



		# Start Orientation Buf
		startOriBuf = createNode('transform', n=names.get('startOriBuf', 'rnm_startOriBuf'), p=controlsGroup)
		move(startOriBuf, startEndT[0], rpr=1, ws=1)
		xform(startOriBuf, ro=startEndR[0], ws=1)
		nodeList.append(startOriBuf)
		freezeList.append(startOriBuf)
		pointConstraint(startEnd[0], startOriBuf)
		oriC = orientConstraint(startEnd[0], worldGrp, startOriBuf)
		rev = createNode('reverse', n=names.get('startOriBufOriOrientRev', 'rnm_startOriBufOriOrientRev'))
		nodeList.append(rev)
		fitNode.orientation >> rev.inputX
		fitNode.orientation >> oriC.w0
		rev.outputX >> oriC.w1
		oriC.interpType.set(2)
		fitNode.orientControls.connect(startOriBuf.v)

		startOriUnMirror = None
		if mirrorFitRig:
			startOriUnMirror = createNode('transform', n=names['startOriUnMirror'], p=startOriBuf)
			nodeList.append(startOriUnMirror)
			freezeList.append(startOriUnMirror)
			startOriUnMirror.rx.set(-180)
			startOriUnMirror.sx.set(-1)
			

		# Start Orientation Ctrl
		startOriCtrl = createNode('joint', n=names['startOriCtrl'], p=(startOriUnMirror if mirrorFitRig else startOriBuf))
		# startOriCtrlLoc = createNode('locator', n='%sShape' % names['startOriCtrl'], p=startOriCtrl)
		nodeList.append(startOriCtrl)
		startOriCtrl.radius.set(2)
		startOriCtrl.displayLocalAxis.set(1)
		col.setViewportRGB([startOriCtrl], [1,1,1])
		lockList = [ 'tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'v']
		rb.lockAndHide([startOriCtrl], lockList)
		rb.messageConnect(startOriCtrl, 'message', fitNode, 'startOriCtrl')

		# End Orientation Buf
		endOriBuf = createNode('transform', n=names.get('endOriBuf', 'rnm_endOriBuf'), p=controlsGroup)
		move(endOriBuf, startEndT[1], rpr=1, ws=1)
		xform(endOriBuf, ro=startEndR[1], ws=1)
		nodeList.append(endOriBuf)
		freezeList.append(endOriBuf)
		pointConstraint(startEnd[1], endOriBuf)
		oriC = orientConstraint(startEnd[1], worldGrp, endOriBuf)
		rev = createNode('reverse', n=names.get('endOriOrientRev', 'rnm_endOriOrientRev'))
		nodeList.append(rev)
		fitNode.orientation >> rev.inputX
		fitNode.orientation >> oriC.w0
		rev.outputX >> oriC.w1
		oriC.interpType.set(2)
		fitNode.orientControls.connect(endOriBuf.v)

		endOriUnMirror = None
		if mirrorFitRig:
			endOriUnMirror = createNode('transform', n=names['endOriUnMirror'], p=endOriBuf)
			nodeList.append(endOriUnMirror)
			freezeList.append(endOriUnMirror)
			endOriUnMirror.rx.set(-180)
			endOriUnMirror.sx.set(-1)

		# End Orientation Ctrl
		endOriCtrl = createNode('joint', n=names['endOriCtrl'], p=(endOriUnMirror if mirrorFitRig else endOriBuf))
		# endOriCtrlLoc = createNode('locator', n='%sShape' % names['endOriCtrl'], p=endOriCtrl)
		nodeList.append(endOriCtrl)
		endOriCtrl.radius.set(2)
		endOriCtrl.displayLocalAxis.set(1)
		col.setViewportRGB([endOriCtrl], [1,1,1])
		rb.lockAndHide([endOriCtrl], lockList)
		rb.messageConnect(endOriCtrl, 'message', fitNode, 'endOriCtrl')


		# # Mid controls
		# midCtrlsGrp = createNode('transform', n=names['midCtrlsGrp'], p=controlsGroup)
		# freezeList.append(midCtrlsGrp)
		# nodeList.append(midCtrlsGrp)
		# if self.dev: print midCtrlsGrp


		# parameterAdd = createNode('addDoubleLinear', n=names['parameterAdd'])
		# nodeList.append(parameterAdd)
		# fitNode.inbetweenJoints >> parameterAdd.i1
		# parameterAdd.i2.set(1)

		# midCtrls = []
		# for i in range(5):
		# 	parameterDiv = createNode('multiplyDivide', n=names['parameterDiv'])
		# 	nodeList.append(parameterDiv)
		# 	parameterDiv.operation.set(2)
		# 	parameterDiv.i1x.set(i)
		# 	parameterAdd.o.connect(parameterDiv.i2x)
			
		# 	midCtrl = createNode('joint', n=names['midCtrl'], p=midCtrlsGrp)
		# 	addAttr(midCtrl, ln='parameter', min=0, max=1, k=1)
		# 	nodeList.append(midCtrl)
		# 	midCtrls.append(midCtrl)

		# 	parameterDiv.outputX.connect(midCtrl.parameter)
		# 	pnt = pointConstraint(start, end, midCtrl)

		# 	pointRev = createNode('reverse', n=names['pointRev'])
		# 	nodeList.append(pointRev)
		# 	midCtrl.parameter >> pointRev.inputX

		# 	midCtrl.parameter >> pnt.w0
		# 	pointRev.outputX >> pnt.w1

		# lockList = [ 'tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']
		# # rb.lockAndHide(midCtrls, lockList)


		# Shapes Group
		shapesGrp = createNode('transform', n=names['shapesGrp'], p=grp)
		nodeList.append(shapesGrp)
		freezeList.append(shapesGrp)
		if mirrorFitRig:
			shapesGrp.sx.set(-1)

		# Shapes
		startShapeGrp = createNode('transform', n='%s_%s' % (startEnd[0].shortName(), names['startShapeGrp']), p=shapesGrp)
		nodeList.append(startShapeGrp)
		fitNode.controlScaleResult >> startShapeGrp.scaleX
		fitNode.controlScaleResult >> startShapeGrp.scaleY
		fitNode.controlScaleResult >> startShapeGrp.scaleZ
		freezeList.append(startShapeGrp)

		
		

		startNode = ls(rb.shapeMaker(name='%s_%s' % (startEnd[0].shortName(), names['startShape']), shape=8))[0]
		# fitNode.shapesVis >> startNode.v
		parent(startNode, startShapeGrp)
		startNode.translate.set([0,0,0])
		startNode.rotate.set([0,90,0])
		startNode.scale.set([1,1,1])
		startNode.message >> fitNode.startShape
		makeIdentity(startNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
		startIkShape = startNode.getShapes()[0]
		col.setViewportRGB([startIkShape], self.colorsIK[side])
		nodeList.append(startNode)

		ikStartCtrlVisMult = createNode('multDoubleLinear', n=names.get('ikStartCtrlVisMult', 'ikStartCtrlVisMult'))
		nodeList.append(ikStartCtrlVisMult)
		fitNode.shapesVis >> ikStartCtrlVisMult.i1
		fitNode.ikVisStart >> ikStartCtrlVisMult.i2
		ikStartCtrlVisMult.o >> startNode.v
		


		fkNode = ls(rb.shapeMaker(name='%s_%s' % (startEnd[0].shortName(), names['fkShape']), shape=3))[0]
		fitNode.shapesVis >> fkNode.v
		parent(fkNode, startShapeGrp)
		fkNode.translate.set([0,0,0])
		fkNode.rotate.set([180,0,0])
		fkNode.scale.set([0.5,0.5,0.5])
		fkNode.message >> fitNode.fkShape
		makeIdentity(fkNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
		startIkShape = fkNode.getShapes()[0]
		col.setViewportRGB([startIkShape], self.colorsFK[side])
		nodeList.append(fkNode)

		fkCtrlVisMult = createNode('multDoubleLinear', n=names.get('fkCtrlVisMult', 'fkCtrlVisMult'))
		nodeList.append(fkCtrlVisMult)
		fitNode.shapesVis >> fkCtrlVisMult.i1
		fitNode.fkVis >> fkCtrlVisMult.i2
		fkCtrlVisMult.o >> fkNode.v
		

		pointConstraint(startEnd[0], startShapeGrp)
		oriC = orientConstraint(ikShapeOrient, startShapeGrp)
		# rev = createNode('reverse', n=names.get('rnm_ikShapeOrientRev', 'rnm_ikShapeOrientRev'))
		# nodeList.append(rev)
		# fitNode.orientation >> rev.inputX
		# fitNode.orientation >> oriC.w0
		# rev.outputX >> oriC.w1
		# oriC.interpType.set(2)

		endShapeGrp = createNode('transform', n='%s_%s' % (startEnd[1].shortName(), names['endShapeGrp']), p=shapesGrp)
		nodeList.append(endShapeGrp)
		fitNode.controlScaleResult >> endShapeGrp.scaleX
		fitNode.controlScaleResult >> endShapeGrp.scaleY
		fitNode.controlScaleResult >> endShapeGrp.scaleZ
		freezeList.append(endShapeGrp)

		endIkNode = ls(rb.shapeMaker(name='%s_%s' % (startEnd[1].shortName(), names['endShape']), shape=8))[0]
		# ikCtrlVisMult.o >> endIkNode.v
		parent(endIkNode, endShapeGrp)
		endIkNode.translate.set([0,0,0])
		endIkNode.rotate.set([0,90,0])
		endIkNode.scale.set([1,1,1])
		endIkNode.message >> fitNode.endShape
		makeIdentity(endIkNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
		endIkShape = endIkNode.getShapes()[0]
		col.setViewportRGB([endIkShape], self.colorsIK[side])
		nodeList.append(endIkNode)
		# ikEndInheritRev.ox.connect(endIkNode.v)

		ikEndCtrlVisMult = createNode('multDoubleLinear', n=names.get('ikEndCtrlVisMult', 'ikEndCtrlVisMult'))
		nodeList.append(ikEndCtrlVisMult)
		fitNode.shapesVis >> ikEndCtrlVisMult.i1
		fitNode.ikVisEnd >> ikEndCtrlVisMult.i2
		ikEndCtrlVisMult.o >> endIkNode.v


		pointConstraint(startEnd[1], endShapeGrp)
		oriC = orientConstraint(ikShapeOrient, endShapeGrp)
		# fitNode.orientation >> oriC.w0
		# rev.outputX >> oriC.w1
		# oriC.interpType.set(2)

		# parentConstraint(startEnd[1], endShapeGrp)

		# Up Buffer
		if ls(names['bufUpName']):
			delete(ls(names['bufUpName']))
		bufUpSetAttrs = {}
		bufUp = createNode('transform', n=names['bufUpName'], p=controlsGroup)
		nodeList.append(bufUp)
		freezeList.append(bufUp)
		move(bufUp, startEndT[0], rpr=1, ws=1)
		xform(bufUp, ro=startEndR[0], ws=1)
		rb.setAttrsWithDictionary(bufUp, bufUpSetAttrs)
		# pointConstraint(start, bufUp)
		parentConstraint(start, bufUp)

		# if mirrorFitRig:
			# print 'mirror yes'
			# bufUp.sx.set(-1)
			# aimConstraint(start, bufUp, aimVector=[-1,0,0], upVector=[0,1,0], worldUpType='objectrotation', worldUpObject=start)
			
	
		if self.dev: print bufUp

		# Up Direction Control
		'''
		Aim to end joint, figure out up orientation dealie
		'''
		oriUp = createNode('transform', n=names['oriUpName'], p=bufUp)
		nodeList.append(oriUp)
		ctrlList.append(oriUp)
		freezeList.append(oriUp)
		if self.dev: print oriUp
		col.setViewportRGB(oriUp, [0.5,1,0.5])


		# Up Direction Joint
		oriUpJoint = createNode('joint', n=names['oriUpJointName'], p=oriUp)
		nodeList.append(oriUpJoint)
		freezeList.append(oriUpJoint)
		oriUpJoint.radius.set(0)
		oriUpJoint.overrideEnabled.set(1),
		oriUpJoint.overrideDisplayType.set(2)
		if self.dev: print oriUpJoint
		
		# Up Control
		upSetAttrs = { 'radius': 1, 'tz': boneLength,  'overrideEnabled': 1, 'overrideDisplayType': 0 }
		up = createNode('joint', n=names['upName'], p=oriUpJoint)
		nodeList.append(up)
		up.message.connect(fitNode.up)
		rb.setAttrsWithDictionary(up, upSetAttrs)
		col.setViewportRGB(up, [0.5,1,0.5])
		addAttr(up, ln='upDirection', at='enum', enumName='Y:Y-:Z:Z-', k=1)
		rb.lockAndHide([up], ['rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v'])
		# transformLimits(up, tz=[0.001,1], etz=[1,0])
		if self.dev: print up
		if hasAttr(start, 'worldOrientObject'):
			if not start.worldOrientObject.get():
				up.message.connect(start.worldOrientObject)

		# World oriented object to lock ik controls to
		addAttr(up, ln='choice0', at='float', keyable=0, dv=1.5708*3)
		addAttr(up, ln='choice1', at='float', keyable=0, dv=1.5708)
		addAttr(up, ln='choice2', at='float', keyable=0, dv=0)
		addAttr(up, ln='choice3', at='float', keyable=0, dv=1.5708*2)

		orientChoice = createNode('choice', name=names.get('orientChoice', 'rnm_orientChoice'))
		nodeList.append(orientChoice)
		
		up.choice0 >> orientChoice.input[0]
		up.choice1 >> orientChoice.input[1]
		up.choice2 >> orientChoice.input[2]
		up.choice3 >> orientChoice.input[3]

		up.upDirection >> orientChoice.selector
		orientChoice.output >> oriUp.rotateX



		# if mirrorFitRig:
		# 	aimConstraint(ctrls[1], start, upVector=[0,1,0], wut='objectrotation', worldUpVector=[0,-1,0], wuo=ctrlsPiv[0], aimVector=[-1,0,0])
		# 	# parentConstraint(ctrlsPiv[0], start)
		# else:
		# 	aimConstraint(ctrls[1], start, upVector=[0,1,0], wut='objectrotation', worldUpVector=[0,1,0], wuo=ctrlsPiv[0], aimVector=[1,0,0])
		# 	# parentConstraint(ctrlsPiv[0], start)

		# pointConstraint(ctrls[0], start)

		# if not len(end.getShapes()):
		# 	parentConstraint(ctrlPivs[1], end, mo=1)


		# Finalize
		# for ctrl in ctrlList:
		# 	# parent(fitNode, ctrl, s=1, add=1)
		# 	rb.ctrlSetupStandard(ctrl, ctrlSet=None, pivot=False, ro=False)

		# fitNode.orientation.set(1)

		for node in nodeList:
			addAttr(node, k=1, h=self.hidden, at='message', ln='fitNode')
			# node.fitNode.connect(fitNode.deleteList, nextAvailable=1, f=1)
			fitNode.deleteList.connect(node.fitNode)
		

		print "\nTwo-Point FitRig Finished"
		return fitNode

	#===================================================================================================
	#===================================================================================================

	def mirrorFitRig(self, fitNode):
		'''
		Digs through and finds mirror joints to each join in provided fitrig, and uses those joints to create a new one.
		Connects result attributes
		'''
		# Get joints 
		joints = fitNode.jointsList.get()
		if self.dev:
			print 'Joints:'
			print joints

		# Error check
		if not all(self.hasMirror(j) for j in joints):
			print 'Failed Joints: '
			print failList
			raise Exception('Not all joints associated with fitNode have mirrored joints connected.')
			# Add options for specifying joints to be mirrored?

		# Get mirror joints
		mirrorJoints = []
		for j in joints:
			mirrorJoints.append(j.mirror.get())

		if self.dev: 
			print 'Mirrored Joints:'
			print mirrorJoints


		# rigParent = self.fitNode.getParent()
		# mirrorFitRig = fitRig.__init__(self, joints=mirrorJoints, rigType='poleVectorIK')

		# Create mirrored fitRig class instance (or maintain standard class instance? easy link wouldnt be so bad?)
		mirrorFitRig = aimIKFitRig(mirrorJoints, self.fitSkeleton, mirrorFitRig=True)

		# Get fitNode
		mirrorFitNode = mirrorFitRig.fitNode
		attributes = [
			'globalName',
			'subName0',
			'subName1',
			'controlScale',
			'parentSocketIndex',
			'visCategory',
			'orientation',
			'orientChoice',
			'stretch',
			'fkScale',
			'bindEnd',
			'fk',
			'inbetweenJoints',
			'orientControls',
			'ikEndInherit',
			'fkVis',
			'ikVisStart',
			'ikVisEnd',
			'inheritScale',
			'doStretch',
			'doTwist',
			'doVolume',
			'doScaling',
			'twistAxis'
		]


		# up attributes
		fitNode.up.inputs()[0].translate >> mirrorFitNode.up.inputs()[0].translate
		fitNode.up.inputs()[0].upDirection >> mirrorFitNode.up.inputs()[0].upDirection
		fitNode.up.inputs()[0].radius >> mirrorFitNode.up.inputs()[0].radius

		fitNode.startOriCtrl.get().rotate >> mirrorFitNode.startOriCtrl.get().rotate
		fitNode.endOriCtrl.get().rotate >> mirrorFitNode.endOriCtrl.get().rotate

		# connect attributes in this list and hide right side
		for attribute in attributes:
			try:
				fitNode.attr(attribute).connect(mirrorFitNode.attr(attribute), force=1)
			except:
				warning('FitNode attribute mirroring error: %s' % attribute)
			# mirrorFitNode.attr(attribute).set(k=0, cb=0)


		if not hasAttr(fitNode, 'mirror'):
			addAttr(fitNode, ln='mirror', at='message', k=1)
		if not hasAttr(mirrorFitNode, 'mirror'):
			addAttr(mirrorFitNode, ln='mirror', at='message', k=1)
		mirrorFitNode.mirror.connect(fitNode.mirror)


		if self.dev: print 'Mirror Fit Node: %s' % mirrorFitNode
		return mirrorFitNode

# =================================================================================

class bezierSplineFitRig(fitRig):


	def __init__(self, joints=None, fitSkele=None, fitNode=None, mirrorFitRig=False, *args, **kwargs):
		if fitSkele is None:
			try:
				fitSkele = ls('skeleNode_META')[0]
			except:
				raise Exception('Fit Skeleton node not found.')

		self.fitSkeleton = fitSkele

		# ERROR CHECKS
		self.rigType = 'bezierIK'
		if self.dev: print 'RUNNING BEZIER IK RIG'
		if self.dev: print 'CHECKING FOR ERRORS...'

		# if self.dev: print len(joints)
		if not len(joints) == 2:
			raise Exception('Wrong number of joints specified for bezier IK fitRig. Select 2 joints.')

		# FITNODE GLOBAL ATTRIBUTES
		fitNode = fitRig.__init__(self, joints=joints, rigType=self.rigType)

		if self.dev:
			print 'FITNODE'
			print self.fitNode

		# FITNODE SPECIFIC ATTRIBUTES
		self.fitNode = self.bezierIKInit(self.fitNode, mirrorFitRig=mirrorFitRig)

		# MIRRORING
		# Automatically mirror if all mirror joints found (and mirroring hasn't already been done)
		if not mirrorFitRig and all(self.hasMirror(j) for j in joints):
			print 'Apply Mirroring'
			mirrorFitNode = self.mirrorFitRig(self.fitNode)

	def bezierIKInit(self, fitNode, mirrorFitRig=False):
		'''
		To do:
		use xCubes for fk

		'''
		start = fitNode.jointsList[0].inputs()[0]
		end = fitNode.jointsList[1].inputs()[0]

		startEnd = [start, end]
		
		defJ = 4
		maxJ = 12

		globalName = fitNode.globalName.get()
		suffix = ''
		rigType = fitNode.rigType.get()

		settings = self.fitGroup
		fitrigGroup = self.fitRigsGrp

		side = fitNode.side.get()
		
				
		namesList = [
		{'name': 'startDecmp', 		'warble': 'decmp',	'side': side, 	'other': [suffix, rigType] },
		{'name': 'endDecmp', 		'warble': 'decmp',	'side': side, 	'other': [suffix, rigType] },
		]



		# ========================================= Names ==========================================
		names = {
		'fitNode':					'%s_fitNode%s'						% (start, suffix),
		'startDecmp':				'%s_fitNode_startDecmp%s'			% (start, suffix),
		'endDecmp':					'%s_fitNode_endDecmp%s'				% (start, suffix),
		'dist':						'%s_fitNode_length%s'				% (start, suffix),
		'grp': 						'%s_%s%s' 							% (start, rigType, suffix),
		'vec': 						'%s_%s_upVector%s' 					% (start, rigType, suffix),
		'worldGrp': 				'%s_%s_world_GRP%s' 				% (start, rigType, suffix),
		'controlsGroup': 			'%s_%s_controlsGroup%s' 			% (start, rigType, suffix),
		'shapesGrp': 				'%s_%s_shapes_Grp%s' 				% (start, rigType, suffix),
		'curve': 					'%s_%s_Eff_CRV%s' 					% (start, rigType, suffix),
		'resCurve': 				'%s_%s_Result_CRV%s' 				% (start, rigType, suffix),
		'curveInfo':				'%s_%s_curveInfo%s' 				% (start, rigType, suffix),
		'controlScaleMult':			'%s_%s_controlScaleMult%s' 			% (start, rigType, suffix),
		'lengthCtrlScaleResult':	'%s_%s_lengthCtrlScaleResult%s' 	% (start, rigType, suffix),
		'lengthAdjustMult':			'%s_%s_lengthAdjustMult%s' 			% (start, rigType, suffix),
		'lengthBasedScalingBlend':	'%s_%s_lengthBasedScalingBlend%s' 	% (start, rigType, suffix),
		'bufStart': 				'%s_%s_start_BUF%s' 				% (start, rigType, suffix),
		'bufEnd': 					'%s_%s_end_BUF%s' 					% (start, rigType, suffix),
		'startOriCtrl': 			'%s_%s_start_ORI%s' 				% (start, rigType, suffix),
		'endOriCtrl': 				'%s_%s_end_ORI%s' 					% (start, rigType, suffix),
		'startCtrl': 				'%s_%s_start_CTRL%s' 				% (start, rigType, suffix),
		'endCtrl': 					'%s_%s_end_CTRL%s' 					% (start, rigType, suffix),
		'ctrlStartTangent': 		'%s_%s_start_tangent_CTRL%s' 		% (start, rigType, suffix),
		'ctrlEndTangent': 			'%s_%s_end_tangent_CTRL%s' 			% (start, rigType, suffix),
		'indicGroup':				'%s_%s_indicGroup%s'				% (start, rigType, suffix),
		'indicStartTan1':			'%s_%s_indicStartTan1%s'			% (start, rigType, suffix),
		'indicStartTan2':			'%s_%s_indicStartTan2%s'			% (start, rigType, suffix),
		'indicEndTan1':				'%s_%s_indicEndTan1%s'				% (start, rigType, suffix),
		'indicEndTan2':				'%s_%s_indicEndTan2%s'				% (start, rigType, suffix),
		'clsStart': 				'%s_%s_start_CLS%s' 				% (start, rigType, suffix),
		'clsStartTangent': 			'%s_%s_start_tangent_CLS%s' 		% (start, rigType, suffix),
		'clsEnd': 					'%s_%s_end_CLS%s'					% (start, rigType, suffix),
		'clsEndTangent': 			'%s_%s_end_tangent_CLS%s' 			% (start, rigType, suffix),
		'add': 						'%s_%s_distr_ADD%s' 				% (start, rigType, suffix),
		'resultsGroup':	 			'%s_%s_Results_Group%s'				% (start, rigType, suffix),
		'div': 						'%s_%s_distr_DIV%s' 				% (start, rigType, suffix),
		'sr':  						'%s_%s_distr_SR%s' 					% (start, rigType, suffix),
		'cond': 					'%s_%s_distr_COND%s' 				% (start, rigType, suffix),
		'addOffset': 				'%s_%s_distr_offset_ADD%s'			% (start, rigType, suffix),
		'mp': 	 					'%s_%s_distr_MP%s'					% (start, rigType, suffix),
		'resGroup':	 				'%s_%s_distr_result_BUF%s'			% (start, rigType, suffix),
		'resJoint': 				'%s_%s_distr_result_JNT%s' 			% (start, rigType, suffix),
		'fkShapeGrp': 				'%s_%s_fkShapeGroup%s' 				% (start, rigType, suffix),
		'reverseCtrlScale': 		'%s_%s_reverseScaleGroup%s'			% (start, rigType, suffix),
		'ikShapeGrp': 				'%s_%s_ikShapeGrp%s' 				% (start, rigType, suffix),
		'fkShape': 					'%s_%s_fkSNode%s' 					% (start, rigType, suffix),
		'ikShape': 					'%s_%s_ikSNode%s' 					% (start, rigType, suffix),
		'indicStartJoint1': 		'%s_%s_distr_indic_start_JNT%s' 	% (start, rigType, suffix),
		'indicStartJoint2': 		'%s_%s_distr_indic_end_JNT%s' 		% (start, rigType, suffix),
		'ikShapeOrient': 			'%s_%s_ik_Shape_Orient%s' 			% (start, rigType, suffix),
		}
		

		# Collections
		nodeList = []
		shapesList = []
		ctrlList = []
		freezeList = []
		# Rig-specific attributes
		if not hasAttr(fitNode, 'length'):
			rb.cbSep(fitNode)
			addAttr(fitNode, k=1, ct='input', at='float', ln='length')
			addAttr(fitNode, k=1, ct='input', at='float', ln='curveLength')

			rb.cbSep(fitNode)
			addAttr(fitNode, k=1, ct='input', at='short', min=0, max=maxJ, dv= defJ, ln='resultPoints')
			addAttr(fitNode, k=1, ct='input', at='float', min=0, max=1, dv=0, ln='startBounds')
			addAttr(fitNode, k=1, ct='input', at='float', min=0, max=1, dv=1, ln='endBounds')

			rb.cbSep(fitNode)
			addAttr(fitNode, k=1, ct='input', at='float', min=0, max=1, dv=1, ln='stretchLimits')
			addAttr(fitNode, k=1, ct='input', at='enum', ln='style', enumName='FK/IK Switch:IK Only:FK to IK:IK to FK:')

			rb.cbSep(fitNode)
			addAttr(fitNode, ln='orientation', nn='IK Control Orientation', ct='attribute', at='enum', enumName='world:inherit', dv=1, keyable=True)
			addAttr(fitNode, ln='orientChoice', nn='IK Orientation Choice', ct='output', at='enum', enumName='X:Y:Z', keyable=True)


			# rb.cbSep(fitNode)
			addAttr(fitNode, k=1, h=self.hidden, ct='output', at='message', ln='curve')
			addAttr(fitNode, k=1, h=self.hidden, ct='output', at='message', multi=True, ln='outputJoints')

			# Selection attributes
			addAttr(fitNode, k=1, h=self.hidden, ct='selection', at='message', multi=True, ln='fitRigControls')


			# SHAPES
			addAttr(fitNode, ln='startShape', ct='shape', at='message', keyable=True, h=self.hidden)
			addAttr(fitNode, ln='endShape', ct='shape', at='message', keyable=True, h=self.hidden)
			# rb.cbSep(fitNode)
			addAttr(fitNode, ln='fkShapes', ct='output', at='message', multi=True, keyable=True, h=self.hidden)
			
			# rb.cbSep(fitNode)
			addAttr(fitNode, ln='tangent1', ct='output', at='message', keyable=True, h=self.hidden)
			addAttr(fitNode, ln='tangent2', ct='output', at='message', keyable=True, h=self.hidden)

			

		###


		# Get input transform space
		startT = xform(start, q=1, rp=1, ws=1)
		startR = xform(start, q=1, ro=1, ws=1)
		endT = xform(end, q=1, rp=1, ws=1)
		endR = xform(end, q=1, ro=1, ws=1)

		# Decompose Matrix
		startDecmp = createNode('decomposeMatrix', n=names.get('startDecmp', 'rnm_startDecmp'))
		nodeList.append(startDecmp)

		endDecmp = createNode('decomposeMatrix', n=names.get('endDecmp', 'rnm_endDecmp'))
		nodeList.append(endDecmp)

		connectAttr(start.worldMatrix[0], startDecmp.inputMatrix)
		connectAttr(end.worldMatrix[0], endDecmp.inputMatrix)

		# Length
		dist = createNode('distanceBetween', n=names.get('dist', 'rnm_dist'))
		nodeList.append(dist)
		if self.dev: print dist
		startDecmp.outputTranslate	>> dist.point1
		endDecmp.outputTranslate	>> dist.point2
		dist.distance				>> fitNode.length
		

		length = fitNode.length.get()


		# VectorY (?)
		vecProd = createNode('vectorProduct', n=names['vec'])
		vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
		rb.setAttrsWithDictionary(vecProd, vecSetAttr)
		connectAttr(start.worldMatrix[0], vecProd.matrix)
		if not hasAttr(fitNode, 'upVector'):
			addAttr(fitNode, ln='upVector', at='compound', numberOfChildren=3, keyable=True)
			addAttr(fitNode, ln='upVectorX', at='float', parent='upVector', keyable=True)
			addAttr(fitNode, ln='upVectorY', at='float', parent='upVector', keyable=True)
			addAttr(fitNode, ln='upVectorZ', at='float', parent='upVector', keyable=True)
		connectAttr(vecProd.outputX, fitNode.upVectorX)
		connectAttr(vecProd.outputY, fitNode.upVectorY)
		connectAttr(vecProd.outputZ, fitNode.upVectorZ)
		nodeList.append(vecProd)
		if self.dev:
			print vecProd


		# MAIN GROUPS

		# Group
		grp = createNode('transform', n=names.get('grp', 'rnm_grp'), p = fitrigGroup)
		nodeList.append(grp)
		freezeList.append(grp)
		if self.dev: print grp
		move(grp, startT, rpr=1, ws=1)
		xform(grp, ro=startR, ws=1)
		self.fitNode.v.connect(grp.v)
		rb.messageConnect([grp], 'message', fitNode, 'fitGroup')
		# parent(fitNode, grp, r=True, s=True)

		# No-Translate Group
		# worldGrp = createNode('transform', n=names.get('worldGrp', 'rnm_worldGrp'), p=grp)
		# nodeList.append(worldGrp)
		# freezeList.append(worldGrp)
		# if self.dev: print worldGrp
		# worldGrp.inheritsTransform.set(0)
		# move(grp, (0, 0, 0), rpr=1, ws=1)
		# xform(grp, ro=(0, 0, 0), ws=1)

		# No-Translate Group
		worldGroupAttrs =  {'inheritsTransform': 0}
		worldGrp = createNode('transform',  n=names.get('worldGrp', 'rnm_worldGrp'))
		nodeList.append(worldGrp)
		freezeList.append(worldGrp)
		rb.setAttrsWithDictionary(worldGrp, worldGroupAttrs)
		parent(worldGrp, grp)
		worldGrp.t.set([0,0,0])
		worldGrp.r.set([0,0,0])
		if self.dev: print worldGrp
		fitNode.controlsVis >> worldGrp.v


		# Controls Group
		controlsGroup = createNode('transform', n=names.get('controlsGroup', 'rnm_controlsGroup'), p=grp)
		freezeList.append(controlsGroup)
		nodeList.append(controlsGroup)
		if self.dev: print controlsGroup
		move(controlsGroup, (0, 0, 0), rpr=1, ws=1)
		xform(controlsGroup, ro=(0, 0, 0), ws=1)
		fitNode.controlsVis >> controlsGroup.v


		# Shapes Group
		shapesGrp = createNode('transform', n=names.get('shapesGrp', 'rnm_shapesGrp'), p=grp)
		nodeList.append(shapesGrp)
		freezeList.append(shapesGrp)
		fitNode.shapesVis >> shapesGrp.v

		# IK RIG
		# Curve
		boneCurve = curve(d=1, p=[startT, endT], n=names.get('curve', 'rnm_curve'))
		if self.dev: print boneCurve
		boneCurve = rebuildCurve(boneCurve, d=3, ch=False, rpo=True, rt=0, end=1, kr=0, s=0)[0]
		nodeList.append(boneCurve)
		freezeList.append(boneCurve)
		parent(boneCurve, worldGrp)
		rb.messageConnect(boneCurve, 'message', [fitNode], 'curve')


		# Curve shape
		curveShapeAttrs = {'v': 0 }
		curveShape = listRelatives(boneCurve, s=True)[0]
		curveShape = curveShape.rename('%sShape' % boneCurve.shortName())
		rb.setAttrsWithDictionary(curveShape, curveShapeAttrs)

		# Curve Info
		curveInfoAttrs =  {}
		curveInfo = createNode('curveInfo', n=names.get('curveInfo', 'rnm_curveInfo'))
		rb.setAttrsWithDictionary(curveInfo, curveInfoAttrs)
		nodeList.append(curveInfo)
		curveShape.worldSpace[0].connect(curveInfo.inputCurve)
		curveInfo.arcLength.connect(fitNode.curveLength)
		
		if self.dev: print curveInfo


		# CONTROL SCALING
		controlScaleMult = createNode('multDoubleLinear', n=names.get('controlScaleMult', 'rnm_controlScaleMult')) # Local * Global Scale
		nodeList.append(controlScaleMult)
		if self.dev: print controlScaleMult
		fitNode.controlScale 		>> controlScaleMult.i1
		settings.controlScale 		>> controlScaleMult.i2
		
		lengthCtrlScaleResult = createNode('multDoubleLinear', n=names.get('lengthCtrlScaleResult', 'rnm_lengthCtrlScaleResult')) # (local * global) * length
		nodeList.append(lengthCtrlScaleResult)
		if self.dev: print lengthCtrlScaleResult
		controlScaleMult.o 			>> lengthCtrlScaleResult.i1
		curveInfo.arcLength 		>> lengthCtrlScaleResult.i2

		lengthAdjustMult = createNode('multDoubleLinear', n=names.get('lengthAdjustMult', 'rnm_lengthAdjustMult'))
		nodeList.append(lengthAdjustMult)
		if self.dev: print lengthAdjustMult
		lengthAdjustMult.i2.set(0.4)
		lengthCtrlScaleResult.o 	>> lengthAdjustMult.i1

		lengthBasedScalingBlend = createNode('blendTwoAttr', n=names.get('lengthBasedScalingBlend', 'rnm_lengthBasedScalingBlend'))
		nodeList.append(lengthBasedScalingBlend)
		if self.dev: print lengthBasedScalingBlend
		controlScaleMult.o 			>> lengthBasedScalingBlend.i[0]
		lengthAdjustMult.o 			>> lengthBasedScalingBlend.i[1]
		settings.lengthBasedScaling >> lengthBasedScalingBlend.ab
		lengthBasedScalingBlend.o 	>> fitNode.controlScaleResult

		





		# Start Buffer
		if mirrorFitRig:
			bufStartSetAttrs = {'sx':-1, 'sy':-1, 'sz':-1}
		else:
			bufStartSetAttrs = {}
		bufStart = createNode('transform', n=names.get('bufStart', 'rnm_bufStart'))
		nodeList.append(bufStart)
		move(bufStart, startT, rpr=1, ws=1)
		xform(bufStart, ro=startR, ws=1)
		parent(bufStart, controlsGroup)
		parentConstraint(start, bufStart)
		rb.setAttrsWithDictionary(bufStart, bufStartSetAttrs)
		freezeList.append(bufStart)
		if self.dev: print bufStart




		# End Buffer
		if mirrorFitRig:
			bufEndSetAttrs = {'sy': -1, 'sz': -1}
		else:
			bufEndSetAttrs = {'sx': -1}
		bufEnd = createNode('transform', n=names.get('bufEnd', 'rnm_bufEnd'))
		nodeList.append(bufEnd)
		move(bufEnd, endT, rpr=1, ws=1)
		xform(bufEnd, ro=endR, ws=1)
		parent(bufEnd, controlsGroup)
		rb.setAttrsWithDictionary(bufEnd, bufEndSetAttrs)
		parentConstraint(end, bufEnd)
		freezeList.append(bufEnd)
		if self.dev: print bufEnd


		ikShapeOrient = createNode('transform', n=names.get('ikShapeOrient', 'rnm_ikShapeOrient'), p=worldGrp)
		nodeList.append(ikShapeOrient)
		rb.lockAndHide([ikShapeOrient], [ 'tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'v' ])
		addAttr(ikShapeOrient, ln='vectorOption1', at='compound', numberOfChildren=3, keyable=True)
		addAttr(ikShapeOrient, ln='vectorOption1X', at='float', parent='vectorOption1', keyable=True, dv=1.5708)
		addAttr(ikShapeOrient, ln='vectorOption1Y', at='float', parent='vectorOption1', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption1Z', at='float', parent='vectorOption1', keyable=True, dv=0)
		# 
		addAttr(ikShapeOrient, ln='vectorOption2', at='compound', numberOfChildren=3, keyable=True)
		addAttr(ikShapeOrient, ln='vectorOption2X', at='float', parent='vectorOption2', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption2Y', at='float', parent='vectorOption2', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption2Z', at='float', parent='vectorOption2', keyable=True, dv=1.5708)
		# 
		addAttr(ikShapeOrient, ln='vectorOption3', at='compound', numberOfChildren=3, keyable=True)
		addAttr(ikShapeOrient, ln='vectorOption3X', at='float', parent='vectorOption3', keyable=True, dv=0)
		addAttr(ikShapeOrient, ln='vectorOption3Y', at='float', parent='vectorOption3', keyable=True, dv=1.5708)
		addAttr(ikShapeOrient, ln='vectorOption3Z', at='float', parent='vectorOption3', keyable=True, dv=0)
		# expose option to fitNode
		orientChoice = createNode('choice', name=names.get('orientChoice', 'rnm_orientChoice'))
		nodeList.append(orientChoice)

		
		ikShapeOrient.vectorOption1 >> orientChoice.input[0]
		ikShapeOrient.vectorOption2 >> orientChoice.input[1]
		ikShapeOrient.vectorOption3 >> orientChoice.input[2]

		fitNode.orientChoice >> orientChoice.selector
		orientChoice.output >> ikShapeOrient.rotate


		# Start Orientation Buf
		startOriBuf = createNode('transform', n=names.get('startOriBuf', 'rnm_startOriBuf'), p=controlsGroup)
		move(startOriBuf, startT, rpr=1, ws=1)
		xform(startOriBuf, ro=startR, ws=1)
		nodeList.append(startOriBuf)
		freezeList.append(startOriBuf)
		pointConstraint(startEnd[0], startOriBuf)
		oriC = orientConstraint(startEnd[0], ikShapeOrient, startOriBuf)
		rev = createNode('reverse', n=names.get('startOriBufOriOrientRev', 'rnm_startOriBufOriOrientRev'))
		nodeList.append(rev)
		fitNode.orientation >> rev.inputX
		fitNode.orientation >> oriC.w0
		rev.outputX >> oriC.w1
		oriC.interpType.set(2)

		# Start Orientation Ctrl
		startOriCtrl = createNode('transform', n=names.get('startOriCtrl', 'rnm_startOriCtrl'), p=startOriBuf)
		move(startOriCtrl, startT, rpr=1, ws=1)
		xform(startOriCtrl, ro=startR, ws=1)
		nodeList.append(startOriCtrl)


		# End Orientation Buf
		endOriBuf = createNode('transform', n=names.get('endOriBuf', 'rnm_endOriBuf'), p=controlsGroup)
		move(endOriBuf, endT, rpr=1, ws=1)
		xform(endOriBuf, ro=endR, ws=1)
		nodeList.append(endOriBuf)
		freezeList.append(endOriBuf)
		pointConstraint(startEnd[1], endOriBuf)
		oriC = orientConstraint(startEnd[1], ikShapeOrient, endOriBuf)
		rev = createNode('reverse', n=names.get('endOriOrientRev', 'rnm_endOriOrientRev'))
		nodeList.append(rev)
		fitNode.orientation >> rev.inputX
		fitNode.orientation >> oriC.w0
		rev.outputX >> oriC.w1
		oriC.interpType.set(2)

		# End Orientation Ctrl
		endOriCtrl = createNode('transform', n=names.get('endOriCtrl', 'rnm_endOriCtrl'), p=endOriBuf)
		move(endOriCtrl, endT, rpr=1, ws=1)
		xform(endOriCtrl, ro=endR, ws=1)
		nodeList.append(endOriCtrl)


		# Shapes
		startShapeGrp = createNode('transform', n='%s_%s' % (startEnd[0].shortName(), names.get('ikShapeGrp', 'rnm_ikShapeGrp')), p=shapesGrp)
		nodeList.append(startShapeGrp)
		fitNode.controlScaleResult >> startShapeGrp.scaleX
		fitNode.controlScaleResult >> startShapeGrp.scaleY
		fitNode.controlScaleResult >> startShapeGrp.scaleZ
		freezeList.append(startShapeGrp)
		startIkNode = ls(rb.shapeMaker(name='%s_%s' % (startEnd[0].shortName(), names.get('ikShape', 'rnm_ikShape')), shape=1))[0]
		# fitNode.shapesVis >> startIkNode.v
		parent(startIkNode, startShapeGrp)
		startIkNode.translate.set([0,0,0])
		startIkNode.rotate.set([0,0,90])
		startIkNode.scale.set([1.2,1.2,1.2])
		startIkNode.message >> fitNode.startShape
		makeIdentity(startIkNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
		startIkShape = startIkNode.getShapes()[0]
		print side
		col.setViewportRGB([startIkShape], self.colorsIK[side])
		nodeList.append(startIkNode)
		shapesList.append(startIkNode)
		pointConstraint(startEnd[0], startShapeGrp)
		oriC = orientConstraint(startOriCtrl, startShapeGrp)


		endShapeGrp = createNode('transform', n='%s_%s' % (startEnd[1].shortName(), names.get('ikShapeGrp', 'rnm_ikShapeGrp')), p=shapesGrp)
		nodeList.append(endShapeGrp)
		fitNode.controlScaleResult >> endShapeGrp.scaleX
		fitNode.controlScaleResult >> endShapeGrp.scaleY
		fitNode.controlScaleResult >> endShapeGrp.scaleZ
		freezeList.append(endShapeGrp)
		endIkNode = ls(rb.shapeMaker(name='%s_%s' % (startEnd[1].shortName(), names.get('ikShape', 'rnm_ikShape')), shape=1))[0]
		# fitNode.shapesVis >> endIkNode.v
		parent(endIkNode, endShapeGrp)
		endIkNode.translate.set([0,0,0])
		endIkNode.rotate.set([0,0,90])
		endIkNode.scale.set([1.2,1.2,1.2])
		endIkNode.message >> fitNode.endShape
		makeIdentity(endIkNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
		endIkShape = endIkNode.getShapes()[0]
		col.setViewportRGB([endIkShape], self.colorsIK[side])
		nodeList.append(endIkNode)
		shapesList.append(endIkNode)
		pointConstraint(startEnd[1], endShapeGrp)
		oriC = orientConstraint(endOriCtrl, endShapeGrp)
		# Start Tangent Control

		ctrlStartTanSetAttrs = { 'radius': 1.5 } # 'translateX': (fitNode.length.get()/3) 
		ctrlStartTan = createNode('joint', n=names.get('ctrlStartTangent', 'rnm_ctrlStartTangent'), p=bufStart)
		nodeList.append(ctrlStartTan)
		ctrlList.append(ctrlStartTan)
		# color(ctrlStartTan, rgb=[0.5, 1, 0.3])
		col.setViewportRGB(ctrlStartTan, [0.5, 1, 0.3])
		rb.lockAndHide([ctrlStartTan], ['sx', 'sy', 'sz', 'rx', 'ry', 'rz'])
		if self.dev: print ctrlStartTan
		ctrlStartTan.message.connect(fitNode.tangent1)

		# End Tangent Control
		ctrlEndTanSetAttrs = { 'radius': 1.5 }
		ctrlEndTan = createNode('joint', n=names.get('ctrlEndTangent', 'rnm_ctrlEndTangent'), p=bufEnd)
		nodeList.append(ctrlEndTan)
		ctrlList.append(ctrlEndTan)
		col.setViewportRGB(ctrlEndTan, [0.5, 1, 0.3])
		rb.lockAndHide([ctrlEndTan], ['sx', 'sy', 'sz', 'rx', 'ry', 'rz'])
		if self.dev: print ctrlEndTan
		ctrlEndTan.message.connect(fitNode.tangent2)

		# Indic group
		indicGroup = createNode('transform', n=names.get('indicGroup', 'rnm_indicGroup'), p=worldGrp)
		nodeList.append(indicGroup)
		freezeList.append(indicGroup)

		# Start Tangent Indic1
		indicStartTan1Attrs = {'radius': 0, 'overrideEnabled': 1, 'overrideDisplayType': 2}
		indicStartTan1 = createNode('joint', n=names.get('indicStartTan1', 'rnm_indicStartTan1'), p=indicGroup)
		nodeList.append(indicStartTan1)
		rb.setAttrsWithDictionary(indicStartTan1, indicStartTan1Attrs)
		pointConstraint(start, indicStartTan1)
		freezeList.append(indicStartTan1)
		if self.dev: print indicStartTan1

		indicStartTan2Attrs = {'radius': 0, 'overrideEnabled': 1, 'overrideDisplayType': 2}
		indicStartTan2 = createNode('joint', n=names.get('indicStartTan2', 'rnm_indicStartTan2'), p=indicStartTan1)
		nodeList.append(indicStartTan2)
		rb.setAttrsWithDictionary(indicStartTan2, indicStartTan2Attrs)
		pointConstraint(ctrlStartTan, indicStartTan2)
		freezeList.append(indicStartTan2)
		if self.dev: print indicStartTan2

		# End Tangent Indic1
		indicEndTan1Attrs = {'radius': 0, 'overrideEnabled': 1, 'overrideDisplayType': 2}
		indicEndTan1 = createNode('joint', n=names.get('indicEndTan1', 'rnm_indicEndTan1'), p=indicGroup)
		nodeList.append(indicEndTan1)
		rb.setAttrsWithDictionary(indicEndTan1, indicEndTan1Attrs)
		pointConstraint(end, indicEndTan1)
		freezeList.append(indicEndTan1)
		if self.dev: print indicEndTan1

		indicEndTan2Attrs = {'radius': 0, 'overrideEnabled': 1, 'overrideDisplayType': 2}
		indicEndTan2 = createNode('joint', n=names.get('indicEndTan2', 'rnm_indicEndTan2'), p=indicEndTan1)
		nodeList.append(indicEndTan2)
		rb.setAttrsWithDictionary(indicEndTan2, indicEndTan2Attrs)
		pointConstraint(ctrlEndTan, indicEndTan2)
		freezeList.append(indicEndTan2)
		if self.dev: print indicEndTan2



		# Start Cluster
		clsSetAttrs = { 'v': 0 }
		clsStart = cluster((boneCurve + '.cv[0]'), n=names.get('clsStart', 'rnm_clsStart'))[1]
		nodeList.append(clsStart)
		# addFitRigAttrs(clsStart)
		rb.setAttrsWithDictionary(clsStart, clsSetAttrs)
		parent(clsStart, bufStart)
		freezeList.append(clsStart)
		if self.dev: print clsStart

		# Start Tangent Cluster
		clsTSetAttrs = { 'v': 0 }
		clsTStart = cluster((boneCurve + '.cv[1]'), n=names.get('clsStartTangent', 'rnm_clsStartTangent'))[1]
		nodeList.append(clsTStart)
		move(clsTStart, startT, rpr=1, ws=1)
		rb.setAttrsWithDictionary(clsTStart, clsTSetAttrs)
		parent(clsTStart, ctrlStartTan)
		freezeList.append(clsTStart)
		if self.dev: print clsTStart


		# End Cluster
		clsEnd = cluster((boneCurve + '.cv[3]'), n=names.get('clsEnd', 'rnm_clsEnd'))[1]
		nodeList.append(clsEnd)
		rb.setAttrsWithDictionary(clsEnd, clsSetAttrs)
		parent(clsEnd, bufEnd)
		freezeList.append(clsEnd)
		if self.dev: print clsEnd

		# End Tangent Cluster
		clsTEnd = cluster((boneCurve + '.cv[2]'), n=names.get('clsEndTangent', 'rnm_clsEndTangent'))[1]
		nodeList.append(clsTEnd)
		move(clsTEnd, endT, rpr=1, ws=1)
		rb.setAttrsWithDictionary(clsTEnd, clsTSetAttrs)
		parent(clsTEnd, ctrlEndTan)
		freezeList.append(clsTEnd)
		if self.dev: print clsTEnd


		# Set controls translate attributes after cluster initialzed
		rb.setAttrsWithDictionary(ctrlStartTan, ctrlStartTanSetAttrs)
		rb.setAttrsWithDictionary(ctrlEndTan, ctrlEndTanSetAttrs)


		# ===============================================================================
		# def populateCurveWithJoints(curve, start, end, controlNode, default=3, max=12):
		

		curveShape = listRelatives(boneCurve, s=True)
		if len(curveShape) == 0:
			raise Exception('No shape node found.')

		# add node
		addSetAttrs = {'i2': 1}
		add = createNode('addDoubleLinear', n=names.get('add', 'rnm_add'))
		nodeList.append(add)
		rb.setAttrsWithDictionary(add, addSetAttrs)
		connectAttr(fitNode.resultPoints, add.i1)
		if self.dev: print add

		# Results group
		resultsGroup = createNode('transform', n=names.get('resultsGroup', 'rnm_resultsGroup'), p=worldGrp)
		nodeList.append(resultsGroup)

		if self.dev:
			print "\n"
			print 'Per Point:'
			print "\n"

		resJoints = []

		#For each joint in the max list
		for i in range(maxJ):
			# name objects
			if range(maxJ) < 10:
				d = i
			elif range(maxJ) < 100:
				d = '%01d' % i
			else:
				d = '%02d' % i

			if self.dev:
				print "\n"
				print d

			divName = 			'%s_%s' % (names.get('div', 'rnm_div'), d)
			srName = 			'%s_%s' % (names.get('sr', 'rnm_sr'), d)
			condName = 			'%s_%s' % (names.get('cond', 'rnm_cond'), d)
			addOffsetName = 	'%s_%s' % (names.get('addOffset', 'rnm_addOffset'), d)
			mpName = 			'%s_%s' % (names.get('mp', 'rnm_mp'), d)
			resGroupName = 		'%s_%s' % (names.get('resGroup', 'rnm_resGroup'), d)
			jointName = 		'%s_%s' % (names.get('resJoint', 'rnm_resJoint'), d)
			indicStartJoint1 = 	'%s_%s' % (names.get('indicStartJoint1', 'rnm_indicStartJoint1'), d)
			indicStartJoint2 = 	'%s_%s' % (names.get('indicStartJoint2', 'rnm_indicStartJoint2'), d)
			reverseScaleName = 	'%s_%s' % (names.get('reverseCtrlScale', 'rnm_reverseCtrlScale'), d)
			fkShapeGrpName = 	'%s_%s' % (names.get('fkShapeGrp', 'rnm_fkShapeGrp'), d)
			fkShapeName = 		'%s_%s' % (names.get('fkShape', 'rnm_fkShape'), d)

			# divide node
			divSetAttrs = {'i1x': i, 'i2x': 0, 'op':2}
			div = createNode('multiplyDivide', n=divName)
			nodeList.append(div)
			rb.setAttrsWithDictionary(div, divSetAttrs)
			connectAttr(add.o, div.i2x)
			if self.dev: print div


			# set range node
			srSetAttrs = {'oldMinX': 0, 'oldMaxX': 1}
			sr = createNode('setRange', n=srName)
			nodeList.append(sr)
			rb.setAttrsWithDictionary(sr, srSetAttrs)
			connectAttr(div.ox, sr.vx)
			connectAttr(fitNode.startBounds, sr.minX)
			if self.dev: print sr
			

			# condition node
			condSetAttrs = {'firstTerm': i, 'operation': 5, 'colorIfTrueR': 1, 'colorIfTrueG': 1, 'colorIfTrueB': 1, 'colorIfFalseR': 0, 'colorIfFalseG': 1, 'colorIfFalseB': 0 }
			cond = createNode('condition', n=condName)
			nodeList.append(cond)
			rb.setAttrsWithDictionary(cond, condSetAttrs)
			connectAttr(add.o, cond.secondTerm)
			connectAttr(fitNode.endBounds, cond.colorIfTrueG)
			connectAttr(cond.ocg, sr.maxX)
			if self.dev: print cond

			# add node
			addOffset = createNode('addDoubleLinear', n=addOffsetName)
			nodeList.append(addOffset)
			connectAttr(sr.ox, addOffset.i1)
			if self.dev: print addOffset

			# motion path node
			mpSetAttrs = {'fractionMode': True, 'follow': False, 'worldUpType': 3, 'inverseUp': False, 'frontAxis': 0, 'upAxis': 1}
			mp = createNode('motionPath', n=mpName)
			nodeList.append(mp)
			rb.setAttrsWithDictionary(mp, mpSetAttrs)
			connectAttr(curveShape[0].worldSpace[0], mp.geometryPath)
			connectAttr(addOffset.o, mp.u)
			connectAttr(cond.ocr, mp.frozen)
			connectAttr(fitNode.upVector, mp.worldUpVector)
			if self.dev: print mp

			# Group
			resGroup = createNode('transform', n=resGroupName, p=resultsGroup)
			nodeList.append(resGroup)
			connectAttr(mp.allCoordinates, resGroup.translate)
			connectAttr(mp.rotate, resGroup.rotate)
			connectAttr(cond.ocr, resGroup.visibility)
			freezeList.append(resGroup)
			if self.dev: print resGroup

			# Joint
			resJoint = createNode('joint', n=jointName, p=resGroup)
			nodeList.append(resJoint)
			resJoints.append(resJoint)
			freezeList.append(resJoint)
			addAttr(resJoint, ln='offset', k=1)
			addAttr(resJoint, ln='uValue', k=1)
			resJoint.uValue.set(k=0, cb=1)
			connectAttr(resJoint.offset, addOffset.i2)
			connectAttr(mp.uValue, resJoint.uValue)

			
			addAttr(resJoint, ln='fitNode', at='message')
			# resLoc = createNode('locator', n=jointName+'Shape', p=resJoint)
			col.setViewportRGB(resJoint, [1, 1, 0.6])
			resJointIndic = createNode('joint', n=jointName + 'indic', p=resJoint)
			nodeList.append(resJointIndic)
			resJointIndic.radius.set(0.5)
			resJointIndic.overrideEnabled.set(1)
			resJointIndic.overrideDisplayType.set(2)


			# FK Shapes
			fkShapeGrp = createNode('transform', n=fkShapeGrpName, p=shapesGrp)
			nodeList.append(fkShapeGrp)
			# Control scaling
			if mirrorFitRig:
				reverseCtrlScale = createNode('multDoubleLinear', n=reverseScaleName)
				nodeList.append(reverseCtrlScale)
				reverseCtrlScale.i2.set(-1)
				fitNode.controlScaleResult >> reverseCtrlScale.i1
				reverseCtrlScale.o >> fkShapeGrp.scaleX
			else:
				fitNode.controlScaleResult >> fkShapeGrp.scaleX
			fitNode.controlScaleResult >> fkShapeGrp.scaleY
			fitNode.controlScaleResult >> fkShapeGrp.scaleZ
			freezeList.append(fkShapeGrp)
			# fkNode = ls(rb.shapeMaker(name='%s_%s' % (resJoint.shortName(), names.get('fkShape', 'rnm_fkShape')), shape=2))[0]
			fkNode = ls(rb.shapeMaker(name=fkShapeName, shape=8))[0]
			parent(fkNode, fkShapeGrp)
			# fitNode.shapesVis >> fkNode.v
			fkNode.translate.set([0,0,0])
			fkNode.rotate.set([0,0,90])
			fkNode.scale.set([1,.1,.1])
			fkNode.message >> fitNode.fkShapes[i]
			makeIdentity(fkNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
			nodeList.append(fkNode)
			shapesList.append(fkNode)
			fkShape = fkNode.getShapes()[0]
			connectAttr(cond.ocr, fkShape.visibility)
			col.setViewportRGB(fkShape, self.colorsFK[side])
			parentConstraint(resJoint, fkShapeGrp)


			if i>0:
				aimConstraint(resJoint, resJoints[i-1], wut='objectrotation', wuo = start, upVector=[0,1,0], aimVector=[1,0,0])

				indicStartJoint1Attrs = {'radius': 0, 'overrideEnabled': 1, 'overrideDisplayType': 2}
				indicStartJoint1 = createNode('joint', n=indicStartJoint1, p=resJoints[i-1])
				nodeList.append(indicStartJoint1)
				rb.setAttrsWithDictionary(indicStartJoint1, indicStartJoint1Attrs)
				if self.dev: print indicStartJoint1

				indicStartJoint2Attrs = {'radius': 0, 'overrideEnabled': 1, 'overrideDisplayType': 2}
				indicStartJoint2 = createNode('joint', n=indicStartJoint2, p=indicStartJoint1)
				nodeList.append(indicStartJoint2)
				rb.setAttrsWithDictionary(indicStartJoint2, indicStartJoint2Attrs)
				pointConstraint(resJoint, indicStartJoint2)
				if self.dev: print indicStartJoint2

			connectAttr(resJoint.fitNode, fitNode.outputJoints[i])
			if self.dev: print resJoint


		ctrlStartTan.tx.set(length/3)
		ctrlEndTan.tx.set(length/3)


		fitNode.orientation.set(1)

		# Final
		if self.dev:
			print "\n"
			print nodeList
			print "\n"

		for node in nodeList:
			
			if not hasAttr(node, 'fitNode'):
				addAttr(node, k=1, h=self.hidden, at='message', ln='fitNode')
			fitNode.deleteList.connect(node.fitNode)
			# node.fitNode.connect(fitNode.deleteList, nextAvailable=1, f=1)

		for ctrl in ctrlList:
			# parent(fitNode, ctrl, s=1, add=1)
			rb.ctrlSetupStandard(ctrl, pivot=False, ro=False, ctrlSet=None)


		for shape in shapesList:
			rb.ctrlSetupStandard(shape, pivot=False, ro=False, ctrlSet=None)

		# Freeze nodes
		if len(freezeList):
			rb.lockAndHide(freezeList, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'])

		if self.dev:
			print "\n"
				
		fitNode.length.set(k=0, cb=1, l=1)
		fitNode.upVectorX.set(k=0, l=1, cb=1)
		fitNode.upVectorY.set(k=0, l=1, cb=1)
		fitNode.upVectorZ.set(k=0, l=1, cb=1)
		fitNode.curveLength.set(k=0, cb=1, l=1)
		fitNode.controlScaleResult.set(k=0, cb=1, l=1)
		select(fitNode)
		return fitNode



	def mirrorFitRig(self, fitNode):
		'''
		Digs through and finds mirror joints to each join in provided fitrig, and uses those joints to create a new one.
		Connects result attributes
		'''
		# Get joints 
		joints = fitNode.jointsList.get()
		if self.dev:
			print 'Joints:'
			print joints

		# Error check
		if not all(self.hasMirror(j) for j in joints):
			print 'Failed Joints: '
			print failList
			raise Exception('Not all joints associated with fitNode have mirrored joints connected.')
			# Add options for specifying joints to be mirrored?

		# Get mirror joints
		mirrorJoints = []
		for j in joints:
			mirrorJoints.append(j.mirror.get())

		if self.dev: 
			print 'Mirrored Joints:'
			print mirrorJoints


		# rigParent = self.fitNode.getParent()
		# mirrorFitRig = fitRig.__init__(self, joints=mirrorJoints, rigType='poleVectorIK')

		# Create mirrored fitRig class instance (or maintain standard class instance? easy link wouldnt be so bad?)
		mirrorFitRig = bezierSplineFitRig(mirrorJoints, self.fitSkeleton, mirrorFitRig=True)

		# Get fitNode
		mirrorFitNode = mirrorFitRig.fitNode
		attributes = [
			'inheritScale',
			]
		# connect attributes in this list and hide right side
		for attribute in attributes:
			fitNode.attr(attribute).connect(mirrorFitNode.attr(attribute), force=1)
			# mirrorFitNode.attr(attribute).set(k=0, cb=0)



		if not hasAttr(fitNode, 'mirror'):
			addAttr(fitNode, ln='mirror', at='message', k=1)
		if not hasAttr(mirrorFitNode, 'mirror'):
			addAttr(mirrorFitNode, ln='mirror', at='message', k=1)
		mirrorFitNode.mirror.connect(fitNode.mirror)

		if self.dev: print 'Mirror Fit Node: %s' % mirrorFitNode
		return mirrorFitNode



	#===================================================================================================
	#===================================================================================================

# =================================================================================

class footRollFitRigNew(fitRig):
	'''TODO:
	subrigs like this (and the hand) can be a shape node under the pvik fit node, in order to 
	remove the posibility of messing up parenting
	'''

	def __init__(self, joints=None, pvikFitNode=None, fitNode=None, mirrorFitRig=False, *args, **kwargs):
	
		# ERROR CHECKS
		self.rigType = 'footRoll'
		if self.dev: print 'RUNNING FOOTROLL FITRIG'
		if self.dev: print 'CHECKING FOR ERRORS...'

		self.fitSkeleton = ls('skeleNode_META')[0]

		if not len(joints) == 3:
			raise Exception('Wrong number of joints specified for footroll fitRig (%s). Select 3 Joints.' % len(joints))



		# FITNODE GLOBAL ATTRIBUTES
		fitNode = fitRig.__init__(self, joints=joints, rigType=self.rigType)
		
		print 'FITNODE'
		print self.fitNode
		
		# FITNODE SPECIFIC ATTRIBUTES
		self.fitNode = self.footRollInit(self.fitNode, mirrorFitRig=mirrorFitRig, pvikFitNode=pvikFitNode)

		# MIRRORING
		# Automatically mirror if all mirror joints found (and mirroring hasn't already been done)
		if not mirrorFitRig and all(self.hasMirror(j) for j in joints):
			print 'Apply Mirroring'
			mirrorFitNode = self.mirrorFitRig(fitNode=self.fitNode, pvikFitNode=pvikFitNode)


	def footRollInit(self, fitNode, mirrorFitRig=False, pvikFitNode=None):

		start = fitNode.jointsList[0].inputs()[0]
		mid = fitNode.jointsList[1].inputs()[0]
		end = fitNode.jointsList[2].inputs()[0]

		startMidEnd = start, mid, end

		settings = self.fitGroup
		fitRigsGrp = self.fitRigsGrp
		side = fitNode.side.get()

		fitNode.globalName.set('footRoll')


		# ========================================= Names ==========================================
		suffix='_foot'
		fitRig='fitRig'
		GlobalMoveName = 'GlobalMove'
		names = {
		'fitNode':					'%s_fitNode%s'						% (start, suffix),
		'decmp':					'_decmp%s'							% (suffix),
		'dist':						'%s_fitNode_length%s'				% (start, suffix),
		'vecStartName':				'%s_vec%s'							% (start.shortName(), suffix),
		'vecMidName':				'%s_vec%s'							% (mid.shortName(), suffix),
		'vecEndName':				'%s_vec%s'							% (end.shortName(), suffix),
		'lengthSM':					'%s_SM_distance%s'					% (start.shortName(), suffix),
		'lengthME':					'%s_ME_distance%s'					% (mid.shortName(), suffix),
		'lengthAdd':				'%s_length_ADD%s'					% (start.shortName(), suffix),
		'controlScaleMult':			'%s_ctrlScale_MULT%s'				% (start.shortName(), suffix),
		'lengthAdjustMult':			'%s_len_ctrlScaleAdjust_MULT%s'		% (start.shortName(), suffix),
		'lengthCtrlScaleResult':	'%s_len_ctrlScale_MULT%s'			% (start.shortName(), suffix),
		'lengthBasedScalingBlend':	'%s_len_scaling_Blend%s'			% (start.shortName(), suffix),
		'reverseCtrlScale':			'%s_scale_reverse_MULT%s'			% (start.shortName(), suffix),
		'grp': 						'%s_%s%s' 							% (start, fitRig, suffix),
		'worldGrp': 				'%s_%s_noTransform%s' 				% (start, fitRig, suffix),
		'pivGrp': 					'%s_%s_pivotGroup%s' 				% (start, fitRig, suffix),
		'buf':						'%s_%s_buf%s'						% (start, fitRig, suffix),
		'shapesGrp':				'%s_%s_shapesGroup%s' 				% (start, fitRig, suffix),
		'pivShape':					'pivotShp%s' 						% (suffix),

		}


		# Collections
		nodeList = []
		shapesList = []
		ctrlList = []
		freezeList = []

		# Rig-specific attributes
		addAttr(fitNode, ln='floorPlane', keyable=True)

		if not hasAttr(fitNode, 'shapeHeel'):

			addAttr(fitNode, ln='shapeFK', ct='shape', at='message', keyable=True)
			addAttr(fitNode, ln='shapeHeel', ct='shape', at='message', keyable=True)
			addAttr(fitNode, ln='shapeToe', ct='shape', at='message', keyable=True)
			addAttr(fitNode, ln='shapeBankIn', ct='shape', at='message', keyable=True)
			addAttr(fitNode, ln='shapeBankOut', ct='shape', at='message', keyable=True)
			addAttr(fitNode, ln='shapeBall', ct='shape', at='message', keyable=True)

			###
			rb.cbSep(fitNode)

			addAttr(fitNode, ln='startOutputJoint', ct='output', at='message', multi=True, keyable=True)
			addAttr(fitNode, ln='midOutputJoint', ct='output', at='message', multi=True, keyable=True)
			
			addAttr(fitNode, ln='pvikFitNode', ct='input', at='message', keyable=True)
			
			print 'PVIKFITNODE'
			print pvikFitNode
			if pvikFitNode:
				pvikFitNode.message.connect(fitNode.pvikFitNode)
				fitNode.message.connect(pvikFitNode.subNode)
			

			# =================================== Y Vectors ===================================
			# Vector Start
			vecProdStart = createNode('vectorProduct', n=names.get('vecStartName', 'rnm_vecStartName'))
			nodeList.append(vecProdStart)
			vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
			rb.setAttrsWithDictionary(vecProdStart, vecSetAttr)
			connectAttr(start.worldMatrix[0], vecProdStart.matrix)	
			addAttr(fitNode, ln='upVectorStart', at='compound', numberOfChildren=3, keyable=True)
			addAttr(fitNode, ln='upVectorStartX', at='float', parent='upVectorStart', keyable=True)
			addAttr(fitNode, ln='upVectorStartY', at='float', parent='upVectorStart', keyable=True)
			addAttr(fitNode, ln='upVectorStartZ', at='float', parent='upVectorStart', keyable=True)
			fitNode.upVectorStartX.set(k=0, cb=1)
			fitNode.upVectorStartY.set(k=0, cb=1)
			fitNode.upVectorStartZ.set(k=0, cb=1)
			connectAttr(vecProdStart.outputX, fitNode.upVectorStartX)
			connectAttr(vecProdStart.outputY, fitNode.upVectorStartY)
			connectAttr(vecProdStart.outputZ, fitNode.upVectorStartZ)
			if self.dev: print vecProdStart
			# Vector Mid
			vecProdMid = createNode('vectorProduct', n=names.get('vecMidName', 'rnm_vecMidName'))
			nodeList.append(vecProdMid)
			vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
			rb.setAttrsWithDictionary(vecProdMid, vecSetAttr)
			connectAttr(mid.worldMatrix[0], vecProdMid.matrix)	
			addAttr(fitNode, ln='upVectorMid', at='compound', numberOfChildren=3, keyable=True)
			addAttr(fitNode, ln='upVectorMidX', at='float', parent='upVectorMid', keyable=True)
			addAttr(fitNode, ln='upVectorMidY', at='float', parent='upVectorMid', keyable=True)
			addAttr(fitNode, ln='upVectorMidZ', at='float', parent='upVectorMid', keyable=True)
			fitNode.upVectorMidX.set(k=0, cb=1)
			fitNode.upVectorMidY.set(k=0, cb=1)
			fitNode.upVectorMidZ.set(k=0, cb=1)
			connectAttr(vecProdMid.outputX, fitNode.upVectorMidX)
			connectAttr(vecProdMid.outputY, fitNode.upVectorMidY)
			connectAttr(vecProdMid.outputZ, fitNode.upVectorMidZ)
			if self.dev: print vecProdMid


			# Vector End
			vecProdEnd = createNode('vectorProduct', n=names.get('vecEndName', 'rnm_vecEndName'))
			nodeList.append(vecProdEnd)
			vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
			rb.setAttrsWithDictionary(vecProdEnd, vecSetAttr)
			connectAttr(end.worldMatrix[0], vecProdEnd.matrix)	
			addAttr(fitNode, ln='upVectorEnd', at='compound', numberOfChildren=3, keyable=True)
			addAttr(fitNode, ln='upVectorEndX', at='float', parent='upVectorEnd', keyable=True)
			addAttr(fitNode, ln='upVectorEndY', at='float', parent='upVectorEnd', keyable=True)
			addAttr(fitNode, ln='upVectorEndZ', at='float', parent='upVectorEnd', keyable=True)
			fitNode.upVectorEndX.set(k=0, cb=1)
			fitNode.upVectorEndY.set(k=0, cb=1)
			fitNode.upVectorEndZ.set(k=0, cb=1)
			connectAttr(vecProdEnd.outputX, fitNode.upVectorEndX)
			connectAttr(vecProdEnd.outputY, fitNode.upVectorEndY)
			connectAttr(vecProdEnd.outputZ, fitNode.upVectorEndZ)
			if self.dev: print vecProdEnd


			# ============================== Length ==============================
			decmp = []
			sme = ['start', 'mid', 'end']
			# Decompose Matrix
			for i in range(3):
				decmpName = '%s_%s_%s' % (start, sme[i], names.get('decmp', 'rnm_decmp'))
				decmp.append(createNode('decomposeMatrix', n=decmpName))
				nodeList.append(decmp[i])
				startMidEnd[i].worldMatrix[0] >> decmp[i].inputMatrix
				if self.dev: print decmp[i]
			lengths = []
			# Length Start-Mid
			if not hasAttr(fitNode, 'lengthSM'):
				addAttr(fitNode, ln='lengthSM', nn='Length Start/Mid', keyable=True)
				fitNode.lengthSM.set(k=0, cb=1)
			lengthSM = createNode('distanceBetween', n=names.get('lengthSM', 'rnm_lengthSM'))
			lengths.append(lengthSM)
			decmp[0].outputTranslate >> lengthSM.point1
			decmp[1].outputTranslate >> lengthSM.point2
			lengthSM.distance >> fitNode.lengthSM
			# Length Mid-End
			if not hasAttr(fitNode, 'lengthME'):
				addAttr(fitNode, ln='lengthME', nn='Length Mid/End', keyable=True)
				fitNode.lengthME.set(k=0, cb=1)
				rb.cbSep(fitNode)
			lengthME = createNode('distanceBetween', n=names.get('lengthME', 'rnm_lengthME'))
			nodeList.append(lengthME)
			lengths.append(lengthME)
			decmp[1].outputTranslate >> lengthME.point1
			decmp[2].outputTranslate >> lengthME.point2
			lengthME.distance >> fitNode.lengthME

			
			# ============================== Control Scaling ==============================
			lengthAdd = createNode('addDoubleLinear', n=names.get('lengthAdd', 'rnm_lengthAdd'))
			nodeList.append(lengthAdd)
			lengthSM.distance >> lengthAdd.i1
			lengthME.distance >> lengthAdd.i2

			controlScaleMult = createNode('multDoubleLinear', n=names.get('controlScaleMult', 'rnm_controlScaleMult')) # Local * Global Scale
			nodeList.append(controlScaleMult)
			fitNode.controlScale >> controlScaleMult.i1
			settings.controlScale >> controlScaleMult.i2

			lengthCtrlScaleResult = createNode('multDoubleLinear', n=names.get('lengthCtrlScaleResult', 'rnm_lengthCtrlScaleResult')) # (local * global) * length
			nodeList.append(lengthCtrlScaleResult)
			controlScaleMult.o >> lengthCtrlScaleResult.i1
			lengthAdd.o >> lengthCtrlScaleResult.i2

			lengthAdjustMult = createNode('multDoubleLinear', n=names.get('lengthAdjustMult', 'rnm_lengthAdjustMult'))
			nodeList.append(lengthAdjustMult)
			lengthCtrlScaleResult.o >> lengthAdjustMult.i1
			lengthAdjustMult.i2.set(0.1)

			lengthBasedScalingBlend = createNode('blendTwoAttr', n=names.get('lengthBasedScalingBlend', 'rnm_lengthBasedScalingBlend'))
			nodeList.append(lengthBasedScalingBlend)
			controlScaleMult.o >> lengthBasedScalingBlend.i[0]
			lengthAdjustMult.o >> lengthBasedScalingBlend.i[1]
			settings.lengthBasedScaling >> lengthBasedScalingBlend.ab

			lengthBasedScalingBlend.o >> fitNode.controlScaleResult


			
			# ============================== Standard Inputs ==============================
			rb.messageConnect(start, 'fitNode', [fitNode], 'startInput')
			rb.messageConnect(mid, 'fitNode', [fitNode], 'midInput')
			rb.messageConnect(end, 'fitNode', [fitNode], 'endInput')

			# fitNode.globalName.set(start.shortName().split("|")[-1].split("_")[0]) # Removes all but last '|' block and returns first '_' block
			fitNode.side.set(start.side.get())

			# Attach fitNode to joints
			# parent(fitNode, start, add=True, s=True)
			# parent(fitNode, mid, add=True, s=True)
			# parent(fitNode, end, add=True, s=True)

			# Get points
			startT = xform(start, q=1, rp=1, ws=1)
			startR = xform(start, q=1, ro=1, ws=1)
			midT = xform(mid, q=1, rp=1, ws=1)
			midR = xform(mid, q=1, ro=1, ws=1)
			endT = xform(end, q=1, rp=1, ws=1)
			endR = xform(end, q=1, ro=1, ws=1)

			startMidEndT = [startT, midT, endT]
			startMidEndR = [startR, midR, endR]


			# =================================== Nodes =========================================


			# Group
			grp = createNode('transform', n=names.get('grp', 'rnm_grp'))
			freezeList.append(grp)
			nodeList.append(grp)
			parent(grp, fitRigsGrp)
			# parent(fitNode, grp, r=True, s=True)
			rb.messageConnect(grp, 'message', fitNode, 'fitRig')
			self.fitNode.v.connect(grp.v)
			if self.dev: print grp

			pointConstraint(start, grp, mo=True, skip='y')
			fitNode.floorPlane.connect(grp.translateY)


			# No-Translate Group
			worldGroupAttrs =  {'inheritsTransform': 0}
			worldGrp = createNode('transform', n=names.get('worldGrp', 'rnm_worldGrp'))
			nodeList.append(worldGrp)
			freezeList.append(worldGrp)
			rb.setAttrsWithDictionary(worldGrp, worldGroupAttrs)
			fitNode.controlsVis >> worldGrp.v
			parent(worldGrp, grp)
			if self.dev: print worldGrp


			pivGrp = createNode('transform', n=names.get('pivGrp', 'rnm_pivGrp'), p=grp)
			nodeList.append(pivGrp)
			freezeList.append(pivGrp)
			move(pivGrp, startT, rpr=1, ws=1)
			xform(pivGrp, ro=startR, ws=1)
			move(pivGrp, 0, y=1, rpr=1, ws=1)
			xform(pivGrp, ro=[0,0,0], ws=1)
			if mirrorFitRig:
				pivGrp.sx.set(-1)
			fitNode.controlsVis >> pivGrp.v

			# Use pivot group to guide placement of fitNode selection handle
			# import pymel.core.datatypes as dt

			# temp = createNode('transform', p=fitNode)
			# xform(temp, ws=1, m=xform(pivGrp, q=1, ws=1, m=1))
			# fitNode.selectHandle.set(temp.t.get())
			# delete(temp)




			# Shapes Group
			shapesGrp = createNode('transform', n=names.get('shapesGrp', 'rnm_shapesGrp'), p=grp)
			nodeList.append(shapesGrp)
			freezeList.append(shapesGrp)
			fitNode.shapesVis >> shapesGrp.v
			
			if mirrorFitRig:
				reverseCtrlScale = createNode('multDoubleLinear', n=names.get('reverseCtrlScale', 'rnm_reverseCtrlScale'))
				nodeList.append(reverseCtrlScale)
				shapesGrp.scaleX.set(-1)


			fkShapeGrp = createNode('transform', n=names.get('fkShapeGrp', 'rnm_fkShapeGrp'), p=shapesGrp)
			nodeList.append(fkShapeGrp)
			freezeList.append(fkShapeGrp)
			
			# shapeFK
			fkNode = ls(rb.shapeMaker(name='%s_%s_%s' % (start, fitRig, names.get('fkShape', 'rnm_fkShape')), shape=2 ) )[0]
			parent(fkNode, fkShapeGrp)
			# fkNode.translate.set(-0.5,0.5,0.0)
			fkNode.rotate.set(0,0,90)
			# fkNode.rotatePivotTranslate.set(0,-1,0)
			# fkNode.rotatePivot.set(0,-1,0)
			# fkNode.scalePivot.set(0.5,0.5,0.0)
			fkNode.scale.set(5,5,5)
			makeIdentity(fkNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
			fkNode.message >> fitNode.shapeFK
			fkShape = fkNode.getShapes()[0]
			col.setViewportRGB([fkShape], self.colorsFK[side])
			nodeList.append(fkNode)
			parentConstraint(mid, fkShapeGrp)
			if self.dev: print fkShape

			pivCtrls = []

			pivShapeAttr = [
			fitNode.shapeHeel,
			fitNode.shapeToe,
			fitNode.shapeBankIn,
			fitNode.shapeBankOut,
			fitNode.shapeBall
			]

			pivots = [
			'heel',
			'toe',
			'bankIn',
			'bankOut',
			'ball'
			]
			bufList = []
			# Create pivot points
			rad = 1.2
			val = 10 # default control spacing
			
			for i, piv in enumerate(pivots): # Don't create control for ball
				if i is not len(pivots)-1:
					
					buf = createNode('transform', n='%s_%s' % (names.get('buf', 'rnm_buf'), pivots[i]), p=pivGrp)
					nodeList.append(buf)
					bufList.append(buf)
					freezeList.append(buf)
					if self.dev: print buf

					if self.dev: print pivots[i]
					pivCtrl = createNode('joint', n='pivot_%s' % pivots[i], p=buf)
					pivCtrls.append(pivCtrl)
					nodeList.append(pivCtrl)
					ctrlList.append(pivCtrl)
					pivCtrl.radius.set(rad)
					rb.messageConnect(pivCtrl, 'message', fitNode, pivCtrl.shortName().split('|')[-1])
					if self.dev: print pivCtrl
					col.setViewportRGB([pivCtrl], [0.5,1,0.5])
					addAttr(pivCtrl, ln='curveLen', min=0, dv=val, k=1)
					pivCtrl.curveLen.set(k=0, cb=1)


					posZTrans = createNode('transform', n='%s_posZ'  % pivots[i], p=pivCtrl)
					nodeList.append(posZTrans)
					pivCtrl.curveLen >> posZTrans.tz

					negZTrans = createNode('transform', n='%s_negZ'  % pivots[i], p=pivCtrl)
					nodeList.append(negZTrans)
					unitConv = createNode('unitConversion')
					unitConv.conversionFactor.set(-1)
					pivCtrl.curveLen >> unitConv.i
					unitConv.o >> negZTrans.tz

					zIndics = rb.boneIndic(posZTrans, negZTrans, worldGrp, blackGrey=0)

				# Control Shape
				pivShapeGrp = createNode('transform', n='%s_%s' % (pivots[i], names.get('shapesGrp', 'rnm_shapesGrp')), p=shapesGrp)
				nodeList.append(pivShapeGrp)
				fitNode.controlScaleResult >> pivShapeGrp.scaleX
				fitNode.controlScaleResult >> pivShapeGrp.scaleY
				fitNode.controlScaleResult >> pivShapeGrp.scaleZ
				freezeList.append(pivShapeGrp)
				if self.dev: print pivShapeGrp

				pivNode = ls(rb.shapeMaker(name='%s_%s_%s_%s' % (start, fitRig, pivots[i], names.get('pivShape', 'rnm_pivShape')), shape=8 ) )[0]
				parent(pivNode, pivShapeGrp)
				# pivNode.translate.set(-0.5,0.5,0.0)
				# pivNode.rotate.set(0,0,-90)
				# pivNode.rotatePivotTranslate.set(0,-1,0)
				# pivNode.rotatePivot.set(0,-1,0)
				# pivNode.scalePivot.set(0.5,0.5,0.0)
				# pivNode.scale.set(1,1,1)
				pivNode.message >> pivShapeAttr[i]
				makeIdentity(pivNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
				pivShape = pivNode.getShapes()[0]
				col.setViewportRGB([pivShape], self.colorsIK[side])
				nodeList.append(pivNode)
				if i is not len(pivots)-1:
					parentConstraint(pivCtrl, pivShapeGrp)
				else:
					parentConstraint(mid, pivShapeGrp)
				if self.dev: print pivShape

			if mirrorFitRig:

				# Heel
				move(bufList[0], -val, z=1, rpr=1, r=1, ws=0)
				xform(bufList[0], ro=[0,90,0], ws=1)
				# Toe
				move(bufList[1], val, z=1, rpr=1, r=1, ws=0)
				xform(bufList[1], ro=[0,-90,0], ws=1)
				# In
				move(bufList[2], val, x=1, rpr=1, r=1, ws=0)
				# xform(bufList[2], ro=[0,0,0], ws=1)
				# Out
				move(bufList[3], -val, x=1, rpr=1, r=1, ws=0)
				xform(bufList[3], ro=[0,180,0], r=1)


			else:
				# Heel
				move(bufList[0], -val, z=1, rpr=1, r=1, ws=0)
				xform(bufList[0], ro=[0,-90,0], ws=1)
				# Toe
				move(bufList[1], val, z=1, rpr=1, r=1, ws=0)
				xform(bufList[1], ro=[0,90,0], ws=1)
				# In
				move(bufList[2], -val, x=1, rpr=1, r=1, ws=0)
				# xform(bufList[2], ro=[0,0,0], ws=1)
				# Out
				move(bufList[3], val, x=1, rpr=1, r=1, ws=0)
				xform(bufList[3], ro=[0,180,0], r=1)

			rb.lockAndHide(pivCtrls, ['ty', 'rx', 'rz', 'sx', 'sy', 'sz', 'v'])


			bankIndics = rb.boneIndic(pivCtrls[2], pivCtrls[3], worldGrp, blackGrey=1)
			rollIndics = rb.boneIndic(pivCtrls[0], pivCtrls[1], worldGrp, blackGrey=1)



		# Finalize

		for node in nodeList:
			print node
			if not hasAttr(node, 'fitNode'):
				addAttr(node, k=1, h=self.hidden, at='message', ln='fitNode')
			fitNode.deleteList.connect(node.fitNode)
		
		for ctrl in ctrlList:
			if not hasAttr(fitNode, 'ctrlList'):
				addAttr(fitNode, k=1, h=self.hidden, at='message', ln='ctrlList', multi=True, indexMatters=False)
			ctrl.message.connect(fitNode.ctrlList, na=1)
			# node.fitNode.connect(fitNode.deleteList, nextAvailable=1, f=1)
		
		print 'Footroll Rig Finished'
		select(fitNode)
		return fitNode

	def mirrorFitRig(self, fitNode, pvikFitNode):
		'''
		Digs through and finds mirror joints to each join in provided fitrig, and uses those joints to create a new one.
		Connects result attributes
		'''
		# Get joints 
		joints = fitNode.jointsList.get()
		if self.dev:
			print 'Joints:'
			print joints

		# Error check
		if not all(self.hasMirror(j) for j in joints):
			print 'Failed Joints: '
			raise Exception('Not all joints associated with fitNode have mirrored joints connected.')
			# Add options for specifying joints to be mirrored?
		

		# Get mirror joints
		mirrorJoints = []
		for j in joints:
			mirrorJoints.append(j.mirror.get())

		if self.dev: 
			print 'Mirrored Joints:'
			print mirrorJoints

		# get mirror fitNode
		if len(pvikFitNode.mirror.outputs()):
			mirrorPvIkFitNode = pvikFitNode.mirror.outputs()[0]
		elif len(pvikFitNode.mirror.inputs()):
			mirrorPvIkFitNode = pvikFitNode.mirror.inputs()[0]


		# rigParent = self.fitNode.getParent()
		# mirrorFitRig = fitRig.__init__(self, joints=mirrorJoints, rigType='poleVectorIK')

		# Create mirrored fitRig class instance (or maintain standard class instance? easy link wouldnt be so bad?)
		mirrorFitRig = footRollFitRigNew(joints=mirrorJoints, pvikFitNode=mirrorPvIkFitNode, mirrorFitRig=True)

		# Get fitNode
		mirrorFitNode = mirrorFitRig.fitNode
		attributes = [
		]
		# connect attributes in this list and hide right side
		for attribute in attributes:
			fitNode.attr(attribute).connect(mirrorFitNode.attr(attribute), force=1)
			# mirrorFitNode.attr(attribute).set(k=0, cb=0)


		if not hasAttr(fitNode, 'mirror'):
			addAttr(fitNode, ln='mirror', at='message', k=1)
		if not hasAttr(mirrorFitNode, 'mirror'):
			addAttr(mirrorFitNode, ln='mirror', at='message', k=1)
		mirrorFitNode.mirror.connect(fitNode.mirror)

		fitNode.scaleX.connect(mirrorFitNode.scaleX)
		fitNode.floorPlane.connect(mirrorFitNode.floorPlane)
		fitNode.parentSocketIndex.connect(mirrorFitNode.parentSocketIndex)

		for ctrl, mirCtrl in zip(fitNode.ctrlList.get(), mirrorFitNode.ctrlList.get()):
			ctrl.translate.connect(mirCtrl.translate)
			ctrl.rotateY.connect(mirCtrl.rotateY)
			ctrl.curveLen.connect(mirCtrl.curveLen)

		if self.dev: print 'Mirror Fit Node: %s' % mirrorFitNode
		return mirrorFitNode

# =================================================================================

class footRollFitRig(fitRig):
	
	def __init__(self, fitRigs=None, fitSkele=None, fitNode=None, mirrorFitRig=False, *args, **kwargs):
		if fitSkele is None:
			try:
				fitSkele = ls('skeleNode_META')[0]
			except:
				raise Exception('Fit Skeleton node not found.')

		self.fitSkeleton = fitSkele

		# ERROR CHECKS
		self.rigType = 'footRoll'
		if self.dev: print 'RUNNING FOOTROLL RIG'
		if self.dev: print 'CHECKING FOR ERRORS...'

		if not len(fitRigs) == 3:
			raise Exception('Wrong number of fitRigs specified for footroll fitRig. Select poleVector IK and two aim IK fitNodes.')
		legFitRig, ankleFitRig, toeFitRig = fitRigs

		if not legFitRig.rigType.get() == 'poleVectorIK':
			raise Exception('FitRig[0] is wrong type. Select poleVector IK and two aim IK fitNodes.')

		if not ankleFitRig.rigType.get() == 'aimIK':
			raise Exception('FitRig[1] is wrong type. Select poleVector IK and two aim IK fitNodes.')

		if not toeFitRig.rigType.get() == 'aimIK':
			raise Exception('FitRig[2] is wrong type. Select poleVector IK and two aim IK fitNodes.')

		joints = ankleFitRig.jointsList.get()
		joints.append(toeFitRig.jointsList.get()[-1])
		print joints

		if self.dev: print len(joints)
		if not len(joints) == 3:
			raise Exception('Wrong number of joints specified for footroll fitRig. Select 3 joints.')

		# FITNODE GLOBAL ATTRIBUTES
		fitNode = fitRig.__init__(self, joints=joints, rigType=self.rigType)
		# if self.dev:
		
		print 'FITNODE'
		print self.fitNode
		if not hasAttr(self.fitNode, 'fitNodesList'):
			addAttr(self.fitNode, k=1, at='message', ct=['selection', 'input'], multi=1, indexMatters=0, ln='fitNodesList')
		for fr in fitRigs:
				connectAttr(fr.message, self.fitNode.fitNodesList, na=1)

		# FITNODE SPECIFIC ATTRIBUTES
		self.fitNode = self.footRollInit(self.fitNode, mirrorFitRig=mirrorFitRig)

		# MIRRORING
		# Automatically mirror if all mirror joints found (and mirroring hasn't already been done)
		if not mirrorFitRig and all(self.hasMirror(j) for j in joints):
			print 'Apply Mirroring'
			mirrorFitNode = self.mirrorFitRig(self.fitNode)

	def footRollInit(self, fitNode, mirrorFitRig=False):

		start = fitNode.jointsList[0].inputs()[0]
		mid = fitNode.jointsList[1].inputs()[0]
		end = fitNode.jointsList[2].inputs()[0]

		startMidEnd = start, mid, end

		settings = self.fitGroup
		fitRigsGrp = self.fitRigsGrp
		side = fitNode.side.get()

		# prefix = fitNode.globalName.get()


		# ========================================= Names ==========================================
		suffix='_foot'
		fitRig='fitRig'
		GlobalMoveName = 'GlobalMove'
		names = {
		'fitNode':					'%s_fitNode%s'						% (start, suffix),
		'decmp':					'_decmp%s'							% (suffix),
		'dist':						'%s_fitNode_length%s'				% (start, suffix),
		'vecStartName':				'%s_vec%s'							% (start.shortName(), suffix),
		'vecMidName':				'%s_vec%s'							% (mid.shortName(), suffix),
		'vecEndName':				'%s_vec%s'							% (end.shortName(), suffix),
		'lengthSM':					'%s_SM_distance%s'					% (start.shortName(), suffix),
		'lengthME':					'%s_ME_distance%s'					% (mid.shortName(), suffix),
		'lengthAdd':				'%s_length_ADD%s'					% (start.shortName(), suffix),
		'controlScaleMult':			'%s_ctrlScale_MULT%s'				% (start.shortName(), suffix),
		'lengthAdjustMult':			'%s_len_ctrlScaleAdjust_MULT%s'		% (start.shortName(), suffix),
		'lengthCtrlScaleResult':	'%s_len_ctrlScale_MULT%s'			% (start.shortName(), suffix),
		'lengthBasedScalingBlend':	'%s_len_scaling_Blend%s'			% (start.shortName(), suffix),
		'reverseCtrlScale':			'%s_scale_reverse_MULT%s'			% (start.shortName(), suffix),
		'grp': 						'%s_%s%s' 							% (start, fitRig, suffix),
		'worldGrp': 				'%s_%s_noTransform%s' 				% (start, fitRig, suffix),
		'pivGrp': 					'%s_%s_pivotGroup%s' 				% (start, fitRig, suffix),
		'buf':						'%s_%s_buf%s'						% (start, fitRig, suffix),
		'shapesGrp':				'%s_%s_shapesGroup%s' 				% (start, fitRig, suffix),
		'pivShape':					'pivotShp%s' 						% (suffix),

		}


		# Collections
		nodeList = []
		shapesList = []
		ctrlList = []
		freezeList = []

		# Rig-specific attributes
		if not hasAttr(fitNode, 'shapeHeel'):

			addAttr(fitNode, ln='shapeHeel', ct='shape', at='message', keyable=True)
			addAttr(fitNode, ln='shapeToe', ct='shape', at='message', keyable=True)
			addAttr(fitNode, ln='shapeBankIn', ct='shape', at='message', keyable=True)
			addAttr(fitNode, ln='shapeBankOut', ct='shape', at='message', keyable=True)
			addAttr(fitNode, ln='shapeBall', ct='shape', at='message', keyable=True)

			###
			rb.cbSep(fitNode)

			addAttr(fitNode, ln='startOutputJoint', ct='output', at='message', multi=True, keyable=True)
			addAttr(fitNode, ln='midOutputJoint', ct='output', at='message', multi=True, keyable=True)
			
			addAttr(fitNode, ln='threePointIKFitNode', ct='input', at='message', keyable=True)


			# =================================== Y Vectors ===================================
			# Vector Start
			vecProdStart = createNode('vectorProduct', n=names.get('vecStartName', 'rnm_vecStartName'))
			nodeList.append(vecProdStart)
			vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
			rb.setAttrsWithDictionary(vecProdStart, vecSetAttr)
			connectAttr(start.worldMatrix[0], vecProdStart.matrix)	
			addAttr(fitNode, ln='upVectorStart', at='compound', numberOfChildren=3, keyable=True)
			addAttr(fitNode, ln='upVectorStartX', at='float', parent='upVectorStart', keyable=True)
			addAttr(fitNode, ln='upVectorStartY', at='float', parent='upVectorStart', keyable=True)
			addAttr(fitNode, ln='upVectorStartZ', at='float', parent='upVectorStart', keyable=True)
			fitNode.upVectorStartX.set(k=0, cb=1)
			fitNode.upVectorStartY.set(k=0, cb=1)
			fitNode.upVectorStartZ.set(k=0, cb=1)
			connectAttr(vecProdStart.outputX, fitNode.upVectorStartX)
			connectAttr(vecProdStart.outputY, fitNode.upVectorStartY)
			connectAttr(vecProdStart.outputZ, fitNode.upVectorStartZ)
			if self.dev: print vecProdStart
			# Vector Mid
			vecProdMid = createNode('vectorProduct', n=names.get('vecMidName', 'rnm_vecMidName'))
			nodeList.append(vecProdMid)
			vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
			rb.setAttrsWithDictionary(vecProdMid, vecSetAttr)
			connectAttr(mid.worldMatrix[0], vecProdMid.matrix)	
			addAttr(fitNode, ln='upVectorMid', at='compound', numberOfChildren=3, keyable=True)
			addAttr(fitNode, ln='upVectorMidX', at='float', parent='upVectorMid', keyable=True)
			addAttr(fitNode, ln='upVectorMidY', at='float', parent='upVectorMid', keyable=True)
			addAttr(fitNode, ln='upVectorMidZ', at='float', parent='upVectorMid', keyable=True)
			fitNode.upVectorMidX.set(k=0, cb=1)
			fitNode.upVectorMidY.set(k=0, cb=1)
			fitNode.upVectorMidZ.set(k=0, cb=1)
			connectAttr(vecProdMid.outputX, fitNode.upVectorMidX)
			connectAttr(vecProdMid.outputY, fitNode.upVectorMidY)
			connectAttr(vecProdMid.outputZ, fitNode.upVectorMidZ)
			if self.dev: print vecProdMid


			# Vector End
			vecProdEnd = createNode('vectorProduct', n=names.get('vecEndName', 'rnm_vecEndName'))
			nodeList.append(vecProdEnd)
			vecSetAttr = {'input1': [0, 1, 0], 'operation': 3}
			rb.setAttrsWithDictionary(vecProdEnd, vecSetAttr)
			connectAttr(end.worldMatrix[0], vecProdEnd.matrix)	
			addAttr(fitNode, ln='upVectorEnd', at='compound', numberOfChildren=3, keyable=True)
			addAttr(fitNode, ln='upVectorEndX', at='float', parent='upVectorEnd', keyable=True)
			addAttr(fitNode, ln='upVectorEndY', at='float', parent='upVectorEnd', keyable=True)
			addAttr(fitNode, ln='upVectorEndZ', at='float', parent='upVectorEnd', keyable=True)
			fitNode.upVectorEndX.set(k=0, cb=1)
			fitNode.upVectorEndY.set(k=0, cb=1)
			fitNode.upVectorEndZ.set(k=0, cb=1)
			connectAttr(vecProdEnd.outputX, fitNode.upVectorEndX)
			connectAttr(vecProdEnd.outputY, fitNode.upVectorEndY)
			connectAttr(vecProdEnd.outputZ, fitNode.upVectorEndZ)
			if self.dev: print vecProdEnd


			# ============================== Length ==============================
			decmp = []
			sme = ['start', 'mid', 'end']
			# Decompose Matrix
			for i in range(3):
				decmpName = '%s_%s_%s' % (start, sme[i], names.get('decmp', 'rnm_decmp'))
				decmp.append(createNode('decomposeMatrix', n=decmpName))
				nodeList.append(decmp[i])
				startMidEnd[i].worldMatrix[0] >> decmp[i].inputMatrix
				if self.dev: print decmp[i]
			lengths = []
			# Length Start-Mid
			if not hasAttr(fitNode, 'lengthSM'):
				addAttr(fitNode, ln='lengthSM', nn='Length Start/Mid', keyable=True)
				fitNode.lengthSM.set(k=0, cb=1)
			lengthSM = createNode('distanceBetween', n=names.get('lengthSM', 'rnm_lengthSM'))
			lengths.append(lengthSM)
			decmp[0].outputTranslate >> lengthSM.point1
			decmp[1].outputTranslate >> lengthSM.point2
			lengthSM.distance >> fitNode.lengthSM
			# Length Mid-End
			if not hasAttr(fitNode, 'lengthME'):
				addAttr(fitNode, ln='lengthME', nn='Length Mid/End', keyable=True)
				fitNode.lengthME.set(k=0, cb=1)
				rb.cbSep(fitNode)
			lengthME = createNode('distanceBetween', n=names.get('lengthME', 'rnm_lengthME'))
			nodeList.append(lengthME)
			lengths.append(lengthME)
			decmp[1].outputTranslate >> lengthME.point1
			decmp[2].outputTranslate >> lengthME.point2
			lengthME.distance >> fitNode.lengthME

			
			# ============================== Control Scaling ==============================
			lengthAdd = createNode('addDoubleLinear', n=names.get('lengthAdd', 'rnm_lengthAdd'))
			nodeList.append(lengthAdd)
			lengthSM.distance >> lengthAdd.i1
			lengthME.distance >> lengthAdd.i2

			controlScaleMult = createNode('multDoubleLinear', n=names.get('controlScaleMult', 'rnm_controlScaleMult')) # Local * Global Scale
			nodeList.append(controlScaleMult)
			fitNode.controlScale >> controlScaleMult.i1
			settings.controlScale >> controlScaleMult.i2

			lengthCtrlScaleResult = createNode('multDoubleLinear', n=names.get('lengthCtrlScaleResult', 'rnm_lengthCtrlScaleResult')) # (local * global) * length
			nodeList.append(lengthCtrlScaleResult)
			controlScaleMult.o >> lengthCtrlScaleResult.i1
			lengthAdd.o >> lengthCtrlScaleResult.i2

			lengthAdjustMult = createNode('multDoubleLinear', n=names.get('lengthAdjustMult', 'rnm_lengthAdjustMult'))
			nodeList.append(lengthAdjustMult)
			lengthCtrlScaleResult.o >> lengthAdjustMult.i1
			lengthAdjustMult.i2.set(0.1)

			lengthBasedScalingBlend = createNode('blendTwoAttr', n=names.get('lengthBasedScalingBlend', 'rnm_lengthBasedScalingBlend'))
			nodeList.append(lengthBasedScalingBlend)
			controlScaleMult.o >> lengthBasedScalingBlend.i[0]
			lengthAdjustMult.o >> lengthBasedScalingBlend.i[1]
			settings.lengthBasedScaling >> lengthBasedScalingBlend.ab

			lengthBasedScalingBlend.o >> fitNode.controlScaleResult


			
			# ============================== Standard Inputs ==============================
			rb.messageConnect(start, 'fitNode', [fitNode], 'startInput')
			rb.messageConnect(mid, 'fitNode', [fitNode], 'midInput')
			rb.messageConnect(end, 'fitNode', [fitNode], 'endInput')

			# fitNode.globalName.set(start.shortName().split("|")[-1].split("_")[0]) # Removes all but last '|' block and returns first '_' block
			fitNode.side.set(start.side.get())

			# Attach fitNode to joints
			# parent(fitNode, start, add=True, s=True)
			# parent(fitNode, mid, add=True, s=True)
			# parent(fitNode, end, add=True, s=True)

			# Get points
			startT = xform(start, q=1, rp=1, ws=1)
			startR = xform(start, q=1, ro=1, ws=1)
			midT = xform(mid, q=1, rp=1, ws=1)
			midR = xform(mid, q=1, ro=1, ws=1)
			endT = xform(end, q=1, rp=1, ws=1)
			endR = xform(end, q=1, ro=1, ws=1)

			startMidEndT = [startT, midT, endT]
			startMidEndR = [startR, midR, endR]


			# =================================== Nodes =========================================


			# Group
			grp = createNode('transform', n=names.get('grp', 'rnm_grp'))
			freezeList.append(grp)
			nodeList.append(grp)
			parent(grp, settings)
			# parent(fitNode, grp, r=True, s=True)
			rb.messageConnect(grp, 'message', fitNode, 'fitRig')
			if self.dev: print grp


			# No-Translate Group
			worldGroupAttrs =  {'inheritsTransform': 0}
			worldGrp = createNode('transform', n=names.get('worldGrp', 'rnm_worldGrp'))
			nodeList.append(worldGrp)
			freezeList.append(worldGrp)
			rb.setAttrsWithDictionary(worldGrp, worldGroupAttrs)
			fitNode.controlsVis >> worldGrp.v
			parent(worldGrp, grp)
			if self.dev: print worldGrp


			pivGrp = createNode('transform', n=names.get('pivGrp', 'rnm_pivGrp'), p=grp)
			nodeList.append(pivGrp)
			freezeList.append(pivGrp)
			move(pivGrp, startT, rpr=1, ws=1)
			xform(pivGrp, ro=startR, ws=1)
			move(pivGrp, 0, y=1, rpr=1, ws=1)
			xform(pivGrp, ro=[0,0,0], ws=1)
			if mirrorFitRig:
				pivGrp.sx.set(-1)
			fitNode.controlsVis >> pivGrp.v



			# Shapes Group
			shapesGrp = createNode('transform', n=names.get('shapesGrp', 'rnm_shapesGrp'), p=grp)
			nodeList.append(shapesGrp)
			freezeList.append(shapesGrp)
			fitNode.shapesVis >> shapesGrp.v
			
			if mirrorFitRig:
				reverseCtrlScale = createNode('multDoubleLinear', n=names.get('reverseCtrlScale', 'rnm_reverseCtrlScale'))
				nodeList.append(reverseCtrlScale)
				shapesGrp.scaleX.set(-1)

			pivCtrls = []

			pivShapeAttr = [
			fitNode.shapeHeel,
			fitNode.shapeToe,
			fitNode.shapeBankIn,
			fitNode.shapeBankOut,
			fitNode.shapeBall
			]

			pivots = [
			'heel',
			'toe',
			'bankIn',
			'bankOut',
			'ball'
			]
			bufList = []
			# Create pivot points
			rad = 1.2
			for i, piv in enumerate(pivots): # Don't create control for ball
				if i is not len(pivots)-1:
					buf = createNode('transform', n='%s_%s' % (names.get('buf', 'rnm_buf'), pivots[i]), p=pivGrp)
					nodeList.append(buf)
					bufList.append(buf)
					freezeList.append(buf)
					if self.dev: print buf

					if self.dev: print pivots[i]
					pivCtrl = createNode('joint', n='pivot_%s' % pivots[i], p=buf)
					pivCtrls.append(pivCtrl)
					nodeList.append(pivCtrl)
					ctrlList.append(pivCtrl)
					pivCtrl.radius.set(rad)
					rb.messageConnect(pivCtrl, 'message', fitNode, pivCtrl.shortName().split('|')[-1])
					if self.dev: print pivCtrl
					col.setViewportRGB([pivCtrl], [0.5,1,0.5])
					addAttr(pivCtrl, ln='curveLen', min=0, dv=1, k=1)
					pivCtrl.curveLen.set(k=0, cb=1)

					posZTrans = createNode('transform', n='%s_posZ'  % pivots[i], p=pivCtrl)
					nodeList.append(posZTrans)
					pivCtrl.curveLen >> posZTrans.tz

					negZTrans = createNode('transform', n='%s_negZ'  % pivots[i], p=pivCtrl)
					nodeList.append(negZTrans)
					unitConv = createNode('unitConversion')
					unitConv.conversionFactor.set(-1)
					pivCtrl.curveLen >> unitConv.i
					unitConv.o >> negZTrans.tz

					zIndics = rb.boneIndic(posZTrans, negZTrans, worldGrp, blackGrey=0)

				# Control Shape
				pivShapeGrp = createNode('transform', n='%s_%s' % (pivots[i], names.get('shapesGrp', 'rnm_shapesGrp')), p=shapesGrp)
				nodeList.append(pivShapeGrp)
				fitNode.controlScaleResult >> pivShapeGrp.scaleX
				fitNode.controlScaleResult >> pivShapeGrp.scaleY
				fitNode.controlScaleResult >> pivShapeGrp.scaleZ
				freezeList.append(pivShapeGrp)
				if self.dev: print pivShapeGrp

				pivNode = ls(rb.shapeMaker(name='%s_%s_%s_%s' % (start, fitRig, pivots[i], names.get('pivShape', 'rnm_pivShape')), shape=1 ) )[0]
				parent(pivNode, pivShapeGrp)
				pivNode.translate.set([0,0,0])
				pivNode.rotate.set([90,0,0])
				pivNode.scale.set([1,1,1])
				pivNode.message >> pivShapeAttr[i]
				makeIdentity(pivNode, apply=1, t=1, r=1, s=1, n=0, pn=1)
				pivShape = pivNode.getShapes()[0]
				col.setViewportRGB([pivShape], self.colorsIK[side])
				nodeList.append(pivNode)
				if i is not len(pivots)-1:
					parentConstraint(pivCtrl, pivShapeGrp)
				else:
					parentConstraint(mid, pivShapeGrp)
				if self.dev: print pivShape

			if mirrorFitRig:

				# Heel
				move(bufList[0], -1, z=1, rpr=1, r=1, ws=0)
				xform(bufList[0], ro=[0,90,0], ws=1)
				# Toe
				move(bufList[1], 1, z=1, rpr=1, r=1, ws=0)
				xform(bufList[1], ro=[0,-90,0], ws=1)
				# In
				move(bufList[2], 1, x=1, rpr=1, r=1, ws=0)
				# xform(bufList[2], ro=[0,0,0], ws=1)
				# Out
				move(bufList[3], -1, x=1, rpr=1, r=1, ws=0)
				xform(bufList[3], ro=[0,180,0], r=1)


			else:
				# Heel
				move(bufList[0], -1, z=1, rpr=1, r=1, ws=0)
				xform(bufList[0], ro=[0,-90,0], ws=1)
				# Toe
				move(bufList[1], 1, z=1, rpr=1, r=1, ws=0)
				xform(bufList[1], ro=[0,90,0], ws=1)
				# In
				move(bufList[2], -1, x=1, rpr=1, r=1, ws=0)
				# xform(bufList[2], ro=[0,0,0], ws=1)
				# Out
				move(bufList[3], 1, x=1, rpr=1, r=1, ws=0)
				xform(bufList[3], ro=[0,180,0], r=1)

			rb.lockAndHide(pivCtrls, ['ty', 'rx', 'rz', 'sx', 'sy', 'sz', 'v'])


			bankIndics = rb.boneIndic(pivCtrls[2], pivCtrls[3], worldGrp, blackGrey=1)
			rollIndics = rb.boneIndic(pivCtrls[0], pivCtrls[1], worldGrp, blackGrey=1)



		# Finalize

		for node in nodeList:
			print node
			if not hasAttr(node, 'fitNode'):
				addAttr(node, k=1, h=self.hidden, at='message', ln='fitNode')
			fitNode.deleteList.connect(node.fitNode)
			# node.fitNode.connect(fitNode.deleteList, nextAvailable=1, f=1)
		
		print 'Footroll Rig Finished'
		select(fitNode)
		return fitNode

   	
	def mirrorFitRig(self, fitNode):
		'''
		Digs through and finds mirror joints to each join in provided fitrig, and uses those joints to create a new one.
		Connects result attributes
		'''
		# Get joints 
		joints = fitNode.jointsList.get()
		if self.dev:
			print 'Joints:'
			print joints
		inputFitNodes = fitNode.fitNodesList.get()

		# Error check
		if not all(self.hasMirror(j) for j in joints):
			print 'Failed Joints: '
			raise Exception('Not all joints associated with fitNode have mirrored joints connected.')
			# Add options for specifying joints to be mirrored?
		if not all(self.hasMirror(fn) for fn in inputFitNodes):
			print 'Failed FitNodes: '
			raise Exception('Not all input fitNodes associated with fitNode have mirrored fitNodes connected.')

		# Get mirror joints
		mirrorJoints = []
		for j in joints:
			mirrorJoints.append(j.mirror.get())

		if self.dev: 
			print 'Mirrored Joints:'
			print mirrorJoints

		# get mirror fitNodes
		mirrorFitNodes = []
		for fn in inputFitNodes:
			mirrorFitNodes.append(fn.mirror.get())


		# rigParent = self.fitNode.getParent()
		# mirrorFitRig = fitRig.__init__(self, joints=mirrorJoints, rigType='poleVectorIK')

		# Create mirrored fitRig class instance (or maintain standard class instance? easy link wouldnt be so bad?)
		mirrorFitRig = footRollFitRig(mirrorFitNodes, self.fitSkeleton, mirrorFitRig=True)

		# Get fitNode
		mirrorFitNode = mirrorFitRig.fitNode
		attributes = [
		]
		# connect attributes in this list and hide right side
		for attribute in attributes:
			fitNode.attr(attribute).connect(mirrorFitNode.attr(attribute), force=1)
			mirrorFitNode.attr(attribute).set(k=0, cb=0)


		if not hasAttr(fitNode, 'mirror'):
			addAttr(fitNode, ln='mirror', at='message', k=1)
		if not hasAttr(mirrorFitNode, 'mirror'):
			addAttr(mirrorFitNode, ln='mirror', at='message', k=1)
		mirrorFitNode.mirror.connect(fitNode.mirror)


		if self.dev: print 'Mirror Fit Node: %s' % mirrorFitNode
		return mirrorFitNode

# =================================================================================

def deleteFitRig(fitNode=None):
	print 'Deleting selected fit rigs...'
	if fitNode is None:
		fitNode = getFitNode(selection = ls(sl=1))
		if not len(fitNode):
			raise Exception('FitNode not found.')

	if not isinstance(fitNode, list):
		fitNode = [fitNode]
	# rb.deleteOtherInstances(fitNode)
	for fn in fitNode:
		# Reparent any children of fitNode to fitNode's current parent
		if len(fn.getChildren()):
			parent(fn.getChildren(), fn.getParent(), r=True)
		# deleteByAttrOutput(fn, 'deleteList')
		if hasAttr(fn, 'deleteList'):
			outputs = fn.deleteList.outputs(shapes=True)
			delete(outputs)
		if fn.exists():
			delete(fn)

def getFitNode(selection=None, rigType=None):
	'''ToDo
	If objects in selection have fitNodes associated with them, return them.  If the rigType is specified, only
	return those nodes.
	ISSUE keeps returning the joint as well.  not good.
	'''
	dev=0
	fitNodeList = []
	finalFitNodeList = []

	# Convert selection to a list
	if not isinstance(selection, list):
		selection = [selection]

	for sel in selection:
		if dev: 
			print "\nSelection:"
			print sel
		# Error check
		if not isinstance(sel, PyNode):
			raise Exception('Object is not a PyNode: %s' % sel)

		# Check if selected object IS the fitNode
		if hasAttr(sel, 'rigType'):
			fitNodeList.append(sel)

		if hasAttr(sel, 'fitNode'):
			if dev:
				print 'fitNode attr found'
				print sel.fitNode

			connections = sel.fitNode.listConnections()
			# connections = sel.fitNode.listConnections(sh=True)
			
			if dev:
				print "Connection List:"
				print connections

			for node in connections:
				if dev:
					print "Connection:"
					print node

				if hasAttr(node, 'rigType'):
					if dev: print "Node has rigtype attribute"
					if dev: print 'objectType is %s' % objectType(node)
					if objectType(node, isType='transform'):
						if not node in fitNodeList:
							fitNodeList.append(node)

	if dev:
		print 'Fit node List:'
		print fitNodeList

	if rigType is None:
		finalFitNodeList = fitNodeList
	else:
		for fitNode in fitNodeList:
			if dev: print "Rig Type: %s / %s" % (rigType, fitNode.rigType.get())
			
			if fitNode.rigType.get() in [rigType]:
				if dev: 'print rigType match found: %s' % fitNode
				finalFitNodeList.append(fitNode)

	return finalFitNodeList

def deleteRig(rigNode=None, skeletonInstance=None):
	print 'This one?'
	# if skeletonInstance:
	# 	skeletonInstance.disconnectRigHeirarchy()
	# 	skeletonInstance.disconnectOutputSkeleton(raiseExc=False)

	if rigNode is None:
		print 'Deleting selected rig(s)...'
		rigNodes = ls(sl=True)
	else:
		print 'Deleting specified rig(s)...'

	rigNodes = getRigNode(selection = rigNodes)
	for rigNode in rigNodes:
		if rigNode is not None:
			if hasAttr(rigNode, 'rigNodes'):
				if hasAttr(rigNode, 'exportJoints'):
					for j in rigNode.exportJoints.get():
						rb.removeMatrixConstraint(j)

				if hasAttr(rigNode, 'asset'):
					delete(rigNode)
				else:
					rigNodes = rigNode.rigNodes.outputs()
					delete(rigNodes)



def getRigNode(selection=None, rigType=None, changeSelection=True):
	if selection is None:
		selection = ls(sl=1)

	dev=1


	# Make selection into a list
	if not isinstance(selection, list):
		selection=[selection]
	
	# Error check
	if not len(selection):
		raise Exception('No selection specified.')

	for sel in selection:
		if not isinstance(sel, PyNode):
			raise Exception('Object is not a PyNode: %s' % sel)

	# Gather rigNodes
	rigNodes = []
	rigNodeCount = 0
	for sel in selection:
		if hasAttr(sel, 'rigNode'):
			if dev: print 'HAS ATTRIBUTE'
			rigNode = sel.rigNode.listConnections(sh=True)
			if len(rigNode):
				if dev: print 'RIG NODE CONNECTION TRUE'
				rigNodeCount = rigNodeCount + 1
				# check if it's an fkIk rigNode
				if rigType is None:
					if dev: print 'RIGTYPE NOT SPECIFIED'
					if rigNode[0] not in rigNodes:
						if dev: print 'RIG NODE NOT FOUND IN RIGNODES LIST, APPENDING'
						rigNodes.append(rigNode[0])
				elif hasAttr(rigNode[0], 'rigType') and rigNode[0].rigType.get() == rigType:
					if dev: print 'RIGTYPE SPECIFIED'
					# Prevent duplication
					if rigNode[0] not in rigNodes:
						if dev: print 'RIG NODE NOT FOUND IN RIGNODES LIST, APPENDING'
						rigNodes.append(rigNode[0])
			else:
				raise Exception('No rigNode connected to: %s' % sel)

	if not len(rigNodes):
		if rigNodeCount:
			raise Exception( 'No RigNodes of correct type found on selected objects.' )
		else:
			raise Exception( 'No RigNodes found on selected objects.' )
	else:
		if changeSelection:
			select(rigNodes)

	return rigNodes

def constructNames(namesList):
	'''
	More comprehensive naming convention handler
	
	Input: List of dictionaries
	Input Example:

	namesList = [
	{'name': 'globalMove', 		'warble': 'ctrl',	'side': 3, 	'other': ['1test', '2test'] },
	{'name': 'offset', 			'warble': 'ctrl',	'side': 3, 	'other': [] },
	{'name': 'fitSkeleton',		'warble': 'grp',	'side': 3, 	'other': [] },
	{'name': 'fitRig',			'warble': 'ctrl',	'side': 3, 	'other': [] },
	{'name': 'rig',				'warble': 'grp',	'side': 3, 	'other': [] },
	{'name': 'geometry',		'warble': 'grp',	'side': 3, 	'other': [] },
	]

	'''
	dev = 0
	preset = 0
	# 0  --  hand_L_JNT_end
	# 1  --  lJntHandEnd

	case = 2 # lower, Capitalize, UPPER

	# Presets
	caseDict = [2, 0]
	warbleDict = {
	'ctrl': 	['_Ctrl', 	'Ctl', ],
	'grp': 		['_Grp', 	'Grp', ],
	'jnt': 		['_Jnt', 	'Jnt', ],
	'meta':		['_META',	'META', ]
	}
	sideDict = {
	0:		['_M', 'm'],
	1:		['_L', 'l'],
	2:		['_R', 'r'],
	3:		['', '']
	}
	
	# Return lists
	originalNames = []
	newNames = []

	for nameDict in namesList:
		side = nameDict.get('side', None)
		# If using preset 0 and warble not found, use all caps
		if not nameDict.has_key('name'):
			raise Exception('Dictionary key not found: Name -- %s' % nameDict)
		
		originalNames.append(nameDict['name'])
		name = [nameDict['name'].lower(), nameDict['name'].capitalize(), nameDict['name'].upper()][caseDict[preset]]

		if nameDict.has_key('warble'):
			# if warble not found in warbleDict, default to whatever was sent in, and set case
			try:
				warble = warbleDict[ nameDict['warble'] ][preset]
			except:
				# Auto capitalize
				warble = [
				nameDict['warble'].lower(),
				nameDict['warble'].capitalize(),
				nameDict['warble'].upper()
				][caseDict[preset]]

			# warble = ( '%s' % warbleDict.get(nameDict['warble'])[preset], [ nameDict['warble'].lower(), nameDict['warble'].capitalize(), nameDict['warble'].upper() ][caseDict[preset]] ) )
		else:
			warble = ''


		# if self.dev: print 'Warble: %s ' % warble

		other = []

		if nameDict.has_key('other'):
			for o in nameDict['other']:
				# other.append([nameDict['other'][i].lower(), nameDict['other'][i].capitalize(), nameDict['other'][i].upper()][caseDict[preset]])
				other.append(o)


		# Preset 0	
		if preset == 0:
			# print 'NAME: %s' % nameDict['name']
			# print 'SIDE: %s' % sideDict[side][preset]
			# print 'WARBLE: %s' % warble
			# print 'OTHER: %s' % '_'.join(other)
			# Create string from other.  Add initial '_' if not empty.
			if len(other):
				otherStr = '_' + '_'.join(other)
			else:
				otherStr = ''

			newNames.append('%s%s%s%s' % (nameDict['name'], sideDict[side][preset], warble, otherStr ) )
		
		# Preset 1
		elif preset == 1:
			newNames.append('%s%s%s' % (sideDict[side[preset]], warble, nameDict['name'], ''.join(other)) )
		else:
			raise Exception('Preset is out of range')

	# Assemble result dictionary
	

	namesDict = dict(zip(originalNames, newNames))
	if dev:
		print '\nNAMES CONSTRUCTION:'
		for i in range(len(namesDict)):
			print originalNames[i] + ': ' + newNames[i]
		print '\n'
	return namesDict

def populateCurveWithJoints(curve, controlNode, prefix, suffix, attrSuffix='', vectorAttribute=None, defaultJ=3, maxJ=12, last=False):

	dev = False
	
	nodeList = []
	resJoints = []
	resGrps = []

	curveShape = listRelatives(curve, s=True)



	if len(curveShape) == 0:
		raise Exception('No shape node found.')

	if not hasAttr(controlNode, 'resultPoints%s '% attrSuffix):
		addAttr(controlNode, ln='resultPoints_%s'% attrSuffix, ct='input', at='short', min=0, max=maxJ, dv=defaultJ, keyable=True)

	if not hasAttr(controlNode, 'startBounds_%s'% attrSuffix):
		addAttr(controlNode, ln='startBounds_%s'% attrSuffix, ct='input', at='float', min=0, max=1, dv=0, keyable=True)

	if not hasAttr(controlNode, 'endBounds_%s'% attrSuffix):
		addAttr(controlNode, ln='endBounds_%s'% attrSuffix, ct='input', at='float', min=0, max=1, dv=1, keyable=True)



	if dev:
		print "\n"
		print 'Per Point:'
		print "\n"

	# add node
	addSetAttrs = {'i2': 0}
	add = createNode('addDoubleLinear', n='add_%s_%s' % (prefix, suffix))
	nodeList.append(add)
	rb.setAttrsWithDictionary(add, addSetAttrs)
	connectAttr(controlNode.attr('resultPoints_%s'% attrSuffix), add.i1)
	if dev: print add


	for i in range(maxJ):
		# name objects
		if range(maxJ) < 10:
			d = i
		elif range(maxJ) < 100:
			d = '%01d' % i
		else:
			d = '%02d' % i

		if dev:
			print "\nD Value:"
			print d

	
		names = {
		'divName': 			'%s_DIV_%s' % 		(prefix, d),
		'srName': 			'%s_SR_%s' % 		(prefix, d),
		'mpName': 			'%s_MP_%s' % 		(prefix, d),
		'condName':			'%s_COND_%s' % 		(prefix, d),
		'addOffsetName': 	'%s_Offset_ADD_%s' % (prefix, d),
		'resGroupName': 	'%s_Result_GRP_%s' % (prefix, d),
		'jointName': 		'%s_JNT_%s' % 		(prefix, d),
		'bendIndic1Name':	'bendIndic'
		}

		startMidEnd = ['Start', 'Mid', 'End']



		#For each joint in the max list
		
		# divide node
		divSetAttrs = {'i1x': i, 'i2x': 1, 'op':2}
		div = createNode('multiplyDivide', n=names['divName'])
		nodeList.append(div)
		rb.setAttrsWithDictionary(div, divSetAttrs)
		connectAttr(add.o, div.i2x)
		if dev: print div


		# set range node
		srSetAttrs = {'oldMinX': 0, 'oldMaxX': 1}
		sr = createNode('setRange', n=names['srName'])
		nodeList.append(sr)
		rb.setAttrsWithDictionary(sr, srSetAttrs)
		connectAttr(div.ox, sr.vx)
		connectAttr(controlNode.attr('startBounds_%s'% attrSuffix), sr.minX)
		connectAttr(controlNode.attr('endBounds_%s'% attrSuffix), sr.maxX)
		if dev: print sr
		

		# condition node
		condType = 4
		if last is True:
			condType = 5
		condSetAttrs = {'firstTerm': i, 'operation': condType, 'colorIfTrueR': 1, 'colorIfTrueG': 1, 'colorIfTrueB': 1,  'colorIfFalseR': 0, 'colorIfFalseG': 0, 'colorIfFalseB': 0 }
		cond = createNode('condition', n=names['condName'])
		nodeList.append(cond)
		rb.setAttrsWithDictionary(cond, condSetAttrs)
		connectAttr(add.o, cond.secondTerm)
		if dev: print cond

		# offset
		addOffsetAttrs = {}
		addOffset = createNode('addDoubleLinear', n=names['addOffsetName'])
		nodeList.append(addOffset)
		rb.setAttrsWithDictionary(addOffset, addOffsetAttrs)
		connectAttr(sr.ox, addOffset.i2)
		if dev: print addOffset

		# motion path node
		mpSetAttrs = {'fractionMode': True, 'follow': False, 'worldUpType': 3, 'inverseUp': False, 'frontAxis': 0, 'upAxis': 1}
		mp = createNode('motionPath', n=names['mpName'])
		nodeList.append(mp)
		rb.setAttrsWithDictionary(mp, mpSetAttrs)
		connectAttr(curveShape[0].worldSpace[0], mp.geometryPath)
		connectAttr(addOffset.o, mp.u)
		connectAttr(cond.ocr, mp.frozen)
		if vectorAttribute is not None:
			connectAttr(controlNode.attr(vectorAttribute), mp.worldUpVector)
		if dev: print mp


		# Final Group
		resGrpAttrs = {}
		resGrp = createNode('transform', n=names['resGroupName'])
		resGrps.append(resGrp)
		nodeList.append(resGrp)
		# freezeList.append(resGrp)
		# rb.setAttrsWithDictionary(resGrp, resGrpAttrs)
		connectAttr(mp.allCoordinates, resGrp.translate)
		connectAttr(mp.rotate, resGrp.rotate)
		connectAttr(cond.ocr, resGrp.visibility)
		if dev: print resGrp


		# Final Joint
		resJointAttrs = {'radius': 1}
		resJoint = createNode('joint', n=names['jointName'], p=resGrp)
		resJoints.append(resJoint)
		nodeList.append(resJoint)
		rb.setAttrsWithDictionary(resJoint, resJointAttrs)
		addAttr(resJoint, ln='offset', k=1)
		connectAttr(resJoint.offset, addOffset.i1)
		addAttr(resJoint, ln='uValue', k=1)
		connectAttr(mp.u, resJoint.uValue)
		col.setViewportRGB(resJoint, [0,0,0])
		rb.lockAndHide([resJoint], ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v'])
		if dev: print resJoint

	return resGrps, resJoints

def heirSort(heirList):
	'''
	Sorts a list of DAG objects based on how many parents it has. Helps to allow new objects created to find parents cleanly.
	'''
	heirScore = {}
	for item in heirList:
		heirScore[item] = (len(item.getAllParents()))

	import operator
	sortedHeir = sorted(heirScore.items(), key=operator.itemgetter(1))

	ret = []
	for s in sortedHeir:
		ret.append(s[0])
	return ret

def mirrorShapes(shapes=None, fitNode=None):
	'''Take a fitNode shape or specify a fitNode to mirror shapes transform values to other side'''
	# If no shape specified, check for fitnode or for selection
	if shapes is None:
		if fitNode is None:
			shapes = ls(sl=1)
		else:
			fitNodeShapeAttrsUni = listAttr(fitNode, category='shape')
			shapes = []
			for attrs in fitNodeShapeAttrsUni:
				shapes.append(fitNode.attr(attrs).get())


	if not isinstance(shapes, list):
		shapes=[shapes]

	for sel in shapes:
		fitNode = sel.message.get()
		if not fitNode:
			raise Exception ('No fitnode found on shape %s.' % sel.nodeName())

		outputAttr = sel.message.listConnections(d=1, s=0, p=1)
		if len(outputAttr)==1:
			outputAttr = outputAttr[0]
		else:
			raise Exception('Selected node %s has more than one output.' % sel.nodeName())
		# get shape attributes list to check against
		shapeAttrsUni = listAttr(fitNode, category='shape')
		# convert listConnections unicode output to pymel attr class
		shapeAttrs = []
		for attr in shapeAttrsUni:
			shapeAttrs.append(fitNode.attr(attr))
		
		# Determine whether connected attribute is part of 'shape' category
		if outputAttr not in shapeAttrs:
			raise Exception('Verify that node is a shape: %s' % sel.nodeName())


		# get mirrored fitnode
		mirrorFitNode = fitNode.mirror.get()
		mirrorShape = mirrorFitNode.attr(outputAttr).get()
		print mirrorShape
		attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
		for attribute in attrs:
			mirrorShape.attr(attribute).set(sel.attr(attribute).get())