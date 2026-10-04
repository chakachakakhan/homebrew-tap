class Opencodex < Formula
  desc "Provider proxy for Codex, Claude Code, and other coding clients"
  homepage "https://github.com/lidge-jun/opencodex"
  version "2.77.0"
  license "MIT"

  if Hardware::CPU.arm?
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-arm64.tar.gz"
    sha256 "26c0f108601f9ce676f4472e46ba68b63f906ce7502f76dbf6fa9de4bb2c8fd6"
  else
    url "https://github.com/lidge-jun/opencodex/releases/download/v#{version}/ocx-#{version}-bun-linux-x64.tar.gz"
    sha256 "797e1805b99d7fcdb892c81d9809abe8ad5b7259813fc521194934662afe0e89"
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
