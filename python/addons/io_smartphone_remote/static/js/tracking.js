console.log('Sensors Components Library');

var _status_enum ={"NULL":1,"PLAYING":2,"STOPPED":3,"ERROR":4,"IDLE":5};

function degToRad(deg) // Degree-to-Radian conversion
{
  return deg * Math.PI / 180;
}

//function from https://stackoverflow.com/questions/4998908/convert-data-uri-to-file-then-append-to-formdata/5100158
function dataURItoBlob(dataURI) {
    // convert base64/URLEncoded data component to raw binary data held in a string
    var byteString;
    if (dataURI.split(',')[0].indexOf('base64') >= 0)
        byteString = atob(dataURI.split(',')[1]);
    else
        byteString = unescape(dataURI.split(',')[1]);

    // separate out the mime component
    var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];

    // write the bytes of the string to a typed array
    var ia = new Uint8Array(byteString.length);
    for (var i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }

    return new Blob([ia], {type:mimeString});
}


class Sensor {
  constructor() {
    this.supported = false;
    this.enabled = false;
  }
  init() { }
  get_data() {}
  pause() {}
  remove() {}

}

class Camera extends Sensor {
  constructor(computeUnite) {
    super();
    // this.video = $("#video").get()[0];
    this.canvas = document.getElementById('canvas');
    this.ctx = this.canvas.getContext('2d');
    this.video = document.querySelector('video');
    // Older browsers might not implement mediaDevices at all, so we set an empty object first
    if (navigator.mediaDevices === undefined) {
      navigator.mediaDevices = {};
    }

    this.wsComputeUnite = new WebSocket("ws://"+computeUnite+"/ws");
    this.wsComputeUnite.binaryType = 'arraybuffer';
  }
  init() {
    super.init();

    this.wsComputeUnite.send("start_slam");
    this.supported /*= navigator.getUserMedia*/ = navigator.getUserMedia ||
      navigator.webkitGetUserMedia ||
      navigator.mozGetUserMedia;

    if (  this.supported) {
      // Prefer camera resolution nearest to 1280x720.
      var constraints = {
        audio: false,
        video: {
          width: 640,
          height: 480
        }
      };
      navigator.mediaDevices.getUserMedia(constraints)
        .then(function(mediaStream) {
          // var video = document.querySelector('video');
          this.video.srcObject = mediaStream;
          this.video.onloadedmetadata = function(e) {
            this.video.play();
          }.bind(this);
        }.bind(this))
        .catch(function(err) {
          console.log(err.name + ": " + err.message);
        }); // always check for errors at the end.
    } else {
      console.log("getUserMedia not supported");
    }
  }
  get_data() {
    if(this.video){
      this.ctx.drawImage(this.video,0,0,640,480);
      this.canvas.toBlob(function(blob){
          this.wsComputeUnite.send(blob);
       }.bind(this), 'image/jpeg', 0.90);

      // this.wsComputeUnite.send(dataURItoBlob(this.canvas.get()[0].toDataURL('image/jpeg', 1.0)));
      // return(dataURItoBlob(this.canvas.get()[0].toDataURL('image/jpeg', 1.0)));
      return 1;
    }

  }
  remove(){
    // this.video.pause();
    // this.video.srcObject = null;
    // stop both video and audio
    this.video.srcObject.getTracks().forEach( (track) => {
    track.stop();
    });
  }


}

class Imu extends Sensor {
  constructor(relative, enabled) {
    super();
    this.relative = relative;

    //IMU values
    this.deviceOrientationData = {
      w: 0,
      x: 0,
      y: 0,
      z: 0
    };
    this.deltaDeviceOrientationData = {
      alpha: 0,
      beta: 0,
      gamma: 0
    }; //init with 0 as defaults
    this.deviceMotionData = {
      x: 0,
      y: 0,
      z: 0
    }; //init with 0 as defaults
  }
  init() {
    super.init();
    if (window.DeviceOrientationEvent) {
      this.supported = true;
    } else {
      console.log('Device IMU not supported');
    }
  }
  get_data() {
    if (this.supported) {

      if (!this.enabled) {
        window.addEventListener("deviceorientation", function() {
          this.processGyro(event);
        }.bind(this), true);
        this.enabled = true;
      }
      return this.deviceOrientationData.w+'/'+this.deviceOrientationData.x+'/'+this.deviceOrientationData.y+'/'+this.deviceOrientationData.z;
    } else {
      return null;
    }

  }
    processGyro(event) {
    var x = degToRad(event.beta); // beta value
    var y = degToRad(event.gamma); // gamma value
    var z = degToRad(event.alpha); // alpha value

    //precompute to save on processing time
    var cX = Math.cos(x / 2);
    var cY = Math.cos(y / 2);
    var cZ = Math.cos(z / 2);
    var sX = Math.sin(x / 2);
    var sY = Math.sin(y / 2);
    var sZ = Math.sin(z / 2);

    this.deviceOrientationData.w = cX * cY * cZ - sX * sY * sZ;
    this.deviceOrientationData.x = sX * cY * cZ - cX * sY * sZ;
    this.deviceOrientationData.y = cX * sY * cZ + sX * cY * sZ;
    this.deviceOrientationData.z = cX * cY * sZ + sX * sY * cZ;

    // this.deviceOrientationData.x
  }

  remove() {
    window.removeEventListener("deviceorientation", function() {
      this.processGyro(event);
    }.bind(this), true);
  }

  pause() {}
}

