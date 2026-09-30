[![Installation checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml)
[![Update checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml)
[![Thorium update checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update-thorium.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update-thorium.yml)

this is my personal tap for my homebrew casks, feel free to use it yourself, fork 
it, whatever, no promise no warranty etc

right now its the chatgpt app by openai and thorium reader by edrlab . it takes the 
apps direct from the publisher, turns it into casks, and in theory should update 
automatically with new updates. we'll see how that goes... 

i vibeslopped the whole project/repo if that bothers you sorry, and then the readme 
was super slop so i rewrote it by hand, thats what this is. manual slop. i did 
like the badges so i kept them at the top.


## Install and uninstall

depends on homebrew on linux. both casks support intel/amd (ofc) and arm (why)
```sh
brew install --cask chakachakakhan/tap/chatgpt-linux
brew install --cask chakachakakhan/tap/thorium-reader-linux
```

chatgpt comes with the chatgpt command, desktop launcher, icon, app metadata. homebrew
installs dpkg to extract the deb package. doesn't come with cli as far as i can tell.

thorium reader installs thorium-reader command, desktop launcer, icon. this isn't 
thorium web browser. its an ereader for epub and other formats.

im using bluefin dakota and it updates homebrew automatically . if ur using another
ublue flavor like bazzite or aurora it probably functions the same. otherwise
run 
```sh
brew update
brew upgrade --cask chakachakakhan/tap/chatgpt-linux
brew upgrade --cask chakachakakhan/tap/thorium-reader-linux
```

the github actions automation should keep things current and you just run the 
homebrew updates to keep it updated on your machine.

if you upgrade or uninstall normally, it should preserve all your settings and 
files, folders, etc. in the default config folders for the respective apps. to
uninstall its like any other homebrew cask
```sh
brew uninstall --cask chakachakakhan/tap/chatgpt-linux
brew uninstall --cask chakachakakhan/tap/thorium-reader-linux
```

use `--zap` to remove the data directories listed in the specific cask. for
thorium that includes its default book library and config. for chatgpt
it includes chatgpt and codex configs and caches. zap won't hit custom data 
locations.


