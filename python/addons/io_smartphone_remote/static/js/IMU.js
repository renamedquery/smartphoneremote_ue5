var _deviceOrientationData ={alpha:0,beta:0,gamma:0};
var _DeltaDeviceOrientationData={alpha:0,beta:0,gamma:0};//init with 0 as defaults
var _deviceMotionData ={x:0,y:0,z:0};//init with 0 as defaults
var _debug = false;
var _ws_sensors = new WebSocket("ws://192.168.0.10:5678/sensors");
var _ws_commands = new WebSocket("ws://192.168.0.10:5678/commands");
var _ws_interval;
var _status_enum ={"IDLE":1,"WORKING":2,"ERROR":3};
var _action_status = _status_enum.IDLE;
var _rotation_mode_enum={"ABSOLUTE":1,"RELATIVE":2};
var _rotation_mode = _rotation_mode_enum.ABSOLUTE;
var _base_color = document.getElementById("action_rotate").style.backgroundColor;

function stream_rotation(){
    document.getElementById("action_rotate").innerHTML = "LAUNCHING ROTATION..";
    if(_ws_sensors.readyState == 1)
    {
      if(_action_status == _status_enum.IDLE){
        _ws_commands.send('init_rotation/'+degToRad(_deviceOrientationData.alpha)+
        '/'+degToRad(_deviceOrientationData.beta)+
        '/'+degToRad(_deviceOrientationData.gamma));

        _ws_interval = setInterval(function(){
            if(_rotation_mode= _rotation_mode_enum.ABSOLUTE){
            _ws_sensors.send(degToRad(_deviceOrientationData.alpha)+
            '/'+degToRad(_deviceOrientationData.beta)+
            '/'+degToRad(_deviceOrientationData.gamma)+
            '/'+_deviceMotionData.x+
            '/'+_deviceMotionData.y+
            '/'+_deviceMotionData.z);
            }
            else if (_rotation_mode= _rotation_mode_enum.RELATIVE) {

              _ws_sensors.send(degToRad(_deviceOrientationData.alpha + _OldDeviceOrientationData.alpha)+
              '/'+degToRad(_deviceOrientationData.beta + _OldDeviceOrientationData.beta)+
              '/'+degToRad(_deviceOrientationData.gamma + _OldDeviceOrientationData.gamma)+
              '/'+_deviceMotionData.x+
              '/'+_deviceMotionData.y+
              '/'+_deviceMotionData.z);

                _OldDeviceOrientationData = _deviceOrientationData;
            }
          },16.67);

        _action_status = _status_enum.WORKING;

        document.getElementById("action_rotate").innerHTML = "ROTATING";
        document.getElementById("action_rotate").style.backgroundColor = "green";
      }
      else if (_action_status == _status_enum.WORKING) {
        clearInterval(_ws_interval);
        _action_status = _status_enum.IDLE;

        document.getElementById("action_rotate").innerHTML = "ROTATION";
        document.getElementById("action_rotate").style.backgroundColor = _base_color;
      }
    }

}

document.getElementById("action_rotate").addEventListener("click", stream_rotation);

//WEBSOCKET managment
if(!window.WebSocket)
    throw "Impossible d'utiliser WebSocket. Votre navigateur ne connait pas cette classe.";




//WebsocketInit

_ws_sensors.binaryType = 'arraybuffer';


if (window.DeviceOrientationEvent) {//
    window.addEventListener("deviceorientation", function () {//gyro
        processGyro(event.alpha, event.beta, event.gamma);
    }, true);
}
if (window.DeviceMotionEvent) {
   window.addEventListener('devicemotion', function () {
       processMotion(event.acceleration.x , event.acceleration.y,event.acceleration.y);
   }, true);
}

function processGyro(alpha,beta,gamma)
{


	_deviceOrientationData.alpha=alpha;
	_deviceOrientationData.beta=beta;
	_deviceOrientationData.gamma=gamma;
	//note: this code is much simpler but less obvious: function processGyro(event){_deviceOrientationData = event;}
}
function processMotion(x,y,z)
{
	_deviceMotionData.x=x;
	_deviceMotionData.y=y;
	_deviceMotionData.z=z;
	//note: this code is much simpler but less obvious: function processGyro(event){_deviceOrientationData = event;}
}

var canvas = document.getElementById('gyrosCanvas');
var context = canvas.getContext('2d');
// context.canvas.width  = window.innerWidth/3;//resize canvas to whatever window dimensions are
// context.canvas.height = window.innerHeight/4;
context.font = "5px Arial";
context.translate(context.canvas.width / 2, context.canvas.height / 2); //put 0,0,0 origin at center of screen instead of upper left corner

function degToRad(deg)// Degree-to-Radian conversion
{
	 return deg * Math.PI / 180;
}

