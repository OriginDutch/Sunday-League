shader_type spatial;
// Seats and fans drawn with MultiMesh (GDD §10i).
// Vertex COLOR is a part mask: r = club/shirt colour (INSTANCE_CUSTOM.rgb, linear),
// g = skin, b = fixed colour (seat bracket) or a trousers colour from the palette.
// INSTANCE_CUSTOM.a packs two small indices: (skin + 3 * trousers) / 32.

uniform vec3 fixed_color : source_color = vec3(0.29, 0.31, 0.32);
uniform vec3 skin_light : source_color = vec3(0.945, 0.788, 0.647);
uniform vec3 skin_mid : source_color = vec3(0.788, 0.604, 0.431);
uniform vec3 skin_dark : source_color = vec3(0.478, 0.318, 0.204);
uniform float roughness_value = 0.6;
uniform bool trousers_from_palette = false;
uniform vec3 trousers_palette[6];   // linear colours, set from big_stand.gd

varying vec3 v_albedo;

void vertex() {
	int idx = int(round(INSTANCE_CUSTOM.a * 32.0));
	int s = idx % 3;
	int t = clamp(idx / 3, 0, 5);
	vec3 skin = s == 0 ? skin_light : (s == 1 ? skin_mid : skin_dark);
	vec3 fixed = trousers_from_palette ? trousers_palette[t] : fixed_color;
	v_albedo = COLOR.r * INSTANCE_CUSTOM.rgb + COLOR.g * skin + COLOR.b * fixed;
}

void fragment() {
	ALBEDO = v_albedo;
	ROUGHNESS = roughness_value;
}
