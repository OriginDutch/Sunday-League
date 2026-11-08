shader_type spatial;
render_mode cull_disabled;
// Stands seen through the match camera (Marcel, 2026-11-08, option B "only what really blocks the view"):
// everything on the camera (West) side that sticks up above the sight line from the camera to the
// near touchline is not drawn. main.gd updates `stand_clip` every frame; off in the hub.
// stand_clip = (touchline z, slope = camera height / camera distance behind the touchline, on, margin)
global uniform vec4 stand_clip;
uniform vec4 albedo : source_color = vec4(1.0);
uniform float roughness = 0.8;
uniform float metallic = 0.0;

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	if (stand_clip.z > 0.5 && w.z > stand_clip.x && w.y > (w.z - stand_clip.x) * stand_clip.y + stand_clip.w) {
		discard;
	}
	ALBEDO = albedo.rgb;
	ROUGHNESS = roughness;
	METALLIC = metallic;
}
