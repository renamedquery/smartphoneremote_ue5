console.log('Sensors Components Library');

var _status_enum ={"NULL":1,"PLAYING":2,"STOPPED":3,"ERROR":4,"IDLE":5};

function degToRad(deg) // Degree-to-Radian conversion
{
  return deg * Math.PI / 180;
}

class Sensor {
  constructor(frequency) {
    this.supported = false;
    this.enabled = false;
  }
  init() { }
  get_data() {}
  pause() {}
  remove() {}

}

class Camera extends Sensor {
  constructor() {
    super();
  }
  init() {

  }
}

class Imu extends Sensor {
  constructor(frequency,relative, enabled) {
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
      return this.deviceOrientationData;
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
      var t = this.sensor.remove();
      this.status = _status_enum.IDLE;
    }
    this.update_skin();
  }
  delete() {}
  update_skin(){
    var newTileIcon;
    var newTileColor;

    if(this.status == _status_enum.NULL){
    }
    else if (this.status == _status_enum.IDLE || this.status == _status_enum.STOPPED) {
      newTileColor = "tile-"+this.size+" bg-darkSteel";
      newTileIcon = "mif-play icon";

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
}

class Script extends Action {
  constructor(name, size, icon,client,frequency, command) {
    super(name, size, icon, client, frequency);
    this.script = command;
  }

  // mousedown(){
  //   super.mousedown();
  //
  //   console.log('mouve over from tracking');
  // }

}
class Tracking extends Action {
  constructor(name, size, icon,client,frequency, sensor) {
    super(name, size, icon, client, frequency);
    this.sensor = sensor;
    this.sensor.init();

  }
  // mousedown(){
  //   super.mousedown();
  //
  //   console.log('mouve over from tracking');
  // }

  core() {
      var t = this.sensor.get_data();
      this.websocket.send(t.w+'/'+t.x+'/'+t.y+'/'+t.z);
  }

  // stop(){
  //   super.stop()
  //     clearInterval(this.daemon);
  //     var t = this.sensor.remove();
  //     this.status = _status_enum.IDLE;
  // }

}
