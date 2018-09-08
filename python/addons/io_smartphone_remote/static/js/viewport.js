var container, stats, controls;
var camera, scene, renderer, light;
var isInit = false;

function main(){
  if (!Detector.webgl) Detector.addGetWebGLMessage();
    init();
  animate();
}
function init() {

  container = document.createElement('div');

  document.body.appendChild(container);
  camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.25, 20);
  camera.position.set(-1.8, 0.9, 2.7);
  // window.addEventListener('contextmenu',function(e){e.preventDefault();})


  // envmap
  var path = './textures/bridge/';
  var format = '.jpg';
  var envMap = new THREE.CubeTextureLoader().load([
    path + 'posx' + format, path + 'negx' + format,
    path + 'posy' + format, path + 'negy' + format,
    path + 'posz' + format, path + 'negz' + format
  ]);
  scene = new THREE.Scene();

  //light
  hemiLight = new THREE.HemisphereLight( 0xffffff, 0xffffff, 0.6 );
	hemiLight.color.setHSL( 0.6, 1, 0.6 );
	hemiLight.groundColor.setHSL( 0.095, 1, 0.75 );
	hemiLight.position.set( 0, 50, 0 );
	scene.add( hemiLight );
  scene.background = new THREE.Color( 0x222222 );

  //Helpers
  scene.add( new THREE.GridHelper( 20, 40, 0x111111, 0x111111 ) );

  // model
  var loader = new THREE.GLTFLoader();
  loader.load('./cache/cube.gltf', function(gltf) {
    gltf.scene.traverse(function(child) {
      if (child.isMesh) {
         child.material.envMap = envMap;
       }
    });
    scene.add(gltf.scene);
  }, undefined, function(e) {
    console.error(e);
  });
   container = document.getElementById( "viewportCanvas" );
  renderer = new THREE.WebGLRenderer({
    canvas: container//, alpha: true
  });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.gammaOutput = true;
  controls = new THREE.OrbitControls(camera, renderer.domElement);
  // controls.target.set(0, -0.2, -0.2);
  // controls.update();

  window.addEventListener('resize', onWindowResize, false);
  // stats
  stats = new Stats();
  container.appendChild(stats.dom);
  // Loading the extension
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}
//
function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
  stats.update();
}
