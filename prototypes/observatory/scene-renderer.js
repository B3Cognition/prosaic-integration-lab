import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const C = { coral: 0xff7952, teal: 0x42e5db, gold: 0xf4bd64, metal: 0x536c66, dark: 0x162c2d };
const TAU = Math.PI * 2;
let seed = 71;
const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
const v = (x, y, z) => new THREE.Vector3(x, y, z);

export function createExecutionScene(container, { onSelect, labels, reducedMotion }) {
  const gsap = globalThis.gsap;
  if (!gsap) throw new Error('Animation dependency unavailable');
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x090f13);
  scene.fog = new THREE.FogExp2(0x090f13, .025);
  const camera = new THREE.PerspectiveCamera(33, 1, .1, 100);
  camera.position.set(6.6, 4.6, 9.6);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.6));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.info.autoReset = false;
  renderer.domElement.setAttribute('aria-hidden', 'true');
  container.append(renderer.domElement);
  renderer.domElement.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    container.dispatchEvent(new CustomEvent('graphicslost'));
  });
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(.15, -.15, 0);
  controls.enableDamping = true;
  controls.dampingFactor = .07;
  controls.enablePan = false;
  controls.minDistance = 4.2;
  controls.maxDistance = 24;
  controls.minPolarAngle = .3;
  controls.maxPolarAngle = Math.PI * .78;
  controls.autoRotateSpeed = .15;
  controls.update();
  const pmrem = new THREE.PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  const environment = pmrem.fromScene(room, .04);
  scene.environment = environment.texture;
  scene.environmentIntensity = .42;
  room.dispose();
  pmrem.dispose();
  scene.add(new THREE.HemisphereLight(0x91c3c7, 0x182128, .7));
  const key = new THREE.DirectionalLight(0xffe7c6, 2.3);
  key.position.set(-3, 7, 5); scene.add(key);
  const rim = new THREE.DirectionalLight(0x51c6df, 2.4);
  rim.position.set(4, 2, -4); scene.add(rim);
  const coralLight = new THREE.PointLight(C.coral, 4, 8, 2);
  coralLight.position.set(0, .2, .7); scene.add(coralLight);
  const cyanLight = new THREE.PointLight(C.teal, 4, 8, 2);
  cyanLight.position.set(4, 1.5, -.6); scene.add(cyanLight);

  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), .3, .4, 1.25);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  // Fine procedural roughness supplies material detail without image assets.
  const size = 256, bytes = new Uint8Array(size * size * 4);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const i = (y * size + x) * 4;
    const n = 95 + random() * 100 + Math.sin(y * 2.5) * 25;
    bytes[i] = bytes[i + 1] = bytes[i + 2] = n; bytes[i + 3] = 255;
  }
  const roughness = new THREE.DataTexture(bytes, size, size, THREE.RGBAFormat);
  roughness.wrapS = roughness.wrapT = THREE.RepeatWrapping;
  roughness.repeat.set(3, 3); roughness.needsUpdate = true;
  const metal = new THREE.MeshStandardMaterial({ color: C.metal, metalness: .85, roughness: .36, roughnessMap: roughness });
  const dark = new THREE.MeshStandardMaterial({ color: C.dark, metalness: .55, roughness: .5, roughnessMap: roughness });
  const copper = new THREE.MeshStandardMaterial({ color: 0x9e6745, metalness: .9, roughness: .34, roughnessMap: roughness });
  const ceramic = new THREE.MeshStandardMaterial({ color: 0x9caaa0, metalness: .3, roughness: .5, roughnessMap: roughness });
  const lit = (color, intensity = 1) => new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: intensity, roughness: .48, metalness: .4, roughnessMap: roughness, bumpMap: roughness, bumpScale: .027 });
  const coral = lit(C.coral, .45), cyan = lit(C.teal, .65), gold = lit(C.gold, .15);
  const shellMaterial = new THREE.MeshPhysicalMaterial({ color: 0x6b9c96, metalness: .5, roughness: .24, transparent: true, opacity: .19, side: THREE.DoubleSide, depthWrite: false, clearcoat: 1 });
  const selectable = [], explodables = [], animated = [], shellParts = [], cableGroups = [];
  const system = new THREE.Group(); scene.add(system);
  const components = {
    runtime: new THREE.Group(), provider: new THREE.Group(), tool: new THREE.Group(), harness: new THREE.Group(),
  };
  components.provider.position.set(4.1, .85, -.9);
  components.tool.position.set(-3.65, -.4, 1.0);
  components.harness.position.set(0, -2.05, 0);
  Object.values(components).forEach(g => system.add(g));
  const mesh = (geometry, material, group, position, component) => {
    const object = new THREE.Mesh(geometry, material);
    if (position) object.position.copy(position);
    group.add(object);
    if (component) { object.userData.component = component; selectable.push(object); }
    return object;
  };
  const tube = (points, radius, material, group, segments = 72) => mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), segments, radius, 6, false), material, group);
  const ring = (radius, thickness, group, material, y = 0, arc = TAU) => {
    const object = mesh(new THREE.TorusGeometry(radius, thickness, 8, 100, arc), material, group, v(0, y, 0));
    object.rotation.x = Math.PI / 2; return object;
  };
  const cylinder = (radius, height, group, material, y = 0, segments = 64) => mesh(new THREE.CylinderGeometry(radius, radius, height, segments), material, group, v(0, y, 0));

  // The Runtime specimen: an open shell, circuit wafers, layered coils and a core.
  const runtime = components.runtime;
  const coreGeometry = new THREE.SphereGeometry(.76, 96, 64);
  const positions = coreGeometry.attributes.position;
  for (let i = 0; i < positions.count; i++) {
    const p = v().fromBufferAttribute(positions, i);
    const d = 1 + .026 * Math.sin(p.x * 38) * Math.sin(p.y * 31) * Math.cos(p.z * 35) + .018 * Math.cos(p.y * 55 + p.x * 24);
    p.multiplyScalar(d); positions.setXYZ(i, p.x, p.y * 1.14, p.z);
  }
  coreGeometry.computeVertexNormals();
  const core = mesh(coreGeometry, coral, runtime, v(0, .12, 0), 'runtime');
  const cortex = new THREE.Group(); runtime.add(cortex);
  for (let i = 0; i < 22; i++) {
    const points = [];
    for (let j = 0; j <= 96; j++) {
      const a = j / 96 * TAU, latitude = -.9 + i / 21 * 1.8;
      const radius = Math.sqrt(1 - latitude * latitude) * .83;
      const ripple = .03 * Math.sin(a * 17 + i * 2);
      points.push(v(Math.cos(a) * (radius + ripple), latitude + .13 + Math.sin(a * 9 + i) * .025, Math.sin(a) * (radius + ripple)));
    }
    tube(points, .009, i % 4 === 0 ? coral : copper, cortex, 110);
  }
  animated.push({ object: cortex, rate: .035, axis: 'y' });
  const innerCage = new THREE.Group(); runtime.add(innerCage);
  for (let i = 0; i < 3; i++) {
    const r = ring(.99 + i * .085, .018, innerCage, i === 1 ? coral : copper);
    r.rotation.set(i * .7 + .4, i * 1.1, i * .6);
  }
  animated.push({ object: innerCage, rate: -.055, axis: 'y' });
  // Small, textured lobes and contact points make the exposed core a specimen.
  const coreSurface = new THREE.MeshStandardMaterial({ color: 0x9e4933, metalness: .62, roughness: .42, roughnessMap: roughness, bumpMap: roughness, bumpScale: .04 });
  for (let i = 0; i < 54; i++) {
    const a = i * 2.39996, y = (i / 53 * 2 - 1) * .83;
    const radius = Math.sqrt(Math.max(0, 1 - y * y)) * .79;
    const lobe = mesh(new THREE.SphereGeometry(.045 + random() * .065, 12, 10), i % 9 === 0 ? gold : coreSurface, cortex, v(Math.cos(a) * radius, y + .13, Math.sin(a) * radius));
    lobe.scale.set(1, 1.7, .7); lobe.lookAt(0, .13, 0);
  }
  const shell = mesh(new THREE.CylinderGeometry(1.48, 1.58, 3.1, 100, 1, true, .8, 4.7), shellMaterial, runtime, v(0, .05, 0), 'runtime');
  shellParts.push(shell);
  for (let i = 0; i < 39; i++) {
    const a = .8 + i / 38 * 4.7;
    const points = [v(Math.sin(a) * 1.55, -1.5, Math.cos(a) * 1.55), v(Math.sin(a) * 1.52, 0, Math.cos(a) * 1.52), v(Math.sin(a) * 1.46, 1.6, Math.cos(a) * 1.46)];
    const rib = tube(points, i % 4 === 0 ? .024 : .008, i % 4 === 0 ? metal : copper, runtime);
    shellParts.push(rib);
  }
  for (let i = 0; i < 7; i++) {
    const angle = 1.3 + i * .55;
    const panel = mesh(new THREE.CylinderGeometry(1.51, 1.59, 2.1, 10, 1, true, angle, .22), dark, runtime, v(0, .05, 0), 'runtime');
    panel.material = dark.clone(); panel.material.side = THREE.DoubleSide;
    shellParts.push(panel);
    for (const y of [-.9, .95]) {
      mesh(new THREE.SphereGeometry(.038, 8, 6), ceramic, runtime, v(Math.sin(angle + .11) * 1.59, y, Math.cos(angle + .11) * 1.59));
    }
  }
  for (const [index, y] of [-1.5, -1.3, 1.35, 1.58].entries()) {
    const hoop = ring(1.52, index % 2 ? .025 : .058, runtime, index % 2 ? copper : metal, y, 5.1);
    hoop.rotation.z = .62; shellParts.push(hoop);
    explodables.push({ object: hoop, base: hoop.position.clone(), delta: v(0, y > 0 ? .65 : -.3, 0) });
  }
  for (const [index, y] of [-1.13, -.98, .97, 1.12].entries()) {
    const board = new THREE.Group(); board.position.y = y; runtime.add(board);
    const wafer = cylinder(1.24, .045, board, index % 2 ? dark : metal);
    wafer.geometry = new THREE.CylinderGeometry(1.24, 1.24, .045, 80, 1, false, .75, 4.85);
    ring(1.22, .015, board, copper, .03, 5.05).rotation.z = .6;
    for (let j = 0; j < 22; j++) {
      const a = .82 + j / 21 * 4.7;
      const chip = mesh(new THREE.BoxGeometry(.13, .07, .2), j % 4 === 0 ? gold : ceramic, board, v(Math.sin(a) * 1.03, .06, Math.cos(a) * 1.03));
      chip.rotation.y = a;
      tube([v(Math.sin(a) * .8, .03, Math.cos(a) * .8), v(Math.sin(a + .04) * .94, .03, Math.cos(a + .04) * .94), v(Math.sin(a) * 1.18, .03, Math.cos(a) * 1.18)], .004, copper, board, 12);
    }
    explodables.push({ object: board, base: board.position.clone(), delta: v(0, y > 0 ? 1.0 + index * .16 : -.45 - index * .15, 0) });
  }
  for (let i = 0; i < 6; i++) {
    const a = .85 + i / 5 * 4.6;
    const post = cylinder(.065, 3.15, runtime, metal, .05, 12);
    post.position.x = Math.sin(a) * 1.45; post.position.z = Math.cos(a) * 1.45;
    for (const y of [-1.5, 1.6]) mesh(new THREE.SphereGeometry(.09, 12, 8), copper, runtime, v(post.position.x, y, post.position.z));
    shellParts.push(post);
  }
  // A substantial foot and a recessed workflow control layer.
  const harness = components.harness;
  cylinder(1.75, .18, harness, dark);
  cylinder(1.64, .09, harness, metal, .14);
  ring(1.65, .012, harness, gold, .21);
  cylinder(1.25, .3, harness, dark, .35);
  for (let i = 0; i < 48; i++) {
    const a = i / 48 * TAU;
    const tab = mesh(new THREE.BoxGeometry(.035, .18, .17), i % 6 === 0 ? gold : copper, harness, v(Math.sin(a) * 1.58, .02, Math.cos(a) * 1.58), 'harness');
    tab.rotation.y = a;
  }
  for (let i = 0; i < 14; i++) {
    const a = i / 14 * TAU;
    mesh(new THREE.BoxGeometry(.12, .04, .15), ceramic, harness, v(Math.sin(a) * .98, .52, Math.cos(a) * .98), 'harness');
  }

  // Provider: a ribbed transport capsule, with a luminous internal data stack.
  const provider = components.provider;
  cylinder(.82, .12, provider, metal, -.95);
  cylinder(.9, .12, provider, dark, -1.1);
  const providerCore = mesh(new THREE.SphereGeometry(.57, 48, 32), cyan, provider, v(0, .08, 0), 'provider');
  providerCore.scale.y = 1.28;
  const providerGlass = mesh(new THREE.CylinderGeometry(.76, .76, 1.85, 64, 1, true), shellMaterial, provider, v(0, .08, 0), 'provider');
  for (let i = 0; i < 12; i++) ring(.78, .027, provider, i % 4 === 0 ? cyan : metal, -.8 + i * .16);
  for (let i = 0; i < 8; i++) {
    const a = i / 8 * TAU;
    const rod = cylinder(.025, 1.96, provider, copper, .08, 8);
    rod.position.set(Math.cos(a) * .78, .08, Math.sin(a) * .78);
  }
  cylinder(.8, .1, provider, metal, 1.06);
  ring(.62, .018, provider, cyan, 1.13);
  for (let i = 0; i < 5; i++) {
    const disc = cylinder(.36, .045, provider, i % 2 ? cyan : dark, -.45 + i * .23);
    disc.rotation.z = .15;
    explodables.push({ object: disc, base: disc.position.clone(), delta: v(.15 * i, .12 * i, .08 * i) });
  }
  explodables.push({ object: providerGlass, base: providerGlass.position.clone(), delta: v(.65, .3, 0) });

  // Tool: exposed hexagonal evidence module with fine pins and gold tracks.
  const tool = components.tool;
  for (const y of [-.35, -.18, .12]) {
    const plate = cylinder(.92, .09, tool, y === .12 ? metal : dark, y, 6);
    plate.rotation.y = Math.PI / 6;
    explodables.push({ object: plate, base: plate.position.clone(), delta: v(-.2, y > 0 ? .5 : -.1, .1) });
  }
  cylinder(.67, .11, tool, copper, .2);
  ring(.6, .027, tool, gold, .29);
  mesh(new THREE.IcosahedronGeometry(.37, 3), gold, tool, v(0, .43, 0), 'tool');
  for (let i = 0; i < 28; i++) {
    const a = i / 28 * TAU;
    mesh(new THREE.BoxGeometry(.035, .22, .075), i % 4 === 0 ? gold : copper, tool, v(Math.sin(a) * .75, .28, Math.cos(a) * .75), 'tool');
    tube([v(Math.sin(a) * .4, .28, Math.cos(a) * .4), v(Math.sin(a + .1) * .55, .28, Math.cos(a + .1) * .55), v(Math.sin(a) * .8, .28, Math.cos(a) * .8)], .005, gold, tool, 15);
  }
  const toolHalo = ring(1.04, .008, tool, gold, -.1);
  animated.push({ object: toolHalo, rate: .13, axis: 'z' });

  // Braided activity conduits; every particle route terminates at a real module.
  const routes = [
    { component: 'provider', color: C.teal, points: [v(1.1, .35, -.1), v(2, 1.6, -.6), v(3.25, .25, -.95), v(4.1, .85, -.9)] },
    { component: 'tool', color: C.gold, points: [v(-1.05, -.25, .2), v(-1.8, .45, .8), v(-2.8, -1.25, 1.25), v(-3.65, -.15, 1)] },
    { component: 'harness', color: C.coral, points: [v(.4, -1, .9), v(.7, -1.5, 1.2), v(1.2, -1.8, .3), v(.25, -1.9, .25)] },
  ];
  const spriteCanvas = document.createElement('canvas'); spriteCanvas.width = spriteCanvas.height = 32;
  const ctx = spriteCanvas.getContext('2d');
  const gradient = ctx.createRadialGradient(16, 16, 0, 16, 16, 16);
  gradient.addColorStop(0, '#fff'); gradient.addColorStop(.16, '#fffe'); gradient.addColorStop(.5, '#fff5'); gradient.addColorStop(1, '#fff0');
  ctx.fillStyle = gradient; ctx.fillRect(0, 0, 32, 32);
  const sprite = new THREE.CanvasTexture(spriteCanvas);
  for (const route of routes) {
    const curve = new THREE.CatmullRomCurve3(route.points);
    const bundle = new THREE.Group(); system.add(bundle);
    for (let i = 0; i < 11; i++) {
      const points = [];
      for (let j = 0; j <= 100; j++) {
        const t = j / 100, p = curve.getPoint(t), a = t * 7 * TAU + i / 11 * TAU;
        p.add(v(Math.sin(a) * .045, Math.cos(a) * .045, Math.sin(a + 2) * .035)); points.push(p);
      }
      tube(points, .009, i % 4 === 0 ? lit(route.color, .45) : metal, bundle, 100);
    }
    tube(route.points, .055, dark, bundle);
    for (let i = 1; i < 18; i++) {
      const t = i / 18, p = curve.getPoint(t), tangent = curve.getTangent(t);
      const clamp = mesh(new THREE.TorusGeometry(.063, .012, 5, 10), copper, bundle, p);
      clamp.quaternion.setFromUnitVectors(v(0, 0, 1), tangent.normalize());
    }
    const signal = tube(route.points, .018, new THREE.MeshBasicMaterial({ color: route.color, transparent: true, opacity: .3 }), bundle);
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(90 * 3), 3));
    const particles = new THREE.Points(particleGeometry, new THREE.PointsMaterial({ color: route.color, size: .13, map: sprite, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: .8 }));
    system.add(particles); cableGroups.push({ curve, component: route.component, particles, signal });
  }

  // A quiet instrument bed supplies scale and contact instead of a star field.
  const bed = mesh(new THREE.CircleGeometry(15, 100), new THREE.MeshStandardMaterial({ color: 0x020607, metalness: .08, roughness: .95 }), scene, v(0, -2.22, 0));
  bed.rotation.x = -Math.PI / 2;
  const grid = new THREE.PolarGridHelper(12, 20, 12, 150, 0x1e343a, 0x172a30); grid.position.y = -2.21; scene.add(grid);
  grid.material.transparent = true; grid.material.opacity = .35;
  for (const radius of [2.4, 4.8, 7.2]) ring(radius, .005, scene, new THREE.MeshBasicMaterial({ color: 0x31505a, transparent: true, opacity: .5 }), -2.2);
  const dustPositions = new Float32Array(150 * 3);
  for (let i = 0; i < 150; i++) { dustPositions[i * 3] = (random() - .5) * 17; dustPositions[i * 3 + 1] = random() * 6 - 2; dustPositions[i * 3 + 2] = (random() - .5) * 12; }
  const dustGeometry = new THREE.BufferGeometry(); dustGeometry.setAttribute('position', new THREE.BufferAttribute(dustPositions, 3));
  const dust = new THREE.Points(dustGeometry, new THREE.PointsMaterial({ color: 0x9abeb5, size: .025, map: sprite, transparent: true, opacity: .4, depthWrite: false })); scene.add(dust);

  // Consolidate static detail while preserving moving/exploded parts and picking.
  const movable = new Set([core, ...animated.map(item => item.object), ...explodables.map(item => item.object)]);
  const groups = []; system.traverse(object => { if (object.isGroup) groups.push(object); });
  for (const group of groups) {
    const buckets = new Map();
    for (const object of [...group.children]) {
      if (!object.isMesh || movable.has(object) || Array.isArray(object.material)) continue;
      const key = object.material.uuid + ':' + (object.userData.component || '') + ':' + Boolean(object.geometry.index);
      if (!buckets.has(key)) buckets.set(key, []); buckets.get(key).push(object);
    }
    for (const objects of buckets.values()) {
      if (objects.length < 2) continue;
      const geometries = objects.map(object => { object.updateMatrix(); return object.geometry.clone().applyMatrix4(object.matrix); });
      const mergedGeometry = mergeGeometries(geometries);
      geometries.forEach(geometry => geometry.dispose());
      if (!mergedGeometry) continue;
      const merged = mesh(mergedGeometry, objects[0].material, group);
      merged.userData.component = objects[0].userData.component;
      objects.forEach(object => { group.remove(object); object.geometry.dispose(); });
    }
  }
  selectable.length = 0;
  system.traverse(object => { if (object.isMesh && object.userData.component) selectable.push(object); });

  let state = { time: 15.2, active: { component: 'provider', start: 12.4, end: 21.5 }, done: false, toolFailed: false };
  let playing = !reducedMotion, selected = null, layout = 'section', exploded = false, lastStamp = 0, visualTime = 0, disposed = false, renderable = false;
  let authoredCore = null, assetStatus = 'loading', assetTexturesReady = false;
  const overviewPosition = new THREE.Vector3(6.6, 4.6, 9.6);
  const overviewTarget = new THREE.Vector3(.15, -.15, 0);
  const anchors = { runtime: v(1.05, 1.35, .45), provider: v(4.1, 2.25, -.9), tool: v(-3.65, -.9, 1.1), harness: v(-.9, -2.2, .6) };
  const labelOffsets = { runtime: [0, -35], provider: [-45, -30], tool: [-70, 30], harness: [-50, 20] };

  // The authoring source and packed .blend are kept beside this browser export.
  // Retain the original specimen until the complete glTF, including maps, loads.
  new GLTFLoader().load(new URL('./assets/runtime-core.glb', import.meta.url).href, gltf => {
    if (disposed) return;
    const meshes=[];
    gltf.scene.traverse(object=>{if(object.isMesh)meshes.push(object);});
    assetTexturesReady=meshes.some(object=>object.material.map&&object.material.normalMap&&object.material.roughnessMap);
    if(!assetTexturesReady){assetStatus='procedural-fallback';return;}
    authoredCore = gltf.scene;
    authoredCore.position.set(0, .12, 0);
    authoredCore.traverse(object => {
      if (!object.isMesh) return;
      object.userData.component = 'runtime'; selectable.push(object);
    });
    runtime.add(authoredCore);
    core.visible = false; cortex.visible = false;
    const original = selectable.indexOf(core);
    if (original >= 0) selectable.splice(original, 1);
    assetStatus = 'blender';
  }, undefined, () => { assetStatus = 'procedural-fallback'; });

  function positionLabels() {
    const width = container.clientWidth, height = container.clientHeight;
    const placed = [];
    for (const label of labels) {
      const component = label.dataset.component;
      const point = anchors[component].clone().project(camera);
      let x = (point.x * .5 + .5) * width + labelOffsets[component][0];
      let y = (-point.y * .5 + .5) * height + labelOffsets[component][1];
      x = Math.max(12, Math.min(width - label.offsetWidth - 12, x));
      y = Math.max(155, Math.min(height - 105, y));
      for (const previous of placed) {
        if (x < previous.x + previous.width + 5 && x + label.offsetWidth + 5 > previous.x && y < previous.y + previous.height + 5 && y + label.offsetHeight + 5 > previous.y) {
          y = Math.min(height - 105, previous.y + previous.height + 8);
        }
      }
      placed.push({ x, y, width: label.offsetWidth, height: label.offsetHeight });
      label.style.transform = `translate(${x}px,${y}px)`;
      label.style.opacity = selected && selected !== component ? '.18' : point.z > 1 ? '0' : '1';
      label.style.pointerEvents = point.z > 1 ? 'none' : 'auto';
    }
  }
  function resize() {
    const width = container.clientWidth, height = container.clientHeight;
    renderable = width >= 2 && height >= 2;
    if (!renderable) return;
    camera.aspect = width / height;
    camera.fov = width < 650 ? 42 : 33; camera.updateProjectionMatrix();
    renderer.setSize(width, height, false); composer.setSize(width, height);
    positionLabels();
  }
  const observer = new ResizeObserver(resize); observer.observe(container);
  const raycaster = new THREE.Raycaster();
  let pointerDown = null;
  renderer.domElement.addEventListener('pointerdown', e => { pointerDown = [e.clientX, e.clientY]; });
  renderer.domElement.addEventListener('pointerup', e => {
    if (!pointerDown || Math.hypot(e.clientX - pointerDown[0], e.clientY - pointerDown[1]) > 5) return;
    const rect = renderer.domElement.getBoundingClientRect();
    raycaster.setFromCamera(new THREE.Vector2((e.clientX - rect.left) / rect.width * 2 - 1, -(e.clientY - rect.top) / rect.height * 2 + 1), camera);
    const hit = raycaster.intersectObjects(selectable, false)[0];
    if (hit) onSelect(hit.object.userData.component);
  });
  controls.addEventListener('start', () => { gsap.killTweensOf(camera.position); gsap.killTweensOf(controls.target); });
  function focus(component) {
    component = components[component] ? component : null;
    selected = component;
    const target = component ? components[component].position.clone() : overviewTarget.clone();
    if (component === 'runtime') target.y = .1;
    const distance = component === 'runtime' ? 7.5 : component ? 5.5 : 0;
    const position = component ? target.clone().add(v(.52, .32, .8).normalize().multiplyScalar(distance)) : overviewPosition.clone();
    gsap.to(camera.position, { ...position, duration: reducedMotion ? 0 : 1.3, ease: 'power3.inOut', overwrite: true });
    gsap.to(controls.target, { ...target, duration: reducedMotion ? 0 : 1.3, ease: 'power3.inOut', overwrite: true });
  }
  function setLayout(next) {
    exploded = next === 'exploded'; layout = next;
    for (const part of explodables) {
      const target = part.base.clone().addScaledVector(part.delta, exploded ? 1 : 0);
      gsap.to(part.object.position, { ...target, duration: reducedMotion ? 0 : 1, ease: 'power2.inOut', overwrite: true });
    }
    gsap.to(shellMaterial, { opacity: exploded ? .06 : .19, duration: reducedMotion ? 0 : .8, overwrite: true });
  }
  function update(next, isPlaying) {
    state = next; playing = isPlaying;
    const failed = next.toolFailed;
    gold.color.setHex(failed ? 0xff5c4e : C.gold); gold.emissive.setHex(failed ? 0xff5c4e : C.gold);
    cyan.color.setHex(next.providerFailed ? 0xff5c4e : C.teal); cyan.emissive.setHex(next.providerFailed ? 0xff5c4e : C.teal);
    const active = next.active?.component;
    coral.emissiveIntensity = active === 'provider' || active === 'tool' ? .5 : .22;
    cyan.emissiveIntensity = active === 'provider' ? .75 : .2;
  }
  function animate(stamp) {
    if (disposed) return;
    requestAnimationFrame(animate);
    const delta = Math.min((stamp - lastStamp) / 1000 || 0, .04); lastStamp = stamp;
    if (document.hidden || !renderable) return;
    if (playing && !reducedMotion && !state.done) visualTime += delta;
    controls.autoRotate = playing && !reducedMotion && !selected && !state.done;
    controls.update(delta);
    for (const item of animated) item.object.rotation[item.axis] = visualTime * item.rate;
    (authoredCore || core).scale.setScalar(1 + (!reducedMotion && playing ? Math.sin(visualTime * 2) * .013 : 0));
    for (const channel of cableGroups) {
      const active = state.active?.component === channel.component || channel.component === 'harness' && state.active?.component === 'lab';
      channel.signal.material.opacity = active ? .75 : .14;
      channel.particles.material.opacity = active ? .95 : .06;
      const array = channel.particles.geometry.attributes.position;
      const elapsed = reducedMotion ? state.time : visualTime;
      for (let i = 0; i < array.count; i++) {
        const phase = (elapsed * .32 + i / array.count) % 1;
        const forward = !state.active || state.time - state.active.start < (state.active.end - state.active.start) * .55;
        const point = channel.curve.getPoint(forward ? phase : 1 - phase);
        point.y += Math.sin(i * 1.7) * .022;
        array.setXYZ(i, point.x, point.y, point.z);
      }
      array.needsUpdate = true;
    }
    positionLabels(); renderer.info.reset(); composer.render();
  }
  resize(); requestAnimationFrame(animate);
  return { focus, setLayout, update, renderer,
    setReducedMotion(next) { reducedMotion = next; if (next) { gsap.killTweensOf(camera.position); gsap.killTweensOf(controls.target); controls.autoRotate = false; } },
    info: () => ({ objects: selectable.length, calls: renderer.info.render.calls, triangles: renderer.info.render.triangles, selected, layout, cameraPosition: camera.position.toArray(), cameraTarget: controls.target.toArray(), reducedMotion, renderable, assetStatus,assetTexturesReady,
      explosionSettled: explodables.every(part => part.object.position.distanceTo(part.base.clone().addScaledVector(part.delta, exploded ? 1 : 0)) < .001),
    }),
    dispose() { disposed = true; observer.disconnect(); controls.dispose(); composer.dispose(); environment.dispose(); roughness.dispose(); sprite.dispose(); scene.traverse(object => { object.geometry?.dispose(); if (object.material) for (const material of Array.isArray(object.material) ? object.material : [object.material]) material.dispose(); }); renderer.dispose(); },
  };
}
