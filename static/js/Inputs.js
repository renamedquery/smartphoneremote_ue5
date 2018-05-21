var _ws_command;
var _ws_cameraStream; //Video stream
var _videoStreamHandle;
var video;
var v, canvas, context, w, h;
var _commandButton;

function initRemote() {
  _ws_command = new WebSocket("ws://" + document.URL.toString().split('/')[2].split(':')[0] + ":5678/command");

  setInterval(function() {
    var displayed_status = "None";
    var displayed_status_color = 'White';

    switch (_ws_command.readyState) {
      case 0:
        displayed_status = "connecting";
        break;
      case 1:
        displayed_status = "connected";
        break;
      case 2:
        displayed_status = "closing";
        break;
      case 3:
        displayed_status = "closed";
        break;
      default:
        displayed_status = "none";
    }

    document.getElementById('server_status').innerHTML = displayed_status;
  }, 5000);

  //Video elements init
  v = document.getElementById('videoElement');
  canvas = document.getElementById('canvas');
  context = canvas.getContext('2d');
  // hide the canvas
  canvas.style.display = "none";

  _commandButton =  document.getElementById('webcamCommand');
   document.getElementById('webcamCommand').addEventListener('click', function(e) {

     if (_commandButton.value == "Init") {
       initCameraFeed();
       _commandButton.value = "Start";
     }
     else if (_commandButton.value == "Start") {

       ws_cameraStream = new WebSocket("ws://" + document.URL.toString().split('/')[2].split(':')[0] + ":6302/ws");
       ws_cameraStream.binaryType = 'arraybuffer';
       ws_cameraStream.onopen = function() {
         console.log("Openened connection to websocket");
         ws_cameraStream.send("start_slam");
       }
       ws_cameraStream.onmessage = function(e) {
         var server_message = e.data;
         console.log(server_message);

         if (server_message == "slam_ready") {
           canvas.height = v.videoHeight;
           canvas.width = v.videoWidth;

           _intervalHandle = setInterval(function() {
             RenderFrame(v, context, w, h);
           }, 60);
         }
       }
       _commandButton.value = "Stop";
     } else if (_commandButton.value == "Stop") {
       ws_cameraStream.send("stop_slam");
       clearInterval(_intervalHandle);

       ws_cameraStream.close();
       _commandButton.value = "Start";
     }
   });


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
