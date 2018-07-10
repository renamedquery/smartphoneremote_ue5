console.log('Sensors Components Library');

var _status_enum ={"NULL":1,"PLAYING":2,"STOPPED":3,"ERROR":4,"IDLE":5};

function degToRad(deg) // Degree-to-Radian conversion
{
  return deg * Math.PI / 180;
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
  constructor() {
    super();
  }
  init() {

  }
}

class Imu extends Sensor {
  constructor(relative, enabled) {
    super();
    this.relative = relative;

    //IMU values
    this.deviceOrientationData = {
      alpha: 0,
      beta: 0,
      gamma: 0
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
    processGyro(event){
    this.deviceOrientationData = event;
  }

  remove() {
    window.removeEventListener("deviceorientation", function() {
      this.processGyro(event);
    }.bind(this), true);
  }

  pause() {}
}

class Action {
  constructor(name, size, icon, client) {
    this.name = name;
    this.size = size;
    this.icon = icon;
    this.client = client;
    this.daemon = null;
    this.status = _status_enum.NULL;

    //Setup data sender
    this.websocket = new WebSocket("ws://"+this.client+"/"+this.name);

    //Setup action GUI
    document.getElementById('_actions_list').innerHTML +=
    " <div id = \'"+this.name+"\' data-role=\'tile\' data-size=\'"+this.size+"\'  class=\'bg-darkSteel fg-white\'> \n" +
    "<span id=\'"+this.name+"_icon\' class = \'"+this.icon+ " icon\'></span></div>"


    document.getElementById(this.name).addEventListener("mousedown", function(){this.mousedown();}.bind(this));
    this.status = _status_enum.IDLE;
  }
  mousedown(){
    var newTileIcon;
    var newTileColor;

    if(this.status == _status_enum.NULL){
        console.log('Error on ' + this.name+ " init");
    }
    else if (this.status == _status_enum.IDLE || this.status == _status_enum.STOPPED) {
      newTileColor = "tile-large bg-orange";
      newTileIcon = "mif-stop icon";
      this.play();
    }
    else if (this.status == _status_enum.PLAYING) {
      newTileColor = "tile-large bg-darkSteel";
      newTileIcon = "mif-play icon";
      this.stop();
    }
    else if (this.status == _status_enum.ERROR) {
      console.log('Error on ' + this.name);
    }
    document.getElementById(this.name).className = newTileColor;
    document.getElementById(this.name+"_icon").className = newTileIcon;
  }
  play() {

  }
  stop() {

  }
  delete() {}
}

class Tracking extends Action {
  constructor(name, size, icon, websocket, sensor) {
    super(name, size, icon, websocket);
    this.sensor = sensor;
    this.sensor.init();

  }

  play() {
    // document.getElementById().innerHTML = (t.alpha +' - '+t.beta +' - '+t.gamma +this.sensor.enabled);
    if(this.websocket.readyState == 1){
      this.daemon = setInterval(function(){
        var t = this.sensor.get_data();

        this.websocket.send(degToRad(t.alpha)+
        '/'+degToRad(t.beta)+
        '/'+degToRad(t.gamma));
      }.bind(this),16.67);

      this.status = _status_enum.PLAYING;
    }
    else{
      this.status = _status_enum.ERROR;
    }



  }

  stop(){
      clearInterval(this.daemon);
      var t = this.sensor.remove();
      this.status = _status_enum.IDLE;
  }

}
