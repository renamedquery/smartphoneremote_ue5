function degToRad(deg)// Degree-to-Radian conversion
{
	 return deg * Math.PI / 180;
}

class Action {
  constructor(name, icon, websocket) {
    self.name = name;
    self.icon = icon;
    self.ws = websocket;
  }
}

class Sensor {
  constructor() {
    self.supported = false;
  }
  init(){}
  get_data(){}
  pause(){}
  remove()

}

class Camera extends Sensor {
  constructor() {
    super();
  }
  init(){

  }
}

class Imu extends Sensor {
  constructor(relative, enabled) {
    super();
    self.relative = relative;
    self.enabled = true;

    //IMU values
    self.deviceOrientationData ={alpha:0,beta:0,gamma:0};
    self.deltaDeviceOrientationData={alpha:0,beta:0,gamma:0};//init with 0 as defaults
    self.deviceMotionData ={x:0,y:0,z:0};//init with 0 as defaults
  }
  init(){
    if (window.DeviceOrientationEvent) {
      self.supported = true;
    }
    else {
      console.log('Device IMU not supported');
    }
  }
  get_data(){
    if(self.supported){
      window.addEventListener("deviceorientation", function() {
        self.processGyro(event.alpha, event.beta, event.gamma);
      }, true);

      console.log(self.deviceOrientationData);
    }
  }

  function processGyro(event){deviceOrientationData = event;}

  remove(){}

  pause(){}
}