class Action {
  constructor(name, size, icon, client, frequency) {
    this.name = name;
    this.size = size;
    this.icon = icon;
    this.client = client;
    this.daemon = null;
    this.status = _status_enum.NULL;

    //TODO: Cleanup
    if(frequency > 0){
      this.frequency = 1000/frequency;
    }
    else{
      this.frequency = 0;
    }
    //Setup data sender
    this.websocket = new WebSocket("ws://"+this.client+"/"+this.name);

    //Setup action GUI
    document.getElementById('_actions_list').innerHTML +=
    " <div id = \'"+this.name+"\' data-role=\'tile\' data-size=\'"+this.size+"\'  class=\'bg-darkSteel fg-white\'> \n" +
    "<span id=\'"+this.name+"_icon\' class = \'"+this.icon+ " icon\'></span><span id=\'"+this.name+"_brand\' class=\'badge-bottom\'>"+this.status+"</span></div>"

    $(document).on('mousedown', '#'+this.name, function() {
      this.mousedown();
    }.bind(this));

    this.status = _status_enum.IDLE;

    this.update_skin();

  }
  mousedown(){
    if(this.status == _status_enum.NULL){
        console.log('Error on ' + this.name+ " init");
    }
    else if (this.status == _status_enum.IDLE || this.status == _status_enum.STOPPED) {
      this.play();
    }
    else if (this.status == _status_enum.PLAYING) {
      this.stop();
    }
    else if (this.status == _status_enum.ERROR) {
      console.log('Error on ' + this.name);
    }
      this.update_skin();
  }
  play() {
    if (this.websocket.readyState == 1) {
      if (this.frequency != 0) {
        this.daemon = setInterval(function(){this.core();}.bind(this), this.frequency);
        this.status = _status_enum.PLAYING;
        this.update_skin();
      } else {
        this.core();
        this.status = _status_enum.IDLE;
      }
    } else {
      this.status = _status_enum.ERROR;
    }

  }
  core(){
    console.log('Define action');
  }
  stop() {
    if(this.frequency != 0){
      clearInterval(this.daemon);
      this.status = _status_enum.IDLE;
    }
    this.update_skin();
  }
  delete() {}
  init_settings_pannel(){

  }
  update_skin(){
    var newTileIcon;
    var newTileColor;

    if(this.status == _status_enum.NULL){
    }
    else if (this.status == _status_enum.IDLE || this.status == _status_enum.STOPPED) {
      newTileColor = "tile-"+this.size+" bg-darkSteel";
      newTileIcon = this.icon+" icon";

    }
    else if (this.status == _status_enum.PLAYING) {
      newTileColor = "tile-"+this.size+" bg-orange";
      newTileIcon = "mif-stop icon";

    }
    else if (this.status == _status_enum.ERROR) {
      console.log('Error on ' + this.name);
    }
    document.getElementById(this.name+"_brand").innerHTML = this.status;
    document.getElementById(this.name).className = newTileColor;
    document.getElementById(this.name+"_icon").className = newTileIcon;

  }
  update_settings(){}
}

class Script extends Action {
  constructor(name, size, icon,client,frequency, command) {
    name += "_script"
    super(name, size, icon, client, frequency);
    this.script = command;
    this.init_settings_pannel();
  }
  core(){
    console.log('sending code');
    this.websocket.send(this.script);
  }

  init_settings_pannel(){
    document.getElementById('_tool_window').innerHTML += "<div class='mb-2' data-role='panel' data-title-caption='"+this.name+" settings' data-collapsed='true' data-collapsible='true'>"
         +`<div class='row'>
              <label class='cell'>Frequency</label>`
            +"  <div class='cell'>"
            +    "<input id='tracking_settings_sampling'class='flex-self-center' data-role='slider'"
           +      "data-value='"+this.frequency+"'"
           +   `   data-hint='true'
                 data-min='0' data-max='60'>
              </div>
         </div>`
        +`<div class='row'>
             <label class='cell'>Command</label></div>`
        +"  <div class='row'>    <div class='cell'> <textarea class='flex-self-center' id='newScriptActionCommand'  data-role='textarea'  >"+this.script+" </textarea></div>"
        +`</div>
        </div>`
  }

}

class Tracking extends Action {
  constructor(name, size, icon,client,frequency, sensor) {
    super(name, size, icon, client, frequency);
    this.sensor = sensor;

    this.init_settings_pannel();
  }
  play(){
    this.sensor.init();

    super.play();
  }
  core() {
      this.websocket.send(this.sensor.get_data());
  }
  stop(){
    super.stop();
    var t = this.sensor.remove();

  }
  init_settings_pannel(){
    document.getElementById('_tool_window').innerHTML += "<div data-role='panel' class='mb-2' data-title-caption='"+this.name+" settings' data-collapsed='true' data-collapsible='true'>"
        +`<div class='row '>
           <label class='cell'>Sensor</label>
           <div class='cell'>
             <select data-role='select' name='Input Feed' class='flex-self-center'>
                 <option value='imu'>IMU</option>
                 <option value='camera'>Camera</option>
             </select>
           </div>
         </div>`
        +`<div class='row'>
             <label class='cell'>Frequency</label>
             <div class='cell'>
               <input id='tracking_settings_sampling'class='flex-self-center' data-role='slider'`
          +      "data-value='"+this.frequency+"'"
          +`      data-hint='true'
                data-min='0' data-max='60'>
             </div>
        </div>
        </div>`
  }


}
