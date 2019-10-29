# Blender smartphone remote
> Use your smartphone as a three-dimensional controller.

The blender smartphone remote is an attempt to bring a free wireless spatialized controller for the masses. By using ARCore, it allows the use of human natural gesture for interactions.

:warning: Under development, use it at your own risks. Currently tested on Windows platform. :warning:

## Installation

1. Download and install latest smartphone remote android app from [here](https://gitlab.com/slumber/smartphoneremoteandroid#installation).
2. Download latest release .
3. Run blender as administrator (dependencies installation).
4. Install last_version.zip from your addon preferences.

[Dependencies](#dependencies) will be automatically added to your blender python during installation.


## Usage example

![camera_animation](https://gitlab.com/slumber/smartphoneremote/wikis/uploads/0a83d79c7d6f59e92d4aa8885539feb2/remotelow.gif)
![camera_record](https://gitlab.com/slumber/smartphoneremote/wikis/uploads/361e212366bc9b67230e69075b191075/recordlow.gif)

## Dependencies

| Dependencies | Version | Needed |
| ------------ | :-----: | -----: |
| ZeroMQ       | latest  |    yes |
| umsgpack      | latest  |    yes |


## Contributing

1. Fork it (<https://github.com/yourname/yourproject/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request