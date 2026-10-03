[![Installation checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate.yml)
[![Update checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update.yml)
[![Thorium update checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update-thorium.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/update-thorium.yml)
[![OpenCodex checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-opencodex.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-opencodex.yml)
[![OMP Desktop checks](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-omp-desktop.yml/badge.svg?branch=main)](https://github.com/chakachakakhan/homebrew-tap/actions/workflows/validate-omp-desktop.yml)

this is my personal tap for my homebrew casks, feel free to use it yourself, fork 
it, whatever, no promise no warranty etc

right now its the chatgpt app by openai, thorium reader by edrlab, opencodex, and omp desktop . it takes the
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

## OpenCodex

opencodex is [lidge-jun/opencodex](https://github.com/lidge-jun/opencodex).
the desktop app works on linux intel/amd.
the linux appimage is extracted so it doesn't need fuse. upstream doesn't have
a linux arm desktop build yet.

```sh
brew install --cask chakachakakhan/tap/opencodex
```

launch it from the app menu or run `opencodex-desktop`.
the desktop comes with its own proxy runtime.

if you want the separate cli too, this supports linux on intel/amd and arm:

```sh
brew install --formula chakachakakhan/tap/opencodex
ocx init
ocx start
```

the cli also has the `opencodex` command. its web dashboard is at
http://localhost:10100. desktop and cli use the same default opencodex settings.

the tap checks releases every six hours and merges routine updates after the
install checks pass. no pr merging needed. update your machine through homebrew:

```sh
brew update
brew upgrade --cask chakachakakhan/tap/opencodex
brew upgrade --formula chakachakakhan/tap/opencodex
```

ordinary uninstall keeps your settings. desktop `--zap` removes the listed
opencodex data including `~/.opencodex`, which the cli also uses.

## OMP Desktop

omp desktop is [apoc/omp-desktop](https://github.com/apoc/omp-desktop), a gui
for the oh my pi engine you already have installed. linux intel/amd for now.

```sh
brew install --cask chakachakakhan/tap/omp-desktop
```

launch it from the app menu or run `omp-desktop /path/to/project`.
it uses your installed `omp`, including its provider logins, settings, and sessions.
if you need the engine too: `brew install can1357/tap/omp`.

the appimage is extracted so it doesn't need fuse. the launcher includes
homebrew's command path so it can find omp when opened from the app menu.
updates belong to homebrew for this installation:

```sh
brew update
brew upgrade --cask chakachakakhan/tap/omp-desktop
```

github checks releases every six hours and merges routine updates after the
install, launch, and update-policy checks pass. no pr merging needed.

ordinary uninstall preserves desktop settings and all omp data.
`--zap` removes only the desktop's listed settings and caches; it keeps
`~/.omp`, including the engine's logins, sessions, and named profiles.

```sh
brew uninstall --cask chakachakakhan/tap/omp-desktop
```
