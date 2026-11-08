shader_type spatial;
// Crowd v2: every fan is a MultiMesh instance; animations are baked bone matrices in `anim`
// (row = frame, 3 texels per bone = rows of a 3x4 matrix; last texel .x = how much the fan sits).
// Mesh CUSTOM0 = (bone, part, u, v); NORMAL is only used to wave the flag cloth.
// INSTANCE_CUSTOM = (intro + 1 + 32 * loop, start time, accessory mask,
//                    palette indices skin | hair<<3 | trousers<<7 | coat<<10 | cap<<13 | shirt<<16). See fan_crowd.gd.

uniform sampler2D anim : filter_nearest, repeat_disable;
uniform int bones = 21;
uniform float now = 0.0;
uniform float fps = 24.0;
uniform float seat_height = 0.455;
uniform int clip_row[16];
uniform int clip_len[16];
uniform int clip_desync[16];       // 1 = idle loop: every fan its own phase/speed
uniform int clip_scarf_up = 9;
uniform int clip_scarf_twirl = 10;
uniform int clip_flag = 11;
uniform int clip_flag_cw = 12;
uniform vec3 club_a : source_color = vec3(0.1, 0.55, 0.25);
uniform vec3 club_b : source_color = vec3(0.95, 0.95, 0.95);
uniform vec3 skin_pal[8];
uniform vec3 hair_pal[16];
uniform vec3 trousers_pal[8];
uniform vec3 coat_pal[8];
uniform vec3 shirt_pal[16];       // 0 = club colour
uniform sampler2D crest : source_color, filter_linear_mipmap, repeat_disable;

varying vec3 v_col;
varying vec2 v_uv;
varying flat int v_kind;           // 0 plain, 1 scarf stripes, 2 flag
varying flat int v_pattern;

float hash(float n) {
	return fract(sin(n * 12.9898) * 43758.5453);
}

mat4 bone_mat(int row, int bone) {
	vec4 r0 = texelFetch(anim, ivec2(bone * 3, row), 0);
	vec4 r1 = texelFetch(anim, ivec2(bone * 3 + 1, row), 0);
	vec4 r2 = texelFetch(anim, ivec2(bone * 3 + 2, row), 0);
	return mat4(vec4(r0.x, r1.x, r2.x, 0.0), vec4(r0.y, r1.y, r2.y, 0.0), vec4(r0.z, r1.z, r2.z, 0.0), vec4(r0.w, r1.w, r2.w, 1.0));
}

bool has(int mask, int bit) {
	return ((mask >> bit) & 1) == 1;
}

