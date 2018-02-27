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

int main(int argc, char** argv)
{
    /*if(argc != 4)
    {
        cerr << endl << "Usage: ./devicetracker path_to_vocabulary path_to_settings path_to_sequence" << endl;
        return 1;
    }*/

    VideoCapture cap;
    // open the default camera, use something different from 0 otherwise;
    // Check VideoCapture documentation.
    if(!cap.open(0))
        return 0;

    // Create SLAM system. It initializes all system threads and gets ready to process frames.
    ORB_SLAM2::System SLAM(argv[1],argv[2],ORB_SLAM2::System::MONOCULAR,true);

    cout << endl << "-------" << endl;
    cout << "Start processing sequence ..." << endl;

    for(;;)
    {
          Mat frame;
          cap >> frame;
          // Pass the image to the SLAM system
          SLAM.TrackMonocular(frame,0);
          if( frame.empty() ) break; // end of video stream
          imshow("this is you, smile! :)", frame);
          if( waitKey(10) == 27 ) break; // stop capturing by pressing ESC

    }
    // the camera will be closed automatically upon exit
    cap.release();
    // Stop all threads
    SLAM.Shutdown();

    return 0;
}
