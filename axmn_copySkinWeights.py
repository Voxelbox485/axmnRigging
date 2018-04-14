from pymel.core import *
def axmn_copySkinWeights():

	# Select source mesh than destination(s). Creates new skinCluster if necessary, adds joints if neccessary, copies skin weights, and prunes and removes unused weights.
	
	selection = ls(sl=1)
	if len(selection) < 2:
		raise Exception('Not enough objects selected.')

	# Split selection
	source = selection[0]

	dest = selection[0:]

	# Get skinCluster (and check for errors)
	# sc =  findRelatedSkinCluster(source)
	sc = ls(mel.findRelatedSkinCluster(source))[0]
	if not sc:
		raise Exception('SkinCluster could not be found on source node %s' % source)

	# Get destination shapes in heirarchy
	destShapes = []
	for d in dest:
		descendants = d.listRelatives(allDescendents=True)
		for desc in descendants:
			if isinstance(desc, nt.DeformableShape):
				destShapes.append(desc)

	# Get joints in skincluster
	scJoints = sc.matrix.inputs()

	if not scJoints:
		raise Exception('No Joints found on SkinCluster %s' % sc.nodeName())

	for destShape in destShapes:
		bindList = scJoints + [destShape]
		print bindList
		sc = skinCluster(bindList, toSelectedBones=True)

		copySkinWeights(source, destShape, noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='closestBone', normalize=True)



'''
string $selection[] = `ls -sl`;
    int $size = `size $selection`;
    if ($size < 2){error "Size Error";}
    for ($i = 1; $i < $size; $i++){
        string $source = $selection[0];
        string $target = $selection[$i];
        
        string $sc = (`findRelatedSkinCluster($source)`);
        if ($sc != ""){
            select $sc;
            string $connections[] = `listConnections ".matrix"`;
            if (`size $connections` > 0){
                select -r $connections;
            } else { error "no joints in skincluster?"; }
        } else {
            //delete (`ls -type "ngSkinLayerDisplay"`);
            //$sc = (`findRelatedSkinCluster($source)`);
            //if ($sc == ""){error "no skincluster found"; }
        }
        select -add $target;
        
        SmoothBindSkin;
        
        select -r $source;
        select -add $target;
        
        copySkinWeights  -noMirror -surfaceAssociation closestPoint -influenceAssociation closestJoint -influenceAssociation closestBone -normalize;
        select -r $target;
        //doPruneSkinClusterWeightsArgList 1 { "0.01" };
		//removeUnusedInfluences;
        select -r $source;
		select -add $target;
    }
}'''