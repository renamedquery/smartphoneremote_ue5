var video = document.querySelector("#videoElement");
var _commandButton = v = document.getElementById('webcamCommand');

//Video web socket
var ws;


var _intervalHandle;

// check for getUserMedia support
navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia || navigator.oGetUserMedia;

if (navigator.getUserMedia) {
    // get webcam feed if available
    navigator.getUserMedia({video: true}, handleVideo, videoError);
}

function dataURItoBlob(dataURI) {
    var binary = atob(dataURI.split(',')[1]);
    var array = [];
    for(var i = 0; i < binary.length; i++) {
        array.push(binary.charCodeAt(i));
    }
    return new Blob([new Uint8Array(array)], {type: 'image/jpeg'});
}

function handleVideo(stream) {
    // if found attach feed to video element
    video.srcObject = stream;
}


function videoError(e) {
    // no webcam found - do something
}
var v,canvas,context,w,h;

document.addEventListener('DOMContentLoaded', function(){
    // when DOM loaded, get canvas 2D context and store width and height of element
    v = document.getElementById('videoElement');
    canvas = document.getElementById('canvas');
    context = canvas.getContext('2d');
    // hide the canvas
    canvas.style.display="none";
    canvas.height = 480;
    canvas.width = 640;
},false);

function draw(v,c) {


    if(v.paused || v.ended) return false; // if no video, exit here
    context.drawImage(v,0,0,v.videoWidth,v.videoHeight); // draw video feed to canvas

   canvas.toBlob(function(blob){
       ws.send(blob);
    }, 'image/jpeg', 0.90);


}

document.getElementById('webcamCommand').addEventListener('click',function(e){
  if(_commandButton.value == "Start")
  {

    ws = new WebSocket("ws://"+document.URL.toString().split('/')[2]+"/ws");
    ws.binaryType = 'arraybuffer';
    ws.onopen = function () {
              console.log("Openened connection to websocket");
              ws.send("start_slam");
    }
    ws.onmessage = function(e){
     var server_message = e.data;
     console.log(server_message);

     if(server_message == "slam_ready"){
       _intervalHandle = setInterval(function(){
           draw(v,context,w,h);
         },30);
     }
   }
      _commandButton.value="Stop";
    }
    else if(_commandButton.value == "Stop")
    {
      ws.send("stop_slam");
      clearInterval(_intervalHandle);

      ws.close();
      _commandButton.value="Start";
    }
});
