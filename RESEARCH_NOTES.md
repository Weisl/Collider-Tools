# Collision Research Notes

Reference/roadmap-input document, not a spec — compiled 2026-08-15 via an AI-assisted research session (codebase inspection + live GitHub issue-tracker queries + web research against official Unity/Unreal/Godot documentation). Claims are sourced where possible; anything inferred rather than directly confirmed is flagged as such inline. Treat this as a snapshot: engine docs and this repo's own issue tracker both move, so re-verify anything load-bearing before acting on it long after this date.

Two things anchor every "does this fit the addon" judgment call below, found directly in this repo:
- README's contribution philosophy: *"Let's see if the proposed changes fit the overall design and purpose of this addon. I will be strict in keeping a consistent user experience and vision."*
- Issue [#482](https://github.com/Weisl/simple_collider/issues/482): a request to reuse the addon's bounding-fit tooling for occlusion-mesh generation was declined outright ("will not be supported") — the clearest real scope boundary available. Adjacent-but-different problems get pushed out even when the underlying tech is shared.
- The addon also ships no export operator by design, deliberately pushing that concern to a separate sibling addon ("Simple Export," same author).

---

# Part 1: Collision feature-request landscape vs. this addon

Sourced from this addon's own GitHub issue tracker (665+ issues at time of writing — by far the richest source, since it's literal user requests against this exact product), competitor Blender addons, Unity/Unreal/Godot/Source community forums, academic decomposition-tooling papers, and the emerging Khronos glTF physics-extension standard. Historical issue numbers below were cross-checked against live tracker state (open/closed/reason) rather than taken at face value.

## Summary table

