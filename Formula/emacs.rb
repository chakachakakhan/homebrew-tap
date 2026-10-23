class Emacs < Formula
  desc "GNU Emacs with native Wayland, native compilation, and tree-sitter"
  homepage "https://www.gnu.org/software/emacs/"
  url "https://mirrors.kernel.org/gnu/emacs/emacs-31.1.tar.xz"
  mirror "https://ftp.gnu.org/gnu/emacs/emacs-31.1.tar.xz"
  sha256 "1da5790d9580c81932b5bf700633114468da7b3412d69faa767daebf974f4586"
  license "GPL-3.0-or-later"

  depends_on "pkgconf" => :build
  depends_on "texinfo" => :build
  depends_on "cairo"
  depends_on "dbus"
  depends_on "fontconfig"
  depends_on "freetype"
  depends_on "gcc"
  depends_on "gdk-pixbuf"
  depends_on "giflib"
  depends_on "glib"
  depends_on "gmp"
  depends_on "gnutls"
  depends_on "gtk+3"
  depends_on "harfbuzz"
  depends_on "jpeg-turbo"
  depends_on "libgccjit"
  depends_on "libpng"
  depends_on "librsvg"
  depends_on "libtiff"
  depends_on "libxml2"
  depends_on :linux
  depends_on "little-cms2"
  depends_on "ncurses"
  depends_on "pango"
  depends_on "sqlite"
  depends_on "tree-sitter"
  depends_on "webp"
  depends_on "zlib-ng-compat"

  def install
    # libgccjit uses GCC's version-independent Homebrew library directory.
    jit_lib = formula_opt_lib("libgccjit")/"gcc/current"
    ENV.append "LDFLAGS", "-L#{jit_lib} -Wl,-rpath,#{jit_lib}"

    args = %W[
      --prefix=#{prefix}
      --infodir=#{info}/emacs
      --enable-locallisppath=#{HOMEBREW_PREFIX}/share/emacs/site-lisp
      --disable-silent-rules
      --disable-acl
      --with-pgtk
      --with-native-compilation=aot
      --with-tree-sitter
      --with-modules
      --with-gnutls
      --with-dbus
      --with-systemduserunitdir=no
      --with-xml2
      --with-sqlite3
      --without-ns
      --without-imagemagick
      --without-selinux
      --without-sound
      --without-pop
    ]

    # Keep Homebrew's temporary compiler shims out of the dumped exec-path.
    (buildpath/"lisp/site-load.el").write <<~LISP
      (setq exec-path (delete nil
        (mapcar (lambda (path)
                  (unless (string-match-p "Homebrew/shims" path) path))
                exec-path)))
    LISP

    system "./configure", *args
    system "make"
    system "make", "install"

    # This cache is shared by every linked GSettings provider and must be
    # regenerated after linking rather than owned by an individual keg.
    rm share/"glib-2.0/schemas/gschemas.compiled"
  end

  post_install_steps do
    compile_gsettings_schemas
  end

  service do
    run [opt_bin/"emacs", "--fg-daemon"]
    keep_alive true
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/emacs --version")
    assert_equal "42", shell_output("#{bin}/emacs -Q --batch --eval '(princ (+ 20 22))'")
    features = shell_output("#{bin}/emacs -Q --batch --eval '(princ system-configuration-features)'")
    %w[PGTK NATIVE_COMP TREE_SITTER GNUTLS LIBXML2 MODULES SQLITE3].each do |feature|
      assert_match feature, features
    end
    schema_dir = HOMEBREW_PREFIX/"share/glib-2.0/schemas"
    assert_path_exists schema_dir/"org.gnu.emacs.defaults.gschema.xml"
    ENV["GSETTINGS_SCHEMA_DIR"] = schema_dir.to_s
    gsettings = formula_opt_bin("glib")/"gsettings"
    # Emacs declares a relocatable schema, so it is listed separately.
    assert_match "org.gnu.emacs.defaults", shell_output("#{gsettings} list-relocatable-schemas")

    # Loading comp alone misses broken compiler/linker lookup after bottling.
    (testpath/"native-test.el").write "(defun tap-native-test () (+ 20 22))\n"
    (testpath/"check.el").write <<~LISP
      (require 'comp)
      (unless (native-comp-available-p) (error "Native compilation unavailable"))
      (load (native-compile "native-test.el") nil nil t)
      (unless (native-comp-function-p (symbol-function 'tap-native-test))
        (error "Function was not natively compiled"))
      (princ (tap-native-test))
    LISP
    assert_equal "42", shell_output("#{bin}/emacs -Q --batch -l check.el").strip
  end
end
