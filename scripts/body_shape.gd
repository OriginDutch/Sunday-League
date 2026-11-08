extends SkeletonModifier3D
## Per-player build on top of the animation: shoulder width, muscle (limb thickness), belly, and a head
## that grows a bit less than the body for tall players. Bone scales are inherited by the children, so
## each child undoes what it shouldn't get from its parent.

var scales := {}   # bone name -> Vector3 pose scale
var _ids := {}


func setup(look: Dictionary, body_scale: float) -> void:
	var w: float = look["shoulders"]
	var m: float = look["muscle"]
	var b: float = look["belly"]
	var chest_depth := 1.0 + (m - 1.0) * 0.5
	var head := pow(1.0 / body_scale, 0.6)
	scales = {
		"spine": Vector3(b, 1.0, b),
		"chest": Vector3(w / b, 1.0, chest_depth / b),          # adds up to (w, 1, chest_depth)
		"neck": Vector3(1.0 / w, 1.0, 1.0 / chest_depth),        # back to (1, 1, 1) for the head
		"head": Vector3(head, head, head),
		"upperarm.L": Vector3(m, 1.0, m), "upperarm.R": Vector3(m, 1.0, m),
		"hand.L": Vector3(1.0 / m, 1.0, 1.0 / m), "hand.R": Vector3(1.0 / m, 1.0, 1.0 / m),
		"thigh.L": Vector3(m, 1.0, m), "thigh.R": Vector3(m, 1.0, m),
	}


func _process_modification_with_delta(_delta: float) -> void:
	var sk := get_skeleton()
	if sk == null:
		return
	if _ids.is_empty():
		for n in scales:
			_ids[n] = sk.find_bone(n)
	for n in scales:
		var i: int = _ids[n]
		if i >= 0:
			sk.set_bone_pose_scale(i, scales[n])
