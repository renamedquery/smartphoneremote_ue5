var _ws_command;
var _ws_cameraStream; //Video stream
var _videoStreamHandle;
var video;
var v, canvas, context, w, h;
var _commandButton;



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
  var connectionActivity = Metro.activity.open({
    type: 'cycle',
    // style: 'light',
    overlayColor: '#585B5D',
    // text: '<div class=\'mt-2 text-small\'>connecting to server</div>',
    overlayAlpha: 1
  });

  _ws_command = new WebSocket("ws://" + document.URL.toString().split('/')[2].split(':')[0] + ":5678/command");

  setInterval(function() {
    var displayed_status = "None";
    var displayed_status_color = "fg-light";

    switch (_ws_command.readyState) {
      case 0:
        displayed_status = "connecting";
        displayed_status_color = "fg-orange";
        break;
      case 1:
        displayed_status = "connected";
        Metro.activity.close(connectionActivity);
        displayed_status_color = "fg-green";

        break;
      case 2:
        displayed_status = "closing";
        displayed_status_color = "fg-orange";
        break;
      case 3:
        displayed_status = "closed";
        displayed_status_color = "fg-grey";
        break;
      default:
        displayed_status = "none";
    }

    document.getElementById('connexion_status').className = "mif-wifi-connect mif-3x "+ displayed_status_color;
  }, 5000);

  document.getElementById('fullscreenCommand').addEventListener('click', function(e) {
    setFullscreen();
  });

  document.getElementById('viewSwitchCommand').addEventListener('click', function(e) {
    setView();
  });


  //Video elements init
  v = document.getElementById('videoElement');
  canvas = document.getElementById('canvas');
  context = canvas.getContext('2d');
  // hide the canvas
  canvas.style.display = "none";

  _commandButton = document.getElementById('trackingTile');
  document.getElementById('trackingTile').addEventListener('click', function(e) {

    
    // if (_commandButton.value == "Init") {
    //   initCameraFeed();
    //   _commandButton.value = "Start";
    // } else if (_commandButton.value == "Start") {
    //
    //   ws_cameraStream = new WebSocket("ws://" + document.URL.toString().split('/')[2].split(':')[0] + ":6302/ws");
    //   ws_cameraStream.binaryType = 'arraybuffer';
    //   ws_cameraStream.onopen = function() {
    //     console.log("Openened connection to websocket");
    //     ws_cameraStream.send("start_slam");
    //   }
    //   ws_cameraStream.onmessage = function(e) {
    //     var server_message = e.data;
    //     console.log(server_message);
    //
    //     if (server_message == "slam_ready") {
    //       canvas.height = v.videoHeight;
    //       canvas.width = v.videoWidth;
    //
    //       _intervalHandle = setInterval(function() {
    //         RenderFrame(v, context, w, h);
    //       }, 60);
    //     }
    //   }
    //   _commandButton.value = "Stop";
    // } else if (_commandButton.value == "Stop") {
    //   ws_cameraStream.send("stop_slam");
    //   clearInterval(_intervalHandle);
    //
    //   ws_cameraStream.close();
    //   _commandButton.value = "Start";
    // }
  });


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

function tracking(){

}

function setView(){
  var displayed_status_icon = "mif-equalizer";
  action_view = $('#_action_window').data('collapse');
  tools_view = $('#_tool_window').data('collapse');
  var collapsed = action_view.isCollapsed();

  if(collapsed){
    action_view.expand();
    tools_view.collapse();


    displayed_status_icon = "mif-equalizer";
  }
  else{
    tools_view.expand();



    displayed_status_icon = "mif-dashboard";
    action_view.collapse();
  }

    document.getElementById('viewSwitchCommandIcon').className = "mif-3x "+ displayed_status_icon ;
}

function initCameraFeed() {
  video = document.querySelector("#videoElement");
  // check for getUserMedia support
  navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia || navigator.oGetUserMedia;

  if (navigator.getUserMedia) {
    // get webcam feed if available
    navigator.getUserMedia({
      audio: false,
      video: {
        width: 640,
        height: 480
      }
    }, handleVideo, videoError);
  }


}

function handleVideo(stream) {
  // if found attach feed to video element
  video.srcObject = stream;
}

function videoError(e) {
  // no webcam found - do something
}

function RenderFrame(v, c) {
  if (v.paused || v.ended) return false; // if no video, exit here
  context.drawImage(v, 0, 0, v.videoWidth, v.videoHeight); // RenderFrame video feed to canvas
  canvas.toBlob(function(blob) {
    ws_cameraStream.send(blob);
    ws_cameraStream.send('t' + v.currentTime);
  }, 'image/jpeg', 1);
}
