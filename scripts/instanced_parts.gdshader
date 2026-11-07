shader_type spatial;
// Seats and fans drawn with MultiMesh (GDD §10i).
// Vertex COLOR is a part mask: r = club/shirt colour (INSTANCE_CUSTOM.rgb, linear),
// g = skin (INSTANCE_CUSTOM.a picks light/mid/dark), b = fixed colour (seat bracket / trousers).

uniform vec3 fixed_color : source_color = vec3(0.29, 0.31, 0.32);
uniform vec3 skin_light : source_color = vec3(0.945, 0.788, 0.647);
uniform vec3 skin_mid : source_color = vec3(0.788, 0.604, 0.431);
uniform vec3 skin_dark : source_color = vec3(0.478, 0.318, 0.204);
uniform float roughness_value = 0.6;

varying vec3 v_albedo;

void vertex() {
	float s = INSTANCE_CUSTOM.a;
	vec3 skin = s < 0.25 ? skin_light : (s < 0.75 ? skin_mid : skin_dark);
	v_albedo = COLOR.r * INSTANCE_CUSTOM.rgb + COLOR.g * skin + COLOR.b * fixed_color;
}

void fragment() {
	ALBEDO = v_albedo;
	ROUGHNESS = roughness_value;
}
