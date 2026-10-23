/* Actual V7 STL geometry, offline Three.js rendering, and inspection controls. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const model = JSON.parse($('model-data').textContent);
  const stage = $('stage'), canvas = $('viewport');
  const state = { layout: 'assembly', selected: null, raf: 0, ready: false,
    parts: [], hidden: new Set(), drawn: 0, clipping: null };
  let renderer, scene, camera, orbit, floor, grid, dimensions, selectionBox;
  let pointerDown = null;
  const vector = a => new THREE.Vector3(...a);
  const download = (blob, name) => {
    const link = document.createElement('a'), url = URL.createObjectURL(blob);
    link.href = url; link.download = name; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 3000);
  };
  function buffer(base64) {
    const decoded = atob(base64), bytes = new Uint8Array(decoded.length);
    for (let i = 0; i < bytes.length; i++) bytes[i] = decoded.charCodeAt(i);
    return bytes.buffer;
  }
  function geometry(bytes) {
    const view = new DataView(bytes), count = view.getUint32(80, true);
    if (bytes.byteLength !== 84 + count * 50) throw Error('Invalid embedded STL');
    const positions = new Float32Array(count * 9), normals = new Float32Array(count * 9);
    for (let f = 0; f < count; f++) {
      const at = 84 + f * 50;
      for (let v = 0; v < 3; v++) for (let axis = 0; axis < 3; axis++) {
        positions[f * 9 + v * 3 + axis] = view.getFloat32(at + 12 + v * 12 + axis * 4, true);
        normals[f * 9 + v * 3 + axis] = view.getFloat32(at + axis * 4, true);
      }
    }
    const result = new THREE.BufferGeometry();
    result.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    result.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
    result.computeBoundingBox(); result.computeBoundingSphere();
    return result;
  }
  function fail(error) {
    state.ready = false;
    cancelAnimationFrame(state.raf); state.raf = 0;
    stage.classList.remove('ready');
    $('gpu-status').textContent = 'Saved CAD views';
    $('fallback-message').textContent = '3D could not start or the graphics context stopped. Saved views still work. Open the downloaded HTML in Chrome or Edge, enable browser graphics acceleration, then retry.';
    $('fallback-message').title = String(error && error.message || error);
    $('part-labels').replaceChildren(); $('dimension-labels').replaceChildren();
    $('selection').hidden = true;
  }
  function request() {
    if (!state.ready || document.hidden || state.raf) return;
    state.raf = requestAnimationFrame(draw);
  }
  function visibleParts() { return state.parts.filter(p => p.mesh.visible); }
  function visibleBounds() {
    const box = new THREE.Box3();
    for (const part of visibleParts()) box.union(new THREE.Box3().setFromObject(part.mesh));
    return box.isEmpty() ? new THREE.Box3(vector([-100, -100, 0]), vector([100, 100, 260])) : box;
  }
  function fit(partOnly = false) {
    if (!state.ready) return;
    const selected = state.parts.find(p => p.id === state.selected);
    const box = partOnly && selected && selected.mesh.visible ? new THREE.Box3().setFromObject(selected.mesh) : visibleBounds();
    const centre = box.getCenter(new THREE.Vector3()), size = box.getSize(new THREE.Vector3());
    const vertical = camera.fov * Math.PI / 180;
    const horizontal = 2 * Math.atan(Math.tan(vertical / 2) * camera.aspect);
    const distance = size.length() / (2 * Math.sin(Math.min(vertical, horizontal) / 2)) * 1.18;
    const direction = camera.position.clone().sub(orbit.target).normalize();
    orbit.target.copy(centre);
    camera.position.copy(centre).add(direction.multiplyScalar(distance));
    orbit.maxDistance = Math.max(2400, distance * 4);
    camera.near = .15; camera.far = Math.max(6000, distance * 10); camera.updateProjectionMatrix();
    orbit.update(); request();
  }
  function cameraPreset(view) {
    if (!state.ready) return;
    const directions = { iso: [1, -1.6, .85], front: [0, -1, .001], rear: [0, 1, .001],
      side: [1, 0, .001], top: [0, -.001, 1], bottom: [0, -.001, -1] };
    camera.position.copy(orbit.target).add(vector(directions[view]));
    fit();
    document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  }
  function select(id) {
    state.selected = id;
    const part = state.parts.find(p => p.id === id);
    $('selection').hidden = !part || !state.ready;
    if (part) {
      $('selection-title').textContent = part.title;
      $('selection-kind').textContent = part.kind === 'printed' ? (part.optional ? 'OPTIONAL PRINTABLE PART' : 'PRINTABLE PART / VERIFIED MESH') : 'REFERENCE HARDWARE / DO NOT PRINT';
      const size = part.local.boundingBox.getSize(new THREE.Vector3());
      $('selection-size').textContent = [size.x, size.y, size.z].map(v => v.toFixed(1)).join(' × ') + ' mm · ' + (part.kind === 'printed' ? 'CAD axes' : 'generic clearance envelope');
      $('download-part').hidden = part.kind !== 'printed';
    }
    document.querySelectorAll('.part-row').forEach(row => row.classList.toggle('selected', row.dataset.id === id));
    applyAppearance();
  }
  function updateVisibility() {
    if (!state.ready) return;
    for (const p of state.parts) {
      const allowed = !state.hidden.has(p.id) && (!p.optional || $('optional').checked) &&
        (p.kind === 'printed' || ($('hardware').checked && state.layout !== 'print'));
      p.mesh.visible = allowed; p.edge.visible = allowed && $('edges').checked;
      p.checkbox.checked = allowed;
    }
    if (state.selected && !state.parts.find(p => p.id === state.selected).mesh.visible) select(null);
    $('visible-count').textContent = visibleParts().length + ' visible parts';
    // Lower the studio floor with the exploded chassis so it cannot hide parts.
    floor.position.z = Math.min(-1.5, visibleBounds().min.z - 1.5);
    grid.position.z = floor.position.z + .2;
    updateDimensions(); request();
  }
  function applyAppearance() {
    if (!state.ready) return;
    const mode = $('render-mode').value;
    const cutValue = +$('cut').value, axis = $('cut-axis').value;
    const bounds = visibleBounds();
    const height = bounds.min[axis] + (bounds.max[axis] - bounds.min[axis]) * cutValue / 100;
    state.clipping = cutValue < 100 ? new THREE.Plane(vector(axis === 'x' ? [-1, 0, 0] : axis === 'y' ? [0, -1, 0] : [0, 0, -1]), height) : null;
    const planes = state.clipping ? [state.clipping] : [];
    $('cut-value').textContent = cutValue === 100 ? 'Complete model · no section' : axis.toUpperCase() + ' ≤ ' + height.toFixed(1) + ' mm · uncapped mesh cut';
    for (const p of state.parts) {
      const m = p.material, isSelected = p.id === state.selected;
      const ghost = $('ghost').checked && (p.id === 'v7_cover_front' || p.id === 'v7_cover_rear') && !isSelected;
      m.wireframe = mode === 'wire';
      m.opacity = mode === 'xray' ? (isSelected ? .85 : .18) : ghost ? .13 : 1;
      m.transparent = m.opacity < 1; m.depthWrite = !m.transparent;
      m.color.set(mode === 'technical' ? (p.kind === 'printed' ? '#7eafc7' : '#314f66') : p.color);
      m.emissive.set(isSelected ? '#e9a35b' : p.id.includes('display_graphic') ? '#52cbb5' : '#000000');
      m.emissiveIntensity = isSelected ? .22 : .7;
      m.metalness = mode === 'technical' ? .1 : p.kind === 'printed' ? .12 : .4;
      m.roughness = p.kind === 'printed' ? .45 : .6;
      m.clippingPlanes = planes; m.needsUpdate = true;
      p.mesh.castShadow = !ghost && mode !== 'wire' && mode !== 'xray';
      p.edge.material.color.set(mode === 'technical' || mode === 'wire' ? '#b8efff' : isSelected ? '#ffd5a0' : '#182c36');
      p.edge.material.opacity = ghost ? .13 : mode === 'xray' ? .35 : .46;
      p.edge.material.clippingPlanes = planes; p.edge.material.needsUpdate = true;
      p.edge.visible = p.mesh.visible && $('edges').checked && mode !== 'wire';
    }
    scene.background.set(mode === 'technical' ? '#102333' : '#18232d');
    scene.fog.color.copy(scene.background);
    $('mode-status').textContent = 'LIVE 3D / ' + {studio:'STUDIO',wire:'WIREFRAME',xray:'X-RAY',technical:'BLUEPRINT'}[mode];
    selectionBox.visible = !!state.selected;
    if (state.selected) selectionBox.box.setFromObject(state.parts.find(p => p.id === state.selected).mesh);
    request();
  }
  function setLayout(mode) {
    if (!state.ready) return;
    state.layout = mode;
    if (mode === 'assembly') $('explode').value = 0;
    if (mode === 'exploded' && +$('explode').value === 0) $('explode').value = 65;
    const amount = +$('explode').value / 100;
    $('explode-value').textContent = Math.round(amount * 100) + '%';
    $('explode').disabled = mode === 'print';
    document.querySelectorAll('[data-layout]').forEach(b => {
      b.classList.toggle('active', b.dataset.layout === mode);
      b.setAttribute('aria-pressed', String(b.dataset.layout === mode));
    });
    let x = 0, y = 0, rowDepth = 0;
    for (const p of state.parts) {
      const printing = mode === 'print';
      p.mesh.geometry = printing ? p.local : p.assembled;
      p.edge.geometry = printing ? p.localEdges : p.assembledEdges;
      if (printing && p.kind === 'printed' && (!p.optional || $('optional').checked)) {
        const box = p.local.boundingBox, size = box.getSize(new THREE.Vector3());
        if (x > 0 && x + size.x > 600) { x = 0; y += rowDepth + 20; rowDepth = 0; }
        p.mesh.position.set(x - box.min.x, y - box.min.y, -box.min.z);
        x += size.x + 20; rowDepth = Math.max(rowDepth, size.y);
      } else p.mesh.position.copy(vector(p.explode).multiplyScalar(amount));
      p.mesh.updateMatrixWorld(true);
    }
    updateVisibility(); applyAppearance();
  }
  function updateDimensions() {
    if (!state.ready) return;
    for (const line of dimensions.children) {
      line.geometry.dispose(); line.material.dispose();
    }
    dimensions.clear();
    $('dimension-labels').replaceChildren();
    if (!$('dimensions').checked) return;
    const b = visibleBounds(), lo = b.min, hi = b.max;
    const axes = [
      [[lo.x, lo.y-18, lo.z], [hi.x, lo.y-18, lo.z], 'X', hi.x-lo.x],
      [[hi.x+18, lo.y, lo.z], [hi.x+18, hi.y, lo.z], 'Y', hi.y-lo.y],
      [[hi.x+18, hi.y+18, lo.z], [hi.x+18, hi.y+18, hi.z], 'Z', hi.z-lo.z],
    ];
    state.dimensionAnchors = [];
    for (const [a,b,axis,length] of axes) {
      const geom = new THREE.BufferGeometry().setFromPoints([vector(a), vector(b)]);
      dimensions.add(new THREE.Line(geom, new THREE.LineBasicMaterial({color:'#76dfcb',transparent:true,opacity:.8,depthTest:false})));
      const label = document.createElement('span'); label.className = 'dimension-label';
      label.textContent = axis + ' ' + length.toFixed(1) + ' mm';
      $('dimension-labels').append(label);
      state.dimensionAnchors.push({label, point:vector(a).lerp(vector(b), .5)});
    }
  }
  function positionLabel(label, point, rect) {
    const projected = point.clone().project(camera);
    const onScreen = projected.z > -1 && projected.z < 1 && Math.abs(projected.x) < .94 && Math.abs(projected.y) < .88;
    label.hidden = !onScreen;
    label.style.left = ((projected.x + 1) * rect.width / 2) + 'px';
    label.style.top = ((1 - projected.y) * rect.height / 2) + 'px';
  }
  function draw() {
    state.raf = 0;
    if (!state.ready || document.hidden) return;
    try {
      const moving = orbit.update();
      floor.visible = $('grid').checked;
      grid.visible = $('grid').checked;
      renderer.render(scene, camera); state.drawn++;
      const rect = canvas.getBoundingClientRect();
      const occupied = [];
      const ordered = [...state.parts].sort((a,b) => Number(b.id===state.selected)-Number(a.id===state.selected) || Number(a.kind==='reference')-Number(b.kind==='reference'));
      for (const p of ordered) {
        p.label.hidden = !$('labels').checked || !p.mesh.visible;
        if (!p.label.hidden) {
          positionLabel(p.label, new THREE.Box3().setFromObject(p.mesh).getCenter(new THREE.Vector3()), rect);
          if (!p.label.hidden) {
            const box = p.label.getBoundingClientRect();
            const overlaps = occupied.some(b => box.left < b.right+4 && box.right+4 > b.left && box.top < b.bottom+4 && box.bottom+4 > b.top);
            p.label.hidden = overlaps;
            if (!overlaps) occupied.push(box);
          }
        }
      }
      for (const d of state.dimensionAnchors || []) positionLabel(d.label, d.point, rect);
      if (moving || orbit.autoRotate) request();
    } catch (error) { fail(error); }
  }
  function resize() {
    if (!renderer || !camera || !state.ready) return;
    const rect = stage.getBoundingClientRect();
    renderer.setSize(rect.width, rect.height, false);
    camera.aspect = rect.width / rect.height; camera.updateProjectionMatrix(); request();
  }
  function quality() {
    if (!state.ready) return;
    const q = $('quality').value;
    renderer.setPixelRatio(q === 'eco' ? 1 : Math.min(devicePixelRatio || 1, q === 'ultra' ? 3 : 2));
    renderer.shadowMap.enabled = q !== 'eco';
    renderer.shadowMap.needsUpdate = true; resize();
  }
  function createParts() {
    $('parts-list').replaceChildren(); $('part-labels').replaceChildren(); state.parts = [];
    let triangles = 0;
    for (const original of model.parts) {
      const p = {...original, bytes:buffer(original.mesh)};
      p.local = geometry(p.bytes); triangles += p.local.attributes.position.count / 3;
      p.assembled = p.local.clone().applyMatrix4(new THREE.Matrix4().set(...p.pose.flat()));
      p.localEdges = new THREE.EdgesGeometry(p.local, 25);
      p.assembledEdges = new THREE.EdgesGeometry(p.assembled, 25);
      p.material = new THREE.MeshStandardMaterial({color:p.color, side:THREE.DoubleSide,
        polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1});
      p.mesh = new THREE.Mesh(p.assembled, p.material); p.mesh.name = p.id;
      p.mesh.castShadow = true; p.mesh.receiveShadow = true; scene.add(p.mesh);
      p.edge = new THREE.LineSegments(p.assembledEdges, new THREE.LineBasicMaterial({color:'#25323c',transparent:true,opacity:.46}));
      p.mesh.add(p.edge);
      const row = document.createElement('div'); row.className = 'part-row'; row.dataset.id = p.id;
      const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.setAttribute('aria-label','Show ' + p.title);
      checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
          state.hidden.delete(p.id);
          if (p.optional) $('optional').checked = true;
          if (p.kind === 'reference') $('hardware').checked = true;
        } else state.hidden.add(p.id);
        if (state.layout === 'print') setLayout('print'); else {updateVisibility(); applyAppearance();}
      });
      const button = document.createElement('button'); button.type = 'button';
      const text = document.createElement('span'), swatch = document.createElement('i');
      swatch.style.background = p.color; text.append(swatch, document.createTextNode(p.title));
      const tag = document.createElement('b'); tag.className = 'tag';
      tag.textContent = p.kind === 'reference' ? 'REF' : p.optional ? 'OPT' : 'STL';
      button.append(text, tag); button.addEventListener('click', () => select(p.id));
      button.addEventListener('dblclick', () => {select(p.id);fit(true);});
      row.append(checkbox, button); $('parts-list').append(row); p.checkbox = checkbox;
      p.label = document.createElement('span'); p.label.className = 'part-label';
      p.label.textContent = p.title; p.label.hidden = true; $('part-labels').append(p.label);
      state.parts.push(p);
    }
    $('part-count').textContent = '12 STL + REFERENCES';
    $('performance').textContent = (triangles/1000).toFixed(0) + 'k triangles';
  }
  function cleanup() {
    if (orbit) orbit.dispose();
    if (renderer) {
      const resources = new Set();
      for (const p of state.parts) for (const key of ['local','assembled','localEdges','assembledEdges']) resources.add(p[key]);
      scene.traverse(o => {
        if (o.geometry) resources.add(o.geometry);
        if (o.material) for (const material of (Array.isArray(o.material) ? o.material : [o.material])) resources.add(material);
        if (o.shadow && o.shadow.map) resources.add(o.shadow.map);
      });
      for (const resource of resources) resource.dispose();
      renderer.dispose(); renderer = null;
    }
    state.parts = [];
  }
  function start() {
    try {
      cleanup();
      renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:false,
        powerPreference:'high-performance', preserveDrawingBuffer:true});
      renderer.setClearColor('#18232d'); renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.12;
      renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      renderer.localClippingEnabled = true;
      scene = new THREE.Scene(); scene.background = new THREE.Color('#18232d');
      scene.fog = new THREE.Fog('#18232d', 850, 2200);
      camera = new THREE.PerspectiveCamera(34, 1, .15, 8000); camera.up.set(0,0,1); camera.position.set(300,-480,310);
      orbit = new OrbitControls(camera, canvas); orbit.target.set(0,20,125);
      orbit.enableDamping = true; orbit.dampingFactor = .12; orbit.minDistance = 28;
      orbit.maxDistance = 3000; orbit.rotateSpeed = .7; orbit.autoRotateSpeed = .8;
      orbit.addEventListener('change', request);
      orbit.addEventListener('start', request);
      scene.add(new THREE.HemisphereLight('#e0edf5','#5a4c42',2.1));
      const key = new THREE.DirectionalLight('#fff1db', 3.2); key.position.set(-180,-240,460);
      key.castShadow = true; key.shadow.mapSize.set(2048,2048);
      key.shadow.camera.left = -500; key.shadow.camera.right = 500;
      key.shadow.camera.top = 500; key.shadow.camera.bottom = -500;
      key.shadow.camera.near = 1; key.shadow.camera.far = 1400;
      key.shadow.bias = -.0005; key.shadow.normalBias = .8;
      scene.add(key);
      const rim = new THREE.DirectionalLight('#8bddff',2.5); rim.position.set(220,200,280); scene.add(rim);
      const fill = new THREE.DirectionalLight('#ffffff',1.4); fill.position.set(180,-300,120);scene.add(fill);
      floor = new THREE.Mesh(new THREE.PlaneGeometry(4000,4000),new THREE.MeshStandardMaterial({color:'#18232d',roughness:.94,metalness:.05}));
      floor.position.z = -1.5; floor.receiveShadow = true; scene.add(floor);
      grid = new THREE.GridHelper(1600,80,'#677d85','#34434d');grid.rotation.x = Math.PI/2;grid.position.z = -1.3;
      grid.material.transparent = true; grid.material.opacity = .36; scene.add(grid);
      dimensions = new THREE.Group(); scene.add(dimensions);
      selectionBox = new THREE.Box3Helper(new THREE.Box3(), '#f6bb78');selectionBox.material.depthTest = false;scene.add(selectionBox);
      createParts(); state.ready = true; state.drawn = 0;
      stage.classList.add('ready'); quality(); setLayout(state.layout); select(state.selected); cameraPreset('iso');
      const context = renderer.getContext();
      $('gpu-status').textContent = renderer.capabilities.isWebGL2 ? 'WebGL 2 active' : 'WebGL active';
      $('gpu-status').title = 'Browser graphics renderer · high-performance GPU preference requested';
      const debug = context.getExtension('WEBGL_debug_renderer_info');
      if (debug) $('gpu-status').title = context.getParameter(debug.UNMASKED_RENDERER_WEBGL);
      draw();
    } catch (error) { fail(error); }
  }
  canvas.addEventListener('webglcontextlost', e => {e.preventDefault();fail(Error('Graphics context lost'));});
  canvas.addEventListener('webglcontextrestored', () => start());
  $('retry').addEventListener('click', start);
  document.querySelectorAll('[data-layout]').forEach(b => b.addEventListener('click', () => {setLayout(b.dataset.layout);fit();}));
  document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => cameraPreset(b.dataset.view)));
  $('explode').addEventListener('input', () => {setLayout(+$('explode').value ? 'exploded' : 'assembly');});
  for (const id of ['edges','ghost','render-mode','cut','cut-axis']) $(id).addEventListener(id === 'cut' ? 'input' : 'change', applyAppearance);
  $('hardware').addEventListener('change', () => {updateVisibility();applyAppearance();});
  $('optional').addEventListener('change', () => {setLayout(state.layout);});
  for (const id of ['grid','labels']) $(id).addEventListener('change', request);
  $('dimensions').addEventListener('change', () => {updateDimensions();request();});
  $('rotate').addEventListener('change', () => {if(orbit) {orbit.autoRotate=$('rotate').checked;request();}});
  $('quality').addEventListener('change', quality);
  $('isolate').addEventListener('click', () => {
    const chosen = state.parts.find(p => p.id === state.selected);
    if (!chosen) return;
    if (chosen.optional) $('optional').checked = true;
    if (chosen.kind === 'reference') $('hardware').checked = true;
    state.hidden = new Set(state.parts.filter(p => p.id !== chosen.id).map(p => p.id));
    setLayout(chosen.kind === 'reference' && state.layout === 'print' ? 'assembly' : state.layout);fit(true);
  });
  $('show-all').addEventListener('click', () => {state.hidden.clear();updateVisibility();applyAppearance();fit();});
  $('focus').addEventListener('click', () => fit(true));
  $('clear-selection').addEventListener('click', () => select(null));
  $('download-part').addEventListener('click', () => {
    const p = state.parts.find(p => p.id === state.selected);
    if (p && p.kind === 'printed') download(new Blob([p.bytes], {type:'model/stl'}),p.id+'.stl');
  });
  $('fit').addEventListener('click', () => fit());
  function reset() {
    state.hidden.clear();state.selected = null;$('selection').hidden = true;
    for(const [id,value] of Object.entries({ghost:false,hardware:true,optional:false,edges:true,dimensions:false,labels:false,rotate:false,grid:true})) $(id).checked=value;
    $('render-mode').value='studio';$('cut').value=100;$('explode').value=0;
    if(orbit) orbit.autoRotate=false;
    setLayout('assembly');select(null);cameraPreset('iso');
  }
  $('reset').addEventListener('click',reset);
  for (const [id,factor] of [['zoom-in',.8],['zoom-out',1.25]]) $(id).addEventListener('click', () => {
    if(!state.ready)return;
    const offset=camera.position.clone().sub(orbit.target).multiplyScalar(factor);
    offset.setLength(THREE.MathUtils.clamp(offset.length(),orbit.minDistance,orbit.maxDistance));
    camera.position.copy(orbit.target).add(offset);orbit.update();request();
  });
  $('snapshot').addEventListener('click', () => {
    if(!state.ready)return;
    try {renderer.render(scene,camera);canvas.toBlob(blob => {if(blob)download(blob,'KITTY-V7-'+state.layout+'.png');},'image/png');}
    catch(error){fail(error);}
  });
  $('fullscreen').addEventListener('click', async () => {
    try {if(document.fullscreenElement)await document.exitFullscreen();else if(stage.requestFullscreen)await stage.requestFullscreen();}
    catch(error){$('fullscreen').title='Fullscreen unavailable in this browser; open the downloaded file in a full tab.';}
  });
  canvas.addEventListener('pointerdown', e => {pointerDown={x:e.clientX,y:e.clientY,button:e.button};canvas.focus();});
  canvas.addEventListener('pointerup', e => {
    if(!state.ready || !pointerDown || pointerDown.button !== 0 || Math.hypot(e.clientX-pointerDown.x,e.clientY-pointerDown.y)>5)return;
    const rect=canvas.getBoundingClientRect(), ray=new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2((e.clientX-rect.left)/rect.width*2-1,1-(e.clientY-rect.top)/rect.height*2),camera);
    const hit=ray.intersectObjects(visibleParts().map(p => p.mesh),false).find(h => !state.clipping || state.clipping.distanceToPoint(h.point)>=0);
    select(hit ? hit.object.name : null);pointerDown=null;
  });
  canvas.addEventListener('dblclick', () => fit(true));
  canvas.addEventListener('keydown', e => {
    const key=e.key.toLowerCase();
    if(key==='f'){e.preventDefault();fit();}
    else if(key==='w'){e.preventDefault();$('render-mode').value=$('render-mode').value==='wire'?'studio':'wire';applyAppearance();}
    else if(key==='r'||key==='home'){e.preventDefault();reset();}
    else if(['arrowleft','arrowright','arrowup','arrowdown'].includes(key)&&state.ready){
      e.preventDefault();const offset=camera.position.clone().sub(orbit.target);
      if(key==='arrowleft'||key==='arrowright')offset.applyAxisAngle(vector([0,0,1]),key==='arrowleft'?.12:-.12);
      else offset.applyAxisAngle(new THREE.Vector3().crossVectors(offset,camera.up).normalize(),key==='arrowup'?.12:-.12);
      camera.position.copy(orbit.target).add(offset);orbit.update();request();
    }
  });
  window.addEventListener('resize',resize);
  document.addEventListener('fullscreenchange',resize);
  document.addEventListener('visibilitychange',() => {if(document.hidden){cancelAnimationFrame(state.raf);state.raf=0;}else request();});
  new ResizeObserver(resize).observe(stage);
  // Small read-only diagnostics for real browser verification; no remote requests.
  window.kittyViewer = {info:() => ({ready:state.ready,layout:state.layout,selected:state.selected,
    visible:visibleParts().map(p=>p.id),drawn:state.drawn,triangles:state.parts.reduce((n,p)=>n+p.local.attributes.position.count/3,0),
    camera:camera ? camera.position.toArray():null,renderer:renderer ? renderer.getContext().getParameter(renderer.getContext().VERSION):null})};
  setTimeout(start,30);
})();
