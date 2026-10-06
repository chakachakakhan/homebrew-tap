class Opencodex < Formula
  desc "Provider proxy for Codex, Claude Code, and other coding clients"
  homepage "https://github.com/lidge-jun/opencodex"
  version "2.79.0"
  license "MIT"

  if Hardware::CPU.arm?
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-arm64.tar.gz"
    sha256 "f81bff6692c79fbe5113178e605fb41a66c83acf0a9111a6fc5e1c3505d76e0d"
  else
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-x64.tar.gz"
    sha256 "fbb0acfdde7d97bca840970508c5fce606728b6a26927ead4739b6f21af5b3db"
  end

  depends_on :linux

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
