from pymel.core import *
import utils as rb
import colorOverride as col

def boxRig():
	'''creates a useful control for blendshapes, with attributes for adjusting size and result values built in.'''
	rigGroup = createNode('transform', n=names.get('rigGroup', 'rnm_rigGroup'))
	rb.cbSep(rigGroup)
	addAttr(rigGroup, ln='boxVis', at='short', min=0, max=1, dv=1)
	rigGroup.boxVis.set(cb=1)

	compAttrs = [
	'minBounds',
	'maxBounds',
	'newMinBounds',
	'newMaxBounds',
	'outputPos',
	'outputNeg'
	]

	for attribute in compAttrs:
		rb.cbSep(rigGroup)
		addAttr(rigGroup, ln=attribute, at='compound', numberOfChildren=3, k=1)
		addAttr(rigGroup, ln='%sX' % attribute, at='float', p=attribute, k=1)
		addAttr(rigGroup, ln='%sY' % attribute, at='float', p=attribute, k=1)
		addAttr(rigGroup, ln='%sZ' % attribute, at='float', p=attribute, k=1)