void vertex() {
	int bone = int(CUSTOM0.x + 0.5);
	int part = int(CUSTOM0.y + 0.5);
	v_uv = CUSTOM0.zw;
	int clips = int(round(INSTANCE_CUSTOM.x));
	int intro = (clips & 31) - 1;
	int lp = clips >> 5;
	int mask = int(round(INSTANCE_CUSTOM.z));
	// seed from the fan's position: INSTANCE_ID repeats across the per-variant MultiMeshes
	float seed = hash(dot(MODEL_MATRIX[3].xyz, vec3(12.9898, 4.1414, 78.233)) + 0.37);
	float t = max(0.0, now - INSTANCE_CUSTOM.y);

	// --- which frame
	float f;
	int base;
	int len;
	bool in_intro = intro >= 0 && t * fps < float(clip_len[max(intro, 0)] - 1);
	if (in_intro) {
		base = clip_row[intro];
		len = clip_len[intro];
		f = t * fps;
	} else {
		if (intro >= 0) {
			t -= float(clip_len[intro] - 1) / fps;
		}
		base = clip_row[lp];
		len = clip_len[lp];
		float speed = clip_desync[lp] == 1 ? mix(0.8, 1.2, seed) : mix(0.92, 1.08, seed);
		float phase = clip_desync[lp] == 1 ? seed * float(len) : 0.0;
		f = mod(t * fps * speed + phase, float(len));
	}
	int f0 = int(floor(f));
	int f1 = in_intro ? min(f0 + 1, len - 1) : (f0 + 1) % len;
	float w = fract(f);
	int row0 = base + f0;
	int row1 = base + f1;

	// --- accessories on/off
	int cur = in_intro ? -1 : lp;
	bool show = true;
	if (part == 7) show = has(mask, 0);                                  // coat
	else if (part == 8) show = has(mask, 2) && cur != clip_scarf_up && cur != clip_scarf_twirl;
	else if (part == 9) show = has(mask, 3);                             // cap
	else if (part == 10) show = has(mask, 4);                            // beanie
	else if (part == 11) show = has(mask, 5);                            // glasses
	else if (part == 12) show = has(mask, 6);                            // sunglasses
	else if (part == 13) show = has(mask, 7);                            // stubble
	else if (part == 14) show = has(mask, 8);                            // full beard
	else if (part == 15) show = has(mask, 9);                            // goatee
	else if (part == 16) show = has(mask, 10);                           // moustache
	else if (part == 17) show = has(mask, 2) && cur == clip_scarf_up;
	else if (part == 18) show = has(mask, 2) && cur == clip_scarf_twirl;
	else if (part == 19 || part == 20) show = has(mask, 11) && (cur == clip_flag || cur == clip_flag_cw);
	else if (part == 4) show = !has(mask, 15);                           // hair under a cap/beanie

	// --- colours
	int pal = int(round(INSTANCE_CUSTOM.w));
	vec3 shirt = shirt_pal[(pal >> 16) & 15];
	vec3 skin = skin_pal[pal & 7];
	vec3 hair = hair_pal[(pal >> 3) & 15];
	vec3 coat = coat_pal[(pal >> 10) & 7];
	vec3 col = vec3(0.5);
	v_kind = 0;
	v_pattern = (mask >> 12) & 7;
	if (part == 0) col = skin;
	else if (part == 1) col = shirt;
	else if (part == 2) col = trousers_pal[(pal >> 7) & 7];
	else if (part == 3) col = vec3(0.06);
	else if (part == 4 || part == 21) col = hair;
	else if (part == 5) col = vec3(0.03);
	else if (part == 6) col = has(mask, 0) ? coat : (has(mask, 1) ? shirt : skin);
	else if (part == 7) col = coat;
	else if (part == 8 || part == 17 || part == 18) { col = club_a; v_kind = 1; }
	else if (part == 9) col = coat_pal[(pal >> 13) & 7];
	else if (part == 10) col = has(mask, 16) ? club_a : coat_pal[(pal >> 13) & 7];
	else if (part == 11) col = vec3(0.08);
	else if (part == 12) col = vec3(0.02);
	else if (part == 13) col = mix(hair, skin, 0.45);
	else if (part >= 14 && part <= 16) col = hair;
	else if (part == 19) col = vec3(0.7);
	else if (part == 20) { col = club_a; v_kind = 2; }
	v_col = col;

	// --- flag cloth: a thin sheet that bends — slow billow, travelling waves and flutter, all growing
	// towards the free edge (u = 0 at the pole, 1 at the end; v = 0 top, 1 bottom)
	vec3 rest = VERTEX;
	if (part == 20) {
		float ph = seed * 6.2831;
		float u = v_uv.x;
		float billow = sin(now * 2.3 + ph) * 0.28 * u * u * (0.6 + 0.4 * sin(v_uv.y * 3.1416));
		float wave = sin(now * 6.5 - u * 6.0 + v_uv.y * 1.5 + ph) * 0.26 * u
			+ sin(now * 11.0 - u * 10.0 + v_uv.y * 4.0 + ph * 2.0) * 0.08 * u;
		rest += NORMAL * (billow + wave);
		rest.y -= 0.22 * u * u * (0.7 + 0.3 * v_uv.y);          // the free end sags a little
	}
	// the flag cloth drags behind the pole: the further from the pole, the older the frame it follows
	int c0 = row0;
	int c1 = row1;
	float cw = w;
	if (part == 20 && !in_intro) {
		float fc = mod(f - (v_uv.x * v_uv.x * 6.0 + v_uv.x * 1.5 + v_uv.y * 1.2), float(len));
		c0 = base + int(floor(fc));
		c1 = base + (int(floor(fc)) + 1) % len;
		cw = fract(fc);
	}
	vec4 p0 = bone_mat(c0, bone) * vec4(rest, 1.0);
	vec4 p1 = bone_mat(c1, bone) * vec4(rest, 1.0);
	vec3 pos = mix(p0.xyz, p1.xyz, cw);
	// small people on a seat: lift them so they sit on it instead of in it
	float sit0 = texelFetch(anim, ivec2(bones * 3, row0), 0).x;
	float sit1 = texelFetch(anim, ivec2(bones * 3, row1), 0).x;
	float s = length(MODEL_MATRIX[1].xyz);
	pos.y += seat_height * (1.0 - s) / s * mix(sit0, sit1, w);
	VERTEX = show ? pos : vec3(0.0);
}

void fragment() {
	NORMAL = normalize(cross(dFdy(VERTEX), dFdx(VERTEX)));
	vec3 col = v_col;
	if (v_kind == 1) {
		col = fract(v_uv.x * 6.0) < 0.5 ? club_a : club_b;
	} else if (v_kind == 2) {
		vec2 uv = v_uv;
		bool b = false;
		if (v_pattern == 1) b = fract(uv.y * 2.5) < 0.5;                         // horizontal stripes
		else if (v_pattern == 2) b = fract(uv.x * 3.0) < 0.5;                    // vertical stripes
		else if (v_pattern == 3) b = uv.x > 0.5;                                 // halves
		else if (v_pattern == 4) b = uv.x * 0.7 + uv.y < 0.75;                   // diagonal
		else if (v_pattern == 5) b = abs(uv.x - 0.5) < 0.09 || abs(uv.y - 0.5) < 0.12;   // cross
		col = b ? club_b : club_a;
		if (v_pattern >= 6) {                                                   // crest on plain / stripes
			if (v_pattern == 7) col = fract(uv.y * 2.5) < 0.5 ? club_b : club_a;
			vec2 cuv = (uv - vec2(0.5)) * vec2(1.6, 1.0) + vec2(0.5);
			if (cuv.x > 0.0 && cuv.x < 1.0 && cuv.y > 0.0 && cuv.y < 1.0) {
				vec4 c = texture(crest, cuv);
				col = mix(col, c.rgb, c.a);
			}
		}
	}
	ALBEDO = col;
	ROUGHNESS = 0.85;
}
