var _ws_command;
var _ws_cameraStream; //Video stream
var _videoStreamHandle;
var video;
var v, canvas, context, w, h;
var _commandButton;
var _isCommandStreamInit;
var _actions = [];
var _client;
var _timout ;
var _connexionAttempt;

function StartuInfoBoxEvents() {
  return Metro.infobox.create(
    "<div align='center' data-role='activity' data-type='simple'></div>Connecting. Wait... ",
    "", {
      closeButton: false,
      //overlay: false,
      width: 'auto',
      overlayAlpha: 0,
      overlayColor: '#303030',
    }

  );
}

function initRemote() {


  // screen.orientation.lock('landscape');
  _client = document.URL.toString().split('/')[2].split(':')[0] + ':5678';
  _trackingUnit = document.URL.toString().split('/')[2].split(':')[0] + ':6302';
  var connectionActivity = Metro.activity.open({
    type: 'cycle',
    style: 'light',
    overlayColor: '#585B5D',
     text: '<div class=\'mt-2 text-small\'>reaching local blender instance.</div>',
    overlayAlpha: 1
  });

  _ws_command = new WebSocket("ws://" + _client + "/command");

  setInterval(function() {
    var displayed_status = "None";
    var displayed_status_color = "fg-light";

    switch (_ws_command.readyState) {
      case 0:
        displayed_status = "connecting";
        displayed_status_color = "fg-orange";
        break;
      case 1:
        if(!_isCommandStreamInit)
          Metro.activity.close(connectionActivity);

        displayed_status = "connected";
        displayed_status_color = "fg-green";

        _isCommandStreamInit = true;

        break;
      case 2:
        displayed_status = "closing";
        Metro.toast.create("Can't reach blender instance, please reload", null, null, "alert");

        _connexionAttempt++;
        displayed_status_color = "fg-red";

        break;
      case 3:
        displayed_status = "closed";
        Metro.toast.create("Can't reach blender instance, please reload", null, 5000, "alert");
        displayed_status_color = "fg-red";

        _connexionAttempt++;
        break;
      default:
        displayed_status = "none";

    }

    document.getElementById('connexion_status').className = "mif-wifi-connect mif-3x "+ displayed_status_color;
  }, 5000);

  var imu = new Imu(false,false);
  var cam = new Camera(_trackingUnit);

  _actions.push(new Tracking("tracking", "medium", "mif-play", _client,30, imu));
  _actions.push(new Tracking('camera_tracking','medium','mif-compass',_client,25,cam));

  var translate_local = "bpy.ops.transform.translate(value=(0, 0.5, 0), constraint_axis=(False, True, False), constraint_orientation='LOCAL')"
  _actions.push(new Script("test", "medium", "mif-airplane", _client,30,translate_local));

  document.getElementById('fullscreenCommand').addEventListener('click', function(e) {
    setFullscreen();
  });

  //Windows buttons
  //TODO: Clean that shit
  document.getElementById('viewSwitchSettings').addEventListener('click', function(e) {
    setView(0);
  });
  document.getElementById('viewSwitchTiles').addEventListener('click', function(e) {
    setView(1);
  });
  document.getElementById('viewSwitchScene').addEventListener('click', function(e) {
    setView(2);
  });

  setView(1);





  //Video elements init
  v = document.getElementById('videoElement');
  canvas = document.getElementById('canvas');
  context = canvas.getContext('2d');
  // hide the canvas
  // canvas.style.display = "none";


}

function createScriptAction(){
  var actionName =  document.getElementById('newScriptActionName').value;
  var actionSize =  document.getElementById('newScriptActionSize').value;
  var actionCommand =  document.getElementById('newScriptActionCommand').value;
  var actionCommand =  document.getElementById('newScriptActionFrequency').value;

  _actions.push(new Script(actionName, actionSize, "mif-file-code", _client,30,actionCommand));
}

function setFullscreen() {
  var isInFullScreen = (document.fullScreenElement && document.fullScreenElement !== null) || // alternative standard method
    (document.mozFullScreen || document.webkitIsFullScreen);

  var docElm = document.documentElement;
  if (!isInFullScreen) {

    if (docElm.requestFullscreen) {
      docElm.requestFullscreen();
    } else if (docElm.mozRequestFullScreen) {
      docElm.mozRequestFullScreen();
      //alert("Mozilla entering fullscreen!");
    } else if (docElm.webkitRequestFullScreen) {
      docElm.webkitRequestFullScreen();
      //alert("Webkit entering fullscreen!");
    }
    document.getElementById('fullscreenCommandIcon').className = "mif-3x mif-shrink2";
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.mozCancelFullScreen) {
      document.mozCancelFullScreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
    document.getElementById('fullscreenCommandIcon').className = "mif-3x mif-enlarge2";
  }
}
//
// function tracking(){
//
// }

function setView(target){

  action_view = $('#_action_window').data('collapse');
  tools_view = $('#_tool_window').data('collapse');
  scene_view = $('#_scene_window').data('collapse');

  switch (target) {
    case 0:
      action_view.collapse();
      tools_view.expand();
      scene_view.collapse();

      document.getElementById('viewSwitchSettings').className = "brand bg-dark";
      document.getElementById('viewSwitchScene').className = "brand ";
      document.getElementById('viewSwitchTiles').className = "brand ";
      break;
    case 1:
      action_view.expand();
      tools_view.collapse();
      scene_view.collapse();

      document.getElementById('viewSwitchSettings').className = "brand";
      document.getElementById('viewSwitchScene').className = "brand";
      document.getElementById('viewSwitchTiles').className = "brand  bg-dark ";
      break;
    case 2:
      action_view.collapse();
      tools_view.collapse();
      scene_view.expand();

      main();
      document.getElementById('viewSwitchSettings').className = "brand";
      document.getElementById('viewSwitchScene').className = "brand bg-dark";
      document.getElementById('viewSwitchTiles').className = "brand ";
      break;
    default:

  }
}
