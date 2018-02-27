var video = document.querySelector("#videoElement");
var ws = new WebSocket("ws://127.0.0.1:9090/ws");
ws.binaryType = 'arraybuffer';
ws.onopen = function () {
          console.log("Openened connection to websocket");
}
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
},false);

function draw(v,c) {
    canvas.width = v.videoWidth;
    canvas.height = v.videoHeight;

    // hide the canvas
    //canvas.style.display="none";

    if(v.paused || v.ended) return false; // if no video, exit here
    context.drawImage(v,0,0,v.videoWidth,v.videoHeight); // draw video feed to canvas
   //
   // var uri = canvas.toDataURL("image/jpg"); // convert canvas to data URI
   // var blob = dataURItoBlob(uri);
   // ws.send(blob);
   //  console.log(blob);
   //
   canvas.toBlob(function(blob){

       console.log(blob);
       ws.send(blob);
           var myReader = new FileReader();
       myReader.onload = function(event){
           console.log(JSON.stringify(myReader.result));
       };
       myReader.readAsText(blob);
    }, 'image/jpeg', 0.95);


}

document.getElementById('save').addEventListener('click',function(e){

    draw(v,context,w,h); // when save button is clicked, draw video feed to canvas

});