function makeRect(width,height,depth)//returns a 3D box like object centered around the origin. There are more than 8 points for this cube as it is being made by chaining together a strip of triangles so points are redundant at least 3x. Confusing for now (sorry) but this odd structure comes in handy later for transitioning into webgl
{
	var newObj={};
	var hw=width/2;
	var hh=height/2;
	var hd=depth/2;
	newObj.vertices=[  [-hw,hh,hd],[hw,hh,hd],[hw,-hh,hd],//first triangle
					  [-hw,hh,hd],[-hw,-hh,hd],[hw,-hh,hd],//2 triangles make front side
					  [-hw,hh,-hd],[-hw,hh,hd],[-hw,-hh,-hd], //left side
					  [-hw,hh,hd],[-hw,-hh,hd],[-hw,-hh,-hd],
					  [hw,hh,-hd],[hw,hh,hd],[hw,-hh,-hd], //right side
					  [hw,hh,hd],[hw,-hh,hd],[hw,-hh,-hd],
					  [-hw,hh,-hd],[hw,hh,-hd],[hw,-hh,-hd],//back
					  [-hw,hh,-hd],[-hw,-hh,-hd],[hw,-hh,-hd],
					  [-hw,hh,-hd],[hw,hh,-hd],[hw,hh,hd],//top
					  [-hw,hh,-hd],[-hw,hh,hd],[hw,hh,hd],
					  [-hw,-hh,-hd],[hw,-hh,-hd],[hw,-hh,hd],//bottom
					  [-hw,-hh,-hd],[-hw,-hh,hd],[hw,-hh,hd]
	];

	return newObj;
}

var xAxis=makeRect(100,1,1);
xAxis.color=" #d3ff71";
var yAxis=makeRect(1,100,1);
yAxis.color="#df9d59";
var zAxis=makeRect(1,1,100);
zAxis.color="#14649f";

//render loop
function renderLoop()
{
  if(!( window.DeviceOrientationEvent && 'ontouchstart' in window))
  {
    requestAnimationFrame( renderLoop );
    context.font = "5px Arial";
    context.fillText("NO SENSOR DETECTED ",0,0 );
  }
  else{
    requestAnimationFrame( renderLoop );//better than set interval as it pauses when browser isn't active
    context.clearRect( -canvas.width/2, -canvas.height/2, canvas.width, canvas.height);//clear screen x, y, width, height

    if(_debug){
      context.fillText("alpha: " + _deviceOrientationData.alpha,-canvas.width/2.2,-canvas.height/2.65);
      context.fillText("beta: " +_deviceOrientationData.beta,-canvas.width/2.2,-canvas.height/2.8);
      context.fillText("gamma: " +_deviceOrientationData.gamma,-canvas.width/2.2,-canvas.height/2.95);

      context.fillText("x: " + _deviceMotionData.x,-canvas.width/2.2,-canvas.height/2.2);
      context.fillText("y: " +_deviceMotionData.y,-canvas.width/2.2,-canvas.height/2.35);
      context.fillText("z: " +_deviceMotionData.z,-canvas.width/2.2,-canvas.height/2.5);
    }

    renderObj(xAxis);
    renderObj(yAxis);
    renderObj(zAxis);
  }


}
renderLoop();

function renderObj(obj)//renders an object as a series of triangles
{
	var rotatedObj=rotateObject(obj);
	context.lineWidth = 4;
	context.strokeStyle = obj.color;

	for(var i=0 ; i<obj.vertices.length ; i+=3)
	{
		for (var k=0;k<3;k++)
		{
		  var vertexFrom=rotatedObj.vertices[i+k];
		  var temp=i+k+1;
		  if(k==2)
			  temp=i;

		  var vertexTo=rotatedObj.vertices[temp];
		  context.beginPath();
		  context.moveTo(scaleByZ(vertexFrom[0],vertexFrom[2]), -scaleByZ(vertexFrom[1],vertexFrom[2]));
		  context.lineTo(scaleByZ(vertexTo[0],vertexTo[2]), -scaleByZ(vertexTo[1],vertexTo[2]));
		  context.stroke();
		}
	}
}

function scaleByZ(val,z)
{
	var focalLength=900; //pick any value that looks good
	var scale= focalLength/((-z)+focalLength);
	return val*scale;
}

function rotateObject(obj) //rotates obeject
{
	var newObj={};
	newObj.vertices=[];
	for(var i=0 ; i<obj.vertices.length ; i++)
	{
	  newObj.vertices.push(rotatePointViaGyroEulars(obj.vertices[i]));
	}
	return newObj;
}

function rotatePointViaGyroEulars(ra) //rotates 3d point based on eular angles
{
	var oldX=ra[0];
	var oldY=ra[1];
	var oldZ=ra[2];

	//order here is important - it must match the processing order of the device

	//rotate about z axis
	var newX = oldX * Math.cos(-degToRad(_deviceOrientationData.alpha)) - oldY * Math.sin(-degToRad(_deviceOrientationData.alpha));
	var newY = oldY * Math.cos(-degToRad(_deviceOrientationData.alpha)) + oldX * Math.sin(-degToRad(_deviceOrientationData.alpha));

	//rotate about x axis
	oldY=newY;
	newY = oldY * Math.cos(-degToRad(_deviceOrientationData.beta)) - oldZ * Math.sin(-degToRad(_deviceOrientationData.beta));
	var newZ = oldZ * Math.cos(-degToRad(_deviceOrientationData.beta)) + oldY * Math.sin(-degToRad(_deviceOrientationData.beta));


	//rotate about y axis
	oldZ=newZ;
	oldX=newX;

	newZ = oldZ * Math.cos(-degToRad(_deviceOrientationData.gamma)) - oldX * Math.sin(-degToRad(_deviceOrientationData.gamma));
	newX = oldX * Math.cos(-degToRad(_deviceOrientationData.gamma)) + oldZ * Math.sin(-degToRad(_deviceOrientationData.gamma));


	return [newX,newY,newZ];
}
