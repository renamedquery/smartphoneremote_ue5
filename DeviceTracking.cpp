#include <stdio.h>
#include<iostream>
#include<algorithm>
#include<fstream>
#include<chrono>

#include "opencv2/opencv.hpp"
#include<opencv2/core/core.hpp>

#include "seasocks/PrintfLogger.h"
#include "seasocks/Server.h"
#include "seasocks/StringUtil.h"
#include "seasocks/WebSocket.h"
#include "seasocks/util/Json.h"

#include<System.h>

using namespace std;
using namespace cv;
using namespace seasocks;


class MyHandler: public WebSocket::Handler {
public:


    explicit MyHandler(Server* server,ORB_SLAM2::System* SLAMPtr) : _server(server),_slam(SLAMPtr), _currentValue(0) {
        setValue(1);


        }

    virtual void onConnect(WebSocket* connection) {
        _connections.insert(connection);
        connection->send(_currentSetValue.c_str());
        cout << "Connected: " << connection->getRequestUri()
                << " : " << formatAddress(connection->getRemoteAddress())
                << endl;
        cout << "Credentials: " << *(connection->credentials()) << endl;
    }

    virtual void onData(WebSocket* connection, const char* data) {
        if (0 == strcmp("die", data)) {
            _server->terminate();
            return;
        }
        if (0 == strcmp("stop_slam", data)) {
            _slam->Shutdown();
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
    virtual void onData(WebSocket*, const uint8_t* data, size_t size) {
      vector<char> jpgbytes(data, data+size);
      Mat img = imdecode(jpgbytes, 1);//Mat(480, 640, CV_8UC3, &data).clone();

      if(img.empty())
      {
          cout<<"image not loaded";
      }
      else
      {
          _slam->TrackMonocular(img,0);
          // cv::imshow("test",img);
          if( waitKey(1) == 27 ){
            _slam->Shutdown();
            exit(0);
          }
      }
      // copies from Result.Buffer into img
      //memcpy(img.ptr(),data,480*640);
    }

    virtual void onDisconnect(WebSocket* connection) {
        _connections.erase(connection);
        cout << "Disconnected: " << connection->getRequestUri()
                << " : " << formatAddress(connection->getRemoteAddress())
                << endl;
        // Stop all threads
        if(_slam)
          _slam->Shutdown();

    }

private:
    set<WebSocket*> _connections;
    Server* _server;
    ORB_SLAM2::System* _slam;
    int _currentValue;
    string _currentSetValue;
    // Create SLAM system. It initializes all system threads and gets ready to process frames.

    void setValue(int value) {
        _currentValue = value;
        _currentSetValue = makeExecString("set", _currentValue);
    }
};


int main(int argc, char** argv)
{
    auto logger = std::make_shared<PrintfLogger>(Logger::Level::DEBUG);
    ORB_SLAM2::System  SLAM("/home/slumber/Repos/ORB_SLAM2/Vocabulary/ORBvoc.txt","/home/slumber/Repos/DeviceTracking/CameraSettings.yaml",ORB_SLAM2::System::MONOCULAR,true);

    Server server(logger);

    auto handler = std::make_shared<MyHandler>(&server, &SLAM);
    server.addWebSocketHandler("/ws", handler);
    server.serve("/home/slumber/Repos/DeviceTracking/static", 8080);
    return 0;
}
