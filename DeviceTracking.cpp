#include <algorithm>
#include <chrono>
#include <fstream>
#include <iostream>
#include <stdio.h>
#include <vector>

#include "opencv2/opencv.hpp"
// #include <opencv2/core/eigen.hpp>.
#include <opencv2/core/core.hpp>
#include <Eigen/Geometry>

#include "seasocks/PrintfLogger.h"
#include "seasocks/Server.h"
#include "seasocks/StringUtil.h"
#include "seasocks/WebSocket.h"
#include "seasocks/util/Json.h"

#include <System.h>

using namespace std;
using namespace cv;
using namespace seasocks;

static Eigen::Matrix4f _SLAM;
static Eigen::Matrix4f _BLENDER;

class CommandHandler : public WebSocket::Handler {
public:
  explicit CommandHandler(Server *server)
      : _server(server), _currentValue(0) {
    setValue(1);
  }

  virtual void onConnect(WebSocket *connection) {
    _connections.insert(connection);
    connection->send(_currentSetValue.c_str());
    cout << "Connected: " << connection->getRequestUri() << " : "
         << formatAddress(connection->getRemoteAddress()) << endl;
    cout << "Credentials: " << *(connection->credentials()) << endl;
  }
  virtual void onData(WebSocket *connection, const char *data) {
      cout<<"Reveceiving command"<<endl;
  }
  virtual void onData(WebSocket *, const uint8_t *data, size_t size) {
      cout<<"Reveceiving command"<<endl;
  }

  virtual void onDisconnect(WebSocket *connection) {
    _connections.erase(connection);
    cout << "Disconnected: " << connection->getRequestUri() << " : "
         << formatAddress(connection->getRemoteAddress()) << endl;

  }

private:
  set<WebSocket *> _connections;
  Server *_server;
  int _currentValue;
  double _currentTime;
  string _currentSetValue;

  void setValue(int value) {
    _currentValue = value;
    _currentSetValue = makeExecString("set", _currentValue);
  }
};

class CameraHandler : public WebSocket::Handler {
public:
  explicit CameraHandler(Server *server, ORB_SLAM2::System *SLAMPtr)
      : _server(server), _slam(SLAMPtr), _currentValue(0) {
    setValue(1);
  }