| # | Category | Representative asks | Current state in Simple Collider | Verdict |
|---|---|---|---|---|
| 1 | Primitive shape fitting & accuracy | Cylinder fit algorithm, capsule fit accuracy, auto-align to local axis, OBB rotation bugs | Core, mature — box/OBB/sphere/cylinder/capsule/K-DOP/convex-hull all real, custom-fit implementations | Already core — remaining asks are bug-fix/refinement, not new scope |
| 2 | Batch / multi-object workflows | "Batch through all selected objects, one collider per object" | Core architecture — every shape operator loops `context.selected_objects`; `Creation Mode` (Individual/Selection) toggle; validated as a standout in marketplace reviews | Already core, is the addon's differentiator |
| 3 | Compound colliders | "Join multiple colliders into one compound mesh" (#445) | Partial — a `join_primitives` toggle exists at creation time (`add_bounding_primitive.py:2087`) when generating from multiple objects, but no operator joins pre-existing separate collider objects after the fact | Real but narrow gap — see Part 2's "compound colliders reconsidered" for an important nuance |
| 4 | LOD / collision simplification | Trimesh decimation, mesh+collision-in-one-pass, "optimizer" tools | Remesh (wraps stock Voxel Remesh modifier) + decomposition vertex/hull targets give indirect control. A voxel/"Simplified Mesh" grid collider (`bmesh_operations/voxel_generation.py`) has geometry code, tests, and naming/HUD plumbing, but is unregistered — this is the WIP output tracked by issue #577 (open), not a hidden extra feature | Tracked in #577; maintainer's own assessment of the current result: "Pretty useless. Not working as I want" — needs real algorithm work (surface-offset bug, object-relative scaling, sensitivity), not just wiring up |
| 5 | Selection / vertex-group-driven generation | "Make colliders from selection," collision from vertex-group weights (rigged meshes) | Edit-mode/selection-based creation and per-island ("Use Loose Islands") generation already exist; vertex-group-*weight*-driven generation specifically not found, no prior issue | Moderate fit — filed as [#667](https://github.com/Weisl/simple_collider/issues/667) |
| 6 | Naming automation per engine | UE/Unity/Godot/studio presets, sequential UCX numbering, portable preset files | Mature — 4 shipped presets (UE, Unity, Northlight, Godot) with real engine prefixes, per-shape naming tokens, digit count, portable preset files. Verified accurate against live Unreal/Godot docs — see Part 2 | Already well covered |
| 7 | Visualization / overlay | Viewport HUD during creation, color-coded collections, wireframe/shaded views | Mature — wireframe toggle, 8 configurable HUD color roles, group color-coding, color-by-object/material operators | Already well covered |
| 8 | Complexity & budget validation | Engine-specific hull/vertex/triangle limits causing silent import-time re-simplification | Partial — Validation module (14 checks) already checks whole-collider triangle count and collider count per render mesh. No per-convex-hull vertex-count check, and thresholds aren't linked to the active naming/engine preset | Real, precise gap — filed as [#666](https://github.com/Weisl/simple_collider/issues/666) |
| 9 | Physics material assignment | Per-face assignment, mark-existing-material-as-physics, combine-mode standardization | Mature core (create/set/random-color/active-material operators + naming presets). Per-face assignment and material-in-preset asks were already resolved (#366, #365, #367). Combine-mode standardization is an export/runtime concern the addon deliberately doesn't touch | Already well covered |
| 10 | Convex-decomposition tuning & presets | Better progress feedback, non-blocking UI, persist default preset, parameter fiddliness | Mature and actively the addon's current investment area — V-HACD and CoACD both converted to async with a live status overlay; persisting a default preset already shipped (#600) | Already core, correctly the current focus |
| 11 | Non-destructive / modifier-aware workflows | Respect modifier stack without forcing Apply first | A "use modifier stack" tool default exists; loose-parts modifier interaction bugs were already fixed (#420, #489, #571) | Already well covered |
| 12 | Collection / organization | Auto collection-per-source-model, cross-scene collection linking | Cross-scene linking already shipped (#523, #552). Collection-per-model was explicitly rejected by the maintainer ([#507](https://github.com/Weisl/simple_collider/issues/507), closed not-planned) | Not planned — maintainer's call, not a gap |
| 13 | Export / interchange formats | Emerging Khronos `KHR_physics_rigid_bodies`/`KHR_implicit_shapes` glTF standard, USD `UsdPhysics.CollisionAPI` metadata gaps, FBX collision quirks | None by design — no export operator exists, deliberately, pushed to the sibling "Simple Export" addon | Out of scope by explicit precedent — worth watching as the glTF physics standard matures |
| 14 | Ragdoll / bone-driven colliders | Generate hitboxes from armature bones, VRChat PhysBone-style per-bone colliders | Not implemented; fundamentally different input (bones + constraints vs. selected mesh objects). Specialized competitors already exist | Out of scope — same shape as the declined occlusion-mesh request |
| 15 | Wheel / vehicle colliders | Vehicle-specific collider wizards; manual part-segmentation before decomposition flagged elsewhere as "the hardest step" | No dedicated feature, but "Use Loose Islands" (existing, previously buggy, now fixed per #571/#489/#420) already addresses the real underlying pain point | Don't build a vehicle wizard — the general-purpose fix already shipped |
| 16 | Terrain collision | Heightfield/terrain-specific collision generation | Not implemented; terrain collision is heightfield-generated in-engine on all three target engines, not imported-mesh-driven (confirmed in Part 2) | Out of scope |
| 17 | Occlusion mesh generation | Reuse bounding-fit tooling for occlusion culling volumes | Explicitly declined by the maintainer in #482 | Confirmed out of scope — direct precedent |
| 18 | Symmetry / mirroring | Mirror a collider setup for symmetric meshes | No dedicated request found anywhere, including this addon's own issue history. Generic Blender mirror tools + regenerating colliders from mirrored source geometry likely cover the real need | Gap without real demand — low priority |

## Status of the four original prioritized recommendations

1. ~~Ship the orphaned voxel/"Simplified Mesh" collider~~ — already tracked as #577; not "shovel-ready" as first assumed, needs real algorithm fixes (see row 4 above).
2. Retroactive "Join to Compound" operator — filed as [#668](https://github.com/Weisl/simple_collider/issues/668), flagged as an open question since #445 already shipped a creation-time join toggle that may already answer the underlying need. See Part 2's compound-colliders section for why merging isn't actually the cross-engine-preferred pattern.
3. Link validation to the active naming preset / hull-vertex-count check — filed as [#666](https://github.com/Weisl/simple_collider/issues/666).
4. ~~Harden "Use Loose Islands"~~ — already fixed (#571, #489, #420 all closed completed); no action needed.

---

# Part 2: Engine collision systems — Unity vs. Unreal vs. Godot, and relevance to this addon

Researched directly against each engine's current official docs (Unity 6.x manual, Unreal 5.7/5.8 docs, Godot 4.7 docs).

## Shape types — cross-engine support matrix

| Shape | Unity | Unreal | Godot | Note |
|---|---|---|---|---|
| Box | Native (Box Collider) | Native (`UBX_`) | Native (BoxShape3D) | Universal |
| Sphere | Native | Native (`USP_`) | Native (SphereShape3D) | Universal |
| Capsule | Native | Native (`UCP_`, internally "Sphyl") | Native (CapsuleShape3D) | Universal |
| **Cylinder** | **No native primitive** | **No native primitive** | **Native (CylinderShape3D)** | Only Godot has a true cylinder collider — Unity/Unreal have no cylinder primitive at all (PhysX/Chaos don't support one) |
| Convex hull | Native (Mesh Collider, Is Convex) | Native (`UCX_`) | Native (ConvexPolygonShape3D) | Universal |
| Convex decomposition (multi-hull) | Manual (compound of several convex Mesh Colliders) | Built-in Auto Convex Collision tool (Accuracy / Max Hull Verts) | Built-in "Create Convex Collision Siblings" (Quickhull or V-HACD) | Godot ships V-HACD in the editor natively |
| Concave/trimesh | Mesh Collider (non-convex) — static/kinematic only, can't collide with another concave | Complex Collision (per-poly) — usable as simple only via "Use Complex As Simple," which then forbids simulation | ConcavePolygonShape3D — "You can only use concave shapes within StaticBodies," explicitly the slowest shape | All three converge: full-detail mesh collision is static-only, never for simulated/dynamic props |
| Terrain/heightfield | Terrain Collider (matches heightmap) | Landscape collision (separate system) | HeightMapShape3D | All heightfield-generated in-engine, not authored-mesh-driven |
| Convex hull vertex/tri limit | 255 triangles (verbatim current wording; historically conflated with "255 vertices" from the underlying PhysX constraint) | No official numeric limit found in current docs; ~255-vertex ceiling is well-attested via PhysX/forum/bug-tracker sources but not in Epic's current first-party text | No fixed engine-level cap found; practically bounded by decomposition settings, not a hard import limit | Cross-engine safe target: stay comfortably under 255 verts/tris per hull |

## Physics materials & the audio/VFX question

| | Unity | Unreal | Godot |
|---|---|---|---|
| Core properties | Dynamic/Static Friction, Bounciness, Friction/Bounce Combine (Average/Min/Max/Multiply, fixed tiebreak order) | Friction, Restitution, Density, Raise Mass To Power, per-property combine-mode override | friction, bounce, `rough` (friction combine flag), `absorbent` (bounce combine flag) |
| Built-in "surface type" → audio/VFX system | None — confirmed absent. Community convention: read `.name` on collision, or maintain a custom lookup table. | **Yes — first-party.** `EPhysicalSurface` enum (up to 30 named slots), assigned per Physical Material, read at runtime via `GetSurfaceType(FHitResult)` to drive footstep/impact effects. | None — confirmed absent. Community convention (e.g. `godot-material-footsteps` addon): node metadata key, groups, or inspecting the rendered material. |

Asymmetric across engines — only Unreal has a real first-party surface-type-to-effect pipeline. For Unity and Godot it's 100% a naming/metadata convention the project defines itself. The addon's existing physics-material naming/coloring system already fits this pattern reasonably well across all three (name materials to match the target engine's surface-type conventions).

## Simple vs. complex, and triggers

- **Unreal**: explicit, formalized dual representation on one Static Mesh asset (Simple = primitives/hulls, Complex = per-triangle trimesh), switchable via "Collision Complexity." Epic frames "Use Complex Collision As Simple" as a fallback/special-case (no simulation, more expensive queries), not a recommended default — validating the addon's decomposition-first design philosophy.
- **Unity**: no equivalent single-asset dual representation — "simple"/"complex" are just two different component types attached independently, no built-in linkage.
- **Godot**: same — no per-mesh dual-representation toggle; you choose one shape resource per `CollisionShape3D`.
- **Triggers**: Unity has a literal `isTrigger` bool. Unreal has no single bool — a trigger is the composite result of Object Type + Overlap response + Generate Overlap Events + Collision Enabled = Query Only (bundled as a "Trigger" preset). **Godot has no trigger flag on a shape at all — trigger vs. solid is a choice of node type** (`Area3D` vs. `StaticBody3D`/etc.), confirmed by how Godot's glTF OMI-physics importer picks one or the other based on the source collider's `isTrigger` flag.

**Concave/full-mesh collision is static-only, convergently.** All three engines independently enforce the same rule: a non-convex Mesh Collider can't attach to a non-kinematic Rigidbody in Unity, `ConcavePolygonShape3D` is documented as usable only within `StaticBody3D` in Godot, and Unreal's "Use Complex Collision As Simple" explicitly disables physics simulation. Simple Collider's **Full-detail Mesh (copy)** and **Re-meshed** collider types are exactly this kind of geometry, but nothing currently checks whether one is paired with a rigid-body-tagged object — that combination would silently misbehave on import to any of the three engines. Filed as [#670](https://github.com/Weisl/simple_collider/issues/670).

**Relevance**: all three engines have a real trigger/solid distinction; Simple Collider currently has no concept of it at all. Given the addon already has a naming-only pattern for behavioral tagging (`set_rigid_body` appends a suffix without creating real Blender rigid-body data), a parallel "Trigger" naming-token would fit the existing architecture and be useful across all three engines even without an export operator. Filed as [#669](https://github.com/Weisl/simple_collider/issues/669).

## Import & naming convention accuracy check

- **UE-default preset** (`UBX_`/`USP_`/`UCP_`/`UCX_` + `_00`/`_01` numbering) — matches Epic's documented convention exactly, including the compound-numbering pattern. Epic's convention is one *named object per hull*, not one joined mesh carrying multiple names (see below).
- **Godot-default preset** (`-colonly`/`-convcolonly`) — matches Godot's `ResourceImporterScene` suffix convention exactly. This suffix path can only ever produce `StaticBody3D`-based colliders — it cannot produce a trigger (`Area3D`). Godot's `OMI_physics_body` glTF extension path can (via a `"trigger"` body type) and Godot has supported it natively since 4.3, but it's unconfirmed whether Blender's stock glTF exporter writes those extensions out of the box or needs a separate plugin.
- **Unity-default preset** — correctly organizational-only: Unity's Model Importer has zero naming-convention recognition (confirmed by direct doc inspection), unlike Unreal/Godot. Community tools (e.g. `unity-fbx-collider-importer`) exist purely to fill this gap, confirming it's real and unaddressed by Unity itself.

## Compound colliders, reconsidered

Issue #668 (retroactive "join separate colliders into one compound mesh") should account for this nuance: **for all three engines, the natively-preferred compound pattern is separate sibling objects, not one merged mesh.** Unity's own docs call separate Collider components under one Rigidbody parent "compound colliders" — the recommended approach. Unreal's `_00`/`_01` numbering is designed for multiple separately-named objects, not one joined mesh. Godot's compound pattern is multiple `CollisionShape3D` children under one body node. So joining primitives is a scene-organization convenience, not something required for import fidelity — and for Unreal specifically, joining trades away the ability to author distinct, precisely-shaped hulls in favor of the importer's own decomposition of the joined mesh.

## Static vs. kinematic vs. dynamic, and mass

### Classification model

| | Unity | Unreal | Godot |
|---|---|---|---|
| Static | Collider, no Rigidbody | Mobility = Static/Stationary, no Simulate Physics | `StaticBody3D` (distinct node type) |
| Kinematic | Rigidbody + `isKinematic = true` — moved by script/animation; can still push dynamic bodies, isn't pushed back | Movable mobility, Simulate Physics off | `AnimatableBody3D` (distinct node type) — estimates its own velocity so it correctly pushes other bodies |
| Dynamic/simulated | Rigidbody + `isKinematic = false` | Movable mobility + Simulate Physics on (requires collision to exist first) | `RigidBody3D` (distinct node type) |

Unity and Unreal express this as flags/toggles on one object type; Godot expresses it as a choice of node type, consistent with its trigger-vs-solid model.

### Mass — asymmetric across engines

| | Unity | Unreal | Godot |
|---|---|---|---|
| Mass source | Manual only. `Rigidbody.mass`, default 1, flat user-set float. No shape/volume auto-calculation. | **Auto-computed by default**: Physical Material `Density` (g/cm³) × the simple collision shape volume = mass. `Override Mass` available. | Manual only. `RigidBody3D.mass`, default 1.0, flat float. No shape/volume auto-calculation found. |
| Center of mass | Auto-computed by default from all attached colliders' shape/scale (`automaticCenterOfMass`); overridable. | Auto-computed from collision shape(s) and mass; overridable via offset. | Auto-computed from attached shapes (`center_of_mass_mode = AUTO`, default) — moving a collision shape moves the computed center of mass; overridable. |
| Inertia tensor | Auto-computed by default from all attached colliders (`automaticTensor`); overridable. | Auto-computed from collision shape + mass; overridable via a scale multiplier. | Auto-computed from mass and shapes when `inertia = Vector3.ZERO` (default); overridable. |

**Unreal is the one engine where collider volume directly sets weight** — a tight, accurate hull at a given density produces meaningfully different (more realistic) mass than a loose bounding box, a direct documented multiplication. Unity and Godot keep raw mass manual, **but both auto-compute center of mass and/or inertia from actual collider geometry by default** — so tumbling/toppling/torque-response realism is shape-dependent in all three engines, just through different channels.

### Relevance

The addon's entire value proposition (fitted primitives/hulls/decomposition instead of loose bounding volumes) has a real, documented simulated-physics payoff in all three target engines, not just a collision-detection one. In Unreal, a botched or oversized collider makes the object the wrong *weight* under the common auto-mass setup. In Unity/Godot, it skews computed center of mass/inertia — spin and toppling behavior.

Filed as [#671](https://github.com/Weisl/simple_collider/issues/671) — a validation check comparing a collider's volume against the source render mesh's own bounding/hull volume, flagging results wildly outside a reasonable ratio. Catches exactly the failure mode with real cross-engine physics consequences (wrong mass in Unreal, wrong inertia in Unity/Godot), not just "does this collider look reasonable." Natural sibling to #666 in `validation/checks.py`.

This also explains why `set_rigid_body` being naming-only (no real Blender rigid-body data) is the right level of abstraction, not a shortcut — actual mass/density/inertia setup is inherently engine-specific and can't be meaningfully pre-authored in Blender in a way that transfers correctly across all three targets.

## Uncertainties flagged by this research (verify before relying on them)

- Whether Blender's stock glTF exporter (`io_scene_gltf2`) writes `OMI_physics_shape`/`OMI_physics_body` extensions natively or needs a separate add-on.
- Unreal's exact current default for "Max Hull Verts" in the Auto Convex Collision tool, and whether Chaos (UE5's physics engine) preserves the historical ~255-vertex PhysX ceiling — not stated in Epic's current first-party pages, only in forum/bug-tracker threads.
- Whether the Unity Layer Collision Matrix gates trigger pairs the same way it gates solid collision pairs — inferred with high confidence, not from an explicit doc sentence.

---

# Open items / not yet actioned

Filed this session, all currently untriaged/unassigned:
- [#666](https://github.com/Weisl/simple_collider/issues/666) — convex-hull vertex-count validation
- [#667](https://github.com/Weisl/simple_collider/issues/667) — vertex-group-driven generation
- [#668](https://github.com/Weisl/simple_collider/issues/668) — retroactive join-to-compound (flagged as an open question given #445's prior resolution)
- [#669](https://github.com/Weisl/simple_collider/issues/669) — trigger/solid naming tag
- [#670](https://github.com/Weisl/simple_collider/issues/670) — validation: Full-Mesh/Remesh collider + rigid-body tag combination
- [#671](https://github.com/Weisl/simple_collider/issues/671) — validation: collider volume vs. source-mesh volume sanity check

Still open and untouched from before this session: [#577](https://github.com/Weisl/simple_collider/issues/577) (Simple Mesh Collision generator — needs real algorithm work, not just wiring up).
