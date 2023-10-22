# FFPython - Python Audio Player

**FFPython** is a Python app using the open source FFmpeg software
which provides the functionality of a typical audio player, albeit
much more lightweight and simple than the everyday Spotify and other
popular music apps. FFPython can be viewed as a high-level GUI wrapper
around the FFplay program. It is not affilated with FFmpeg in any way.

## Compatibility and Requirements

### Operating System

This software is only supported on Windows. Unfortunately, FFPython
will not run on MacOS or Linux.

### FFmpeg

Of course, the app relies on FFmpeg media software. In this case,
the FFplay and FFprobe binaries must be available for the app to run.
Ensure these commands work in the command prompt:
`ffplay -version`
`ffprobe -version`
If these commands do not work, the app will also not work. Use
to https://www.gyan.dev/ffmpeg/builds/ to install FFmpeg on Windows.
Also ensure the folder you install FFmpeg in is added to PATH. Refer
to this [tutorial](https://www.wikihow.com/Install-FFmpeg-on-Windows) for additional guidance in installing FFmpeg on Windows.

### EXE

A standalone EXE is available to be downloaded and run directly, so no Python installation is necessary to use the app (provided FFmpeg is installed). If running the EXE, the information in the section below is irrelevant.

### Python

If you wish to run the code through Python or tweak the app yourself, the app requires Python 3.10 or above.

There are two Python 3rd party dependencies for loading the font and images (not needed if running the executable):
- [pyglet](https://pypi.org/project/pyglet/)
- [Pillow](https://pypi.org/project/Pillow/)

Furthermore, there is a C++ file which is compiled to an object file.
Its purpose is to communicate with the Win32 API. The object file can be
seen in the bin folder. If not there, the app will still work, but it is
ideal for the object file to exist.

## Key Features

### Supported Audio File Formats

Common audio formats can be played in the app.
The full list of supported file types is:

- **mp3**
- **wav/wma**
- **ogg/oga**
- **m4a**
- acc
- flac
- opus
- mp4 (audio only)

### Audio Player Features

Common audio player features are included.

#### Playback Features
- Pause/resume playback
- Go back/forward a given number seconds (10s in the app)
- Drag to seek to a given timestamp
- Click to seek to a given timestamp
- Looping (can be a fixed number of times, or infinite)

#### Playlist Features

##### Create/Edit/Delete
- Set a playlist name and optionally, a description
- Add a file to a playlist
- Import a folder into a playlist (recursive or not)
- Rearrange a playlist
- Remove a file from a playlist
- Remove missing files from a playlist
- Delete a playlist

##### Play
- Shuffle the playlist
- Go back/forward a file
- Click to play a file in the playlist
- Loop the playlist (can be a fixed number of times, or infinite)

## Tutorial

For guidance on how to use the app once you have set it up,
refer to the [tutorial](TUTORIAL.md) here.