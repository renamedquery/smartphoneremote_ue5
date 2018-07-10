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

  remove() {}

  pause() {}
}

class Action {
  constructor(name, size, icon, websocket) {
    this.name = name;
    this.size = size;
    this.icon = icon;
    this.ws = websocket;
    this.daemon = null;
    this.status = _status_enum.NULL;


    //Setup action GUI
    document.getElementById('_actions_list').innerHTML +=
    " <div id = \'"+this.name+"\' data-role=\'tile\' data-size=\'"+this.size+"\' style=\'background-color:#585B5D;\' class=\' fg-white\'> \n" +
    "<span id=\'"+this.name+"_icon\' class = \'"+this.icon+ " icon\'></span></div>"


    this.status = _status_enum.IDLE;
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
  }
  play() {
    console.log('Play on ' + this.name + ' action');
  }
  stop() {}
  delete() {}
}

class Tracking extends Action {
  constructor(name, size, icon, websocket, sensor) {
    super(name, size, icon, websocket);
    this.sensor = sensor;
    this.sensor.init();

  }

  play() {
     var t = this.sensor.get_data();
    // document.getElementById().innerHTML = (t.alpha +' - '+t.beta +' - '+t.gamma +this.sensor.enabled);
    // this.daemon = setInterval(function(){
    //   var t = this.sensor.get_data();
    //
    //
    // }.bind(this),16.67);
      document.getElementById(this.name+"_icon").className = "mif-stop icon";
      console.log(this.name+"_icon");
  }

  stop(){

  }

}