  virtual void onConnect(WebSocket *connection) {
    _connections.insert(connection);
    connection->send(_currentSetValue.c_str());
    cout << "Connected: " << connection->getRequestUri() << " : "
         << formatAddress(connection->getRemoteAddress()) << endl;
    cout << "Credentials: " << *(connection->credentials()) << endl;
    connection->send("ping from image processor");
  }
  virtual void onData(WebSocket *connection, const char *data) {
    if (0 == strcmp("die", data)) {
      _server->terminate();
      return;
    }
    if (data[0] == 't') {
      char subbuff[5];
      memcpy(subbuff, &data[1], 4);
      _currentTime = atof(subbuff);
      return;
    }
    if (0 == strcmp("blender_instance_login", data)) {
      _blenderInstanceConnexion = connection;
      std::cout<<"blender instance registered looged"<<std::endl;
    }
    if (0 == strcmp("start_slam", data)) {
      _slam = new ORB_SLAM2::System(
          "/home/slumber/Repos/ORB_SLAM2/Vocabulary/ORBvoc.txt",
          "/home/slumber/Repos/DeviceTracking/CameraSettings.yaml",
          ORB_SLAM2::System::MONOCULAR, true);
      connection->send("slam_ready");
      return;
    }
    if (0 == strcmp("stop_slam", data)) {
      _slam->Shutdown();
      return;
    }
    if (0 == strcmp("map", data)) {
      vector<ORB_SLAM2::MapPoint*> vMPs = _slam->GetTrackedMapPoints();
      vector<cv::Mat> vPoints;
      vPoints.reserve(vMPs.size());
      vector<ORB_SLAM2::MapPoint*> vPointMP;
      vPointMP.reserve(vMPs.size());
      std::stringstream buffer;
      buffer  << 'm';
      for(size_t i=0; i<vMPs.size(); i++)
      {
          ORB_SLAM2::MapPoint* pMP=vMPs[i];
          if(pMP)
          {
              if(pMP->Observations()>5)
              {
                  vPoints.push_back(pMP->GetWorldPos());
                  vPointMP.push_back(pMP);

                  if(buffer.seekp(0, ios::end).tellp() <50){
                    buffer  << vPoints.back()<<';' ;
                  }
                  else{
                    std::cout << buffer.str() ;
                    buffer.str("m");
                  }


              }
          }
      }
      std::cout << buffer.str() ;

      return;
    }
    if (0 == strcmp("close", data)) {
      cout << "Closing.." << endl;
      connection->close();
      cout << "Closed." << endl;
      return;
    }

    /*int value = atoi(data) + 1;
       if (value > _currentValue) {
        setValue(value);
        for (auto c : _connections) {
            c->send(_currentSetValue.c_str());
        }
       }*/
  }
  virtual void onData(WebSocket *, const uint8_t *data, size_t size) {
    vector<char> jpgbytes(data, data + size);
    Mat img = imdecode(jpgbytes, 1); // Mat(480, 640, CV_8UC3, &data).clone();

    if (img.empty()) {
      // cout << "image not loaded";
    } else {
      // cout <<'p'<< _slam->TrackMonocular(img,_currentTime ) << endl;//_currentTime
      cv::Mat Tcw = _slam->TrackMonocular(img,_currentTime );

      if(!Tcw.empty())
      {
          Eigen::Matrix4f M;

          M(0,0) = Tcw.at<float>(0,0);
          M(1,0)= Tcw.at<float>(1,0);
          M(2,0) = Tcw.at<float>(2,0);
          M(3,0)  = 0.0;

          M(0,1) = Tcw.at<float>(0,1);
          M(1,1) = Tcw.at<float>(1,1);
          M(2,1) = Tcw.at<float>(2,1);
          M(3,1)  = 0.0;

          M(0,2) = Tcw.at<float>(0,2);
          M(1,2) = Tcw.at<float>(1,2);
          M(2,2) = Tcw.at<float>(2,2);
          M(3,2)  = 0.0;

          M(0,3) = Tcw.at<float>(0,3);
          M(1,3) = Tcw.at<float>(1,3);
          M(2,3) = Tcw.at<float>(2,3);
          M(3,3)  = 1.0;

           M.block<3, 3>(0, 0) = _BLENDER.transpose().block<3, 3>(0, 0) * M.block<3, 3>(0, 0)  * _BLENDER.block<3, 3>(0, 0) ;

          M(3,0) = -Tcw.at<float>(0,3);
          M(3,1) = Tcw.at<float>(1,3);
          M(3,2) = Tcw.at<float>(2,3);
          // M(2,3) = Tcw.at<float>(2,3);
          Eigen::IOFormat HeavyFmt(Eigen::FullPrecision, 0, ", ", ";\n", "[", "]", "[", "]");
          std::stringstream buffer;

          // std::cout << "p"<<M.format(HeavyFmt) <<std::endl ;
          // set<WebSocket*>::iterator it;
          // it = _connections.begin();
          // WebSocket *connection = *it;
          buffer << M.format(HeavyFmt);
          _blenderInstanceConnexion->send(buffer.str());

          buffer.str();

          /**/
      }



      if (waitKey(1) == 27) {
        _slam->Shutdown();
        exit(0);
      }
    }
  }

  virtual void onDisconnect(WebSocket *connection) {
    _connections.erase(connection);
    cout << "Disconnected: " << connection->getRequestUri() << " : "
         << formatAddress(connection->getRemoteAddress()) << endl;
    // Stop all threads
    if (_slam)
      _slam->Shutdown();
  }

private:
  WebSocket* _blenderInstanceConnexion;
  set<WebSocket *> _connections;
  Server *_server;
  ORB_SLAM2::System *_slam;
  int _currentValue;
  double _currentTime;
  string _currentSetValue;
  // Create SLAM system. It initializes all system threads and gets ready to
  // process frames.

  void setValue(int value) {
    _currentValue = value;
    _currentSetValue = makeExecString("set", _currentValue);
  }
};

int main(int argc, char **argv) {
  _SLAM <<
    1, 0, 0, 0,
    0, 1, 0, 0,
    0, 0, -1, 0,
    0, 0, 0, 1;

  _BLENDER <<
  1, 0, 0, 0,
  0, -1, 0, 0,
  0, 0, -1, 0,
  0, 0, 0, 1;

  cout<<"test";
  auto logger = std::make_shared<PrintfLogger>(Logger::Level::SEVERE);
  ORB_SLAM2::System *SLAM;
  Server server(logger);

  auto cameraHandler = std::make_shared<CameraHandler>(&server, SLAM);
  server.addWebSocketHandler("/ws", cameraHandler);
  auto commandHandler = std::make_shared<CommandHandler>(&server);
  server.addWebSocketHandler("/command", commandHandler);

  server.serve(/*"/home/slumber/Repos/DeviceTracking/static"*/"/dev/null", 6302);
  return 0;
}
