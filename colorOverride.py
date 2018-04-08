import pymel.core as pm

def setViewportRGB(nodes, rgb, shape=0):

	isList = False
	if isinstance(nodes, tuple) or isinstance(nodes, list):
		isList = True
	
	if not isList:
		nodes = [nodes]

	for node in nodes:
		
		shapes = pm.listRelatives(node, s=True)
		if (shape==1 ):
			
			if len(shapes) > 0:
				for shape in shapes:
					
					if pm.hasAttr(shape, 'overrideColorRGB'):
						shape.overrideEnabled.set(1)
						shape.overrideDisplayType.set(0)
						shape.overrideRGBColors.set(1)
						shape.overrideColor.set(rgb)
						shape.overrideColor.set(rgb)
		else:
			if pm.hasAttr(node, 'overrideColorRGB'):
				
				node.overrideEnabled.set(1)
				node.overrideDisplayType.set(0)
				node.overrideRGBColors.set(1)
				node.overrideColorRGB.set(rgb)
				node.overrideColor.set(1)




def resetViewportColor(nodes):
	for node in nodes:
		if pm.hasAttr(node, 'overrideEnabled'):
			node.overrideEnabled.set(0)
			node.overrideDisplayType.set(0)
			node.overrideRGBColors.set(0)
			node.overrideColor.set(0, 0, 0)
			shapes = pm.listRelatives(sel, shapes=True)
			for shape in shapes:
				if pm.hasAttr(shape, 'overrideEnabled'):
					shape.overrideEnabled.set(0)
					shape.overrideDisplayType.set(0)
					shape.overrideRGBColors.set(0)
					shape.overrideColorR.set(0)
					shape.overrideColorG.set(0)
					shape.overrideColorB.set(0)
					shape.overrideColor.set(0)




def setOutlinerRGB(nodes, rgb):
	if not isinstance(nodes, list):
		nodes = [nodes]
	for node in nodes:
		if pm.hasAttr(node, 'useOutlinerColor'):
			node.useOutlinerColor.set(1)
			node.outlinerColor.set(rgb)
		


def resetOutlinerRGB(nodes):
	if not isinstance(nodes, list):
		nodes = [nodes]
	for node in nodes:
		if pm.hasAttr(node, 'useOutlinerColor'):
			node.useOutlinerColor.set(0)
			node.outlinerColor.set(0,0,0)

