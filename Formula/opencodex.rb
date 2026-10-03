class Opencodex < Formula
  desc "Provider proxy for Codex, Claude Code, and other coding clients"
  homepage "https://github.com/lidge-jun/opencodex"
  version "2.76.0"
  license "MIT"

  on_macos do
    on_arm do
      url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-darwin-arm64.tar.gz"
      sha256 "14322ffe96ab9dd886939c006e97813817b56463578b112391490e4ca4064b2f"
    end
    on_intel do
      url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-darwin-x64.tar.gz"
      sha256 "23ae617019229cc0c06c0b5cec8f8412de698161d19181b294a55fcd9443b46d"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-arm64.tar.gz"
      sha256 "c6cf97828014a40d6dee0dcb43788a972c6acb5f543f9848155b97e0390be0be"
    end
    on_intel do
      url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-x64.tar.gz"
      sha256 "a7da1e1cab42ccc45f7e64c5c25cc5eb7657f127a8771a86397897ae1baac755"
    end
  end

  def install
    # The compiled runtime resolves dashboard and native addons beside its real executable.
    libexec.install "ocx", "gui", "keyring"
    bin.install_symlink libexec/"ocx"
    bin.install_symlink libexec/"ocx" => "opencodex"
  end

  def caveats
    <<~EOS
      Run ocx start to start the proxy, or ocx service to install its background service.
      Open the dashboard at http://localhost:10100.
      Update this installation with brew upgrade --formula chakachakakhan/tap/opencodex.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/ocx --version")
    assert_match version.to_s, shell_output("#{bin}/opencodex --version")
  end
end
