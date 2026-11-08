shader_type spatial;
// Seated crowd drawn with one MultiMesh (every occupied seat gets a fan).
// Vertex COLOR is a part mask: r = shirt (INSTANCE_CUSTOM.rgb, linear), g = skin, b = trousers.
// INSTANCE_CUSTOM.a packs (skin + 3 * trousers) / 32. Same mask as instanced_parts.gdshader.
// Reactions come from uniforms set by the crowd script: jump (goal for), slump (goal against).

uniform vec3 skin_light : source_color = vec3(0.945, 0.788, 0.647);
uniform vec3 skin_mid : source_color = vec3(0.788, 0.604, 0.431);
uniform vec3 skin_dark : source_color = vec3(0.478, 0.318, 0.204);
uniform vec3 trousers_palette[6];
uniform float jump = 0.0;     // 0..1, everyone bounces (each with their own phase)
uniform float slump = 0.0;    // 0..1, heads down
uniform float sway = 1.0;     // idle sway amount

varying vec3 v_albedo;

float hash(float n) {
	return fract(sin(n * 12.9898) * 43758.5453);
}

void vertex() {
	int idx = int(round(INSTANCE_CUSTOM.a * 32.0));
	int s = idx % 3;
	int t = clamp(idx / 3, 0, 5);
	vec3 skin = s == 0 ? skin_light : (s == 1 ? skin_mid : skin_dark);
	v_albedo = COLOR.r * INSTANCE_CUSTOM.rgb + COLOR.g * skin + COLOR.b * trousers_palette[t];

	float ph = hash(float(INSTANCE_ID)) * 6.2831;
	float upper = smoothstep(0.55, 0.75, VERTEX.y);          // torso, arms and head move, legs stay
	// idle: a little sway
	VERTEX.x += sin(TIME * 1.3 + ph) * 0.015 * upper * sway;
	// goal: stand up and bounce
	float bounce = abs(sin(TIME * 9.0 + ph)) * 0.32 + 0.3;
	VERTEX.y += jump * bounce * step(0.3, VERTEX.y);
	// conceded: lean forward, head down
	VERTEX.z += slump * 0.12 * upper;
	VERTEX.y -= slump * 0.06 * upper;
}

void fragment() {
	ALBEDO = v_albedo;
	ROUGHNESS = 0.8;
}
