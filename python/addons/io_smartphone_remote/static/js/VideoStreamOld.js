&var video = document.querySelector("#videoElement");
var _commandButton = v = document.getElementById('webcamCommand');

//Video web socket
var ws;


var _intervalHandle;

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

var v, canvas, context, w, h;

function handleVideo(stream) {
  // if found attach feed to video element
  video.srcObject = stream;
}


function videoError(e) {
  // no webcam found - do something
}
document.addEventListener('DOMContentLoaded', function() {
  // when DOM loaded, get canvas 2D context and store width and height of element
  v = document.getElementById('videoElement');
  canvas = document.getElementById('canvas');
  context = canvas.getContext('2d');
  // hide the canvas
  canvas.style.display = "none";
}, false);

function draw(v, c) {
  if (v.paused || v.ended) return false; // if no video, exit here
  context.drawImage(v, 0, 0, v.videoWidth, v.videoHeight); // draw video feed to canvas
  canvas.toBlob(function(blob) {
    ws.send(blob);
    ws.send('t' + v.currentTime);
  }, 'image/jpeg', 1);


}

document.getElementById('webcamCommand').addEventListener('click', function(e) {
  if (_commandButton.value == "Start") {

    ws = new WebSocket("ws://" + document.URL.toString().split('/')[2] + "/ws");
    ws.binaryType = 'arraybuffer';
    ws.onopen = function() {
      console.log("Openened connection to websocket");
      ws.send("start_slam");
    }
    ws.onmessage = function(e) {
      var server_message = e.data;
      console.log(server_message);

      if (server_message == "slam_ready") {
        canvas.height = v.videoHeight;
        canvas.width = v.videoWidth;

        _intervalHandle = setInterval(function() {
          draw(v, context, w, h);
        }, 60);
      }
    }
    _commandButton.value = "Stop";
  } else if (_commandButton.value == "Stop") {
    ws.send("stop_slam");
    clearInterval(_intervalHandle);

    ws.close();
    _commandButton.value = "Start";
  }
});
